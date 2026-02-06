# remote/vision/yoloCommanderApp.py
#================================================================
# YOLO Commander App - StreamListener version
# Receives frames via Unix socket from camera app
# Detects humans, dogs, cats and commands robot to track them
#================================================================

import cv2
import time
import pickle
import numpy as np
import socket
import sys
import os
from collections import deque
from threading import Thread

#=================================================================
# Custom System
#=================================================================
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))
from remote.common.streamListener import StreamListener

from remote.common.pythonIpcManager import pythonIpcManager
from remote.time.record_event import record_event, merge_and_sort_events

#=================================================================
# Configuration
#=================================================================
CAMERA_SOCKET = "/tmp/cameraFrames"
WALK_SOCKET = "/tmp/loopBack"
BUZZER_SOCKET = "/tmp/buzzerLoop"
CMD_COMPLETE_SOCKET = "/tmp/periodicCmdComplete"

TARGET_CLASSES = {0: "person", 16: "dog", 17: "cat"}
CONFIDENCE_THRESHOLD = 0.5
TRACK_LOSS_TIMEOUT = 2.0
SCAN_ROTATION_COUNT = 8
CENTER_THRESHOLD = 0.2
RESIZE_WIDTH = 192
SKIP_FRAMES = 1
IOU_THRESHOLD = 0.5
MAX_DETECTIONS = 10

#=================================================================
# YOLO Detector
#=================================================================
class YOLODetector:
    def __init__(self, model_size='n'):
        print(f"Loading YOLOv8{model_size} model...")
        try:
            from ultralytics import YOLO
            self.model = YOLO(f'yolov8{model_size}.pt')
            self.model.overrides['verbose'] = False
            self.model.overrides['conf'] = CONFIDENCE_THRESHOLD
            self.model.overrides['iou'] = IOU_THRESHOLD
            self.model.overrides['max_det'] = MAX_DETECTIONS
            self.model.overrides['half'] = True
            self.model.overrides['device'] = 'cpu'
            print("✓ YOLO loaded")
        except Exception as e:
            print(f"ERROR loading YOLO: {e}")
            raise

    def detect(self, frame):
        h, w = frame.shape[:2]
        scale = RESIZE_WIDTH / w
        new_h = int(h * scale)
        resized = cv2.resize(frame, (RESIZE_WIDTH, new_h))
        results = self.model.predict(
            resized,
            verbose=False,
            conf=CONFIDENCE_THRESHOLD,
            iou=IOU_THRESHOLD,
            max_det=MAX_DETECTIONS,
            half=True,
            device='cpu'
        )

        detections = []
        for result in results:
            boxes = result.boxes
            if boxes is None or len(boxes) == 0:
                continue
            for box in boxes:
                cls_id = int(box.cls[0])
                if cls_id in TARGET_CLASSES:
                    conf = float(box.conf[0])
                    if conf >= CONFIDENCE_THRESHOLD:
                        bbox_resized = box.xyxy[0].cpu().numpy()
                        bbox = bbox_resized / scale
                        detections.append({
                            'class_id': cls_id,
                            'class_name': TARGET_CLASSES[cls_id],
                            'confidence': conf,
                            'bbox': bbox
                        })
        return detections

    def get_bbox_center(self, bbox):
        x1, y1, x2, y2 = bbox
        return (x1 + x2) / 2, (y1 + y2) / 2

#=================================================================
# Command Sender
#=================================================================
class CommandSender:
    def __init__(self):
        self.sock = socket.socket(socket.AF_UNIX, socket.SOCK_DGRAM)
        self.last_walk_time = 0
        self.walk_cooldown = 0.3

    def send_command_complete(self):
        try:
            self.sock.sendto(pickle.dumps("complete"), CMD_COMPLETE_SOCKET)
        except Exception as e:
            print(f" Command Send Error: {e}")

    def send_walk_command(self, cmd):
        t = time.time()
        if t - self.last_walk_time < self.walk_cooldown:
            return
        try:
            self.sock.sendto(pickle.dumps(cmd), WALK_SOCKET)
            self.last_walk_time = t
            print(f"  → {cmd}")
        except Exception as e:
            print(f"  ✗ Walk error: {e}")

    def send_buzzer_command(self, text):
        try:
            self.sock.sendto(pickle.dumps(text), BUZZER_SOCKET)
            print(f"  🔊 {text}")
        except Exception as e:
            print(f"  ✗ Buzzer error: {e}")

    def close(self):
        self.sock.close()

