# pc-side/src/database_handler.py
import mysql.connector

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
    
    def insert_license_plate(self, plate_number):
        """Indsæt nummerplade i databasen (simpel version)"""
        try:
            cursor = self.connection.cursor()
            
            # Indsæt direkte - lad database håndtere duplikater hvis vi har UNIQUE constraint
            query = "INSERT INTO license_plates (plate_number) VALUES (%s)"
            cursor.execute(query, (plate_number,))
            self.connection.commit()
            cursor.close()
            
            print(f"   Database: Nummerplade gemt: {plate_number}")
            return True
            
        except mysql.connector.IntegrityError:
            # Hvis nummerpladen allerede findes (UNIQUE constraint)
            print(f"   Database: Nummerplade eksisterer allerede: {plate_number}")
            return True
            
        except Exception as e:
            print(f"   Database fejl: {e}")
            return False
    
    def close(self):
        """Luk database forbindelsen"""
        if self.connection:
            self.connection.close()
            print(" Database forbindelse lukket")