import bpy
import math
import random
from ..utils import CONTAINER_SIZES, clear_container_children
from ..geometry.frame import create_box
from ..geometry.corrugation import create_corrugated_panel
from ..geometry.doors import (
    create_door_panel,
    create_door_hinges,
    create_locking_hardware,
    get_hinge_positions,
    get_corrugation_gap_centers,
    HINGE_H,
)
from ..geometry.castings import create_corner_casting_instance
from ..geometry.roof import create_roof_bows
from ..geometry.floor import (
    create_floor_cross_members,
    create_wooden_floor,
    create_forklift_pocket_tubes,
    create_side_rail_with_forklift_pockets,
)
from ..geometry.decals import (
    generate_container_id,
    create_text_decal,
    create_logo_text,
    create_logo_plane,
    get_company_for_seed,
)
from ..geometry.proxy import create_proxy_box
from .materials import (
    get_or_create_container_material,
    get_or_create_container_material_double_sided,
    get_or_create_wood_material,
    get_or_create_decal_material,
    get_or_create_hardware_material,
    get_or_create_proxy_material,
    get_or_create_brand_material,
)


def update_container_materials(root_obj):
    """Re-assign materials on an existing container (no geometry rebuild)."""
    if not root_obj or not hasattr(root_obj, "shipping_container"):
        return
    if not root_obj.shipping_container.is_container:
        return

    props = root_obj.shipping_container
    if props.detail_level == 'LOW':
        # Proxy uses a different material pipeline.
        return

    if getattr(props, "shader_material_mode", 'SINGLE') == 'DOUBLE':
        metal_mat = get_or_create_container_material_double_sided()
    else:
        metal_mat = get_or_create_container_material()

    wood_mat = get_or_create_wood_material()
    decal_mat = get_or_create_decal_material()
    hardware_mat = get_or_create_hardware_material()

    for obj in root_obj.children_recursive:
        if obj.type == 'MESH':
            if obj.get("is_hardware"):
                mat = hardware_mat
            elif obj.get("is_logo_decal"):
                mat = metal_mat
            elif "Wood" in obj.name:
                mat = wood_mat
            else:
                mat = metal_mat

            if obj.data.materials:
                obj.data.materials[0] = mat
            else:
                obj.data.materials.append(mat)

        elif obj.type == 'FONT':
            if obj.get("is_logo_decal"):
                pass
            elif obj.data.materials:
                obj.data.materials[0] = decal_mat
            else:
                obj.data.materials.append(decal_mat)


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
    """Update door pivot rotations in-place (fast path for door animation).

    Returns True if the update succeeded or wasn't needed, False if a full
    rebuild is required.
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
def rebuild_container(root_obj, context=None):
    """Rebuild the container geometry from scratch based on current properties."""
    if not root_obj or not root_obj.shipping_container.is_container:
        return

    # Assign a stable random seed to this container instance
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

    # ── VISIBILITY CONDITIONS ─────────────────────────────────────────────────
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

    # ── POSTS ─────────────────────────────────────────────────────────────────
    created_posts = {}

    def _clamp(v, lo, hi):
        return max(lo, min(hi, v))

    def _create_front_post_assembly(name, hinge_axis_x, hinge_axis_y, hinge_centers_world_z):
        """Front post replacement: plate + rib segments with hinge gaps."""
        assembly = bpy.data.objects.new(name, None)
        assembly.empty_display_type = 'PLAIN_AXES'
        assembly.empty_display_size = 0.4
        assembly["is_container_part"] = True
        col.objects.link(assembly)
        assembly.parent = root_obj

        # Reinforcement rib running along the plate (Z), except where hinges are.
        # NOTE: User requested "0.45 by 0.45" — interpreted as 0.045 m (45 mm).
        rib_x = 0.045
        rib_y = 0.045

        # Ribs: align XY-centre to hinge pivot axis.
        rib_cx = hinge_axis_x
        rib_cy = hinge_axis_y

        # Plate: 0.1 m wide in X, spans in Y from rib back-face to the side-panel edge.
        plate_x = 0.100
        post_max_y = cy + (pw * 0.5)  # where the side-panel starts (front edge)
        plate_min_y = rib_cy + (rib_y * 0.5)
        plate_max_y = post_max_y
        if plate_max_y < plate_min_y:
            plate_min_y, plate_max_y = plate_max_y, plate_min_y

        plate_y = max(0.001, plate_max_y - plate_min_y)
        plate_cx = _clamp(hinge_axis_x + 0.027, plate_x * 0.5, W - plate_x * 0.5)
        plate_cy = _clamp((plate_min_y + plate_max_y) * 0.5, plate_y * 0.5, L - plate_y * 0.5)

        plate = create_box(f"{name}_Plate", plate_x, plate_y, post_h, (plate_cx, plate_cy, H / 2))
        col.objects.link(plate)
        plate.parent = assembly

        z0 = ch
        z1 = H - ch

        gap_half = (HINGE_H * 0.5) + 0.006
        gaps = []
        for zc in hinge_centers_world_z:
            gs = max(z0, zc - gap_half)
            ge = min(z1, zc + gap_half)
            if ge > gs:
                gaps.append((gs, ge))
        gaps.sort()

        # Merge overlapping gaps
        merged = []
        for gs, ge in gaps:
            if not merged or gs > merged[-1][1]:
                merged.append([gs, ge])
            else:
                merged[-1][1] = max(merged[-1][1], ge)

        def _add_segment(zs, ze, idx):
            seg_h = ze - zs
            if seg_h <= 0.005:
                return
            seg_cz = (zs + ze) * 0.5
            seg = create_box(f"{name}_Rib_{idx:02d}", rib_x, rib_y, seg_h, (rib_cx, rib_cy, seg_cz))
            col.objects.link(seg)
            seg.parent = assembly

        cur = z0
        seg_i = 0
        for gs, ge in merged:
            if gs > cur:
                _add_segment(cur, gs, seg_i)
                seg_i += 1
            cur = max(cur, ge)
        if cur < z1:
            _add_segment(cur, z1, seg_i)

        return assembly

    # Back posts remain as a single box for now
    for name, loc in [
        ("Back_Left_Post",   (cx,     L - cy, H / 2)),
        ("Back_Right_Post",  (W - cx, L - cy, H / 2)),
    ]:
        if post_conditions.get(name, lambda: False)():
            post = create_box(name, pw, pw, post_h, loc)
            col.objects.link(post)
            post.parent = root_obj
            created_posts[name] = post

    # ── HINGE RECESSES in front posts ────────────────────────────────────────
    panel_w = W - (2 * cx) - pw
    panel_l = L - (2 * cy) - pw
    panel_h = H - (2 * cz) - rh

    door_floor_z = cz + rh / 2

    hinge_off_y = 0.027
    hinge_off_x = 0.077

    hinge_z_world = []
    if props.show_front_panel:
        # Distribute hinges with a 0.05 m margin from the *casting clearance*
        # (between castings), then translate into door-local/world space.
        hinge_span_h = post_h  # z extent between castings: [ch, H-ch]
        hinge_span_z = get_hinge_positions(hinge_span_h, hinge_count=props.door_hinge_count)
        hinge_z_local = [(ch - door_floor_z) + z for z in hinge_span_z]
        hinge_z_world = [ch + z for z in hinge_span_z]

    if post_conditions.get("Front_Left_Post", lambda: False)():
        fl_axis_x = (cx + pw / 2) - hinge_off_x
        fl_axis_y = cy - hinge_off_y
        created_posts["Front_Left_Post"] = _create_front_post_assembly(
            "Front_Left_Post", fl_axis_x, fl_axis_y, hinge_z_world)

    if post_conditions.get("Front_Right_Post", lambda: False)():
        fr_axis_x = (W - cx - pw / 2) + hinge_off_x
        fr_axis_y = cy - hinge_off_y
        created_posts["Front_Right_Post"] = _create_front_post_assembly(
            "Front_Right_Post", fr_axis_x, fr_axis_y, hinge_z_world)

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
        if not side_rail_conditions.get(name, lambda: False)():
            continue

        if "Bottom" in name:
            rail = create_side_rail_with_forklift_pockets(
                name,
                pw,
                side_rail_len,
                rh,
                loc,
                context=context,
            )
        else:
            rail = create_box(name, pw, side_rail_len, rh, loc)

        col.objects.link(rail)
        rail.parent = root_obj

    # ── FRONT PANEL / DOORS ───────────────────────────────────────────────────
    if props.show_front_panel:
        door_w      = panel_w / 2
        door_h      = panel_h
        floor_z_off = cz + rh / 2
        n_corr      = props.door_corrugations

        # Z-centres of flat door background sections — for hardware and decal snapping.
        # FRAME_T = 0.150 m (top/bottom rail height from doors.py).
        _door_frame_t = 0.150
        gap_zs = get_corrugation_gap_centers(
            _door_frame_t, door_h - 2 * _door_frame_t, n_corr)

        # Shared company info (same seed → same company on both doors)
        company   = get_company_for_seed(container_seed)
        brand_mat = get_or_create_brand_material(company["name"], company["color"])

        if props.show_left_door:
            left_pivot = bpy.data.objects.new("Left_Door_Pivot", None)
            left_pivot.empty_display_type  = 'ARROWS'
            left_pivot.empty_display_size  = 0.3
            left_pivot.location            = ((cx + pw / 2) - hinge_off_x, cy - hinge_off_y, floor_z_off)
            left_pivot.rotation_euler      = (0.0, 0.0, -props.door_open_angle)
            col.objects.link(left_pivot)
            left_pivot.parent = root_obj
            left_pivot["is_container_part"] = True

            # Offset ONLY the door geometry/hardware back into the opening so
            # both doors still close correctly, while keeping the hinge axis
            # aligned to the post corner.
            left_door_geo = bpy.data.objects.new("Left_Door_Geo", None)
            left_door_geo.empty_display_type = 'PLAIN_AXES'
            left_door_geo.empty_display_size = 0.2
            left_door_geo.location = (hinge_off_x, hinge_off_y, 0.0)
            col.objects.link(left_door_geo)
            left_door_geo.parent = left_pivot
            left_door_geo["is_container_part"] = True

            # Door panel
            lp = create_door_panel("Left_Panel", door_w, door_h, True,
                                   num_corrugations=n_corr)
            col.objects.link(lp)
            lp.parent = left_door_geo

            # Hinges
            lh = create_door_hinges(
                "Left_Hinges", door_w, door_h, True, hinge_count=props.door_hinge_count)
            col.objects.link(lh)
            lh.parent = left_pivot
            for child in lh.children:
                if not child.users_collection:
                    col.objects.link(child)

            # Override hinge Z positions so distribution respects the casting clearance margin.
            if hinge_z_local:
                for idx, inst in enumerate(sorted(lh.children, key=lambda o: o.name)):
                    if idx >= len(hinge_z_local):
                        break
                    inst.location.z = hinge_z_local[idx]

            # Locking hardware — brackets snapped to gap centres
            hw = create_locking_hardware(
                "Left_Hardware", door_w, door_h, True, floor_z_off,
                num_corrugations=n_corr)
            col.objects.link(hw)
            hw.parent = left_door_geo

            # ── Logo decal on left door ───────────────────────────────────────
            # Place in the first gap centre above the door midpoint, centred in X.
            sorted_gaps = sorted(gap_zs)
            above_mid   = [z for z in sorted_gaps if z > door_h * 0.5]
            logo_z      = above_mid[0] if above_mid else (sorted_gaps[-1] if sorted_gaps else door_h * 0.75)
            cx_left     = door_w * 0.5   # horizontal centre of left door panel
            logo_pw     = max(0.20, door_w - 2 * 0.150 - 0.04)
            logo_ph     = 0.22

            logo_plane = create_logo_plane("Left_Logo_Plane", logo_pw, logo_ph)
            logo_plane.location = (cx_left, -0.001, logo_z)
            col.objects.link(logo_plane)
            logo_plane.parent = left_door_geo
            # Plane uses the container metal shader so it blends with the door.
            logo_plane.data.materials.append(get_or_create_container_material())

            logo_text = create_logo_text("Left_Logo_Text", company["name"], size=0.14)
            logo_text.location       = (cx_left, -0.003, logo_z)
            logo_text.rotation_euler = (math.radians(90), 0, 0)
            col.objects.link(logo_text)
            logo_text.parent = left_door_geo
            # Text is coloured with the company brand colour.
            logo_text.data.materials.append(brand_mat)

        if props.show_right_door:
            right_pivot = bpy.data.objects.new("Right_Door_Pivot", None)
            right_pivot.empty_display_type  = 'ARROWS'
            right_pivot.empty_display_size  = 0.3
            right_pivot.location            = ((W - cx - pw / 2) + hinge_off_x, cy - hinge_off_y, floor_z_off)
            right_pivot.rotation_euler      = (0.0, 0.0, props.door_open_angle)
            col.objects.link(right_pivot)
            right_pivot.parent = root_obj
            right_pivot["is_container_part"] = True

            right_door_geo = bpy.data.objects.new("Right_Door_Geo", None)
            right_door_geo.empty_display_type = 'PLAIN_AXES'
            right_door_geo.empty_display_size = 0.2
            right_door_geo.location = (-hinge_off_x, hinge_off_y, 0.0)
            col.objects.link(right_door_geo)
            right_door_geo.parent = right_pivot
            right_door_geo["is_container_part"] = True

            # Door panel
            rp = create_door_panel("Right_Panel", door_w, door_h, False,
                                   num_corrugations=n_corr)
            col.objects.link(rp)
            rp.parent = right_door_geo

            # Hinges
            rh_obj = create_door_hinges(
                "Right_Hinges", door_w, door_h, False, hinge_count=props.door_hinge_count)
            col.objects.link(rh_obj)
            rh_obj.parent = right_pivot
            for child in rh_obj.children:
                if not child.users_collection:
                    col.objects.link(child)

            # Override hinge Z positions so distribution respects the casting clearance margin.
            if hinge_z_local:
                for idx, inst in enumerate(sorted(rh_obj.children, key=lambda o: o.name)):
                    if idx >= len(hinge_z_local):
                        break
                    inst.location.z = hinge_z_local[idx]

            # Locking hardware — brackets snapped to gap centres
            hw = create_locking_hardware(
                "Right_Hardware", door_w, door_h, False, floor_z_off,
                num_corrugations=n_corr)
            col.objects.link(hw)
            hw.parent = right_door_geo

            # ── Decals on the right door — flush (Y = −0.001), centred in X ────
            # sorted_gaps is shared from the left-door block above.
            cx_right = -door_w * 0.5   # horizontal centre of right door panel

            # Decal_Specs: first gap above midpoint, centred
            specs_z    = above_mid[0] if above_mid else (sorted_gaps[-1] if sorted_gaps else door_h * 0.55)
            specs_text = (
                "MAX GROSS  30,480 KG\n"
                "TARE       2,200 KG\n"
                "NET        28,280 KG\n"
                "CU. CAP.   33.2 CU.M"
            )
            decal_specs = create_text_decal(
                "Decal_Specs", specs_text, size=0.06, align_x='CENTER', align_y='CENTER')
            decal_specs.location       = (cx_right, -0.001, specs_z)
            decal_specs.rotation_euler = (math.radians(90), 0, 0)
            col.objects.link(decal_specs)
            decal_specs.parent = right_door_geo

            # Decal_ID: next gap up from Decal_Specs, centred
            specs_idx = sorted_gaps.index(specs_z) if specs_z in sorted_gaps else -1
            id_z = (sorted_gaps[specs_idx + 1]
                    if specs_idx >= 0 and specs_idx + 1 < len(sorted_gaps)
                    else specs_z + 0.200)
            decal_id = create_text_decal(
                "Decal_ID", container_id, size=0.12, align_x='CENTER', align_y='CENTER')
            decal_id.location       = (cx_right, -0.001, id_z)
            decal_id.rotation_euler = (math.radians(90), 0, 0)
            col.objects.link(decal_id)
            decal_id.parent = right_door_geo

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
            "Roof_Panel", panel_l, panel_w,
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
    if getattr(props, "shader_material_mode", 'SINGLE') == 'DOUBLE':
        metal_mat = get_or_create_container_material_double_sided()
    else:
        metal_mat = get_or_create_container_material()
    wood_mat     = get_or_create_wood_material()
    decal_mat    = get_or_create_decal_material()
    hardware_mat = get_or_create_hardware_material()

    for obj in root_obj.children_recursive:
        if obj.type == 'MESH':
            obj["container_seed"] = container_seed

            # Shader control values — read by ShaderNodeAttribute (OBJECT) in
            # the v5 ISO_Container_Metal shader.  Stamped here so every mesh
            # child reflects the root's current shader settings at build time.
            obj["shader_rust_strength"]      = props.shader_rust_strength
            obj["shader_stain_intensity"]    = props.shader_stain_intensity
            obj["shader_dust_intensity"]     = props.shader_dust_intensity
            obj["shader_scratch_intensity"]  = props.shader_scratch_intensity
            obj["shader_color_override_amt"] = props.shader_color_override_amount
            obj["shader_color_override"]     = list(props.shader_color_override)
            obj["shader_inside_color"]       = list(getattr(props, "shader_inside_color", (0.62, 0.62, 0.62, 1.0)))
            obj["shader_inside_roughness"]   = float(getattr(props, "shader_inside_roughness", 0.75))
            obj["shader_inside_metallic"]    = float(getattr(props, "shader_inside_metallic", 0.0))

            if obj.get("is_hardware"):
                mat = hardware_mat
            elif obj.get("is_logo_decal"):
                # Logo backing plane — use the same metal shader as the rest of
                # the container so it blends in colour and weathering.
                # Shader attribute props must be stamped so the v5 shader works.
                obj["container_seed"]            = container_seed
                obj["shader_rust_strength"]      = props.shader_rust_strength
                obj["shader_stain_intensity"]    = props.shader_stain_intensity
                obj["shader_dust_intensity"]     = props.shader_dust_intensity
                obj["shader_scratch_intensity"]  = props.shader_scratch_intensity
                obj["shader_color_override_amt"] = props.shader_color_override_amount
                obj["shader_color_override"]     = list(props.shader_color_override)
                obj["shader_inside_color"]       = list(getattr(props, "shader_inside_color", (0.62, 0.62, 0.62, 1.0)))
                obj["shader_inside_roughness"]   = float(getattr(props, "shader_inside_roughness", 0.75))
                obj["shader_inside_metallic"]    = float(getattr(props, "shader_inside_metallic", 0.0))
                mat = metal_mat
            elif "Wood" in obj.name:
                mat = wood_mat
            else:
                mat = metal_mat

            if obj.data.materials:
                obj.data.materials[0] = mat
            else:
                obj.data.materials.append(mat)

        elif obj.type == 'FONT':
            if obj.get("is_logo_decal"):
                # Logo text already has brand_mat assigned at creation — keep it.
                pass
            elif obj.data.materials:
                obj.data.materials[0] = decal_mat
            else:
                obj.data.materials.append(decal_mat)
