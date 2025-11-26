import cv2
import numpy as np
import os

def create_license_plate_templates():
    """Opret simple templates for tal og bogstaver"""
    templates = {}
    
    # Opret en mappe til templates hvis den ikke findes
    if not os.path.exists('templates'):
        os.makedirs('templates')
    
    # Generer simple templates for tal 0-9
    for i in range(10):
        # Lav et lille billede med et tal
        template = np.zeros((30, 20), dtype=np.uint8)
        cv2.putText(template, str(i), (5, 20), cv2.FONT_HERSHEY_SIMPLEX, 0.8, 255, 2)
        templates[str(i)] = template
        cv2.imwrite(f'templates/{i}.png', template)
    
    # Generer templates for bogstaver A-Z
    for letter in 'ABCDEFGHIJKLMNOPQRSTUVWXYZ':
        template = np.zeros((30, 20), dtype=np.uint8)
        cv2.putText(template, letter, (5, 20), cv2.FONT_HERSHEY_SIMPLEX, 0.8, 255, 2)
        templates[letter] = template
        cv2.imwrite(f'templates/{letter}.png', template)
    
    return templates

def detect_license_plate_region(frame):
    """Detekter nummerplade region baseret på farve og form"""
    # Konverter til HSV farverum
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
    
    # Definer ranges for hvide områder (typisk for nummerplader)
    lower_white = np.array([0, 0, 150])
    upper_white = np.array([180, 50, 255])
    
    # Definer ranges for lysegrå områder
    lower_gray = np.array([0, 0, 100])
    upper_gray = np.array([180, 50, 200])
    
    # Lav masker
    mask_white = cv2.inRange(hsv, lower_white, upper_white)
    mask_gray = cv2.inRange(hsv, lower_gray, upper_gray)
    
    # Kombiner masker
    mask = cv2.bitwise_or(mask_white, mask_gray)
    
    # Forbedring af masken
    kernel = np.ones((5, 5), np.uint8)
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
    
    # Find konturer
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    potential_plates = []
    
    for contour in contours:
        # Check områdestørrelse
        area = cv2.contourArea(contour)
        if area < 1000 or area > 50000:
            continue
        
        # Få bounding rectangle
        x, y, w, h = cv2.boundingRect(contour)
        
        # Check aspect ratio (nummerplader er brede)
        aspect_ratio = w / h
        if 2.0 < aspect_ratio < 6.0:
            potential_plates.append((x, y, w, h))
    
    return potential_plates, mask

def extract_characters(plate_region):
    """Ekstrakér individuelle tegn fra nummerplade region"""
    # Konverter til gråskala
    gray = cv2.cvtColor(plate_region, cv2.COLOR_BGR2GRAY)
    
    # Threshold for at få binært billede
    _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    
    # Inverter hvis baggrund er mørk
    if np.mean(thresh) > 127:
        thresh = cv2.bitwise_not(thresh)
    
    # Find konturer af tegn
    contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    characters = []
    
    for contour in contours:
        x, y, w, h = cv2.boundingRect(contour)
        
        # Filtrer baseret på størrelse (tegn vs støj)
        if 20 < w < 100 and 40 < h < 120:
            char_region = thresh[y:y+h, x:x+w]
            characters.append((x, char_region))
    
    # Sorter tegn fra venstre mod højre
    characters.sort(key=lambda x: x[0])
    
    return [char[1] for char in characters]

def simple_character_recognition(char_image, templates):
    """Simpel tegn-genkendelse ved template matching"""
    best_match = None
    best_score = 0
    
    # Resize karakter til standard størrelse
    char_resized = cv2.resize(char_image, (20, 30))
    
    for char, template in templates.items():
        # Template matching
        result = cv2.matchTemplate(char_resized, template, cv2.TM_CCOEFF_NORMED)
        _, max_val, _, _ = cv2.minMaxLoc(result)
        
        if max_val > best_score:
            best_score = max_val
            best_match = char
    
    # Returner kun hvis match er godt nok
    return best_match if best_score > 0.5 else None

def detect_edges_find_plates(frame):
    """Alternativ metode: Kantdetektion for at finde nummerplader"""
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
    
    plates = []
    
    for contour in contours:
        area = cv2.contourArea(contour)
        if area < 2000:
            continue
        
        # Tilnærm kontur med polygon
        epsilon = 0.02 * cv2.arcLength(contour, True)
        approx = cv2.approxPolyDP(contour, epsilon, True)
        
        # Look for rectangular shapes (4 corners)
        if len(approx) == 4:
            x, y, w, h = cv2.boundingRect(approx)
            aspect_ratio = w / h
            
            if 2.0 < aspect_ratio < 5.0:
                plates.append((x, y, w, h))
    
    return plates, edges_closed

