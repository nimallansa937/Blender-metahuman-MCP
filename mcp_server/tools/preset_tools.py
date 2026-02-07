"""
Face preset tools — apply predefined facial feature combinations.
"""

import sys
import os
import logging

logger = logging.getLogger("blender_metahuman_mcp.preset_tools")

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from semantic_layer.presets import FACE_PRESETS, list_presets, get_preset, blend_presets


def register_preset_tools(mcp, get_connection):
    """Register face preset tools with the MCP server."""

    @mcp.tool()
    def apply_face_preset(preset_name: str, intensity: float = 1.0) -> str:
        """Apply a predefined face preset.

        Presets are combinations of facial features that create a
        specific look (e.g., "angular_face", "button_nose", "heroic").

        Args:
            preset_name: Name of the preset. Use list_face_presets to see options.
            intensity: How strongly to apply (0.0 to 1.0). Default 1.0 = full.
        """
        preset = get_preset(preset_name)
        if not preset:
            available = ", ".join(list_presets().keys())
            return f"Preset '{preset_name}' not found. Available: {available}"

        # Import face_tools edit function via connection
        from semantic_layer.face_map import get_operations_for_feature, detect_rig_type
        from semantic_layer.validators import clamp_value

        conn = get_connection()

        # Detect rig
        bones_result = conn.send_command("list_bones", {})
        if bones_result.get("status") != "success":
            return f"Error: {bones_result.get('error')}"

        bone_names = [b["name"] for b in bones_result["result"]["bones"]]
        rig_type = detect_rig_type(bone_names)

        # Apply each feature in the preset
        results = []
        all_ops = []

        for feature_name, value in preset["features"].items():
            adjusted_value = value * intensity
            adjusted_value, _ = clamp_value(adjusted_value)

            operations = get_operations_for_feature(feature_name, rig_type)
            for op in operations:
                amount = adjusted_value * op["multiplier"]
                all_ops.append({
                    "bone_name": op["bone"],
                    "transform": op["transform"],
                    "axis": op["axis"],
                    "amount": amount,
                })
            results.append(f"  {feature_name}: {adjusted_value:+.2f}")

        # Batch apply all operations
        batch_result = conn.send_command("batch_move_bones", {"operations": all_ops})

        if batch_result.get("status") == "success":
            applied = batch_result["result"]["applied"]
            skipped = batch_result["result"]["skipped"]
            header = f"Applied preset '{preset_name}' ({preset['description']}) at {intensity:.0%} intensity"
            features_str = "\n".join(results)
            footer = f"\n{applied} bone operations applied"
            if skipped:
                footer += f", {len(skipped)} bones not found"
            return f"{header}\n{features_str}{footer}"
        return f"Error applying preset: {batch_result.get('error')}"

    @mcp.tool()
    def list_face_presets() -> str:
        """List all available face presets with descriptions.

        Returns preset names grouped by type (face shape, nose, eyes, etc.)
        """
        presets = list_presets()

        lines = ["Available Face Presets:\n"]
        for name, description in sorted(presets.items()):
            lines.append(f"  {name}: {description}")

        lines.append(f"\nTotal: {len(presets)} presets")
        lines.append("Use apply_face_preset(name) to apply, or apply_face_preset(name, 0.5) for half intensity.")

        return "\n".join(lines)

    @mcp.tool()
    def blend_face_presets(preset_a: str, preset_b: str, blend_factor: float = 0.5) -> str:
        """Blend between two face presets.

        Creates a face that's a mix between two presets.

        Args:
            preset_a: First preset name.
            preset_b: Second preset name.
            blend_factor: 0.0 = fully preset A, 1.0 = fully preset B, 0.5 = equal mix.
        """
        blended = blend_presets(preset_a, preset_b, blend_factor)
        if blended is None:
            return f"Error: One or both presets not found ('{preset_a}', '{preset_b}')"

        # Apply the blended features
        from semantic_layer.face_map import get_operations_for_feature, detect_rig_type
        from semantic_layer.validators import clamp_value

        conn = get_connection()

        bones_result = conn.send_command("list_bones", {})
        if bones_result.get("status") != "success":
            return f"Error: {bones_result.get('error')}"

        bone_names = [b["name"] for b in bones_result["result"]["bones"]]
        rig_type = detect_rig_type(bone_names)

        all_ops = []
        for feature_name, value in blended.items():
            value, _ = clamp_value(value)
            operations = get_operations_for_feature(feature_name, rig_type)
            for op in operations:
                all_ops.append({
                    "bone_name": op["bone"],
                    "transform": op["transform"],
                    "axis": op["axis"],
                    "amount": value * op["multiplier"],
                })

        result = conn.send_command("batch_move_bones", {"operations": all_ops})

        if result.get("status") == "success":
            return (
                f"Blended '{preset_a}' ({1-blend_factor:.0%}) + '{preset_b}' ({blend_factor:.0%})\n"
                f"Applied {result['result']['applied']} bone operations"
            )
        return f"Error: {result.get('error')}"
