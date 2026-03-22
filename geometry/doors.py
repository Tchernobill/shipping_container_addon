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

# ── Physical constants (metres) ───────────────────────────────────────────────
FRAME_T = 0.150   # top / bottom rail height (Z)
FRAME_S = 0.100   # left / right stile width (X)

CORR_OUTSIDE = 0.134                               # outer corrugation pitch
CORR_INSIDE  = 0.070                               # inner flat (rib bottom) width
CORR_SLOPE   = (CORR_OUTSIDE - CORR_INSIDE) / 2   # = 0.032 m each slope
CORR_DEPTH   = 0.045                               # recess depth from frame face

LEAF_T     = 0.060   # total door leaf thickness (Y axis)

HINGE_H    = 0.080   # single hinge plate height
HINGE_GAP  = 0.700   # centre-to-centre hinge spacing
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


def _hinge_z_positions(door_height):
    """Return Z of the *bottom* of each hinge, NUM_HINGES total, centred on door."""
    span    = (NUM_HINGES - 1) * HINGE_GAP
    z_start = max(0.0, (door_height - span) * 0.5)
    return [z_start + i * HINGE_GAP for i in range(NUM_HINGES)]


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
        z += CORR_SLOPE;  pts.append((z, CORR_DEPTH))
        # Inner flat at rib bottom (deepest point)
        z += CORR_INSIDE; pts.append((z, CORR_DEPTH))
        # Slope back out to flush face
        z += CORR_SLOPE;  pts.append((z, 0.0))
        # Full gap between ribs; trailing half-gap after last rib
        gap = space if (i < n - 1) else space * 0.5
        z  += gap;        pts.append((z, 0.0))

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
      • Forward path : corrugation profile  z0 → z0+panel_h  (varying y)
      • Closing path : straight line at y = LEAF_T            (door back face)

    The profile is swept from x = x0 (hinge side) to x = x1 (closing edge).
    Left and right faces are n-gon caps; Blender's ear-clipping handles the
    non-convex corrugation shape correctly at tessellation time.
    """
    fwd  = _corr_profile(z0, panel_h, n_corr)

    # Close the cross-section at the back of the door leaf
    loop = fwd + [
        (fwd[-1][0], LEAF_T),   # back-top    corner  (z=z0+panel_h, y=LEAF_T)
        (fwd[0][0],  LEAF_T),   # back-bottom corner  (z=z0,         y=LEAF_T)
    ]
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

def get_hinge_positions(door_height):
    """Exposed wrapper: used by rebuild.py to position hinge-recess boolean cuts."""
    return _hinge_z_positions(door_height)


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
    obj, mesh = _make_obj(name)
    bm = bmesh.new()

    dt = LEAF_T   # door leaf thickness along Y

    # Center panel area in door-local coordinates
    px0     = FRAME_S
    px1     = width  - FRAME_S
    pz0     = FRAME_T
    pz1     = height - FRAME_T
    panel_w = px1 - px0
    panel_h = pz1 - pz0

    # ── Perimeter frame boxes ──────────────────────────────────────────────────
    # Bottom rail (full door width)
    _b(bm, width,   dt, FRAME_T,
       cx=width * 0.5,          cy=dt * 0.5, cz=FRAME_T * 0.5)
    # Top rail
    _b(bm, width,   dt, FRAME_T,
       cx=width * 0.5,          cy=dt * 0.5, cz=height - FRAME_T * 0.5)
    # Left stile (hinge side)
    _b(bm, FRAME_S, dt, panel_h,
       cx=FRAME_S * 0.5,        cy=dt * 0.5, cz=pz0 + panel_h * 0.5)
    # Right stile (closing edge)
    _b(bm, FRAME_S, dt, panel_h,
       cx=width - FRAME_S * 0.5, cy=dt * 0.5, cz=pz0 + panel_h * 0.5)

    # ── Corrugated center panel (ribs run horizontally) ───────────────────────
    if panel_w > 0.020 and panel_h > 0.020:
        _add_corrugated_strip(bm, px0, px1, pz0, panel_h, num_corrugations)

    # ── Mirror for right door ──────────────────────────────────────────────────
    if not is_left:
        _mirror(bm)

    if bm.faces:
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces)

    bm.to_mesh(mesh)
    bm.free()
    return obj


# ─────────────────────────────────────────────────────────────────────────────
def create_door_hinges(name, width, height, is_left):
    """Four hinge assemblies, 80 mm tall, 700 mm centre-to-centre, vertically
    centred on the door height.

    Each assembly:
      • Door leaf  – plate +55 mm in X onto door face
      • Post leaf  – plate −45 mm in X into post recess
      • Knuckles   – 3 short cylinders at the pivot axis (X = 0)
      • Pin        – full-height cylinder through all knuckles
    """
    obj, mesh = _make_obj(name)
    bm = bmesh.new()

    hh      = HINGE_H
    door_lw = 0.055
    post_lw = 0.045
    lt      = 0.010
    pin_r   = 0.008
    knk_r   = 0.014
    y_leaf  = -lt   # hinge leaves proud of the outer door face (Y = 0)

    for hz_bot in _hinge_z_positions(height):
        hz = hz_bot + hh * 0.5

        _b(bm, door_lw, lt, hh, cx=door_lw * 0.5,  cy=y_leaf - lt * 0.5, cz=hz)
        _b(bm, post_lw, lt, hh, cx=-post_lw * 0.5, cy=y_leaf - lt * 0.5, cz=hz)

        for kz_off in (-hh * 0.33, 0.0, hh * 0.33):
            _cyl(bm, knk_r, lt * 2.5,
                 cx=0.0, cy=y_leaf - lt * 0.5, cz=hz + kz_off, axis='Z')

        _cyl(bm, pin_r, hh * 0.90,
             cx=0.0, cy=y_leaf - lt * 0.5, cz=hz, axis='Z')

    if not is_left:
        _mirror(bm)
    if bm.faces:
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(mesh)
    bm.free()
    return obj


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
    obj, mesh = _make_obj(name, is_hardware=True)
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
        # A short Z-axis cylinder forms a clamp collar encircling the bar,
        # with a small mounting tab connecting it to the door face.
        for gz in gap_zs:
            # Collar: short cylinder along Z encircling the bar
            _cyl(bm, 0.028, 0.060,
                 cx=bx, cy=y_bar, cz=gz, axis='Z', segs=12)
            # Mounting tab: small block from door face to collar back
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

        # Mounting plate
        _b(bm, 0.120, 0.012, 0.260, cx=bx, cy=y_bar - 0.006, cz=hz)
        # Grip rod (horizontal cylinder, the user grabs)
        _cyl(bm, 0.014, 0.115,
             cx=bx, cy=y_bar - 0.065, cz=hz, axis='Y', segs=8)
        # Two short arms connecting plate to grip rod
        for dz in (-0.080, 0.080):
            _b(bm, 0.020, 0.060, 0.018, cx=bx, cy=y_bar - 0.034, cz=hz + dz)
        # Latch body
        _b(bm, 0.062, 0.032, 0.065, cx=bx, cy=y_bar - 0.016, cz=hz - 0.100)

    if not is_left:
        _mirror(bm)
    if bm.faces:
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(mesh)
    bm.free()
    return obj
