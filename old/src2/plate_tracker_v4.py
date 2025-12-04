import cv2
import numpy as np
import pytesseract
import re
import matplotlib.pyplot as plt
from PIL import Image
import io
import time

# === BRUG DIN EKSISTERENDE TESSERACT ===
pytesseract.pytesseract.tesseract_cmd = r'C:\Users\mikke\AppData\Local\Programs\Tesseract-OCR\tesseract.exe'

def smart_license_plate_detection(frame):
    """Smart detection der kombinerer flere teknikker"""
    # Metode 1: Kant-baseret detection
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)
    edges = cv2.Canny(blurred, 50, 150)
    
    kernel = np.ones((5, 5), np.uint8)
    edges_closed = cv2.morphologyEx(edges, cv2.MORPH_CLOSE, kernel)
    
    contours, _ = cv2.findContours(edges_closed, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    plates = []
    for contour in contours:
        area = cv2.contourArea(contour)
        if 2000 < area < 50000:
            epsilon = 0.02 * cv2.arcLength(contour, True)
            approx = cv2.approxPolyDP(contour, epsilon, True)
            
            if len(approx) == 4:
                x, y, w, h = cv2.boundingRect(approx)
                aspect_ratio = w / h
                if 2.0 < aspect_ratio < 5.0:
                    plates.append((x, y, w, h))
    
    return plates

def ai_enhanced_ocr(plate_image):
    """Forbedret OCR med AI-inspirerede teknikker"""
    try:
        # Forstør billedet for bedre detaljer (AI-teknik)
        scale_factor = 3
        height, width = plate_image.shape[:2]
        new_size = (width * scale_factor, height * scale_factor)
        resized = cv2.resize(plate_image, new_size, interpolation=cv2.INTER_CUBIC)
        
        # Avanceret forbehandling (AI-inspireret)
        gray = cv2.cvtColor(resized, cv2.COLOR_BGR2GRAY)
        
        # Brug CLAHE for bedre kontrast (brugt i deep learning)
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
        enhanced = clahe.apply(gray)
        
        # Adaptiv threshold (bedre end global threshold)
        thresh = cv2.adaptiveThreshold(enhanced, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
                                      cv2.THRESH_BINARY, 11, 2)
        
        # Morphological operations for at rydde op
        kernel = np.ones((2,2), np.uint8)
        thresh = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel)
        thresh = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, kernel)
        
        # Smart OCR konfiguration
        config = '--oem 3 --psm 8 -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789'
        text = pytesseract.image_to_string(thresh, config=config)
        
        # Avanceret tekstrensning
        text = re.sub(r'[^A-Z0-9]', '', text.upper())
        text = text.replace('DK', '')  # Fjern DK
        
        # Valider med simple AI-regler
        if len(text) >= 4:
            # Check om det ligner en nummerplade
            has_letters = any(c.isalpha() for c in text)
            has_digits = any(c.isdigit() for c in text)
            
            if has_letters and has_digits:
                return text
        
        return ""
        
    except Exception as e:
        return ""

def display_frame_matplotlib(frame, title="License Plate Detection"):
    """Vis frame med matplotlib i stedet for OpenCV GUI"""
    # Konverter BGR til RGB for matplotlib
    frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    
    # Ryd den forrige plot
    plt.clf()
    
    # Vis billedet
    plt.imshow(frame_rgb)
    plt.title(title)
    plt.axis('off')
    plt.tight_layout()
    
    # Opdater plottet
    plt.pause(0.001)
    plt.draw()

