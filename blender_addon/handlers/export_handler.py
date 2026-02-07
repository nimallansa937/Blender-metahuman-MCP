"""
Export handlers — FBX export for Unreal Engine and preview rendering.
"""

import bpy
import os
import tempfile
import base64
import math
import logging

logger = logging.getLogger("blender_metahuman_mcp.export_handler")


def handle_export_fbx(params):
    """Export scene/selected objects as FBX for Unreal Engine.

    params: {
        filepath: str,
        selected_only: bool (default True),
        apply_modifiers: bool (default True)
    }
    """
    filepath = params.get("filepath", "")
    if not filepath:
        # Default export path
        filepath = os.path.join(tempfile.gettempdir(), "metahuman_export.fbx")

    selected_only = params.get("selected_only", True)
    apply_modifiers = params.get("apply_modifiers", True)

    # Ensure directory exists
    os.makedirs(os.path.dirname(filepath), exist_ok=True)

    # Ensure object mode
    if bpy.context.mode != "OBJECT":
        bpy.ops.object.mode_set(mode="OBJECT")

    try:
        bpy.ops.export_scene.fbx(
            filepath=filepath,
            use_selection=selected_only,
            apply_scale_options="FBX_SCALE_ALL",
            use_mesh_modifiers=apply_modifiers,
            mesh_smooth_type="FACE",
            add_leaf_bones=False,
            bake_anim=False,
            axis_forward="-Y",
            axis_up="Z",
        )

        file_size = os.path.getsize(filepath) if os.path.exists(filepath) else 0

        return {
            "status": "success",
            "result": {
                "filepath": filepath,
                "file_size_bytes": file_size,
                "selected_only": selected_only,
            }
        }
    except Exception as e:
        return {"status": "error", "error": f"FBX export failed: {e}"}


def handle_render_preview(params):
    """Render a preview of the current viewport.

    params: {
        angle: "front"|"side"|"three_quarter"|"current" (default "front"),
        resolution_x: int (default 512),
        resolution_y: int (default 512),
        filepath: str (optional, defaults to temp file)
    }
    """
    angle = params.get("angle", "front")
    res_x = int(params.get("resolution_x", 512))
    res_y = int(params.get("resolution_y", 512))
    filepath = params.get("filepath", "")

    if not filepath:
        filepath = os.path.join(tempfile.gettempdir(), f"metahuman_preview_{angle}.png")

    scene = bpy.context.scene

    # Set render settings
    scene.render.resolution_x = res_x
    scene.render.resolution_y = res_y
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.render.filepath = filepath

    # Position camera based on angle
    camera = None
    for obj in scene.objects:
        if obj.type == "CAMERA":
            camera = obj
            break

    if not camera:
        # Create a temporary camera using data API (no operator context needed)
        cam_data = bpy.data.cameras.new(name="MCP_Preview_Cam")
        cam_data.lens = 85  # Portrait lens
        camera = bpy.data.objects.new("MCP_Preview_Camera", cam_data)
        bpy.context.collection.objects.link(camera)

    scene.camera = camera

    # Ensure we have a light for rendering
    has_light = any(obj.type == "LIGHT" for obj in scene.objects)
    if not has_light:
        light_data = bpy.data.lights.new(name="MCP_Preview_Light", type="AREA")
        light_data.energy = 100
        light_data.size = 0.5
        light_obj = bpy.data.objects.new("MCP_Preview_Light", light_data)
        bpy.context.collection.objects.link(light_obj)
        light_obj.location = (0.3, -0.5, 2.0)
        light_obj.rotation_euler = (math.radians(30), 0, math.radians(10))

    # Find the head/face center for aiming
    target_loc = (0, 0, 1.6)  # Default head height
    for obj in scene.objects:
        if obj.type == "ARMATURE":
            head_bone = obj.pose.bones.get("head") or obj.pose.bones.get("Head")
            if head_bone:
                target_loc = list(obj.matrix_world @ head_bone.head)
            break

    # Set camera position based on angle
    distance = 0.5  # Close-up distance for face
    if angle == "front":
        camera.location = (target_loc[0], target_loc[1] - distance, target_loc[2])
        camera.rotation_euler = (math.radians(90), 0, 0)
    elif angle == "side":
        camera.location = (target_loc[0] + distance, target_loc[1], target_loc[2])
        camera.rotation_euler = (math.radians(90), 0, math.radians(90))
    elif angle == "three_quarter":
        camera.location = (
            target_loc[0] + distance * 0.7,
            target_loc[1] - distance * 0.7,
            target_loc[2] + 0.1
        )
        camera.rotation_euler = (math.radians(80), 0, math.radians(45))
    # "current" = don't move camera

    try:
        bpy.ops.render.render(write_still=True)

        return {
            "status": "success",
            "result": {
                "filepath": filepath,
                "angle": angle,
                "resolution": f"{res_x}x{res_y}",
            }
        }
    except Exception as e:
        return {"status": "error", "error": f"Render failed: {e}"}


def get_export_handlers():
    """Return dict mapping command names to handler functions."""
    return {
        "export_fbx": handle_export_fbx,
        "render_preview": handle_render_preview,
    }
