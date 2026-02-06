import cv2
import numpy as np
from rknnlite.api import RKNNLite
import os
import sys

TARGET_CLASSES = {0: "person", 16: "dog", 17: "cat"}
OBJ_THRESH = 0.45
NMS_THRESH = 0.45
IMG_SIZE = (640, 640)

class simpleOrangePiNpuYolo:
    def __init__(self, model_path='yolov5n_rk3588.rknn'):
        # Suppress RKNN C-level warnings
        self._devnull = os.open(os.devnull, os.O_WRONLY)
        self._old_stderr = os.dup(2)
        
        # Redirect stderr during init
        os.dup2(self._devnull, 2)
        
        self.rknn = RKNNLite()
        
        ret = self.rknn.load_rknn(model_path)
        if ret != 0:
            os.dup2(self._old_stderr, 2)  # Restore for error
            raise Exception(f'Load RKNN model failed! Error code: {ret}')
        
        ret = self.rknn.init_runtime(core_mask=RKNNLite.NPU_CORE_AUTO)
        if ret != 0:
            os.dup2(self._old_stderr, 2)  # Restore for error
            raise Exception(f'Init runtime environment failed! Error code: {ret}')
        
        # Restore stderr after init
        os.dup2(self._old_stderr, 2)
        
        sdk_version = self.rknn.get_sdk_version()
        print(f"✓ RKNN SDK: {sdk_version}")
        print(f"✓ Model loaded: {model_path}")
        print(f"✓ NPU core: AUTO")
        
        self.input_size = IMG_SIZE
        self.scale = 1.0
        self.pad_w = 0
        self.pad_h = 0

    def letter_box(self, img):
        img_h, img_w = img.shape[:2]
        new_w, new_h = self.input_size
        
        scale = min(new_w / img_w, new_h / img_h)
        scaled_w = int(img_w * scale)
        scaled_h = int(img_h * scale)
        
        img_resized = cv2.resize(img, (scaled_w, scaled_h))
        
        self.pad_w = (new_w - scaled_w) // 2
        self.pad_h = (new_h - scaled_h) // 2
        self.scale = scale
        
        img_padded = np.full((new_h, new_w, 3), 0, dtype=np.uint8)
        img_padded[self.pad_h:self.pad_h+scaled_h, 
                   self.pad_w:self.pad_w+scaled_w] = img_resized
        
        return img_padded

    def detect_objects(self, frame):
        # Suppress only during inference
        os.dup2(self._devnull, 2)
        
        img = self.letter_box(frame)
        img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        img_batched = np.expand_dims(img_rgb, axis=0)
        
        outputs = self.rknn.inference(inputs=[img_batched])
        
        # Restore immediately
        os.dup2(self._old_stderr, 2)
        
        if outputs is None:
            return []
        
        return self.postprocess(outputs, frame.shape)

    @staticmethod
    def get_bbox_center(bbox):
        return (bbox[0] + bbox[2]) / 2, (bbox[1] + bbox[3]) / 2

    def __del__(self):
        if hasattr(self, '_old_stderr'):
            os.close(self._old_stderr)
        if hasattr(self, '_devnull'):
            os.close(self._devnull)
        if hasattr(self, 'rknn'):
            self.rknn.release()

    def postprocess(self, outputs, original_shape):
        if outputs is None or len(outputs) == 0:
            return []
        
        anchors = np.array([
            [[10, 13], [16, 30], [33, 23]],
            [[30, 61], [62, 45], [59, 119]],
            [[116, 90], [156, 198], [373, 326]]
        ])
        
        strides = [8, 16, 32]
        all_detections = []
        
        for i, output in enumerate(outputs):
            batch, channels, grid_h, grid_w = output.shape
            
            output = output.reshape(batch, 3, 85, grid_h, grid_w)
            output = output.transpose(0, 1, 3, 4, 2)
            
            output[..., 0:2] = 1 / (1 + np.exp(-output[..., 0:2]))
            output[..., 4:] = 1 / (1 + np.exp(-output[..., 4:]))
            
            anchor = anchors[i]
            stride = strides[i]
            
            grid_y, grid_x = np.meshgrid(np.arange(grid_h), np.arange(grid_w), indexing='ij')
            grid = np.stack([grid_x, grid_y], axis=-1)
            
            for anc_idx in range(3):
                pred = output[0, anc_idx]
                
                xy = (pred[..., 0:2] * 2 - 0.5 + grid) * stride
                wh = (pred[..., 2:4] * 2) ** 2 * anchor[anc_idx]
                
                obj_conf = pred[..., 4]
                class_scores = pred[..., 5:]
                
                mask = obj_conf > OBJ_THRESH
                if not mask.any():
                    continue
                
                xy_valid = xy[mask]
                wh_valid = wh[mask]
                obj_valid = obj_conf[mask]
                cls_valid = class_scores[mask]
                
                class_ids = np.argmax(cls_valid, axis=1)
                class_confs = cls_valid[np.arange(len(cls_valid)), class_ids]
                
                for idx, cls_id in enumerate(class_ids):
                    if cls_id not in TARGET_CLASSES:
                        continue
                    
                    confidence = obj_valid[idx] * class_confs[idx]
                    if confidence < OBJ_THRESH:
                        continue
                    
                    cx, cy = xy_valid[idx]
                    w, h = wh_valid[idx]
                    
                    x1 = (cx - w/2 - self.pad_w) / self.scale
                    y1 = (cy - h/2 - self.pad_h) / self.scale
                    x2 = (cx + w/2 - self.pad_w) / self.scale
                    y2 = (cy + h/2 - self.pad_h) / self.scale
                    
                    # Clip to frame boundaries
                    x1 = max(0, min(x1, original_shape[1]))
                    y1 = max(0, min(y1, original_shape[0]))
                    x2 = max(0, min(x2, original_shape[1]))
                    y2 = max(0, min(y2, original_shape[0]))
                    
                    # Reject degenerate boxes
                    box_w = x2 - x1
                    box_h = y2 - y1
                    if box_w < 5 or box_h < 5:
                        continue
                    
                    # Aspect ratio sanity check for people
                    aspect = box_w / box_h
                    if cls_id == 0 and (aspect > 3.0 or aspect < 0.2):
                        continue
                    
                    all_detections.append({
                        'class_id': int(cls_id),
                        'class_name': TARGET_CLASSES[cls_id],
                        'confidence': float(confidence),
                        'bbox': np.array([x1, y1, x2, y2])
                    })
        
        # NMS
        if len(all_detections) > 0:
            boxes = np.array([d['bbox'] for d in all_detections])
            scores = np.array([d['confidence'] for d in all_detections])
            classes = np.array([d['class_id'] for d in all_detections])
            
            final_detections = []
            for cls in np.unique(classes):
                cls_mask = classes == cls
                cls_boxes = boxes[cls_mask]
                cls_scores = scores[cls_mask]
                cls_dets = [all_detections[i] for i, m in enumerate(cls_mask) if m]
                
                indices = cv2.dnn.NMSBoxes(
                    cls_boxes.tolist(),
                    cls_scores.tolist(),
                    OBJ_THRESH,
                    NMS_THRESH
                )
                
                for idx in indices:
                    final_detections.append(cls_dets[idx])
            
            return final_detections
        
        return []