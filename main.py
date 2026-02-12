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
from remote.vision.simpleOrangePiNpuYolo import simpleOrangePiNpuYolo as yoloManager
from remote.buzzer.droid_sounds import DroidSpeaker as buzzerManager
from remote.keyboard.keyboardReader import KeyboardReader as keyboardManager
from remote.servo.servoCommander import ServoCommander as servoManager

from remote.gsi.impl.tofl.goal import GoalImpl
# from remote.gsi.impl.tofl.context import ContextImpl
# from remote.gsi.impl.tofl.dataModel import DataModelImpl
# from remote.gsi.impl.tofl.gsiProblem import GsiProblemImpl
# from remote.gsi.impl.tofl.implementation import ImplementationImpl
# from remote.gsi.impl.tofl.strategy import StrategyImpl
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
    now = time.monotonic()

    if not detections and now - self._last_detection_time > 5.0:
        if now - self._last_servo_cmd > 2.0:
            ipc.send("left", "servo")
            ipc.send("snap_yolo", "camera")
            self._last_servo_cmd = now
            return

    for det in detections:

        if now - self._last_detection_time > 5.0:
            print(f"Detected: {det['class_name']}")

            if det['class_name'] == "person":
                ipc.send("p","buzzer")

            if det['class_name'] == "cat":
                ipc.send("c","buzzer")

            if det['class_name'] == "dog":
                ipc.send("d","buzzer")

        if det['class_name'] == "dog" or det['class_name'] == "cat" :
            bbox = det['bbox']
            bbox_center_x = (bbox[0] + bbox[2]) / 2

            bbox_width = bbox[2] - bbox[0]
            bbox_height = bbox[3] - bbox[1]
            bbox_area = bbox_width * bbox_height

            if bbox_center_x < frame_center - 600:
                if now - self._last_servo_cmd > 2.0:
                    direction = "TURN LEFT"
                    ipc.send("left","servo")
                    self._last_servo_cmd = now
            elif bbox_center_x > frame_center + 600:
                if now - self._last_servo_cmd > 2.0:
                    direction = "TURN RIGHT"
                    ipc.send("right","servo")
                    self._last_servo_cmd = now
            else:
                direction = "CENTERED"
                if bbox_area < 1000000:
                    if now - self._last_servo_cmd > 2.0:
                        ipc.send("forward","servo")
                        self._last_servo_cmd = now
                elif bbox_area > 2000000:
                    if now - self._last_servo_cmd > 2.0:
                        ipc.send("backwards","servo")
                        self._last_servo_cmd = now

            print(f"Label \t{det['class_name']}")
            print(f"\tDirect\t{direction}")
            print(f"\tCenter\t{bbox_center_x:.0f}")
            print(f"\tWidth \t{bbox_width:.0f}")
            print(f"\tHeight\t{bbox_height:.0f}")
            print(f"\tArea  \t{bbox_area:.0f}")

        self._last_detection_time = now
    ipc.send("snap_yolo","camera")
#=================================================================

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

try:
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    print("Shutting down...")
#=================================================================