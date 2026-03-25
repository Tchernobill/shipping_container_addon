"""ISO Shipping Container – Door Geometry

Four focused public builders:

    create_door_panel()       – frame + corrugated center panel
    create_door_hinges()      – 4 hinge assemblies
    create_locking_hardware() – bars, guides, cams, handles  (tagged is_hardware)
    get_hinge_positions()     – helper consumed by rebuild.py for post-recess cuts

Local-axis convention (left-door canonical space):
    X : 0 = hinge/pivot side  →  width = closing edge
    Y : 0 = outer (viewer) face  →  LEAF_T = inner face
    Z : 0 = door bottom  →  height = door top

Right-door geometry is the left-door mesh mirrored through X = 0.

Door panel anatomy
──────────────────
    ┌────────────────────────────┐  ← Top rail    150 mm  (FRAME_T)
    │ ┌────────────────────────┐ │
    │ │  corrugated center     │ │  ← Left / right stiles  100 mm  (FRAME_S)
    │ │  (0–8 ribs, param.)    │ │
    │ └────────────────────────┘ │
    └────────────────────────────┘  ← Bottom rail 150 mm  (FRAME_T)

Corrugation cross-section (XY plane, swept along Z)
────────────────────────────────────────────────────
    Y = 0            (viewer face / corrugation peaks — flush with frame)
    ─────┐  ┌──────┐  ┌──────  ← peaks
          ╲ ╱        ╲ ╱
    ──────╳──────────╳──────  ← background at Y = CORR_DEPTH = 0.045 m
          │◄ 32 ►│◄ 70 ►│◄ 32 ►│
          │◄────── 134 mm ──────►│

    Total door leaf thickness  LEAF_T = 60 mm  (Y axis)
"""

import bpy
import bmesh
import math
import mathutils

from .primitives import append_box, create_object_from_mesh

# ── Physical constants (metres) ───────────────────────────────────────────────
FRAME_T = 0.150   # top / bottom rail height (Z)
FRAME_S = 0.100   # left / right stile width (X)

CORR_OUTSIDE = 0.134                               # outer corrugation pitch
CORR_INSIDE  = 0.070                               # inner flat (rib bottom) width
CORR_SLOPE   = (CORR_OUTSIDE - CORR_INSIDE) / 2   # = 0.032 m each slope
CORR_DEPTH   = 0.045                               # recess depth from frame face

LEAF_T     = 0.060   # total door leaf thickness (Y axis)

HINGE_D    = 0.040   # hinge cylinder diameter
HINGE_R    = HINGE_D * 0.5
HINGE_H    = 0.130   # hinge cylinder height (Z axis)
NUM_HINGES = 4

BAR1_EDGE     = 0.170   # locking bar 1: distance from closing edge
BAR2_OFFSET   = 0.420   # locking bar 2: distance from bar 1 toward hinge
HANDLE_HEIGHT = 0.900   # handle grip world-Z from container floor


# ── Private mesh helpers ───────────────────────────────────────────────────────

def _b(bm, sx, sy, sz, cx=0.0, cy=0.0, cz=0.0):
    """Append a box (sx × sy × sz, centred at cx,cy,cz) to bm."""
    g = bmesh.ops.create_cube(bm, size=1.0)
    bmesh.ops.scale(bm,     verts=g['verts'], vec=(sx, sy, sz))
    bmesh.ops.translate(bm, verts=g['verts'], vec=(cx, cy, cz))


def _cyl(bm, r, length, cx=0.0, cy=0.0, cz=0.0, axis='Z', segs=8):
    """Append a cylinder (radius r, length along axis) to bm."""
    g = bmesh.ops.create_cone(bm, cap_ends=True, cap_tris=False,
                               segments=segs, radius1=r, radius2=r, depth=length)
    if axis == 'Y':
        bmesh.ops.rotate(bm, verts=g['verts'], cent=(0, 0, 0),
                         matrix=mathutils.Matrix.Rotation(math.pi * 0.5, 3, 'X'))
    elif axis == 'X':
        bmesh.ops.rotate(bm, verts=g['verts'], cent=(0, 0, 0),
                         matrix=mathutils.Matrix.Rotation(math.pi * 0.5, 3, 'Y'))
    bmesh.ops.translate(bm, verts=g['verts'], vec=(cx, cy, cz))


