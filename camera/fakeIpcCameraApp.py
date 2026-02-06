# ipcCameraApp.py
#================================================================
# Ipc Camera Commander App
# Captures and distributes images
#================================================================
import cv2
import time
import threading
import pickle
import socket
import os
from pathlib import Path
from datetime import datetime, timezone

#=================================================================
# Custom System
#=================================================================
from remote.common.pythonIpcManager import pythonIpcManager
from remote.camera.simpleCamera import simpleCam
from remote.time.record_event import record_event, merge_and_sort_events


globalEvents=[]
globalTimeStart = time.perf_counter()

frameCounter=0

def testCmd(data):
    global globalTimeStart
    global frameCounter
    newEvent = record_event(f"Receiving Frame: {frameCounter}", globalTimeStart)
    globalEvents.append(newEvent)
    frameCounter = frameCounter + 1

class ipcCameraApp:
    
    def __init__(self):
        print("Creating Ipc Camera App")

        ctorEvent = record_event("ipcCameraApp Construct")
        globalEvents.append(ctorEvent)

        self.ipc = pythonIpcManager()
        self.camera = simpleCam()

        self.ipc.setupResponseCallback(testCmd,"/tmp/ipcCameraAppTest")

        print("Testing simple ipc rate.")

        n=0
        while n < 10:
            frame = self.camera.snap()
            self.ipc.sendMsg(frame, "/tmp/ipcCameraAppTest")
            newEvent = record_event(f"Sending Frame: {n}", globalTimeStart)
            globalEvents.append(newEvent)
            n = n + 1

        print("Results: ")

        prev = globalTimeStart

        for e in globalEvents:
            dt=(e["mono_time"] - prev)
            print(f"Event: {e["event"]}, {dt:.3f}, {(1/dt):.3f}")
            prev = e["mono_time"]

    def capture(self, dest, frameCount=10, delay=0):
        c=0
        i=1
        if frameCount == -1:
            i=0
        while c < frameCount:
            frame = self.camera.snap()
            c=c+i
            self.ipc.sendMsg(frame, dest)
            if delay != 0:
                time.sleep(delay)


#=================================================================
# Main Entry Point
#=================================================================
if __name__ == "__main__":
    app = ipcCameraApp()

    app.capture("/tmp/ipcYoloApp")