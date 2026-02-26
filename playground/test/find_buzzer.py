# find_buzzer.py
"""
Buzzer Pin Finder for Orange Pi 5 Ultra
This script will test each GPIO pin by toggling it rapidly to make a buzzer beep.
When you hear the beep, note the GPIO name!
"""

from opi_gpio import Pin
import time
import sys

# All available GPIO pins from your test results
# Format: (chip, line, "GPIO_NAME")
AVAILABLE_PINS = [
    (0, 1, "GPIO0_A1"), (0, 2, "GPIO0_A2"), (0, 3, "GPIO0_A3"), (0, 4, "GPIO0_A4"),
    (0, 5, "GPIO0_A5"), (0, 6, "GPIO0_A6"), (0, 7, "GPIO0_A7"), (0, 8, "GPIO0_B0"),
    (0, 9, "GPIO0_B1"), (0, 10, "GPIO0_B2"), (0, 11, "GPIO0_B3"), (0, 12, "GPIO0_B4"),
    (0, 13, "GPIO0_B5"), (0, 14, "GPIO0_B6"), (0, 15, "GPIO0_B7"), (0, 16, "GPIO0_C0"),
    (0, 17, "GPIO0_C1"), (0, 18, "GPIO0_C2"), (0, 19, "GPIO0_C3"), (0, 20, "GPIO0_C4"),
    (0, 23, "GPIO0_C7"), (0, 24, "GPIO0_D0"), (0, 25, "GPIO0_D1"), (0, 26, "GPIO0_D2"),
    (0, 28, "GPIO0_D4"), (0, 29, "GPIO0_D5"), (0, 30, "GPIO0_D6"), (0, 31, "GPIO0_D7"),
    
    (1, 0, "GPIO1_A0"), (1, 1, "GPIO1_A1"), (1, 2, "GPIO1_A2"), (1, 3, "GPIO1_A3"),
    (1, 4, "GPIO1_A4"), (1, 5, "GPIO1_A5"), (1, 6, "GPIO1_A6"), (1, 7, "GPIO1_A7"),
    (1, 8, "GPIO1_B0"), (1, 9, "GPIO1_B1"), (1, 10, "GPIO1_B2"), (1, 11, "GPIO1_B3"),
    (1, 12, "GPIO1_B4"), (1, 13, "GPIO1_B5"), (1, 14, "GPIO1_B6"), (1, 15, "GPIO1_B7"),
    (1, 16, "GPIO1_C0"), (1, 17, "GPIO1_C1"), (1, 18, "GPIO1_C2"), (1, 19, "GPIO1_C3"),
    (1, 20, "GPIO1_C4"), (1, 21, "GPIO1_C5"), (1, 22, "GPIO1_C6"), (1, 23, "GPIO1_C7"),
    (1, 24, "GPIO1_D0"), (1, 25, "GPIO1_D1"), (1, 26, "GPIO1_D2"), (1, 27, "GPIO1_D3"),
    (1, 28, "GPIO1_D4"), (1, 29, "GPIO1_D5"), (1, 30, "GPIO1_D6"), (1, 31, "GPIO1_D7"),
    
    (2, 0, "GPIO2_A0"), (2, 1, "GPIO2_A1"), (2, 2, "GPIO2_A2"), (2, 3, "GPIO2_A3"),
    (2, 4, "GPIO2_A4"), (2, 5, "GPIO2_A5"), (2, 6, "GPIO2_A6"), (2, 7, "GPIO2_A7"),
    (2, 8, "GPIO2_B0"), (2, 9, "GPIO2_B1"), (2, 10, "GPIO2_B2"), (2, 11, "GPIO2_B3"),
    (2, 12, "GPIO2_B4"), (2, 13, "GPIO2_B5"), (2, 15, "GPIO2_B7"), (2, 16, "GPIO2_C0"),
    (2, 17, "GPIO2_C1"), (2, 18, "GPIO2_C2"), (2, 19, "GPIO2_C3"), (2, 20, "GPIO2_C4"),
    (2, 22, "GPIO2_C6"), (2, 23, "GPIO2_C7"), (2, 24, "GPIO2_D0"), (2, 25, "GPIO2_D1"),
    (2, 26, "GPIO2_D2"), (2, 27, "GPIO2_D3"), (2, 28, "GPIO2_D4"), (2, 29, "GPIO2_D5"),
    (2, 30, "GPIO2_D6"), (2, 31, "GPIO2_D7"),
    
    (3, 0, "GPIO3_A0"), (3, 1, "GPIO3_A1"), (3, 2, "GPIO3_A2"), (3, 3, "GPIO3_A3"),
    (3, 4, "GPIO3_A4"), (3, 5, "GPIO3_A5"), (3, 6, "GPIO3_A6"), (3, 7, "GPIO3_A7"),
    (3, 8, "GPIO3_B0"), (3, 9, "GPIO3_B1"), (3, 10, "GPIO3_B2"), (3, 11, "GPIO3_B3"),
    (3, 12, "GPIO3_B4"), (3, 13, "GPIO3_B5"), (3, 14, "GPIO3_B6"), (3, 15, "GPIO3_B7"),
    (3, 16, "GPIO3_C0"), (3, 17, "GPIO3_C1"), (3, 18, "GPIO3_C2"), (3, 19, "GPIO3_C3"),
    (3, 20, "GPIO3_C4"), (3, 21, "GPIO3_C5"), (3, 22, "GPIO3_C6"), (3, 23, "GPIO3_C7"),
    (3, 24, "GPIO3_D0"), (3, 25, "GPIO3_D1"), (3, 30, "GPIO3_D6"), (3, 31, "GPIO3_D7"),
    
    (4, 0, "GPIO4_A0"), (4, 1, "GPIO4_A1"), (4, 2, "GPIO4_A2"), (4, 3, "GPIO4_A3"),
    (4, 4, "GPIO4_A4"), (4, 5, "GPIO4_A5"), (4, 6, "GPIO4_A6"), (4, 7, "GPIO4_A7"),
    (4, 11, "GPIO4_B3"), (4, 12, "GPIO4_B4"), (4, 13, "GPIO4_B5"), (4, 15, "GPIO4_B7"),
    (4, 16, "GPIO4_C0"), (4, 17, "GPIO4_C1"), (4, 19, "GPIO4_C3"), (4, 22, "GPIO4_C6"),
    (4, 23, "GPIO4_C7"), (4, 24, "GPIO4_D0"), (4, 25, "GPIO4_D1"), (4, 26, "GPIO4_D2"),
    (4, 27, "GPIO4_D3"), (4, 28, "GPIO4_D4"), (4, 29, "GPIO4_D5"), (4, 30, "GPIO4_D6"),
    (4, 31, "GPIO4_D7"),
]


