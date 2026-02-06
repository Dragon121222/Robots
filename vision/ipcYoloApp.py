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
from remote.vision.simpleYolo import simpleYolo
from remote.time.record_event import record_event, merge_and_sort_events, log_events


globalEvents=[]
globalTimeStart = time.perf_counter()

frameCounter=0

def testCmd(data):
    global globalTimeStart
    global frameCounter
    newEvent = record_event(f"Receiving Frame: {frameCounter}", globalTimeStart)
    globalEvents.append(newEvent)
    frameCounter = frameCounter + 1

class ipcYoloApp:
    
    def __init__(self):
        print("Creating Ipc Yolo App")

        self.start = globalTimeStart

        ctorEvent = record_event("ipcYoloApp Construct")
        globalEvents.append(ctorEvent)

        self.ipc = pythonIpcManager()
        self.yolo = simpleYolo()

        self.ipc.setupResponseCallback(testCmd,"/tmp/ipcYoloApp")




#=================================================================
# Main Entry Point
#=================================================================
if __name__ == "__main__":
    app = ipcYoloApp()

    time.sleep(10)

    log_events(globalEvents, globalTimeStart)