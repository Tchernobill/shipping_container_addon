import bpy

from ..utils import remove_object_and_orphan_data
from .primitives import (
    append_box,
    create_object_from_mesh,
    get_or_create_box_mesh,
)


def _get_scene(context=None):
    if context is not None and getattr(context, "scene", None) is not None:
        return context.scene
    return bpy.context.scene


def _get_depsgraph(context=None):
    if context is not None and hasattr(context, "evaluated_depsgraph_get"):
        return context.evaluated_depsgraph_get()
    return bpy.context.evaluated_depsgraph_get()

def create_floor_cross_members(name, width, length, spacing=0.3, pocket_spacing=2.05):
    """Generates transverse floor cross members (structural support beams)."""
    # Typical floor cross member dimensions (C-channel or I-beam)
    beam_w = width
    beam_l = 0.05 # 50mm wide
    beam_h = 0.0975 # Match rail height perfectly
    
    # Calculate number of cross members based on length and spacing
    num_beams = max(1, int(length / spacing))
    actual_spacing = length / num_beams
    
    pocket_w = 0.300 # Scaled pocket width
    pocket_y1 = -pocket_spacing/2
    pocket_y2 = pocket_spacing/2
    
    mesh_name = (
        f"_ISO_FloorCrossMembers_{int(round(width*1e6))}_{int(round(length*1e6))}_"
        f"{int(round(spacing*1e6))}_{int(round(pocket_spacing*1e6))}"
    )
    mesh = bpy.data.meshes.get(mesh_name)
    if mesh is None:
        verts = []
        faces = []

        # Generate cross members
        for i in range(1, num_beams):
            y_pos = -length / 2 + i * actual_spacing

            # Skip cross members that intersect with the forklift pockets
            if (abs(y_pos - pocket_y1) < pocket_w / 2 + 0.05) or (abs(y_pos - pocket_y2) < pocket_w / 2 + 0.05):
                continue

            append_box(verts, faces, center=(0.0, y_pos, 0.0), size=(beam_w, beam_l, beam_h))

        mesh = bpy.data.meshes.new(mesh_name)
        mesh.from_pydata(verts, [], faces)
        mesh.update()
        mesh.use_fake_user = True

    return create_object_from_mesh(name, mesh, tag_container_part=True)

def create_wooden_floor(name, width, length):
    """Generates the marine plywood floor panels."""
    # Standard marine plywood thickness is 28mm
    thickness = 0.028

    mesh = get_or_create_box_mesh(width, length, thickness, keep=True)
    return create_object_from_mesh(name, mesh, tag_container_part=True)

def create_forklift_pocket_cutters(name, width, spacing=2.05):
    """Creates boolean cutters for punching holes in the side rails."""
    pocket_w = 0.300 
    pocket_h = 0.080 
    pocket_d = width + 0.5 # Extra wide to ensure it cuts completely through

    mesh_name = f"_ISO_PocketCutters_{int(round(width*1e6))}_{int(round(spacing*1e6))}"
    mesh = bpy.data.meshes.get(mesh_name)
    if mesh is None:
        verts = []
        faces = []
        append_box(verts, faces, center=(0.0, -spacing / 2, 0.0), size=(pocket_d, pocket_w, pocket_h))
        append_box(verts, faces, center=(0.0, spacing / 2, 0.0), size=(pocket_d, pocket_w, pocket_h))
        mesh = bpy.data.meshes.new(mesh_name)
        mesh.from_pydata(verts, [], faces)
        mesh.update()
        mesh.use_fake_user = True

    return create_object_from_mesh(name, mesh, tag_container_part=True)

