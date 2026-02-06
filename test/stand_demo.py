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


class op:
    def __init__(self,ch):
        self.s = mk(ch)
        self.trim=0
        self.last_val=None

    def write(a):
        self.last_val=a
        self.s(a+self.trim)

hip_fl=None
hip_fr=None
hip_bl=None
hip_br=None

knee_fl=None
knee_fr=None
knee_bl=None
knee_br=None

foot_fl=None
foot_fr=None
foot_bl=None
foot_br=None

def cmd_hips(a):
    hip_fl(a)
    hip_fr(a)
    hip_bl(a)
    hip_br(a)

def cmd_knees(a):
    knee_fl(a)
    knee_fr(a)
    knee_bl(a)
    knee_br(a)

def cmd_feet(a):
    foot_fl(a)
    foot_fr(a)
    foot_bl(a)
    foot_br(a)

hip_fl=mk(0)
hip_fr=mk(1)
hip_bl=mk(2)
hip_br=mk(3)

knee_fl=mk(4)
knee_fr=mk(5)
knee_bl=mk(6)
knee_br=mk(7)

foot_fl=mk(8)
foot_fr=mk(9)
foot_bl=mk(10)
foot_br=mk(11)

cmd_hips(0)
cmd_knees(-40)
cmd_feet(90)

time.sleep(1)

cmd_feet(-80)

for a in range(90):
    cmd_knees(-40+a)
    time.sleep(0.025)

for x in range(10):
    knee_fl(25)
    time.sleep(0.25)
    knee_fl(55)
    time.sleep(0.25)

    knee_fr(25)
    time.sleep(0.25)
    knee_fr(55)
    time.sleep(0.25)

    knee_br(25)
    time.sleep(0.25)
    knee_br(55)
    time.sleep(0.25)

    knee_bl(25)
    time.sleep(0.25)
    knee_bl(55)
    time.sleep(0.25)



time.sleep(5)

for a in range(90):
    cmd_knees(90-40-a)
    time.sleep(0.025)

print("\nDone.")

