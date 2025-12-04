# pc-side/src/mqtt_publisher.py

import paho.mqtt.client as mqtt
import json
from datetime import datetime
import ssl
import os

class MQTTPublisher:
    def __init__(self, config):
        self.config = config
        self.client = mqtt.Client(client_id=config['mqtt']['client_id'])
        self.setup_tls()
        self.connect()
    
    def setup_tls(self):
        """Opsæt TLS for MQTT forbindelse"""
        try:
            mqtt_config = self.config['mqtt']
            
            # Hent TLS konfiguration - brug get() for at håndtere manglende værdier
            tls_config = mqtt_config.get('tls', {})
            ca_cert = tls_config.get('ca_cert', 'config/ssl/ca.crt')
            client_cert = tls_config.get('client_cert')
            client_key = tls_config.get('client_key')
            
            # Opsæt TLS - kun CA certifikat er påkrævet
            self.client.tls_set(
                ca_certs=ca_cert,
                certfile=client_cert if client_cert and os.path.exists(client_cert) else None,
                keyfile=client_key if client_key and os.path.exists(client_key) else None,
                cert_reqs=ssl.CERT_REQUIRED,
                tls_version=ssl.PROTOCOL_TLSv1_2
            )
            
            # Slå hostname verification fra for localhost
            self.client.tls_insecure_set(True)
            
            print(" TLS konfigureret for MQTT")
            
        except Exception as e:
            print(f" Fejl ved TLS opsætning: {e}")
    
    def connect(self):
        """Forbind til MQTT broker med TLS"""
        try:
            self.client.connect(
                self.config['mqtt']['broker'],
                int(self.config['mqtt']['port'])
            )
            self.client.loop_start()
            print(" Forbundet til MQTT broker med TLS")
        except Exception as e:
            print(f" MQTT TLS forbindelsesfejl: {e}")
    
    def publish_available_spots(self, available_spots):
        """Publicer antal ledige pladser"""
        try:
            message = {
                "available_spots": available_spots,
                "total_spots": 200,
                "timestamp": datetime.now().isoformat()
            }
            result = self.client.publish(
                self.config['mqtt']['topics']['available_spots'],
                json.dumps(message)
            )
            if result.rc == mqtt.MQTT_ERR_SUCCESS:
                print(f"   MQTT: Ledige pladser = {available_spots}")
            else:
                print(f"   MQTT publish fejl: {result.rc}")
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
            result = self.client.publish(
                "parking/events",
                json.dumps(message)
            )
            if result.rc == mqtt.MQTT_ERR_SUCCESS:
                print(f"   MQTT: {event_type} - {plate_number}")
            else:
                print(f"   MQTT publish fejl: {result.rc}")
        except Exception as e:
            print(f"   MQTT publish fejl (event): {e}")

    def disconnect(self):
        """Afslut forbindelse korrekt"""
        self.client.loop_stop()
        self.client.disconnect()