def _mirror(bm):
    """Flip through X = 0 and reverse winding (right-door mirroring)."""
    bmesh.ops.scale(bm, verts=bm.verts, vec=(-1.0, 1.0, 1.0))
    bmesh.ops.reverse_faces(bm, faces=bm.faces)


def _make_obj(name, is_hardware=False):
    mesh = bpy.data.meshes.new(name)
    obj  = bpy.data.objects.new(name, mesh)
    obj["is_container_part"] = True
    if is_hardware:
        obj["is_hardware"] = True
    return obj, mesh


def _q(v, step=1.0e-6):
    return int(round(float(v) / step))


def _door_panel_mesh_name(width, height, n_corr, is_left):
    side = "L" if is_left else "R"
    return f"ISO_DoorPanel_{side}_{_q(width)}_{_q(height)}_{int(n_corr)}_v2"


def _build_door_panel_mesh_data(width, height, num_corrugations):
    """Return (verts, faces) for the *left* door panel in canonical space."""
    verts = []
    faces = []

    dt = LEAF_T

    # Center panel area in door-local coordinates
    px0     = FRAME_S
    px1     = width  - FRAME_S
    pz0     = FRAME_T
    pz1     = height - FRAME_T
    panel_w = px1 - px0
    panel_h = pz1 - pz0

    # ── Perimeter frame boxes ────────────────────────────────────────────────
    # Bottom rail (full door width)
    append_box(
        verts,
        faces,
        center=(width * 0.5, dt * 0.5, FRAME_T * 0.5),
        size=(width, dt, FRAME_T),
    )
    # Top rail
    append_box(
        verts,
        faces,
        center=(width * 0.5, dt * 0.5, height - FRAME_T * 0.5),
        size=(width, dt, FRAME_T),
    )
    # Left stile (hinge side)
    append_box(
        verts,
        faces,
        center=(FRAME_S * 0.5, dt * 0.5, pz0 + panel_h * 0.5),
        size=(FRAME_S, dt, panel_h),
    )
    # Right stile (closing edge)
    append_box(
        verts,
        faces,
        center=(width - FRAME_S * 0.5, dt * 0.5, pz0 + panel_h * 0.5),
        size=(FRAME_S, dt, panel_h),
    )

    # ── Corrugated center panel volume ───────────────────────────────────────
    if panel_w > 0.020 and panel_h > 0.020:
        fwd = _corr_profile(pz0, panel_h, num_corrugations)
        loop = fwd + [
            (fwd[-1][0], LEAF_T),   # back-top corner
            (fwd[0][0],  LEAF_T),   # back-bottom corner
        ]
        n = len(loop)

        base_left = len(verts)
        # left face at x=px0, right face at x=px1
        for z, y in loop:
            verts.append((px0, y, z))
        for z, y in loop:
            verts.append((px1, y, z))

        # side-wall quads
        for i in range(n):
            j = (i + 1) % n
            faces.append(
                (
                    base_left + i,
                    base_left + n + i,
                    base_left + n + j,
                    base_left + j,
                )
            )

        # end caps (ngons)
        faces.append(tuple(reversed(range(base_left, base_left + n))))  # normal -X
        faces.append(tuple(range(base_left + n, base_left + 2 * n)))    # normal +X

    return verts, faces


def _get_or_create_door_panel_mesh(width, height, num_corrugations, is_left):
    mesh_name = _door_panel_mesh_name(width, height, num_corrugations, is_left)
    mesh = bpy.data.meshes.get(mesh_name)
    if mesh is not None:
        return mesh

    verts, faces = _build_door_panel_mesh_data(width, height, num_corrugations)

    if not is_left:
        # Mirror through X=0 and reverse face winding to preserve outward normals.
        verts = [(-x, y, z) for (x, y, z) in verts]
        faces = [tuple(reversed(f)) for f in faces]

    mesh = bpy.data.meshes.new(mesh_name)
    mesh.from_pydata(verts, [], faces)
    mesh.update()
    mesh.use_fake_user = True
    return mesh


def _door_hardware_mesh_name(width, height, is_left, floor_z_offset, num_corrugations):
    side = "L" if is_left else "R"
    return (
        f"ISO_DoorHardware_{side}_{_q(width)}_{_q(height)}_{_q(floor_z_offset)}_"
        f"{int(num_corrugations)}_v1"
    )


