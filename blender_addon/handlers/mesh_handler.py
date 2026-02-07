"""
Mesh information handlers.

Provides info about mesh geometry, vertex groups, and dimensions.
"""

import bpy
import logging

logger = logging.getLogger("blender_metahuman_mcp.mesh_handler")


def _get_mesh_object(name=None):
    """Get a mesh object by name, or find the head/face mesh."""
    if name:
        obj = bpy.data.objects.get(name)
        if obj and obj.type == "MESH":
            return obj
        return None

    # Try active object
    obj = bpy.context.active_object
    if obj and obj.type == "MESH":
        return obj

    # Search for head/face mesh
    for obj in bpy.context.scene.objects:
        if obj.type == "MESH":
            lower = obj.name.lower()
            if "head" in lower or "face" in lower:
                return obj

    # Fallback: first mesh
    for obj in bpy.context.scene.objects:
        if obj.type == "MESH":
            return obj

    return None


def handle_get_mesh_info(params):
    """Get detailed info about a mesh.

    params: {name: str (optional, defaults to head/active mesh)}
    """
    obj = _get_mesh_object(params.get("name"))
    if not obj:
        return {"status": "error", "error": "No mesh found."}

    mesh = obj.data
    bounds = [list(v) for v in obj.bound_box]

    return {
        "status": "success",
        "result": {
            "name": obj.name,
            "vertex_count": len(mesh.vertices),
            "edge_count": len(mesh.edges),
            "face_count": len(mesh.polygons),
            "has_shape_keys": mesh.shape_keys is not None,
            "shape_key_count": len(mesh.shape_keys.key_blocks) if mesh.shape_keys else 0,
            "vertex_group_count": len(obj.vertex_groups),
            "dimensions": list(obj.dimensions),
            "location": list(obj.location),
            "bounding_box": bounds,
            "material_count": len(obj.material_slots),
            "materials": [slot.material.name if slot.material else None for slot in obj.material_slots],
        }
    }


def handle_get_vertex_groups(params):
    """List all vertex groups on a mesh.

    params: {name: str (optional), filter: str (optional)}
    """
    obj = _get_mesh_object(params.get("name"))
    if not obj:
        return {"status": "error", "error": "No mesh found."}

    filter_str = params.get("filter", "").lower()
    groups = []

    for vg in obj.vertex_groups:
        if filter_str and filter_str not in vg.name.lower():
            continue
        groups.append({
            "name": vg.name,
            "index": vg.index,
            "lock_weight": vg.lock_weight,
        })

    return {
        "status": "success",
        "result": {
            "mesh": obj.name,
            "count": len(groups),
            "vertex_groups": groups
        }
    }


def handle_list_meshes(params):
    """List all mesh objects in the scene.

    params: {} (none required)
    """
    meshes = []
    for obj in bpy.context.scene.objects:
        if obj.type == "MESH":
            meshes.append({
                "name": obj.name,
                "vertex_count": len(obj.data.vertices),
                "has_shape_keys": obj.data.shape_keys is not None,
                "location": list(obj.location),
                "visible": obj.visible_get(),
            })

    return {
        "status": "success",
        "result": {
            "count": len(meshes),
            "meshes": meshes
        }
    }


def get_mesh_handlers():
    """Return dict mapping command names to handler functions."""
    return {
        "get_mesh_info": handle_get_mesh_info,
        "get_vertex_groups": handle_get_vertex_groups,
        "list_meshes": handle_list_meshes,
    }
