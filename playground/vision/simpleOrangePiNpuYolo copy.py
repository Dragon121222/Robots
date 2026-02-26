import cv2
import numpy as np
from rknnlite.api import RKNNLite

TARGET_CLASSES = {0: "person", 16: "dog", 17: "cat"}
CONFIDENCE_THRESHOLD = 0.5
IOU_THRESHOLD = 0.5
MAX_DETECTIONS = 10
RESIZE_WIDTH = 640  # RKNN models typically use 640x640

class simpleOrangePiNpuYolo:
    def __init__(self, model_path='yolov5n_rk3588.rknn', target='rk3588'):
        print("CTOR Simple Orange Pi NPU Yolo")
        """Load RKNN model for NPU inference"""
        print(f"Loading RKNN model: {model_path}")
        
        self.rknn = RKNNLite()
        
        # Load RKNN model
        ret = self.rknn.load_rknn(model_path)
        if ret != 0:
            raise Exception(f'Load RKNN model failed! Error code: {ret}')
        
        # Initialize runtime environment
        ret = self.rknn.init_runtime(
            core_mask=RKNNLite.NPU_CORE_AUTO
        )


        if ret != 0:
            raise Exception(f'Init runtime environment failed! Error code: {ret}')
        
        print("✓ RKNN model loaded on NPU")
        
        # Get model input/output info
        self.input_size = (640, 640)  # YOLOv5 default
        
    def preprocess(self, frame):
        """Preprocess image for RKNN model"""
        # Resize to model input size
        resized = cv2.resize(frame, self.input_size)
        # Convert BGR to RGB
        rgb = cv2.cvtColor(resized, cv2.COLOR_BGR2RGB)
        return rgb
    
    def postprocess(self, outputs, original_shape):
        """Process RKNN output to detections"""
        detections = []
        
        # YOLOv5 RKNN output format: [batch, num_boxes, 85]
        # 85 = x, y, w, h, obj_conf, class_conf[80]
        predictions = outputs[0][0]  # Remove batch dimension
        
        h_orig, w_orig = original_shape[:2]
        h_model, w_model = self.input_size
        
        for pred in predictions:
            # pred format: [center_x, center_y, width, height, objectness, class_scores...]
            obj_conf = pred[4]
            
            if obj_conf < CONFIDENCE_THRESHOLD:
                continue
            
            # Get class scores (80 COCO classes)
            class_scores = pred[5:]
            class_id = np.argmax(class_scores)
            class_conf = class_scores[class_id]
            
            # Filter by target classes
            if class_id not in TARGET_CLASSES:
                continue
            
            # Combined confidence
            confidence = obj_conf * class_conf
            if confidence < CONFIDENCE_THRESHOLD:
                continue
            
            # Convert from center format to corner format
            cx, cy, w, h = pred[:4]
            
            # Scale coordinates back to original image size
            x1 = (cx - w/2) * w_orig / w_model
            y1 = (cy - h/2) * h_orig / h_model
            x2 = (cx + w/2) * w_orig / w_model
            y2 = (cy + h/2) * h_orig / h_model
            
            detections.append({
                'class_id': class_id,
                'class_name': TARGET_CLASSES[class_id],
                'confidence': float(confidence),
                'bbox': np.array([x1, y1, x2, y2])
            })
        
        return detections
    
    def detect_objects(self, frame):
        """
        Detect objects in a single frame using NPU.
        Returns a list of dicts:
        [{'class_id': int, 'class_name': str, 'confidence': float, 'bbox': [x1,y1,x2,y2]}, ...]
        """
        original_shape = frame.shape
        
        # Preprocess
        input_data = self.preprocess(frame)
        
        # Run inference on NPU
        outputs = self.rknn.inference(inputs=[input_data])
        
        # Postprocess
        detections = self.postprocess(outputs, original_shape)
        
        return detections
    
    @staticmethod
    def get_bbox_center(bbox):
        x1, y1, x2, y2 = bbox
        return (x1 + x2) / 2, (y1 + y2) / 2
    
    def __del__(self):
        """Cleanup RKNN runtime"""
        if hasattr(self, 'rknn'):
            self.rknn.release()