"""
Facial Proportion Analyzer

Computes facial proportion ratios from MediaPipe's 478 face landmarks.
All measurements are normalized to the Inter-Pupil Distance (IPD) for
robustness across photo scales and mild head pose variations.

Returns a dict of named proportion ratios that can be mapped to the
semantic layer's 32 facial features.
"""

import math
import logging

logger = logging.getLogger("face_reconstruction.proportion_analyzer")


# === MEDIAPIPE LANDMARK INDICES ===
# Reference: https://github.com/google/mediapipe/blob/master/mediapipe/modules/face_geometry/data/canonical_face_model_uv_visualization.png

LM = {
    # Face boundary
    "forehead_top": 10,
    "chin_bottom": 152,

    # Nose
    "nose_bridge_top": 6,
    "nose_tip": 4,
    "nostril_left": 129,
    "nostril_right": 358,
    "nose_bridge_left": 31,
    "nose_bridge_right": 261,

    # Eyes — outer and inner corners
    "left_eye_outer": 33,
    "left_eye_inner": 133,
    "right_eye_inner": 362,
    "right_eye_outer": 263,

    # Eyes — upper and lower lids
    "left_eye_upper": 159,
    "left_eye_lower": 145,
    "right_eye_upper": 386,
    "right_eye_lower": 374,

    # Brows
    "left_brow_inner": 107,
    "right_brow_inner": 336,
    "left_brow_mid": 105,
    "right_brow_mid": 334,
    "left_brow_outer": 70,
    "right_brow_outer": 300,

    # Lips
    "lip_top_center": 13,
    "lip_bottom_center": 14,
    "lip_left_corner": 61,
    "lip_right_corner": 291,
    "upper_lip_vermillion": 0,  # Upper lip boundary

    # Jaw
    "jaw_left": 234,
    "jaw_right": 454,
    "jaw_angle_left": 172,
    "jaw_angle_right": 397,

    # Chin
    "chin_center": 199,
    "chin_left": 202,
    "chin_right": 422,

    # Cheeks
    "cheek_left": 123,
    "cheek_right": 352,
    "cheek_upper_left": 116,
    "cheek_upper_right": 345,

    # Forehead
    "glabella": 9,  # Between the brows

    # Mid-face reference points
    "nose_root": 168,  # Between the eyes, top of nose
}


