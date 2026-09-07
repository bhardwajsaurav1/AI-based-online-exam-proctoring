"""
3D Head Pose Estimation Module.
Author: Sole Contributor / Creator
Estimates 3D Head Orientation (Yaw, Pitch, Roll) using Perspective-n-Point (solvePnP).
"""

import cv2
import numpy as np
import config

class HeadPoseEstimator:
    def __init__(self):
        # 3D Model Coordinates of facial keypoints in world space
        self.model_points = np.array([
            (0.0, 0.0, 0.0),             # Nose tip (30)
            (0.0, -330.0, -65.0),        # Chin (8)
            (-225.0, 170.0, -135.0),     # Left eye left corner (36)
            (225.0, 170.0, -135.0),      # Right eye right corner (45)
            (-150.0, -150.0, -125.0),    # Left Mouth corner (48)
            (150.0, -150.0, -125.0)      # Right mouth corner (54)
        ], dtype=np.float64)

        # 3D Axis points for visual vector projection
        self.axis_3d = np.array([
            (500.0, 0.0, 0.0),
            (0.0, 500.0, 0.0),
            (0.0, 0.0, -500.0)
        ], dtype=np.float64)

    def estimate_pose(self, landmarks, frame_shape):
        """
        Calculates rotation vector, translation vector, and Euler angles.
        Returns: { 'pitch': float, 'yaw': float, 'roll': float, 'is_looking_away': bool, 'nose_end_point2D': ... }
        """
        if landmarks is None:
            return {"pitch": 0.0, "yaw": 0.0, "roll": 0.0, "is_looking_away": False, "score": -1}

        height, width = frame_shape[:2]

        # 2D Image Points extracted from Dlib landmarks
        image_points = np.array([
            (landmarks.part(30).x, landmarks.part(30).y),     # Nose tip
            (landmarks.part(8).x, landmarks.part(8).y),       # Chin
            (landmarks.part(36).x, landmarks.part(36).y),     # Left eye corner
            (landmarks.part(45).x, landmarks.part(45).y),     # Right eye corner
            (landmarks.part(48).x, landmarks.part(48).y),     # Left mouth corner
            (landmarks.part(54).x, landmarks.part(54).y)      # Right mouth corner
        ], dtype=np.float64)

        # Camera Internals approximation
        focal_length = width
        center = (width / 2, height / 2)
        camera_matrix = np.array([
            [focal_length, 0, center[0]],
            [0, focal_length, center[1]],
            [0, 0, 1]
        ], dtype=np.float64)

        dist_coeffs = np.zeros((4, 1))

        # Solve Perspective-n-Point
        success, rvec, tvec = cv2.solvePnP(
            self.model_points, image_points, camera_matrix, dist_coeffs, flags=cv2.SOLVEPNP_ITERATIVE
        )

        if not success:
            return {"pitch": 0.0, "yaw": 0.0, "roll": 0.0, "is_looking_away": False, "score": -1}

        # Project 3D axis to 2D image
        (nose_end_point2D, _) = cv2.projectPoints(
            self.axis_3d, rvec, tvec, camera_matrix, dist_coeffs
        )

        # Convert rotation vector to rotation matrix
        rmat, _ = cv2.Rodrigues(rvec)
        
        # Extract Euler Angles (Pitch, Yaw, Roll)
        sy = np.sqrt(rmat[0, 0] * rmat[0, 0] + rmat[1, 0] * rmat[1, 0])
        singular = sy < 1e-6

        if not singular:
            pitch = np.arctan2(rmat[2, 1], rmat[2, 2])
            yaw = np.arctan2(-rmat[2, 0], sy)
            roll = np.arctan2(rmat[1, 0], rmat[0, 0])
        else:
            pitch = np.arctan2(-rmat[1, 2], rmat[1, 1])
            yaw = np.arctan2(-rmat[2, 0], sy)
            roll = 0

        # Convert to degrees
        pitch_deg = np.degrees(pitch)
        yaw_deg = np.degrees(yaw)
        roll_deg = np.degrees(roll)

        is_looking_away = (abs(pitch_deg) > config.HEAD_PITCH_THRESHOLD) or (abs(yaw_deg) > config.HEAD_YAW_THRESHOLD)

        return {
            "pitch": round(float(pitch_deg), 2),
            "yaw": round(float(yaw_deg), 2),
            "roll": round(float(roll_deg), 2),
            "is_looking_away": is_looking_away,
            "score": round(float(abs(pitch_deg) + abs(yaw_deg)), 2),
            "nose_pt": (int(image_points[0][0]), int(image_points[0][1])),
            "proj_pt": (int(nose_end_point2D[0][0][0]), int(nose_end_point2D[0][0][1]))
        }
