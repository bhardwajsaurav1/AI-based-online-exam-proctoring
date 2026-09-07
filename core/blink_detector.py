"""
Blink & Liveness Detection Module.
Author: Sole Contributor / Creator
Calculates Eye Aspect Ratio (EAR) to detect eye blinks and verify liveness.
"""

from math import hypot
import config

class BlinkDetector:
    def __init__(self, ear_threshold=config.BLINK_EAR_THRESHOLD):
        self.ear_threshold = ear_threshold
        self.LEFT_EYE_POINTS = [36, 37, 38, 39, 40, 41]
        self.RIGHT_EYE_POINTS = [42, 43, 44, 45, 46, 47]
        self.total_blinks = 0
        self.is_currently_blinking = False

    def _euclidean_dist(self, p1, p2):
        return hypot(p1[0] - p2[0], p1[1] - p2[1])

    def compute_ear(self, eye_points, landmarks):
        """
        Computes the Eye Aspect Ratio (EAR):
        EAR = (||p2 - p6|| + ||p3 - p5||) / (2 * ||p1 - p4||)
        """
        pts = [(landmarks.part(p).x, landmarks.part(p).y) for p in eye_points]
        
        # Vertical distances
        v1 = self._euclidean_dist(pts[1], pts[5])
        v2 = self._euclidean_dist(pts[2], pts[4])
        
        # Horizontal distance
        h = self._euclidean_dist(pts[0], pts[3])
        
        if h == 0:
            return 0.3
        
        ear = (v1 + v2) / (2.0 * h)
        return ear

    def evaluate_blink(self, landmarks):
        """
        Evaluates whether candidate is blinking in current frame.
        Returns: ('Blink' or 'No Blink', EAR_value)
        """
        if landmarks is None:
            return "No Blink", 0.3

        left_ear = self.compute_ear(self.LEFT_EYE_POINTS, landmarks)
        right_ear = self.compute_ear(self.RIGHT_EYE_POINTS, landmarks)
        avg_ear = (left_ear + right_ear) / 2.0

        if avg_ear < self.ear_threshold:
            if not self.is_currently_blinking:
                self.total_blinks += 1
                self.is_currently_blinking = True
            return "Blink", avg_ear
        else:
            self.is_currently_blinking = False
            return "No Blink", avg_ear
