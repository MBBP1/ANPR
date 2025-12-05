# raspberry-pi-side/src/mqtt_subscriber.py
import paho.mqtt.client as mqtt
import json
import time
import ssl
import os
from display_manager import DisplayManager
from gate_controller import GateController  # IMPORT GATE CONTROLLER!

class MQTTSubscriber:
    def __init__(self, config):
        self.available_spots = 0
        
        # Initialize display og gate controller
        self.display = DisplayManager(config)
        self.gate_controller = GateController(config)  # VIGTIGT!
        
        # MQTT client
        self.client = mqtt.Client(client_id="raspberry_pi")
        self.setup_tls(config)
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message
        
        self.connect(config)

    def setup_tls(self, config):
        """Opsæt TLS for MQTT forbindelse"""
        try:
            mqtt_config = config['mqtt']
            
            # Hent TLS konfiguration
            tls_config = mqtt_config.get('tls', {})
            ca_cert = tls_config.get('ca_cert', 'config/ssl/ca.crt')
            client_cert = tls_config.get('client_cert')
            client_key = tls_config.get('client_key')
            
            # Opsæt TLS
            self.client.tls_set(
                ca_certs=ca_cert,
                certfile=client_cert if client_cert and os.path.exists(client_cert) else None,
                keyfile=client_key if client_key and os.path.exists(client_key) else None,
                cert_reqs=ssl.CERT_REQUIRED,
                tls_version=ssl.PROTOCOL_TLSv1_2
            )
            
            # Slå hostname verification fra
            self.client.tls_insecure_set(True)
            
            print(" TLS konfigureret for MQTT Subscriber")
            
        except Exception as e:
            print(f" Fejl ved TLS opsætning: {e}")

    def connect(self, config):
        """Forbind til MQTT broker med TLS"""
        try:
            mqtt_config = config['mqtt']
            self.client.connect(
                mqtt_config['broker'],
                int(mqtt_config['port']),
                60
            )
            self.client.loop_start()
            print(" Forbundet til MQTT broker med TLS")
        except Exception as e:
            print(f" MQTT TLS forbindelsesfejl: {e}")

    def on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            print(" MQTT TLS forbundet succesfuldt")
            # Subscribe til ALLE relevante topics
            client.subscribe("parking/available_spots")
            client.subscribe("parking/events")
            client.subscribe("parking/gate_control")  # VIGTIGT FOR BOM KONTROL!
            
            # Vis 0 pladser som start
            self.display.update_parking_display(0)
            
            print(" Abonnerer på:")
            print("  - parking/available_spots")
            print("  - parking/events")
            print("  - parking/gate_control")
        else:
            print(f" MQTT forbindelsesfejl: {rc}")

    def on_message(self, client, userdata, msg):
        try:
            print(f"\n📨 Modtaget på {msg.topic}")
            
            if msg.topic == "parking/available_spots":
                payload = json.loads(msg.payload.decode())
                new_available_spots = payload['available_spots']
                
                print(f" Ledige pladser: {new_available_spots}")
                self.display.update_parking_display(new_available_spots)
                
                self.available_spots = new_available_spots
                
            elif msg.topic == "parking/events":
                payload = json.loads(msg.payload.decode())
                plate = payload['plate_number']
                event = payload['event_type']
                print(f" BEGIVENHED: Bil {plate} - {event}")
                
            elif msg.topic == "parking/gate_control":  # VIGTIGT!
                payload = json.loads(msg.payload.decode())
                command = payload['command']
                plate = payload.get('plate_number', '')
                
                print(f" GATE KOMMANDO: {command} for {plate}")
                
                if command == "open":
                    print(f"   → Åbner bom for bil {plate}")
                    self.gate_controller.open_gate()
                elif command == "close":
                    print(f"   → Lukker bom")
                    self.gate_controller.close_gate()
                elif command == "test":
                    print(f"   → Test bom")
                    self.gate_controller.open_gate()
                    
        except Exception as e:
            print(f" Fejl ved håndtering af MQTT besked: {e}")

    def cleanup(self):
        """Ryd op ved afslutning"""
        print(" Rydder op...")
        self.display.cleanup()
        self.gate_controller.cleanup()  # VIGTIGT!
        self.client.loop_stop()
        self.client.disconnect()
        print(" Alt ryddet op")