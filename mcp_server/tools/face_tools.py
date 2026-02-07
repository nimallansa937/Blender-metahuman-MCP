"""
High-level facial feature editing tools.

These are the primary tools Claude Code uses to edit MetaHuman faces
via natural language. They use the semantic layer to translate
feature names into bone operations.
"""

import sys
import os
import logging

logger = logging.getLogger("blender_metahuman_mcp.face_tools")

# Add project root to path for semantic_layer import
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from semantic_layer.face_map import (
    FACIAL_FEATURE_MAP, get_operations_for_feature, get_all_features,
    get_features_by_category, detect_rig_type
)
from semantic_layer.validators import (
    validate_feature_name, clamp_value, normalize_direction, parse_natural_description
)


def register_face_tools(mcp, get_connection):
    """Register high-level face editing tools with the MCP server."""

    @mcp.tool()
    def edit_facial_feature(feature: str, value: float) -> str:
        """Edit a specific facial feature by name and value.

        Args:
            feature: Feature name (e.g., "nose_width", "jaw_width", "eye_size").
                     Use list_editable_features to see all available features.
            value: Value from -1.0 to 1.0.
                   Negative = decrease (narrower, smaller, lower)
                   Positive = increase (wider, bigger, higher)
                   0.0 = default/neutral position.

        Returns:
            Summary of applied bone operations.
        """
        conn = get_connection()

        # Validate feature name
        validation = validate_feature_name(feature)
        if not validation["valid"]:
            return f"Error: {validation['error']}"

        feature_name = validation["name"]
        value, was_clamped = clamp_value(value)

        # Detect rig type by listing bones first
        bones_result = conn.send_command("list_bones", {})
        if bones_result.get("status") != "success":
            return f"Error: {bones_result.get('error', 'Could not list bones')}"

        bone_names = [b["name"] for b in bones_result["result"]["bones"]]
        rig_type = detect_rig_type(bone_names)

        # Get resolved operations
        operations = get_operations_for_feature(feature_name, rig_type)
        if not operations:
            return f"Error: No operations defined for feature '{feature_name}'"

        # Build batch bone operation
        batch_ops = []
        for op in operations:
            amount = value * op["multiplier"]
            batch_ops.append({
                "bone_name": op["bone"],
                "transform": op["transform"],
                "axis": op["axis"],
                "amount": amount,
            })

        result = conn.send_command("batch_move_bones", {"operations": batch_ops})

        if result.get("status") == "success":
            applied = result["result"]["applied"]
            skipped = result["result"]["skipped"]
            msg = f"Applied '{feature_name}' = {value} ({applied} bone operations"
            if was_clamped:
                msg += ", value was clamped to range"
            if skipped:
                msg += f", {len(skipped)} bones not found: {skipped}"
            msg += f", rig type: {rig_type})"
            return msg
        else:
            return f"Error: {result.get('error', 'Unknown error')}"

    @mcp.tool()
    def edit_face_natural(description: str) -> str:
        """Edit facial features using natural language description.

        Parses descriptions like:
          "wider nose, stronger jawline, bigger eyes"
          "make the nose narrower and the lips fuller"
          "slightly wider face with higher cheekbones"

        Args:
            description: Natural language description of desired changes.

        Returns:
            Summary of all applied changes.
        """
        edits = parse_natural_description(description)

        if not edits:
            return (
                "Could not parse any facial feature changes from your description. "
                "Try being more specific, e.g., 'wider nose, fuller lips, stronger jaw'. "
                "Use list_editable_features to see available features."
            )

        results = []
        for edit in edits:
            result = edit_facial_feature(edit["feature"], edit["value"])
            results.append(f"  {edit['feature']}: {edit['value']:+.2f} ({edit.get('direction', '')}) -> {result}")

        return f"Applied {len(edits)} changes from: \"{description}\"\n" + "\n".join(results)

    @mcp.tool()
    def list_editable_features() -> str:
        """List all available facial features that can be edited.

        Returns a categorized list of features with descriptions and valid ranges.
        """
        categories = get_features_by_category()
        all_features = get_all_features()

        lines = ["Available Facial Features:\n"]
        for category, feature_names in sorted(categories.items()):
            lines.append(f"\n=== {category.upper()} ===")
            for name in sorted(feature_names):
                info = all_features[name]
                lines.append(f"  {name}: {info['description']} (range: {info['range'][0]} to {info['range'][1]})")

        lines.append(f"\nTotal: {len(all_features)} features across {len(categories)} categories")
        lines.append("\nUse edit_facial_feature(feature, value) to modify any feature.")
        lines.append("Use edit_face_natural('description') for natural language editing.")

        return "\n".join(lines)

    @mcp.tool()
    def describe_current_face() -> str:
        """Describe the current facial features by reading bone positions.

        Returns a natural language description of which features
        have been modified from the default position.
        """
        conn = get_connection()

        bones_result = conn.send_command("list_bones", {})
        if bones_result.get("status") != "success":
            return f"Error: {bones_result.get('error')}"

        bone_names = [b["name"] for b in bones_result["result"]["bones"]]
        rig_type = detect_rig_type(bone_names)

        # Check each feature's bones for modifications
        modified = []
        for feature_name, feature_data in FACIAL_FEATURE_MAP.items():
            operations = get_operations_for_feature(feature_name, rig_type)
            total_deviation = 0.0

            for op in operations:
                bone_result = conn.send_command("get_bone_transform", {"bone_name": op["bone"]})
                if bone_result.get("status") == "success":
                    loc = bone_result["result"]["location"]
                    axis_idx = {"X": 0, "Y": 1, "Z": 2}.get(op["axis"], 0)

                    if op["transform"] == "location" and abs(loc[axis_idx]) > 0.0005:
                        # Reverse-calculate the approximate feature value
                        if abs(op["multiplier"]) > 0.0001:
                            approx_value = loc[axis_idx] / op["multiplier"]
                            total_deviation += abs(approx_value)

            if total_deviation > 0.05:
                modified.append(feature_name)

        if not modified:
            return "Face is at default position — no features have been modified."

        return f"Modified features: {', '.join(modified)}\nUse get_bone_transform for detailed values."

    @mcp.tool()
    def reset_face() -> str:
        """Reset all facial bones to their default rest position.

        This undoes all facial feature modifications.
        """
        conn = get_connection()
        result = conn.send_command("reset_all_bones", {})

        if result.get("status") == "success":
            return f"Face reset to default. {result['result']['bones_reset']} bones restored."
        else:
            return f"Error: {result.get('error')}"