def license_plate_tracker_no_ocr():
    """Hovedfunktion - tracker nummerplader uden OCR"""
    # Åbn kamera
    cap = cv2.VideoCapture(0)
    
    if not cap.isOpened():
        print("Fejl: Kunne ikke åbne kamera!")
        return
    
    print("Nummerplade tracker (uden OCR) startet!")
    print("Tryk 'q' for at afslutte")
    print("Tryk 'm' for at skifte mellem detektionsmetoder")
    
    # Opret templates (kun første gang)
    templates = create_license_plate_templates()
    
    detection_method = 0  # 0 = farvebaseret, 1 = kantbaseret
    tracked_plates = []
    
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        
        frame = cv2.flip(frame, 1)
        display_frame = frame.copy()
        
        if detection_method == 0:
            # Farvebaseret detektion
            plates, mask = detect_license_plate_region(frame)
            method_name = "COLOR-BASED"
        else:
            # Kantbaseret detektion
            plates, mask = detect_edges_find_plates(frame)
            method_name = "EDGE-BASED"
        
        # Process hver fundet nummerplade
        for (x, y, w, h) in plates:
            # Tegn boks om nummerplade
            cv2.rectangle(display_frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
            
            # Udtræk nummerplade region
            plate_region = frame[y:y+h, x:x+w]
            
            # Prøv at ekstrakér tegn (valgfrit)
            try:
                characters = extract_characters(plate_region)
                
                # Simpel tegn-tælling visning
                cv2.putText(display_frame, f'Chars: {len(characters)}', 
                           (x, y-10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
                
            except:
                pass
            
            # Gem plade info
            plate_info = {
                'position': (x, y, w, h),
                'timestamp': cv2.getTickCount()
            }
            tracked_plates.append(plate_info)
            
            # Hold kun de seneste 10 plader
            if len(tracked_plates) > 10:
                tracked_plates.pop(0)
        
        # Vis tracking info
        cv2.putText(display_frame, f'Method: {method_name}', 
                   (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        cv2.putText(display_frame, f'Plates detected: {len(plates)}', 
                   (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        cv2.putText(display_frame, "Press 'm' to switch method", 
                   (10, 90), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 0), 2)
        
        # Vis hovedframe
        cv2.imshow('License Plate Tracker (No OCR)', display_frame)
        
        # Vis masken for debugging
        cv2.imshow('Detection Mask', mask)
        
        # Håndter tastetryk
        key = cv2.waitKey(1) & 0xFF
        if key == ord('q'):
            break
        elif key == ord('m'):
            detection_method = 1 - detection_method  # Skift mellem 0 og 1
            print(f"Skiftet til {['COLOR-BASED', 'EDGE-BASED'][detection_method]} detektion")
        elif key == ord('s'):
            # Gem screenshot
            cv2.imwrite("license_plate_detection.jpg", display_frame)
            print("Screenshot gemt!")
    
    cap.release()
    cv2.destroyAllWindows()
    print("Tracker afsluttet!")

def simple_motion_based_tracker():
    """Enkel bevægelsesbaseret tracker for nummerplader"""
    cap = cv2.VideoCapture(0)
    
    # Forrige frame for motion detection
    ret, prev_frame = cap.read()
    prev_gray = cv2.cvtColor(prev_frame, cv2.COLOR_BGR2GRAY)
    
    print("Bevægelsesbaseret tracker startet!")
    
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        
        frame = cv2.flip(frame, 1)
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        
        # Beregn frame differens
        frame_diff = cv2.absdiff(prev_gray, gray)
        
        # Threshold differensen
        _, motion_mask = cv2.threshold(frame_diff, 25, 255, cv2.THRESH_BINARY)
        
        # Forbedring af motion mask
        kernel = np.ones((5, 5), np.uint8)
        motion_mask = cv2.morphologyEx(motion_mask, cv2.MORPH_OPEN, kernel)
        
        # Find bevægelsesområder
        contours, _ = cv2.findContours(motion_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        for contour in contours:
            if cv2.contourArea(contour) > 1000:
                x, y, w, h = cv2.boundingRect(contour)
                
                # Check om dette kunne være en nummerplade baseret på form
                aspect_ratio = w / h
                if 2.0 < aspect_ratio < 5.0:
                    cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 0, 255), 2)
                    cv2.putText(frame, 'MOVING PLATE', (x, y-10), 
                               cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)
        
        # Opdater previous frame
        prev_gray = gray.copy()
        
        cv2.imshow('Motion-Based Plate Tracker', frame)
        cv2.imshow('Motion Mask', motion_mask)
        
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
    
    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    # Kør hovedtrackeren uden OCR
    license_plate_tracker_no_ocr()
    
    # Eller kør den bevægelsesbaserede version:
    # simple_motion_based_tracker()