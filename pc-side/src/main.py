# pc-side/src/main.py
import yaml
import sys
import os
from database_handler import DatabaseHandler
from mqtt_publisher import MQTTPublisher
from license_plate_recognizer import LicensePlateRecognizer

def load_config():
    """Indlæs YAML konfiguration"""
    try:
        current_dir = os.path.dirname(os.path.abspath(__file__))
        config_path = os.path.join(current_dir, '..', 'config', 'config.yaml')
        config_path = os.path.abspath(config_path)
        
        print(f" Leder efter config: {config_path}")
        
        with open(config_path, 'r', encoding='utf-8') as file:
            config = yaml.safe_load(file)
        
        print(" Konfiguration indlæst")
        return config
    except Exception as e:
        print(f" Fejl ved indlæsning af config: {e}")
        return {}

def main():
    print("=" * 50)
    print(" PARKINGSYSTEM - NUMMERPLADEGENKENDELSE")
    print("=" * 50)
    
    # Load configuration
    config = load_config()
    
    if not config:
        print(" Kunne ikke indlæse konfiguration")
        sys.exit(1)
    
    print(f"\nSystem konfiguration:")
    print(f"  Database: {config['database']['host']}:{config['database']['port']}")
    print(f"  MQTT Broker: {config['mqtt']['broker']}:{config['mqtt']['port']}")
    print(f"  Kamera: Source {config['camera']['source']}")
    
    # Initialize components
    print("\nInitialiserer komponenter...")
    db_handler = DatabaseHandler(config)
    mqtt_publisher = MQTTPublisher(config)
    plate_recognizer = LicensePlateRecognizer(config)
    
    # Send initial status til MQTT
    mqtt_publisher.publish_available_spots(plate_recognizer.available_spots)
    
    print("\n" + "=" * 50)
    print(" SYSTEM KLAR")
    print("  - Genkender nummerplader med kamera")
    print("  - Gemmer plader i database")
    print("  - Sender til MQTT broker")
    print("\nTryk Q i kamera-vinduet for at stoppe")
    print("=" * 50 + "\n")
    
    try:
        # Start realtids nummerpladegenkendelse
        # KUN to parametre - ikke available_spots!
        plate_recognizer.run_real_time(
            db_handler=db_handler,
            mqtt_publisher=mqtt_publisher
        )
        
    except KeyboardInterrupt:
        print("\n\n System stoppet af bruger")
    except Exception as e:
        print(f"\n\n Ukendt fejl: {e}")
        import traceback
        traceback.print_exc()
    finally:
        # Cleanup
        print("\nRydder op...")
        mqtt_publisher.disconnect()
        db_handler.close()
        print("System afsluttet")

if __name__ == "__main__":
    main()