#================================================================
# Imports
#================================================================

import time
import threading
import sys
import termios
import tty
import select
import yaml
import pickle

try:
    from robot_hat import Servo
except Exception:
    from robot_hat.servo import Servo

from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from pathlib import Path

#=================================================================
# Custom System
#=================================================================
from remote.common.listenerApp import Listener

def MakeServoChannel(ch):
    print("Servo Channel: ",ch)
    s = Servo(ch)
    def set_angle(a):
        if hasattr(s, "angle"): s.angle(a)
        elif hasattr(s, "write"): s.write(a)
        elif hasattr(s, "set_angle"): s.set_angle(a)
        else: raise RuntimeError("no angle method")
    return set_angle

class ServoCommander:
    def __init__(self):
        print("CTOR Servo Commander")
        self.base_hip_fl=MakeServoChannel(2)
        self.base_hip_fr=MakeServoChannel(5)
        self.base_hip_bl=MakeServoChannel(8)
        self.base_hip_br=MakeServoChannel(11)

        self.base_knee_fl=MakeServoChannel(1)
        self.base_knee_fr=MakeServoChannel(4)
        self.base_knee_bl=MakeServoChannel(7)
        self.base_knee_br=MakeServoChannel(10)

        self.base_foot_fl=MakeServoChannel(0)
        self.base_foot_fr=MakeServoChannel(3)
        self.base_foot_bl=MakeServoChannel(6)
        self.base_foot_br=MakeServoChannel(9)

        self.yaw_accumulator = 0

#========================================================#
# Base Write                                             #
#========================================================#
    #Hips
    def BaseHipFL(self, angle):
        self.base_hip_fl(self.hip_fl_scale*angle+self.hip_fl_trim)
        self.base_hip_fl_value=angle

    def BaseHipFR(self, angle):
        self.base_hip_fr(self.hip_fr_scale*angle+self.hip_fr_trim)
        self.base_hip_fr_value=angle

    def BaseHipBL(self, angle):
        self.base_hip_bl(self.hip_bl_scale*angle+self.hip_bl_trim)
        self.base_hip_bl_value=angle

    def BaseHipBR(self, angle):
        self.base_hip_br(self.hip_br_scale*angle+self.hip_br_trim)
        self.base_hip_br_value=angle

    def BaseHipFLFRBLBR(self, angle_fl, angle_fr, angle_bl, angle_br):
        self.BaseHipFL(angle_fl)
        self.BaseHipFR(angle_fr)
        self.BaseHipBL(angle_bl)
        self.BaseHipBR(angle_br)

    #Knees
    def BaseKneeFL(self, angle):
        self.base_knee_fl(self.knee_fl_scale*angle+self.knee_fl_trim)
        self.base_knee_fl_value=angle

    def BaseKneeFR(self, angle):
        self.base_knee_fr(self.knee_fr_scale*angle+self.knee_fr_trim)
        self.base_knee_fr_value=angle

    def BaseKneeBL(self, angle):
        self.base_knee_bl(self.knee_bl_scale*angle+self.knee_bl_trim)
        self.base_knee_bl_value=angle

    def BaseKneeBR(self, angle):
        self.base_knee_br(self.knee_br_scale*angle+self.knee_br_trim)
        self.base_knee_br_value=angle

    def BaseKneeFLBR(self, angle_fl, angle_br):
        self.BaseKneeFL(angle_fl)
        self.BaseKneeBR(angle_br)

    def BaseKneeFRBL(self, angle_fr, angle_bl):
        self.BaseKneeFR(angle_fr)
        self.BaseKneeBL(angle_bl)

    #Feet
    def BaseFootFL(self, angle):
        self.base_foot_fl(self.foot_fl_scale*angle+self.foot_fl_trim)
        self.base_foot_fl_value=angle

    def BaseFootFR(self, angle):
        self.base_foot_fr(self.foot_fr_scale*angle+self.foot_fr_trim)
        self.base_foot_fr_value=angle

    def BaseFootBL(self, angle):
        self.base_foot_bl(self.foot_bl_scale*angle+self.foot_bl_trim)
        self.base_foot_bl_value=angle

    def BaseFootBR(self, angle):
        self.base_foot_br(self.foot_br_scale*angle+self.foot_br_trim)
        self.base_foot_br_value=angle

    def BaseReset(self):
        self.BaseHipFL(0)
        self.BaseHipFR(0)
        self.BaseHipBL(0)
        self.BaseHipBR(0)

        self.BaseKneeFL(0)
        self.BaseKneeFR(0)
        self.BaseKneeBL(0)
        self.BaseKneeBR(0)

        self.BaseFootFL(0)
        self.BaseFootFR(0)
        self.BaseFootBL(0)
        self.BaseFootBR(0)

    def BaseSit(self):
        self.BaseHipFL(0)
        self.BaseHipFR(0)
        self.BaseHipBL(0)
        self.BaseHipBR(0)

        self.BaseKneeFL(90)
        self.BaseKneeFR(90)
        self.BaseKneeBL(90)
        self.BaseKneeBR(90)
        
        self.BaseFootFL(90)
        self.BaseFootFR(90)
        self.BaseFootBL(90)
        self.BaseFootBR(90)

