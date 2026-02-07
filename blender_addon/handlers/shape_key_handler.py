"""
Shape key (blend shape) manipulation handlers.

Shape keys control facial expressions, corrective shapes, and morph targets.
"""

import bpy
import logging

logger = logging.getLogger("blender_metahuman_mcp.shape_key_handler")


def _get_mesh_with_shape_keys():
    """Find the active mesh object that has shape keys, or search for one."""
    obj = bpy.context.active_object
    if obj and obj.type == "MESH" and obj.data.shape_keys:
        return obj

    # Search for a mesh with shape keys (prefer head mesh)
    for obj in bpy.context.scene.objects:
        if obj.type == "MESH" and obj.data.shape_keys:
            if "head" in obj.name.lower() or "face" in obj.name.lower():
                return obj

    # Fallback: any mesh with shape keys
    for obj in bpy.context.scene.objects:
        if obj.type == "MESH" and obj.data.shape_keys:
            return obj

    return None


def handle_set_shape_key(params):
    """Set a shape key value.

    params: {name: str, value: float (0.0 to 1.0)}
    """
    obj = _get_mesh_with_shape_keys()
    if not obj:
        return {"status": "error", "error": "No mesh with shape keys found."}

    name = params.get("name", "")
    value = float(params.get("value", 0.0))
    value = max(0.0, min(1.0, value))  # Clamp to valid range

    key_block = obj.data.shape_keys.key_blocks.get(name)
    if not key_block:
        return {"status": "error", "error": f"Shape key '{name}' not found on '{obj.name}'"}

    key_block.value = value
    bpy.context.view_layer.update()

    return {
        "status": "success",
        "result": {
            "mesh": obj.name,
            "shape_key": name,
            "value": value
        }
    }


def handle_get_shape_key(params):
    """Get current value of a shape key.

    params: {name: str}
    """
    obj = _get_mesh_with_shape_keys()
    if not obj:
        return {"status": "error", "error": "No mesh with shape keys found."}

    name = params.get("name", "")
    key_block = obj.data.shape_keys.key_blocks.get(name)
    if not key_block:
        return {"status": "error", "error": f"Shape key '{name}' not found"}

    return {
        "status": "success",
        "result": {
            "mesh": obj.name,
            "shape_key": name,
            "value": key_block.value,
            "slider_min": key_block.slider_min,
            "slider_max": key_block.slider_max,
            "mute": key_block.mute,
        }
    }


def handle_list_shape_keys(params):
    """List all shape keys on the mesh.

    params: {filter: str (optional substring filter)}
    """
    obj = _get_mesh_with_shape_keys()
    if not obj:
        return {"status": "error", "error": "No mesh with shape keys found."}

    filter_str = params.get("filter", "").lower()
    shape_keys = []

    for kb in obj.data.shape_keys.key_blocks:
        if filter_str and filter_str not in kb.name.lower():
            continue
        shape_keys.append({
            "name": kb.name,
            "value": kb.value,
            "slider_min": kb.slider_min,
            "slider_max": kb.slider_max,
            "mute": kb.mute,
        })

    return {
        "status": "success",
        "result": {
            "mesh": obj.name,
            "count": len(shape_keys),
            "shape_keys": shape_keys
        }
    }


def handle_reset_all_shape_keys(params):
    """Reset all shape keys to 0.0.

    params: {} (none required)
    """
    obj = _get_mesh_with_shape_keys()
    if not obj:
        return {"status": "error", "error": "No mesh with shape keys found."}

    count = 0
    for kb in obj.data.shape_keys.key_blocks:
        if kb.name == "Basis":
            continue  # Don't touch the basis shape
        kb.value = 0.0
        count += 1

    bpy.context.view_layer.update()

    return {
        "status": "success",
        "result": {"mesh": obj.name, "shape_keys_reset": count}
    }


def handle_batch_set_shape_keys(params):
    """Set multiple shape keys at once.

    params: {values: {shape_key_name: float_value, ...}}
    """
    obj = _get_mesh_with_shape_keys()
    if not obj:
        return {"status": "error", "error": "No mesh with shape keys found."}

    values = params.get("values", {})
    applied = []
    skipped = []

    for name, value in values.items():
        kb = obj.data.shape_keys.key_blocks.get(name)
        if not kb:
            skipped.append(name)
            continue
        kb.value = max(0.0, min(1.0, float(value)))
        applied.append({"name": name, "value": kb.value})

    bpy.context.view_layer.update()

    return {
        "status": "success",
        "result": {
            "mesh": obj.name,
            "applied": applied,
            "skipped": skipped
        }
    }


def get_shape_key_handlers():
    """Return dict mapping command names to handler functions."""
    return {
        "set_shape_key": handle_set_shape_key,
        "get_shape_key": handle_get_shape_key,
        "list_shape_keys": handle_list_shape_keys,
        "reset_all_shape_keys": handle_reset_all_shape_keys,
        "batch_set_shape_keys": handle_batch_set_shape_keys,
    }