def _get_or_create_door_hardware_mesh(width, height, is_left, floor_z_offset, num_corrugations):
    mesh_name = _door_hardware_mesh_name(width, height, is_left, floor_z_offset, num_corrugations)
    mesh = bpy.data.meshes.get(mesh_name)
    if mesh is not None:
        return mesh

    mesh = bpy.data.meshes.new(mesh_name)
    bm = bmesh.new()

    bar_r   = 0.016
    bar_ext = 0.040
    y_bar   = -0.022   # bars sit 22 mm proud of the outer door face
    cam_r, cam_t  = 0.032, 0.018
    chw, chh, chd = 0.080, 0.058, 0.036

    bar_x1 = max(0.010, width - BAR1_EDGE)
    bar_x2 = max(0.010, bar_x1 - BAR2_OFFSET)
    bar_xs = [bx for bx in (bar_x1, bar_x2) if 0.010 < bx < width - 0.010]

    # Z-centres of flat door background sections — used for bracket / handle snapping
    gap_zs = get_corrugation_gap_centers(FRAME_T, height - 2 * FRAME_T, num_corrugations)

    for bx in bar_xs:
        # ── Locking rod ───────────────────────────────────────────────────────
        _cyl(bm, bar_r, height + 2 * bar_ext,
             cx=bx, cy=y_bar, cz=height * 0.5, axis='Z', segs=10)

        # ── Guide brackets — cylinder collars, one per gap centre ───────────
        for gz in gap_zs:
            _cyl(bm, 0.028, 0.060,
                 cx=bx, cy=y_bar, cz=gz, axis='Z', segs=12)
            _b(bm, 0.010, 0.014, 0.020,
               cx=bx, cy=-0.007, cz=gz)

        # ── Cam disc + cam holder at top and bottom of each bar ───────────────
        for cz_cam in (0.030, height - 0.030):
            _cyl(bm, cam_r, cam_t,
                 cx=bx, cy=y_bar, cz=cz_cam, axis='Y', segs=10)
            _b(bm, chw, chd, chh, cx=bx, cy=y_bar - chd * 0.5, cz=cz_cam)

    # ── Handle assembly — snapped to nearest gap centre ───────────────────────
    if bar_xs and gap_zs:
        bx = bar_xs[0]
        target_hz = max(0.050, HANDLE_HEIGHT - floor_z_offset)
        hz = min(gap_zs, key=lambda z: abs(z - target_hz))
        hz = max(FRAME_T + 0.050, min(hz, height - FRAME_T - 0.050))

        _b(bm, 0.120, 0.012, 0.260, cx=bx, cy=y_bar - 0.006, cz=hz)
        _cyl(bm, 0.014, 0.115,
             cx=bx, cy=y_bar - 0.065, cz=hz, axis='Y', segs=8)
        for dz in (-0.080, 0.080):
            _b(bm, 0.020, 0.060, 0.018, cx=bx, cy=y_bar - 0.034, cz=hz + dz)
        _b(bm, 0.062, 0.032, 0.065, cx=bx, cy=y_bar - 0.016, cz=hz - 0.100)

    if not is_left:
        _mirror(bm)
    if bm.faces:
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(mesh)
    bm.free()

    mesh.use_fake_user = True
    return mesh


def _hinge_z_positions(door_height, hinge_count=NUM_HINGES, hinge_height=HINGE_H):
    """Return Z of the *center* of each hinge, hinge_count total.

    Hinges are distributed evenly from 0.05 m above the door bottom to 0.05 m
    below the door top, independent of hinge_count (3–5 via UI).

    Note: the 0.05 m margin is measured to the hinge *pivot/center* (not the
    cylinder extents), matching the door-instancing expectation.
    """
    hinge_count = max(1, int(hinge_count))
    _ = hinge_height
    if hinge_count == 1:
        return [door_height * 0.5]
    margin = 0.10
    z0 = margin
    z1 = door_height - margin
    if z1 <= z0:
        return [door_height * 0.5]
    step = (z1 - z0) / (hinge_count - 1)
    return [z0 + i * step for i in range(hinge_count)]


