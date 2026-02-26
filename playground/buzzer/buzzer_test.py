# buzzer_test.py
"""
Buzzer control for Orange Pi 5 Ultra
Buzzer connected to GPIO1_A6 (chip1, line6)
"""
import time

#=================================================================
# Custom System
#=================================================================
from remote.buzzer.opi_gpio import Pin

# Your buzzer pin
BUZZER_PIN = (1, 7)  # GPIO1_A6

class Buzzer:
    """Simple buzzer class compatible with robot-hat"""
    
    def __init__(self, pin):
        """Initialize buzzer on given pin"""
        if isinstance(pin, tuple):
            self.pin = Pin(pin, Pin.OUT)
        else:
            self.pin = pin
        self.pin.off()
    
    def on(self):
        """Turn buzzer on (constant tone)"""
        self.pin.on()
    
    def off(self):
        """Turn buzzer off"""
        self.pin.off()
    
    def beep(self, duration=0.1, frequency=2000):
        """
        Make a beep sound at specified frequency.
        
        Args:
            duration: Length of beep in seconds
            frequency: Frequency in Hz (default 2000Hz)
        """
        half_period = 1.0 / (2.0 * frequency)
        cycles = int(frequency * duration)
        
        for _ in range(cycles):
            self.pin.on()
            time.sleep(half_period)
            self.pin.off()
            time.sleep(half_period)
    
    def play(self, note_frequency, duration=0.2):
        """
        Play a musical note.
        
        Common note frequencies:
        C4=262, D4=294, E4=330, F4=349, G4=392, A4=440, B4=494
        C5=523, D5=587, E5=659, F5=698, G5=784, A5=880, B5=988
        """
        self.beep(duration, note_frequency)
    
    def melody(self, notes, tempo=1.0):
        """
        Play a melody.
        
        Args:
            notes: List of (frequency, duration) tuples
            tempo: Speed multiplier (1.0=normal, 2.0=double speed)
        """
        for freq, duration in notes:
            if freq > 0:
                self.beep(duration / tempo, freq)
            else:
                # Rest (frequency = 0)
                time.sleep(duration / tempo)
            time.sleep(0.02 / tempo)  # Small gap between notes
    
    def close(self):
        """Clean up"""
        self.off()
        self.pin.close()


# Predefined melodies
MELODIES = {
    'startup': [
        (523, 0.1),  # C
        (659, 0.1),  # E
        (784, 0.2),  # G
    ],
    'success': [
        (659, 0.1),  # E
        (784, 0.1),  # G
        (1047, 0.2), # C (high)
    ],
    'error': [
        (392, 0.1),  # G
        (330, 0.1),  # E
        (262, 0.2),  # C
    ],
    'alarm': [
        (880, 0.2),  # A
        (0, 0.1),    # Rest
        (880, 0.2),  # A
        (0, 0.1),    # Rest
        (880, 0.2),  # A
    ],
    'mario': [
        (659, 0.15),  # E
        (659, 0.15),  # E
        (0, 0.15),    # Rest
        (659, 0.15),  # E
        (0, 0.15),    # Rest
        (523, 0.15),  # C
        (659, 0.15),  # E
        (0, 0.15),    # Rest
        (784, 0.3),   # G
    ],
    'scale': [
        (262, 0.2),  # C
        (294, 0.2),  # D
        (330, 0.2),  # E
        (349, 0.2),  # F
        (392, 0.2),  # G
        (440, 0.2),  # A
        (494, 0.2),  # B
        (523, 0.2),  # C (high)
    ]
}


def demo():
    """Demo all buzzer functions"""
    buzzer = Buzzer(BUZZER_PIN)
    
    print("Buzzer Demo - GPIO1_A6 (chip1, line6)")
    print("=" * 50)
    
    print("\n1. Single beep...")
    buzzer.beep(0.2)
    time.sleep(0.5)
    
    print("2. Three short beeps...")
    for i in range(3):
        buzzer.beep(0.1)
        time.sleep(0.2)
    time.sleep(0.5)
    
    print("3. Low frequency beep (500Hz)...")
    buzzer.beep(0.3, 500)
    time.sleep(0.5)
    
    print("4. High frequency beep (4000Hz)...")
    buzzer.beep(0.3, 4000)
    time.sleep(0.5)
    
    print("5. Startup melody...")
    buzzer.melody(MELODIES['startup'])
    time.sleep(0.5)
    
    print("6. Success melody...")
    buzzer.melody(MELODIES['success'])
    time.sleep(0.5)
    
    print("7. Error melody...")
    buzzer.melody(MELODIES['error'])
    time.sleep(0.5)
    
    print("8. Alarm...")
    buzzer.melody(MELODIES['alarm'])
    time.sleep(0.5)
    
    print("9. Mario theme...")
    buzzer.melody(MELODIES['mario'])
    time.sleep(0.5)
    
    print("10. Musical scale...")
    buzzer.melody(MELODIES['scale'])
    
    buzzer.close()
    print("\n✓ Demo complete!")


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        # Play specific melody
        melody_name = sys.argv[1].lower()
        if melody_name in MELODIES:
            buzzer = Buzzer(BUZZER_PIN)
            print(f"Playing {melody_name}...")
            buzzer.melody(MELODIES[melody_name])
            buzzer.close()
        else:
            print(f"Unknown melody: {melody_name}")
            print(f"Available: {', '.join(MELODIES.keys())}")
    else:
        # Run full demo
        demo()