def analyze_proportions(landmarks: list) -> dict:
    """Compute facial proportion ratios from 478 MediaPipe landmarks.

    All distances are normalized to IPD (inter-pupil distance) for
    scale-invariant measurements.

    Args:
        landmarks: List of (x, y, z) tuples from detect_face_landmarks().

    Returns:
        Dict of named proportion ratios (all floats).
    """
    if not landmarks or len(landmarks) < 468:
        logger.error(f"Insufficient landmarks: {len(landmarks) if landmarks else 0}")
        return {}

    # Convenience accessor
    def lm(idx):
        return landmarks[idx]

    # Compute IPD (inter-pupil distance) as the normalization reference
    ipd = _compute_ipd(landmarks)
    if ipd < 0.001:
        logger.error("IPD is too small — face detection may be unreliable")
        return {}

    logger.info(f"IPD = {ipd:.4f} (normalized units)")

    props = {}

    # === NOSE ===
    props["nose_width_ratio"] = _dist2d(lm(LM["nostril_left"]), lm(LM["nostril_right"])) / ipd
    props["nose_length_ratio"] = _dist2d(lm(LM["nose_bridge_top"]), lm(LM["nose_tip"])) / ipd
    props["nose_tip_height_ratio"] = lm(LM["nose_tip"])[2] - lm(LM["nose_bridge_top"])[2]  # z difference
    props["nose_bridge_width_ratio"] = _dist2d(lm(LM["nose_bridge_left"]), lm(LM["nose_bridge_right"])) / ipd
    # Bridge height: how much the bridge protrudes (z relative to eye plane)
    eye_mid_z = (lm(LM["left_eye_inner"])[2] + lm(LM["right_eye_inner"])[2]) / 2
    props["nose_bridge_height_ratio"] = eye_mid_z - lm(LM["nose_bridge_top"])[2]

    # === JAW ===
    props["jaw_width_ratio"] = _dist2d(lm(LM["jaw_left"]), lm(LM["jaw_right"])) / ipd
    # Jaw height: vertical distance from jaw angle midpoint to chin
    jaw_mid_y = (lm(LM["jaw_left"])[1] + lm(LM["jaw_right"])[1]) / 2
    props["jaw_height_ratio"] = (lm(LM["chin_bottom"])[1] - jaw_mid_y) / ipd
    # Jaw angle: compare jaw angle position to jaw corners and chin
    props["jaw_angle_ratio"] = _compute_jaw_angle(landmarks, ipd)
    # Chin
    props["chin_prominence_ratio"] = lm(LM["chin_center"])[2] - lm(LM["nose_tip"])[2]  # z forward projection
    props["chin_width_ratio"] = _dist2d(lm(LM["chin_left"]), lm(LM["chin_right"])) / ipd
    props["chin_height_ratio"] = _dist2d(lm(LM["chin_center"]), lm(LM["chin_bottom"])) / ipd

    # === EYES ===
    left_eye_h = _dist2d(lm(LM["left_eye_upper"]), lm(LM["left_eye_lower"]))
    right_eye_h = _dist2d(lm(LM["right_eye_upper"]), lm(LM["right_eye_lower"]))
    props["eye_height_ratio"] = ((left_eye_h + right_eye_h) / 2) / ipd
    props["eye_spacing_ratio"] = _dist2d(lm(LM["left_eye_inner"]), lm(LM["right_eye_inner"])) / ipd
    # Eye tilt: height difference between outer and inner corners
    left_tilt = lm(LM["left_eye_outer"])[1] - lm(LM["left_eye_inner"])[1]
    right_tilt = lm(LM["right_eye_inner"])[1] - lm(LM["right_eye_outer"])[1]
    props["eye_tilt_ratio"] = (left_tilt + right_tilt) / 2  # positive = outer corners higher (upward tilt)
    # Eye depth: how deep-set the eyes are (z relative to nose bridge)
    eye_z = (lm(LM["left_eye_inner"])[2] + lm(LM["right_eye_inner"])[2]) / 2
    props["eye_depth_ratio"] = eye_z - lm(LM["nose_root"])[2]

    # === BROWS ===
    # Brow height: distance from brow to eye
    left_brow_h = _dist2d(lm(LM["left_brow_inner"]), lm(LM["left_eye_inner"]))
    right_brow_h = _dist2d(lm(LM["right_brow_inner"]), lm(LM["right_eye_inner"]))
    props["brow_height_ratio"] = ((left_brow_h + right_brow_h) / 2) / ipd
    # Brow arch: how much the brow mid peaks above the inner-outer line
    props["brow_arch_ratio"] = _compute_brow_arch(landmarks, ipd)
    # Brow spacing: distance between inner brow points
    props["brow_spacing_ratio"] = _dist2d(lm(LM["left_brow_inner"]), lm(LM["right_brow_inner"])) / ipd

    # === LIPS ===
    # Upper lip thickness: vermillion to top of lip
    props["lip_upper_ratio"] = _dist2d(lm(LM["upper_lip_vermillion"]), lm(LM["lip_top_center"])) / ipd
    # Lower lip thickness: vermillion to bottom of lip
    props["lip_lower_ratio"] = _dist2d(lm(LM["upper_lip_vermillion"]), lm(LM["lip_bottom_center"])) / ipd
    # Lip width
    props["lip_width_ratio"] = _dist2d(lm(LM["lip_left_corner"]), lm(LM["lip_right_corner"])) / ipd
    # Lip vertical position (relative position between nose and chin)
    lip_center_y = (lm(LM["lip_top_center"])[1] + lm(LM["lip_bottom_center"])[1]) / 2
    face_height = _dist2d(lm(LM["forehead_top"]), lm(LM["chin_bottom"]))
    if face_height > 0.001:
        props["lip_height_ratio"] = (lip_center_y - lm(LM["nose_tip"])[1]) / ipd
    else:
        props["lip_height_ratio"] = 0.32

    # === CHEEKS ===
    # Cheekbone height: relative to eye level
    eye_center_y = (lm(LM["left_eye_inner"])[1] + lm(LM["right_eye_inner"])[1]) / 2
    cheek_y = (lm(LM["cheek_left"])[1] + lm(LM["cheek_right"])[1]) / 2
    props["cheekbone_height_ratio"] = (cheek_y - eye_center_y) / ipd  # positive = lower
    # Cheekbone prominence: lateral extent
    props["cheekbone_prominence_ratio"] = _dist2d(lm(LM["cheek_left"]), lm(LM["cheek_right"])) / ipd
    # Cheek fullness: z-depth of mid-cheek area
    cheek_z = (lm(LM["cheek_upper_left"])[2] + lm(LM["cheek_upper_right"])[2]) / 2
    props["cheek_fullness_ratio"] = cheek_z - eye_mid_z

    # === FOREHEAD ===
    # Forehead height: from top of head to brow line
    brow_mid_y = (lm(LM["left_brow_inner"])[1] + lm(LM["right_brow_inner"])[1]) / 2
    props["forehead_height_ratio"] = abs(lm(LM["forehead_top"])[1] - brow_mid_y) / ipd
    # Forehead width: approximated from outer brow points
    props["forehead_width_ratio"] = _dist2d(lm(LM["left_brow_outer"]), lm(LM["right_brow_outer"])) / ipd
    # Forehead slope: z-depth change from top to glabella
    props["forehead_slope_ratio"] = lm(LM["forehead_top"])[2] - lm(LM["glabella"])[2]

    # === FACE SHAPE ===
    props["face_width_ratio"] = _dist2d(lm(LM["jaw_left"]), lm(LM["jaw_right"])) / ipd
    props["face_length_ratio"] = _dist2d(lm(LM["forehead_top"]), lm(LM["chin_bottom"])) / ipd

    # === EARS (defaulted — not reliably detected by MediaPipe) ===
    props["ear_size_ratio"] = 0.0
    props["ear_angle_ratio"] = 0.0

    logger.info(f"Computed {len(props)} proportion ratios")
    return props


