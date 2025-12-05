# pc-side/src/license_plate_recognizer.py
import cv2
import easyocr
import re
import time
import numpy as np

class LicensePlateRecognizer:
    def __init__(self, config):
        self.config = config
        self.reader = easyocr.Reader(['en'], verbose=False)
        self.stable_plate = ""
        self.stable_start = 0
        self.last_logged = ""
        
        # Kamera opsætning
        self.camera_source = config.get('camera', {}).get('source', 0)
        self.camera_width = config.get('camera', {}).get('width', 640)
        self.camera_height = config.get('camera', {}).get('height', 480)
    
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
        Returnerer: detected_plate eller None
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
    
    def run_real_time(self, db_handler, mqtt_publisher, available_spots=50):
        """
        Kør realtids nummerpladegenkendelse med kamera
        """
        cap = cv2.VideoCapture(self.camera_source)
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.camera_width)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.camera_height)
        
        print("EasyOCR ANPR kører... Tryk Q for stop")
        
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            
            plate = self.process_frame(frame)
            
            if plate:
                # 1. Gem nummerplade i database
                db_handler.insert_license_plate(plate)
                
                # 2. Simpel logik: Hver bil der kommer ind fylder en plads
                #    Hver bil der kører ud frigiver en plads
                #    Dette er en simpel antagelse - i virkeligheden skal du tracke hvilke biler er på parkeringspladsen
                
                # For nu: Hvis der er ledige pladser, antag indkørsel
                if available_spots > 0:
                    event_type = "entry"
                    available_spots -= 1
                    print(f"   → Bil {plate} kører ind. Ledige pladser: {available_spots}")
                else:
                    # Hvis ingen ledige pladser, antag udkørsel
                    event_type = "exit"
                    available_spots = min(available_spots + 1, 200)
                    print(f"   → Bil {plate} kører ud. Ledige pladser: {available_spots}")
                
                # 3. Send til MQTT
                mqtt_publisher.publish_available_spots(available_spots)
                mqtt_publisher.parking_event(plate, event_type)
            
            # Vis kamera output
            cv2.imshow("EasyOCR ANPR", frame)
            
            key = cv2.waitKey(1) & 0xFF
            if key == ord("q"):
                break
        
        cap.release()
        cv2.destroyAllWindows()
        return available_spots