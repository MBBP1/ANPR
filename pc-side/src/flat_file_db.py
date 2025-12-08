# pc-side/src/flat_file_db.py
import json
import os
from datetime import datetime

class FlatFileDB:
    def __init__(self, db_file="parked_cars.json"):
        self.db_file = db_file
        self.parked_cars = self.load_data()
    
    def load_data(self):
        """Indlæs data fra JSON fil"""
        try:
            if os.path.exists(self.db_file):
                with open(self.db_file, 'r') as f:
                    data = json.load(f)
                    print(f" 📂 Indlæst {len(data)} parkerede biler fra {self.db_file}")
                    return data
            else:
                print(f" 📂 Ingen eksisterende database - starter med tom liste")
                return []
        except Exception as e:
            print(f" ❌ Fejl ved indlæsning af data: {e}")
            return []
    
    def save_data(self):
        """Gem data til JSON fil"""
        try:
            with open(self.db_file, 'w') as f:
                json.dump(self.parked_cars, f, indent=2)
        except Exception as e:
            print(f" ❌ Fejl ved gemning af data: {e}")
    
    def car_entry(self, plate_number):
        """Registrer indkørsel - tilføj bil til database"""
        if plate_number in self.parked_cars:
            print(f"   ⚠️  Bil {plate_number} er allerede registreret")
            return False
        
        self.parked_cars.append(plate_number)
        self.save_data()
        print(f"   📥 Bil {plate_number} tilføjet til database")
        print(f"      Antal parkerede biler: {len(self.parked_cars)}")
        return True
    
    def car_exit(self, plate_number):
        """Registrer udkørsel - fjern bil fra database"""
        if plate_number in self.parked_cars:
            self.parked_cars.remove(plate_number)
            self.save_data()
            print(f"   📤 Bil {plate_number} fjernet fra database")
            print(f"      Antal parkerede biler: {len(self.parked_cars)}")
            return True
        else:
            print(f"   ⚠️  Bil {plate_number} findes ikke i database")
            return False
    
    def is_car_parked(self, plate_number):
        """Tjek om en bil er registreret som parkeret"""
        return plate_number in self.parked_cars
    
    def get_all_parked_cars(self):
        """Hent liste over alle parkerede biler"""
        return self.parked_cars.copy()
    
    def get_count(self):
        """Hent antal parkerede biler"""
        return len(self.parked_cars)
    
    def clear_all(self):
        """Ryd alle data (til debugging)"""
        self.parked_cars = []
        self.save_data()
        print("   ♻️  Alle data ryddet")