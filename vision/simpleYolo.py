import cv2
import numpy as np
from ultralytics import YOLO

TARGET_CLASSES = {0: "person", 16: "dog", 17: "cat"}
CONFIDENCE_THRESHOLD = 0.5
IOU_THRESHOLD = 0.5
MAX_DETECTIONS = 10
RESIZE_WIDTH = 192

class simpleYolo:
    def __init__(self, model_size='n', device='cpu'):
        print("CTOR Simple Yolo")
        """Load YOLOv8 model"""
        print(f"Loading YOLOv8{model_size} model...")
        self.model = YOLO(f'yolov8{model_size}.pt')
        self.model.overrides.update({
            'verbose': False,
            'conf': CONFIDENCE_THRESHOLD,
            'iou': IOU_THRESHOLD,
            'max_det': MAX_DETECTIONS,
            'half': True,
            'device': device
        })
        print("✓ YOLO loaded")

    def detect_objects(self, frame):



        """
        Detect objects in a single frame.
        Returns a list of dicts:
        [{'class_id': int, 'class_name': str, 'confidence': float, 'bbox': [x1,y1,x2,y2]}, ...]
        """
        h, w = frame.shape[:2]
        scale = RESIZE_WIDTH / w
        new_h = int(h * scale)
        resized = cv2.resize(frame, (RESIZE_WIDTH, new_h))

        results = self.model.predict(resized, verbose=False)
        detections = []

        for result in results:
            if not result.boxes:
                continue
            for box in result.boxes:
                cls_id = int(box.cls[0])
                if cls_id not in TARGET_CLASSES:
                    continue
                conf = float(box.conf[0])
                if conf < CONFIDENCE_THRESHOLD:
                    continue
                bbox_resized = box.xyxy[0].cpu().numpy()
                bbox = bbox_resized / scale
                detections.append({
                    'class_id': cls_id,
                    'class_name': TARGET_CLASSES[cls_id],
                    'confidence': conf,
                    'bbox': bbox
                })
        self._processing = False
        return detections

    @staticmethod
    def get_bbox_center(bbox):
        x1, y1, x2, y2 = bbox
        return (x1 + x2) / 2, (y1 + y2) / 2
