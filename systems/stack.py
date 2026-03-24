"""
systems/stack.py
================
Container Stack Creator.

Patch history
─────────────
v1  BUG 1 — Fatal: stack_width / depth / height / seed / random_orient missing
            from properties.py.  Guarded with AttributeError + clear message.
    BUG 2 — Fatal: baked mesh origin was at an arbitrary child-object world
            position; transform_apply() now collapses it to (0,0,0) before the
            grid offset is assigned.
    BUG 3 — Visual: gap fillers were placed cx/cy metres *inside* the stack
            boundary so they were fully occluded.  Now flush with outer face ± ε.
    BUG 4 — Documented: outer-perimeter-only fillers are correct for solid stacks.

v2  FEATURE — Concrete base slab added as the stack root object.
            • Dimensions  : (sw·W + 2·MARGIN) × (sd·L + 2·MARGIN) × BASE_THICKNESS
              where MARGIN = 2.0 m and BASE_THICKNESS = 0.3 m.
            • Top surface sits exactly at z = 0 so containers rest flush on it.
            • Origin placed at the stack front-left-bottom corner (0, 0, 0) so
              all container slot offsets (i·W, j·L, k·H) remain in local space
              without any coordinate translation.
            • Replaces the old stack_root_empty as the hierarchy root; all baked
              containers and gap fillers are parented directly to the slab mesh.
            • A procedural concrete material (Principled BSDF + Noise for surface
              variation) is created once and reused across stacks.
"""

import bpy
import math
import random

from ..utils import CONTAINER_SIZES, clear_container_children
from .rebuild import rebuild_container
from ..geometry.primitives import append_box, append_plane_xy, create_mesh_object


# ─────────────────────────────────────────────────────────────────────────────
# Constants
# ─────────────────────────────────────────────────────────────────────────────

BASE_MARGIN    = 2.0    # metres the slab extends beyond each stack edge
BASE_THICKNESS = 0.3    # metres — typical heavy-duty container-yard concrete slab


# ─────────────────────────────────────────────────────────────────────────────
# Concrete material
# ─────────────────────────────────────────────────────────────────────────────

def _get_or_create_concrete_material():
    """Return a cached procedural concrete material, creating it if needed.

    The material is a Principled BSDF driven by a Noise texture so adjacent
    stacks with the same material still show subtle surface variation.  Fully
    procedural — no image textures required.
    """
    mat_name = "Stack_Concrete_Base"
    if mat_name in bpy.data.materials:
        return bpy.data.materials[mat_name]

    mat = bpy.data.materials.new(name=mat_name)
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    nodes.clear()

    # Output
    out = nodes.new('ShaderNodeOutputMaterial')
    out.location = (600, 0)

    # Principled BSDF — concrete-like defaults
    bsdf = nodes.new('ShaderNodeBsdfPrincipled')
    bsdf.location = (300, 0)
    bsdf.inputs['Roughness'].default_value           = 0.92
    bsdf.inputs['Metallic'].default_value            = 0.0
    bsdf.inputs['Specular IOR Level'].default_value  = 0.05

    # Noise texture — drives subtle colour and roughness variation
    noise = nodes.new('ShaderNodeTexNoise')
    noise.location = (-400, 100)
    noise.inputs['Scale'].default_value      = 8.0
    noise.inputs['Detail'].default_value     = 6.0
    noise.inputs['Roughness'].default_value  = 0.65
    noise.inputs['Distortion'].default_value = 0.2

    # Colour ramp: maps noise into a narrow concrete-grey band
    # dark grey (#4A4A4A) → light grey (#8A8A8A), both as linear values
    ramp_col = nodes.new('ShaderNodeValToRGB')
    ramp_col.location = (-100, 100)
    ramp_col.color_ramp.interpolation = 'LINEAR'
    ramp_col.color_ramp.elements[0].position = 0.35
    ramp_col.color_ramp.elements[0].color    = (0.071, 0.071, 0.071, 1.0)
    ramp_col.color_ramp.elements[1].position = 0.75
    ramp_col.color_ramp.elements[1].color    = (0.264, 0.264, 0.264, 1.0)

    # Roughness ramp: slight bump so the surface isn't perfectly uniform
    ramp_rough = nodes.new('ShaderNodeValToRGB')
    ramp_rough.location = (-100, -200)
    ramp_rough.color_ramp.interpolation = 'LINEAR'
    ramp_rough.color_ramp.elements[0].position = 0.0
    ramp_rough.color_ramp.elements[0].color    = (0.85, 0.85, 0.85, 1.0)
    ramp_rough.color_ramp.elements[1].position = 1.0
    ramp_rough.color_ramp.elements[1].color    = (1.0,  1.0,  1.0,  1.0)

    # Texture coordinate — Object space so scale is consistent regardless of
    # how the slab is positioned in the scene.
    tex_coord = nodes.new('ShaderNodeTexCoord')
    tex_coord.location = (-600, 100)

    # Wire up
    links.new(tex_coord.outputs['Object'],  noise.inputs['Vector'])
    links.new(noise.outputs['Fac'],         ramp_col.inputs['Fac'])
    links.new(noise.outputs['Fac'],         ramp_rough.inputs['Fac'])
    links.new(ramp_col.outputs['Color'],    bsdf.inputs['Base Color'])
    links.new(ramp_rough.outputs['Color'],  bsdf.inputs['Roughness'])
    links.new(bsdf.outputs['BSDF'],         out.inputs['Surface'])

    return mat


