import os
import subprocess

class DisplayManager:
    def __init__(self, config):
        self.available_spots = 0
        self.oled_program_path = "/home/pi/test/ssd1306_linux/ssd1306_bin"
        self.init_display()

    def oled_command(self, args):
        """Kører OLED kommando via C-programmet"""
        if not os.path.exists(self.oled_program_path):
            return None
        cmd = [self.oled_program_path, "-n", "1"] + args
        subprocess.run(cmd, capture_output=True, text=True)

    def oled_clear(self):
        """Ryd OLED skærm"""
        self.oled_command(["-c"])

    def oled_text(self, x, y, text):
        """Vis tekst på OLED skærm"""
        self.oled_command(["-x", str(x), "-y", str(y), "-l", text])

    def init_display(self):
        """Initialiser OLED skærm"""
        try:
            self.oled_command(["-I", "128x64"])
            self.oled_clear()
        except:
            pass

    def update_parking_display(self, available_spots, total_spots=None):
        """Opdater display - KUN antal ledige pladser"""
        self.available_spots = available_spots
        self.oled_clear()

        # Header
        self.oled_text(1, 0, "  === PARKERING ===")

        if available_spots == 0:
            self.oled_text(40, 3, "  FULD")
        else:
            self.oled_text(30, 3, f" {available_spots} LEDIGE")

    def cleanup(self):
        """Ryd op ved afslutning"""
        self.oled_clear()









