import time

# import Servo
try:
    from robot_hat import Servo
except Exception:
    from robot_hat.servo import Servo

def mk(ch):
    s = Servo(ch)
    def set_angle(a):
        if hasattr(s, "angle"): s.angle(a)
        elif hasattr(s, "write"): s.write(a)
        elif hasattr(s, "set_angle"): s.set_angle(a)
        else: raise RuntimeError("no angle method")
    return set_angle

for ch in range(16):
    print(f"\n== channel {ch} ==")
    set_angle = mk(ch)
    # small wiggle only
    for a in (0, 5, 0):
        set_angle(a)
        time.sleep(0.35)
    time.sleep(0.5)

print("\nDone.")

