import cv2
import numpy as np
import pytesseract
import re

# === VIGTIGT: Indstil stien til Tesseract ===
# Windows (mest almindelige):
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

# Mac (brug denne i stedet):
# pytesseract.pytesseract.tesseract_cmd = '/usr/local/bin/tesseract'

# Linux (brug denne i stedet):
# pytesseract.pytesseract.tesseract_cmd = '/usr/bin/tesseract'

def preprocess_for_ocr(image):
    """Forbehandle billede for bedre OCR resultat"""
    # Konverter til gråskala
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    
    # Støjreduktion
    gray = cv2.bilateralFilter(gray, 11, 17, 17)
    
    # Brug adaptiv threshold for bedre tekstlæsning
    thresh = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
                                  cv2.THRESH_BINARY, 11, 2)
    
    return thresh

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
        # Forbehandle nummerplade for OCR
        processed_plate = preprocess_for_ocr(plate_image)
        
        # OCR konfiguration - optimeret for nummerplader
        config = '--oem 3 --psm 8 -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789'
        
        # Kør OCR
        text = pytesseract.image_to_string(processed_plate, config=config)
        
        # Rens tekst - fjern specialtegn og mellemrum
        text = re.sub(r'[^A-Z0-9]', '', text.upper())
        
        return text
    except Exception as e:
        print(f"OCR fejl: {e}")
        return ""

def validate_plate_text(text):
    """Valider om teksten ligner en nummerplade"""
    if len(text) < 4 or len(text) > 8:
        return False
    
    # Dansk nummerplade formater
    patterns = [
        r'^[A-Z]{2}\d{5}$',      # AB12345
        r'^[A-Z]{2}\d{4}$',      # AB1234 (ældre)
        r'^[A-Z]{2}\d{3}[A-Z]{2}$', # AB123CD (personlig)
        r'^\d{2}[A-Z]{2}\d{3}$', # 12AB345 (ny)
    ]
    
    for pattern in patterns:
        if re.match(pattern, text):
            return True
    
    # Hvis ikke matcher nøjagtigt, men har ret format
    if any(c.isalpha() for c in text) and any(c.isdigit() for c in text):
        return True
    
    return False

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
    detection_count = 0
    
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
            
            # Valider og vis resultat
            if plate_text and validate_plate_text(plate_text):
                # Tegn grøn boks for valideret nummerplade
                cv2.rectangle(display_frame, (x, y), (x + w, y + h), (0, 255, 0), 3)
                
                # Tegn baggrund for tekst
                cv2.rectangle(display_frame, (x, y-40), (x + w, y), (0, 255, 0), -1)
                cv2.putText(display_frame, f'{plate_text}', 
                           (x, y-10), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 0), 2)
                
                if plate_text != last_detected_plate:
                    print(f"✅ Genkendt nummerplade: {plate_text}")
                    last_detected_plate = plate_text
                    detection_count += 1
                    
                    # Gem nummerpladebillede
                    cv2.imwrite(f"plate_{plate_text}_{detection_count}.jpg", plate_region)
            
            elif plate_text:  # Tekst fundet men ikke valideret
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
    print(f"Program afsluttet. Total genkendte plader: {detection_count}")

# === TEST MED BILLEDE FIL ===
def test_with_image(image_path):
    """Test OCR med et statisk billede"""
    image = cv2.imread(image_path)
    if image is None:
        print(f"Kunne ikke indlæse billede: {image_path}")
        return
    
    plates = detect_license_plate(image)
    
    for (x, y, w, h) in plates:
        plate_region = image[y:y+h, x:x+w]
        plate_text = read_license_plate(plate_region)
        
        if plate_text:
            print(f"Genkendt tekst: {plate_text}")
            cv2.rectangle(image, (x, y), (x + w, y + h), (0, 255, 0), 3)
            cv2.putText(image, plate_text, (x, y-10), 
                       cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
        else:
            cv2.rectangle(image, (x, y), (x + w, y + h), (0, 0, 255), 2)
    
    cv2.imshow('Test Result', image)
    cv2.waitKey(0)
    cv2.destroyAllWindows()

if __name__ == "__main__":
    # Kør realtid tracker
    license_plate_tracker_with_ocr()
    
    # For at teste med et billede i stedet:
    # test_with_image("din_billede_fil.jpg")