"""
Input validation and normalization for facial feature editing.
"""

import difflib
from .face_map import FACIAL_FEATURE_MAP


def clamp_value(value, min_val=-1.0, max_val=1.0):
    """Clamp a value to a valid range.

    Returns:
        tuple: (clamped_value, was_clamped: bool)
    """
    clamped = max(min_val, min(max_val, value))
    return clamped, clamped != value


def validate_feature_name(name):
    """Validate a feature name against the feature map.

    Returns:
        dict: {valid: bool, name: str, suggestion: str|None, error: str|None}
    """
    # Normalize: lowercase, replace spaces/hyphens with underscores
    normalized = name.lower().strip().replace(" ", "_").replace("-", "_")

    if normalized in FACIAL_FEATURE_MAP:
        return {"valid": True, "name": normalized, "suggestion": None, "error": None}

    # Fuzzy match
    all_features = list(FACIAL_FEATURE_MAP.keys())
    matches = difflib.get_close_matches(normalized, all_features, n=3, cutoff=0.4)

    if matches:
        return {
            "valid": False,
            "name": normalized,
            "suggestion": matches[0],
            "all_suggestions": matches,
            "error": f"Unknown feature '{normalized}'. Did you mean '{matches[0]}'?"
        }

    return {
        "valid": False,
        "name": normalized,
        "suggestion": None,
        "error": f"Unknown feature '{normalized}'. Use list_editable_features to see available options."
    }


# Direction word mappings
DIRECTION_MAP = {
    # Positive (increase)
    "wider": 1.0,
    "bigger": 1.0,
    "larger": 1.0,
    "more": 1.0,
    "higher": 1.0,
    "taller": 1.0,
    "fuller": 1.0,
    "thicker": 1.0,
    "longer": 1.0,
    "stronger": 1.0,
    "deeper": 1.0,
    "prominent": 1.0,
    "pronounced": 1.0,
    "raised": 1.0,
    "increased": 1.0,
    "up": 1.0,
    "out": 1.0,
    "forward": 1.0,
    "rounder": 1.0,
    "plumper": 1.0,

    # Negative (decrease)
    "narrower": -1.0,
    "smaller": -1.0,
    "less": -1.0,
    "lower": -1.0,
    "shorter": -1.0,
    "thinner": -1.0,
    "flatter": -1.0,
    "shallower": -1.0,
    "reduced": -1.0,
    "receding": -1.0,
    "decreased": -1.0,
    "down": -1.0,
    "in": -1.0,
    "back": -1.0,
    "slimmer": -1.0,
}


def normalize_direction(direction_str):
    """Convert a direction word to a sign multiplier.

    Args:
        direction_str: e.g., "wider", "narrower", "bigger"

    Returns:
        float: 1.0 for increase, -1.0 for decrease, 0.0 if unknown
    """
    normalized = direction_str.lower().strip()
    return DIRECTION_MAP.get(normalized, 0.0)


def parse_natural_description(description):
    """Parse a natural language description into feature edits.

    Handles descriptions like:
      "wider nose, stronger jawline, bigger eyes"
      "make the nose narrower and the lips fuller"

    Returns:
        list of dicts: [{feature: str, value: float, direction: str}, ...]
    """
    # Clean up
    text = description.lower().strip()

    # Remove filler words
    for word in ["make", "the", "a", "an", "with", "and", "please", "give", "me", "set", "adjust"]:
        text = text.replace(f" {word} ", " ")

    # Split on commas, "and", semicolons
    import re
    parts = re.split(r'[,;]|\band\b', text)

    edits = []
    feature_keywords = _build_feature_keyword_map()

    for part in parts:
        part = part.strip()
        if not part:
            continue

        # Find direction word
        direction = 0.0
        direction_word = ""
        for word, sign in DIRECTION_MAP.items():
            if word in part:
                direction = sign
                direction_word = word
                break

        # Find feature
        matched_feature = None
        best_score = 0

        for keyword, feature_name in feature_keywords.items():
            if keyword in part:
                score = len(keyword)
                if score > best_score:
                    best_score = score
                    matched_feature = feature_name

        if matched_feature:
            # Default magnitude: moderate change
            value = direction * 0.5

            # Look for intensity words
            if any(w in part for w in ["very", "much", "extremely", "significantly"]):
                value = direction * 0.8
            elif any(w in part for w in ["slightly", "a bit", "a little", "subtly"]):
                value = direction * 0.25

            edits.append({
                "feature": matched_feature,
                "value": value,
                "direction": direction_word,
                "raw_text": part.strip(),
            })

    return edits


def _build_feature_keyword_map():
    """Build a reverse map from keywords to feature names."""
    keywords = {
        # Nose
        "nose width": "nose_width",
        "nose": "nose_width",  # Default nose = width
        "nostril": "nose_width",
        "nose length": "nose_length",
        "nose tip": "nose_tip_height",
        "nose bridge": "nose_bridge_height",
        # Jaw
        "jawline": "jaw_width",
        "jaw width": "jaw_width",
        "jaw": "jaw_width",
        "jaw angle": "jaw_angle",
        "chin": "chin_prominence",
        "chin width": "chin_width",
        # Eyes
        "eye size": "eye_size",
        "eyes": "eye_size",
        "eye spacing": "eye_spacing",
        "eye tilt": "eye_tilt",
        "eye depth": "eye_depth",
        # Brows
        "brow height": "brow_height",
        "brow": "brow_height",
        "eyebrow": "brow_height",
        "brow arch": "brow_arch",
        # Lips
        "upper lip": "lip_fullness_upper",
        "lower lip": "lip_fullness_lower",
        "lip": "lip_fullness_upper",
        "lips": "lip_fullness_upper",
        "mouth width": "lip_width",
        "mouth": "lip_width",
        # Cheeks
        "cheekbone": "cheekbone_prominence",
        "cheek": "cheek_fullness",
        # Forehead
        "forehead height": "forehead_height",
        "forehead width": "forehead_width",
        "forehead": "forehead_height",
        # Ears
        "ear size": "ear_size",
        "ear": "ear_size",
        # Face
        "face width": "face_width",
        "face length": "face_length",
        "face": "face_width",
    }
    return keywords