#========================================================#
# Write with Delay                                       #
#========================================================#
    #========================================================#
    # Hips
    #========================================================#
    def DelayHipFL(self, angle, extra_delay=0):
        diff = abs(angle-self.base_hip_fl_value)
        self.BaseHipFL(angle)
        time.sleep(self.hip_sleep_trim*diff+extra_delay)

    def DelayHipFR(self, angle, extra_delay=0):
        diff = abs(angle-self.base_hip_fr_value)
        self.BaseHipFR(angle)
        time.sleep(self.hip_sleep_trim*diff+extra_delay)

    def DelayHipBL(self, angle, extra_delay=0):
        diff = abs(angle-self.base_hip_bl_value)
        self.BaseHipBL(angle)
        time.sleep(self.hip_sleep_trim*diff+extra_delay)

    def DelayHipBR(self, angle, extra_delay=0):
        diff = abs(angle-self.base_hip_br_value)
        self.BaseHipBR(angle)
        time.sleep(self.hip_sleep_trim*diff+extra_delay)

    def DelayHipFLFRBLBR(self, angle_fl, angle_fr, angle_bl, angle_br, extra_delay=0):
        diff_fl = abs(angle_fl-self.base_hip_fl_value)
        diff_fr = abs(angle_fr-self.base_hip_fr_value)
        diff_bl = abs(angle_bl-self.base_hip_bl_value)
        diff_br = abs(angle_br-self.base_hip_br_value)
        diff_max = max(diff_fl,diff_fr,diff_bl,diff_br)
        self.BaseHipFL(angle_fl)
        self.BaseHipFR(angle_fr)
        self.BaseHipBL(angle_bl)
        self.BaseHipBR(angle_br)
        time.sleep(self.hip_sleep_trim*diff_max+extra_delay)

    #========================================================#
    #Knees
    #========================================================#
    def DelayKneeFL(self, angle, extra_delay=0):
        diff = abs(angle-self.base_knee_fl_value)
        self.BaseKneeFL(angle)
        time.sleep(self.knee_sleep_trim*diff+extra_delay)

    def DelayKneeFR(self, angle, extra_delay=0):
        diff = abs(angle-self.base_knee_fr_value)
        self.BaseKneeFR(angle)
        time.sleep(self.knee_sleep_trim*diff+extra_delay)

    def DelayKneeBL(self, angle, extra_delay=0):
        diff = abs(angle-self.base_knee_bl_value)
        self.BaseKneeBL(angle)
        time.sleep(self.knee_sleep_trim*diff+extra_delay)

    def DelayKneeBR(self, angle, extra_delay=0):
        diff = abs(angle-self.base_knee_br_value)
        self.BaseKneeBR(angle)
        time.sleep(self.knee_sleep_trim*diff+extra_delay)

    def DelayKneeFLBR(self,angle, extra_delay=0):
        diff_fl = abs(angle-self.base_knee_fl_value)
        diff_br = abs(angle-self.base_knee_br_value)
        diff_max = max(diff_fl,diff_br)
        self.BaseKneeFL(angle)
        self.BaseKneeBR(angle)
        time.sleep(self.knee_sleep_trim*diff_max+extra_delay)

    def DelayKneeFRBL(self,angle, extra_delay=0):
        diff_fr = abs(angle-self.base_knee_fr_value)
        diff_bl = abs(angle-self.base_knee_bl_value)
        diff_max = max(diff_fr,diff_bl)
        self.BaseKneeFR(angle)
        self.BaseKneeBL(angle)
        time.sleep(self.knee_sleep_trim*diff_max+extra_delay)

    def DelayKneeFLFRBLBR(self, angle_fl, angle_fr, angle_bl, angle_br, extra_delay=0):
        diff_fl = abs(angle_fl-self.base_knee_fl_value)
        diff_fr = abs(angle_fr-self.base_knee_fr_value)
        diff_bl = abs(angle_bl-self.base_knee_bl_value)
        diff_br = abs(angle_br-self.base_knee_br_value)
        diff_max = max(diff_fl,diff_fr,diff_bl,diff_br)
        self.BaseKneeFL(angle_fl)
        self.BaseKneeFR(angle_fr)
        self.BaseKneeBL(angle_bl)
        self.BaseKneeBR(angle_br)
        time.sleep(self.knee_sleep_trim*diff_max+extra_delay)

    #========================================================#
    #Feet
    #========================================================#
    def DelayFootFL(self, angle, extra_delay=0):
        self.BaseFootFL(angle)
        diff = abs(angle-self.base_foot_fl_value)
        time.sleep(self.foot_sleep_trim*diff+extra_delay)

    def DelayFootFR(self, angle, extra_delay=0):
        self.BaseFootFR(angle)
        diff = abs(angle-self.base_foot_fr_value)
        time.sleep(self.foot_sleep_trim*diff+extra_delay)

    def DelayFootBL(self, angle, extra_delay=0):
        self.BaseFootBL(angle)
        diff = abs(angle-self.base_foot_bl_value)
        time.sleep(self.foot_sleep_trim*diff+extra_delay)

    def DelayFootBR(self, angle, extra_delay=0):
        self.BaseFootBR(angle)
        diff = abs(angle-self.base_foot_br_value)
        time.sleep(self.foot_sleep_trim*diff+extra_delay)

    def DelayFootFLFRBLBR(self, angle_fl, angle_fr, angle_bl, angle_br, extra_delay=0):
        diff_fl = abs(angle_fl-self.base_foot_fl_value)
        diff_fr = abs(angle_fr-self.base_foot_fr_value)
        diff_bl = abs(angle_bl-self.base_foot_bl_value)
        diff_br = abs(angle_br-self.base_foot_br_value)
        diff_max = max(diff_fl,diff_fr,diff_bl,diff_br)
        self.BaseFootFL(angle_fl)
        self.BaseFootFR(angle_fr)
        self.BaseFootBL(angle_bl)
        self.BaseFootBR(angle_br)
        time.sleep(self.foot_sleep_trim*diff_max+extra_delay)