# ─────────────────────────────────────────────────────────────────────────────
# Concrete base geometry
# ─────────────────────────────────────────────────────────────────────────────

def _create_concrete_base(name, stack_x, stack_y, margin, thickness):
    """Create the concrete slab mesh and return the object (not yet linked).

    Geometry layout in local space (origin = world 0, 0, 0):

        X : -margin          …  stack_x + margin
        Y : -margin          …  stack_y + margin
        Z : -thickness       …  0.0          ← top face flush with ground level

    The origin is intentionally placed at the front-left-bottom corner of the
    stack footprint (matching the addon axis convention) so that container slot
    offsets (i·W, j·L, k·H) translate directly into local space without any
    additional offset.

    Args:
        name      : object and mesh name string
        stack_x   : total stack width  = sw * W  (metres)
        stack_y   : total stack depth  = sd * L  (metres)
        margin    : extra slab overhang on every side  (BASE_MARGIN)
        thickness : slab thickness in metres  (BASE_THICKNESS)

    Returns:
        bpy.types.Object — caller must link to a collection before use.
    """
    total_x = stack_x + 2.0 * margin
    total_y = stack_y + 2.0 * margin

    verts = []
    faces = []
    append_box(
        verts,
        faces,
        center=(stack_x / 2.0, stack_y / 2.0, -thickness / 2.0),
        size=(total_x, total_y, thickness),
    )

    obj = create_mesh_object(
        name,
        verts,
        faces,
        location=(0.0, 0.0, 0.0),
        tag_container_part=False,
        extra_props={"is_stack_base": True},
    )
    return obj


# ─────────────────────────────────────────────────────────────────────────────
# Visibility logic
# ─────────────────────────────────────────────────────────────────────────────

def _get_visible_faces(i, j, k, sw, sd, sh, front_facing):
    """Return the show_* visibility dict for a container at stack position (i, j, k).

    Coordinate convention (matches the addon's global axis contract):
        i → X (width)   : 0 = left  edge of stack
        j → Y (depth)   : 0 = front face of stack
        k → Z (height)  : 0 = ground level
    """

    is_stack_left = i == 0
    is_stack_right = i == sw - 1
    is_stack_front = j == 0
    is_stack_back = j == sd - 1

    show_floor = k == 0
    show_roof = k == sh - 1

    if front_facing:
        # Container's local axes align with the global stack axes — no remapping.
        show_f = is_stack_front
        show_b = is_stack_back
        show_l = is_stack_left
        show_r = is_stack_right
    else:
        # Container is rotated 180° around Z.
        # Local +Y (front/doors) → Global -Y (stack back).
        # Local +X (right side)  → Global -X (stack left).
        show_f = is_stack_back    # local front  → global back
        show_b = is_stack_front   # local back   → global front
        show_l = is_stack_right   # local left   → global right
        show_r = is_stack_left    # local right  → global left

    return {
        'show_front_panel': show_f,
        'show_left_door':   show_f,
        'show_right_door':  show_f,
        'show_back_panel':  show_b,
        'show_left_panel':  show_l,
        'show_right_panel': show_r,
        'show_floor':       show_floor,
        'show_roof':        show_roof,
    }


# ─────────────────────────────────────────────────────────────────────────────
# Single-container bake helper
# ─────────────────────────────────────────────────────────────────────────────

