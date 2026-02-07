"""
Scene management tools — import, export, render preview, undo/redo.
"""

import logging

logger = logging.getLogger("blender_metahuman_mcp.scene_tools")


def register_scene_tools(mcp, get_connection):
    """Register scene management tools with the MCP server."""

    @mcp.tool()
    def import_metahuman(file_path: str) -> str:
        """Import a MetaHuman FBX file into Blender.

        After import, the armature will be auto-detected and ready for
        facial feature editing.

        Args:
            file_path: Full path to the .fbx file.
        """
        conn = get_connection()
        result = conn.send_command("import_fbx", {"filepath": file_path})

        if result.get("status") == "success":
            r = result["result"]
            lines = [
                f"Imported: {r['filepath']}",
                f"Objects imported: {r['count']}",
                f"Armature: {r['armature'] or 'None detected'}",
            ]
            if r.get("imported_objects"):
                lines.append(f"Objects: {', '.join(r['imported_objects'][:10])}")
            return "\n".join(lines)
        return f"Error: {result.get('error')}"

    @mcp.tool()
    def export_for_unreal(file_path: str = "", selected_only: bool = True) -> str:
        """Export the modified MetaHuman as FBX for Unreal Engine.

        Uses Unreal-compatible FBX settings (Z-up, scale 1.0, no leaf bones).

        Args:
            file_path: Output path for the .fbx file. Defaults to temp directory.
            selected_only: If True, export only selected objects.
        """
        conn = get_connection()
        result = conn.send_command("export_fbx", {
            "filepath": file_path,
            "selected_only": selected_only,
        })

        if result.get("status") == "success":
            r = result["result"]
            size_kb = r.get("file_size_bytes", 0) / 1024
            return (
                f"Exported to: {r['filepath']}\n"
                f"File size: {size_kb:.1f} KB\n"
                f"Selected only: {r['selected_only']}\n\n"
                f"To import into Unreal Engine:\n"
                f"  1. Use UnrealMCP's execute_python tool:\n"
                f"     unreal.EditorAssetLibrary.import_asset('{r['filepath']}')\n"
                f"  2. Or drag the FBX into the Unreal Content Browser"
            )
        return f"Error: {result.get('error')}"

    @mcp.tool()
    def render_preview(angle: str = "front") -> str:
        """Render a preview image of the current face.

        Args:
            angle: Camera angle — "front", "side", "three_quarter", or "current".
        """
        conn = get_connection()
        result = conn.send_command("render_preview", {"angle": angle})

        if result.get("status") == "success":
            r = result["result"]
            return (
                f"Preview rendered: {r['filepath']}\n"
                f"Angle: {r['angle']}\n"
                f"Resolution: {r['resolution']}"
            )
        return f"Error: {result.get('error')}"

    @mcp.tool()
    def undo() -> str:
        """Undo the last operation in Blender."""
        conn = get_connection()
        result = conn.send_command("undo", {})
        if result.get("status") == "success":
            return "Undo successful"
        return f"Error: {result.get('error')}"

    @mcp.tool()
    def redo() -> str:
        """Redo the last undone operation in Blender."""
        conn = get_connection()
        result = conn.send_command("redo", {})
        if result.get("status") == "success":
            return "Redo successful"
        return f"Error: {result.get('error')}"

    @mcp.tool()
    def get_scene_info() -> str:
        """Get information about the current Blender scene.

        Returns list of objects, active object, current mode, etc.
        """
        conn = get_connection()
        result = conn.send_command("get_scene_info", {})

        if result.get("status") == "success":
            r = result["result"]
            lines = [
                f"Scene: {r['scene_name']}",
                f"Mode: {r['mode']}",
                f"Active object: {r['active_object']} ({r['active_type']})",
                f"Objects ({r['object_count']}):",
            ]
            for obj in r["objects"][:20]:
                vis = "visible" if obj["visible"] else "hidden"
                sel = " [selected]" if obj["selected"] else ""
                lines.append(f"  {obj['name']} ({obj['type']}) - {vis}{sel}")
            return "\n".join(lines)
        return f"Error: {result.get('error')}"

    @mcp.tool()
    def get_mesh_info(name: str = "") -> str:
        """Get detailed information about a mesh object.

        Args:
            name: Mesh name (optional, defaults to head/face mesh).
        """
        conn = get_connection()
        result = conn.send_command("get_mesh_info", {"name": name})

        if result.get("status") == "success":
            r = result["result"]
            lines = [
                f"Mesh: {r['name']}",
                f"  Vertices: {r['vertex_count']}",
                f"  Faces: {r['face_count']}",
                f"  Shape keys: {r['shape_key_count']}",
                f"  Vertex groups: {r['vertex_group_count']}",
                f"  Materials: {r['material_count']}",
                f"  Dimensions: {r['dimensions']}",
            ]
            return "\n".join(lines)
        return f"Error: {result.get('error')}"

    @mcp.tool()
    def check_blender_connection() -> str:
        """Check if Blender is running and the MCP addon is active."""
        conn = get_connection()
        if conn.ping():
            return "Connected to Blender successfully. MCP addon is running."
        return "Cannot connect to Blender. Ensure Blender is running with the MCP addon enabled on port 9876."
