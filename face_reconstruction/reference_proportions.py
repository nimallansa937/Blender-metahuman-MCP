"""
Reference Facial Proportions

Defines the average face proportions as measured by MediaPipe FaceMesh,
used as the baseline (feature value = 0.0). Deviations from these
averages are mapped to feature values in [-1.0, 1.0].

Each entry: (mean_ratio, standard_deviation)
  - mean_ratio: average measurement / IPD for a neutral face
  - standard_deviation: typical variation across faces

Proportions are normalized to Inter-Pupil Distance (IPD) for
robustness across photo scales and mild head poses.

Based on anthropometric data (Farkas 1994) calibrated for MediaPipe output.
These values should be empirically tuned for best results.
"""


# === REFERENCE PROPORTIONS ===
# Format: ratio_name -> (mean, std_deviation)

REFERENCE_PROPORTIONS = {
    # --- Nose ---
    "nose_width_ratio":           (0.56, 0.07),    # nostril width / IPD
    "nose_length_ratio":          (0.70, 0.09),    # bridge-to-tip / IPD
    "nose_tip_height_ratio":      (0.00, 0.018),   # z-offset of tip vs bridge (signed)
    "nose_bridge_width_ratio":    (0.28, 0.04),    # bridge width / IPD
    "nose_bridge_height_ratio":   (0.020, 0.012),  # bridge depth protrusion (z)

    # --- Jaw ---
    "jaw_width_ratio":            (2.00, 0.18),    # jaw width / IPD
    "jaw_height_ratio":           (0.62, 0.09),    # jaw vertical extent / IPD
    "jaw_angle_ratio":            (0.00, 0.08),    # angular deviation from average
    "chin_prominence_ratio":      (0.00, 0.013),   # chin forward projection (z)
    "chin_width_ratio":           (0.52, 0.07),    # chin width / IPD
    "chin_height_ratio":          (0.23, 0.04),    # chin vertical length / IPD

    # --- Eyes ---
    "eye_height_ratio":           (0.16, 0.025),   # avg eye opening / IPD
    "eye_spacing_ratio":          (0.60, 0.06),    # inner-corner distance / IPD
    "eye_tilt_ratio":             (0.00, 0.025),   # outer-inner height diff (signed)
    "eye_depth_ratio":            (0.00, 0.012),   # eye z relative to nose bridge

    # --- Brows ---
    "brow_height_ratio":          (0.26, 0.045),   # brow-to-eye dist / IPD
    "brow_arch_ratio":            (0.035, 0.018),  # brow peak relative to ends
    "brow_spacing_ratio":         (0.52, 0.06),    # inner brow distance / IPD

    # --- Lips ---
    "lip_upper_ratio":            (0.11, 0.025),   # upper lip thickness / IPD
    "lip_lower_ratio":            (0.14, 0.025),   # lower lip thickness / IPD
    "lip_width_ratio":            (0.76, 0.09),    # mouth width / IPD
    "lip_height_ratio":           (0.32, 0.04),    # mouth vertical position (relative)

    # --- Cheeks ---
    "cheekbone_height_ratio":     (0.00, 0.025),   # cheekbone Y position (relative)
    "cheekbone_prominence_ratio": (0.88, 0.07),    # cheekbone lateral extent / IPD
    "cheek_fullness_ratio":       (0.00, 0.015),   # mid-cheek depth (z-based)

    # --- Forehead ---
    "forehead_height_ratio":      (0.82, 0.11),    # forehead-to-brow / IPD
    "forehead_width_ratio":       (1.75, 0.14),    # forehead width / IPD
    "forehead_slope_ratio":       (0.00, 0.012),   # depth change from top to glabella

    # --- Face shape ---
    "face_width_ratio":           (2.00, 0.18),    # overall face width / IPD
    "face_length_ratio":          (2.55, 0.22),    # top-to-chin / IPD

    # --- Ears (rarely visible — default neutral) ---
    "ear_size_ratio":             (0.00, 0.10),    # placeholder
    "ear_angle_ratio":            (0.00, 0.10),    # placeholder
}


# How many standard deviations = feature value ±1.0
# Lower = more sensitive (small differences → large feature values)
# Higher = less sensitive (needs bigger differences)
DEFAULT_SENSITIVITY = 1.5


# === CONFIDENCE LEVELS ===
# Indicates how reliable each measurement is from a 2D photo

MEASUREMENT_CONFIDENCE = {
    # High: Direct 2D distances, well-defined landmarks
    "nose_width_ratio":           "high",
    "nose_length_ratio":          "high",
    "jaw_width_ratio":            "high",
    "eye_height_ratio":           "high",
    "eye_spacing_ratio":          "high",
    "lip_width_ratio":            "high",
    "lip_upper_ratio":            "high",
    "lip_lower_ratio":            "high",
    "face_length_ratio":          "high",
    "face_width_ratio":           "high",
    "chin_width_ratio":           "high",
    "brow_spacing_ratio":         "high",
    "brow_height_ratio":          "high",

    # Medium: Derived from indirect or less stable landmarks
    "nose_bridge_width_ratio":    "medium",
    "jaw_height_ratio":           "medium",
    "jaw_angle_ratio":            "medium",
    "chin_height_ratio":          "medium",
    "eye_tilt_ratio":             "medium",
    "brow_arch_ratio":            "medium",
    "lip_height_ratio":           "medium",
    "cheekbone_height_ratio":     "medium",
    "cheekbone_prominence_ratio": "medium",
    "forehead_height_ratio":      "medium",
    "forehead_width_ratio":       "medium",

    # Low: Depth-based (z-axis) or occluded features
    "nose_tip_height_ratio":      "low",
    "nose_bridge_height_ratio":   "low",
    "chin_prominence_ratio":      "low",
    "eye_depth_ratio":            "low",
    "cheek_fullness_ratio":       "low",
    "forehead_slope_ratio":       "low",
    "ear_size_ratio":             "low",
    "ear_angle_ratio":            "low",
}