def quick_ai_plate_tracker_no_gui():
    """Hurtig tracker der gemmer billeder i stedet for at vise GUI"""
    cap = cv2.VideoCapture(0)
    
    if not cap.isOpened():
        print("Fejl: Kunne ikke åbne kamera!")
        return
    
    print("AI-Forbedret Nummerplade Tracker startet!")
    print("Mode: Gemmer resultater som filer (ingen GUI)")
    print("Tryk Ctrl+C i terminalen for at afslutte")
    print("Scanning starter nu...")
    
    last_plate = ""
    frame_count = 0
    last_save_time = time.time()
    
    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            
            frame_count += 1
            
            # Kør detection kun hvert 5. frame for at spare CPU
            if frame_count % 5 == 0:
                plates = smart_license_plate_detection(frame)
                
                current_time = time.time()
                should_save = (current_time - last_save_time) > 2  # Gem kun hvert 2. sekund
                
                for (x, y, w, h) in plates:
                    plate_region = frame[y:y+h, x:x+w]
                    
                    # Brug AI-forbedret OCR
                    plate_text = ai_enhanced_ocr(plate_region)
                    
                    if plate_text:
                        # Tegn boks og tekst på frame
                        cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 0), 3)
                        cv2.rectangle(frame, (x, y-35), (x+w, y), (0, 255, 0), -1)
                        cv2.putText(frame, f'AI: {plate_text}', (x, y-10), 
                                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 0), 2)
                        
                        if plate_text != last_plate:
                            print(f"🎯 AI genkendte: {plate_text}")
                            last_plate = plate_text
                            
                            if should_save:
                                # Gem resultatbillede
                                cv2.imwrite(f"results/plate_{plate_text}_{int(time.time())}.jpg", frame)
                                cv2.imwrite(f"results/cropped_{plate_text}_{int(time.time())}.jpg", plate_region)
                                print(f"💾 Gemt billeder for: {plate_text}")
                                last_save_time = current_time
                    
                    else:
                        cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 255), 2)
                
                # Vis status på frame
                cv2.putText(frame, f"Frame: {frame_count} | Last: {last_plate}", (10, 30), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
            
            # Gem et screenshot hvert 10. sekund
            if frame_count % 100 == 0:
                cv2.imwrite(f"results/latest_frame_{frame_count}.jpg", frame)
            
            # Prøv at vise med matplotlib (valgfrit)
            try:
                if frame_count % 30 == 0:  # Kun hvert 30. frame for performance
                    display_frame_matplotlib(frame, f"Live Scan - Frame {frame_count}")
            except:
                pass  # Ignorer matplotlib fejl
            
            # Lav en simpel exit med tastatur (uden GUI)
            # Brug Ctrl+C i terminalen i stedet
            
    except KeyboardInterrupt:
        print("\nAfslutter program...")
    
    finally:
        cap.release()
        print(f"Program afsluttet. Processerede {frame_count} frames")
        print(f"Sidste genkendte plade: {last_plate}")

def simple_batch_processing():
    """Simpel version der bare scanner og gemmer resultater"""
    cap = cv2.VideoCapture(0)
    
    # Opret results mappe
    import os
    if not os.path.exists('results'):
        os.makedirs('results')
    
    print("🚗 Simpel Batch Nummerplade Scanner")
    print("Scanner i 30 sekunder og gemmer resultater...")
    print("Hold en nummerplade foran kameraet!")
    
    start_time = time.time()
    detected_plates = set()
    
    while time.time() - start_time < 30:  # Kør i 30 sekunder
        ret, frame = cap.read()
        if not ret:
            break
        
        plates = smart_license_plate_detection(frame)
        
        for (x, y, w, h) in plates:
            plate_region = frame[y:y+h, x:x+w]
            plate_text = ai_enhanced_ocr(plate_region)
            
            if plate_text and plate_text not in detected_plates:
                print(f"✅ Fundet: {plate_text}")
                detected_plates.add(plate_text)
                
                # Gem med tidsstempel
                timestamp = int(time.time())
                cv2.imwrite(f"results/detected_{plate_text}_{timestamp}.jpg", frame)
                cv2.imwrite(f"results/cropped_{plate_text}_{timestamp}.jpg", plate_region)
        
        # Vis progress
        elapsed = int(time.time() - start_time)
        remaining = 30 - elapsed
        print(f"⏰ Scanning: {elapsed}s/{30}s - Fundet: {len(detected_plates)} plader", end='\r')
        
        time.sleep(0.1)  # Lille pause
    
    cap.release()
    print(f"\n🎉 Scanning færdig! Fundet {len(detected_plates)} unikke nummerplader:")
    for plate in detected_plates:
        print(f"   - {plate}")

if __name__ == "__main__":
    # Vælg hvilken version du vil køre:
    
    # Version 1: Kontinuerlig scanning med filgemning
    quick_ai_plate_tracker_no_gui()
    
    # Version 2: Simpel 30-sekunders batch scanning
    # simple_batch_processing()