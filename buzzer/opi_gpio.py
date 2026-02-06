# opi_gpio.py - Orange Pi 5 Ultra GPIO Pin class compatible with robot-hat
"""
GPIO Pin class for Orange Pi 5 Ultra using libgpiod.
Drop-in replacement for robot_hat.Pin class.

Usage:
    from opi_gpio import Pin
    
    # Using tuple format (chip, line)
    pin = Pin((1, 0), Pin.OUT)
    pin.on()
    pin.off()
    
    # Using GPIO name format
    pin = Pin("GPIO1_A0", Pin.OUT)
    pin.value(1)  # Set HIGH
    
    # Reading input
    pin = Pin((1, 5), Pin.IN, pull=Pin.PULL_UP)
    state = pin.value()
"""

import gpiod
from gpiod.line import Direction, Value, Bias
import re


class Pin:
    """GPIO Pin class for Orange Pi 5 Ultra"""
    
    # Pin modes
    OUT = "OUT"
    IN = "IN"
    
    # Pin values
    HIGH = 1
    LOW = 0
    
    # Pull resistor modes
    PULL_UP = "PULL_UP"
    PULL_DOWN = "PULL_DOWN"
    PULL_NONE = "PULL_NONE"
    
    # IRQ modes (for compatibility, not fully implemented)
    IRQ_FALLING = "IRQ_FALLING"
    IRQ_RISING = "IRQ_RISING"
    IRQ_RISING_FALLING = "IRQ_RISING_FALLING"
    
    def __init__(self, pin, mode=None, pull=None):
        """
        Initialize a GPIO pin.
        
        Args:
            pin: Can be:
                 - tuple: (chip_num, line_num) for direct access
                 - str: "GPIOx_yz" format (e.g., "GPIO1_A0")
                 - int: Physical pin number (requires _PIN_MAP configuration)
            mode: Pin.OUT or Pin.IN
            pull: Pin.PULL_UP, Pin.PULL_DOWN, or Pin.PULL_NONE
        """
        self.line_request = None
        self._mode = None
        self._value = 0
        
        # Parse pin specification
        if isinstance(pin, tuple):
            self.chip_num, self.line_num = pin
            self.pin_name = f"GPIO{self.chip_num}_{self._line_to_bank(self.line_num)}"
        elif isinstance(pin, str) and pin.upper().startswith("GPIO"):
            self.chip_num, self.line_num = self._parse_gpio_name(pin)
            self.pin_name = pin.upper()
        elif isinstance(pin, int):
            # For physical pin mapping compatibility
            raise NotImplementedError(
                f"Physical pin numbers not yet mapped. "
                f"Use tuple format: Pin((chip, line)) or GPIO name: Pin('GPIO1_A0')"
            )
        else:
            raise ValueError(
                "Pin must be tuple (chip,line) or GPIO string like 'GPIO1_A0'"
            )
        
        # Open the GPIO chip
        self.chip_path = f'/dev/gpiochip{self.chip_num}'
        try:
            self.chip = gpiod.Chip(self.chip_path)
        except Exception as e:
            raise RuntimeError(f"Failed to open {self.chip_path}: {e}")
        
        # Set initial mode if provided
        if mode is not None:
            self.mode(mode, pull)
    
    @staticmethod
    def _line_to_bank(line):
        """Convert line number to bank notation (e.g., 13 -> B5)"""
        bank = chr(ord('A') + line // 8)
        pin = line % 8
        return f"{bank}{pin}"
    
    @staticmethod
    def _parse_gpio_name(name):
        """Parse GPIO1_B5 into (chip=1, line=13)"""
        match = re.match(r'GPIO(\d+)_([A-D])(\d+)', name.upper())
        if not match:
            raise ValueError(
                f"Invalid GPIO name: {name}. "
                f"Use format GPIOx_yz (e.g., GPIO1_B5)"
            )
        
        chip = int(match.group(1))
        bank = ord(match.group(2)) - ord('A')
        pin = int(match.group(3))
        line = bank * 8 + pin
        
        if chip > 4:
            raise ValueError(f"Invalid chip number {chip}. Must be 0-4")
        if line > 31:
            raise ValueError(f"Invalid line {line}. Must be 0-31")
        
        return chip, line
    
    def mode(self, mode, pull=None):
        """
        Set pin mode.
        
        Args:
            mode: Pin.OUT or Pin.IN
            pull: Pin.PULL_UP, Pin.PULL_DOWN, or Pin.PULL_NONE
        """
        # Release existing line request
        if self.line_request is not None:
            self.line_request.release()
            self.line_request = None
        
        self._mode = mode
        settings = gpiod.LineSettings()
        
        if mode == self.OUT:
            settings.direction = Direction.OUTPUT
            settings.output_value = Value.INACTIVE
        else:  # IN
            settings.direction = Direction.INPUT
            
            # Set pull resistor
            if pull == self.PULL_UP:
                settings.bias = Bias.PULL_UP
            elif pull == self.PULL_DOWN:
                settings.bias = Bias.PULL_DOWN
            else:
                settings.bias = Bias.DISABLED
        
        # Request the line
        try:
            self.line_request = self.chip.request_lines(
                consumer="robot-hat",
                config={self.line_num: settings}
            )
        except Exception as e:
            raise RuntimeError(
                f"Failed to configure {self.pin_name} "
                f"(chip{self.chip_num} line{self.line_num}): {e}"
            )
    
    def value(self, val=None):
        """
        Get or set pin value.
        
        Args:
            val: None to read, 0/1 to write
            
        Returns:
            Current pin value when reading, set value when writing
        """
        if val is None:
            # Read mode
            if self._mode != self.IN:
                self.mode(self.IN)
            return self.line_request.get_value(self.line_num)
        else:
            # Write mode
            if self._mode != self.OUT:
                self.mode(self.OUT)
            self._value = 1 if val else 0
            self.line_request.set_value(
                self.line_num,
                Value.ACTIVE if self._value else Value.INACTIVE
            )
            return self._value
    
    def on(self):
        """Set pin HIGH"""
        self.value(self.HIGH)
    
    def off(self):
        """Set pin LOW"""
        self.value(self.LOW)
    
    def high(self):
        """Set pin HIGH (alias for on)"""
        self.on()
    
    def low(self):
        """Set pin LOW (alias for off)"""
        self.off()
    
    def read(self):
        """Read pin value"""
        return self.value()
    
    def write(self, val):
        """Write pin value"""
        self.value(val)
    
    def toggle(self):
        """Toggle pin state"""
        self.value(0 if self._value else 1)
    
    def dict(self, _dict=None):
        """
        Get/set pin configuration as dict (for robot-hat compatibility).
        
        Args:
            _dict: Dictionary with 'mode' and optionally 'pull'
            
        Returns:
            Current configuration dict
        """
        if _dict is not None:
            mode = _dict.get('mode')
            pull = _dict.get('pull', self.PULL_NONE)
            if mode:
                self.mode(mode, pull)
        
        return {
            'mode': self._mode,
            'value': self._value,
            'chip': self.chip_num,
            'line': self.line_num,
            'name': self.pin_name
        }
    
    def close(self):
        """Release GPIO resources"""
        if self.line_request is not None:
            try:
                self.line_request.release()
                self.line_request = None
            except:
                pass
    
    def __del__(self):
        """Cleanup on deletion"""
        self.close()
    
    def __repr__(self):
        return f"Pin({self.pin_name}, chip{self.chip_num}, line{self.line_num}, mode={self._mode})"
    
    def __str__(self):
        return self.pin_name


# Example usage and testing
if __name__ == "__main__":
    print("Orange Pi 5 Ultra GPIO Pin Test")
    print("=" * 50)
    
    # Test with tuple format
    print("\n1. Testing with tuple format (chip, line):")
    pin1 = Pin((1, 0), Pin.OUT)
    print(f"   Created: {pin1}")
    pin1.on()
    print(f"   Set HIGH")
    pin1.off()
    print(f"   Set LOW")
    pin1.close()
    
    # Test with GPIO name format
    print("\n2. Testing with GPIO name:")
    pin2 = Pin("GPIO1_A1", Pin.OUT)
    print(f"   Created: {pin2}")
    pin2.high()
    print(f"   Set HIGH")
    pin2.low()
    print(f"   Set LOW")
    
    # Test input with pull-up
    print("\n3. Testing input with pull-up:")
    pin3 = Pin((1, 2), Pin.IN, pull=Pin.PULL_UP)
    print(f"   Created: {pin3}")
    val = pin3.read()
    print(f"   Read value: {val}")
    
    # Test toggle
    print("\n4. Testing toggle:")
    pin4 = Pin("GPIO1_A3", Pin.OUT)
    print(f"   Created: {pin4}")
    pin4.on()
    print(f"   Initial: HIGH")
    pin4.toggle()
    print(f"   After toggle: {'HIGH' if pin4._value else 'LOW'}")
    pin4.toggle()
    print(f"   After toggle: {'HIGH' if pin4._value else 'LOW'}")
    
    print("\n✓ All tests passed!")
