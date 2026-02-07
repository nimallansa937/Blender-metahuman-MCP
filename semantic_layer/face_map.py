"""
Semantic Facial Feature Map

Maps high-level facial feature names (e.g., "nose_width", "jaw_width")
to specific bone operations in Blender. Supports multiple rig types
(MetaHuman, Rigify, Mixamo, generic).

Each feature defines:
  - description: Human-readable description
  - operations: List of bone transforms to apply
  - range: Valid input range (normalized)
  - category: Grouping for UI/listing

Each operation defines:
  - bone: Generic bone name (resolved via BONE_ALIAS_MAPS)
  - transform: "location" | "scale" | "rotation"
  - axis: "X" | "Y" | "Z"
  - multiplier: How much to move per unit of input value (in Blender units / meters)
"""


# === RIG-SPECIFIC BONE NAME ALIASES ===

BONE_ALIAS_MAPS = {
    "metahuman": {
        # Nose — verified against Bernice_FaceMesh rig
        "nose_bridge": "FACIAL_C_NoseBridge",
        "nose_tip": "FACIAL_C_NoseTip",
        "nose_L": "FACIAL_L_Nostril",
        "nose_R": "FACIAL_R_Nostril",
        "nostril_L": "FACIAL_L_NostrilThickness1",
        "nostril_R": "FACIAL_R_NostrilThickness1",
        # Jaw
        "jaw": "FACIAL_C_Jaw",
        "jaw_L": "FACIAL_L_Jawline",
        "jaw_R": "FACIAL_R_Jawline",
        "chin": "FACIAL_C_Chin",
        "chin_L": "FACIAL_L_ChinSide",
        "chin_R": "FACIAL_R_ChinSide",
        # Eyes
        "eye_L": "FACIAL_L_Eye",
        "eye_R": "FACIAL_R_Eye",
        "eyelid_upper_L": "FACIAL_L_EyelidUpperA",
        "eyelid_upper_R": "FACIAL_R_EyelidUpperA",
        "eyelid_lower_L": "FACIAL_L_EyelidLowerA",
        "eyelid_lower_R": "FACIAL_R_EyelidLowerA",
        # Brows
        "brow_inner_L": "FACIAL_L_ForeheadIn",
        "brow_inner_R": "FACIAL_R_ForeheadIn",
        "brow_mid_L": "FACIAL_L_ForeheadMid",
        "brow_mid_R": "FACIAL_R_ForeheadMid",
        "brow_outer_L": "FACIAL_L_ForeheadOut",
        "brow_outer_R": "FACIAL_R_ForeheadOut",
        # Lips
        "lip_upper_mid": "FACIAL_C_LipUpper",
        "lip_lower_mid": "FACIAL_C_LipLower",
        "lip_corner_L": "FACIAL_L_LipCorner",
        "lip_corner_R": "FACIAL_R_LipCorner",
        "lip_upper_L": "FACIAL_L_LipUpperOuter",
        "lip_upper_R": "FACIAL_R_LipUpperOuter",
        "lip_lower_L": "FACIAL_L_LipLowerOuter",
        "lip_lower_R": "FACIAL_R_LipLowerOuter",
        # Cheeks
        "cheek_L": "FACIAL_L_CheekOuter",
        "cheek_R": "FACIAL_R_CheekOuter",
        "cheek_upper_L": "FACIAL_L_CheekInner",
        "cheek_upper_R": "FACIAL_R_CheekInner",
        # Forehead
        "forehead_mid": "FACIAL_C_Forehead",
        "forehead_L": "FACIAL_L_ForeheadIn",
        "forehead_R": "FACIAL_R_ForeheadIn",
        # Ears
        "ear_L": "FACIAL_L_Ear",
        "ear_R": "FACIAL_R_Ear",
    },

    "rigify": {
        "nose_bridge": "nose_master",
        "nose_tip": "nose.004",
        "nose_L": "nose.L.001",
        "nose_R": "nose.R.001",
        "jaw": "jaw_master",
        "jaw_L": "jaw.L",
        "jaw_R": "jaw.R",
        "chin": "chin",
        "eye_L": "eye.L",
        "eye_R": "eye.R",
        "brow_inner_L": "brow.B.L.001",
        "brow_inner_R": "brow.B.R.001",
        "brow_mid_L": "brow.B.L.002",
        "brow_mid_R": "brow.B.R.002",
        "brow_outer_L": "brow.B.L.003",
        "brow_outer_R": "brow.B.R.003",
        "lip_upper_mid": "lip.T",
        "lip_lower_mid": "lip.B",
        "lip_corner_L": "lips.L",
        "lip_corner_R": "lips.R",
        "cheek_L": "cheek.B.L",
        "cheek_R": "cheek.B.R",
        "ear_L": "ear.L",
        "ear_R": "ear.R",
    },

    "generic": {
        # Fallback: use the generic names directly
        # The system will try these as-is against the armature
        "nose_bridge": "nose_bridge",
        "nose_tip": "nose_tip",
        "nose_L": "nose.L",
        "nose_R": "nose.R",
        "jaw": "jaw",
        "jaw_L": "jaw.L",
        "jaw_R": "jaw.R",
        "chin": "chin",
        "eye_L": "eye.L",
        "eye_R": "eye.R",
        "brow_inner_L": "brow_inner.L",
        "brow_inner_R": "brow_inner.R",
        "brow_mid_L": "brow_mid.L",
        "brow_mid_R": "brow_mid.R",
        "brow_outer_L": "brow_outer.L",
        "brow_outer_R": "brow_outer.R",
        "lip_upper_mid": "lip_upper",
        "lip_lower_mid": "lip_lower",
        "lip_corner_L": "lip_corner.L",
        "lip_corner_R": "lip_corner.R",
        "cheek_L": "cheek.L",
        "cheek_R": "cheek.R",
        "ear_L": "ear.L",
        "ear_R": "ear.R",
    },
}


