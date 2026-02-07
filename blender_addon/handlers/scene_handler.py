"""
Scene management handlers.

Handles scene info, object selection, undo/redo, and FBX import.
"""

import bpy
import os
import logging

logger = logging.getLogger("blender_metahuman_mcp.scene_handler")


def handle_get_scene_info(params):
    """Get overview of the current scene.

    params: {} (none required)
    """
    scene = bpy.context.scene
    objects = []

    for obj in scene.objects:
        objects.append({
            "name": obj.name,
            "type": obj.type,
            "location": list(obj.location),
            "visible": obj.visible_get(),
            "selected": obj.select_get(),
        })

    active = bpy.context.active_object

    return {
        "status": "success",
        "result": {
            "scene_name": scene.name,
            "object_count": len(objects),
            "active_object": active.name if active else None,
            "active_type": active.type if active else None,
            "mode": bpy.context.mode,
            "frame_current": scene.frame_current,
            "objects": objects,
        }
    }


def handle_select_object(params):
    """Select an object by name.

    params: {name: str, add: bool (optional, add to selection)}
    """
    name = params.get("name", "")
    add_to_selection = params.get("add", False)

    obj = bpy.data.objects.get(name)
    if not obj:
        return {"status": "error", "error": f"Object '{name}' not found"}

    # Ensure we're in object mode
    if bpy.context.mode != "OBJECT":
        bpy.ops.object.mode_set(mode="OBJECT")

    if not add_to_selection:
        bpy.ops.object.select_all(action="DESELECT")

    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj

    return {
        "status": "success",
        "result": {"selected": name, "type": obj.type}
    }


def handle_undo(params):
    """Undo the last operation.

    params: {} (none required)
    """
    try:
        bpy.ops.ed.undo()
        return {"status": "success", "result": {"action": "undo"}}
    except Exception as e:
        return {"status": "error", "error": f"Undo failed: {e}"}


def handle_redo(params):
    """Redo the last undone operation.

    params: {} (none required)
    """
    try:
        bpy.ops.ed.redo()
        return {"status": "success", "result": {"action": "redo"}}
    except Exception as e:
        return {"status": "error", "error": f"Redo failed: {e}"}


def handle_import_fbx(params):
    """Import an FBX file (MetaHuman or other).

    params: {filepath: str}
    """
    filepath = params.get("filepath", "")
    if not filepath:
        return {"status": "error", "error": "No filepath provided"}

    if not os.path.exists(filepath):
        return {"status": "error", "error": f"File not found: {filepath}"}

    # Ensure object mode
    if bpy.context.mode != "OBJECT":
        bpy.ops.object.mode_set(mode="OBJECT")

    try:
        bpy.ops.import_scene.fbx(filepath=filepath)

        # Find imported objects (they'll be selected)
        imported = [obj.name for obj in bpy.context.selected_objects]

        # Try to find the armature
        armature = None
        for obj in bpy.context.selected_objects:
            if obj.type == "ARMATURE":
                armature = obj.name
                bpy.context.view_layer.objects.active = obj
                break

        return {
            "status": "success",
            "result": {
                "filepath": filepath,
                "imported_objects": imported,
                "armature": armature,
                "count": len(imported)
            }
        }
    except Exception as e:
        return {"status": "error", "error": f"FBX import failed: {e}"}


def handle_delete_object(params):
    """Delete an object by name.

    params: {name: str}
    """
    name = params.get("name", "")
    obj = bpy.data.objects.get(name)
    if not obj:
        return {"status": "error", "error": f"Object '{name}' not found"}

    if bpy.context.mode != "OBJECT":
        bpy.ops.object.mode_set(mode="OBJECT")

    bpy.ops.object.select_all(action="DESELECT")
    obj.select_set(True)
    bpy.ops.object.delete()

    return {"status": "success", "result": {"deleted": name}}


def get_scene_handlers():
    """Return dict mapping command names to handler functions."""
    return {
        "get_scene_info": handle_get_scene_info,
        "select_object": handle_select_object,
        "undo": handle_undo,
        "redo": handle_redo,
        "import_fbx": handle_import_fbx,
        "delete_object": handle_delete_object,
    }
