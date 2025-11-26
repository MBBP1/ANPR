# simulator for Raspberry Pi parking system

from mqtt_subscriber import MQTTSubscriber
import time
import yaml
import os

def load_config():
    """Indlæs YAML konfiguration fra korrekt sti"""
    try:
        # Find den korrekte sti til config filen
        current_dir = os.path.dirname(os.path.abspath(__file__))
        config_path = os.path.join(current_dir, '..', 'config', 'config.yaml')
        config_path = os.path.abspath(config_path)

        print(f" Leder efter config: {config_path}")

        with open(config_path, 'r') as file:
            config = yaml.safe_load(file)
        print(" Konfiguration indlæst")
        return config
    except Exception as e:
        print(f" Fejl ved indlæsning af config: {e}")
        return {}

def main():
    print(" Raspberry Pi Parkeringssystem startet...")

    # Load configuration
    config = load_config()

    if not config:
        print(" Kunne ikke indlæse konfiguration")
        return

    subscriber = MQTTSubscriber(config)

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n Raspberry Pi stoppet")
        subscriber.cleanup()

if __name__ == "__main__":
    main()