def _get_or_create_hinge_master_mesh():
    """Create (or reuse) the master hinge mesh used by per-door instances."""
    mesh_name = "ISO_Door_Hinge_Master_v2"
    if mesh_name in bpy.data.meshes:
        return bpy.data.meshes[mesh_name]

    mesh = bpy.data.meshes.new(mesh_name)
    bm = bmesh.new()

    def _scale_about_point(verts, vec, center):
        """Scale verts about an arbitrary center (bmesh.ops.scale has no center arg)."""
        if not verts:
            return
        bmesh.ops.translate(bm, verts=verts, vec=(-center.x, -center.y, -center.z))
        bmesh.ops.scale(bm, verts=verts, vec=vec)
        bmesh.ops.translate(bm, verts=verts, vec=(center.x, center.y, center.z))

    bmesh.ops.create_cone(
        bm,
        cap_ends=True,
        cap_tris=False,
        segments=16,
        radius1=HINGE_R,
        radius2=HINGE_R,
        depth=HINGE_H,
    )

    # Select the 4 side faces with the strongest +X normal.
    side_faces = [f for f in bm.faces if abs(f.normal.z) < 0.5]
    side_faces.sort(key=lambda f: f.normal.x, reverse=True)
    target_faces = side_faces[:4]

    if target_faces:
        # 1) Extrude +X by 0.06, angled 15° toward +Y, then scale in by 10% in Z.
        res1 = bmesh.ops.extrude_face_region(bm, geom=target_faces)
        verts1 = [e for e in res1["geom"] if isinstance(e, bmesh.types.BMVert)]

        dy = math.tan(math.radians(15.0)) * 0.06
        bmesh.ops.translate(bm, verts=verts1, vec=(0.06, dy, 0.0))

        if verts1:
            cent1 = mathutils.Vector((0.0, 0.0, 0.0))
            for v in verts1:
                cent1 += v.co
            cent1 /= len(verts1)
            _scale_about_point(verts1, (0.5, 0.25, 0.9), cent1)

        # 2) Extrude the new most +X faces by +X 0.1, then scale in by 40% in Z.
        side_faces2 = [f for f in bm.faces if abs(f.normal.z) < 0.5]
        side_faces2.sort(key=lambda f: f.calc_center_median().x, reverse=True)
        target_faces2 = side_faces2[:4]

        if target_faces2:
            res2 = bmesh.ops.extrude_face_region(bm, geom=target_faces2)
            verts2 = [e for e in res2["geom"] if isinstance(e, bmesh.types.BMVert)]
            bmesh.ops.translate(bm, verts=verts2, vec=(0.10, 0.0, 0.0))

            if verts2:
                cent2 = mathutils.Vector((0.0, 0.0, 0.0))
                for v in verts2:
                    cent2 += v.co
                cent2 /= len(verts2)
                _scale_about_point(verts2, (0.75, 0.5, 0.6), cent2)

        # 3) Small bevel on the whole hinge.
        if bm.edges:
            bmesh.ops.bevel(
                bm,
                geom=list(bm.edges),
                offset=0.002,
                segments=2,
                profile=0.5,
                affect='EDGES',
                clamp_overlap=True,
            )

    if bm.faces:
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces)

    bm.to_mesh(mesh)
    bm.free()
    return mesh


def get_hinge_master_bounds():
    """Return (min_vec, max_vec) of the hinge master mesh in its local space."""
    mesh = _get_or_create_hinge_master_mesh()
    if not mesh.vertices:
        return (mathutils.Vector((0.0, 0.0, 0.0)), mathutils.Vector((0.0, 0.0, 0.0)))

    min_v = mathutils.Vector((1.0e9, 1.0e9, 1.0e9))
    max_v = mathutils.Vector((-1.0e9, -1.0e9, -1.0e9))
    for v in mesh.vertices:
        co = v.co
        min_v.x = min(min_v.x, co.x)
        min_v.y = min(min_v.y, co.y)
        min_v.z = min(min_v.z, co.z)
        max_v.x = max(max_v.x, co.x)
        max_v.y = max(max_v.y, co.y)
        max_v.z = max(max_v.z, co.z)
    return (min_v, max_v)


# ── Corrugation profile builder ────────────────────────────────────────────────

