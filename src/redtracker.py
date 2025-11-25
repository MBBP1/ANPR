import cv2
import numpy as np
from collections import deque

def track_red_object():
    # Åbn kamera
    cap = cv2.VideoCapture(0)
    
    # Tjek om kameraet åbner korrekt
    if not cap.isOpened():
        print("Fejl: Kunne ikke åbne kamera!")
        return
    
    print("Kamera åbnet! Tryk 'q' for at afslutte")
    print("Visuel feedback:")
    print("- Grøn boks: Tracket objekt")
    print("- Rød cirkel: Objektets center")
    print("- Blå sti: Bevægelseshistorik")
    
    # Gem positionshistorik for bevægelsessti
    track_points = deque(maxlen=20)
    
    while True:
        # Læs frame fra kamera
        ret, frame = cap.read()
        if not ret:
            print("Fejl: Kunne ikke læse frame fra kamera!")
            break
        
        # Flip billedet horisontalt for spejleffekt (som et spejl)
        frame = cv2.flip(frame, 1)
        
        # Konverter BGR til HSV (bedre til farvedetektion)
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        
        # Definer range for rød farve i HSV
        # Rød farve er speciel fordi den spænder over 0 grad
        lower_red1 = np.array([0, 120, 70])
        upper_red1 = np.array([10, 255, 255])
        lower_red2 = np.array([170, 120, 70])
        upper_red2 = np.array([180, 255, 255])
        
        # Lav masker for rød farve
        mask1 = cv2.inRange(hsv, lower_red1, upper_red1)
        mask2 = cv2.inRange(hsv, lower_red2, upper_red2)
        red_mask = mask1 + mask2
        
        # Rens masken for støj
        kernel = np.ones((5, 5), np.uint8)
        red_mask = cv2.morphologyEx(red_mask, cv2.MORPH_OPEN, kernel)
        red_mask = cv2.morphologyEx(red_mask, cv2.MORPH_CLOSE, kernel)
        
        # Find konturer i masken
        contours, _ = cv2.findContours(red_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        current_position = None
        
        # Hvis der er konturer, find den største
        if contours:
            largest_contour = max(contours, key=cv2.contourArea)
            
            # Filtrer kun store nok konturer (fjern støj)
            if cv2.contourArea(largest_contour) > 500:
                # Få bounding rectangle
                x, y, w, h = cv2.boundingRect(largest_contour)
                
                # Tegn grøn rektangel om objektet
                cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
                
                # Beregn center punkt
                center_x = x + w // 2
                center_y = y + h // 2
                current_position = (center_x, center_y)
                
                # Tilføj position til historik
                track_points.appendleft(current_position)
                
                # Tegn rød cirkel i centrum
                cv2.circle(frame, (center_x, center_y), 8, (0, 0, 255), -1)
                
                # Vis position som tekst
                cv2.putText(frame, f'X: {center_x}, Y: {center_y}', 
                           (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
                cv2.putText(frame, f'Size: {w}x{h}', 
                           (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
                
                # Vis "TRACKING" tekst
                cv2.putText(frame, 'TRACKING RED OBJECT', 
                           (x, y - 15), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
            else:
                # Ingen stor nok kontur fundet
                cv2.putText(frame, 'NO RED OBJECT DETECTED', 
                           (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
        else:
            # Ingen konturer fundet
            cv2.putText(frame, 'NO RED OBJECT DETECTED', 
                       (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
        
        # Tegn bevægelsessti (blå linjer)
        for i in range(1, len(track_points)):
            if track_points[i-1] is None or track_points[i] is None:
                continue
            
            # Gør linjen tyndere jo længere tilbage i historikken
            thickness = int(np.sqrt(20 / float(i + 1)) * 1.5)
            cv2.line(frame, track_points[i-1], track_points[i], (255, 0, 0), thickness)
        
        # Vis kamera billedet med tracking
        cv2.imshow('Red Object Tracker - Press Q to quit', frame)
        
        # Vis også masken (valgfrit - hjælper med debugging)
        cv2.imshow('Red Color Mask', red_mask)
        
        # Tryk 'q' for at afslutte
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
    
    # Ryd op
    cap.release()
    cv2.destroyAllWindows()
    print("Program afsluttet!")

if __name__ == "__main__":
    track_red_object()