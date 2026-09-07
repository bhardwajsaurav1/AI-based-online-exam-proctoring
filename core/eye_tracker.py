"""
Eye Gaze & Tracking Module.
Author: Sole Contributor / Creator
Determines gaze direction (Center, Left, Right) using pupil/sclera segmentation.
"""

import cv2
import numpy as np
import config

class EyeGazeTracker:
    def __init__(self):
        # 68-landmark indices for left and right eyes
        self.LEFT_EYE_INDICES = [36, 37, 38, 39, 40, 41]
        self.RIGHT_EYE_INDICES = [42, 43, 44, 45, 46, 47]

    def _create_eye_mask(self, points, frame_shape):
        """Creates a binary mask for an eye region."""
        mask = np.zeros(frame_shape[:2], dtype=np.uint8)
        cv2.fillPoly(mask, [points], 255)
        return mask

    def _get_gaze_ratio(self, eye_points, landmarks, gray_frame):
        """Computes the sclera/pupil ratio for gaze direction estimation."""
        points = np.array([(landmarks.part(point).x, landmarks.part(point).y) for point in eye_points], np.int32)
        
        min_x = np.min(points[:, 0])
        max_x = np.max(points[:, 0])
        min_y = np.min(points[:, 1])
        max_y = np.max(points[:, 1])

        if max_x <= min_x or max_y <= min_y:
            return 1.0

        eye_crop = gray_frame[min_y:max_y, min_x:max_x]
        if eye_crop.size == 0:
            return 1.0

        # Apply thresholding to isolate pupil/iris
        _, thresh = cv2.threshold(eye_crop, 70, 255, cv2.THRESH_BINARY_INV)
        
        h, w = thresh.shape
        half_w = int(w / 2)
        if half_w == 0:
            return 1.0

        left_side = thresh[0:h, 0:half_w]
        right_side = thresh[0:h, half_w:w]

        left_white = cv2.countNonZero(left_side)
        right_white = cv2.countNonZero(right_side)

        if right_white == 0:
            return 3.0  # Extreme looking right
        if left_white == 0:
            return 0.33 # Extreme looking left

        return left_white / right_white

    def detect_gaze(self, faces, landmarks_list, gray_frame):
        """
        Evaluates gaze direction across both eyes.
        Returns: 'center', 'left', 'right' or 'unknown'.
        """
        if not faces or not landmarks_list:
            return "center"

        try:
            landmarks = landmarks_list[0]
            left_ratio = self._get_gaze_ratio(self.LEFT_EYE_INDICES, landmarks, gray_frame)
            right_ratio = self._get_gaze_ratio(self.RIGHT_EYE_INDICES, landmarks, gray_frame)

            avg_ratio = (left_ratio + right_ratio) / 2.0

            if avg_ratio < config.GAZE_RATIO_LEFT_THRESH:
                return "left"
            elif avg_ratio > config.GAZE_RATIO_RIGHT_THRESH:
                return "right"
            else:
                return "center"
        except Exception:
            return "center"
