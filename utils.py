import bpy

# ISO 668 Dimensions in meters
CONTAINER_SIZES = {
    '10FT': {'length': 2.991, 'width': 2.438, 'height': 2.591},
    '20FT': {'length': 6.058, 'width': 2.438, 'height': 2.591},
    '40FT': {'length': 12.192, 'width': 2.438, 'height': 2.591},
}

def find_container_root(obj):
    """Return the container root for an object (the object itself or any descendant)."""
    cur = obj
    while cur:
        # Pointer property exists only while the addon is registered.
        if hasattr(cur, "shipping_container") and getattr(cur.shipping_container, "is_container", False):
            return cur
        cur = cur.parent
    return None

def remove_object_and_orphan_data(obj):
    """Remove an object and purge its datablock if it becomes orphaned.

    Blender keeps datablocks (meshes/curves/etc.) even after their objects are deleted,
    so procedural rebuilds can quickly bloat .blend files unless we clean up.
    """
    data = obj.data
    bpy.data.objects.remove(obj, do_unlink=True)

    if not data:
        return

    # Never remove linked library data.
    if getattr(data, "library", None) is not None:
        return

    # Respect fake users (e.g., cached master meshes).
    if getattr(data, "use_fake_user", False):
        return

    if getattr(data, "users", 0) != 0:
        return

    # Note: text objects (type='FONT') store data in bpy.data.curves (Curve datablock).
    if isinstance(data, bpy.types.Mesh):
        bpy.data.meshes.remove(data)
    elif isinstance(data, bpy.types.Curve):
        bpy.data.curves.remove(data)

def clear_container_children(root_obj):
    """Safely deletes all generated container parts parented to the root (recursively)."""

    def get_all_children(obj):
        children = []
        for child in obj.children:
            children.append(child)
            children.extend(get_all_children(child))
        return children

    # Get all nested children
    objs_to_delete = [child for child in get_all_children(root_obj) if child.get("is_container_part")]

    # Reverse the list so we delete deepest children first (prevents unparenting issues)
    objs_to_delete.reverse()

    for obj in objs_to_delete:
        remove_object_and_orphan_data(obj)
