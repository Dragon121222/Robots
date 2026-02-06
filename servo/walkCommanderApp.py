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

import sys, termios, tty, select

from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

from pathlib import Path


from remote.common.listenerApp import Listener
from remote.servo.servoCommander import ServoCommander

#=================================================================
# Listener 
#=================================================================

sc = ServoCommander()
sc.SetupWalk()

def processCmd(data):
    print("Command Received: ", data)

    if data=="Reset":
        print("Doing a reset.")
        sc.BaseReset()

    if data=="Sit":
        print("Being a good boy.")
        sc.Sit()

    if data=="walkForward":
        print("Trying to walk forward.")
        sc.Walk("forward")

    if data=="walkBackward":
        print("Trying to walk forward.")
        sc.Walk("backward")

    if data=="walkLeft":
        print("Trying to walk left")
        sc.Walk("left")

    if data=="walkRight":
        print("Trying to walk right")
        sc.Walk("right")

    if data=="rotateLeft":
        print("Trying to rotate left.")
        sc.Rotate("left")

    if data=="rotateRight":
        print("Trying to rotate right.")
        sc.Rotate("right")

    if data=="panUp":
        print("Trying to pan up.")
        sc.Pan("up")

    if data=="panDown":
        print("Trying to pan down.")
        sc.Pan("down")

    if data=="translateUp":
        print("Trying to translate up")
        sc.Translate("up")

    if data=="translateDown":
        print("Trying to translate down")
        sc.Translate("down")

    if data=="rollLeft":
        print("Trying to roll left")
        sc.Roll("left")

    if data=="rollRight":
        print("Trying to roll right")
        sc.Roll("right")

print("==================================================================")
print("Activate Walk Commander App")
print("==================================================================")

l = Listener("/tmp/loopBack",processCmd)

l.processQueue()













