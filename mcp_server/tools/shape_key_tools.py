"""
Shape key (blend shape / morph target) tools.

Shape keys control facial expressions and corrective shapes.
"""

import logging

logger = logging.getLogger("blender_metahuman_mcp.shape_key_tools")


def register_shape_key_tools(mcp, get_connection):
    """Register shape key tools with the MCP server."""

    @mcp.tool()
    def set_shape_key(name: str, value: float) -> str:
        """Set a shape key value on the face mesh.

        Args:
            name: Shape key name (e.g., "browInnerUp", "mouthSmileLeft").
            value: Value from 0.0 (off) to 1.0 (fully applied).
        """
        conn = get_connection()
        result = conn.send_command("set_shape_key", {"name": name, "value": value})

        if result.get("status") == "success":
            r = result["result"]
            return f"Shape key '{r['shape_key']}' set to {r['value']} on mesh '{r['mesh']}'"
        return f"Error: {result.get('error')}"

    @mcp.tool()
    def get_shape_key(name: str) -> str:
        """Get the current value of a shape key.

        Args:
            name: Shape key name.
        """
        conn = get_connection()
        result = conn.send_command("get_shape_key", {"name": name})

        if result.get("status") == "success":
            r = result["result"]
            return (
                f"Shape key: {r['shape_key']}\n"
                f"  Value: {r['value']}\n"
                f"  Range: {r['slider_min']} to {r['slider_max']}\n"
                f"  Muted: {r['mute']}"
            )
        return f"Error: {result.get('error')}"

    @mcp.tool()
    def list_shape_keys(filter_text: str = "") -> str:
        """List all shape keys on the face mesh.

        Args:
            filter_text: Optional substring to filter shape key names.
        """
        conn = get_connection()
        result = conn.send_command("list_shape_keys", {"filter": filter_text})

        if result.get("status") == "success":
            r = result["result"]
            lines = [f"Mesh: {r['mesh']} ({r['count']} shape keys)"]
            for sk in r["shape_keys"]:
                val_str = f" = {sk['value']:.3f}" if sk["value"] != 0.0 else ""
                muted = " [MUTED]" if sk["mute"] else ""
                lines.append(f"  {sk['name']}{val_str}{muted}")
            return "\n".join(lines)
        return f"Error: {result.get('error')}"

    @mcp.tool()
    def reset_all_shape_keys() -> str:
        """Reset all shape keys to 0.0 (neutral face)."""
        conn = get_connection()
        result = conn.send_command("reset_all_shape_keys", {})

        if result.get("status") == "success":
            return f"Reset {result['result']['shape_keys_reset']} shape keys to 0.0"
        return f"Error: {result.get('error')}"
