"""
Mouth Movement & Speech Detection Module.
Author: Sole Contributor / Creator
Calculates vertical lip distance to detect talking, whispering, or open mouth.
"""

from math import hypot
import config

class MouthTracker:
    def __init__(self, threshold_ratio=config.MOUTH_AR_THRESHOLD):
        self.threshold_ratio = threshold_ratio

    def _euclidean_dist(self, p1, p2):
        return hypot(p1[0] - p2[0], p1[1] - p2[1])

    def detect_mouth_state(self, landmarks):
        """
        Measures vertical vs horizontal lip distance (Mouth Aspect Ratio - MAR).
        Returns: 'Mouth Open' (speaking) or 'Mouth Close' (normal)
        """
        if landmarks is None:
            return "Mouth Close", 0.0

        try:
            # Outer Lip Top (51) & Bottom (57)
            top_outer = (landmarks.part(51).x, landmarks.part(51).y)
            bottom_outer = (landmarks.part(57).x, landmarks.part(57).y)

            # Inner Lip Top (62) & Bottom (66)
            top_inner = (landmarks.part(62).x, landmarks.part(62).y)
            bottom_inner = (landmarks.part(66).x, landmarks.part(66).y)

            # Left Lip Corner (48) & Right Lip Corner (54)
            left_corner = (landmarks.part(48).x, landmarks.part(48).y)
            right_corner = (landmarks.part(54).x, landmarks.part(54).y)

            v_dist_outer = self._euclidean_dist(top_outer, bottom_outer)
            v_dist_inner = self._euclidean_dist(top_inner, bottom_inner)
            h_dist = self._euclidean_dist(left_corner, right_corner)

            if h_dist == 0:
                return "Mouth Close", 0.0

            mar = (v_dist_outer + v_dist_inner) / (2.0 * h_dist)

            if mar > self.threshold_ratio:
                return "Mouth Open", round(mar, 2)
            else:
                return "Mouth Close", round(mar, 2)
        except Exception:
            return "Mouth Close", 0.0
