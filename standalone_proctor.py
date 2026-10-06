"""
Standalone Desktop AI Proctoring Runner (OpenCV Direct View).
Author: Sole Contributor / Creator
"""

import cv2
import config
from core.proctor_engine import ProctorEngine
from backend.logger import ForensicLogger

def main():
    print("=" * 60)
    print("AI-Based Online Exam Proctoring System - Desktop Mode")
    print("Author: Sole Contributor / Creator")
    print("Press 'q' or 'ESC' to exit.")
    print("=" * 60)

    engine = ProctorEngine()
    logger = ForensicLogger()

    cam = cv2.VideoCapture(config.CAMERA_INDEX)
    if not cam.isOpened():
        print("[Error] Could not access camera.")
        return

    while True:
        ret, frame = cam.read()
        if not ret:
            break

        annotated_frame, telemetry, raw_vector = engine.process_frame(frame)
        logger.log_record(raw_vector, telemetry)

        # Render status banner on frame
        color = (0, 0, 255) if telemetry["is_violation"] else (0, 255, 0)
        status_text = f"Status: {telemetry['face_status']} | Gaze: {telemetry['gaze_direction']} | Warnings: {telemetry['warning_count']}"
        cv2.putText(annotated_frame, status_text, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)

        cv2.imshow("AI Exam Proctoring Monitor", annotated_frame)

        key = cv2.waitKey(1) & 0xFF
        if key == ord('q') or key == 27:
            break

    cam.release()
    cv2.destroyAllWindows()
    print("[OK] Session terminated. Logs saved to activity.txt.")

if __name__ == "__main__":
    main()
