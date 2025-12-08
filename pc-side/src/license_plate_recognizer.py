# pc-side/src/license_plate_recognizer.py
import cv2
import easyocr
import re
import time
import numpy as np
from flat_file_db import FlatFileDB  # NY IMPORT!

class LicensePlateRecognizer:
    def __init__(self, config):
        self.config = config
        self.reader = easyocr.Reader(['en'], verbose=False)
        
        # Kamera opsætning
        self.camera_source = config.get('camera', {}).get('source', 0)
        self.camera_width = config.get('camera', {}).get('width', 640)
        self.camera_height = config.get('camera', {}).get('height', 480)
        
        # System state
        self.mode = "entry"  # "entry" eller "exit"
        self.available_spots = 50
        
        # Flat file database
        self.db = FlatFileDB("parked_cars.json")
        
        # Tracking
        self.stable_plate = ""
        self.stable_start = 0
        self.last_logged = ""
    
    def validate_plate_text(self, text):
        """Valider dansk nummerplade format"""
        text = text.replace(" ", "").upper()
        return bool(re.match(r"^[A-Z]{2}\d{5}$", text))
    
    def detect_license_plate(self, frame):
        """Detekter største rektangulære område"""
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        blurred = cv2.GaussianBlur(gray, (5,5), 0)
        edges = cv2.Canny(blurred, 50, 150)
        
        kernel = np.ones((5,5), np.uint8)
        edges_closed = cv2.morphologyEx(edges, cv2.MORPH_CLOSE, kernel)
        
        contours, _ = cv2.findContours(edges_closed, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        candidates = []
        h, w = gray.shape
        cx, cy = w/2, h/2
        
        for cnt in contours:
            area = cv2.contourArea(cnt)
            if area < 2500:
                continue
            x, y, ww, hh = cv2.boundingRect(cnt)
            ratio = ww / float(hh)
            if 2 < ratio < 6:
                dist = np.sqrt((x + ww/2 - cx)**2 + (y + hh/2 - cy)**2)
                score = area - 0.3 * dist
                candidates.append((score, x, y, ww, hh))
        
        if not candidates:
            return []
        
        candidates.sort(reverse=True, key=lambda c: c[0])
        _, x, y, w, h = candidates[0]
        return [(x, y, w, h)]
    
    def read_plate_easyocr(self, plate_img):
        """Læs nummerplade med EasyOCR"""
        result = self.reader.readtext(plate_img, detail=0, paragraph=False)
        
        if not result:
            return ""
        
        text = "".join(result).upper()
        text = re.sub(r"[^A-Z0-9]", "", text)
        
        if len(text) > 7:
            text = text[:7]
        
        return text
    
    def process_frame(self, frame):
        """
        Processer et enkelt frame og returnerer detekteret nummerplade
        """
        plates = self.detect_license_plate(frame)
        now = time.time()
        
        for (x, y, w, h) in plates:
            roi = frame[y:y+h, x:x+w]
            text = self.read_plate_easyocr(roi)
            
            if text and self.validate_plate_text(text):
                # Stabilitetscheck
                if text != self.stable_plate:
                    self.stable_plate = text
                    self.stable_start = now
                else:
                    if now - self.stable_start >= 0.3 and text != self.last_logged:
                        print(f" NUMMERPLADE FUNDET: {text}")
                        self.last_logged = text
                        return text
        
        return None
    
    def handle_entry(self, plate, db_handler, mqtt_publisher):
        """Håndter indkørsel"""
        print(f"   → INDSKÆR: Bil {plate} kører ind")
        
        # Tjek om der er plads
        if self.available_spots > 0:
            # 1. Gem i MariaDB (hvis du vil beholde historik)
            db_handler.insert_license_plate(plate)
            
            # 2. Gem i flat file DB (til exit tracking)
            self.db.car_entry(plate)
            
            # 3. Opdater ledige pladser
            self.available_spots -= 1
            
            # 4. Send til MQTT
            mqtt_publisher.publish_available_spots(self.available_spots)
            mqtt_publisher.parking_event(plate, "entry")
            
            print(f"      ✅ Accepteret - Ledige pladser: {self.available_spots}")
            return True
        else:
            print(f"   ⛔ INGEN PLADS: Bil {plate} afvist")
            mqtt_publisher.parking_event(plate, "denied")
            return False

    def reset_tracking(self):
        """Nulstil tracking når mode ændres"""
        self.stable_plate = ""
        self.stable_start = 0
        self.last_logged = ""
        print("    Tracking nulstillet for nyt mode")

    def handle_exit(self, plate, db_handler, mqtt_publisher):
        """Håndter udkørsel"""
        print(f"   ← UDSKÆR: Bil {plate} kører ud")
        
        # 1. Tjek om bilen er i flat file DB
        if self.db.is_car_parked(plate):
            print(f"      ✅ Bil {plate} er registreret - åbner bom")
            
            # 2. Gem i MariaDB (historik)
            db_handler.insert_license_plate(plate)
            
            # 3. Fjern fra flat file DB
            self.db.car_exit(plate)
            
            # 4. Opdater ledige pladser
            self.available_spots += 1
            
            # 5. Send GATE OPEN kommando til MQTT
            mqtt_publisher.publish_gate_command("open", plate)
            
            # 6. Send status til MQTT
            mqtt_publisher.publish_available_spots(self.available_spots)
            mqtt_publisher.parking_event(plate, "exit")
            
            print(f"      🚗 Bom åbnes - Ledige pladser: {self.available_spots}")
            return True
        else:
            print(f"      ⚠️  Bil {plate} IKKE registreret - ingen handling")
            return False
    
    def run_real_time(self, db_handler, mqtt_publisher):
        """Kør realtids nummerpladegenkendelse"""
        cap = cv2.VideoCapture(self.camera_source)
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.camera_width)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.camera_height)
        
        print("=" * 60)
        print(" PARKERINGSYSTEM - FLAT FILE DATABASE")
        print("=" * 60)
        print(" Tastatur kommandoer:")
        print("  I = Indskær mode (bil kører IND)")
        print("  U = Udskær mode (bil kører UD)")
        print("  S = Status (vis antal parkerede biler)")
        print("  C = Clear database (ryd alle data)")
        print("  Q = Afslut program")
        print("=" * 60)
        print(f" Nuværende mode: {self.mode.upper()}")
        print(f" Ledige pladser: {self.available_spots}")
        print(f" Parkerede biler: {self.db.get_count()}")
        print("=" * 60)
        
        # Send initial status
        mqtt_publisher.publish_available_spots(self.available_spots)
        
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            
            # Process frame for nummerplade
            plate = self.process_frame(frame)
            
            if plate:
                if self.mode == "entry":
                    self.handle_entry(plate, db_handler, mqtt_publisher)
                elif self.mode == "exit":
                    self.handle_exit(plate, db_handler, mqtt_publisher)
            
            # Tilføj overlay
            frame_with_info = self.add_overlay(frame)
            
            # Vis kamera output
            cv2.imshow("Parkeringssystem - Flat File DB", frame_with_info)
            
            # Tastatur input
            key = cv2.waitKey(1) & 0xFF
            
            if key == ord('q') or key == ord('Q'):
                break
            elif key == ord('i') or key == ord('I'):
                if self.mode != "entry":  # Kun hvis faktisk ændring
                    self.mode = "entry"
                    self.reset_tracking()  # NULSTIL TRACKING!
                    print(f"\n[ÆNDRET MODE] Nu: INDSKÆR (bil kører IND)")
            elif key == ord('u') or key == ord('U'):
                if self.mode != "exit":  # Kun hvis faktisk ændring
                    self.mode = "exit"
                    self.reset_tracking()  # NULSTIL TRACKING!
                    print(f"\n[ÆNDRET MODE] Nu: UDSKÆR (bil kører UD)")
            elif key == ord('s') or key == ord('S'):
                parked_cars = self.db.get_all_parked_cars()
                print(f"\n[STATUS] Ledige pladser: {self.available_spots}")
                print(f"         Parkerede biler: {self.db.get_count()}")
                print(f"         Mode: {self.mode}")
                if parked_cars:
                    print(f"         Liste over parkerede biler:")
                    for i, car in enumerate(parked_cars, 1):
                        print(f"           {i}. {car}")
            elif key == ord('c') or key == ord('C'):
                confirm = input("\nEr du sikker på du vil rydde alle data? (ja/nej): ")
                if confirm.lower() == 'ja':
                    self.db.clear_all()
                    self.available_spots = 50
                    print("   ✅ Alle data ryddet og pladser nulstillet")
        
        cap.release()
        cv2.destroyAllWindows()
    
    def add_overlay(self, frame):
        """Tilføj overlay med info til videoen"""
        overlay = frame.copy()
        
        # Mode info (øverst venstre)
        mode_text = f"Mode: {self.mode.upper()}"
        spots_text = f"Ledige pladser: {self.available_spots}"
        parked_text = f"Parkeret: {self.db.get_count()}"
        
        # Baggrund for tekst
        cv2.rectangle(overlay, (10, 10), (300, 120), (0, 0, 0), -1)
        cv2.rectangle(overlay, (10, 10), (300, 120), (255, 255, 255), 2)
        
        # Tilføj tekst
        cv2.putText(overlay, mode_text, (20, 40), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)
        cv2.putText(overlay, spots_text, (20, 70), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 200, 255), 2)
        cv2.putText(overlay, parked_text, (20, 100), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 150, 255), 2)
        
        # Instruktioner
        instructions = "I=Indskær  U=Udskær  S=Status  C=Clear  Q=Afslut"
        cv2.putText(overlay, instructions, 
                    (10, frame.shape[0] - 20), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
        
        # Farve baseret på mode
        border_color = (0, 100, 0) if self.mode == "entry" else (0, 0, 100)
        cv2.rectangle(overlay, (5, 5), (frame.shape[1]-5, frame.shape[0]-5), 
                     border_color, 8)
        
        return overlay