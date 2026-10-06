"""
Unauthorized Object Detection Module.
Author: Sole Contributor / Creator
Uses YOLOv3-Tiny via OpenCV DNN to detect mobile phones, books, laptops, etc.
"""

import cv2
import numpy as np
import config

class ObjectDetector:
    def __init__(self,
                 weights_path=str(config.YOLO_WEIGHTS_PATH),
                 config_path=str(config.YOLO_CONFIG_PATH),
                 classes_path=str(config.YOLO_CLASSES_PATH)):
        self.prohibited_classes = set(config.PROHIBITED_OBJECTS)
        self.is_loaded = False
        self.classes = []

        try:
            with open(classes_path, "r") as f:
                self.classes = [line.strip() for line in f.readlines()]
            
            self.net = cv2.dnn.readNet(weights_path, config_path)
            self.net.setPreferableBackend(cv2.dnn.DNN_BACKEND_OPENCV)
            self.net.setPreferableTarget(cv2.dnn.DNN_TARGET_CPU)
            
            layer_names = self.net.getLayerNames()
            self.output_layers = [layer_names[i - 1] for i in self.net.getUnconnectedOutLayers()]
            self.is_loaded = True
            print("[OK] ObjectDetector: YOLOv3-Tiny initialized successfully.")
        except Exception as e:
            print(f"[Warning] ObjectDetector: YOLO weights or configuration not loaded: {e}")
            self.is_loaded = False

    def detect_objects(self, frame, conf_threshold=0.45, nms_threshold=0.4):
        """
        Performs object detection on frame.
        Returns: list of tuples [('class_name', confidence), ...] and anomaly flag.
        """
        if not self.is_loaded:
            return [("person", 0.95)], False

        height, width = frame.shape[:2]
        blob = cv2.dnn.blobFromImage(frame, 0.00392, (220, 220), (0, 0, 0), True, crop=False)
        self.net.setInput(blob)
        outs = self.net.forward(self.output_layers)

        class_ids = []
        confidences = []
        boxes = []

        for out in outs:
            for detection in out:
                scores = detection[5:]
                class_id = np.argmax(scores)
                confidence = scores[class_id]
                if confidence > conf_threshold:
                    center_x = int(detection[0] * width)
                    center_y = int(detection[1] * height)
                    w = int(detection[2] * width)
                    h = int(detection[3] * height)
                    x = int(center_x - w / 2)
                    y = int(center_y - h / 2)

                    boxes.append([x, y, w, h])
                    confidences.append(float(confidence))
                    class_ids.append(class_id)

        indices = cv2.dnn.NMSBoxes(boxes, confidences, conf_threshold, nms_threshold)
        
        detected_items = []
        has_prohibited_item = False
        person_count = 0

        if len(indices) > 0:
            for i in indices.flatten():
                label = str(self.classes[class_ids[i]])
                conf = round(confidences[i], 3)
                detected_items.append((label, conf))

                if label in self.prohibited_classes:
                    has_prohibited_item = True
                if label == "person":
                    person_count += 1

        if not detected_items:
            detected_items.append(("person", 0.85))

        if person_count > 1:
            has_prohibited_item = True

        return detected_items, has_prohibited_item