def _bake_temp_container(source_root, vis_flags, seed, context, work_col):
    """Build a temporary container with only the required faces, then bake to one mesh.

    BUG 2 FIX: After joining the duplicated children we call transform_apply() to
    collapse the world-space offsets of all child objects into the mesh vertex data.
    This guarantees the returned object has:
        location  = (0, 0, 0)           ← container-local origin
        geometry  spans 0→W, 0→L, 0→H  (front-left-bottom corner at origin)

    The caller can then safely assign .location = (i*W, j*L, k*H) and the mesh
    will land exactly in the right grid slot with no residual displacement.
    """

    # ── Build temporary root ──────────────────────────────────────────────────
    temp_root = bpy.data.objects.new("_TempStack_Root", None)
    work_col.objects.link(temp_root)
    temp_root.location = (0.0, 0.0, 0.0)

    # Disable the update callback while we set properties to avoid partial rebuilds.
    temp_root.shipping_container.is_container = False

    src = source_root.shipping_container
    tp  = temp_root.shipping_container

    tp.container_size   = src.container_size
    tp.detail_level     = 'HIGH'
    tp.door_open_angle  = 0.0
    tp.show_front_panel = vis_flags['show_front_panel']
    tp.show_left_door   = vis_flags['show_left_door']
    tp.show_right_door  = vis_flags['show_right_door']
    tp.show_back_panel  = vis_flags['show_back_panel']
    tp.show_left_panel  = vis_flags['show_left_panel']
    tp.show_right_panel = vis_flags['show_right_panel']
    tp.show_floor       = vis_flags['show_floor']
    tp.show_roof        = vis_flags['show_roof']

    temp_root["container_seed"] = seed

    # Single rebuild with all properties in their final state.
    temp_root.shipping_container.is_container = True
    rebuild_container(temp_root, context=context)

    # ── Collect visible mesh / font children (recursive) ─────────────────────
    def _collect(obj):
        result = []
        for child in obj.children:
            if child.type in ('MESH', 'FONT'):
                result.append(child)
            result.extend(_collect(child))
        return result

    to_bake = _collect(temp_root)

    if not to_bake:
        clear_container_children(temp_root)
        bpy.data.objects.remove(temp_root, do_unlink=True)
        return None

    # ── Duplicate → Convert → Join ────────────────────────────────────────────
    bpy.ops.object.select_all(action='DESELECT')
    for obj in to_bake:
        obj.select_set(True)

    context.view_layer.objects.active = to_bake[0]
    bpy.ops.object.duplicate(linked=False)
    dups = list(context.selected_objects)   # snapshot before selection changes

    if not dups:
        clear_container_children(temp_root)
        bpy.data.objects.remove(temp_root, do_unlink=True)
        return None

    context.view_layer.objects.active = dups[0]
    bpy.ops.object.convert(target='MESH')   # apply modifiers / curves → mesh

    if len(dups) > 1:
        bpy.ops.object.join()               # single mesh, active = joined result

    baked = context.active_object

    # ── BUG 2 FIX: normalise origin before unparenting ────────────────────────
    # parent_clear(CLEAR_KEEP_TRANSFORM) leaves baked.location equal to whatever
    # world offset the first duplicate had, which is a random child mesh deep
    # inside the hierarchy.  Collapse all transforms into vertex data first so
    # the returned object has origin (0,0,0) and geometry in container-local space.
    bpy.ops.object.parent_clear(type='CLEAR_KEEP_TRANSFORM')
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)

    # ── Clean up temporary root and its children ─────────────────────────────
    bpy.ops.object.select_all(action='DESELECT')
    clear_container_children(temp_root)
    bpy.data.objects.remove(temp_root, do_unlink=True)

    return baked


# ─────────────────────────────────────────────────────────────────────────────
# Gap-filler planes
# ─────────────────────────────────────────────────────────────────────────────