#========================================================#
# Marching Orders                                        #
#========================================================#
    def Walk(self,dir):
        if dir=="forward":
            self.Forward()
        if dir=="backward":
            self.Backward()
        if dir=="left":
            self.Left()
        if dir=="right":
            self.Right()

    def Rotate(self,dir):
        if dir=="right":
            self.RotateRight()
        if dir=="left":
            self.RotateLeft()

    def Translate(self,dir):
        if dir=="up":
            self.MoveUp()
        if dir=="down":
            self.MoveDown()

    def Pan(self,dir):
        if dir=="up":
            self.PanUp()
        if dir=="down":
            self.PanDown()

    def Roll(self,dir):
        if dir=="left":
            self.RollLeft()
        if dir=="Right":
            self.RollRight()

    def Yaw(self,dir):
        if dir=="left":
            self.YawLeft()
        if dir=="Right":
            self.YawRight()

    def RollLeft(self):
        print("Roll Left!")

    def RollRight(self):
        print("Roll Right")

    def YawLeft(self):
        print("Yaw Left Accumulate")
        self.yaw_accumulator = self.yaw_accumulator + 1
        if self.yaw_accumulator < 10:
            self.DelayHipFLFRBLBR(
                self.hip_f*self.yaw_accumulator/10,
                self.hip_b*self.yaw_accumulator/10,
                self.hip_f*self.yaw_accumulator/10,
                self.hip_b*self.yaw_accumulator/10
            )
        else: 
            self.yaw_accumulator = 0
            self.Rotate("left")

    def YawRight(self):
        print("Yaw Right Accumulate")
        self.yaw_accumulator = self.yaw_accumulator - 1
        if self.yaw_accumulator > -10:
            self.DelayHipFLFRBLBR(
                self.hip_f*self.yaw_accumulator/10,
                self.hip_b*self.yaw_accumulator/10,
                self.hip_f*self.yaw_accumulator/10,
                self.hip_b*self.yaw_accumulator/10
            )
        else: 
            self.yaw_accumulator = 0
            self.Rotate("right")

    def PanUp(self):
        print("Pan up!")

    def PanDown(self):
        print("Pan Down")

    def MoveUp(self):
        print("Lift")

    def MoveDown(self):
        print("Down")

    def Forward(self):
        print("Forward March!")
        self.DelayKneeFLBR(self.knee_up)
        self.DelayHipFLFRBLBR(self.hip_f,self.hip_b,self.hip_b,self.hip_f)
        self.DelayKneeFLBR(self.knee_n)
        self.DelayKneeFRBL(self.knee_up)
        self.DelayHipFLFRBLBR(self.hip_b,self.hip_f,self.hip_f,self.hip_b)
        self.DelayKneeFRBL(self.knee_n)

    def Backward(self):
        print("Backwards March!")
        self.DelayKneeFLBR(self.knee_up)
        self.DelayHipFLFRBLBR(self.hip_b,self.hip_f,self.hip_f,self.hip_b)
        self.DelayKneeFLBR(self.knee_n)
        self.DelayKneeFRBL(self.knee_up)
        self.DelayHipFLFRBLBR(self.hip_f,self.hip_b,self.hip_b,self.hip_f)
        self.DelayKneeFRBL(self.knee_n)


    def Left(self):
        print("Left March!")

    def Right(self):
        print("Right March!")

    def RotateRight(self):
        print("Rotate Right")
        self.DelayKneeFL(self.knee_up)
        self.DelayHipFL(self.hip_f)
        self.DelayKneeFL(self.knee_n)

        self.DelayKneeFR(self.knee_up)
        self.DelayHipFR(self.hip_b)
        self.DelayKneeFR(self.knee_n)

        self.DelayKneeBL(self.knee_up)
        self.DelayHipBL(self.hip_f)
        self.DelayKneeBL(self.knee_n)

        self.DelayKneeBR(self.knee_up)
        self.DelayHipBR(self.hip_b)
        self.DelayKneeBR(self.knee_n)

        self.DelayHipFLFRBLBR(self.hip_b,self.hip_f,self.hip_b,self.hip_f)


    def RotateLeft(self):
        print("Rotate Left")
        self.DelayKneeFL(self.knee_up)
        self.DelayHipFL(self.hip_b)
        self.DelayKneeFL(self.knee_n)

        self.DelayKneeFR(self.knee_up)
        self.DelayHipFR(self.hip_f)
        self.DelayKneeFR(self.knee_n)

        self.DelayKneeBL(self.knee_up)
        self.DelayHipBL(self.hip_b)
        self.DelayKneeBL(self.knee_n)

        self.DelayKneeBR(self.knee_up)
        self.DelayHipBR(self.hip_f)
        self.DelayKneeBR(self.knee_n)

        self.DelayHipFLFRBLBR(self.hip_f,self.hip_b,self.hip_f,self.hip_b)


    def SetupWalk(self):
        self.DelayKneeFL(self.knee_n)
        self.DelayKneeFR(self.knee_n)
        self.DelayKneeBL(self.knee_n)
        self.DelayKneeBR(self.knee_n)
        self.DelayFootFL(self.foot_n)
        self.DelayFootFR(self.foot_n)
        self.DelayFootBL(self.foot_n)
        self.DelayFootBR(self.foot_n)
        self.DelayHipFLFRBLBR(0,0,0,0)
        

    def Sit(self):
        current_hfl=self.base_hip_fl_value
        current_hfr=self.base_hip_fr_value
        current_hbl=self.base_hip_bl_value
        current_hbr=self.base_hip_br_value

        current_kfl=self.base_knee_fl_value
        current_kfr=self.base_knee_fr_value
        current_kbl=self.base_knee_bl_value
        current_kbr=self.base_knee_br_value

        current_ffl=self.base_foot_fl_value
        current_ffr=self.base_foot_fr_value
        current_fbl=self.base_foot_bl_value
        current_fbr=self.base_foot_br_value

        for s in range(10):
            v = s/10
            newFFL = (1-v)*current_ffl + v*90
            newFFR = (1-v)*current_ffr + v*90
            newFBL = (1-v)*current_fbl + v*90
            newFBR = (1-v)*current_fbr + v*90

            self.DelayFootFLFRBLBR(newFFL,newFFR,newFBL,newFBR,0.1)

        for s in range(10):
            v = s/10
            newKFL = (1-v)*current_kfl + v*90
            newKFR = (1-v)*current_kfr + v*90
            newKBL = (1-v)*current_kbl + v*90
            newKBR = (1-v)*current_kbr + v*90
            self.DelayKneeFLFRBLBR(newKFL,newKFR,newKBL,newKBR,0.1)

        self.DelayHipFLFRBLBR(0,0,0,0)


