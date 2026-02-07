"""
Bone manipulation handlers.

All functions run on Blender's main thread (via CommandQueue).
They manipulate pose bones on the active armature.
"""

import bpy
import math
import logging

logger = logging.getLogger("blender_metahuman_mcp.bone_handler")


def _get_armature():
    """Find the active armature or the first armature in the scene."""
    obj = bpy.context.active_object
    if obj and obj.type == "ARMATURE":
        return obj

    # Search scene for an armature
    for obj in bpy.context.scene.objects:
        if obj.type == "ARMATURE":
            return obj

    return None


def _ensure_pose_mode(armature):
    """Ensure the armature is selected and in pose mode."""
    bpy.context.view_layer.objects.active = armature
    armature.select_set(True)
    if bpy.context.mode != "POSE":
        bpy.ops.object.mode_set(mode="POSE")


def _get_pose_bone(armature, bone_name):
    """Get a pose bone by name, returns None if not found."""
    return armature.pose.bones.get(bone_name)


def _axis_index(axis_str):
    """Convert axis string to index: X=0, Y=1, Z=2."""
    return {"X": 0, "Y": 1, "Z": 2}.get(axis_str.upper(), 0)


# --- Handler Functions ---

def handle_move_bone(params):
    """Move a bone along an axis.

    params: {bone_name: str, axis: "X"|"Y"|"Z", amount: float, space: "LOCAL"|"WORLD"}
    """
    armature = _get_armature()
    if not armature:
        return {"status": "error", "error": "No armature found. Import a MetaHuman FBX first."}

    bone_name = params.get("bone_name", "")
    axis = params.get("axis", "X").upper()
    amount = float(params.get("amount", 0.0))

    _ensure_pose_mode(armature)
    bone = _get_pose_bone(armature, bone_name)
    if not bone:
        return {"status": "error", "error": f"Bone '{bone_name}' not found in armature '{armature.name}'"}

    idx = _axis_index(axis)
    bone.location[idx] += amount

    # Force viewport update
    bpy.context.view_layer.update()

    return {
        "status": "success",
        "result": {
            "bone_name": bone_name,
            "axis": axis,
            "amount": amount,
            "new_location": list(bone.location)
        }
    }


def handle_scale_bone(params):
    """Scale a bone along an axis.

    params: {bone_name: str, axis: "X"|"Y"|"Z", amount: float}
    """
    armature = _get_armature()
    if not armature:
        return {"status": "error", "error": "No armature found."}

    bone_name = params.get("bone_name", "")
    axis = params.get("axis", "X").upper()
    amount = float(params.get("amount", 1.0))

    _ensure_pose_mode(armature)
    bone = _get_pose_bone(armature, bone_name)
    if not bone:
        return {"status": "error", "error": f"Bone '{bone_name}' not found"}

    idx = _axis_index(axis)
    bone.scale[idx] *= (1.0 + amount)

    bpy.context.view_layer.update()

    return {
        "status": "success",
        "result": {
            "bone_name": bone_name,
            "axis": axis,
            "new_scale": list(bone.scale)
        }
    }


def handle_rotate_bone(params):
    """Rotate a bone on an axis (in degrees).

    params: {bone_name: str, axis: "X"|"Y"|"Z", degrees: float}
    """
    armature = _get_armature()
    if not armature:
        return {"status": "error", "error": "No armature found."}

    bone_name = params.get("bone_name", "")
    axis = params.get("axis", "X").upper()
    degrees = float(params.get("degrees", 0.0))

    _ensure_pose_mode(armature)
    bone = _get_pose_bone(armature, bone_name)
    if not bone:
        return {"status": "error", "error": f"Bone '{bone_name}' not found"}

    idx = _axis_index(axis)
    bone.rotation_euler[idx] += math.radians(degrees)

    bpy.context.view_layer.update()

    return {
        "status": "success",
        "result": {
            "bone_name": bone_name,
            "axis": axis,
            "degrees": degrees,
            "new_rotation_euler": [math.degrees(r) for r in bone.rotation_euler]
        }
    }