def _corr_profile(z0, panel_h, n_corr):
    """Build the corrugation cross-section profile as a list of (z, y) points.

    Coordinate space:
        z : door-local Z (height), spanning z0 → z0 + panel_h
        y : 0          = viewer face / corrugation peaks  (flush with frame)
            CORR_DEPTH = recessed background between corrugations

    One rib cycle (bottom → top):
        ½ gap flat  ──  slope up 32 mm (Y: CORR_DEPTH → 0)  ──  inner flat 70 mm
                    ──  slope dn 32 mm (Y: 0 → CORR_DEPTH)   ──  ½ gap flat

    Between consecutive ribs the two half-gaps join to form a full 'space' gap.
    Profile starts and ends at y = CORR_DEPTH (background level).
    """
    if n_corr <= 0 or panel_h < 0.020:
        # Flat flush background — no corrugation geometry
        return [(z0, 0.0), (z0 + panel_h, 0.0)]

    # Clamp: guarantee at least MIN_GAP between adjacent ribs
    MIN_GAP = 0.015
    max_n   = max(1, int((panel_h - MIN_GAP) / (CORR_OUTSIDE + MIN_GAP)))
    n       = min(n_corr, max_n)

    if n * CORR_OUTSIDE >= panel_h:
        return [(z0, 0.0), (z0 + panel_h, 0.0)]

    space = (panel_h - n * CORR_OUTSIDE) / n   # inter-rib gap

    pts = [(z0, 0.0)]
    z   = z0

    # Leading half-gap before first rib
    z += space * 0.5
    pts.append((z, 0.0))

    for i in range(n):
        # Slope inward (Y increases away from viewer)
        z += CORR_SLOPE
        pts.append((z, CORR_DEPTH))
        # Inner flat at rib bottom (deepest point)
        z += CORR_INSIDE
        pts.append((z, CORR_DEPTH))
        # Slope back out to flush face
        z += CORR_SLOPE
        pts.append((z, 0.0))
        # Full gap between ribs; trailing half-gap after last rib
        gap = space if (i < n - 1) else space * 0.5
        z += gap
        pts.append((z, 0.0))

    return pts


def get_corrugation_gap_centers(z0, panel_h, n_corr):
    """Return the Z-centre of every flat background section between corrugation ribs.

    These are the positions where hardware (guide brackets, handle) and decals
    can be mounted flush on the door face without overlapping a rib crest.

    Returns n_corr + 1 centres for n_corr > 0, or five evenly-spaced fallback
    positions when n_corr == 0 (flat panel — no ribs).
    """
    if n_corr <= 0:
        return [z0 + panel_h * (i + 1) / 6 for i in range(5)]

    pts = _corr_profile(z0, panel_h, n_corr)
    centers = []
    for i in range(len(pts) - 1):
        z_a, y_a = pts[i]
        z_b, y_b = pts[i + 1]
        # Flat segment: both endpoints on the outer face (y ≈ 0) with real length
        if abs(y_a) < 1e-6 and abs(y_b) < 1e-6 and (z_b - z_a) > 0.010:
            centers.append((z_a + z_b) * 0.5)
    return centers


def _add_corrugated_strip(bm, x0, x1, z0, panel_h, n_corr):
    """Sweep the corrugation cross-section along X to create the panel volume.

    Ribs run horizontally (left → right across the door width).

    Cross-section closed loop (ZY plane):
      • Forward path : corrugation mid-surface profile  z0 → z0+panel_h  (varying y)
      • Return path  : same profile, offset by +2 mm in Y

    The resulting center panel is a 2 mm-thick extrusion in Y, centered within
    the door leaf thickness (Y = LEAF_T/2).

    The profile is swept from x = x0 (hinge side) to x = x1 (closing edge).
    Left and right faces are n-gon caps; Blender's ear-clipping handles the
    non-convex corrugation shape correctly at tessellation time.
    """
    base = _corr_profile(z0, panel_h, n_corr)

    t = 0.002
    half_t = t * 0.5
    corr_depth = CORR_DEPTH if n_corr > 0 and panel_h >= 0.020 else 0.0

    def _y_mid(y_profile):
        # Center the corrugation profile within the leaf thickness.
        # For corrugated panels, map [0..CORR_DEPTH] → [mid-CORR_DEPTH/2 .. mid+CORR_DEPTH/2].
        # For flat panels (no corrugations), keep the mid-surface at LEAF_T/2.
        return (LEAF_T * 0.5) + (y_profile - corr_depth * 0.5)

    fwd = [(z, _y_mid(y) - half_t) for (z, y) in base]                 # −Y face
    rev = [(z, _y_mid(y) + half_t) for (z, y) in reversed(base)]       # +Y face (return path)
    loop = fwd + rev
    N = len(loop)

    # Each profile point (z, y) becomes a vert at x=x0 and a vert at x=x1.
    # Vertex layout: (x, y, z)
    lv = [bm.verts.new((x0, p[1], p[0])) for p in loop]  # left face  (x = x0)
    rv = [bm.verts.new((x1, p[1], p[0])) for p in loop]  # right face (x = x1)

    # Side-wall quads — one per adjacent pair around the closed loop
    for i in range(N):
        j = (i + 1) % N
        try:
            bm.faces.new([lv[i], rv[i], rv[j], lv[j]])
        except ValueError:
            pass   # guard against degenerate duplicate edges

    # Left and right end caps — n-gons in the ZY plane
    try:
        bm.faces.new(list(reversed(lv)))   # left  cap; winding → normal −X
    except ValueError:
        pass
    try:
        bm.faces.new(rv)                   # right cap; winding → normal +X
    except ValueError:
        pass


