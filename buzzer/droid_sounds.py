# droid_sounds.py
"""
Star Wars Droid-style sounds for buzzer
Each letter gets a unique beep pattern inspired by R2-D2 and BB-8
"""
import time
import random

#=================================================================
# Custom System
#=================================================================
from remote.buzzer.buzzer_test import Buzzer, BUZZER_PIN

# Droid sound alphabet - each letter is (frequency, duration) tuples
# Inspired by droid communication patterns: chirps, beeps, whistles
DROID_ALPHABET = {
    'A': [(880, 0.08), (1100, 0.06)],  # Quick rising chirp
    'B': [(700, 0.12), (700, 0.08)],   # Double low beep
    'C': [(1200, 0.05), (900, 0.05), (600, 0.05)],  # Descending trill
    'D': [(500, 0.15)],  # Deep boop
    'E': [(1500, 0.06), (1500, 0.06), (1500, 0.06)],  # Triple high chirp
    'F': [(800, 0.08), (1000, 0.08), (1200, 0.08)],  # Rising sequence
    'G': [(1000, 0.12), (800, 0.08)],  # Down sweep
    'H': [(600, 0.06), (600, 0.06), (600, 0.06), (600, 0.06)],  # Rapid beeps
    'I': [(1400, 0.10)],  # Single high tone
    'J': [(900, 0.08), (700, 0.08), (500, 0.12)],  # Sliding down
    'K': [(750, 0.08), (1250, 0.08), (750, 0.08)],  # Up-down pattern
    'L': [(1100, 0.06), (1300, 0.06), (1500, 0.06), (1700, 0.06)],  # Climbing chirps
    'M': [(650, 0.18)],  # Medium low sustained
    'N': [(950, 0.08), (950, 0.08)],  # Two identical beeps
    'O': [(1600, 0.12), (1200, 0.08)],  # High to mid drop
    'P': [(800, 0.06), (1100, 0.06), (800, 0.06), (1100, 0.06)],  # Alternating
    'Q': [(1300, 0.15), (400, 0.08)],  # High then very low
    'R': [(850, 0.08), (1050, 0.08), (850, 0.08)],  # Warble
    'S': [(1450, 0.05), (1350, 0.05), (1250, 0.05), (1150, 0.05)],  # Quick descent
    'T': [(720, 0.12)],  # Single mid tone
    'U': [(500, 0.08), (800, 0.08), (1100, 0.10)],  # Rising sweep
    'V': [(1000, 0.08), (600, 0.08), (1000, 0.08)],  # V-shaped pattern
    'W': [(550, 0.08), (900, 0.08), (550, 0.08), (900, 0.08)],  # Wave pattern
    'X': [(1400, 0.06), (800, 0.06), (1400, 0.06), (800, 0.06)],  # Cross pattern
    'Y': [(1200, 0.08), (900, 0.12)],  # Question-like fall
    'Z': [(1500, 0.05), (1000, 0.05), (1500, 0.05), (1000, 0.05), (500, 0.08)],  # Zigzag
    
    # Punctuation and special characters
    ' ': [(0, 0.15)],  # Space = silence
    '.': [(400, 0.20)],  # Period = low definitive tone
    '!': [(1800, 0.08), (1600, 0.08), (1800, 0.10)],  # Excited chirps
    '?': [(800, 0.08), (1200, 0.12)],  # Rising question tone
    ',': [(0, 0.10)],  # Comma = short pause
    '-': [(700, 0.08), (700, 0.08)],  # Dash = steady beeps
    
    # Numbers get simple patterns
    '0': [(600, 0.15)],
    '1': [(700, 0.08)],
    '2': [(800, 0.08), (800, 0.08)],
    '3': [(900, 0.08), (900, 0.08), (900, 0.08)],
    '4': [(1000, 0.06)] * 4,
    '5': [(1100, 0.06)] * 5,
    '6': [(1200, 0.05)] * 6,
    '7': [(1300, 0.05)] * 7,
    '8': [(1400, 0.04)] * 8,
    '9': [(1500, 0.04)] * 9,
}