# === FACIAL FEATURE MAP ===

FACIAL_FEATURE_MAP = {
    # --- NOSE ---
    "nose_width": {
        "description": "Width of the nose — wider or narrower nostrils and bridge",
        "category": "nose",
        "range": [-1.0, 1.0],
        "operations": [
            {"bone": "nose_L", "transform": "location", "axis": "X", "multiplier": 0.005},
            {"bone": "nose_R", "transform": "location", "axis": "X", "multiplier": -0.005},
            {"bone": "nostril_L", "transform": "location", "axis": "X", "multiplier": 0.004},
            {"bone": "nostril_R", "transform": "location", "axis": "X", "multiplier": -0.004},
        ],
    },
    "nose_length": {
        "description": "Length of the nose — longer or shorter from bridge to tip",
        "category": "nose",
        "range": [-1.0, 1.0],
        "operations": [
            {"bone": "nose_tip", "transform": "location", "axis": "Y", "multiplier": -0.006},
        ],
    },
    "nose_tip_height": {
        "description": "Height of the nose tip — upturned or downturned",
        "category": "nose",
        "range": [-1.0, 1.0],
        "operations": [
            {"bone": "nose_tip", "transform": "location", "axis": "Z", "multiplier": 0.004},
        ],
    },
    "nose_bridge_width": {
        "description": "Width of the nose bridge between the eyes",
        "category": "nose",
        "range": [-1.0, 1.0],
        "operations": [
            {"bone": "nose_bridge", "transform": "scale", "axis": "X", "multiplier": 0.3},
        ],
    },
    "nose_bridge_height": {
        "description": "Prominence of the nose bridge — flatter or more pronounced",
        "category": "nose",
        "range": [-1.0, 1.0],
        "operations": [
            {"bone": "nose_bridge", "transform": "location", "axis": "Y", "multiplier": -0.004},
        ],
    },

    # --- JAW ---
    "jaw_width": {
        "description": "Width of the jawline — wider or narrower jaw",
        "category": "jaw",
        "range": [-1.0, 1.0],
        "operations": [
            {"bone": "jaw_L", "transform": "location", "axis": "X", "multiplier": 0.008},
            {"bone": "jaw_R", "transform": "location", "axis": "X", "multiplier": -0.008},
        ],
    },
    "jaw_height": {
        "description": "Vertical position of the jaw — longer or shorter face",
        "category": "jaw",
        "range": [-1.0, 1.0],
        "operations": [
            {"bone": "jaw", "transform": "location", "axis": "Z", "multiplier": -0.006},
        ],
    },
    "jaw_angle": {
        "description": "Angle of the jawline — more angular or rounded",
        "category": "jaw",
        "range": [-1.0, 1.0],
        "operations": [
            {"bone": "jaw_L", "transform": "location", "axis": "Z", "multiplier": -0.004},
            {"bone": "jaw_R", "transform": "location", "axis": "Z", "multiplier": -0.004},
            {"bone": "jaw_L", "transform": "location", "axis": "X", "multiplier": -0.003},
            {"bone": "jaw_R", "transform": "location", "axis": "X", "multiplier": 0.003},
        ],
    },
    "chin_prominence": {
        "description": "How much the chin projects forward",
        "category": "jaw",
        "range": [-1.0, 1.0],
        "operations": [
            {"bone": "chin", "transform": "location", "axis": "Y", "multiplier": -0.005},
        ],
    },
    "chin_width": {
        "description": "Width of the chin",
        "category": "jaw",
        "range": [-1.0, 1.0],
        "operations": [
            {"bone": "chin_L", "transform": "location", "axis": "X", "multiplier": 0.004},
            {"bone": "chin_R", "transform": "location", "axis": "X", "multiplier": -0.004},
        ],
    },
    "chin_height": {
        "description": "Vertical length of the chin",
        "category": "jaw",
        "range": [-1.0, 1.0],
        "operations": [
            {"bone": "chin", "transform": "location", "axis": "Z", "multiplier": -0.005},
        ],
    },

    # --- EYES ---
    "eye_size": {
        "description": "Overall eye size — larger or smaller eyes",
        "category": "eyes",
        "range": [-1.0, 1.0],
        "operations": [
            {"bone": "eyelid_upper_L", "transform": "location", "axis": "Z", "multiplier": 0.003},
            {"bone": "eyelid_upper_R", "transform": "location", "axis": "Z", "multiplier": 0.003},
            {"bone": "eyelid_lower_L", "transform": "location", "axis": "Z", "multiplier": -0.002},
            {"bone": "eyelid_lower_R", "transform": "location", "axis": "Z", "multiplier": -0.002},
        ],
    },
    "eye_spacing": {
        "description": "Distance between the eyes — closer or further apart",
        "category": "eyes",
        "range": [-1.0, 1.0],
        "operations": [
            {"bone": "eye_L", "transform": "location", "axis": "X", "multiplier": -0.005},
            {"bone": "eye_R", "transform": "location", "axis": "X", "multiplier": 0.005},
        ],
    },
    "eye_tilt": {
        "description": "Tilt of the eyes — upward or downward outer corners",
        "category": "eyes",
        "range": [-1.0, 1.0],
        "operations": [
            {"bone": "eyelid_upper_L", "transform": "rotation", "axis": "Y", "multiplier": 5.0},
            {"bone": "eyelid_upper_R", "transform": "rotation", "axis": "Y", "multiplier": -5.0},
        ],
    },
    "eye_depth": {
        "description": "How deep-set or protruding the eyes are",
        "category": "eyes",
        "range": [-1.0, 1.0],
        "operations": [
            {"bone": "eye_L", "transform": "location", "axis": "Y", "multiplier": 0.004},
            {"bone": "eye_R", "transform": "location", "axis": "Y", "multiplier": 0.004},
        ],
    },

    # --- BROWS ---
    "brow_height": {
        "description": "Height of the eyebrows — raised or lowered",
        "category": "brows",
        "range": [-1.0, 1.0],
        "operations": [
            {"bone": "brow_inner_L", "transform": "location", "axis": "Z", "multiplier": 0.004},
            {"bone": "brow_inner_R", "transform": "location", "axis": "Z", "multiplier": 0.004},
            {"bone": "brow_mid_L", "transform": "location", "axis": "Z", "multiplier": 0.004},
            {"bone": "brow_mid_R", "transform": "location", "axis": "Z", "multiplier": 0.004},
            {"bone": "brow_outer_L", "transform": "location", "axis": "Z", "multiplier": 0.004},
            {"bone": "brow_outer_R", "transform": "location", "axis": "Z", "multiplier": 0.004},
        ],
    },
    "brow_arch": {
        "description": "Arch shape of the brows — more arched or flatter",
        "category": "brows",
        "range": [-1.0, 1.0],
        "operations": [
            {"bone": "brow_inner_L", "transform": "location", "axis": "Z", "multiplier": -0.002},
            {"bone": "brow_inner_R", "transform": "location", "axis": "Z", "multiplier": -0.002},
            {"bone": "brow_mid_L", "transform": "location", "axis": "Z", "multiplier": 0.004},
            {"bone": "brow_mid_R", "transform": "location", "axis": "Z", "multiplier": 0.004},
            {"bone": "brow_outer_L", "transform": "location", "axis": "Z", "multiplier": -0.001},
            {"bone": "brow_outer_R", "transform": "location", "axis": "Z", "multiplier": -0.001},
        ],
    },
    "brow_spacing": {
        "description": "Distance between the inner brow points",
        "category": "brows",
        "range": [-1.0, 1.0],
        "operations": [
            {"bone": "brow_inner_L", "transform": "location", "axis": "X", "multiplier": -0.003},
            {"bone": "brow_inner_R", "transform": "location", "axis": "X", "multiplier": 0.003},
        ],
    },

    # --- LIPS / MOUTH ---
    "lip_fullness_upper": {
        "description": "Fullness of the upper lip",
        "category": "lips",
        "range": [-1.0, 1.0],
        "operations": [
            {"bone": "lip_upper_mid", "transform": "location", "axis": "Y", "multiplier": -0.003},
            {"bone": "lip_upper_mid", "transform": "location", "axis": "Z", "multiplier": 0.001},
            {"bone": "lip_upper_L", "transform": "location", "axis": "Y", "multiplier": -0.002},
            {"bone": "lip_upper_R", "transform": "location", "axis": "Y", "multiplier": -0.002},
        ],
    },
    "lip_fullness_lower": {
        "description": "Fullness of the lower lip",
        "category": "lips",
        "range": [-1.0, 1.0],
        "operations": [
            {"bone": "lip_lower_mid", "transform": "location", "axis": "Y", "multiplier": -0.003},
            {"bone": "lip_lower_mid", "transform": "location", "axis": "Z", "multiplier": -0.001},
            {"bone": "lip_lower_L", "transform": "location", "axis": "Y", "multiplier": -0.002},
            {"bone": "lip_lower_R", "transform": "location", "axis": "Y", "multiplier": -0.002},
        ],
    },
    "lip_width": {
        "description": "Width of the mouth — wider or narrower",
        "category": "lips",
        "range": [-1.0, 1.0],
        "operations": [
            {"bone": "lip_corner_L", "transform": "location", "axis": "X", "multiplier": 0.005},
            {"bone": "lip_corner_R", "transform": "location", "axis": "X", "multiplier": -0.005},
        ],
    },
    "lip_height": {
        "description": "Vertical position of the mouth on the face",
        "category": "lips",
        "range": [-1.0, 1.0],
        "operations": [
            {"bone": "lip_upper_mid", "transform": "location", "axis": "Z", "multiplier": 0.003},
            {"bone": "lip_lower_mid", "transform": "location", "axis": "Z", "multiplier": 0.003},
            {"bone": "lip_corner_L", "transform": "location", "axis": "Z", "multiplier": 0.003},
            {"bone": "lip_corner_R", "transform": "location", "axis": "Z", "multiplier": 0.003},
        ],
    },

    # --- CHEEKS ---
    "cheekbone_height": {
        "description": "Height of the cheekbones — higher or lower",
        "category": "cheeks",
        "range": [-1.0, 1.0],
        "operations": [
            {"bone": "cheek_upper_L", "transform": "location", "axis": "Z", "multiplier": 0.005},
            {"bone": "cheek_upper_R", "transform": "location", "axis": "Z", "multiplier": 0.005},
        ],
    },
    "cheekbone_prominence": {
        "description": "How pronounced the cheekbones are — more or less defined",
        "category": "cheeks",
        "range": [-1.0, 1.0],
        "operations": [
            {"bone": "cheek_L", "transform": "location", "axis": "X", "multiplier": 0.004},
            {"bone": "cheek_R", "transform": "location", "axis": "X", "multiplier": -0.004},
            {"bone": "cheek_L", "transform": "location", "axis": "Y", "multiplier": -0.003},
            {"bone": "cheek_R", "transform": "location", "axis": "Y", "multiplier": -0.003},
        ],
    },
    "cheek_fullness": {
        "description": "Fullness of the cheeks — rounder or more hollow",
        "category": "cheeks",
        "range": [-1.0, 1.0],
        "operations": [
            {"bone": "cheek_L", "transform": "location", "axis": "Y", "multiplier": -0.005},
            {"bone": "cheek_R", "transform": "location", "axis": "Y", "multiplier": -0.005},
            {"bone": "cheek_L", "transform": "location", "axis": "X", "multiplier": 0.003},
            {"bone": "cheek_R", "transform": "location", "axis": "X", "multiplier": -0.003},
        ],
    },

    # --- FOREHEAD ---
    "forehead_height": {
        "description": "Height of the forehead — taller or shorter",
        "category": "forehead",
        "range": [-1.0, 1.0],
        "operations": [
            {"bone": "forehead_mid", "transform": "location", "axis": "Z", "multiplier": 0.006},
            {"bone": "forehead_L", "transform": "location", "axis": "Z", "multiplier": 0.005},
            {"bone": "forehead_R", "transform": "location", "axis": "Z", "multiplier": 0.005},
        ],
    },
    "forehead_width": {
        "description": "Width of the forehead",
        "category": "forehead",
        "range": [-1.0, 1.0],
        "operations": [
            {"bone": "forehead_L", "transform": "location", "axis": "X", "multiplier": 0.005},
            {"bone": "forehead_R", "transform": "location", "axis": "X", "multiplier": -0.005},
        ],
    },
    "forehead_slope": {
        "description": "Slope of the forehead — more vertical or receding",
        "category": "forehead",
        "range": [-1.0, 1.0],
        "operations": [
            {"bone": "forehead_mid", "transform": "location", "axis": "Y", "multiplier": -0.005},
        ],
    },

    # --- EARS ---
    "ear_size": {
        "description": "Overall ear size",
        "category": "ears",
        "range": [-1.0, 1.0],
        "operations": [
            {"bone": "ear_L", "transform": "scale", "axis": "X", "multiplier": 0.3},
            {"bone": "ear_L", "transform": "scale", "axis": "Z", "multiplier": 0.3},
            {"bone": "ear_R", "transform": "scale", "axis": "X", "multiplier": 0.3},
            {"bone": "ear_R", "transform": "scale", "axis": "Z", "multiplier": 0.3},
        ],
    },
    "ear_angle": {
        "description": "How much the ears stick out",
        "category": "ears",
        "range": [-1.0, 1.0],
        "operations": [
            {"bone": "ear_L", "transform": "rotation", "axis": "Y", "multiplier": 10.0},
            {"bone": "ear_R", "transform": "rotation", "axis": "Y", "multiplier": -10.0},
        ],
    },

    # --- OVERALL FACE SHAPE ---
    "face_width": {
        "description": "Overall face width",
        "category": "face",
        "range": [-1.0, 1.0],
        "operations": [
            {"bone": "jaw_L", "transform": "location", "axis": "X", "multiplier": 0.006},
            {"bone": "jaw_R", "transform": "location", "axis": "X", "multiplier": -0.006},
            {"bone": "cheek_L", "transform": "location", "axis": "X", "multiplier": 0.005},
            {"bone": "cheek_R", "transform": "location", "axis": "X", "multiplier": -0.005},
            {"bone": "forehead_L", "transform": "location", "axis": "X", "multiplier": 0.004},
            {"bone": "forehead_R", "transform": "location", "axis": "X", "multiplier": -0.004},
        ],
    },
    "face_length": {
        "description": "Overall face length — longer or shorter",
        "category": "face",
        "range": [-1.0, 1.0],
        "operations": [
            {"bone": "chin", "transform": "location", "axis": "Z", "multiplier": -0.006},
            {"bone": "jaw", "transform": "location", "axis": "Z", "multiplier": -0.004},
            {"bone": "forehead_mid", "transform": "location", "axis": "Z", "multiplier": 0.004},
        ],
    },
}


