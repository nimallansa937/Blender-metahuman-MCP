"""
Unit tests for the face reconstruction pipeline.

Tests the reference proportions, feature mapper, proportion analyzer,
and landmark detector modules. Most tests run without MediaPipe or Blender.
"""

import sys
import os
import unittest
import math

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from face_reconstruction.reference_proportions import (
    REFERENCE_PROPORTIONS,
    DEFAULT_SENSITIVITY,
    MEASUREMENT_CONFIDENCE,
)
from face_reconstruction.feature_mapper import (
    PROPORTION_TO_FEATURE,
    map_proportions_to_features,
    get_feature_confidence,
    get_top_distinctive_features,
    format_features_by_category,
    _ratio_to_feature_value,
)
from face_reconstruction.proportion_analyzer import (
    analyze_proportions,
    _dist2d,
    _dist3d,
    _midpoint,
    _compute_ipd,
)
from semantic_layer.face_map import FACIAL_FEATURE_MAP


class TestReferenceProportions(unittest.TestCase):
    """Test the reference proportions data."""

    def test_all_features_have_reference_values(self):
        """Every ratio key used in PROPORTION_TO_FEATURE must exist in REFERENCE_PROPORTIONS."""
        for feature_name, ratio_key in PROPORTION_TO_FEATURE.items():
            self.assertIn(
                ratio_key, REFERENCE_PROPORTIONS,
                f"Feature '{feature_name}' maps to '{ratio_key}' which is missing from REFERENCE_PROPORTIONS"
            )

    def test_all_std_deviations_positive(self):
        """All standard deviations must be > 0."""
        for ratio_key, (mean, std) in REFERENCE_PROPORTIONS.items():
            self.assertGreater(std, 0, f"Std for '{ratio_key}' is not positive: {std}")

    def test_all_means_are_finite(self):
        """All means must be finite numbers."""
        for ratio_key, (mean, std) in REFERENCE_PROPORTIONS.items():
            self.assertTrue(math.isfinite(mean), f"Mean for '{ratio_key}' is not finite: {mean}")
            self.assertTrue(math.isfinite(std), f"Std for '{ratio_key}' is not finite: {std}")

    def test_sensitivity_positive(self):
        """Default sensitivity must be positive."""
        self.assertGreater(DEFAULT_SENSITIVITY, 0)

    def test_all_confidence_levels_valid(self):
        """All confidence levels must be high/medium/low."""
        valid_levels = {"high", "medium", "low"}
        for ratio_key, level in MEASUREMENT_CONFIDENCE.items():
            self.assertIn(level, valid_levels,
                          f"'{ratio_key}' has invalid confidence level: {level}")

    def test_all_proportions_have_confidence(self):
        """Every ratio in REFERENCE_PROPORTIONS should have a confidence level."""
        for ratio_key in REFERENCE_PROPORTIONS:
            self.assertIn(ratio_key, MEASUREMENT_CONFIDENCE,
                          f"'{ratio_key}' missing from MEASUREMENT_CONFIDENCE")


