"""
Blender MetaHuman MCP Server

Main entry point — creates the FastMCP server, registers all tools,
and runs with STDIO transport for Claude Code integration.
"""

import sys
import os
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
    stream=sys.stderr,  # Log to stderr so it doesn't interfere with STDIO MCP
)
logger = logging.getLogger("blender_metahuman_mcp")

# Add project root to path
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

from mcp.server.fastmcp import FastMCP
from mcp_server.blender_connection import get_connection

# Create the MCP server
mcp = FastMCP(
    "blender-metahuman-mcp",
    instructions="""
    Blender MetaHuman Face Editor - MCP Server

    This server lets you edit MetaHuman facial features in Blender via natural language.

    QUICK START:
    1. check_blender_connection() — verify Blender is running
    2. import_metahuman("path/to/metahuman.fbx") — load a MetaHuman
    3. list_editable_features() — see what you can edit
    4. edit_face_natural("wider nose, stronger jaw") — edit with natural language
    5. render_preview("front") — see the result
    6. export_for_unreal("output.fbx") — export for Unreal Engine

    TOOLS BY LEVEL:
    - High-level: edit_facial_feature, edit_face_natural, apply_face_preset
    - Mid-level: move_bone, scale_bone, rotate_bone
    - Shape keys: set_shape_key, list_shape_keys
    - Scene: import_metahuman, export_for_unreal, render_preview
    - Presets: apply_face_preset, list_face_presets, blend_face_presets
    """
)


def _get_connection():
    """Get the global Blender connection (lazy singleton)."""
    return get_connection()


# Register all tool modules
from mcp_server.tools.face_tools import register_face_tools
from mcp_server.tools.bone_tools import register_bone_tools
from mcp_server.tools.shape_key_tools import register_shape_key_tools
from mcp_server.tools.scene_tools import register_scene_tools
from mcp_server.tools.preset_tools import register_preset_tools

register_face_tools(mcp, _get_connection)
register_bone_tools(mcp, _get_connection)
register_shape_key_tools(mcp, _get_connection)
register_scene_tools(mcp, _get_connection)
register_preset_tools(mcp, _get_connection)

logger.info("All tools registered. Server ready.")


def main():
    """Run the MCP server with STDIO transport."""
    logger.info("Starting Blender MetaHuman MCP Server (STDIO)...")
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
