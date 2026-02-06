# Import Pin class
from orangePin import orangePin as Pin

# Create Pin object with numeric pin numbering and default input pullup enabled
d0 = Pin(0, Pin.IN, Pin.PULL_UP)
# Create Pin object with named pin numbering
d1 = Pin('D0')

# read value
value0 = d0.value()
value1 = d1.value()
print(value0, value1)

# write value
d0.value(1) # force input to output
d1.value(0)

# set pin high/low
d0.high()
d1.off()

# set interrupt
led = Pin('LED', Pin.OUT)
switch = Pin('SW', Pin.IN, Pin.PULL_DOWN)
def onPressed(chn):
    led.value(not switch.value())
switch.irq(handler=onPressed, trigger=Pin.IRQ_RISING_FALLING)