# === HELPER FUNCTIONS ===

def _dist2d(p1, p2):
    """Euclidean distance using x, y components only."""
    return math.sqrt((p1[0] - p2[0]) ** 2 + (p1[1] - p2[1]) ** 2)


def _dist3d(p1, p2):
    """Euclidean distance using x, y, z components."""
    return math.sqrt((p1[0] - p2[0]) ** 2 + (p1[1] - p2[1]) ** 2 + (p1[2] - p2[2]) ** 2)


def _midpoint(p1, p2):
    """Midpoint of two landmark points."""
    return ((p1[0] + p2[0]) / 2, (p1[1] + p2[1]) / 2, (p1[2] + p2[2]) / 2)


def _compute_ipd(landmarks):
    """Compute inter-pupil distance from eye center landmarks.

    Uses the midpoints of outer and inner eye corners for each eye.
    """
    # Left eye center: midpoint of outer (33) and inner (133)
    left_center = _midpoint(landmarks[33], landmarks[133])
    # Right eye center: midpoint of outer (263) and inner (362)
    right_center = _midpoint(landmarks[263], landmarks[362])

    return _dist2d(left_center, right_center)


def _compute_jaw_angle(landmarks, ipd):
    """Compute jaw angle metric.

    Measures the angular sharpness of the jawline by comparing
    the jaw angle position relative to the jaw corner and chin.
    More angular jaws have sharper transitions.
    """
    # Left side: angle at jaw_angle_left between jaw_left and chin_bottom
    jaw_angle_l = landmarks[LM["jaw_angle_left"]]
    jaw_l = landmarks[LM["jaw_left"]]
    chin = landmarks[LM["chin_bottom"]]

    # Right side
    jaw_angle_r = landmarks[LM["jaw_angle_right"]]
    jaw_r = landmarks[LM["jaw_right"]]

    # Compute how much the jaw angle point deviates inward from the jaw-chin line
    # A sharper jawline = more deviation
    left_dev = _point_line_distance_2d(jaw_angle_l, jaw_l, chin)
    right_dev = _point_line_distance_2d(jaw_angle_r, jaw_r, chin)

    avg_dev = (left_dev + right_dev) / 2
    return avg_dev / ipd


def _point_line_distance_2d(point, line_start, line_end):
    """Compute perpendicular distance from a point to a line in 2D (x, y)."""
    x0, y0 = point[0], point[1]
    x1, y1 = line_start[0], line_start[1]
    x2, y2 = line_end[0], line_end[1]

    num = abs((y2 - y1) * x0 - (x2 - x1) * y0 + x2 * y1 - y2 * x1)
    den = math.sqrt((y2 - y1) ** 2 + (x2 - x1) ** 2)

    if den < 1e-10:
        return 0.0
    return num / den


def _compute_brow_arch(landmarks, ipd):
    """Compute brow arch by measuring how much the mid-brow peaks above the inner-outer line."""
    # Left brow arch
    left_inner = landmarks[LM["left_brow_inner"]]
    left_mid = landmarks[LM["left_brow_mid"]]
    left_outer = landmarks[LM["left_brow_outer"]]
    left_baseline_y = (left_inner[1] + left_outer[1]) / 2
    left_arch = left_baseline_y - left_mid[1]  # positive = mid is higher (lower y)

    # Right brow arch
    right_inner = landmarks[LM["right_brow_inner"]]
    right_mid = landmarks[LM["right_brow_mid"]]
    right_outer = landmarks[LM["right_brow_outer"]]
    right_baseline_y = (right_inner[1] + right_outer[1]) / 2
    right_arch = right_baseline_y - right_mid[1]

    return ((left_arch + right_arch) / 2) / ipd