#=================================================================
# Target Tracker
#=================================================================
class TargetTracker:
    def __init__(self, detector, commander):
        self.detector = detector
        self.commander = commander
        self.current_target = None
        self.last_seen_time = 0
        self.target_history = deque(maxlen=5)
        self.scanning = False
        self.scan_rotation = 0
        self.last_announced = {}
        self.announcement_cooldown = 4.0
        self.frame_count = 0

    def update(self, frame):
        self.frame_count += 1
        detections = self.detector.detect(frame)
        fh, fw = frame.shape[:2]
        frame_center = fw / 2
        t_now = time.time()

        if detections:
            if self.scanning:
                self.scanning = False
                self.commander.send_buzzer_command("FOUND")
            best = max(detections, key=lambda d: self._bbox_area(d['bbox']))
            cls = best['class_name']

            if self._should_announce(cls, t_now):
                self.commander.send_buzzer_command(cls.upper())
                self.last_announced[cls] = t_now

            self.current_target = best
            self.last_seen_time = t_now
            self.target_history.append(best)

            bx, _ = self.detector.get_bbox_center(best['bbox'])
            offset = bx - frame_center
            off_ratio = abs(offset) / fw

            if off_ratio > CENTER_THRESHOLD:
                self.commander.send_walk_command("rotateRight" if offset > 0 else "rotateLeft")
                print(f"  ↻ Centering {cls} ({off_ratio:.0%} off)")
            else:
                print(f"  ✓ {cls} centered")
        else:
            print("Nothing found.")

        self.commander.send_command_complete()

    def _should_announce(self, cls, t_now):
        if cls not in self.last_announced:
            return True
        return (t_now - self.last_announced[cls]) > self.announcement_cooldown

    def _bbox_area(self, bbox):
        x1, y1, x2, y2 = bbox
        return (x2 - x1) * (y2 - y1)

#=================================================================
# YOLO Commander App
#=================================================================
class YOLOCommander:
    def __init__(self):
        print("="*60)
        print("Yolo: YOLO Vision System")
        print("="*60)
        self.detector = YOLODetector('n')
        self.commander = CommandSender()
        self.tracker = TargetTracker(self.detector, self.commander)
        self.fps_counter = 0
        self.fps_start_time = time.time()
        print("Yolo: ✓ Ready\n")

    def process_frame(self, frame_data):
        try:
            img_bytes = frame_data['image']
            nparr = np.frombuffer(img_bytes, np.uint8)
            frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            if frame is not None:
                self.tracker.update(frame)
                self.fps_counter += 1
                if self.fps_counter % 30 == 0:
                    elapsed = time.time() - self.fps_start_time
                    fps = self.fps_counter / elapsed
                    proc_fps = fps / SKIP_FRAMES
                    print(f"[Performance] Camera: {fps:.1f} FPS | Processing: {proc_fps:.1f} FPS")
            else:
                print("✗ Failed to decode frame")
        except Exception as e:
            print(f"✗ Error processing frame: {e}")

    def close(self):
        if self.fps_counter > 0:
            elapsed = time.time() - self.fps_start_time
            fps = self.fps_counter / elapsed
            proc_fps = fps / SKIP_FRAMES
            print(f"\nFinal: {fps:.1f} camera FPS, {proc_fps:.1f} processing FPS")
        self.commander.close()
        print("✓ YOLO Stopped")

#=================================================================
# Main Entry
#=================================================================
if __name__ == "__main__":
    commander_app = YOLOCommander()

    # Callback for incoming frames
    def on_frame(frame_data):
        commander_app.process_frame(frame_data)

    # Connect to camera via robust StreamListener (client)
    listener = StreamListener(CAMERA_SOCKET, callback=on_frame)
    try:
        listener.processQueue()
    except KeyboardInterrupt:
        print("\nShutdown requested")
    except Exception as e:
        import traceback
        traceback.print_exc()
    finally:
        listener.stop()
        commander_app.close()
