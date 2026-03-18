import bpy
import bmesh
import math
import random
from ..utils import CONTAINER_SIZES, clear_container_children, remove_object_and_orphan_data
from ..geometry.panels import create_plane
from ..geometry.frame import create_box
from ..geometry.corrugation import create_corrugated_panel
from ..geometry.doors import (
    create_door_panel,
    create_door_hinges,
    create_locking_hardware,
    get_hinge_positions,
    HINGE_H,
)
from ..geometry.castings import create_corner_casting_instance
from ..geometry.roof import create_roof_bows
from ..geometry.floor import (
    create_floor_cross_members,
    create_wooden_floor,
    create_forklift_pocket_cutters,
    create_forklift_pocket_tubes,
)
from ..geometry.decals import generate_container_id, create_text_decal
from ..geometry.proxy import create_proxy_box
from .materials import (
    get_or_create_container_material,
    get_or_create_wood_material,
    get_or_create_decal_material,
    get_or_create_hardware_material,
    get_or_create_proxy_material,
)


def _get_collection_for_root(root_obj, context=None):
    if root_obj.users_collection:
        return root_obj.users_collection[0]
    if context is not None:
        if getattr(context, "collection", None) is not None:
            return context.collection
        if getattr(context, "scene", None) is not None:
            return context.scene.collection
    return bpy.context.scene.collection


def _get_depsgraph(context=None):
    if context is not None and hasattr(context, "evaluated_depsgraph_get"):
        return context.evaluated_depsgraph_get()
    return bpy.context.evaluated_depsgraph_get()


def update_door_pivots(root_obj):
    """Update door pivot rotations in-place for fast animation updates.

    Returns True if the update succeeded or wasn't needed, False if a rebuild is
    recommended.
    """
    if not root_obj or not hasattr(root_obj, "shipping_container"):
        return False
    if not root_obj.shipping_container.is_container:
        return False

    props = root_obj.shipping_container
    if props.detail_level == 'LOW':
        return True
    if not props.show_front_panel:
        return True

    angle = props.door_open_angle
    updated_any = False

    for child in root_obj.children:
        if child.type != 'EMPTY':
            continue
        if child.name.startswith("Left_Door_Pivot"):
            child.rotation_euler = (0.0, 0.0, -angle)
            updated_any = True
        elif child.name.startswith("Right_Door_Pivot"):
            child.rotation_euler = (0.0, 0.0, angle)
            updated_any = True

    if (props.show_left_door or props.show_right_door) and not updated_any:
        return False
    return True


# ─────────────────────────────────────────────────────────────────────────────
def _apply_hinge_recesses(post_obj, col, hinge_z_positions_world,
                          pivot_x_world, post_cy_world, x_sign,
                          context=None):
    """Boolean-cut rectangular slots into a front post to accept the hinge leaves.

    post_obj               – the post mesh object (already linked to collection)
    hinge_z_positions_world – list of world-Z values for the *bottom* of each hinge
    pivot_x_world          – world X of the hinge pivot axis (= door pivot X)
    post_cy_world          – world Y centre of the post
    x_sign                 – +1 if the recess opens toward +X (left post),
                             −1 if it opens toward −X (right post)
    """
    slot_depth  = 0.050          # 50 mm into the post face
    slot_y_ext  = 0.070          # slot extends this far in Y (wider than post for clean cut)
    slot_z      = HINGE_H + 0.004  # 4 mm clearance above/below hinge plate

    cutter_mesh = bpy.data.meshes.new("_HingeRecess_Cutter")
    cutter_obj  = bpy.data.objects.new("_HingeRecess_Cutter", cutter_mesh)
    cbm = bmesh.new()

    for hz_bot_world in hinge_z_positions_world:
        hz_ctr_world = hz_bot_world + slot_z * 0.5
        # The slot is centred on the pivot X, pushed slightly into the post face.
        slot_cx = pivot_x_world - x_sign * (slot_depth * 0.5)
        g = bmesh.ops.create_cube(cbm, size=1.0)
        bmesh.ops.scale(cbm,     verts=g['verts'], vec=(slot_depth + 0.002, slot_y_ext, slot_z))
        bmesh.ops.translate(cbm, verts=g['verts'], vec=(slot_cx, post_cy_world, hz_ctr_world))

    cbm.to_mesh(cutter_mesh)
    cbm.free()
    col.objects.link(cutter_obj)

    mod = post_obj.modifiers.new("HingeRecess", 'BOOLEAN')
    mod.object    = cutter_obj
    mod.operation = 'DIFFERENCE'
    mod.solver    = 'MANIFOLD'

    try:
        depsgraph = _get_depsgraph(context=context)
        eval_post = post_obj.evaluated_get(depsgraph)
        new_mesh  = bpy.data.meshes.new_from_object(eval_post)
        old_mesh  = post_obj.data
        post_obj.data = new_mesh
        bpy.data.meshes.remove(old_mesh)
        post_obj.modifiers.clear()
    finally:
        remove_object_and_orphan_data(cutter_obj)


