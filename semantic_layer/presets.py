"""
Face Presets — predefined combinations of facial feature values.

Each preset maps feature names to values in the [-1.0, 1.0] range.
"""


FACE_PRESETS = {
    # --- FACE SHAPE PRESETS ---
    "angular_face": {
        "description": "Strong angular features with defined jawline and cheekbones",
        "features": {
            "jaw_width": -0.3,
            "jaw_angle": 0.7,
            "cheekbone_prominence": 0.6,
            "cheekbone_height": 0.3,
            "chin_prominence": 0.4,
            "face_width": -0.2,
            "cheek_fullness": -0.3,
        }
    },
    "round_face": {
        "description": "Soft round face with full cheeks",
        "features": {
            "jaw_width": 0.4,
            "jaw_angle": -0.5,
            "cheekbone_prominence": -0.2,
            "face_width": 0.5,
            "chin_prominence": -0.3,
            "chin_width": 0.3,
            "cheek_fullness": 0.6,
        }
    },
    "oval_face": {
        "description": "Balanced oval face shape",
        "features": {
            "jaw_width": -0.1,
            "face_width": 0.1,
            "face_length": 0.2,
            "chin_prominence": 0.1,
            "cheekbone_prominence": 0.2,
        }
    },
    "heart_face": {
        "description": "Wider forehead tapering to a narrow chin",
        "features": {
            "forehead_width": 0.4,
            "cheekbone_prominence": 0.3,
            "jaw_width": -0.5,
            "chin_width": -0.4,
            "chin_prominence": 0.2,
        }
    },
    "square_face": {
        "description": "Strong square jaw with equal width forehead",
        "features": {
            "jaw_width": 0.5,
            "jaw_angle": 0.8,
            "forehead_width": 0.3,
            "chin_width": 0.4,
            "face_width": 0.3,
            "cheekbone_prominence": 0.1,
        }
    },

    # --- NOSE PRESETS ---
    "button_nose": {
        "description": "Small upturned nose",
        "features": {
            "nose_width": -0.3,
            "nose_length": -0.5,
            "nose_tip_height": 0.4,
            "nose_bridge_width": -0.2,
        }
    },
    "roman_nose": {
        "description": "Prominent nose bridge with a slight bump",
        "features": {
            "nose_bridge_height": 0.7,
            "nose_length": 0.3,
            "nose_tip_height": -0.2,
            "nose_width": -0.1,
        }
    },
    "wide_nose": {
        "description": "Broad nose with wider nostrils",
        "features": {
            "nose_width": 0.6,
            "nose_bridge_width": 0.4,
            "nose_bridge_height": -0.2,
        }
    },
    "narrow_nose": {
        "description": "Thin narrow nose",
        "features": {
            "nose_width": -0.5,
            "nose_bridge_width": -0.4,
            "nose_bridge_height": 0.2,
        }
    },

    # --- EYE PRESETS ---
    "large_eyes": {
        "description": "Large expressive eyes",
        "features": {
            "eye_size": 0.6,
            "eye_spacing": 0.1,
            "brow_height": 0.3,
        }
    },
    "almond_eyes": {
        "description": "Almond-shaped eyes with slight upward tilt",
        "features": {
            "eye_size": -0.1,
            "eye_tilt": 0.4,
            "eye_spacing": 0.0,
        }
    },
    "deep_set_eyes": {
        "description": "Deep-set eyes under prominent brow",
        "features": {
            "eye_depth": 0.5,
            "brow_height": -0.3,
            "eye_size": -0.2,
        }
    },

    # --- BROW PRESETS ---
    "strong_brow": {
        "description": "Low prominent brow ridge",
        "features": {
            "brow_height": -0.3,
            "brow_arch": -0.4,
            "brow_spacing": -0.2,
        }
    },
    "arched_brows": {
        "description": "High arched eyebrows",
        "features": {
            "brow_height": 0.3,
            "brow_arch": 0.7,
        }
    },

    # --- LIP PRESETS ---
    "full_lips": {
        "description": "Full plump lips",
        "features": {
            "lip_fullness_upper": 0.6,
            "lip_fullness_lower": 0.7,
            "lip_width": 0.2,
        }
    },
    "thin_lips": {
        "description": "Thin narrow lips",
        "features": {
            "lip_fullness_upper": -0.5,
            "lip_fullness_lower": -0.4,
            "lip_width": -0.2,
        }
    },
    "wide_mouth": {
        "description": "Wide mouth with natural lips",
        "features": {
            "lip_width": 0.6,
            "lip_fullness_upper": 0.1,
            "lip_fullness_lower": 0.1,
        }
    },

    # --- COMPOSITE CHARACTER PRESETS ---
    "heroic": {
        "description": "Classic heroic face — strong jaw, defined cheekbones, prominent brow",
        "features": {
            "jaw_width": 0.3,
            "jaw_angle": 0.6,
            "chin_prominence": 0.5,
            "cheekbone_prominence": 0.5,
            "cheekbone_height": 0.3,
            "brow_height": -0.2,
            "nose_bridge_height": 0.3,
            "face_width": 0.1,
        }
    },
    "delicate": {
        "description": "Delicate refined features — narrow face, small nose, high cheekbones",
        "features": {
            "face_width": -0.3,
            "jaw_width": -0.4,
            "nose_width": -0.3,
            "nose_length": -0.2,
            "cheekbone_height": 0.4,
            "cheekbone_prominence": 0.3,
            "lip_fullness_upper": 0.2,
            "lip_fullness_lower": 0.2,
            "brow_arch": 0.3,
            "eye_size": 0.3,
        }
    },
    "rugged": {
        "description": "Weathered rugged face — wide jaw, deep-set eyes, prominent nose",
        "features": {
            "jaw_width": 0.5,
            "jaw_angle": 0.4,
            "chin_prominence": 0.3,
            "nose_bridge_height": 0.5,
            "nose_width": 0.2,
            "brow_height": -0.4,
            "eye_depth": 0.4,
            "cheek_fullness": -0.3,
            "forehead_slope": 0.3,
        }
    },
    "youthful": {
        "description": "Youthful soft features — round face, large eyes, small nose",
        "features": {
            "face_width": 0.2,
            "eye_size": 0.5,
            "nose_length": -0.3,
            "nose_width": -0.2,
            "nose_tip_height": 0.2,
            "cheek_fullness": 0.4,
            "lip_fullness_upper": 0.3,
            "lip_fullness_lower": 0.3,
            "jaw_angle": -0.3,
            "brow_height": 0.2,
            "forehead_height": 0.2,
        }
    },
}


def get_preset(name):
    """Get a preset by name.

    Returns:
        dict with 'description' and 'features', or None if not found.
    """
    return FACE_PRESETS.get(name)


def list_presets():
    """List all available presets with descriptions.

    Returns:
        dict mapping preset_name -> description
    """
    return {name: data["description"] for name, data in FACE_PRESETS.items()}


def blend_presets(preset_a_name, preset_b_name, factor=0.5):
    """Interpolate between two presets.

    Args:
        preset_a_name: Name of the first preset.
        preset_b_name: Name of the second preset.
        factor: Blend factor (0.0 = all A, 1.0 = all B).

    Returns:
        dict of blended feature values, or None if preset not found.
    """
    a = FACE_PRESETS.get(preset_a_name)
    b = FACE_PRESETS.get(preset_b_name)

    if not a or not b:
        return None

    all_keys = set(a["features"].keys()) | set(b["features"].keys())
    blended = {}

    for key in all_keys:
        val_a = a["features"].get(key, 0.0)
        val_b = b["features"].get(key, 0.0)
        blended[key] = val_a * (1.0 - factor) + val_b * factor

    return blended
