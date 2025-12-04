import cv2
import numpy as np
import pytesseract
import re

# === BRUG DIN STI ===
pytesseract.pytesseract.tesseract_cmd = r'C:\Users\mikke\AppData\Local\Programs\Tesseract-OCR\tesseract.exe'

def detect_license_plate(frame):
    """Detekter nummerplade i billedet"""
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)
    edges = cv2.Canny(blurred, 50, 150)
    
    kernel = np.ones((5, 5), np.uint8)
    edges_closed = cv2.morphologyEx(edges, cv2.MORPH_CLOSE, kernel)
    
    contours, _ = cv2.findContours(edges_closed, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    potential_plates = []
    
    for contour in contours:
        area = cv2.contourArea(contour)
        if area < 2000:
            continue
        
        epsilon = 0.02 * cv2.arcLength(contour, True)
        approx = cv2.approxPolyDP(contour, epsilon, True)
        
        if len(approx) == 4:
            x, y, w, h = cv2.boundingRect(approx)
            aspect_ratio = w / h
            
            if 2.0 < aspect_ratio < 5.0:
                potential_plates.append((x, y, w, h))
    
    return potential_plates

def remove_blue_dk_field(plate_image):
    """Fjern det blå DK-felt fra nummerpladen"""
    # Konverter til HSV for bedre farvedetektion
    hsv = cv2.cvtColor(plate_image, cv2.COLOR_BGR2HSV)
    
    # Definer range for blå farve (DK-feltet)
    lower_blue = np.array([100, 150, 50])
    upper_blue = np.array([140, 255, 255])
    
    # Lav maske for blå områder
    blue_mask = cv2.inRange(hsv, lower_blue, upper_blue)
    
    # Hvis der er et stort blåt område (DK-felt), fjern det
    blue_pixels = np.sum(blue_mask > 0)
    total_pixels = plate_image.shape[0] * plate_image.shape[1]
    
    if blue_pixels / total_pixels > 0.1:  # Hvis mere end 10% er blåt
        # Find konturer i den blå maske
        contours, _ = cv2.findContours(blue_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        for contour in contours:
            # Hvis dette er DK-feltet (typisk i venstre side)
            x_dk, y_dk, w_dk, h_dk = cv2.boundingRect(contour)
            
            # Hvis det blå område er i venstre side og er cirka 1/4 af bredden
            if x_dk < plate_image.shape[1] * 0.3 and w_dk < plate_image.shape[1] * 0.4:
                # Erstat det blå område med hvid baggrund
                plate_image[y_dk:y_dk+h_dk, x_dk:x_dk+w_dk] = [255, 255, 255]
    
    return plate_image

def extract_main_plate_text(plate_image):
    """Ekstraher hovedteksten og ignorer DK-feltet"""
    # Fjern DK-feltet først
    cleaned_plate = remove_blue_dk_field(plate_image)
    
    # Konverter til gråskala
    gray = cv2.cvtColor(cleaned_plate, cv2.COLOR_BGR2GRAY)
    
    # Brug adaptiv threshold for bedre tekst
    thresh = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
                                  cv2.THRESH_BINARY, 11, 2)
    
    # Find alle tekstområder
    contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    text_regions = []
    
    for contour in contours:
        x, y, w, h = cv2.boundingRect(contour)
        
        # Filtrer for store nok tekstområder (ikke støj)
        if w > 20 and h > 30 and w < plate_image.shape[1] * 0.8:
            text_regions.append((x, y, w, h))
    
    # Sorter fra venstre mod højre
    text_regions.sort(key=lambda region: region[0])
    
    # Hvis vi har flere tekstområder, fokuser på de største (hovednummeret)
    if len(text_regions) >= 2:
        # Tag de områder der er i midten/højre side (ikke DK-feltet)
        main_regions = [region for region in text_regions 
                       if region[0] > plate_image.shape[1] * 0.2]
        
        if main_regions:
            # Kombiner de vigtigste regioner
            main_text = ""
            for region in main_regions:
                x, y, w, h = region
                char_region = thresh[y:y+h, x:x+w]
                
                config = '--oem 3 --psm 8 -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789'
                char_text = pytesseract.image_to_string(char_region, config=config)
                main_text += char_text
            
            main_text = re.sub(r'[^A-Z0-9]', '', main_text.upper())
            return main_text
    
    # Hvis ikke vi kunne isolere specifikke regioner, brug hele billedet
    config = '--oem 3 --psm 8 -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789'
    full_text = pytesseract.image_to_string(thresh, config=config)
    full_text = re.sub(r'[^A-Z0-9]', '', full_text.upper())
    
    return full_text

def read_license_plate(plate_image):
    """Læs nummerplade tekst med OCR - ignorer DK"""
    try:
        # Brug den smarte metode der fjerner DK
        plate_text = extract_main_plate_text(plate_image)
        
        # Filtrer "DK" ud af resultatet
        plate_text = plate_text.replace('DK', '')
        
        return plate_text
    except Exception as e:
        print(f"OCR fejl: {e}")
        return ""

def validate_plate_text(text):
    """Valider om teksten ligner en nummerplade (uden DK)"""
    if len(text) < 4 or len(text) > 8:
        return False
    
    # Dansk nummerplade formater (uden DK)
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
    """Hovedfunktion med OCR der ignorerer DK-felt"""
    # Åbn kamera
    cap = cv2.VideoCapture(0)
    
    if not cap.isOpened():
        print("Fejl: Kunne ikke åbne kamera!")
        return
    
    print("Nummerplade tracker med OCR startet!")
    print("Ignorerer DK-feltet på danske nummerplader")
    print("Tryk 'q' for at afslutte")
    print("Tryk 's' for at gemme nummerplade")
    
    last_detected_plate = ""
    detection_count = 0
    
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        
        display_frame = frame.copy()
        
        # Detekter nummerplader
        plates = detect_license_plate(frame)
        
        for (x, y, w, h) in plates:
            # Udtræk nummerplade region
            plate_region = frame[y:y+h, x:x+w]
            
            # Læs nummerplade med OCR (ignorer DK)
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
                    print(f"[SUCCESS] Genkendt nummerplade: {plate_text}")
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
        cv2.imshow('License Plate Tracker (ignorerer DK)', display_frame)
        
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

# Kør programmet
if __name__ == "__main__":
    license_plate_tracker_with_ocr()