
#=======================================================================================#
# Imports                                                                               #
#=======================================================================================#

import time

try:
    from robot_hat import Servo
except Exception:
    from robot_hat.servo import Servo

import sys, termios, tty, select

import yaml
from pathlib import Path

from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

#=======================================================================================#
# Global Vars                                                                           #
#=======================================================================================#

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

#=======================================================================================#
# Servo Commanding                                                                      #
#=======================================================================================#

def mk(ch):
    s = Servo(ch)
    def set_angle(a):
        if hasattr(s, "angle"): s.angle(a)
        elif hasattr(s, "write"): s.write(a)
        elif hasattr(s, "set_angle"): s.set_angle(a)
        else: raise RuntimeError("no angle method")
    return set_angle

#=======================================================================================#
# Default Servo Setup                                                                   #
#=======================================================================================#

"""
Default Leg Motion:
    Hip: 
        Right [-90,60] Left
    Knee:
        Up [-90,90] Down
    Foot:
        Down [-90,80] Up
"""

base_hip_fl=mk(0)
base_hip_fr=mk(1)
base_hip_bl=mk(2)
base_hip_br=mk(3)

base_knee_fl=mk(4)
base_knee_fr=mk(5)
base_knee_bl=mk(6)
base_knee_br=mk(7)

base_foot_fl=mk(8)
base_foot_fr=mk(9)
base_foot_bl=mk(10)
base_foot_br=mk(11)

#=======================================================================================#
# Affine Transform                                                                      #
#=======================================================================================#

current_val_hfl=0
current_val_hfr=0
current_val_hbl=0
current_val_hbr=0

def mkAf_hfl(op,m,b,sleepTrim):
    def set_new_angle(a):
        global current_val_hfl
        diff = current_val_hfl - a
        norm_diff = abs(diff / 150)
        op(a*m+b)
        time.sleep(sleepTrim*norm_diff)
        current_val_hfl = a
    return set_new_angle

def mkAf_hfr(op,m,b,sleepTrim):
    def set_new_angle(a):
        global current_val_hfr
        diff = current_val_hfr - a
        norm_diff = abs(diff / 150)
        op(a*m+b)
        time.sleep(sleepTrim*norm_diff)
        current_val_hfr = a
    return set_new_angle

def mkAf_hbl(op,m,b,sleepTrim):
    def set_new_angle(a):
        global current_val_hbl
        diff = current_val_hbl - a
        norm_diff = abs(diff / 150)
        op(a*m+b)
        time.sleep(sleepTrim*norm_diff)
        current_val_hbl = a
    return set_new_angle

def mkAf_hbr(op,m,b,sleepTrim):
    def set_new_angle(a):
        global current_val_hbr
        diff = current_val_hbr - a
        norm_diff = abs(diff / 150)
        op(a*m+b)
        time.sleep(sleepTrim*norm_diff)
        current_val_hbr = a
    return set_new_angle

current_val_kfl=0
current_val_kfr=0
current_val_kbl=0
current_val_kbr=0

def mkAf_kfl(op,m,b,sleepTrim):
    def set_new_angle(a):
        global current_val_kfl
        diff = current_val_kfl - a
        norm_diff = abs(diff / 180)
        op(a*m+b)
        time.sleep(sleepTrim*norm_diff)
        current_val_kfl = a
    return set_new_angle

def mkAf_kfr(op,m,b,sleepTrim):
    def set_new_angle(a):
        global current_val_kfr
        diff = current_val_kfr - a
        norm_diff = abs(diff / 180)
        op(a*m+b)
        time.sleep(sleepTrim*norm_diff)
        current_val_kfr = a
    return set_new_angle

def mkAf_kbr(op,m,b,sleepTrim):
    def set_new_angle(a):
        global current_val_kbr
        diff = current_val_kbr - a
        norm_diff = abs(diff / 180)
        op(a*m+b)
        time.sleep(sleepTrim*norm_diff)
        current_val_kbr = a
    return set_new_angle

def mkAf_kbl(op,m,b,sleepTrim):
    def set_new_angle(a):
        global current_val_kbl
        diff = current_val_kbl - a
        norm_diff = abs(diff / 180)
        op(a*m+b)
        time.sleep(sleepTrim*norm_diff)
        current_val_kbl = a
    return set_new_angle

current_val_ffl=0
current_val_ffr=0
current_val_fbl=0
current_val_fbr=0

def mkAf_ffl(op,m,b,sleepTrim):
    def set_new_angle(a):
        global current_val_ffl
        diff = current_val_ffl - a
        norm_diff = abs(diff / 170)
        op(a*m+b)
        time.sleep(sleepTrim*norm_diff)
        current_val_ffl = a
    return set_new_angle

def mkAf_ffr(op,m,b,sleepTrim):
    def set_new_angle(a):
        global current_val_ffr
        diff = current_val_ffr - a
        norm_diff = abs(diff / 170)
        op(a*m+b)
        time.sleep(sleepTrim*norm_diff)
        current_val_ffr = a
    return set_new_angle

