import bpy
import bmesh


def _make_face(bm, verts):
    try:
        return bm.faces.new(verts)
    except ValueError:
        return None


def _build_official_side_profile_points(width, depth):
    """Build the OFFICIAL trapezoidal corrugation profile (real ISO container spec).
    
    Repeating unit (meters):
    - 70 mm flat at z=0          (Interface / bottom)
    - 68 mm slope up to depth    (inward slope)
    - 72 mm flat at depth        (Outerface / rib)
    - 68 mm slope down to z=0    (outward slope)
    
    Exact pitch = 0.278 m.
    """
    w_bottom = 0.070
    w_slope = 0.068
    w_top = 0.072          # rib at depth

    pattern = [
        (w_bottom, 0.0),   # bottom flat
        (w_slope, depth),  # slope inward/up
        (w_top, depth),    # rib flat at depth
        (w_slope, 0.0),    # slope outward/down
    ]

    pitch = sum(w for w, _z in pattern)  # 0.278 m

    if width <= 0.0:
        return [(-0.0, 0.0), (0.0, 0.0)]

    # Small-width case: scale entire pattern to fit
    if width < pitch:
        s = width / pitch if pitch > 0.0 else 1.0
        pattern = [(w * s, z) for w, z in pattern]
        cycles = 1
        edge_flat = 0.0
    else:
        cycles = max(1, int((width / pitch) + 1e-9))
        edge_flat = max(0.0, (width - (cycles * pitch)) * 0.5)

    x = -width * 0.5
    z = 0.0
    pts = [(x, z)]

    if edge_flat > 1.0e-9:
        x += edge_flat
        pts.append((x, z))

    # Build trapezoidal profile (NO vertical jumps)
    for _ in range(cycles):
        for seg_w, seg_z in pattern:
            x += seg_w
            pts.append((x, seg_z))
            z = seg_z

    # Finish with flat edge up to +width/2 if needed
    if x < (width * 0.5) - 1.0e-8:
        x = width * 0.5
        pts.append((x, z))

    # Snap last point exactly
    pts[-1] = (width * 0.5, pts[-1][1])

    return pts



def _create_corrugated_panel_legacy(bm, width, height, rib_spacing, rib_depth):
    """Legacy trapezoidal corrugation (kept for backwards compatibility)."""
    # Calculate exact number of ribs to fit the panel width perfectly
    num_ribs = max(1, int(width / rib_spacing))
    actual_spacing = width / num_ribs

    bottom_y = -height * 0.5
    top_y = height * 0.5

    # Generate the bottom profile (Local Y = -height/2)
    bottom_verts = []
    for i in range(num_ribs):
        x_start = -width/2 + i * actual_spacing

        # 4 points per trapezoidal wave
        bottom_verts.append(bm.verts.new((x_start, bottom_y, -rib_depth/2)))
        bottom_verts.append(bm.verts.new((x_start + actual_spacing * 0.25, bottom_y, rib_depth/2)))
        bottom_verts.append(bm.verts.new((x_start + actual_spacing * 0.75, bottom_y, rib_depth/2)))

    # Cap the end of the final wave
    bottom_verts.append(bm.verts.new((width/2, bottom_y, -rib_depth/2)))

    # Generate the top profile (Local Y = height/2)
    top_verts = [bm.verts.new((bv.co.x, top_y, bv.co.z)) for bv in bottom_verts]

    # Bridge the profiles with faces
    for i in range(len(bottom_verts) - 1):
        _make_face(bm, (bottom_verts[i], bottom_verts[i+1], top_verts[i+1], top_verts[i]))


def _create_corrugated_panel_official_side(bm, width, height, depth):
    """Official trapezoidal side corrugation (real ISO spec)."""
    pts = _build_official_side_profile_points(width, depth)
    bottom_y = -height * 0.5
    top_y = height * 0.5
    bottom_verts = [bm.verts.new((x, bottom_y, z)) for x, z in pts]
    top_verts = [bm.verts.new((x, top_y, z)) for x, z in pts]

    for i in range(len(bottom_verts) - 1):
        _make_face(bm, (bottom_verts[i], bottom_verts[i+1], top_verts[i+1], top_verts[i]))


def create_corrugated_panel(
    name,
    width,
    height,
    location,
    rotation,
    rib_spacing=0.305,
    rib_depth=0.028,
    profile="OFFICIAL_SIDE",          # ← default is now the real official profile
    corrugation_depth=0.036,
):
    """Creates a corrugated panel mesh.
    
    OFFICIAL_SIDE = authentic ISO trapezoidal profile (70-68-72-68 mm pattern with real slopes).
    LEGACY = old trapezoidal wave (for backwards compatibility).
    
    Local axes:
    - X: panel width
    - Y: panel height
    - Z: corrugation depth (outward = +Z)
    """
    mesh = bpy.data.meshes.new(name)
    obj = bpy.data.objects.new(name, mesh)
    bm = bmesh.new()

    if profile == "LEGACY":
        _create_corrugated_panel_legacy(bm, width, height, rib_spacing, rib_depth)
    else:
        _create_corrugated_panel_official_side(bm, width, height, corrugation_depth)

    if bm.faces:
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces)

    bm.to_mesh(mesh)
    bm.free()

    obj.location = location
    obj.rotation_euler = rotation
    obj["is_container_part"] = True

    return obj