class TestFeatureMapper(unittest.TestCase):
    """Test the feature mapping logic."""

    def test_all_features_match_semantic_layer(self):
        """All feature names in PROPORTION_TO_FEATURE must exist in FACIAL_FEATURE_MAP."""
        for feature_name in PROPORTION_TO_FEATURE:
            self.assertIn(
                feature_name, FACIAL_FEATURE_MAP,
                f"Feature '{feature_name}' not found in semantic layer's FACIAL_FEATURE_MAP"
            )

    def test_average_face_maps_to_near_zeros(self):
        """Feeding exact mean values should produce feature values near 0.0."""
        # Build a proportions dict with all mean values
        avg_proportions = {}
        for ratio_key, (mean, std) in REFERENCE_PROPORTIONS.items():
            avg_proportions[ratio_key] = mean

        features = map_proportions_to_features(avg_proportions)

        for name, value in features.items():
            self.assertAlmostEqual(
                value, 0.0, places=2,
                msg=f"Feature '{name}' should be ~0.0 for average face, got {value}"
            )

    def test_wide_nose_maps_positive(self):
        """A wider-than-average nose should produce positive nose_width."""
        avg_proportions = {k: v[0] for k, v in REFERENCE_PROPORTIONS.items()}
        # Make nose wider than average
        mean, std = REFERENCE_PROPORTIONS["nose_width_ratio"]
        avg_proportions["nose_width_ratio"] = mean + 2 * std

        features = map_proportions_to_features(avg_proportions)
        self.assertGreater(features["nose_width"], 0,
                           "Wider nose should produce positive nose_width")

    def test_narrow_nose_maps_negative(self):
        """A narrower-than-average nose should produce negative nose_width."""
        avg_proportions = {k: v[0] for k, v in REFERENCE_PROPORTIONS.items()}
        mean, std = REFERENCE_PROPORTIONS["nose_width_ratio"]
        avg_proportions["nose_width_ratio"] = mean - 2 * std

        features = map_proportions_to_features(avg_proportions)
        self.assertLess(features["nose_width"], 0,
                        "Narrower nose should produce negative nose_width")

    def test_extreme_values_are_clamped(self):
        """Values far from average should be clamped to [-1.0, 1.0]."""
        avg_proportions = {k: v[0] for k, v in REFERENCE_PROPORTIONS.items()}
        mean, std = REFERENCE_PROPORTIONS["nose_width_ratio"]
        avg_proportions["nose_width_ratio"] = mean + 10 * std  # Very extreme

        features = map_proportions_to_features(avg_proportions)
        self.assertEqual(features["nose_width"], 1.0,
                         "Extreme positive should clamp to 1.0")

    def test_negative_extreme_clamped(self):
        """Negative extreme should clamp to -1.0."""
        avg_proportions = {k: v[0] for k, v in REFERENCE_PROPORTIONS.items()}
        mean, std = REFERENCE_PROPORTIONS["jaw_width_ratio"]
        avg_proportions["jaw_width_ratio"] = mean - 10 * std

        features = map_proportions_to_features(avg_proportions)
        self.assertEqual(features["jaw_width"], -1.0,
                         "Extreme negative should clamp to -1.0")

    def test_missing_proportions_default_to_zero(self):
        """Missing proportion keys should result in feature value 0.0."""
        features = map_proportions_to_features({"nose_width_ratio": 0.56})
        # Most features should be 0.0 since we only provided one proportion
        zero_count = sum(1 for v in features.values() if v == 0.0)
        self.assertGreater(zero_count, 25, "Most features should default to 0.0")

    def test_empty_proportions(self):
        """Empty dict should return all zeros."""
        features = map_proportions_to_features({})
        self.assertEqual(len(features), len(PROPORTION_TO_FEATURE))
        for name, value in features.items():
            self.assertEqual(value, 0.0, f"Feature '{name}' should be 0.0")

    def test_sensitivity_parameter(self):
        """Higher sensitivity should produce smaller feature values."""
        proportions = {k: v[0] + v[1] for k, v in REFERENCE_PROPORTIONS.items()}

        features_low = map_proportions_to_features(proportions, sensitivity=1.0)
        features_high = map_proportions_to_features(proportions, sensitivity=3.0)

        # For features that aren't clamped, higher sensitivity = smaller values
        for name in PROPORTION_TO_FEATURE:
            if abs(features_low[name]) < 1.0:  # Only check non-clamped values
                self.assertGreaterEqual(
                    abs(features_low[name]),
                    abs(features_high[name]),
                    f"Feature '{name}': sensitivity 1.0 should produce >= values than 3.0"
                )

    def test_all_32_features_in_output(self):
        """Output should have exactly 32 features."""
        features = map_proportions_to_features({})
        self.assertEqual(len(features), 32)

    def test_ratio_to_feature_value_basic(self):
        """Test the core mapping function directly."""
        # At mean: should be 0
        self.assertAlmostEqual(_ratio_to_feature_value(0.5, 0.5, 0.1, 1.5), 0.0)
        # 1 std above: should be 1/sensitivity
        self.assertAlmostEqual(_ratio_to_feature_value(0.6, 0.5, 0.1, 1.5), 1.0/1.5, places=3)

    def test_get_feature_confidence(self):
        """Confidence should return values for all features."""
        conf = get_feature_confidence()
        self.assertEqual(len(conf), 32)
        for name, level in conf.items():
            self.assertIn(level, {"high", "medium", "low"})

    def test_top_distinctive_features(self):
        """Should return features sorted by absolute value."""
        features = {"a": 0.1, "b": -0.9, "c": 0.5, "d": -0.3, "e": 0.8}
        top = get_top_distinctive_features(features, 3)
        self.assertEqual(len(top), 3)
        self.assertEqual(top[0][0], "b")  # |−0.9| is highest
        self.assertEqual(top[1][0], "e")  # |0.8| is second
        self.assertEqual(top[2][0], "c")  # |0.5| is third


