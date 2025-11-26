import mysql.connector
from datetime import datetime

class DatabaseHandler:
    def __init__(self, config):
        self.config = config
        self.connection = None
        self.connect()
    
    def connect(self):
        """Opret forbindelse til databasen"""
        try:
            db_config = self.config.get('database', {})
            self.connection = mysql.connector.connect(
                host=db_config.get('host', 'localhost'),
                port=db_config.get('port', 3306),
                user=db_config.get('user', 'parking_user'),
                password=db_config.get('password', 'parking_password123'),
                database=db_config.get('database', 'parking_system')
            )
            print(" Forbundet til database")
        except Exception as e:
            print(f" Database fejl: {e}")
    
    # Resten af metoderne forbliver de samme...
    def insert_license_plate(self, plate_number):
        """Indsæt nummerplade i databasen"""
        try:
            cursor = self.connection.cursor()
            query = "INSERT INTO license_plates (plate_number) VALUES (%s)"
            cursor.execute(query, (plate_number,))
            self.connection.commit()
            cursor.close()
            print(f"   Gemt nummerplade: {plate_number}")
        except Exception as e:
            print(f"   Database fejl (plade): {e}")
    
    def insert_parking_event(self, plate_number, event_type):
        """Indsæt parkeringsbegivenhed"""
        try:
            cursor = self.connection.cursor()
            query = "INSERT INTO parking_events (plate_number, event_type) VALUES (%s, %s)"
            cursor.execute(query, (plate_number, event_type))
            self.connection.commit()
            cursor.close()
            print(f"   Event: {event_type} for {plate_number}")
        except Exception as e:
            print(f"   Database fejl (event): {e}")
    
    def update_parking_spots(self, available_spots):
        """Opdater ledige pladser i databasen"""
        try:
            cursor = self.connection.cursor()
            
            # Opdater alle pladser
            for spot_num in range(1, 201):  # 15 pladser totalt
                is_occupied = spot_num > available_spots
                plate = f"SIM{spot_num:03d}" if is_occupied else None
                
                query = """
                INSERT INTO parking_spots (spot_number, is_occupied, plate_number) 
                VALUES (%s, %s, %s)
                ON DUPLICATE KEY UPDATE 
                is_occupied = VALUES(is_occupied), 
                plate_number = VALUES(plate_number),
                last_updated = NOW()
                """
                cursor.execute(query, (spot_num, is_occupied, plate))
            
            self.connection.commit()
            cursor.close()
        except Exception as e:
            print(f"   Database fejl (spots): {e}")