def beep_pin(chip, line, name, frequency=2000, duration=0.5):
    """
    Toggle a pin rapidly to create a beep sound on a buzzer.
    
    Args:
        chip: GPIO chip number
        line: GPIO line number
        name: GPIO name for display
        frequency: Beep frequency in Hz (2000 = 2kHz, good for buzzers)
        duration: How long to beep in seconds
    """
    try:
        pin = Pin((chip, line), Pin.OUT)
        
        # Calculate timing for desired frequency
        # Period = 1/frequency, half_period for square wave
        half_period = 1.0 / (2.0 * frequency)
        
        # Calculate number of cycles
        cycles = int(frequency * duration)
        
        # Generate square wave
        for _ in range(cycles):
            pin.on()
            time.sleep(half_period)
            pin.off()
            time.sleep(half_period)
        
        pin.close()
        return True
        
    except Exception as e:
        return False


def test_specific_pin(gpio_name):
    """Test a specific pin by name"""
    for chip, line, name in AVAILABLE_PINS:
        if name.upper() == gpio_name.upper():
            print(f"\nTesting {name}...")
            print("Listen for beep...")
            beep_pin(chip, line, name, frequency=2000, duration=1.0)
            return True
    
    print(f"GPIO {gpio_name} not found in available pins")
    return False


def scan_all_pins(start_from=0, delay=2.0):
    """
    Scan through all available pins and beep each one.
    
    Args:
        start_from: Index to start from (useful if you want to resume)
        delay: Delay between testing each pin
    """
    print("=" * 80)
    print("BUZZER PIN FINDER")
    print("=" * 80)
    print(f"\nTesting {len(AVAILABLE_PINS)} available GPIO pins...")
    print("Listen for your buzzer to beep!")
    print("Press Ctrl+C to stop\n")
    print(f"Delay between pins: {delay} seconds")
    print("=" * 80)
    
    try:
        for i, (chip, line, name) in enumerate(AVAILABLE_PINS[start_from:], start=start_from):
            print(f"\n[{i+1}/{len(AVAILABLE_PINS)}] Testing {name} (chip{chip} line{line})...")
            print("    🔊 BEEPING NOW...")
            
            beep_pin(chip, line, name, frequency=2000, duration=0.5)
            
            print(f"    If you heard a beep, your buzzer is on: {name}")
            print(f"    Use: Pin(({chip}, {line})) or Pin('{name}')")
            
            if i < len(AVAILABLE_PINS) - 1:
                print(f"    Waiting {delay} seconds before next pin...")
                time.sleep(delay)
    
    except KeyboardInterrupt:
        print(f"\n\nStopped at index {i}")
        print(f"To resume from here, run: python find_buzzer.py --resume {i+1}")


def test_range(start_gpio, end_gpio):
    """Test a range of pins by GPIO name"""
    testing = False
    for chip, line, name in AVAILABLE_PINS:
        if name == start_gpio.upper():
            testing = True
        
        if testing:
            print(f"\nTesting {name}...")
            beep_pin(chip, line, name, frequency=2000, duration=0.5)
            time.sleep(2)
        
        if name == end_gpio.upper():
            break


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Find which GPIO pin your buzzer is connected to")
    parser.add_argument('--pin', type=str, help='Test a specific GPIO pin (e.g., GPIO1_A0)')
    parser.add_argument('--resume', type=int, help='Resume scanning from index N')
    parser.add_argument('--delay', type=float, default=2.0, help='Delay between pins in seconds (default: 2.0)')
    parser.add_argument('--range', nargs=2, metavar=('START', 'END'), 
                       help='Test range of pins (e.g., --range GPIO1_A0 GPIO1_A7)')
    parser.add_argument('--chip', type=int, help='Only test pins on specific chip (0-4)')
    
    args = parser.parse_args()
    
    # Check if running as root
    import os
    if os.geteuid() != 0:
        print("WARNING: Not running as root. Run with sudo for best results.")
        print("sudo python find_buzzer.py\n")
    
    if args.pin:
        # Test specific pin
        test_specific_pin(args.pin)
    
    elif args.range:
        # Test range of pins
        test_range(args.range[0], args.range[1])
    
    elif args.chip is not None:
        # Test only pins on specific chip
        filtered_pins = [(c, l, n) for c, l, n in AVAILABLE_PINS if c == args.chip]
        print(f"Testing {len(filtered_pins)} pins on chip{args.chip}...")
        AVAILABLE_PINS = filtered_pins
        scan_all_pins(start_from=0, delay=args.delay)
    
    else:
        # Scan all pins
        start = args.resume if args.resume else 0
        scan_all_pins(start_from=start, delay=args.delay)