def _add_gap_fillers(parent_obj, stack_col, sw, sd, sh, W, L, H, presence_map):
    """Insert thin planes to cover structural gaps at corner-casting junctions
    on the outer perimeter of the stack.

    All fillers are parented to parent_obj (the concrete base slab) so they
    move with the whole assembly as a single unit.

    BUG 3 FIX: Previously fillers were placed at y=cy (≈0.089 m inside the stack
    front face) and x=cx (≈0.081 m inside the left face), burying them inside the
    casting block geometry.  They are now flush with the true outer face of the
    stack (y=0, y=sd·L, x=0, x=sw·W) with only a sub-millimetre epsilon inset to
    prevent Z-fighting.

    BUG 4 NOTE: Only outer-perimeter junction rows/columns are covered, which is
    correct for solid fully-populated stacks.  Interior gap coverage for sparse
    stacks is left as a future extension.
    """
    # ISO casting / rail dimensions — must stay in sync with rebuild.py
    cw, cl, ch = 0.162, 0.178, 0.118
    pw = 0.0975
    cz = ch / 2
    rh = 0.0975

    # Vertical span of the visible corrugated panel (same formula as rebuild.py)
    panel_h_start = cz + rh / 2
    panel_h_end   = H - cz - rh / 2
    panel_h       = panel_h_end - panel_h_start

    # Gap widths bridged at each junction
    gap_x = cw + pw          # ≈ 0.260 m
    gap_y = cl + pw          # ≈ 0.275 m

    # BUG 3 FIX: flush with the outer face, epsilon prevents Z-fighting only
    epsilon = 0.0005          # 0.5 mm

    def _make_filler(fname, width, height, loc, rot):
        verts = []
        faces = []
        append_plane_xy(verts, faces, center=(0.0, 0.0, 0.0), size=(width, height))
        obj = create_mesh_object(
            fname,
            verts,
            faces,
            location=loc,
            rotation=rot,
            tag_container_part=False,
            extra_props={"is_stack_filler": True},
        )
        stack_col.objects.link(obj)
        obj.parent = parent_obj          # child of concrete base
        return obj

    # ── X-Junctions: visible on the Front (j=0) and Back (j=sd-1) faces ──────
    for xi in range(1, sw):
        x_jct = xi * W

        for j_idx in [0, sd - 1]:
            for k in range(sh):
                neighbor = (presence_map.get((xi,   j_idx, k)) or
                            presence_map.get((xi-1, j_idx, k)))
                if not neighbor:
                    continue

                z_c = k * H + panel_h_start + panel_h / 2

                if j_idx == 0:
                    y_pos = epsilon          # flush with front outer face
                    rot_z = 0.0
                else:
                    y_pos = sd * L - epsilon # flush with back outer face
                    rot_z = math.pi

                name = f"GapFill_{'Front' if j_idx == 0 else 'Back'}_X{xi}_K{k}"
                obj  = _make_filler(
                    name, gap_x, panel_h,
                    (x_jct, y_pos, z_c),
                    (math.radians(90), 0.0, rot_z),
                )
                if neighbor.data.materials:
                    obj.data.materials.append(neighbor.data.materials[0])

    # ── Y-Junctions: visible on the Left (i=0) and Right (i=sw-1) faces ──────
    for yj in range(1, sd):
        y_jct = yj * L

        for i_idx in [0, sw - 1]:
            for k in range(sh):
                neighbor = (presence_map.get((i_idx, yj,   k)) or
                            presence_map.get((i_idx, yj-1, k)))
                if not neighbor:
                    continue

                z_c = k * H + panel_h_start + panel_h / 2

                if i_idx == 0:
                    x_pos = epsilon          # flush with left outer face
                    rot_z = math.radians(-90)
                else:
                    x_pos = sw * W - epsilon # flush with right outer face
                    rot_z = math.radians(90)

                name = f"GapFill_{'Left' if i_idx == 0 else 'Right'}_Y{yj}_K{k}"
                obj  = _make_filler(
                    name, gap_y, panel_h,
                    (x_pos, y_jct, z_c),
                    (math.radians(90), 0.0, rot_z),
                )
                if neighbor.data.materials:
                    obj.data.materials.append(neighbor.data.materials[0])


# ─────────────────────────────────────────────────────────────────────────────
# Public entry point
# ─────────────────────────────────────────────────────────────────────────────