def mkAf_fbl(op,m,b,sleepTrim):
    def set_new_angle(a):
        global current_val_fbl
        diff = current_val_fbl - a
        norm_diff = abs(diff / 170)
        op(a*m+b)
        time.sleep(sleepTrim*norm_diff)
        current_val_fbl = a
    return set_new_angle

def mkAf_fbr(op,m,b,sleepTrim):
    def set_new_angle(a):
        global current_val_fbr
        diff = current_val_fbr - a
        norm_diff = abs(diff / 170)
        op(a*m+b)
        time.sleep(sleepTrim*norm_diff)
        current_val_fbr = a
    return set_new_angle

def mkAf_kfl_kbr(op1,op2,m1,m2,b1,b2,sleepTrim):
    def set_new_angle(a1,a2):
        global current_val_kfl
        diff1 = current_val_kfl - a1
        global current_val_kbr
        diff2 = current_val_kbr - a2
        norm_diff = max(abs(diff1 / 180), abs(diff2 / 180))
        op1(a1*m1+b1)
        op2(a2*m2+b2)
        time.sleep(sleepTrim*norm_diff)
        current_val_kfl = a1
        current_val_kbr = a2
    return set_new_angle

def mkAf_kfr_kbl(op1,op2,m1,m2,b1,b2,sleepTrim):
    def set_new_angle(a1,a2):
        global current_val_kfr
        diff1 = current_val_kfr - a1
        global current_val_kbl
        diff2 = current_val_kbl - a2
        norm_diff = max(abs(diff1 / 180), abs(diff2 / 180))
        op1(a1*m1+b1)
        op2(a2*m2+b2)
        time.sleep(sleepTrim*norm_diff)
        current_val_kfr = a1
        current_val_kbl = a2
    return set_new_angle

def mkAf_hfl_hfr_hbl_hbr(op1,op2,op3,op4,m1,m2,m3,m4,b1,b2,b3,b4,sleepTrim):
    def set_new_angle(a1,a2,a3,a4):
        global current_val_hfl
        diff1 = current_val_hfl - a1
        global current_val_hfr
        diff2 = current_val_hfr - a2
        global current_val_hbl
        diff3 = current_val_hbl - a3
        global current_val_hbr
        diff4 = current_val_hbr - a4

        norm_diff = max(abs(diff1/150), abs(diff2/150), abs(diff3/150), abs(diff4/150))
        op1(a1*m1+b1)
        op2(a2*m2+b2)
        op3(a3*m3+b3)
        op4(a4*m4+b4)

        time.sleep(sleepTrim*norm_diff)
        current_val_hfl = a1
        current_val_hfr = a2
        current_val_hbl = a3
        current_val_hbr = a4
    return set_new_angle


#=====================================================================================
# Trim
#=====================================================================================

knee_sleep_trim=0.7
foot_sleep_trim=0.7
hip_sleep_trim=0.5

trim_hfl = 5
trim_hfr = 5
trim_hbl = 15
trim_hbr = 5

trim_kfl = 0
trim_kfr = 0
trim_kbl = 0
trim_kbr = 0

trim_ffl = 0
trim_ffr = 0
trim_fbl = 0
trim_fbr = 0

#=======================================================================================#
# Custom Servo Setup                                                                    #
#=======================================================================================#

"""
Motion:
    Hip FL & FR: 
        Left [-60,90] Right
    Hip FR & BL: 
        Right [-90,60] Left
    Knee:
        Down [-90,90] Up
    Foot:
        Down [-90,80] Up
"""

hip_fl=mkAf_hfl(base_hip_fl,-1,trim_hfl,hip_sleep_trim)
hip_fr=mkAf_hfr(base_hip_fr, 1,trim_hfr,hip_sleep_trim)
hip_bl=mkAf_hbl(base_hip_bl,-1,trim_hbl,hip_sleep_trim)
hip_br=mkAf_hbr(base_hip_br, 1,trim_hbr,hip_sleep_trim)

hip_flfrblbr = mkAf_hfl_hfr_hbl_hbr(base_hip_fl,base_hip_fr,base_hip_bl,base_hip_br,-1,1,-1,1,trim_hfl,trim_hfr,trim_hbl,trim_hbr,hip_sleep_trim)

knee_fl=mkAf_kfl(base_knee_fl,-1,trim_kfl,knee_sleep_trim)
knee_fr=mkAf_kfr(base_knee_fr,-1,trim_kfr,knee_sleep_trim)
knee_bl=mkAf_kbl(base_knee_bl,-1,trim_kbl,knee_sleep_trim)
knee_br=mkAf_kbr(base_knee_br,-1,trim_kbr,knee_sleep_trim)

knee_flbr = mkAf_kfl_kbr(base_knee_fl,base_knee_br,-1,-1,trim_kfl,trim_kbr,knee_sleep_trim)
knee_frbl = mkAf_kfr_kbl(base_knee_fr,base_knee_bl,-1,-1,trim_kfl,trim_kfr,knee_sleep_trim)


