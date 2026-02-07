"""
Unit tests for the semantic facial mapping layer.

These tests run WITHOUT Blender — they only test the mapping logic,
validation, presets, and natural language parsing.
"""

import sys
import os
import unittest

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from semantic_layer.face_map import (
    FACIAL_FEATURE_MAP, BONE_ALIAS_MAPS, detect_rig_type,
    resolve_bone_name, get_operations_for_feature,
    get_all_features, get_features_by_category
)
from semantic_layer.presets import (
    FACE_PRESETS, get_preset, list_presets, blend_presets
)
from semantic_layer.validators import (
    clamp_value, validate_feature_name, normalize_direction,
    parse_natural_description
)


class TestFaceMap(unittest.TestCase):

    def test_all_features_have_required_fields(self):
        """Every feature must have description, category, range, and operations."""
        for name, data in FACIAL_FEATURE_MAP.items():
            self.assertIn("description", data, f"{name} missing 'description'")
            self.assertIn("category", data, f"{name} missing 'category'")
            self.assertIn("range", data, f"{name} missing 'range'")
            self.assertIn("operations", data, f"{name} missing 'operations'")
            self.assertIsInstance(data["operations"], list, f"{name} operations not a list")
            self.assertGreater(len(data["operations"]), 0, f"{name} has no operations")

    def test_all_operations_have_required_fields(self):
        """Every operation must have bone, transform, axis, and multiplier."""
        for name, data in FACIAL_FEATURE_MAP.items():
            for i, op in enumerate(data["operations"]):
                self.assertIn("bone", op, f"{name} op[{i}] missing 'bone'")
                self.assertIn("transform", op, f"{name} op[{i}] missing 'transform'")
                self.assertIn("axis", op, f"{name} op[{i}] missing 'axis'")
                self.assertIn("multiplier", op, f"{name} op[{i}] missing 'multiplier'")
                self.assertIn(op["transform"], ["location", "scale", "rotation"],
                              f"{name} op[{i}] invalid transform: {op['transform']}")
                self.assertIn(op["axis"], ["X", "Y", "Z"],
                              f"{name} op[{i}] invalid axis: {op['axis']}")

    def test_all_bones_have_aliases(self):
        """Every generic bone used in features should exist in at least one alias map."""
        all_generic_bones = set()
        for data in FACIAL_FEATURE_MAP.values():
            for op in data["operations"]:
                all_generic_bones.add(op["bone"])

        for bone in all_generic_bones:
            found = False
            for rig_type, alias_map in BONE_ALIAS_MAPS.items():
                if bone in alias_map:
                    found = True
                    break
            self.assertTrue(found, f"Bone '{bone}' not found in any alias map")

    def test_detect_rig_type_metahuman(self):
        bones = ["FACIAL_C_Jaw", "FACIAL_C_NoseTip", "FACIAL_L_Eye", "FACIAL_C_ForeheadMid"]
        self.assertEqual(detect_rig_type(bones), "metahuman")

    def test_detect_rig_type_rigify(self):
        bones = ["jaw_master", "nose_master", "brow.B.L.001", "lip.T"]
        self.assertEqual(detect_rig_type(bones), "rigify")

    def test_detect_rig_type_generic(self):
        bones = ["Bone", "Bone.001", "Armature"]
        self.assertEqual(detect_rig_type(bones), "generic")

    def test_resolve_bone_name(self):
        self.assertEqual(resolve_bone_name("jaw", "metahuman"), "FACIAL_C_Jaw")
        self.assertEqual(resolve_bone_name("jaw", "rigify"), "jaw_master")
        self.assertEqual(resolve_bone_name("jaw", "generic"), "jaw")

    def test_get_operations_for_feature(self):
        ops = get_operations_for_feature("nose_width", "metahuman")
        self.assertGreater(len(ops), 0)
        # Verify bones are resolved to MetaHuman names
        for op in ops:
            self.assertTrue(
                op["bone"].startswith("FACIAL_") or op["bone"] in BONE_ALIAS_MAPS["metahuman"].values(),
                f"Bone '{op['bone']}' not resolved for MetaHuman"
            )

    def test_get_operations_unknown_feature(self):
        ops = get_operations_for_feature("nonexistent_feature", "generic")
        self.assertEqual(ops, [])

    def test_get_all_features(self):
        features = get_all_features()
        self.assertGreater(len(features), 20)
        for name, info in features.items():
            self.assertIn("description", info)
            self.assertIn("category", info)

    def test_get_features_by_category(self):
        cats = get_features_by_category()
        self.assertIn("nose", cats)
        self.assertIn("jaw", cats)
        self.assertIn("eyes", cats)