# ─────────────────────────────────────────────────────────────────────────────
def rebuild_container(root_obj, context=None):
    """Rebuilds the container geometry based on current properties."""
    if not root_obj or not root_obj.shipping_container.is_container:
        return

    # Generate a random seed for this specific container if it doesn't have one
    if "container_seed" not in root_obj:
        root_obj["container_seed"] = (random.random() * 0.999) + 0.001
    container_seed = float(root_obj["container_seed"])
    if container_seed <= 0.0:
        container_seed = 0.001
        root_obj["container_seed"] = container_seed

    container_id = generate_container_id(container_seed)

    props     = root_obj.shipping_container
    size_data = CONTAINER_SIZES[props.container_size]

    L = size_data['length']
    W = size_data['width']
    H = size_data['height']

    clear_container_children(root_obj)
    col = _get_collection_for_root(root_obj, context=context)

    # ── LOW-DETAIL PROXY ──────────────────────────────────────────────────────
    if props.detail_level == 'LOW':
        proxy = create_proxy_box("Container_Proxy", W, L, H)
        col.objects.link(proxy)
        proxy.parent = root_obj

        proxy_mat = get_or_create_proxy_material()
        proxy["container_seed"] = container_seed
        if proxy.data.materials:
            proxy.data.materials[0] = proxy_mat
        else:
            proxy.data.materials.append(proxy_mat)
        return

    # ── FRAME DIMENSIONS ─────────────────────────────────────────────────────
    pw = 0.0975   # post / rail section width
    rh = 0.0975   # rail height

    # ISO 1161 casting dimensions
    cw = 0.162
    cl = 0.178
    ch = 0.118

    cx = cw / 2
    cy = cl / 2
    cz = ch / 2

    # ── CONDITIONS ───────────────────────────────────────────────────────────
    p = props
    casting_conditions = {
        "Casting_BLF": lambda: p.show_front_panel or p.show_left_panel  or p.show_floor,
        "Casting_BRF": lambda: p.show_front_panel or p.show_right_panel or p.show_floor,
        "Casting_BLB": lambda: p.show_back_panel  or p.show_left_panel  or p.show_floor,
        "Casting_BRB": lambda: p.show_back_panel  or p.show_right_panel or p.show_floor,
        "Casting_TLF": lambda: p.show_front_panel or p.show_left_panel  or p.show_roof,
        "Casting_TRF": lambda: p.show_front_panel or p.show_right_panel or p.show_roof,
        "Casting_TLB": lambda: p.show_back_panel  or p.show_left_panel  or p.show_roof,
        "Casting_TRB": lambda: p.show_back_panel  or p.show_right_panel or p.show_roof,
    }

    post_conditions = {
        "Front_Left_Post":  lambda: p.show_front_panel or p.show_left_panel,
        "Front_Right_Post": lambda: p.show_front_panel or p.show_right_panel,
        "Back_Left_Post":   lambda: p.show_back_panel  or p.show_left_panel,
        "Back_Right_Post":  lambda: p.show_back_panel  or p.show_right_panel,
    }

    fb_rail_conditions = {
        "Front_Bottom_Rail": lambda: p.show_front_panel or p.show_floor,
        "Front_Top_Rail":    lambda: p.show_front_panel or p.show_roof,
        "Back_Bottom_Rail":  lambda: p.show_back_panel  or p.show_floor,
        "Back_Top_Rail":     lambda: p.show_back_panel  or p.show_roof,
    }

    side_rail_conditions = {
        "Left_Bottom_Rail":  lambda: p.show_left_panel  or p.show_floor,
        "Left_Top_Rail":     lambda: p.show_left_panel  or p.show_roof,
        "Right_Bottom_Rail": lambda: p.show_right_panel or p.show_floor,
        "Right_Top_Rail":    lambda: p.show_right_panel or p.show_roof,
    }

    post_h = H - (2 * ch)

    # ── CORNER CASTINGS ───────────────────────────────────────────────────────
    castings = [
        ("Casting_BLF", (0, 0, 0), False, True,  True),
        ("Casting_BRF", (W, 0, 0), False, True,  False),
        ("Casting_BLB", (0, L, 0), False, False, True),
        ("Casting_BRB", (W, L, 0), False, False, False),
        ("Casting_TLF", (0, 0, H), True,  True,  True),
        ("Casting_TRF", (W, 0, H), True,  True,  False),
        ("Casting_TLB", (0, L, H), True,  False, True),
        ("Casting_TRB", (W, L, H), True,  False, False),
    ]

    for name, loc, is_top, is_front, is_left in castings:
        if casting_conditions.get(name, lambda: False)():
            casting = create_corner_casting_instance(
                name, loc, is_top, is_front, is_left, context=context)
            col.objects.link(casting)
            casting.parent = root_obj

    # ── POSTS (created first so we can boolean the front two) ─────────────────
    posts = [
        ("Front_Left_Post",  (cx,       cy,       H / 2)),
        ("Front_Right_Post", (W - cx,   cy,       H / 2)),
        ("Back_Left_Post",   (cx,       L - cy,   H / 2)),
        ("Back_Right_Post",  (W - cx,   L - cy,   H / 2)),
    ]

    created_posts = {}
    for name, loc in posts:
        if post_conditions.get(name, lambda: False)():
            post = create_box(name, pw, pw, post_h, loc)
            col.objects.link(post)
            post.parent = root_obj
            created_posts[name] = post

    # ── HINGE RECESSES in front posts ────────────────────────────────────────
    # Panel dimensions needed to compute door height (same formula used below).
    panel_w = W - (2 * cx) - pw
    panel_l = L - (2 * cy) - pw
    panel_h = H - (2 * cz) - rh

    # World-Z of the door bottom (= the door pivot's Z position in rebuild below).
    door_floor_z = cz + rh / 2

    if props.show_front_panel:
        door_h = panel_h
        # get_hinge_positions() returns door-local Z (bottom of each hinge).
        hinge_z_local = get_hinge_positions(door_h)
        # Convert to world Z.
        hinge_z_world = [door_floor_z + z for z in hinge_z_local]

        if props.show_left_door and "Front_Left_Post" in created_posts:
            _apply_hinge_recesses(
                post_obj             = created_posts["Front_Left_Post"],
                col                  = col,
                hinge_z_positions_world = hinge_z_world,
                pivot_x_world        = cx + pw / 2,   # X of the left hinge pivot
                post_cy_world        = cy,             # Y centre of front posts
                x_sign               = +1,             # recess opens toward +X face
                context              = context,
            )

        if props.show_right_door and "Front_Right_Post" in created_posts:
            _apply_hinge_recesses(
                post_obj             = created_posts["Front_Right_Post"],
                col                  = col,
                hinge_z_positions_world = hinge_z_world,
                pivot_x_world        = W - cx - pw / 2,  # X of the right hinge pivot
                post_cy_world        = cy,
                x_sign               = -1,               # recess opens toward -X face
                context              = context,
            )

    # ── FORKLIFT POCKET CUTTERS ───────────────────────────────────────────────
    any_side_bottom_rail = any(cond() for cond in [
        side_rail_conditions["Left_Bottom_Rail"],
        side_rail_conditions["Right_Bottom_Rail"],
    ])

    pocket_cutters = None
    if any_side_bottom_rail:
        pocket_cutters = create_forklift_pocket_cutters("Pocket_Cutters", W)
        col.objects.link(pocket_cutters)
        pocket_cutters.location = (W / 2, L / 2, cz)

    try:
        # ── FRONT / BACK RAILS ────────────────────────────────────────────────
        fb_rail_len = W - (2 * cw)
        fb_rails = [
            ("Front_Bottom_Rail", (W / 2, cy,     cz)),
            ("Front_Top_Rail",    (W / 2, cy,     H - cz)),
            ("Back_Bottom_Rail",  (W / 2, L - cy, cz)),
            ("Back_Top_Rail",     (W / 2, L - cy, H - cz)),
        ]

        for name, loc in fb_rails:
            if fb_rail_conditions.get(name, lambda: False)():
                rail = create_box(name, fb_rail_len, pw, rh, loc)
                col.objects.link(rail)
                rail.parent = root_obj

        # ── SIDE RAILS ────────────────────────────────────────────────────────
        side_rail_len = L - (2 * cl)
        side_rails = [
            ("Left_Bottom_Rail",  (cx,     L / 2, cz)),
            ("Left_Top_Rail",     (cx,     L / 2, H - cz)),
            ("Right_Bottom_Rail", (W - cx, L / 2, cz)),
            ("Right_Top_Rail",    (W - cx, L / 2, H - cz)),
        ]

        for name, loc in side_rails:
            if side_rail_conditions.get(name, lambda: False)():
                rail = create_box(name, pw, side_rail_len, rh, loc)
                col.objects.link(rail)
                rail.parent = root_obj

                if "Bottom" in name and pocket_cutters:
                    mod = rail.modifiers.new(name="Forklift_Hole", type='BOOLEAN')
                    mod.object    = pocket_cutters
                    mod.operation = 'DIFFERENCE'
                    mod.solver    = 'MANIFOLD'

                    depsgraph = _get_depsgraph(context=context)
                    eval_obj  = rail.evaluated_get(depsgraph)
                    new_mesh  = bpy.data.meshes.new_from_object(eval_obj)
                    old_mesh  = rail.data
                    rail.data = new_mesh
                    bpy.data.meshes.remove(old_mesh)
                    rail.modifiers.clear()

    finally:
        if pocket_cutters is not None:
            remove_object_and_orphan_data(pocket_cutters)
            pocket_cutters = None

    # ── FRONT PANEL / DOORS ───────────────────────────────────────────────────
    if props.show_front_panel:
        door_w      = panel_w / 2
        door_h      = panel_h
        floor_z_off = cz + rh / 2   # world-Z of door bottom = door-local Z origin

        if props.show_left_door:
            left_pivot = bpy.data.objects.new("Left_Door_Pivot", None)
            left_pivot.empty_display_type = 'ARROWS'
            left_pivot.empty_display_size = 0.3
            left_pivot.location      = (cx + pw / 2, cy, floor_z_off)
            left_pivot.rotation_euler = (0.0, 0.0, -props.door_open_angle)
            col.objects.link(left_pivot)
            left_pivot.parent = root_obj
            left_pivot["is_container_part"] = True

            for builder, suffix in [
                (create_door_panel,       "Panel"),
                (create_door_hinges,      "Hinges"),
            ]:
                obj = builder(f"Left_{suffix}", door_w, door_h, True)
                col.objects.link(obj)
                obj.parent = left_pivot

            hw = create_locking_hardware(
                "Left_Hardware", door_w, door_h, True, floor_z_off)
            col.objects.link(hw)
            hw.parent = left_pivot

        if props.show_right_door:
            right_pivot = bpy.data.objects.new("Right_Door_Pivot", None)
            right_pivot.empty_display_type = 'ARROWS'
            right_pivot.empty_display_size = 0.3
            right_pivot.location      = (W - cx - pw / 2, cy, floor_z_off)
            right_pivot.rotation_euler = (0.0, 0.0, props.door_open_angle)
            col.objects.link(right_pivot)
            right_pivot.parent = root_obj
            right_pivot["is_container_part"] = True

            for builder, suffix in [
                (create_door_panel,       "Panel"),
                (create_door_hinges,      "Hinges"),
            ]:
                obj = builder(f"Right_{suffix}", door_w, door_h, False)
                col.objects.link(obj)
                obj.parent = right_pivot

            hw = create_locking_hardware(
                "Right_Hardware", door_w, door_h, False, floor_z_off)
            col.objects.link(hw)
            hw.parent = right_pivot

            # ── Decals on the right door ──────────────────────────────────────
            decal_id = create_text_decal(
                "Decal_ID", container_id, size=0.12, align_x='RIGHT')
            decal_id.location      = (-0.1, -0.05, door_h - 0.3)
            decal_id.rotation_euler = (math.radians(90), 0, 0)
            col.objects.link(decal_id)
            decal_id.parent = right_pivot

            specs_text = (
                "MAX GROSS  30,480 KG\n"
                "TARE       2,200 KG\n"
                "NET        28,280 KG\n"
                "CU. CAP.   33.2 CU.M"
            )
            decal_specs = create_text_decal(
                "Decal_Specs", specs_text, size=0.06, align_x='LEFT')
            decal_specs.location      = (-door_w + 0.1, -0.05, door_h / 2)
            decal_specs.rotation_euler = (math.radians(90), 0, 0)
            col.objects.link(decal_specs)
            decal_specs.parent = right_pivot

    # ── BACK PANEL ────────────────────────────────────────────────────────────
    if props.show_back_panel:
        back = create_corrugated_panel(
            "Back_Assembly", panel_w, panel_h,
            (W / 2, L - cy, H / 2),
            (math.radians(90), 0, math.radians(180)),
        )
        col.objects.link(back)
        back.parent = root_obj

    # ── LEFT PANEL ────────────────────────────────────────────────────────────
    if props.show_left_panel:
        left = create_corrugated_panel(
            "Left_Side_Assembly", panel_l, panel_h,
            (cx, L / 2, H / 2),
            (math.radians(90), 0, math.radians(-90)),
        )
        col.objects.link(left)
        left.parent = root_obj

    # ── RIGHT PANEL ───────────────────────────────────────────────────────────
    if props.show_right_panel:
        right = create_corrugated_panel(
            "Right_Side_Assembly", panel_l, panel_h,
            (W - cx, L / 2, H / 2),
            (math.radians(90), 0, math.radians(90)),
        )
        col.objects.link(right)
        right.parent = root_obj

    # ── FLOOR ─────────────────────────────────────────────────────────────────
    if props.show_floor:
        floor_assembly = bpy.data.objects.new("Floor_Assembly", None)
        floor_assembly.empty_display_type = 'PLAIN_AXES'
        floor_assembly.empty_display_size = 0.5
        floor_z = cz + rh / 2
        floor_assembly.location = (W / 2, L / 2, floor_z)
        col.objects.link(floor_assembly)
        floor_assembly.parent = root_obj
        floor_assembly["is_container_part"] = True

        cross_members = create_floor_cross_members("Floor_Cross_Members", panel_w, panel_l)
        cross_members.location = (0, 0, -rh / 2)
        col.objects.link(cross_members)
        cross_members.parent = floor_assembly

        wood_floor = create_wooden_floor("Wooden_Floor", panel_w, panel_l)
        wood_floor.location = (0, 0, 0.014)
        col.objects.link(wood_floor)
        wood_floor.parent = floor_assembly

        pocket_tubes = create_forklift_pocket_tubes("Forklift_Pockets", panel_w)
        pocket_tubes.location = (0, 0, -rh / 2)
        col.objects.link(pocket_tubes)
        pocket_tubes.parent = floor_assembly

    # ── ROOF ──────────────────────────────────────────────────────────────────
    if props.show_roof:
        roof_assembly = bpy.data.objects.new("Roof_Assembly", None)
        roof_assembly.empty_display_type = 'PLAIN_AXES'
        roof_assembly.empty_display_size = 0.5
        roof_z = H - cz - rh / 2
        roof_assembly.location = (W / 2, L / 2, roof_z)
        col.objects.link(roof_assembly)
        roof_assembly.parent = root_obj
        roof_assembly["is_container_part"] = True

        roof_panel = create_corrugated_panel(
            "Roof_Panel",
            panel_l,
            panel_w,
            (0, 0, 0),
            (0, 0, math.radians(90)),
            profile="OFFICIAL_SIDE",
        )
        col.objects.link(roof_panel)
        roof_panel.parent = roof_assembly

        bows = create_roof_bows("Roof_Bows", panel_w, panel_l)
        bows.location = (0, 0, -0.024)
        col.objects.link(bows)
        bows.parent = roof_assembly

    # ── MATERIALS ─────────────────────────────────────────────────────────────
    metal_mat    = get_or_create_container_material()
    wood_mat     = get_or_create_wood_material()
    decal_mat    = get_or_create_decal_material()
    hardware_mat = get_or_create_hardware_material()

    for obj in root_obj.children_recursive:
        if obj.type == 'MESH':
            obj["container_seed"] = container_seed

            # Hardware objects (locking bars, cams, guides, handles …)
            if obj.get("is_hardware"):
                mat = hardware_mat
            elif "Wood" in obj.name:
                mat = wood_mat
            else:
                mat = metal_mat

            if obj.data.materials:
                obj.data.materials[0] = mat
            else:
                obj.data.materials.append(mat)

        elif obj.type == 'FONT':
            if obj.data.materials:
                obj.data.materials[0] = decal_mat
            else:
                obj.data.materials.append(decal_mat)