def handle_get_bone_transform(params):
    """Get current transform of a bone.

    params: {bone_name: str}
    """
    armature = _get_armature()
    if not armature:
        return {"status": "error", "error": "No armature found."}

    bone_name = params.get("bone_name", "")
    _ensure_pose_mode(armature)
    bone = _get_pose_bone(armature, bone_name)
    if not bone:
        return {"status": "error", "error": f"Bone '{bone_name}' not found"}

    return {
        "status": "success",
        "result": {
            "bone_name": bone_name,
            "location": list(bone.location),
            "rotation_euler": [math.degrees(r) for r in bone.rotation_euler],
            "scale": list(bone.scale),
            "head_world": list(armature.matrix_world @ bone.head),
            "tail_world": list(armature.matrix_world @ bone.tail),
        }
    }


def handle_list_bones(params):
    """List all bones in the active armature.

    params: {filter: str (optional, glob/substring filter)}
    """
    armature = _get_armature()
    if not armature:
        return {"status": "error", "error": "No armature found."}

    filter_str = params.get("filter", "").lower()

    bones = []
    for bone in armature.pose.bones:
        if filter_str and filter_str not in bone.name.lower():
            continue
        bones.append({
            "name": bone.name,
            "location": list(bone.location),
            "has_children": len(bone.children) > 0,
            "parent": bone.parent.name if bone.parent else None,
        })

    return {
        "status": "success",
        "result": {
            "armature": armature.name,
            "count": len(bones),
            "bones": bones
        }
    }


def handle_reset_bone(params):
    """Reset a bone to its rest position.

    params: {bone_name: str}
    """
    armature = _get_armature()
    if not armature:
        return {"status": "error", "error": "No armature found."}

    bone_name = params.get("bone_name", "")
    _ensure_pose_mode(armature)
    bone = _get_pose_bone(armature, bone_name)
    if not bone:
        return {"status": "error", "error": f"Bone '{bone_name}' not found"}

    bone.location = (0, 0, 0)
    bone.rotation_euler = (0, 0, 0)
    bone.rotation_quaternion = (1, 0, 0, 0)
    bone.scale = (1, 1, 1)

    bpy.context.view_layer.update()

    return {
        "status": "success",
        "result": {"bone_name": bone_name, "reset": True}
    }


def handle_reset_all_bones(params):
    """Reset ALL pose bones to rest position.

    params: {} (none required)
    """
    armature = _get_armature()
    if not armature:
        return {"status": "error", "error": "No armature found."}

    _ensure_pose_mode(armature)
    count = 0
    for bone in armature.pose.bones:
        bone.location = (0, 0, 0)
        bone.rotation_euler = (0, 0, 0)
        bone.rotation_quaternion = (1, 0, 0, 0)
        bone.scale = (1, 1, 1)
        count += 1

    bpy.context.view_layer.update()

    return {
        "status": "success",
        "result": {"bones_reset": count}
    }


def handle_batch_move_bones(params):
    """Move multiple bones at once.

    params: {operations: [{bone_name, axis, amount}, ...]}
    """
    armature = _get_armature()
    if not armature:
        return {"status": "error", "error": "No armature found."}

    operations = params.get("operations", [])
    _ensure_pose_mode(armature)

    results = []
    skipped = []

    for op in operations:
        bone_name = op.get("bone_name", "")
        axis = op.get("axis", "X").upper()
        amount = float(op.get("amount", 0.0))
        transform = op.get("transform", "location")

        bone = _get_pose_bone(armature, bone_name)
        if not bone:
            skipped.append(bone_name)
            continue

        idx = _axis_index(axis)

        if transform == "location":
            bone.location[idx] += amount
        elif transform == "scale":
            bone.scale[idx] *= (1.0 + amount)
        elif transform == "rotation":
            bone.rotation_euler[idx] += math.radians(amount)

        results.append({
            "bone_name": bone_name,
            "transform": transform,
            "axis": axis,
            "amount": amount
        })

    bpy.context.view_layer.update()

    return {
        "status": "success",
        "result": {
            "applied": len(results),
            "skipped": skipped,
            "operations": results
        }
    }


def get_bone_handlers():
    """Return dict mapping command names to handler functions."""
    return {
        "move_bone": handle_move_bone,
        "scale_bone": handle_scale_bone,
        "rotate_bone": handle_rotate_bone,
        "get_bone_transform": handle_get_bone_transform,
        "list_bones": handle_list_bones,
        "reset_bone": handle_reset_bone,
        "reset_all_bones": handle_reset_all_bones,
        "batch_move_bones": handle_batch_move_bones,
    }