class TestPresets(unittest.TestCase):

    def test_all_presets_have_required_fields(self):
        for name, data in FACE_PRESETS.items():
            self.assertIn("description", data, f"Preset '{name}' missing 'description'")
            self.assertIn("features", data, f"Preset '{name}' missing 'features'")
            self.assertIsInstance(data["features"], dict)

    def test_all_preset_features_are_valid(self):
        """All features referenced in presets must exist in FACIAL_FEATURE_MAP."""
        for preset_name, preset_data in FACE_PRESETS.items():
            for feature_name in preset_data["features"]:
                self.assertIn(feature_name, FACIAL_FEATURE_MAP,
                              f"Preset '{preset_name}' uses unknown feature '{feature_name}'")

    def test_preset_values_in_range(self):
        """All preset values should be within [-1.0, 1.0]."""
        for preset_name, preset_data in FACE_PRESETS.items():
            for feature_name, value in preset_data["features"].items():
                self.assertGreaterEqual(value, -1.0,
                    f"Preset '{preset_name}' feature '{feature_name}' value {value} < -1.0")
                self.assertLessEqual(value, 1.0,
                    f"Preset '{preset_name}' feature '{feature_name}' value {value} > 1.0")

    def test_get_preset(self):
        result = get_preset("angular_face")
        self.assertIsNotNone(result)
        self.assertIn("features", result)

    def test_get_preset_missing(self):
        self.assertIsNone(get_preset("nonexistent"))

    def test_list_presets(self):
        presets = list_presets()
        self.assertGreater(len(presets), 10)

    def test_blend_presets(self):
        blended = blend_presets("angular_face", "round_face", 0.5)
        self.assertIsNotNone(blended)
        # Check a feature present in both
        self.assertIn("jaw_width", blended)
        # Blended value should be between the two preset values
        angular_val = FACE_PRESETS["angular_face"]["features"]["jaw_width"]
        round_val = FACE_PRESETS["round_face"]["features"]["jaw_width"]
        expected = (angular_val + round_val) / 2
        self.assertAlmostEqual(blended["jaw_width"], expected, places=3)

    def test_blend_presets_missing(self):
        self.assertIsNone(blend_presets("nonexistent", "round_face"))


class TestValidators(unittest.TestCase):

    def test_clamp_value_in_range(self):
        val, clamped = clamp_value(0.5)
        self.assertEqual(val, 0.5)
        self.assertFalse(clamped)

    def test_clamp_value_over(self):
        val, clamped = clamp_value(2.0)
        self.assertEqual(val, 1.0)
        self.assertTrue(clamped)

    def test_clamp_value_under(self):
        val, clamped = clamp_value(-3.0)
        self.assertEqual(val, -1.0)
        self.assertTrue(clamped)

    def test_validate_feature_name_valid(self):
        result = validate_feature_name("nose_width")
        self.assertTrue(result["valid"])

    def test_validate_feature_name_with_spaces(self):
        result = validate_feature_name("nose width")
        self.assertTrue(result["valid"])
        self.assertEqual(result["name"], "nose_width")

    def test_validate_feature_name_invalid_with_suggestion(self):
        result = validate_feature_name("nose_widht")  # typo
        self.assertFalse(result["valid"])
        self.assertEqual(result["suggestion"], "nose_width")

    def test_normalize_direction(self):
        self.assertEqual(normalize_direction("wider"), 1.0)
        self.assertEqual(normalize_direction("narrower"), -1.0)
        self.assertEqual(normalize_direction("bigger"), 1.0)
        self.assertEqual(normalize_direction("smaller"), -1.0)
        self.assertEqual(normalize_direction("unknown_word"), 0.0)

    def test_parse_natural_description_single(self):
        edits = parse_natural_description("wider nose")
        self.assertGreater(len(edits), 0)
        self.assertEqual(edits[0]["feature"], "nose_width")
        self.assertGreater(edits[0]["value"], 0)

    def test_parse_natural_description_multiple(self):
        edits = parse_natural_description("wider nose, stronger jawline, bigger eyes")
        self.assertEqual(len(edits), 3)
        features = {e["feature"] for e in edits}
        self.assertIn("nose_width", features)
        self.assertIn("jaw_width", features)
        self.assertIn("eye_size", features)

    def test_parse_natural_description_with_intensity(self):
        edits = parse_natural_description("slightly wider nose")
        self.assertGreater(len(edits), 0)
        # "slightly" should result in lower value
        self.assertLess(abs(edits[0]["value"]), 0.4)

    def test_parse_natural_description_very(self):
        edits = parse_natural_description("very wider nose")
        self.assertGreater(len(edits), 0)
        self.assertGreater(abs(edits[0]["value"]), 0.6)

    def test_parse_natural_description_empty(self):
        edits = parse_natural_description("hello world")
        self.assertEqual(len(edits), 0)


if __name__ == "__main__":
    unittest.main()
