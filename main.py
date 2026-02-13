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
from remote.common.fakeIpc import FakeIpcMessage as ipcMessage
from remote.common.simpleFsm import SimpleState as fsmState
from remote.common.simpleFsm import SimpleFsm as fsmManager
from remote.camera.simpleCamera import simpleCam as cameraManager
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
normal_bs   = fsmState("Normal")
excited_bs  = fsmState("Excited")
worried_bs  = fsmState("Worried")

buzzerStateMachine: dict[str, set[str]] = {
    normal_bs._stateId:   {normal_bs._stateId, excited_bs._stateId, worried_bs._stateId},
    excited_bs._stateId:  {normal_bs._stateId, excited_bs._stateId, worried_bs._stateId},
    worried_bs._stateId:  {normal_bs._stateId, excited_bs._stateId, worried_bs._stateId},
}

def buzzerFsm_receive(self, ipcMsg):
    self.requestUpdate(ipcMsg._msg,ipcMsg._senderId)

def buzzer_receive(self, ipcMsg):
    if self.fsm._currentState._stateId == "Normal":
        self.say(ipcMsg._msg)
    elif self.fsm._currentState._stateId == "Excited":
        self.excited(ipcMsg._msg)
    elif self.fsm._currentState._stateId == "Worried":
        self.worried(ipcMsg._msg)
#=================================================================

#=================================================================
normal_cs   = fsmState("Normal")
save_cs     = fsmState("Save")

cameraStateMachine: dict[str, set[str]] = {
    normal_cs._stateId:     {normal_cs._stateId, save_cs._stateId},
    save_cs._stateId:       {normal_cs._stateId, save_cs._stateId}
}

def cameraFsm_receive(self, ipcMsg):
    self.requestUpdate(ipcMsg._msg,ipcMsg._senderId)

def camera_receive(self, ipcMsg):
    if ipcMsg._senderId == "yolo" or ipcMsg._senderId == "main":
        try:
            frame = self.snap()
            ipc.send(ipcMessage(frame,"yolo","camera"))
        except queue.Full:
            print("Camera queue full, dropping frame")
#=================================================================

#=================================================================
person_ys   = fsmState("Person")
cat_ys      = fsmState("Cat")
dog_ys      = fsmState("Dog")

yoloStateMachine: dict[str, set[str]] = {
    person_ys._stateId:     {person_ys._stateId, cat_ys._stateId, dog_ys._stateId},
    cat_ys._stateId:        {person_ys._stateId, cat_ys._stateId, dog_ys._stateId},
    dog_ys._stateId:        {person_ys._stateId, cat_ys._stateId, dog_ys._stateId}
}

def yoloFsm_receive(self, ipcMsg):
    self.requestUpdate(ipcMsg._msg,ipcMsg._senderId)

def yolo_receive(self, ipcMsg):
    detections = self.detect_objects(ipcMsg._msg)
    frame_w = ipcMsg._msg.shape[1]
    frame_center = frame_w / 2
    now = time.monotonic()
    if not detections and now - self._last_detection_time > 5.0:
        if now - self._last_servo_cmd > 2.0:
            ipc.send(ipcMessage("left","servo","yolo"))
            ipc.send(ipcMessage("snap_yolo","camera","yolo"))
            self._last_servo_cmd = now
            return

    for det in detections:
        if now - self._last_detection_time > 5.0:
            print(f"Detected: {det['class_name']}")
            if det['class_name'] == "person":
                ipc.send(ipcMessage("p","buzzer","yolo"))
            if det['class_name'] == "cat":
                ipc.send(ipcMessage("c","buzzer","yolo"))
            if det['class_name'] == "dog":
                ipc.send(ipcMessage("d","buzzer","yolo"))

        if det['class_name'] == "dog" or det['class_name'] == "cat" :
            bbox = det['bbox']
            bbox_center_x = (bbox[0] + bbox[2]) / 2
            bbox_width = bbox[2] - bbox[0]
            bbox_height = bbox[3] - bbox[1]
            bbox_area = bbox_width * bbox_height

            if bbox_center_x < frame_center - 600:
                if now - self._last_servo_cmd > 2.0:
                    direction = "TURN LEFT"
                    ipc.send(ipcMessage("left","servo","yolo"))
                    self._last_servo_cmd = now
            elif bbox_center_x > frame_center + 600:
                if now - self._last_servo_cmd > 2.0:
                    direction = "TURN RIGHT"
                    ipc.send(ipcMessage("right","servo","yolo"))
                    self._last_servo_cmd = now
            else:
                direction = "CENTERED"
                if bbox_area < 1000000:
                    if now - self._last_servo_cmd > 2.0:
                        ipc.send(ipcMessage("forward","servo","yolo"))
                        self._last_servo_cmd = now
                elif bbox_area > 2000000:
                    if now - self._last_servo_cmd > 2.0:
                        ipc.send(ipcMessage("backwards","servo","yolo"))
                        self._last_servo_cmd = now

            print(f"Label \t{det['class_name']}")
            print(f"\tDirect\t{direction}")
            print(f"\tCenter\t{bbox_center_x:.0f}")
            print(f"\tWidth \t{bbox_width:.0f}")
            print(f"\tHeight\t{bbox_height:.0f}")
            print(f"\tArea  \t{bbox_area:.0f}")

        self._last_detection_time = now
    ipc.send(ipcMessage("snap","camera","yolo"))