def create_forklift_pocket_tubes(name, width, spacing=2.05):
    """Generates the structural tubes for the forklift pockets."""
    pocket_w = 0.300
    pocket_h = 0.080
    t = 0.006 # 6mm steel thickness

    mesh_name = f"_ISO_PocketTubes_{int(round(width*1e6))}_{int(round(spacing*1e6))}"
    mesh = bpy.data.meshes.get(mesh_name)
    if mesh is None:
        verts = []
        faces = []

        for y_offset in [-spacing / 2, spacing / 2]:
            # Top plate
            append_box(
                verts,
                faces,
                center=(0.0, y_offset, pocket_h / 2 + t / 2),
                size=(width, pocket_w + 2 * t, t),
            )

            # Bottom plate
            append_box(
                verts,
                faces,
                center=(0.0, y_offset, -pocket_h / 2 - t / 2),
                size=(width, pocket_w + 2 * t, t),
            )

            # Front plate
            append_box(
                verts,
                faces,
                center=(0.0, y_offset - pocket_w / 2 - t / 2, 0.0),
                size=(width, t, pocket_h),
            )

            # Back plate
            append_box(
                verts,
                faces,
                center=(0.0, y_offset + pocket_w / 2 + t / 2, 0.0),
                size=(width, t, pocket_h),
            )

        mesh = bpy.data.meshes.new(mesh_name)
        mesh.from_pydata(verts, [], faces)
        mesh.update()
        mesh.use_fake_user = True

    return create_object_from_mesh(name, mesh, tag_container_part=True)


def get_or_create_side_rail_with_forklift_pockets_mesh(
    rail_x,
    rail_y,
    rail_z,
    *,
    pocket_w=0.300,
    pocket_h=0.080,
    spacing=2.05,
    context=None,
):
    """Return a cached side-rail mesh with two forklift-pocket holes cut in (no per-rebuild booleans)."""
    mesh_name = (
        f"ISO_SideRail_WithPockets_{int(round(rail_x*1e6))}_{int(round(rail_y*1e6))}_"
        f"{int(round(rail_z*1e6))}_{int(round(pocket_w*1e6))}_{int(round(pocket_h*1e6))}_"
        f"{int(round(spacing*1e6))}"
    )
    existing = bpy.data.meshes.get(mesh_name)
    if existing is not None:
        return existing

    scene = _get_scene(context=context)

    # Base rail object (temporary, centered at origin)
    base_mesh = get_or_create_box_mesh(rail_x, rail_y, rail_z, keep=False)
    base_obj = bpy.data.objects.new("_TempRail_Base", base_mesh)
    scene.collection.objects.link(base_obj)

    # Cutter object: two through-rail boxes, slightly over-sized in X so they cut fully.
    cutter_x = rail_x + 0.05
    cutter_mesh = bpy.data.meshes.new("_TempRail_Cutter")
    cv = []
    cf = []
    append_box(cv, cf, center=(0.0, -spacing / 2, 0.0), size=(cutter_x, pocket_w, pocket_h))
    append_box(cv, cf, center=(0.0, spacing / 2, 0.0), size=(cutter_x, pocket_w, pocket_h))
    cutter_mesh.from_pydata(cv, [], cf)
    cutter_mesh.update()
    cutter_obj = bpy.data.objects.new("_TempRail_CutterObj", cutter_mesh)
    scene.collection.objects.link(cutter_obj)

    try:
        mod = base_obj.modifiers.new(name="Forklift_Pockets", type="BOOLEAN")
        mod.object = cutter_obj
        mod.operation = "DIFFERENCE"
        mod.solver = "MANIFOLD"

        depsgraph = _get_depsgraph(context=context)
        eval_obj = base_obj.evaluated_get(depsgraph)
        new_mesh = bpy.data.meshes.new_from_object(eval_obj)
        new_mesh.name = mesh_name
        new_mesh.use_fake_user = True
    finally:
        # Cleanup temp objects & non-cached data
        remove_object_and_orphan_data(base_obj)
        remove_object_and_orphan_data(cutter_obj)

    return new_mesh


def create_side_rail_with_forklift_pockets(
    name,
    rail_x,
    rail_y,
    rail_z,
    location,
    *,
    pocket_w=0.300,
    pocket_h=0.080,
    spacing=2.05,
    context=None,
):
    mesh = get_or_create_side_rail_with_forklift_pockets_mesh(
        rail_x,
        rail_y,
        rail_z,
        pocket_w=pocket_w,
        pocket_h=pocket_h,
        spacing=spacing,
        context=context,
    )
    return create_object_from_mesh(name, mesh, location=location, tag_container_part=True)
