"""
Blender MetaHuman MCP Addon

Provides a TCP server inside Blender that accepts JSON commands
for editing MetaHuman facial features (bones, shape keys, mesh).
Designed to work with the blender-metahuman-mcp MCP server.
"""

bl_info = {
    "name": "MCP: MetaHuman Face Editor",
    "author": "blender-metahuman-mcp",
    "version": (0, 1, 0),
    "blender": (4, 0, 0),
    "location": "View3D > Sidebar > MCP",
    "description": "TCP server for AI-driven MetaHuman facial editing via MCP",
    "category": "MCP",
}

import bpy
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("blender_metahuman_mcp")

# Module-level references
_tcp_server = None
_command_router = None


class MCP_OT_StartServer(bpy.types.Operator):
    """Start the MCP TCP Server"""
    bl_idname = "mcp.start_server"
    bl_label = "Start MCP Server"

    def execute(self, context):
        start_server()
        self.report({"INFO"}, "MCP TCP Server started on port 9876")
        return {"FINISHED"}


class MCP_OT_StopServer(bpy.types.Operator):
    """Stop the MCP TCP Server"""
    bl_idname = "mcp.stop_server"
    bl_label = "Stop MCP Server"

    def execute(self, context):
        stop_server()
        self.report({"INFO"}, "MCP TCP Server stopped")
        return {"FINISHED"}


class MCP_PT_Panel(bpy.types.Panel):
    """MCP Server Control Panel"""
    bl_label = "MCP MetaHuman"
    bl_idname = "MCP_PT_Panel"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "MCP"

    def draw(self, context):
        layout = self.layout
        layout.label(text="MetaHuman Face Editor")
        layout.separator()

        row = layout.row()
        row.operator("mcp.start_server", icon="PLAY")
        row.operator("mcp.stop_server", icon="PAUSE")

        layout.separator()
        global _tcp_server
        if _tcp_server and _tcp_server._running:
            layout.label(text="Status: Running", icon="CHECKMARK")
            layout.label(text=f"Port: {_tcp_server.port}")
        else:
            layout.label(text="Status: Stopped", icon="X")


def _build_command_router():
    """Create and configure the command router with all handlers."""
    from .command_router import CommandRouter
    from .handlers.bone_handler import get_bone_handlers
    from .handlers.shape_key_handler import get_shape_key_handlers
    from .handlers.mesh_handler import get_mesh_handlers
    from .handlers.scene_handler import get_scene_handlers
    from .handlers.export_handler import get_export_handlers

    router = CommandRouter()
    router.register_many(get_bone_handlers())
    router.register_many(get_shape_key_handlers())
    router.register_many(get_mesh_handlers())
    router.register_many(get_scene_handlers())
    router.register_many(get_export_handlers())

    # Register a ping/health-check command
    router.register("ping", lambda params: {"status": "success", "result": "pong"})
    router.register("list_commands", lambda params: {
        "status": "success",
        "result": router.list_commands()
    })

    logger.info(f"Command router ready with {len(router.list_commands())} commands")
    return router


def start_server():
    """Start the TCP server and command queue timer."""
    global _tcp_server, _command_router

    from .tcp_server import MCPTCPServer
    from .utils.thread_safe import command_queue

    if _tcp_server and _tcp_server._running:
        logger.warning("Server already running")
        return

    _command_router = _build_command_router()
    command_queue.start_timer()

    _tcp_server = MCPTCPServer(
        host="127.0.0.1",
        port=9876,
        command_router=_command_router
    )
    _tcp_server.start()


def stop_server():
    """Stop the TCP server and command queue timer."""
    global _tcp_server

    from .utils.thread_safe import command_queue

    if _tcp_server:
        _tcp_server.stop()
        _tcp_server = None

    command_queue.stop_timer()


# Registration
classes = (
    MCP_OT_StartServer,
    MCP_OT_StopServer,
    MCP_PT_Panel,
)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    logger.info("MCP MetaHuman addon registered")
    # Auto-start server on addon load
    bpy.app.timers.register(lambda: (start_server(), None)[-1], first_interval=1.0)


def unregister():
    stop_server()
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
    logger.info("MCP MetaHuman addon unregistered")