#========================================================#
# Member Vars                                            #
#========================================================#
    #Hips
    hip_fl_scale=-1
    hip_fr_scale= 1
    hip_bl_scale=-1
    hip_br_scale= 1

    hip_fl_trim=0
    hip_fr_trim=0
    hip_bl_trim=0
    hip_br_trim=0

    base_hip_fl_value=0
    base_hip_fr_value=0
    base_hip_bl_value=0
    base_hip_br_value=0

    base_hip_fl=None
    base_hip_fr=None
    base_hip_bl=None
    base_hip_br=None

    hip_fl=None
    hip_fr=None
    hip_bl=None
    hip_br=None

    hip_f=20
    hip_b=-20
    hip_sleep_trim=0.5/150

    #Knees
    knee_fl_scale=-1
    knee_fr_scale=-1
    knee_bl_scale=-1
    knee_br_scale=-1

    knee_fl_trim=0
    knee_fr_trim=0
    knee_bl_trim=0
    knee_br_trim=0

    base_knee_fl_value=0
    base_knee_fr_value=0
    base_knee_bl_value=0
    base_knee_br_value=0

    base_knee_fl=None
    base_knee_fr=None
    base_knee_bl=None
    base_knee_br=None

    knee_fl=None
    knee_fr=None
    knee_bl=None
    knee_br=None

    knee_up=80
    knee_n=60
    knee_sleep_trim=0.5/180

    #Feet
    foot_fl_scale=1
    foot_fr_scale=1
    foot_bl_scale=1
    foot_br_scale=1

    foot_fl_trim=0
    foot_fr_trim=10
    foot_bl_trim=0
    foot_br_trim=5

    base_foot_fl_value=0
    base_foot_fr_value=0
    base_foot_bl_value=0
    base_foot_br_value=0

    base_foot_fl=None
    base_foot_fr=None
    base_foot_bl=None
    base_foot_br=None

    foot_fl=None
    foot_fr=None
    foot_bl=None
    foot_br=None

    foot_up=-1000
    foot_n=-85

    foot_sleep_trim=0.5/170