# ── Public API ─────────────────────────────────────────────────────────────────

def get_hinge_positions(door_height, hinge_count=NUM_HINGES):
    """Exposed wrapper: used by rebuild.py to position hinge-recess boolean cuts."""
    return _hinge_z_positions(door_height, hinge_count=hinge_count, hinge_height=HINGE_H)


# ─────────────────────────────────────────────────────────────────────────────
def create_door_panel(name, width, height, is_left, num_corrugations=4):
    """Door leaf: perimeter frame + corrugated (or flat) center panel.

    Frame dimensions
    ────────────────
        Top / bottom rails : 150 mm tall  (FRAME_T) — spans full door width
        Left / right stiles: 100 mm wide  (FRAME_S) — spans between rails

    Center panel
    ────────────
        Width  = door_width  − 2 × FRAME_S
        Height = door_height − 2 × FRAME_T
        Filled with num_corrugations vertical trapezoidal ribs.
        num_corrugations = 0 → flat recessed background (no ribs).

    Corrugation spec (metres)
    ──────────────────────────
        Outer pitch width : 0.134   Inner flat (rib bottom) : 0.070
        Each slope        : 0.032   Depth from frame face   : 0.045
        Peaks are flush with the frame face (y = 0).
        Background sits at y = 0.045 (recessed into the door).
    """
    mesh = _get_or_create_door_panel_mesh(width, height, num_corrugations, is_left)
    return create_object_from_mesh(name, mesh, tag_container_part=True)


# ─────────────────────────────────────────────────────────────────────────────
def create_door_hinges(name, _width, height, is_left, hinge_count=NUM_HINGES):
    """Instanced hinges with cylinder pivot.

    Master hinge mesh:
      - Cylinder: Ø0.04 m, height 0.13 m, 16 sides
      - 4 most +X faces extruded twice as specified, then lightly beveled

    Returned object is an EMPTY parent containing hinge instances (MESH
    children) so all hinges share one mesh datablock.
    """
    hinge_count = max(1, int(hinge_count))

    parent = bpy.data.objects.new(name, None)
    parent.empty_display_type = 'PLAIN_AXES'
    parent.empty_display_size = 0.2
    parent["is_container_part"] = True

    master_mesh = _get_or_create_hinge_master_mesh()

    for idx, hz_ctr in enumerate(_hinge_z_positions(height, hinge_count=hinge_count, hinge_height=HINGE_H)):
        inst = bpy.data.objects.new(f"{name}_{idx:02d}", master_mesh)
        inst["is_container_part"] = True
        inst.location = (0.0, 0.0, hz_ctr)
        if not is_left:
            inst.scale = (-1.0, 1.0, 1.0)
        inst.parent = parent

    return parent


# ─────────────────────────────────────────────────────────────────────────────
def create_locking_hardware(name, width, height, is_left, floor_z_offset=0.108, num_corrugations=4):
    """All locking-mechanism geometry in one mesh tagged is_hardware = True.

    Guide brackets are now cylinder clamps (disc + mount arm) placed at the
    Z-centres of the flat background sections between corrugation ribs, so
    they never visually overlap a corrugation crest.

    The door handle is snapped to the gap centre nearest to HANDLE_HEIGHT above
    the container floor.

    Bar X positions in left-door canonical space:
        bar_x1 = width − BAR1_EDGE          (170 mm from the closing edge)
        bar_x2 = bar_x1 − BAR2_OFFSET       (420 mm from bar_x1 toward hinge)
    """
    mesh = _get_or_create_door_hardware_mesh(width, height, is_left, floor_z_offset, num_corrugations)
    return create_object_from_mesh(
        name,
        mesh,
        tag_container_part=True,
        extra_props={"is_hardware": True},
    )