def detect_rig_type(bone_names):
    """Auto-detect the rig type based on bone names present in the armature.

    Args:
        bone_names: List/set of bone name strings from the armature.

    Returns:
        str: "metahuman", "rigify", or "generic"
    """
    bone_set = set(bone_names)

    # MetaHuman detection: look for FACIAL_ prefix bones
    metahuman_markers = {"FACIAL_C_Jaw", "FACIAL_C_NoseTip", "FACIAL_L_Eye", "FACIAL_C_ForeheadMid"}
    if len(metahuman_markers.intersection(bone_set)) >= 2:
        return "metahuman"

    # Rigify detection: look for typical Rigify face bone names
    rigify_markers = {"jaw_master", "nose_master", "brow.B.L.001", "lip.T"}
    if len(rigify_markers.intersection(bone_set)) >= 2:
        return "rigify"

    return "generic"


def resolve_bone_name(generic_name, rig_type="generic"):
    """Resolve a generic bone name to a rig-specific name.

    Args:
        generic_name: The generic bone name from FACIAL_FEATURE_MAP operations.
        rig_type: One of "metahuman", "rigify", "generic".

    Returns:
        str: The rig-specific bone name, or the generic name as fallback.
    """
    alias_map = BONE_ALIAS_MAPS.get(rig_type, BONE_ALIAS_MAPS["generic"])
    return alias_map.get(generic_name, generic_name)


