"""
Photo-to-3D Face Reconstruction Tools

MCP tools that reconstruct a 3D face in Blender from a 2D photo.
Uses MediaPipe for face landmark detection, proportion analysis for
facial measurements, and the semantic layer for bone operations.

Pipeline: Photo -> Landmarks -> Proportions -> Features -> Bone Ops -> Blender
"""

import sys
import os
import logging

logger = logging.getLogger("blender_metahuman_mcp.photo_tools")

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from face_reconstruction import (
    detect_face_landmarks,
    analyze_proportions,
    map_proportions_to_features,
    get_feature_confidence,
)
from face_reconstruction.feature_mapper import (
    get_top_distinctive_features,
    format_features_by_category,
)
from semantic_layer.face_map import (
    get_operations_for_feature, detect_rig_type, FACIAL_FEATURE_MAP
)


def register_photo_tools(mcp, get_connection):
    """Register photo-to-3D reconstruction tools with the MCP server."""

    @mcp.tool()
    def reconstruct_face_from_photo(
        photo_path: str,
        sensitivity: float = 1.5,
        reset_first: bool = True,
    ) -> str:
        """Reconstruct a 3D face in Blender from a 2D photo.

        Analyzes the photo to extract facial proportions, maps them to
        32 facial features, and applies all bone operations to recreate
        the face on the current armature in Blender.

        Args:
            photo_path: Full path to the face photo (JPG, PNG, etc.).
                        The face should be front-facing, well-lit, and clearly visible.
            sensitivity: How aggressively to map facial differences (1.0-3.0).
                         Lower = more exaggerated features.
                         Higher = more subtle/conservative.
                         Default 1.5 is balanced.
            reset_first: If True, resets all facial bones before applying.
                         If False, applies on top of current face state.

        Returns:
            Summary of the reconstruction including features applied.
        """
        conn = get_connection()

        # Step 1: Validate and detect landmarks
        result = detect_face_landmarks(photo_path)
        if not result["success"]:
            return f"Error: {result['error']}"

        confidence = result["confidence"]
        num_landmarks = result["num_landmarks"]

        # Step 2: Analyze proportions
        proportions = analyze_proportions(result["landmarks"])
        if not proportions:
            return "Error: Could not compute facial proportions from landmarks."

        # Step 3: Map to features
        features = map_proportions_to_features(proportions, sensitivity)
        feature_confidence = get_feature_confidence(proportions)

        # Step 4: Reset bones if requested
        if reset_first:
            reset_result = conn.send_command("reset_all_bones", {})
            if reset_result.get("status") != "success":
                return f"Error resetting face: {reset_result.get('error')}"

        # Step 5: Detect rig type
        bones_result = conn.send_command("list_bones", {})
        if bones_result.get("status") != "success":
            return f"Error: {bones_result.get('error', 'Could not list bones')}"

        bone_names = [b["name"] for b in bones_result["result"]["bones"]]
        rig_type = detect_rig_type(bone_names)

        # Step 6: Build ALL bone operations for ALL features at once
        all_ops = []
        applied_features = 0
        skipped_features = []

        for feature_name, value in features.items():
            if abs(value) < 0.01:  # Skip near-zero features (no visible change)
                continue

            operations = get_operations_for_feature(feature_name, rig_type)
            if not operations:
                skipped_features.append(feature_name)
                continue

            for op in operations:
                amount = value * op["multiplier"]
                all_ops.append({
                    "bone_name": op["bone"],
                    "transform": op["transform"],
                    "axis": op["axis"],
                    "amount": amount,
                })

            applied_features += 1

        # Step 7: Send batch operation to Blender
        if not all_ops:
            return "Photo analyzed but no significant facial differences detected from the average face."

        batch_result = conn.send_command("batch_move_bones", {"operations": all_ops})

        if batch_result.get("status") != "success":
            return f"Error applying face: {batch_result.get('error')}"

        applied_ops = batch_result["result"]["applied"]
        skipped_bones = batch_result["result"].get("skipped", [])

        # Step 8: Build summary
        top_features = get_top_distinctive_features(features, 5)

        lines = [
            f"Face reconstructed from photo!",
            f"",
            f"Detection confidence: {confidence:.0%}",
            f"Rig type: {rig_type}",
            f"Features applied: {applied_features}",
            f"Bone operations: {applied_ops}",
        ]

        if skipped_bones:
            lines.append(f"Bones not found: {len(skipped_bones)} (normal for test rigs)")

        lines.append(f"\nMost distinctive features:")
        for name, val in top_features:
            direction = "+" if val > 0 else ""
            conf = feature_confidence.get(name, "")
            lines.append(f"  {name}: {direction}{val:.3f} [{conf}]")

        lines.append(f"\nTip: Use render_preview('front') to see the result.")
        lines.append(f"Tip: Adjust sensitivity (current: {sensitivity}) to fine-tune.")

        return "\n".join(lines)

    @mcp.tool()
    def analyze_face_photo(photo_path: str) -> str:
        """Analyze a face photo and return detected features WITHOUT applying them.

        Useful for previewing what the reconstruction would look like,
        or for getting feature values to manually adjust.

        Args:
            photo_path: Full path to the face photo (JPG, PNG, etc.).

        Returns:
            Detailed analysis of detected facial proportions and features.
        """
        # Step 1: Detect landmarks
        result = detect_face_landmarks(photo_path)
        if not result["success"]:
            return f"Error: {result['error']}"

        # Step 2: Analyze proportions
        proportions = analyze_proportions(result["landmarks"])
        if not proportions:
            return "Error: Could not compute facial proportions."

        # Step 3: Map to features
        features = map_proportions_to_features(proportions)
        confidence_map = get_feature_confidence(proportions)

        # Build report
        lines = [
            f"Face Photo Analysis",
            f"{'=' * 40}",
            f"Image: {photo_path}",
            f"Size: {result['image_width']}x{result['image_height']}",
            f"Landmarks: {result['num_landmarks']}",
            f"Detection confidence: {result['confidence']:.0%}",
        ]

        # Top distinctive features
        top = get_top_distinctive_features(features, 5)
        lines.append(f"\nTop distinctive features:")
        for name, val in top:
            direction = "+" if val > 0 else ""
            lines.append(f"  {name}: {direction}{val:.3f}")

        # Full categorized breakdown
        lines.append(format_features_by_category(features, confidence_map))

        # Non-zero feature count
        non_zero = sum(1 for v in features.values() if abs(v) >= 0.01)
        lines.append(f"\n{non_zero} of {len(features)} features differ from average")
        lines.append(f"\nTo apply: reconstruct_face_from_photo('{photo_path}')")

        return "\n".join(lines)

    @mcp.tool()
    def compare_face_to_photo(photo_path: str) -> str:
        """Compare the current Blender face to a reference photo.

        Shows which features differ between the current 3D face
        and the face detected in the photo.

        Args:
            photo_path: Full path to the reference face photo.

        Returns:
            Comparison showing differences per feature.
        """
        conn = get_connection()

        # Analyze the photo
        result = detect_face_landmarks(photo_path)
        if not result["success"]:
            return f"Error: {result['error']}"

        proportions = analyze_proportions(result["landmarks"])
        if not proportions:
            return "Error: Could not compute facial proportions."

        photo_features = map_proportions_to_features(proportions)

        # Read current Blender bone state to estimate current features
        bones_result = conn.send_command("list_bones", {})
        if bones_result.get("status") != "success":
            return f"Error: {bones_result.get('error')}"

        bone_names = [b["name"] for b in bones_result["result"]["bones"]]
        rig_type = detect_rig_type(bone_names)

        # Estimate current feature values from bone positions
        current_features = {}
        for feature_name, feature_data in FACIAL_FEATURE_MAP.items():
            operations = get_operations_for_feature(feature_name, rig_type)
            total_value = 0.0
            count = 0

            for op in operations:
                bone_result = conn.send_command("get_bone_transform", {"bone_name": op["bone"]})
                if bone_result.get("status") == "success":
                    loc = bone_result["result"]["location"]
                    axis_idx = {"X": 0, "Y": 1, "Z": 2}.get(op["axis"], 0)

                    if op["transform"] == "location" and abs(op["multiplier"]) > 0.0001:
                        approx_value = loc[axis_idx] / op["multiplier"]
                        total_value += approx_value
                        count += 1

            current_features[feature_name] = total_value / max(count, 1) if count > 0 else 0.0

        # Compare
        lines = [
            f"Face Comparison: Current 3D vs Photo",
            f"{'=' * 45}",
            f"",
            f"Feature                  Current   Photo     Delta",
            f"{'-' * 55}",
        ]

        significant_diffs = []
        for name in sorted(photo_features.keys()):
            current = current_features.get(name, 0.0)
            photo = photo_features[name]
            delta = photo - current

            if abs(delta) >= 0.05:
                significant_diffs.append((name, current, photo, delta))
                c_str = f"{current:+.3f}"
                p_str = f"{photo:+.3f}"
                d_str = f"{delta:+.3f}"
                lines.append(f"  {name:<22} {c_str:>8} {p_str:>8} {d_str:>8}")

        if not significant_diffs:
            lines.append("  No significant differences found!")

        lines.append(f"\n{len(significant_diffs)} features with significant differences (>0.05)")
        lines.append(f"\nTo match the photo: reconstruct_face_from_photo('{photo_path}')")

        return "\n".join(lines)