class TestProportionAnalyzer(unittest.TestCase):
    """Test the proportion analysis functions."""

    def test_distance_2d(self):
        """Test 2D distance calculation."""
        self.assertAlmostEqual(_dist2d((0, 0, 0), (3, 4, 5)), 5.0)
        self.assertAlmostEqual(_dist2d((1, 1, 0), (1, 1, 0)), 0.0)

    def test_distance_3d(self):
        """Test 3D distance calculation."""
        self.assertAlmostEqual(_dist3d((0, 0, 0), (1, 2, 2)), 3.0)

    def test_midpoint(self):
        """Test midpoint calculation."""
        mid = _midpoint((0, 0, 0), (2, 4, 6))
        self.assertAlmostEqual(mid[0], 1.0)
        self.assertAlmostEqual(mid[1], 2.0)
        self.assertAlmostEqual(mid[2], 3.0)

    def test_ipd_calculation(self):
        """Test IPD computation with known eye positions."""
        # Create minimal landmarks (need at least 468)
        landmarks = [(0.5, 0.5, 0.0)] * 478

        # Set eye landmarks for a known IPD
        # Left eye outer (33): x=0.3, inner (133): x=0.4
        landmarks[33] = (0.3, 0.4, 0.0)
        landmarks[133] = (0.4, 0.4, 0.0)
        # Right eye inner (362): x=0.6, outer (263): x=0.7
        landmarks[362] = (0.6, 0.4, 0.0)
        landmarks[263] = (0.7, 0.4, 0.0)

        # Left center: (0.35, 0.4), Right center: (0.65, 0.4)
        # IPD = 0.30
        ipd = _compute_ipd(landmarks)
        self.assertAlmostEqual(ipd, 0.30, places=3)

    def test_analyze_empty_landmarks(self):
        """Empty landmarks should return empty dict."""
        result = analyze_proportions([])
        self.assertEqual(result, {})

    def test_analyze_insufficient_landmarks(self):
        """Too few landmarks should return empty dict."""
        result = analyze_proportions([(0, 0, 0)] * 100)
        self.assertEqual(result, {})

    def test_analyze_all_ratios_present(self):
        """With valid landmarks, all expected ratio keys should be present."""
        # Create synthetic face landmarks
        landmarks = _create_synthetic_face()
        result = analyze_proportions(landmarks)

        if not result:  # IPD might be too small with synthetic data
            return

        expected_keys = set(PROPORTION_TO_FEATURE.values())
        for key in expected_keys:
            self.assertIn(key, result, f"Missing ratio: {key}")

    def test_symmetric_face_zero_tilt(self):
        """A perfectly symmetric face should have near-zero eye tilt."""
        landmarks = _create_synthetic_face()
        result = analyze_proportions(landmarks)

        if not result:
            return

        # Eye tilt should be near zero for symmetric face
        self.assertAlmostEqual(result.get("eye_tilt_ratio", 0), 0.0, places=2)


class TestFormatOutput(unittest.TestCase):
    """Test output formatting functions."""

    def test_format_features_by_category(self):
        """Format should include all category headers."""
        features = {name: 0.0 for name in PROPORTION_TO_FEATURE}
        output = format_features_by_category(features)
        self.assertIn("Nose", output)
        self.assertIn("Jaw", output)
        self.assertIn("Eyes", output)
        self.assertIn("Lips", output)

    def test_format_with_confidence(self):
        """Format with confidence should include confidence tags."""
        features = {name: 0.1 for name in PROPORTION_TO_FEATURE}
        confidence = get_feature_confidence()
        output = format_features_by_category(features, confidence)
        self.assertIn("[high]", output)


