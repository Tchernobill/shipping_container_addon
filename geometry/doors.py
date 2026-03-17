import bpy
import bmesh
import math

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

        # Tunable (meters). Defaults aim for a believable ISO door without being overly dense.
        frame_w = 0.040      # 40mm frame width
        mid_bar_h = 0.050    # 50mm middle stiffener height
        recess = 0.020       # 20mm recess on the outer face (towards +Y / inside)
        leaf_t = 0.040       # overall door leaf thickness (outer face at y=0, inner face at y=leaf_t)

        # Clamp to avoid invalid geometry on extreme sizes.
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

        # If the inner area is too small, fall back to a flat sheet.
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
                # Not enough height for two panels + bar; make a single recessed panel.
                mid_bar_h = 0.0
                z2 = inner_z1
                z3 = inner_z1
            else:
                panel_h = inner_h * 0.5
                z2 = inner_z0 + panel_h
                z3 = z2 + mid_bar_h

            # Vertex cache to avoid duplicates.
            v_cache = {}

            def v(u, y, z):
                # u is the width coordinate in [0..width], mapped to X with x_dir.
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

            # --- Outer (front) surfaces: outward normals should face -Y ---
            # Bottom frame strip
            make_face((v(x0_u, y_outer, 0.0), v(x3_u, y_outer, 0.0), v(x3_u, y_outer, inner_z0), v(x0_u, y_outer, inner_z0)), reverse=False)
            # Top frame strip
            make_face((v(x0_u, y_outer, inner_z1), v(x3_u, y_outer, inner_z1), v(x3_u, y_outer, height), v(x0_u, y_outer, height)), reverse=False)
            # Left frame strip (hinge side)
            make_face((v(x0_u, y_outer, inner_z0), v(x1_u, y_outer, inner_z0), v(x1_u, y_outer, inner_z1), v(x0_u, y_outer, inner_z1)), reverse=False)
            # Right frame strip
            make_face((v(x2_u, y_outer, inner_z0), v(x3_u, y_outer, inner_z0), v(x3_u, y_outer, inner_z1), v(x2_u, y_outer, inner_z1)), reverse=False)

            # Middle stiffener (only if enabled)
            if mid_bar_h > 0.0 and z3 > z2:
                make_face((v(x1_u, y_outer, z2), v(x2_u, y_outer, z2), v(x2_u, y_outer, z3), v(x1_u, y_outer, z3)), reverse=False)

            # --- Recessed outer panels (still outward-facing, but pushed towards +Y) ---
            # Bottom panel
            make_face((v(x1_u, y_recess, inner_z0), v(x2_u, y_recess, inner_z0), v(x2_u, y_recess, z2), v(x1_u, y_recess, z2)), reverse=False)
            # Top panel (if we have a mid bar)
            if mid_bar_h > 0.0 and z3 < inner_z1:
                make_face((v(x1_u, y_recess, z3), v(x2_u, y_recess, z3), v(x2_u, y_recess, inner_z1), v(x1_u, y_recess, inner_z1)), reverse=False)
            elif mid_bar_h == 0.0:
                # Single recessed panel case (no mid bar)
                make_face((v(x1_u, y_recess, inner_z0), v(x2_u, y_recess, inner_z0), v(x2_u, y_recess, inner_z1), v(x1_u, y_recess, inner_z1)), reverse=False)

            # --- Side walls between front and recessed surfaces ---
            def wall_x(u, z_a, z_b):
                make_face((v(u, y_outer, z_a), v(u, y_outer, z_b), v(u, y_recess, z_b), v(u, y_recess, z_a)), reverse=False)

            def wall_z(z, u_a, u_b):
                make_face((v(u_a, y_outer, z), v(u_b, y_outer, z), v(u_b, y_recess, z), v(u_a, y_recess, z)), reverse=False)

            # Bottom panel walls
            wall_z(inner_z0, x1_u, x2_u)   # bottom edge
            wall_z(z2, x1_u, x2_u)         # top edge (to mid bar)
            wall_x(x1_u, inner_z0, z2)     # left edge
            wall_x(x2_u, inner_z0, z2)     # right edge

            if mid_bar_h > 0.0 and z3 < inner_z1:
                # Top panel walls
                wall_z(z3, x1_u, x2_u)         # bottom edge (to mid bar)
                wall_z(inner_z1, x1_u, x2_u)   # top edge
                wall_x(x1_u, z3, inner_z1)     # left edge
                wall_x(x2_u, z3, inner_z1)     # right edge

            # --- Inner (back) skin: flat panels and frame on the inside ---
            # These faces should point +Y (into the container), so we reverse their winding for the left door.
            # For the right door, we reverse all faces at the end (mirroring flips winding).
            rev_inner = True

            # Bottom frame strip
            make_face((v(x0_u, y_inner, 0.0), v(x3_u, y_inner, 0.0), v(x3_u, y_inner, inner_z0), v(x0_u, y_inner, inner_z0)), reverse=rev_inner)
            # Top frame strip
            make_face((v(x0_u, y_inner, inner_z1), v(x3_u, y_inner, inner_z1), v(x3_u, y_inner, height), v(x0_u, y_inner, height)), reverse=rev_inner)
            # Left frame strip
            make_face((v(x0_u, y_inner, inner_z0), v(x1_u, y_inner, inner_z0), v(x1_u, y_inner, inner_z1), v(x0_u, y_inner, inner_z1)), reverse=rev_inner)
            # Right frame strip
            make_face((v(x2_u, y_inner, inner_z0), v(x3_u, y_inner, inner_z0), v(x3_u, y_inner, inner_z1), v(x2_u, y_inner, inner_z1)), reverse=rev_inner)

            # Inner middle stiffener
            if mid_bar_h > 0.0 and z3 > z2:
                make_face((v(x1_u, y_inner, z2), v(x2_u, y_inner, z2), v(x2_u, y_inner, z3), v(x1_u, y_inner, z3)), reverse=rev_inner)

            # Inner flat panels
            make_face((v(x1_u, y_inner, inner_z0), v(x2_u, y_inner, inner_z0), v(x2_u, y_inner, z2), v(x1_u, y_inner, z2)), reverse=rev_inner)
            if mid_bar_h > 0.0 and z3 < inner_z1:
                make_face((v(x1_u, y_inner, z3), v(x2_u, y_inner, z3), v(x2_u, y_inner, inner_z1), v(x1_u, y_inner, inner_z1)), reverse=rev_inner)
            elif mid_bar_h == 0.0:
                make_face((v(x1_u, y_inner, inner_z0), v(x2_u, y_inner, inner_z0), v(x2_u, y_inner, inner_z1), v(x1_u, y_inner, inner_z1)), reverse=rev_inner)

            # --- Perimeter walls to close the door leaf volume ---
            # Left edge (hinge side): outward normal is -X for left door.
            make_face((v(x0_u, y_outer, 0.0), v(x0_u, y_outer, height), v(x0_u, y_inner, height), v(x0_u, y_inner, 0.0)), reverse=False)
            # Right edge: outward normal is +X for left door (note the different winding).
            make_face((v(x3_u, y_outer, 0.0), v(x3_u, y_inner, 0.0), v(x3_u, y_inner, height), v(x3_u, y_outer, height)), reverse=False)
            # Bottom edge: outward normal is -Z
            make_face((v(x0_u, y_outer, 0.0), v(x0_u, y_inner, 0.0), v(x3_u, y_inner, 0.0), v(x3_u, y_outer, 0.0)), reverse=False)
            # Top edge: outward normal is +Z
            make_face((v(x0_u, y_outer, height), v(x3_u, y_outer, height), v(x3_u, y_inner, height), v(x0_u, y_inner, height)), reverse=False)

            # The mirroring approach (x_dir=-1) flips face winding. Correct it for the right door leaf.
            if x_dir == -1 and bm.faces:
                bmesh.ops.reverse_faces(bm, faces=bm.faces)
            
    elif comp_type == 'BARS':
        # Two vertical locking bars per door
        bar_xs = [width * 0.3 * x_dir, width * 0.7 * x_dir]
        for bx in bar_xs:
            geom = bmesh.ops.create_cone(bm, cap_ends=True, cap_tris=False, segments=8, radius1=0.015, radius2=0.015, depth=height+0.05
            bmesh.ops.translate(bm, verts=geom['verts'], vec=(bx, -0.035, height/2))
            
    elif comp_type == 'HINGES':
        # 4 hinges per door attached at the pivot (X=0)
        z_positions = [height * 0.1, height * 0.35, height * 0.65, height * 0.9]
        for z in z_positions:
            geom = bmesh.ops.create_cube(bm, size=1.0)
            bmesh.ops.scale(bm, verts=geom['verts'], vec=(0.04, 0.05, 0.08))
            bmesh.ops.translate(bm, verts=geom['verts'], vec=(0.02 * x_dir, -0.01, z))
            
    elif comp_type == 'HANDLES':
        # Handles attached to the inner locking bar
        bx = width * 0.7 * x_dir
        z_positions = [height * 0.4, height * 0.5]
        for z in z_positions:
            geom = bmesh.ops.create_cube(bm, size=1.0)
            bmesh.ops.scale(bm, verts=geom['verts'], vec=(0.08, 0.02, 0.02))
            bmesh.ops.translate(bm, verts=geom['verts'], vec=(bx + 0.04 * x_dir, -0.05, z))
            
    bm.to_mesh(mesh)
    bm.free()
    
    # Tag for rebuild system
    obj["is_container_part"] = True
    return obj
