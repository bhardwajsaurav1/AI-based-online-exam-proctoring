"""
Master Proctoring Orchestration Engine.
Author: Sole Contributor / Creator
Coordinates Face, Eye, Blink, Pose, Mouth, Object, and Audio detectors into a unified frame telemetry pipeline.
"""

import cv2
import time
from datetime import datetime
import config
from .face_detector import FaceDetector
from .eye_tracker import EyeGazeTracker
from .blink_detector import BlinkDetector
from .head_pose import HeadPoseEstimator
from .mouth_tracker import MouthTracker
from .object_detector import ObjectDetector
from .audio_monitor import AudioMonitor

# Windows auditory warning alert
try:
    import winsound
    HAS_WINSOUND = True
except ImportError:
    HAS_WINSOUND = False

class ProctorEngine:
    def __init__(self):
        self.face_detector = FaceDetector()
        self.eye_tracker = EyeGazeTracker()
        self.blink_detector = BlinkDetector()
        self.head_pose = HeadPoseEstimator()
        self.mouth_tracker = MouthTracker()
        self.object_detector = ObjectDetector()
        self.audio_monitor = AudioMonitor()
        self.audio_monitor.start()

        self.warning_count = 0
        self.last_beep_time = 0

    def trigger_auditory_alert(self):
        """Emits an audible warning beep (throttled)."""
        current_time = time.time()
        if current_time - self.last_beep_time > 2.0:
            self.last_beep_time = current_time
            if HAS_WINSOUND:
                try:
                    winsound.Beep(config.AUDIO_ALERT_FREQUENCY, config.AUDIO_ALERT_DURATION)
                except Exception:
                    pass

    def process_frame(self, frame):
        """
        Executes full multi-modal detection suite on a single video frame.
        Returns: (annotated_frame, telemetry_dict, raw_log_vector)
        """
        timestamp_str = datetime.now().strftime("%H:%M:%S.%f")
        
        # 1. Face Presence & Landmarks
        face_res = self.face_detector.detect_faces(frame)
        face_status = face_res["status"]
        faces = face_res["faces"]
        gray = face_res["gray"]

        landmarks = None
        if len(faces) > 0:
            landmarks = self.face_detector.get_landmarks(frame, faces[0])

        # 2. Eye Gaze Tracking
        landmarks_list = [landmarks] if landmarks else []
        gaze_direction = self.eye_tracker.detect_gaze(faces, landmarks_list, gray)

        # 3. Blink Detection & Liveness
        blink_status, ear_value = self.blink_detector.evaluate_blink(landmarks)

        # 4. Head Pose Estimation
        pose_res = self.head_pose.estimate_pose(landmarks, frame.shape)

        # 5. Mouth Movement / Speech
        mouth_status, mar_value = self.mouth_tracker.detect_mouth_state(landmarks)

        # 6. Object Detection (YOLO)
        detected_objects, has_prohibited_obj = self.object_detector.detect_objects(frame)

        # 7. Audio Monitoring
        audio_res = self.audio_monitor.get_audio_status()

        # Determine Global Violation Flag
        is_violation = (
            face_res["is_anomaly"] or
            pose_res["is_looking_away"] or
            has_prohibited_obj or
            audio_res["is_suspicious"] or
            (gaze_direction in ["left", "right"])
        )

        if is_violation:
            self.warning_count += 1
            self.trigger_auditory_alert()

        # Annotate Visual HUD on Frame
        annotated_frame = frame.copy()
        
        # Draw bounding boxes for faces
        for idx, face in enumerate(faces):
            x, y, w, h = face.left(), face.top(), face.width(), face.height()
            is_multi = len(faces) >= 2
            color = (0, 0, 255) if (is_violation or is_multi) else (0, 255, 0)
            cv2.rectangle(annotated_frame, (x, y), (x + w, y + h), color, 2)
            if is_multi:
                cv2.putText(annotated_frame, f"CONCERN: Person {idx+1}", (x, max(15, y - 8)),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.55, (0, 0, 255), 2)

        if len(faces) >= 2:
            cv2.putText(annotated_frame, f"CONCERN: MULTIPLE PERSONS DETECTED ({len(faces)})", (20, 40),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.75, (0, 0, 255), 2)

        # Draw Head Pose Orientation vector
        if landmarks and "nose_pt" in pose_res and "proj_pt" in pose_res:
            cv2.line(annotated_frame, pose_res["nose_pt"], pose_res["proj_pt"], (255, 255, 0), 2)

        # Telemetry Dictionary
        telemetry = {
            "timestamp": timestamp_str,
            "face_status": face_status,
            "face_count": face_res["count"],
            "blink_status": blink_status,
            "ear_value": ear_value,
            "gaze_direction": gaze_direction,
            "mouth_status": mouth_status,
            "mar_value": mar_value,
            "head_pitch": pose_res["pitch"],
            "head_yaw": pose_res["yaw"],
            "head_looking_away": pose_res["is_looking_away"],
            "detected_objects": detected_objects,
            "audio_status": audio_res["status"],
            "audio_volume": audio_res["volume"],
            "is_violation": is_violation,
            "warning_count": self.warning_count
        }

        # Formatted Vector identical to reference activity.txt output:
        # [Timestamp, FaceStatus, Blink, Gaze, Mouth, Objects, PoseScore]
        raw_log_vector = [
            timestamp_str,
            face_status,
            blink_status,
            gaze_direction,
            mouth_status,
            detected_objects,
            pose_res.get("score", -1)
        ]

        return annotated_frame, telemetry, raw_log_vector
