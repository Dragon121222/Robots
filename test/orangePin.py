#!/usr/bin/env python3
import gpiod
import time

# Pins you want to test
PINS = [9, 17, 19, 21, 44, 83, 84]

def pin_to_chip(pin_number):
    """Map global pin number to gpiochip path and local line offset"""
    chip_index = pin_number // 32
    line_offset = pin_number % 32
    chip_path = f"/dev/gpiochip{chip_index}"
    return chip_path, line_offset

for pin in PINS:
    chip_path, offset = pin_to_chip(pin)
    print(f"Testing pin {pin} (chip: {chip_path}, offset: {offset})...")

    try:
        chip = gpiod.Chip(chip_path)
    except FileNotFoundError:
        print(f"  ❌ Chip {chip_path} not found")
        continue

    settings = gpiod.LineSettings(
        direction=gpiod.line.Direction.OUTPUT,
        drive=gpiod.line.Drive.PUSH_PULL,
        active_low=False
    )

    config = {offset: settings}

    try:
        line_request = chip.request_lines(config, consumer="test_pin")
        # toggle the pin
        line_request.set_values({offset: gpiod.line.Value.ACTIVE})
        time.sleep(0.2)
        line_request.set_values({offset: gpiod.line.Value.INACTIVE})
        line_request.release()
        chip.close()
        print("  ✅ Success")
    except OSError as e:
        print(f"  ❌ Pin {pin} failed: {e}")
    except Exception as e:
        print(f"  ❌ Unexpected error: {e}")