foot_fl=mkAf_ffl(base_foot_fl,1,trim_ffl,hip_sleep_trim)
foot_fr=mkAf_ffr(base_foot_fr,1,trim_ffr,hip_sleep_trim)
foot_bl=mkAf_fbl(base_foot_bl,1,trim_fbl,hip_sleep_trim)
foot_br=mkAf_fbr(base_foot_br,1,trim_fbr,hip_sleep_trim)


#=========================================================================================#
# Read User CLI Input                                                                     #
#=========================================================================================#

def readKeyboard(callback_op):
    fd = sys.stdin.fileno()
    old = termios.tcgetattr(fd)
    tty.setcbreak(fd)
    readNext = True
    try:
        while readNext:
            if select.select([sys.stdin], [], [], 0.05)[0]:
                ch = sys.stdin.read(1)
                status = callback_op(ch)
                if status == "quit": 
                    readNext = False

    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old)


#=========================================================================================#
# Test Commands                                                                           #
#=========================================================================================#

def commandHips(a):
    hip_fl(a)
    hip_fr(a)
    hip_bl(a)
    hip_br(a)

def commandKnees(a):
    knee_fl(a)
    knee_fr(a)
    knee_bl(a)
    knee_br(a)

def commandFeet(a):
    foot_fl(a)
    foot_fr(a)
    foot_bl(a)
    foot_br(a)

def commandAllZero():
    commandHips(0)
    commandKnees(0)
    commandFeet(0)

def commandMaxFeet():
    commandFeet(80)

def commandMinFeet():
    commandFeet(-90)

def commandMaxKnee():
    commandKnees(90)

def commandMinKnee():
    commandKnees(-90)

def commandZeroHips():
    commandHips(0)

#=========================================================================================#
# Walk Dev                                                                                #
#=========================================================================================#

knee_up=75
knee_n=50

foot_up=-50
foot_n=-70

hip_f=20
hip_b=-20

def commandReset():
    commandHips(0)
    commandKnees(knee_n)
    commandFeet(foot_n)
    
def commandA():
    knee_flbr(knee_up,knee_up)
    hip_flfrblbr(hip_f,hip_b,hip_b,hip_f)
    knee_flbr(knee_n,knee_n)

def commandB():
    knee_frbl(knee_up,knee_up)
    hip_flfrblbr(hip_b,hip_f,hip_f,hip_b)
    knee_frbl(knee_n,knee_n)

def walk():
    commandReset()
    x=0
    while x < 5:
        commandA()
        commandB()
        x=x+1
    commandReset()




















#=========================================================================================#
# User Input Multiplex                                                                    #
#=========================================================================================#

def keyboardInputMultiplex(c):
    if c == "q":
        print("Exiting")
        return "quit"
    if c == "z":
        commandAllZero()
    if c == "f":
        commandMaxFeet()
    if c == "g": 
        commandMinFeet()
    if c == "o":
        commandMaxKnee()
    if c == "p":
        commandMinKnee()
    if c == "d":
        dwalk(2)
    if c == "w":
        walk()

#=========================================================================================#
# Program Main Start                                                                      #
#=========================================================================================#

readKeyboard(keyboardInputMultiplex)






































































#=========================================================================================#
# Write dictionary to yaml file                                                           #
#=========================================================================================#

def writeSettings(d):
    yaml.safe_dump(
        d,
        open("settings.yaml", "w"),
        sort_keys=False,
        default_flow_style=False
    )

#=========================================================================================#
# Read dictionary from yaml file                                                          #
#=========================================================================================#

def readSettings():
    with open("settings.yaml", "r") as f:
        d = yaml.safe_load(f)
        return d

#=========================================================================================#
# Update servos using dictionary                                                          #
#=========================================================================================#

def updateServos(d):
    hip_fl(d["H"]["fl"])
    hip_fr(d["H"]["fr"])
    hip_bl(d["H"]["bl"])
    hip_br(d["H"]["br"])

    knee_fl(d["K"]["fl"])
    knee_fl(d["K"]["fr"])
    knee_fl(d["K"]["bl"])
    knee_fl(d["K"]["br"])

    foot_fl(d["F"]["fl"])
    foot_fl(d["F"]["fr"])
    foot_fl(d["F"]["bl"])
    foot_fl(d["F"]["br"])





#=========================================================================================#
# On File Change Update Logic                                                             #
#=========================================================================================#

"""
def on_change(path):
    print(f"{path} changed — reloading")
    time.sleep(1)
    readSettings("Neutral")


SETTINGS = Path("/home/drake/Documents/picrawler/robot-hat/settings.yaml").resolve()

class Handler(FileSystemEventHandler):
    def on_modified(self, event):
        self._check(event.src_path)

    def on_moved(self, event):
        self._check(event.dest_path)

    def _check(self, path):
        if Path(path).resolve() == SETTINGS:
            on_change(path)

observer = Observer()
observer.schedule(Handler(), path=".", recursive=False)
observer.start()

try:
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    observer.stop()

observer.join()
"""