class DroidSpeaker:
    """Droid-style text-to-beep converter"""
    
    def __init__(self, pin=BUZZER_PIN, speed=1.0):
        print("CTOR DroidSpeaker")
        """
        Initialize droid speaker.
        
        Args:
            pin: GPIO pin tuple or Pin object
            speed: Speed multiplier (1.0=normal, 2.0=faster, 0.5=slower)
        """
        self.buzzer = Buzzer(pin)
        self.speed = speed
    
    def say(self, text, speed=None):
        """
        Convert text to droid sounds.
        
        Args:
            text: String to convert to sounds
            speed: Override default speed for this message
        """
        if speed is None:
            speed = self.speed
        
        text = text.upper()
        
        for char in text:
            if char in DROID_ALPHABET:
                pattern = DROID_ALPHABET[char]
                self._play_pattern(pattern, speed)
                # Small gap between letters
                time.sleep(0.05 / speed)
            else:
                # Unknown character = short silence
                time.sleep(0.1 / speed)

    def _play_pattern(self, pattern, speed):
        """Play a sound pattern"""
        for freq, duration in pattern:
            if freq > 0:
                self.buzzer.beep(duration / speed, freq)
            else:
                # Rest/silence
                time.sleep(duration / speed)
            time.sleep(0.01 / speed)  # Tiny gap between notes in pattern
    
    def excited(self, text):
        """Say something excitedly (faster, higher pitch)"""
        text = text.upper()
        for char in text:
            if char in DROID_ALPHABET:
                pattern = DROID_ALPHABET[char]
                # Increase frequency by 20% and speed by 50%
                excited_pattern = [(int(f * 1.2), d * 0.7) for f, d in pattern if f > 0]
                self._play_pattern(excited_pattern, 1.5)
                time.sleep(0.03)
    
    def worried(self, text):
        """Say something worriedly (wavering, slower)"""
        text = text.upper()
        for char in text:
            if char in DROID_ALPHABET:
                pattern = DROID_ALPHABET[char]
                # Add slight frequency wobble and slow down
                worried_pattern = []
                for f, d in pattern:
                    if f > 0:
                        worried_pattern.append((int(f * 0.95), d * 1.2))
                        worried_pattern.append((int(f * 1.05), d * 0.3))
                self._play_pattern(worried_pattern, 0.8)
                time.sleep(0.08)
    
    def random_droid_sound(self, complexity=3):
        """Generate a random droid sound"""
        pattern = []
        for _ in range(complexity):
            freq = random.randint(400, 1800)
            duration = random.uniform(0.05, 0.15)
            pattern.append((freq, duration))
        self._play_pattern(pattern, 1.0)
    
    def affirmative(self):
        """Affirmative beep (like R2's happy chirp)"""
        pattern = [(800, 0.08), (1200, 0.10), (1000, 0.12)]
        self._play_pattern(pattern, 1.0)
    
    def negative(self):
        """Negative beep (like R2's sad sound)"""
        pattern = [(1000, 0.08), (800, 0.10), (600, 0.15)]
        self._play_pattern(pattern, 1.0)
    
    def alert(self):
        """Alert sound"""
        pattern = [(1500, 0.08), (1500, 0.08), (1500, 0.08)]
        self._play_pattern(pattern, 1.2)
    
    def thinking(self):
        """Thinking/processing sound"""
        pattern = [(700, 0.06), (900, 0.06), (700, 0.06), (900, 0.06), (700, 0.08)]
        self._play_pattern(pattern, 1.0)
    
    def close(self):
        """Clean up"""
        self.buzzer.close()


def demo():
    """Demo the droid speaker"""
    droid = DroidSpeaker(speed=1.0)
    
    print("Droid Sound Demo")
    print("=" * 60)
    
    print("\n1. Saying 'HELLO'...")
    droid.say("HELLO")
    time.sleep(0.5)
    
    print("2. Saying 'R2D2'...")
    droid.say("R2D2")
    time.sleep(0.5)
    
    print("3. Saying 'BB8'...")
    droid.say("BB8")
    time.sleep(0.5)
    
    print("4. Alphabet (A-Z)...")
    droid.say("ABCDEFGHIJKLMNOPQRSTUVWXYZ", speed=1.2)
    time.sleep(0.5)
    
    print("5. Saying 'HELLO WORLD' excited...")
    droid.excited("HELLO WORLD")
    time.sleep(0.5)
    
    print("6. Saying 'OH NO' worried...")
    droid.worried("OH NO")
    time.sleep(0.5)
    
    print("7. Affirmative beep...")
    droid.affirmative()
    time.sleep(0.3)
    
    print("8. Negative beep...")
    droid.negative()
    time.sleep(0.3)
    
    print("9. Alert beep...")
    droid.alert()
    time.sleep(0.3)
    
    print("10. Thinking beep...")
    droid.thinking()
    time.sleep(0.3)
    
    print("11. Random droid sounds...")
    for i in range(3):
        droid.random_droid_sound(complexity=random.randint(2, 5))
        time.sleep(0.3)
    
    print("12. Saying 'GOODBYE'...")
    droid.say("GOODBYE")
    
    droid.close()
    print("\n✓ Demo complete!")


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        # Say the command line argument
        message = ' '.join(sys.argv[1:])
        droid = DroidSpeaker()
        print(f"Droid says: '{message}'")
        droid.say(message)
        droid.close()
    else:
        # Run demo
        demo()
