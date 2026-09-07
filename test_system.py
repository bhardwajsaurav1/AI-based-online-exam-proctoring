"""
Verification & Diagnostic Test Suite.
"""
import sys
import numpy as np
import cv2
import config
from backend.database import Database
from backend.logger import ForensicLogger
from core.face_detector import FaceDetector
from core.head_pose import HeadPoseEstimator
from core.blink_detector import BlinkDetector
from core.mouth_tracker import MouthTracker
from core.object_detector import ObjectDetector
from core.proctor_engine import ProctorEngine

def run_tests():
    print("=" * 60)
    print("Running Diagnostics & Unit Tests on AI Proctoring System")
    print("=" * 60)

    # 1. Test Database
    print("[1/5] Testing Database Adapter...")
    db = Database()
    auth_ok = db.authenticate_user("student1", "password123")
    assert auth_ok is not None, "Failed authenticating demo user"
    print(f"  [PASS] Database & Default User Verified: {auth_ok}")

    # 2. Test Face Detector & Shape Predictor
    print("[2/5] Testing Face Detector & Landmark Predictor...")
    face_det = FaceDetector()
    assert face_det.has_predictor, "Shape predictor not loaded"
    dummy_frame = np.zeros((480, 640, 3), dtype=np.uint8)
    res = face_det.detect_faces(dummy_frame)
    assert res["count"] == 0, "Dummy frame should have 0 faces"
    print(f"  [PASS] Face Detector Initialized. Status: {res['status']}")

    # 3. Test YOLO Object Detector
    print("[3/5] Testing YOLOv3-Tiny Object Detector...")
    obj_det = ObjectDetector()
    assert obj_det.is_loaded, "YOLOv3-Tiny network failed to load"
    objs, violation = obj_det.detect_objects(dummy_frame)
    print(f"  [PASS] Object Detector Initialized ({len(obj_det.classes)} COCO classes).")

    # 4. Test Head Pose, Blink, Mouth
    print("[4/5] Testing Facial Geometry Modules...")
    pose_est = HeadPoseEstimator()
    blink_det = BlinkDetector()
    mouth_trk = MouthTracker()
    print("  [PASS] Pose, Blink, and Mouth tracking modules initialized.")

    # 5. Test Full ProctorEngine & Logger
    print("[5/5] Testing ProctorEngine End-to-End Pipeline...")
    engine = ProctorEngine()
    logger = ForensicLogger()
    annotated_frame, telemetry, raw_vector = engine.process_frame(dummy_frame)
    logger.log_record(raw_vector, telemetry)
    assert "timestamp" in telemetry
    assert config.ACTIVITY_LOG_TXT.exists()
    print(f"  [PASS] ProctorEngine processed test frame successfully.")
    print(f"  Telemetry Vector: {raw_vector}")

    print("=" * 60)
    print("ALL DIAGNOSTIC & VERIFICATION TESTS PASSED (5/5)")
    print("=" * 60)

if __name__ == "__main__":
    run_tests()
