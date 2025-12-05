import RPi.GPIO as GPIO
import time

class GateController:
    def __init__(self, config):
        self.config = config
        self.servo_pin = config.get('servo', {}).get('pin', 18)
        self.open_angle = config.get('servo', {}).get('open_angle', 90)
        self.close_angle = config.get('servo', {}).get('close_angle', 0)
        self.open_time = config.get('gate', {}).get('open_time', 3)
        
        # Setup GPIO
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(self.servo_pin, GPIO.OUT)
        
        # Setup PWM for servo
        self.pwm = GPIO.PWM(self.servo_pin, 50)  # 50Hz frequency
        self.pwm.start(0)
        
        # Start med lukket bom
        self.set_angle(self.close_angle)
        print(" Gate controller initialiseret - bom lukket")
    
    def set_angle(self, angle):
        """Sæt servo vinkel (0-180 grader)"""
        duty = angle / 18 + 2
        GPIO.output(self.servo_pin, True)
        self.pwm.ChangeDutyCycle(duty)
        time.sleep(0.3)  # Vent på at servo når position
        GPIO.output(self.servo_pin, False)
        self.pwm.ChangeDutyCycle(0)
        
    
    def open_gate(self):
        """Åbn bom i den angivne tid"""
        print(" Åbner bom...")
        self.set_angle(self.open_angle)
        time.sleep(self.open_time)
        self.close_gate()
    
    def close_gate(self):
        """Luk bom"""
        print(" Lukker bom...")
        self.set_angle(self.close_angle)
    
    def cleanup(self):
        """Ryd op"""
        self.pwm.stop()
        GPIO.cleanup()
        print(" Gate controller ryddet op")

# Test kode
if __name__ == "__main__":
    config = {
        'servo': {
            'pin': 18,
            'open_angle': 90,
            'close_angle': 0
        },
        'gate': {
            'open_time': 3
        }
    }
    
    gate = GateController(config)
    
    try:
        print("Testing gate...")
        gate.open_gate()
    except KeyboardInterrupt:
        pass
    finally:
        gate.cleanup()









