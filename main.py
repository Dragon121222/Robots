# main.py
#================================================================
# Main App
#================================================================
import cv2
import time
import threading
import pickle
import socket
import os
from pathlib import Path
from datetime import datetime
from types import MethodType

#=================================================================
# Custom Ecosystem
#=================================================================
from remote.common.fakeIpc import FakeIpc as ipcManager
from remote.camera.simpleCamera import simpleCam as cameraManager
# from remote.vision.simpleYolo import simpleYolo as yoloManager
from remote.vision.simpleOrangePiNpuYolo import simpleOrangePiNpuYolo as yoloManager
from remote.buzzer.droid_sounds import DroidSpeaker as buzzerManager
from remote.keyboard.keyboardReader import KeyboardReader as keyboardManager
from remote.servo.servoCommander import ServoCommander as servoManager
#=================================================================



#=================================================================
ipc         = None
buzzer      = None
camera      = None
yolo        = None
keyboard    = None
servo       = None
#=================================================================



#=================================================================
def buzzer_receive(self, msg):
    self.say(msg)
#=================================================================



#=================================================================
def camera_receive(self, msg):
    if msg == "snap_yolo":
        try:
            frame = self.snap()
            ipc.send(frame, "yolo")
        except queue.Full:
            print("Camera queue full, dropping frame")
#=================================================================


#=================================================================
def yolo_receive(self, msg):
    detections = self.detect_objects(msg)
    
    frame_w = msg.shape[1]
    frame_center = frame_w / 2
    
    for det in detections:
        bbox = det['bbox']
        bbox_center_x = (bbox[0] + bbox[2]) / 2

        bbox_width = bbox[2] - bbox[0]
        bbox_height = bbox[3] - bbox[1]
        bbox_area = bbox_width * bbox_height

        if bbox_center_x < frame_center - 50:
            direction = "TURN LEFT"
            ipc.send("left","servo")
            time.sleep(1.5)
        elif bbox_center_x > frame_center + 50:
            direction = "TURN RIGHT"
            ipc.send("right","servo")
            time.sleep(1.5)
        else:
            direction = "CENTERED"
            if bbox_area < 75000:
                ipc.send("forward","servo")
                time.sleep(1.5)
            elif bbox_area > 100000:
                ipc.send("backwards","servo")
                time.sleep(1.5)
            else:
                ipc.send(det['class_name'],"buzzer")
                time.sleep(1.5)

        print(f"Label \t{det['class_name']}")
        print(f"\tDirect\t{direction}")
        print(f"\tCenter\t{bbox_center_x:.0f}")
        print(f"\tWidth \t{bbox_width:.0f}")
        print(f"\tHeight\t{bbox_height:.0f}")
        print(f"\tArea  \t{bbox_area:.0f}")

    ipc.send("snap_yolo","camera")


#=================================================================
def servo_receive(self, msg):
    if msg == "setup":
        servo.SetupWalk()
    if msg == "left":
        servo.RotateLeft()
    if msg == "right":
        servo.RotateRight()
    if msg == "forward":
        servo.Forward()
    if msg == "backward":
        servo.Backward()
#=================================================================



#=================================================================
def keyboard_receive(self, msg):
    print("Received Command")
#=================================================================



#=================================================================
buzzer              = buzzerManager()
camera              = cameraManager(width=1920,height=1080)
yolo                = yoloManager()
keyboard            = keyboardManager()
servo               = servoManager()

buzzer.receive      = MethodType(buzzer_receive,    buzzer)
camera.receive      = MethodType(camera_receive,    camera)
yolo.receive        = MethodType(yolo_receive,      yolo)
servo.receive       = MethodType(servo_receive,     servo)
keyboard.receive    = MethodType(keyboard_receive,  keyboard)

keyboard.callback   = keyboard.receive

listenerList = {
    "buzzer":   buzzer,
    "camera":   camera,
    "yolo":     yolo,
    "keyboard": keyboard,
    "servo":    servo
}
#=================================================================



#=================================================================
ipc = ipcManager(listenerList)

ipc.send("Online","buzzer")
ipc.send("setup","servo")
ipc.send("snap_yolo","camera")

# Let the system run indefinitely
try:
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    print("Shutting down...")
#=================================================================