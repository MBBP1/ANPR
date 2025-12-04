# pc-side/src/main.py
#Midlertidig simulator for nummerpladegenkendelse og parkeringshændelser


import time 
import random
import yaml  # Tilføj denne import
from database_handler import DatabaseHandler
from mqtt_publisher import MQTTPublisher

class LicensePlateSimulator:
    def __init__(self):
        self.plates = ["AB12345", "CD67890", "EF24680", "GH13579", "IJ11223"]
        self.available_spots = 50
        self.total_spots = 200
    
    def simulate_plate_detection(self):
        """Simulerer at en nummerplade bliver genkendt"""
        plate = random.choice(self.plates)
        print(f" Nummerplade genkendt: {plate}")
        
        # Simuler indkørsel (75% chance) eller udkørsel (25% chance)
        if random.random() < 0.75 and self.available_spots > 0:
            event_type = "entry"
            self.available_spots -= 1
            print(f"  -> Bil kører ind. Ledige pladser: {self.available_spots}")
        else:
            event_type = "exit" 
            self.available_spots = min(self.available_spots + 1, self.total_spots)
            print(f"  -> Bil kører ud. Ledige pladser: {self.available_spots}")
        
        return plate, event_type

def load_config():
    """Indlæs YAML konfiguration"""
    try:
        with open('config/config.yaml', 'r') as file:
            config = yaml.safe_load(file)
        return config
    except Exception as e:
        print(f" Fejl ved indlæsning af config: {e}")
        return {}

def main():
    # Load configuration
    config = load_config()
    
    if not config:
        print(" Kunne ikke indlæse konfiguration")
        return
    
    # Initialize components
    db_handler = DatabaseHandler(config)
    mqtt_publisher = MQTTPublisher(config)
    simulator = LicensePlateSimulator()
    
    print(" Parkeringssystem simulator startet...")
    print(" Sendere data til MQTT og database")
    print(" Database: localhost:3306")
    print(" MQTT: localhost:1883")
    print("  Tryk Ctrl+C for at stoppe\n")
    
    try:
        while True:
            # Simuler nummerpladegenkendelse
            plate, event_type = simulator.simulate_plate_detection()
            
            # Gem i database
            db_handler.insert_license_plate(plate)
            db_handler.insert_parking_event(plate, event_type)
            db_handler.update_parking_spots(simulator.available_spots)
            
            # Send til MQTT
            mqtt_publisher.publish_available_spots(simulator.available_spots)
            mqtt_publisher.parking_event(plate, event_type)
            
            # Vent 3-8 sekunder før næste "genkendelse"
            time.sleep(random.uniform(3, 8))
            
    except KeyboardInterrupt:
        print("\n Simulator stoppet")

if __name__ == "__main__":
    main()