#=================================================================

#=================================================================
normal_ss   = fsmState("Normal")
fast_ss     = fsmState("Fast")

servoStateMachine: dict[str, set[str]] = {
    normal_ss._stateId:     {normal_ss._stateId, fast_ss._stateId},
    fast_ss._stateId:       {normal_ss._stateId, fast_ss._stateId}
}

def servoFsm_receive(self, ipcMsg):
    self.requestUpdate(ipcMsg._msg,ipcMsg._senderId)

def servo_receive(self, ipcMsg):
    if ipcMsg._msg == "setup":
        servo.SetupWalk()
    if ipcMsg._msg == "left":
        servo.RotateLeft()
    if ipcMsg._msg == "right":
        servo.RotateRight()
    if ipcMsg._msg == "forward":
        servo.Forward()
    if ipcMsg._msg == "backward":
        servo.Backward()
#=================================================================

#=================================================================
word_ks     = fsmState("Word")
key_ks      = fsmState("Key")

keyboardStateMachine: dict[str, set[str]] = {
    word_ks._stateId:   {word_ks._stateId, key_ks._stateId},
    key_ks._stateId:    {word_ks._stateId, key_ks._stateId}
}

def keyboardFsm_receive(self, ipcMsg):
    self.requestUpdate(ipcMsg._msg,ipcMsg._senderId)

def keyboard_receive(self, ipcMsg):
    print("Received Command")
#=================================================================

#=================================================================
normal_is   = fsmState("Normal")
record_is   = fsmState("Record")

ipcStateMachine: dict[str, set[str]] = {
    normal_is._stateId:     {normal_is._stateId, record_is._stateId},
    record_is._stateId:     {normal_is._stateId, record_is._stateId}
}

def ipcFsm_receive(self, ipcMsg):
    print("Received Command")
#=================================================================

#=================================================================
buzzer                  = buzzerManager()
buzzer.fsm              = fsmManager(buzzerStateMachine,    normal_bs)

camera                  = cameraManager(width=1920,height=1080)
camera.fsm              = fsmManager(cameraStateMachine,    normal_cs)

yolo                    = yoloManager()
yolo.fsm                = fsmManager(yoloStateMachine,      person_ys)

servo                   = servoManager()
servo.fsm               = fsmManager(servoStateMachine,     normal_ss)

keyboard                = keyboardManager()
keyboard.fsm            = fsmManager(keyboardStateMachine,  word_ks)

ipcFsm                  = fsmManager(ipcStateMachine,       normal_is)

ipcFsm.receive          = MethodType(ipcFsm_receive,        ipcFsm)

buzzer.fsm.receive      = MethodType(buzzerFsm_receive,     buzzer.fsm)
buzzer.receive          = MethodType(buzzer_receive,        buzzer)

camera.fsm.receive      = MethodType(cameraFsm_receive,     camera.fsm)
camera.receive          = MethodType(camera_receive,        camera)

yolo.fsm.receive        = MethodType(yoloFsm_receive,       yolo.fsm)
yolo.receive            = MethodType(yolo_receive,          yolo)

servo.fsm.receive       = MethodType(servoFsm_receive,      servo.fsm)
servo.receive           = MethodType(servo_receive,         servo)

keyboard.fsm.receive    = MethodType(keyboardFsm_receive,   keyboard.fsm)
keyboard.receive        = MethodType(keyboard_receive,      keyboard)
keyboard.callback       = keyboard.receive

listenerList = {
    "buzzer":       buzzer,
    "buzzerFsm":    buzzer.fsm,
    "camera":       camera,
    "cameraFsm":    camera.fsm,
    "yolo":         yolo,
    "yoloFsm":      yolo.fsm,
    "keyboard":     keyboard,
    "keyboardFsm":  keyboard.fsm,
    "servo":        servo,
    "servoFsm":     servo.fsm,
    "ipcFsm":       ipcFsm
}
#=================================================================



#=================================================================

ipc = ipcManager(listenerList)
ipc.fsm = ipcFsm

ipc.send(ipcMessage("Online","buzzer","main"))
ipc.send(ipcMessage("setup","servo","main"))
ipc.send(ipcMessage("snap","camera","main"))

try:
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    print("Shutting down...")
#=================================================================