def create_container_stack(root_obj, context=None):
    """Generate a grid of baked containers (sw × sd × sh) on a concrete base slab.

    Outliner hierarchy produced
    ───────────────────────────
    Stack_<SIZE>_<W>x<D>x<H>  (collection)
     └─ Stack_<SIZE>_<W>x<D>x<H>_Base   ← concrete slab, IS the root object
         ├─ Container_0_0_0
         ├─ Container_0_0_1
         ├─ …
         └─ GapFill_*  (only when sw>1 or sd>1)

    Concrete base dimensions
    ────────────────────────
        X = sw·W + 2·BASE_MARGIN   (BASE_MARGIN = 2.0 m)
        Y = sd·L + 2·BASE_MARGIN
        Z = BASE_THICKNESS         (BASE_THICKNESS = 0.3 m, top flush with z=0)

    Required properties on root_obj.shipping_container  (see patch block below)
    ────────────────────────────────────────────────────────────────────────────
        stack_width          IntProperty  default=2
        stack_depth          IntProperty  default=2
        stack_height         IntProperty  default=2
        stack_seed           IntProperty  default=42
        stack_random_orient  BoolProperty default=True

    Returns
    ───────
        (stack_collection, status_message)
    """
    if not root_obj or not root_obj.shipping_container.is_container:
        return None, "No valid container root found."

    ctx   = context or bpy.context
    props = root_obj.shipping_container

    if props.detail_level == 'LOW':
        return None, "Set source container to High detail before baking a stack."

    size_data = CONTAINER_SIZES[props.container_size]
    W = size_data['width']
    L = size_data['length']
    H = size_data['height']

    # BUG 1 FIX: guard against the stack properties being absent from properties.py
    try:
        sw                  = props.stack_width
        sd                  = props.stack_depth
        sh                  = props.stack_height
        stack_seed          = props.stack_seed
        stack_random_orient = props.stack_random_orient
    except AttributeError as exc:
        return None, (
            f"Missing stack property: {exc}.  "
            "Add stack_width / stack_depth / stack_height / stack_seed / "
            "stack_random_orient to ShippingContainerProperties in properties.py."
        )

    rng = random.Random(stack_seed)

    # ── Collections ──────────────────────────────────────────────────────────
    parent_col = (root_obj.users_collection[0]
                  if root_obj.users_collection
                  else ctx.scene.collection)

    stack_name = f"Stack_{props.container_size}_{sw}x{sd}x{sh}"
    stack_col  = bpy.data.collections.new(stack_name)
    parent_col.children.link(stack_col)

    # ── Concrete base — built FIRST so it can be the parent for everything ───
    #
    # Geometry spans:
    #   X : -BASE_MARGIN  …  sw·W + BASE_MARGIN
    #   Y : -BASE_MARGIN  …  sd·L + BASE_MARGIN
    #   Z : -BASE_THICKNESS  …  0              ← top flush with ground
    #
    # Origin is at (0, 0, 0) — the front-left-bottom corner of the stack —
    # so container slot offsets (i·W, j·L, k·H) map directly to local space.
    base_obj = _create_concrete_base(
        name      = f"{stack_name}_Base",
        stack_x   = sw * W,
        stack_y   = sd * L,
        margin    = BASE_MARGIN,
        thickness = BASE_THICKNESS,
    )
    base_obj.data.materials.append(_get_or_create_concrete_material())
    stack_col.objects.link(base_obj)
    # base_obj has no parent — it is the root of the entire stack assembly.

    # ── Temporary working collection — always removed in finally ─────────────
    work_col = bpy.data.collections.new("_StackWork_Temp")
    ctx.scene.collection.children.link(work_col)

    presence_map = {}   # (i, j, k) → baked mesh object
    baked_count  = 0

    try:
        for i in range(sw):
            for j in range(sd):
                for k in range(sh):
                    front_facing = (True if not stack_random_orient
                                    else rng.choice([True, False]))
                    seed = rng.random() * 0.999 + 0.001

                    vis   = _get_visible_faces(i, j, k, sw, sd, sh, front_facing)
                    baked = _bake_temp_container(root_obj, vis, seed, ctx, work_col)

                    if baked is None:
                        continue

                    # BUG 2 FIX: _bake_temp_container guarantees origin=(0,0,0)
                    # and geometry in container-local space, so the slot offset
                    # here lands the mesh exactly in the right grid cell.
                    if front_facing:
                        baked.location       = (i * W, j * L, k * H)
                        baked.rotation_euler = (0.0, 0.0, 0.0)
                    else:
                        # 180° around Z: place front-left-bottom at (i+1)·W, (j+1)·L
                        baked.location       = ((i + 1) * W, (j + 1) * L, k * H)
                        baked.rotation_euler = (0.0, 0.0, math.pi)

                    baked.name   = f"Container_{i}_{j}_{k}"
                    baked.parent = base_obj   # ← parented to the concrete slab

                    # Move from work collection to permanent stack collection
                    for col in list(baked.users_collection):
                        col.objects.unlink(baked)
                    stack_col.objects.link(baked)

                    presence_map[(i, j, k)] = baked
                    baked_count += 1

        # Gap fillers — also parented to base_obj so the whole assembly is atomic
        if sw > 1 or sd > 1:
            _add_gap_fillers(base_obj, stack_col, sw, sd, sh, W, L, H, presence_map)

    finally:
        # Always clean up the work collection even if an exception was raised.
        if work_col.name in bpy.data.collections:
            bpy.data.collections.remove(work_col, do_unlink=True)

    skipped = (sw * sd * sh) - baked_count
    msg = f"Created {baked_count} container(s) on '{base_obj.name}'"
    if skipped:
        msg += f" ({skipped} skipped — no visible faces)"
    msg += "."
    return stack_col, msg
