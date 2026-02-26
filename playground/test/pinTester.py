# test_all_pins.py
import gpiod
from gpiod.line import Direction, Value
import time
import sys

def test_gpio_line(chip_num, line_num, duration=0.5):
    """
    Test a single GPIO line by trying to configure it as output and toggle it.
    Returns: (success, error_message)
    """
    chip_path = f'/dev/gpiochip{chip_num}'
    
    try:
        chip = gpiod.Chip(chip_path)
        
        # Try to configure as output
        settings = gpiod.LineSettings()
        settings.direction = Direction.OUTPUT
        settings.output_value = Value.INACTIVE
        
        line_request = chip.request_lines(
            consumer="pin-tester",
            config={line_num: settings}
        )
        
        # Try to toggle the pin
        line_request.set_value(line_num, Value.ACTIVE)
        time.sleep(duration)
        line_request.set_value(line_num, Value.INACTIVE)
        
        # Cleanup
        line_request.release()
        
        return True, None
        
    except PermissionError as e:
        return False, "Permission denied (try with sudo)"
    except OSError as e:
        if "Device or resource busy" in str(e):
            return False, "In use by another consumer"
        else:
            return False, str(e)
    except Exception as e:
        return False, str(e)


def get_gpio_info():
    """Parse gpioinfo output to get line status"""
    import subprocess
    
    gpio_info = {}
    
    try:
        result = subprocess.run(['gpioinfo'], capture_output=True, text=True)
        current_chip = None
        
        for line in result.stdout.split('\n'):
            if line.startswith('gpiochip'):
                # Parse: gpiochip0 - 32 lines:
                current_chip = int(line.split('gpiochip')[1].split()[0])
                gpio_info[current_chip] = {}
            elif 'line' in line and current_chip is not None:
                # Parse: line   0:       unnamed       input consumer="bt_default_wake_host"
                parts = line.strip().split()
                if len(parts) >= 2:
                    line_num = int(parts[1].rstrip(':'))
                    
                    # Check if it has a consumer
                    consumer = None
                    if 'consumer=' in line:
                        consumer = line.split('consumer=')[1].split()[0].strip('"')
                    
                    direction = 'input' if 'input' in line else 'output' if 'output' in line else 'unknown'
                    
                    gpio_info[current_chip][line_num] = {
                        'consumer': consumer,
                        'direction': direction
                    }
        
        return gpio_info
    except Exception as e:
        print(f"Warning: Could not parse gpioinfo: {e}")
        return {}


def test_all_gpios(verbose=True, test_duration=0.1):
    """Test all GPIO chips and lines"""
    
    print("=" * 80)
    print("Orange Pi 5 Ultra GPIO Line Tester")
    print("=" * 80)
    print()
    
    # Get existing GPIO info
    print("Scanning GPIO lines...")
    gpio_info = get_gpio_info()
    print()
    
    results = {
        'available': [],
        'in_use': [],
        'failed': []
    }
    
    # Test all chips (0-4, skip chip 5 as it's the power management IC)
    for chip_num in range(5):
        print(f"\n{'=' * 80}")
        print(f"Testing gpiochip{chip_num}")
        print(f"{'=' * 80}\n")
        
        chip_results = {
            'available': 0,
            'in_use': 0,
            'failed': 0
        }
        
        for line_num in range(32):
            # Get info about this line
            info = gpio_info.get(chip_num, {}).get(line_num, {})
            consumer = info.get('consumer')
            direction = info.get('direction', 'unknown')
            
            # Format the GPIO name
            bank = chr(ord('A') + line_num // 8)
            pin = line_num % 8
            gpio_name = f"GPIO{chip_num}_{bank}{pin}"
            
            # Skip if already in use
            if consumer:
                if verbose:
                    print(f"  {gpio_name:12} (chip{chip_num} line{line_num:2d}): "
                          f"SKIP - in use by '{consumer}'")
                results['in_use'].append((chip_num, line_num, gpio_name, consumer))
                chip_results['in_use'] += 1
                continue
            
            # Test the line
            success, error = test_gpio_line(chip_num, line_num, test_duration)
            
            if success:
                status = "✓ AVAILABLE"
                results['available'].append((chip_num, line_num, gpio_name))
                chip_results['available'] += 1
                color = '\033[92m'  # Green
            else:
                status = f"✗ FAILED - {error}"
                results['failed'].append((chip_num, line_num, gpio_name, error))
                chip_results['failed'] += 1
                color = '\033[91m'  # Red
            
            reset = '\033[0m'
            
            if verbose or success:
                print(f"  {gpio_name:12} (chip{chip_num} line{line_num:2d}): {color}{status}{reset}")
        
        # Chip summary
        print(f"\n  Chip{chip_num} Summary: "
              f"{chip_results['available']} available, "
              f"{chip_results['in_use']} in use, "
              f"{chip_results['failed']} failed")
    
    # Overall summary
    print(f"\n\n{'=' * 80}")
    print("OVERALL SUMMARY")
    print(f"{'=' * 80}\n")
    
    print(f"Available GPIO lines: {len(results['available'])}")
    print(f"Lines in use:         {len(results['in_use'])}")
    print(f"Failed to test:       {len(results['failed'])}")
    
    # List available GPIOs in a usable format
    if results['available']:
        print(f"\n\n{'=' * 80}")
        print("AVAILABLE GPIO LINES (ready to use)")
        print(f"{'=' * 80}\n")
        
        print("You can use these in your Pin class with tuple format (chip, line):\n")
        
        for chip, line, name in results['available']:
            print(f"  Pin(({chip}, {line:2d}))  # {name}")
        
        # Also generate PIN_MAP entries
        print(f"\n\nSuggested _PIN_MAP entries (add physical pin numbers):\n")
        print("_PIN_MAP = {")
        for i, (chip, line, name) in enumerate(results['available'][:20], start=1):
            print(f"    # {i}: ({chip}, {line}, '{name}'),  # Physical pin ? - {name}")
        print("}")
    
    return results


if __name__ == "__main__":
    import os
    
    # Check if running as root
    if os.geteuid() != 0:
        print("WARNING: Not running as root. Some GPIO lines may fail with permission errors.")
        print("Run with: sudo python test_all_pins.py")
        print()
        response = input("Continue anyway? (y/n): ")
        if response.lower() != 'y':
            sys.exit(1)
    
    # Run the test
    verbose = '--verbose' in sys.argv or '-v' in sys.argv
    
    print("Starting GPIO test (this will take a few seconds)...")
    print("Each available GPIO will be toggled briefly.")
    print()
    
    results = test_all_gpios(verbose=True, test_duration=0.05)
    
    print(f"\n\nTest complete! Found {len(results['available'])} available GPIO lines.")
