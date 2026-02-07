"""
Face Reconstruction Module

Reconstructs 3D facial features from a 2D photo using:
  1. MediaPipe FaceMesh — 478 landmark detection
  2. Proportion analysis — landmark distances → facial ratios
  3. Feature mapping — ratios → 32 semantic feature values [-1, 1]

Usage:
    from face_reconstruction import detect_face_landmarks, analyze_proportions, map_proportions_to_features

    result = detect_face_landmarks("photo.jpg")
    proportions = analyze_proportions(result["landmarks"])
    features = map_proportions_to_features(proportions)
    # features = {"nose_width": 0.35, "jaw_width": -0.2, ...}
"""

from .landmark_detector import detect_face_landmarks
from .proportion_analyzer import analyze_proportions
from .feature_mapper import map_proportions_to_features, get_feature_confidence
