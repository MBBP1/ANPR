import paho.mqtt.client as mqtt
import json
from datetime import datetime

class MQTTPublisher:
    def __init__(self, config):
        self.config = config
        self.client = mqtt.Client(client_id=config['mqtt']['client_id'])
        self.connect()
    
    def connect(self):
        """Forbind til MQTT broker"""
        try:
            self.client.connect(
                self.config['mqtt']['broker'],
                int(self.config['mqtt']['port'])
            )
            self.client.loop_start()
            print(" Forbundet til MQTT broker")
        except Exception as e:
            print(f" MQTT fejl: {e}")
    
    def publish_available_spots(self, available_spots):
        """Publicer antal ledige pladser"""
        try:
            message = {
                "available_spots": available_spots,
                "total_spots": 200,
                "timestamp": datetime.now().isoformat()
            }
            self.client.publish(
                self.config['mqtt']['topics']['available_spots'],
                json.dumps(message)
            )
            print(f"   MQTT: Ledige pladser = {available_spots}")
        except Exception as e:
            print(f"   MQTT publish fejl (spots): {e}")
    
    def parking_event(self, plate_number, event_type):
        """Publicer parkeringsbegivenhed"""
        try:
            message = {
                "plate_number": plate_number,
                "event_type": event_type,
                "timestamp": datetime.now().isoformat()
            }
            self.client.publish(
                "parking/events",
                json.dumps(message)
            )
            print(f"   MQTT: {event_type} - {plate_number}")
        except Exception as e:
            print(f"   MQTT publish fejl (event): {e}")