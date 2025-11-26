import paho.mqtt.client as mqtt
import json
import time
from display_manager import DisplayManager
from gate_controller import GateController

class MQTTSubscriber:
    def __init__(self, config):
        self.available_spots = 0
        self.last_available_spots = 0
        
        # Initialize display og gate controller
        self.display = DisplayManager(config)
        self.gate_controller = GateController(config)
        
        # MQTT client
        self.client = mqtt.Client(client_id="raspberry_pi")
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message
        
        self.connect()

    def connect(self):
        """Forbind til MQTT broker"""
        try:
            self.client.connect("10.0.0.104", 1883, 60)
            self.client.loop_start()
            print(" Forbundet til MQTT broker")
        except Exception as e:
            print(f" MQTT fejl: {e}")

    def on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            print(" MQTT forbundet")
            client.subscribe("parking/available_spots")
            client.subscribe("parking/events")
            # Vis 0 pladser som start
            self.display.update_parking_display(0)

    def on_message(self, client, userdata, msg):
        if msg.topic == "parking/available_spots":
            payload = json.loads(msg.payload.decode())
            new_available_spots = payload['available_spots']
            
            print(f"Ledige pladser: {new_available_spots}")
            self.display.update_parking_display(new_available_spots)
            
            # Tjek om nogen er kørt UD (flere ledige pladser)
            if new_available_spots > self.available_spots:
                print(" Bil kørte UD - åbner bom!")
                self.gate_controller.open_gate()
            
            self.available_spots = new_available_spots
            
        elif msg.topic == "parking/events":
            payload = json.loads(msg.payload.decode())
            plate = payload['plate_number']
            event = payload['event_type']
            print(f"BEGIVENHED: Bil {plate} - {event}")

    def cleanup(self):
        """Ryd op ved afslutning"""
        self.display.cleanup()
        self.gate_controller.cleanup()
        self.client.loop_stop()
        self.client.disconnect()

if __name__ == "__main__":
    config = {
        'servo': {'pin': 18, 'open_angle': 90, 'close_angle': 0},
        'gate': {'open_time': 3}
    }
    subscriber = MQTTSubscriber(config)
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print(" Stopper...")
        subscriber.cleanup()