def get_operations_for_feature(feature_name, rig_type="generic"):
    """Get bone operations for a facial feature, resolved for the given rig type.

    Args:
        feature_name: Key from FACIAL_FEATURE_MAP.
        rig_type: "metahuman", "rigify", or "generic".

    Returns:
        list of dicts with resolved bone names, or empty list if feature unknown.
    """
    feature = FACIAL_FEATURE_MAP.get(feature_name)
    if not feature:
        return []

    resolved_ops = []
    for op in feature["operations"]:
        resolved = dict(op)
        resolved["bone"] = resolve_bone_name(op["bone"], rig_type)
        resolved_ops.append(resolved)

    return resolved_ops


def get_all_features():
    """Return a summary of all available facial features.

    Returns:
        dict mapping feature_name -> {description, category, range}
    """
    return {
        name: {
            "description": data["description"],
            "category": data["category"],
            "range": data["range"],
        }
        for name, data in FACIAL_FEATURE_MAP.items()
    }


def get_features_by_category():
    """Return features grouped by category.

    Returns:
        dict mapping category -> [feature_names]
    """
    categories = {}
    for name, data in FACIAL_FEATURE_MAP.items():
        cat = data["category"]
        if cat not in categories:
            categories[cat] = []
        categories[cat].append(name)
    return categories
