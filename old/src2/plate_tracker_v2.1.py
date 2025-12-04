import cv2
import numpy as np
import pytesseract
import re

# === VIGTIGT: Indstil stien til Tesseract ===
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

def detect_license_plate(frame):
    """Detekter nummerplade i billedet"""
    # Konverter til gråskala
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    
    # Støjreduktion
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)
    
    # Kantdetektion
    edges = cv2.Canny(blurred, 50, 150)
    
    # Lukning for at forbinde kanter
    kernel = np.ones((5, 5), np.uint8)
    edges_closed = cv2.morphologyEx(edges, cv2.MORPH_CLOSE, kernel)
    
    # Find konturer
    contours, _ = cv2.findContours(edges_closed, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    potential_plates = []
    
    for contour in contours:
        area = cv2.contourArea(contour)
        if area < 2000:  # Filtrer for små områder
            continue
        
        # Tilnærm kontur med polygon
        epsilon = 0.02 * cv2.arcLength(contour, True)
        approx = cv2.approxPolyDP(contour, epsilon, True)
        
        # Look for rectangular shapes (4 corners)
        if len(approx) == 4:
            x, y, w, h = cv2.boundingRect(approx)
            aspect_ratio = w / h
            
            # Nummerplade-lignende aspect ratio
            if 2.0 < aspect_ratio < 5.0:
                potential_plates.append((x, y, w, h))
    
    return potential_plates

def read_license_plate(plate_image):
    """Læs nummerplade tekst med OCR"""
    try:
        # Konverter til gråskala
        gray = cv2.cvtColor(plate_image, cv2.COLOR_BGR2GRAY)
        
        # Forbedret threshold for bedre læsbarhed
        _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        
        # OCR konfiguration - optimeret for nummerplader
        config = '--oem 3 --psm 8 -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789'
        
        # Kør OCR
        text = pytesseract.image_to_string(thresh, config=config)
        
        # Rens tekst - fjern specialtegn og mellemrum
        text = re.sub(r'[^A-Z0-9]', '', text.upper())
        
        return text
    except Exception as e:
        print(f"OCR fejl: {e}")
        return ""

def license_plate_tracker_with_ocr():
    """Hovedfunktion med OCR"""
    # Åbn kamera
    cap = cv2.VideoCapture(0)
    
    if not cap.isOpened():
        print("Fejl: Kunne ikke åbne kamera!")
        return
    
    print("Nummerplade tracker med OCR startet!")
    print("Tryk 'q' for at afslutte")
    print("Tryk 's' for at gemme nummerplade")
    
    last_detected_plate = ""
    
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        
        frame = cv2.flip(frame, 1)
        display_frame = frame.copy()
        
        # Detekter nummerplader
        plates = detect_license_plate(frame)
        
        for (x, y, w, h) in plates:
            # Udtræk nummerplade region
            plate_region = frame[y:y+h, x:x+w]
            
            # Læs nummerplade med OCR
            plate_text = read_license_plate(plate_region)
            
            # Vis resultat
            if plate_text and len(plate_text) >= 4:
                # Tegn grøn boks for valideret nummerplade
                cv2.rectangle(display_frame, (x, y), (x + w, y + h), (0, 255, 0), 3)
                
                # Tegn baggrund for tekst
                cv2.rectangle(display_frame, (x, y-40), (x + w, y), (0, 255, 0), -1)
                cv2.putText(display_frame, f'{plate_text}', 
                           (x, y-10), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 0), 2)
                
                if plate_text != last_detected_plate:
                    print(f"✅ Genkendt nummerplade: {plate_text}")
                    last_detected_plate = plate_text
            
            elif plate_text:  # Tekst fundet men for kort
                # Tegn gul boks for potentiel nummerplade
                cv2.rectangle(display_frame, (x, y), (x + w, y + h), (0, 255, 255), 2)
                cv2.putText(display_frame, f'? {plate_text}', 
                           (x, y-10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)
            
            else:  # Ingen tekst genkendt
                # Tegn rød boks for detekteret område
                cv2.rectangle(display_frame, (x, y), (x + w, y + h), (0, 0, 255), 2)
                cv2.putText(display_frame, 'No Text', 
                           (x, y-10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)
        
        # Vis statistik
        cv2.putText(display_frame, f'Plates detected: {len(plates)}', 
                   (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        
        if last_detected_plate:
            cv2.putText(display_frame, f'Last plate: {last_detected_plate}', 
                       (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        
        cv2.putText(display_frame, "Press 'Q' to quit", 
                   (10, 90), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 0), 1)
        
        # Vis resultat
        cv2.imshow('License Plate Tracker with OCR', display_frame)
        
        # Håndter tastetryk
        key = cv2.waitKey(1) & 0xFF
        if key == ord('q'):
            break
        elif key == ord('s'):
            # Gem screenshot
            cv2.imwrite("screenshot.jpg", display_frame)
            print("Screenshot gemt som 'screenshot.jpg'")
    
    cap.release()
    cv2.destroyAllWindows()
    print("Program afsluttet")

# Kør programmet
if __name__ == "__main__":
    license_plate_tracker_with_ocr()