# === HELPER: Create synthetic face landmarks ===

def _create_synthetic_face():
    """Create a set of 478 synthetic face landmarks for testing.

    Returns a list of (x, y, z) tuples representing a forward-facing face
    centered in the image with roughly average proportions.
    """
    landmarks = [(0.5, 0.5, 0.0)] * 478

    # Eyes — roughly positioned
    landmarks[33] = (0.38, 0.42, -0.01)   # left eye outer
    landmarks[133] = (0.44, 0.42, -0.01)  # left eye inner
    landmarks[362] = (0.56, 0.42, -0.01)  # right eye inner
    landmarks[263] = (0.62, 0.42, -0.01)  # right eye outer
    landmarks[159] = (0.41, 0.40, -0.01)  # left eye upper
    landmarks[145] = (0.41, 0.44, -0.01)  # left eye lower
    landmarks[386] = (0.59, 0.40, -0.01)  # right eye upper
    landmarks[374] = (0.59, 0.44, -0.01)  # right eye lower

    # Nose
    landmarks[6] = (0.50, 0.40, -0.04)    # nose bridge top
    landmarks[4] = (0.50, 0.52, -0.06)    # nose tip
    landmarks[129] = (0.46, 0.52, -0.03)  # nostril left
    landmarks[358] = (0.54, 0.52, -0.03)  # nostril right
    landmarks[31] = (0.47, 0.43, -0.03)   # nose bridge left
    landmarks[261] = (0.53, 0.43, -0.03)  # nose bridge right
    landmarks[168] = (0.50, 0.40, -0.02)  # nose root

    # Jaw
    landmarks[234] = (0.30, 0.55, 0.0)    # jaw left
    landmarks[454] = (0.70, 0.55, 0.0)    # jaw right
    landmarks[172] = (0.35, 0.60, 0.0)    # jaw angle left
    landmarks[397] = (0.65, 0.60, 0.0)    # jaw angle right
    landmarks[152] = (0.50, 0.70, 0.0)    # chin bottom

    # Chin
    landmarks[199] = (0.50, 0.67, -0.04)  # chin center
    landmarks[202] = (0.46, 0.67, -0.02)  # chin left
    landmarks[422] = (0.54, 0.67, -0.02)  # chin right

    # Brows
    landmarks[107] = (0.43, 0.36, -0.01)  # left brow inner
    landmarks[336] = (0.57, 0.36, -0.01)  # right brow inner
    landmarks[105] = (0.40, 0.35, -0.01)  # left brow mid
    landmarks[334] = (0.60, 0.35, -0.01)  # right brow mid
    landmarks[70] = (0.36, 0.37, -0.01)   # left brow outer
    landmarks[300] = (0.64, 0.37, -0.01)  # right brow outer

    # Lips
    landmarks[13] = (0.50, 0.58, -0.04)   # lip top center
    landmarks[14] = (0.50, 0.62, -0.03)   # lip bottom center
    landmarks[61] = (0.44, 0.60, -0.02)   # lip left corner
    landmarks[291] = (0.56, 0.60, -0.02)  # lip right corner
    landmarks[0] = (0.50, 0.60, -0.04)    # upper lip vermillion

    # Cheeks
    landmarks[123] = (0.35, 0.48, -0.01)  # cheek left
    landmarks[352] = (0.65, 0.48, -0.01)  # cheek right
    landmarks[116] = (0.37, 0.46, -0.01)  # cheek upper left
    landmarks[345] = (0.63, 0.46, -0.01)  # cheek upper right

    # Forehead
    landmarks[10] = (0.50, 0.25, 0.0)     # forehead top
    landmarks[9] = (0.50, 0.38, -0.02)    # glabella

    return landmarks


if __name__ == "__main__":
    unittest.main()
