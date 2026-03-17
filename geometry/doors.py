import bpy
import bmesh
import math
import mathutils


def create_door_component(name, comp_type, width, height, is_left):
    """Generates specific door components (Panel, Bars, Hinges, Handles) relative to the hinge pivot."""
    mesh = bpy.data.meshes.new(name)
    obj = bpy.data.objects.new(name, mesh)
    bm = bmesh.new()

    # Left door builds towards +X, Right door builds towards -X
    x_dir = 1 if is_left else -1

    if comp_type == 'PANEL':
        # Door leaf: framed door with an outer recessed panel and an inner flat panel skin.
        # Local axes for the door leaf:
        # - X: door width (hinge pivot at X=0)
        # - Z: door height
        # - Y: depth (outside is -Y, inside is +Y)

        def make_face(verts, reverse=False):
            try:
                bm.faces.new(tuple(reversed(verts)) if reverse else verts)
            except ValueError:
                pass

        # Tunable (meters).
        frame_w = 0.040
        mid_bar_h = 0.050
        recess = 0.020
        leaf_t = 0.040

        frame_w = min(frame_w, width * 0.25, height * 0.25)
        if frame_w <= 0.0:
            frame_w = min(width, height) * 0.05
        if frame_w <= 0.0:
            frame_w = 0.01
        leaf_t = max(0.002, min(leaf_t, 0.15))
        recess = max(0.0, min(recess, leaf_t * 0.9))

        inner_x0_u = frame_w
        inner_x1_u = max(inner_x0_u + 0.001, width - frame_w)
        inner_z0 = frame_w
        inner_z1 = max(inner_z0 + 0.001, height - frame_w)

        if (inner_x1_u - inner_x0_u) < 0.01 or (inner_z1 - inner_z0) < 0.01:
            v0 = bm.verts.new((0.0, 0.0, 0.0))
            v1 = bm.verts.new((width * x_dir, 0.0, 0.0))
            v2 = bm.verts.new((width * x_dir, 0.0, height))
            v3 = bm.verts.new((0.0, 0.0, height))
            make_face((v0, v1, v2, v3), reverse=False)
            if x_dir == -1 and bm.faces:
                bmesh.ops.reverse_faces(bm, faces=bm.faces)
        else:
            inner_h = (inner_z1 - inner_z0) - mid_bar_h
            if inner_h <= 0.02:
                mid_bar_h = 0.0
                z2 = inner_z1
                z3 = inner_z1
            else:
                panel_h = inner_h * 0.5
                z2 = inner_z0 + panel_h
                z3 = z2 + mid_bar_h

            v_cache = {}

            def v(u, y, z):
                x = u * x_dir
                key = (round(x, 6), round(y, 6), round(z, 6))
                vert = v_cache.get(key)
                if vert is None:
                    vert = bm.verts.new((x, y, z))
                    v_cache[key] = vert
                return vert

            x0_u = 0.0
            x1_u = inner_x0_u
            x2_u = inner_x1_u
            x3_u = width

            y_outer = 0.0
            y_recess = recess
            y_inner = leaf_t

            make_face((v(x0_u, y_outer, 0.0), v(x3_u, y_outer, 0.0), v(x3_u, y_outer, inner_z0), v(x0_u, y_outer, inner_z0)), reverse=False)
            make_face((v(x0_u, y_outer, inner_z1), v(x3_u, y_outer, inner_z1), v(x3_u, y_outer, height), v(x0_u, y_outer, height)), reverse=False)
            make_face((v(x0_u, y_outer, inner_z0), v(x1_u, y_outer, inner_z0), v(x1_u, y_outer, inner_z1), v(x0_u, y_outer, inner_z1)), reverse=False)
            make_face((v(x2_u, y_outer, inner_z0), v(x3_u, y_outer, inner_z0), v(x3_u, y_outer, inner_z1), v(x2_u, y_outer, inner_z1)), reverse=False)

            if mid_bar_h > 0.0 and z3 > z2:
                make_face((v(x1_u, y_outer, z2), v(x2_u, y_outer, z2), v(x2_u, y_outer, z3), v(x1_u, y_outer, z3)), reverse=False)

            make_face((v(x1_u, y_recess, inner_z0), v(x2_u, y_recess, inner_z0), v(x2_u, y_recess, z2), v(x1_u, y_recess, z2)), reverse=False)
            if mid_bar_h > 0.0 and z3 < inner_z1:
                make_face((v(x1_u, y_recess, z3), v(x2_u, y_recess, z3), v(x2_u, y_recess, inner_z1), v(x1_u, y_recess, inner_z1)), reverse=False)
            elif mid_bar_h == 0.0:
                make_face((v(x1_u, y_recess, inner_z0), v(x2_u, y_recess, inner_z0), v(x2_u, y_recess, inner_z1), v(x1_u, y_recess, inner_z1)), reverse=False)

            def wall_x(u, z_a, z_b):
                make_face((v(u, y_outer, z_a), v(u, y_outer, z_b), v(u, y_recess, z_b), v(u, y_recess, z_a)), reverse=False)

            def wall_z(z, u_a, u_b):
                make_face((v(u_a, y_outer, z), v(u_b, y_outer, z), v(u_b, y_recess, z), v(u_a, y_recess, z)), reverse=False)

            wall_z(inner_z0, x1_u, x2_u)
            wall_z(z2, x1_u, x2_u)
            wall_x(x1_u, inner_z0, z2)
            wall_x(x2_u, inner_z0, z2)

            if mid_bar_h > 0.0 and z3 < inner_z1:
                wall_z(z3, x1_u, x2_u)
                wall_z(inner_z1, x1_u, x2_u)
                wall_x(x1_u, z3, inner_z1)
                wall_x(x2_u, z3, inner_z1)

            rev_inner = True

            make_face((v(x0_u, y_inner, 0.0), v(x3_u, y_inner, 0.0), v(x3_u, y_inner, inner_z0), v(x0_u, y_inner, inner_z0)), reverse=rev_inner)
            make_face((v(x0_u, y_inner, inner_z1), v(x3_u, y_inner, inner_z1), v(x3_u, y_inner, height), v(x0_u, y_inner, height)), reverse=rev_inner)
            make_face((v(x0_u, y_inner, inner_z0), v(x1_u, y_inner, inner_z0), v(x1_u, y_inner, inner_z1), v(x0_u, y_inner, inner_z1)), reverse=rev_inner)
            make_face((v(x2_u, y_inner, inner_z0), v(x3_u, y_inner, inner_z0), v(x3_u, y_inner, inner_z1), v(x2_u, y_inner, inner_z1)), reverse=rev_inner)

            if mid_bar_h > 0.0 and z3 > z2:
                make_face((v(x1_u, y_inner, z2), v(x2_u, y_inner, z2), v(x2_u, y_inner, z3), v(x1_u, y_inner, z3)), reverse=rev_inner)

            make_face((v(x1_u, y_inner, inner_z0), v(x2_u, y_inner, inner_z0), v(x2_u, y_inner, z2), v(x1_u, y_inner, z2)), reverse=rev_inner)
            if mid_bar_h > 0.0 and z3 < inner_z1:
                make_face((v(x1_u, y_inner, z3), v(x2_u, y_inner, z3), v(x2_u, y_inner, inner_z1), v(x1_u, y_inner, inner_z1)), reverse=rev_inner)
            elif mid_bar_h == 0.0:
                make_face((v(x1_u, y_inner, inner_z0), v(x2_u, y_inner, inner_z0), v(x2_u, y_inner, inner_z1), v(x1_u, y_inner, inner_z1)), reverse=rev_inner)

            make_face((v(x0_u, y_outer, 0.0), v(x0_u, y_outer, height), v(x0_u, y_inner, height), v(x0_u, y_inner, 0.0)), reverse=False)
            make_face((v(x3_u, y_outer, 0.0), v(x3_u, y_inner, 0.0), v(x3_u, y_inner, height), v(x3_u, y_outer, height)), reverse=False)
            make_face((v(x0_u, y_outer, 0.0), v(x0_u, y_inner, 0.0), v(x3_u, y_inner, 0.0), v(x3_u, y_outer, 0.0)), reverse=False)
            make_face((v(x0_u, y_outer, height), v(x3_u, y_outer, height), v(x3_u, y_inner, height), v(x0_u, y_inner, height)), reverse=False)

            if x_dir == -1 and bm.faces:
                bmesh.ops.reverse_faces(bm, faces=bm.faces)

    elif comp_type == 'BARS':
        # Two vertical locking bars with cam-lock discs and keeper brackets.
        bar_xs  = [width * 0.28 * x_dir, width * 0.72 * x_dir]
        bar_r   = 0.016   # rod radius
        cam_r   = 0.032   # cam disc outer radius
        cam_t   = 0.014   # cam disc thickness
        keep_w  = 0.030   # keeper bracket width
        keep_d  = 0.016   # keeper bracket depth
        keep_h  = 0.055   # keeper bracket height

        rot90x = mathutils.Matrix.Rotation(math.radians(90), 3, 'X')

        for bx in bar_xs:
            # Main vertical rod (octagonal cross-section for visual quality)
            gr = bmesh.ops.create_cone(bm, cap_ends=True, cap_tris=False,
                                        segments=8, radius1=bar_r, radius2=bar_r,
                                        depth=height + 0.06)
            bmesh.ops.translate(bm, verts=gr['verts'], vec=(bx, -0.038, height / 2))

            # Three cam-lock discs per bar (top, middle, bottom thirds)
            for z_frac in [0.12, 0.50, 0.88]:
                gc = bmesh.ops.create_cone(bm, cap_ends=True, cap_tris=False,
                                            segments=10, radius1=cam_r, radius2=cam_r,
                                            depth=cam_t)
                # Rotate disc so its flat face is parallel to the door surface (axis = Y)
                bmesh.ops.rotate(bm, verts=gc['verts'], cent=(0, 0, 0), matrix=rot90x)
                bmesh.ops.translate(bm, verts=gc['verts'],
                                    vec=(bx, -0.038, height * z_frac))

                # Keeper bracket — simple box that holds the cam in position
                gk = bmesh.ops.create_cube(bm, size=1.0)
                bmesh.ops.scale(bm, verts=gk['verts'], vec=(keep_w, keep_d, keep_h))
                bmesh.ops.translate(bm, verts=gk['verts'],
                                    vec=(bx + (cam_r + keep_w * 0.5) * x_dir,
                                         -0.038,
                                         height * z_frac))

    elif comp_type == 'HINGES':
        # Four hinges: each has two leaves (door-side + frame-side) joined by a knuckle barrel.
        z_positions = [height * 0.08, height * 0.30, height * 0.62, height * 0.88]
        leaf_w   = 0.060   # leaf plate width (away from pivot)
        leaf_h   = 0.092   # leaf plate height
        leaf_t   = 0.008   # leaf plate thickness
        barrel_r = 0.013   # knuckle cylinder radius
        y_off    = -(leaf_t / 2 + 0.003)  # slight inset from door outer face

        for z in z_positions:
            # Door leaf — attached to the door panel, extends in x_dir from pivot
            gl = bmesh.ops.create_cube(bm, size=1.0)
            bmesh.ops.scale(bm, verts=gl['verts'], vec=(leaf_w, leaf_t, leaf_h))
            bmesh.ops.translate(bm, verts=gl['verts'],
                                vec=(leaf_w / 2 * x_dir, y_off, z))

            # Frame leaf — extends opposite to x_dir (fixed, attached to container post)
            gf = bmesh.ops.create_cube(bm, size=1.0)
            bmesh.ops.scale(bm, verts=gf['verts'], vec=(leaf_w, leaf_t, leaf_h))
            bmesh.ops.translate(bm, verts=gf['verts'],
                                vec=(-leaf_w / 2 * x_dir, y_off, z))

            # Knuckle barrel — vertical cylinder at the pivot axis
            gb = bmesh.ops.create_cone(bm, cap_ends=True, cap_tris=False,
                                        segments=10,
                                        radius1=barrel_r, radius2=barrel_r,
                                        depth=leaf_h + 0.014)
            bmesh.ops.translate(bm, verts=gb['verts'], vec=(0.0, y_off, z))

    elif comp_type == 'HANDLES':
        # L-shaped operating handle: mount plate → two support arms → horizontal grip bar.
        bx    = width * 0.72 * x_dir
        hz    = height * 0.50
        rod_r = 0.010   # cylinder radius for all rods
        arm_h = 0.090   # vertical arm length
        grip_len = 0.145  # horizontal grip bar length
        arm_spacing = 0.050  # half-distance between upper/lower arm centres

        rot90x = mathutils.Matrix.Rotation(math.radians(90), 3, 'X')

        # Mounting plate (flat box, flush against door inner surface)
        gm = bmesh.ops.create_cube(bm, size=1.0)
        bmesh.ops.scale(bm, verts=gm['verts'], vec=(0.030, 0.008, grip_len * 0.9))
        bmesh.ops.translate(bm, verts=gm['verts'], vec=(bx, -0.008, hz))

        # Upper support arm (vertical cylinder, bridges plate to grip)
        gu = bmesh.ops.create_cone(bm, cap_ends=True, cap_tris=False,
                                    segments=8, radius1=rod_r, radius2=rod_r,
                                    depth=arm_h)
        bmesh.ops.translate(bm, verts=gu['verts'],
                            vec=(bx, -0.028, hz + arm_spacing + arm_h / 2))

        # Lower support arm
        glo = bmesh.ops.create_cone(bm, cap_ends=True, cap_tris=False,
                                     segments=8, radius1=rod_r, radius2=rod_r,
                                     depth=arm_h)
        bmesh.ops.translate(bm, verts=glo['verts'],
                            vec=(bx, -0.028, hz - arm_spacing - arm_h / 2))

        # Horizontal grip bar (cylinder along door-depth axis = Y)
        gh = bmesh.ops.create_cone(bm, cap_ends=True, cap_tris=False,
                                    segments=8, radius1=rod_r, radius2=rod_r,
                                    depth=grip_len)
        bmesh.ops.rotate(bm, verts=gh['verts'], cent=(0, 0, 0), matrix=rot90x)
        bmesh.ops.translate(bm, verts=gh['verts'], vec=(bx, -0.075, hz))

    bm.to_mesh(mesh)
    bm.free()

    # Tag for rebuild system
    obj["is_container_part"] = True
    return obj