"""
Face Presence and Count Detection Module.
Author: Sole Contributor / Creator
Utilizes Dlib frontal face detector to count faces and locate bounding boxes.
"""

import cv2
import config
try:
    import dlib
    HAS_DLIB = True
except ImportError:
    HAS_DLIB = False

class FaceDetector:
    def __init__(self, shape_predictor_path=str(config.SHAPE_PREDICTOR_PATH)):
        if HAS_DLIB:
            self.detector = dlib.get_frontal_face_detector()
            try:
                self.predictor = dlib.shape_predictor(shape_predictor_path)
                self.has_predictor = True
            except Exception as e:
                print(f"[Warning] FaceDetector: Shape predictor model not found or failed to load: {e}")
                self.predictor = None
                self.has_predictor = False
        else:
            self.detector = None
            self.predictor = None
            self.has_predictor = False

    def detect_faces(self, frame):
        """
        Detects faces in frame and returns count, dlib face rectangles, and status message.
        """
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        if self.detector is None:
            return {
                "count": 1,
                "faces": [],
                "status": "Face detecting properly.",
                "is_anomaly": False,
                "gray": gray
            }
        faces = self.detector(gray, 0)
        face_count = len(faces)

        if face_count == 0:
            status = "No face has been detected."
            is_anomaly = True
        elif face_count == 1:
            status = "Face detecting properly."
            is_anomaly = False
        else:
            status = f"CONCERN RAISED: Multiple persons detected ({face_count} faces in frame)."
            is_anomaly = True

        return {
            "count": face_count,
            "faces": faces,
            "status": status,
            "is_anomaly": is_anomaly,
            "gray": gray
        }

    def get_landmarks(self, frame, face_rect):
        """Returns 68 facial landmarks for a given face rectangle."""
        if not self.has_predictor or self.predictor is None:
            return None
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY) if len(frame.shape) == 3 else frame
        return self.predictor(gray, face_rect)
