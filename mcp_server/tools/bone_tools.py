"""
Mid-level bone manipulation tools.

Direct bone control for advanced users who know specific bone names.
"""

import logging

logger = logging.getLogger("blender_metahuman_mcp.bone_tools")


def register_bone_tools(mcp, get_connection):
    """Register bone manipulation tools with the MCP server."""

    @mcp.tool()
    def move_bone(bone_name: str, axis: str, amount: float) -> str:
        """Move a specific bone along an axis.

        Args:
            bone_name: Exact bone name in the armature.
            axis: "X", "Y", or "Z".
            amount: Distance to move (in Blender units/meters). Small values like 0.005.

        Returns:
            New bone position after the move.
        """
        conn = get_connection()
        result = conn.send_command("move_bone", {
            "bone_name": bone_name,
            "axis": axis.upper(),
            "amount": amount,
        })

        if result.get("status") == "success":
            r = result["result"]
            return f"Moved {r['bone_name']} on {r['axis']} by {r['amount']}. New location: {r['new_location']}"
        return f"Error: {result.get('error')}"

    @mcp.tool()
    def scale_bone(bone_name: str, axis: str, amount: float) -> str:
        """Scale a bone on an axis.

        Args:
            bone_name: Exact bone name.
            axis: "X", "Y", or "Z".
            amount: Scale delta (e.g., 0.2 = 20% larger, -0.2 = 20% smaller).
        """
        conn = get_connection()
        result = conn.send_command("scale_bone", {
            "bone_name": bone_name,
            "axis": axis.upper(),
            "amount": amount,
        })

        if result.get("status") == "success":
            r = result["result"]
            return f"Scaled {r['bone_name']} on {r['axis']}. New scale: {r['new_scale']}"
        return f"Error: {result.get('error')}"

    @mcp.tool()
    def rotate_bone(bone_name: str, axis: str, degrees: float) -> str:
        """Rotate a bone on an axis.

        Args:
            bone_name: Exact bone name.
            axis: "X", "Y", or "Z".
            degrees: Rotation in degrees.
        """
        conn = get_connection()
        result = conn.send_command("rotate_bone", {
            "bone_name": bone_name,
            "axis": axis.upper(),
            "degrees": degrees,
        })

        if result.get("status") == "success":
            r = result["result"]
            return f"Rotated {r['bone_name']} on {r['axis']} by {r['degrees']}deg. New rotation: {r['new_rotation_euler']}"
        return f"Error: {result.get('error')}"

    @mcp.tool()
    def get_bone_info(bone_name: str) -> str:
        """Get the current transform of a specific bone.

        Args:
            bone_name: Exact bone name.

        Returns:
            Location, rotation, and scale of the bone.
        """
        conn = get_connection()
        result = conn.send_command("get_bone_transform", {"bone_name": bone_name})

        if result.get("status") == "success":
            r = result["result"]
            return (
                f"Bone: {r['bone_name']}\n"
                f"  Location: {r['location']}\n"
                f"  Rotation: {r['rotation_euler']} degrees\n"
                f"  Scale: {r['scale']}\n"
                f"  World head: {r['head_world']}\n"
                f"  World tail: {r['tail_world']}"
            )
        return f"Error: {result.get('error')}"

    @mcp.tool()
    def list_all_bones(filter_pattern: str = "") -> str:
        """List all bones in the armature.

        Args:
            filter_pattern: Optional substring filter (e.g., "nose", "FACIAL", "jaw").

        Returns:
            List of bone names with their parent relationships.
        """
        conn = get_connection()
        result = conn.send_command("list_bones", {"filter": filter_pattern})

        if result.get("status") == "success":
            r = result["result"]
            lines = [f"Armature: {r['armature']} ({r['count']} bones)"]
            for bone in r["bones"][:100]:  # Limit output
                parent = f" (parent: {bone['parent']})" if bone["parent"] else ""
                lines.append(f"  {bone['name']}{parent}")
            if r["count"] > 100:
                lines.append(f"  ... and {r['count'] - 100} more. Use filter to narrow results.")
            return "\n".join(lines)
        return f"Error: {result.get('error')}"

    @mcp.tool()
    def reset_bone(bone_name: str) -> str:
        """Reset a single bone to its rest position.

        Args:
            bone_name: Exact bone name.
        """
        conn = get_connection()
        result = conn.send_command("reset_bone", {"bone_name": bone_name})

        if result.get("status") == "success":
            return f"Bone '{bone_name}' reset to rest position."
        return f"Error: {result.get('error')}"
