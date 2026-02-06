#!/usr/bin/env python3
# yolo_debug_snapshots.py
"""
Debug tool that reads from camera FIFO and saves annotated images
showing what YOLO detects. Useful for tuning parameters.
"""
import cv2
import pickle
import numpy as np
import time
from pathlib import Path
from datetime import datetime

try:
    from ultralytics import YOLO
except ImportError:
    print("Install YOLOv8: pip install ultralytics --break-system-packages")
    exit(1)

# Configuration
CAMERA_FIFO = "/tmp/cameraImageFifo"
OUTPUT_DIR = "/tmp/yolo_debug"
TARGET_CLASSES = {0: "person", 16: "dog", 17: "cat"}
CONFIDENCE_THRESHOLD = 0.5

# Create output directory
Path(OUTPUT_DIR).mkdir(parents=True, exist_ok=True)

print("=" * 60)
print("YOLO Debug Snapshots")
print("=" * 60)
print(f"Reading from: {CAMERA_FIFO}")
print(f"Saving to: {OUTPUT_DIR}")
print(f"Confidence threshold: {CONFIDENCE_THRESHOLD}")
print("=" * 60)

# Load model
print("\nLoading YOLOv8 nano model...")
model = YOLO('yolov8n.pt')
print("✓ Model loaded\n")

print("Waiting for camera frames...")
print("Make sure cameraCommanderApp is running in 'start' mode")
print("Press Ctrl+C to stop\n")

frame_count = 0
detection_count = 0

try:
    while True:
        try:
            # Read frame from FIFO
            with open(CAMERA_FIFO, 'rb') as f:
                image_data = pickle.load(f)
            
            # Decode image
            image_bytes = image_data['image']
            nparr = np.frombuffer(image_bytes, np.uint8)
            frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            
            if frame is None:
                print("Failed to decode frame")
                continue
            
            frame_count += 1
            
            # Run detection
            results = model(frame, verbose=False)
            
            # Draw on frame
            annotated_frame = frame.copy()
            detections_found = []
            
            for result in results:
                boxes = result.boxes
                for box in boxes:
                    class_id = int(box.cls[0])
                    
                    if class_id in TARGET_CLASSES:
                        confidence = float(box.conf[0])
                        
                        if confidence >= CONFIDENCE_THRESHOLD:
                            bbox = box.xyxy[0].cpu().numpy()
                            x1, y1, x2, y2 = map(int, bbox)
                            
                            class_name = TARGET_CLASSES[class_id]
                            detections_found.append(class_name)
                            detection_count += 1
                            
                            # Draw bounding box
                            color = (0, 255, 0)  # Green
                            cv2.rectangle(annotated_frame, (x1, y1), (x2, y2), color, 2)
                            
                            # Draw label
                            label = f"{class_name} {confidence:.2f}"
                            label_size, _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 2)
                            cv2.rectangle(annotated_frame, 
                                        (x1, y1 - label_size[1] - 10),
                                        (x1 + label_size[0], y1),
                                        color, -1)
                            cv2.putText(annotated_frame, label, (x1, y1 - 5),
                                      cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 0), 2)
                            
                            # Draw center crosshair
                            cx = (x1 + x2) // 2
                            cy = (y1 + y2) // 2
                            cv2.drawMarker(annotated_frame, (cx, cy), color,
                                         cv2.MARKER_CROSS, 20, 2)
            
            # Add frame info
            height, width = frame.shape[:2]
            cv2.putText(annotated_frame, f"Frame: {frame_count}", (10, 30),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
            
            if detections_found:
                cv2.putText(annotated_frame, 
                          f"Detected: {', '.join(detections_found)}", 
                          (10, 60),
                          cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
            
            # Draw center line
            cv2.line(annotated_frame, (width//2, 0), (width//2, height), 
                    (0, 255, 255), 1)
            
            # Save if there were detections
            if detections_found:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
                filename = f"detection_{timestamp}.jpg"
                filepath = Path(OUTPUT_DIR) / filename
                cv2.imwrite(str(filepath), annotated_frame)
                
                print(f"✓ Frame {frame_count}: {', '.join(detections_found)} → {filename}")
            else:
                # Save every 50th frame even without detection
                if frame_count % 50 == 0:
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
                    filename = f"frame_{timestamp}.jpg"
                    filepath = Path(OUTPUT_DIR) / filename
                    cv2.imwrite(str(filepath), annotated_frame)
                    print(f"  Frame {frame_count} (no detections)")
            
        except FileNotFoundError:
            print("Waiting for camera FIFO...")
            time.sleep(1)
        except Exception as e:
            print(f"Error: {e}")
            time.sleep(0.1)

except KeyboardInterrupt:
    print("\n\n" + "=" * 60)
    print("Debug Session Summary")
    print("=" * 60)
    print(f"Frames processed: {frame_count}")
    print(f"Total detections: {detection_count}")
    print(f"Images saved to: {OUTPUT_DIR}")
    print("=" * 60)
    print("\nView images with:")
    print(f"  ls -lh {OUTPUT_DIR}")
    print(f"  eog {OUTPUT_DIR}/*.jpg  # (if GUI available)")
