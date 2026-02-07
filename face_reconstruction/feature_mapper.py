"""
Feature Mapper

Maps facial proportion ratios (from proportion_analyzer) to the
32 semantic facial feature values [-1.0, 1.0] used by the semantic layer.

The mapping uses z-score normalization:
  feature_value = clamp((measured - mean) / (std * sensitivity), -1, 1)

Where mean and std come from reference_proportions.py (average face baseline).
"""

import logging

from .reference_proportions import (
    REFERENCE_PROPORTIONS,
    DEFAULT_SENSITIVITY,
    MEASUREMENT_CONFIDENCE,
)

logger = logging.getLogger("face_reconstruction.feature_mapper")


# === PROPORTION-TO-FEATURE MAPPING TABLE ===
# Maps semantic feature names (used by face_map.py) to proportion ratio names
# (computed by proportion_analyzer.py)

PROPORTION_TO_FEATURE = {
    # Nose
    "nose_width":          "nose_width_ratio",
    "nose_length":         "nose_length_ratio",
    "nose_tip_height":     "nose_tip_height_ratio",
    "nose_bridge_width":   "nose_bridge_width_ratio",
    "nose_bridge_height":  "nose_bridge_height_ratio",

    # Jaw
    "jaw_width":           "jaw_width_ratio",
    "jaw_height":          "jaw_height_ratio",
    "jaw_angle":           "jaw_angle_ratio",
    "chin_prominence":     "chin_prominence_ratio",
    "chin_width":          "chin_width_ratio",
    "chin_height":         "chin_height_ratio",

    # Eyes
    "eye_size":            "eye_height_ratio",
    "eye_spacing":         "eye_spacing_ratio",
    "eye_tilt":            "eye_tilt_ratio",
    "eye_depth":           "eye_depth_ratio",

    # Brows
    "brow_height":         "brow_height_ratio",
    "brow_arch":           "brow_arch_ratio",
    "brow_spacing":        "brow_spacing_ratio",

    # Lips
    "lip_fullness_upper":  "lip_upper_ratio",
    "lip_fullness_lower":  "lip_lower_ratio",
    "lip_width":           "lip_width_ratio",
    "lip_height":          "lip_height_ratio",

    # Cheeks
    "cheekbone_height":    "cheekbone_height_ratio",
    "cheekbone_prominence": "cheekbone_prominence_ratio",
    "cheek_fullness":      "cheek_fullness_ratio",

    # Forehead
    "forehead_height":     "forehead_height_ratio",
    "forehead_width":      "forehead_width_ratio",
    "forehead_slope":      "forehead_slope_ratio",

    # Face shape
    "face_width":          "face_width_ratio",
    "face_length":         "face_length_ratio",

    # Ears (default neutral)
    "ear_size":            "ear_size_ratio",
    "ear_angle":           "ear_angle_ratio",
}


def map_proportions_to_features(
    proportions: dict,
    sensitivity: float = None,
) -> dict:
    """Convert proportion ratios to 32 semantic feature values [-1.0, 1.0].

    Args:
        proportions: Dict from analyze_proportions() with ratio measurements.
        sensitivity: How aggressively to map deviations from average.
                     Lower = more exaggerated (small differences produce large values).
                     Higher = more subtle.
                     Default: 1.5 (from reference_proportions.py).

    Returns:
        Dict mapping feature names to float values in [-1.0, 1.0].
        Example: {"nose_width": 0.35, "jaw_width": -0.2, ...}
    """
    if sensitivity is None:
        sensitivity = DEFAULT_SENSITIVITY

    if not proportions:
        logger.warning("Empty proportions dict — returning all zeros")
        return {feature: 0.0 for feature in PROPORTION_TO_FEATURE}

    features = {}
    mapped_count = 0
    defaulted_count = 0

    for feature_name, ratio_key in PROPORTION_TO_FEATURE.items():
        measured = proportions.get(ratio_key)

        if measured is None:
            features[feature_name] = 0.0
            defaulted_count += 1
            continue

        ref = REFERENCE_PROPORTIONS.get(ratio_key)
        if ref is None:
            features[feature_name] = 0.0
            defaulted_count += 1
            continue

        mean, std = ref
        features[feature_name] = _ratio_to_feature_value(measured, mean, std, sensitivity)
        mapped_count += 1

    logger.info(
        f"Mapped {mapped_count} features, {defaulted_count} defaulted to 0.0 "
        f"(sensitivity={sensitivity})"
    )

    return features


def get_feature_confidence(proportions: dict = None) -> dict:
    """Get confidence level for each feature mapping.

    Returns:
        Dict mapping feature names to confidence strings:
          "high" — direct landmark measurement, reliable
          "medium" — derived from indirect measurements
          "low" — depth-based (z-axis) or defaulted
    """
    result = {}
    for feature_name, ratio_key in PROPORTION_TO_FEATURE.items():
        conf = MEASUREMENT_CONFIDENCE.get(ratio_key, "low")

        # If the proportion wasn't measured at all, it's low confidence
        if proportions and proportions.get(ratio_key) is None:
            conf = "low"

        result[feature_name] = conf

    return result


def get_top_distinctive_features(features: dict, count: int = 5) -> list:
    """Get the most distinctive features (highest absolute values).

    Args:
        features: Dict from map_proportions_to_features().
        count: Number of top features to return.

    Returns:
        List of (feature_name, value) tuples sorted by |value| descending.
    """
    sorted_features = sorted(
        features.items(),
        key=lambda x: abs(x[1]),
        reverse=True
    )
    return sorted_features[:count]


def format_features_by_category(features: dict, confidence: dict = None) -> str:
    """Format feature values grouped by category for readable output.

    Args:
        features: Dict from map_proportions_to_features().
        confidence: Optional dict from get_feature_confidence().

    Returns:
        Formatted string with features grouped by category.
    """
    categories = {
        "Nose": ["nose_width", "nose_length", "nose_tip_height", "nose_bridge_width", "nose_bridge_height"],
        "Jaw": ["jaw_width", "jaw_height", "jaw_angle", "chin_prominence", "chin_width", "chin_height"],
        "Eyes": ["eye_size", "eye_spacing", "eye_tilt", "eye_depth"],
        "Brows": ["brow_height", "brow_arch", "brow_spacing"],
        "Lips": ["lip_fullness_upper", "lip_fullness_lower", "lip_width", "lip_height"],
        "Cheeks": ["cheekbone_height", "cheekbone_prominence", "cheek_fullness"],
        "Forehead": ["forehead_height", "forehead_width", "forehead_slope"],
        "Ears": ["ear_size", "ear_angle"],
        "Face Shape": ["face_width", "face_length"],
    }

    lines = []
    for category, feature_names in categories.items():
        lines.append(f"\n=== {category} ===")
        for name in feature_names:
            val = features.get(name, 0.0)
            conf_str = ""
            if confidence:
                conf = confidence.get(name, "")
                conf_str = f" [{conf}]"
            direction = "+" if val > 0 else ""
            lines.append(f"  {name}: {direction}{val:.3f}{conf_str}")

    return "\n".join(lines)


def _ratio_to_feature_value(measured, mean, std, sensitivity):
    """Convert a measured ratio to a [-1, 1] feature value.

    Uses z-score normalization:
      z = (measured - mean) / std
      feature = clamp(z / sensitivity, -1, 1)
    """
    if std <= 0:
        return 0.0

    z_score = (measured - mean) / std
    value = z_score / sensitivity

    # Clamp to [-1.0, 1.0]
    return max(-1.0, min(1.0, value))
