"""ISO Shipping Container – Door Geometry

Replaces the old monolithic create_door_component() with four focused builders:

    create_door_panel()       – door leaf: 160 mm frame border, 20 mm recess, horizontal ribs
    create_door_hinges()      – 4 hinge assemblies (80 mm × 700 mm spacing)
    create_locking_hardware() – bars, guides, cams, cam holders, handle  (tagged is_hardware)
    get_hinge_positions()     – helper consumed by rebuild.py for post-recess boolean cuts

Local-axis convention for ALL builders (left-door canonical space):
    X  : 0 = hinge/pivot side  →  width = free / closing edge
    Y  : 0 = outer (viewer) face  →  LEAF_T = inner face
    Z  : 0 = door bottom  →  height = door top
Right-door mirroring is a –X scale + normal flip applied once at the end of each builder.
"""

import bpy
import bmesh
import math
import mathutils

# ── Physical constants (metres) ───────────────────────────────────────────────
BORDER        = 0.160   # frame border width on all four door edges
RECESS_DEPTH  = 0.020   # recessed panel sits this far behind the frame face
RIB_HEIGHT    = 0.060   # each corrugation rib is 60 mm tall (Z)
RIB_PROTRUDE  = 0.015   # ribs protrude this far from the recess floor toward viewer
LEAF_T        = 0.040   # overall door leaf depth (Y)

HINGE_H       = 0.080   # single hinge height (80 mm)
HINGE_GAP     = 0.700   # centre-to-centre hinge spacing (700 mm)
NUM_HINGES    = 4

BAR1_EDGE     = 0.170   # first locking bar: 170 mm from the free (closing) edge
BAR2_OFFSET   = 0.420   # second bar: 420 mm from the first bar

HANDLE_HEIGHT = 0.900   # desired handle grip height from container floor (world Z = 0)


# ── Private mesh helpers ───────────────────────────────────────────────────────

def _b(bm, sx, sy, sz, cx=0.0, cy=0.0, cz=0.0):
    """Append a box (size sx × sy × sz, centred at cx, cy, cz) to *bm*."""
    g = bmesh.ops.create_cube(bm, size=1.0)
    bmesh.ops.scale(bm,     verts=g['verts'], vec=(sx, sy, sz))
    bmesh.ops.translate(bm, verts=g['verts'], vec=(cx, cy, cz))


def _cyl(bm, r, length, cx=0.0, cy=0.0, cz=0.0, axis='Z', segs=8):
    """Append a cylinder (radius *r*, length along *axis*) to *bm*."""
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
    """Mirror geometry through X = 0 and fix normals (right-door mirroring)."""
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
    """Return Z coordinates (bottom of each hinge) for NUM_HINGES hinges,
    spaced HINGE_GAP apart and centred vertically on the door."""
    span    = (NUM_HINGES - 1) * HINGE_GAP
    z_start = max(0.0, (door_height - span) * 0.5)
    return [z_start + i * HINGE_GAP for i in range(NUM_HINGES)]


# ── Public API ─────────────────────────────────────────────────────────────────

def get_hinge_positions(door_height):
    """Exposed wrapper used by rebuild.py to align post-recess boolean cuts."""
    return _hinge_z_positions(door_height)


# ──────────────────────────────────────────────────────────────────────────────
def create_door_panel(name, width, height, is_left):
    """Door leaf composed of three layers:

    1. Door body   – full XZ extent, y = RECESS_DEPTH → LEAF_T  (recessed from face)
    2. Frame rails – y = 0 → RECESS_DEPTH, 160 mm wide on all four sides
    3. Ribs        – horizontal corrugation strips inside the recessed area,
                     protruding outward (toward viewer) from the recess floor
                     by RIB_PROTRUDE.  3–5 ribs: one at top, one at bottom,
                     the rest equally spaced in between.
    """
    obj, mesh = _make_obj(name)
    bm = bmesh.new()

    rd  = RECESS_DEPTH
    lt  = LEAF_T
    bdr = BORDER
    rp  = RIB_PROTRUDE

    # Inner panel bounds (area behind the frame border)
    iX0 = bdr
    iX1 = max(bdr + 0.010, width  - bdr)
    iZ0 = bdr
    iZ1 = max(bdr + 0.010, height - bdr)
    iW  = iX1 - iX0
    iH  = iZ1 - iZ0

    body_t  = lt - rd               # thickness of the body behind the recess floor
    body_cy = rd + body_t * 0.5     # Y centre of the body slab

    # ── 1. Door body slab ──────────────────────────────────────────────────────
    _b(bm, width, body_t, height,
       cx=width * 0.5, cy=body_cy, cz=height * 0.5)

    # ── 2. Raised frame border strips (y: 0 → rd, proud of the body) ──────────
    _b(bm, width, rd, bdr,                            # bottom rail (full width)
       cx=width * 0.5,        cy=rd * 0.5, cz=bdr * 0.5)
    _b(bm, width, rd, bdr,                            # top rail (full width)
       cx=width * 0.5,        cy=rd * 0.5, cz=height - bdr * 0.5)
    _b(bm, bdr, rd, iH,                               # left upright (hinge side)
       cx=bdr * 0.5,          cy=rd * 0.5, cz=(iZ0 + iZ1) * 0.5)
    _b(bm, bdr, rd, iH,                               # right upright (free edge)
       cx=width - bdr * 0.5,  cy=rd * 0.5, cz=(iZ0 + iZ1) * 0.5)

    # ── 3. Corrugation ribs ────────────────────────────────────────────────────
    #  Rib outer face at y = rd – rp  (protruding outward from recess floor at rd)
    #  3–5 ribs: 1 at bottom, 1 at top, the remainder equally spaced in between.
    num_ribs = max(3, min(5, 2 + int(iH / 0.600)))

    rib_z_list = [iZ0]
    for i in range(1, num_ribs - 1):
        t = i / (num_ribs - 1)
        rib_z_list.append(iZ0 + t * iH - RIB_HEIGHT * 0.5)
    rib_z_list.append(iZ1 - RIB_HEIGHT)

    # Clamp and deduplicate
    rib_z_list = sorted({max(iZ0, min(z, iZ1 - RIB_HEIGHT)) for z in rib_z_list})

    for rz in rib_z_list:
        rh_actual = min(RIB_HEIGHT, iZ1 - rz)
        if rh_actual < 0.005:
            continue
        _b(bm, iW, rp, rh_actual,
           cx=iX0 + iW * 0.5,
           cy=rd - rp * 0.5,        # protrudes toward viewer from recess floor
           cz=rz + rh_actual * 0.5)

    # ── Mirror + normals ───────────────────────────────────────────────────────
    if not is_left:
        _mirror(bm)

    if bm.faces:
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces)

    bm.to_mesh(mesh)
    bm.free()
    return obj


# ──────────────────────────────────────────────────────────────────────────────
def create_door_hinges(name, width, height, is_left):
    """4 hinge assemblies, each 80 mm tall, spaced 700 mm centre-to-centre,
    vertically centred on the door.

    Each assembly comprises:
      • door leaf  – plate on the outer face, extending +55 mm in X onto the door
      • post leaf  – plate extending –45 mm in X into the post recess
      • knuckles   – 3 short cylinders at the pivot axis (X = 0)
      • pin        – full-height cylinder through the knuckles
    """
    obj, mesh = _make_obj(name)
    bm = bmesh.new()

    hh      = HINGE_H
    door_lw = 0.055         # door-leaf X extent (onto door body)
    post_lw = 0.045         # post-leaf X extent (into post recess)
    lt      = 0.010         # plate thickness
    pin_r   = 0.008         # pin radius
    knk_r   = 0.014         # knuckle radius (slightly wider than pin)
    # Y position: leaves sit just outside the outer door face
    y_leaf  = -lt

    for hz_bot in _hinge_z_positions(height):
        hz = hz_bot + hh * 0.5

        # Door leaf (positive X from pivot)
        _b(bm, door_lw, lt, hh,
           cx=door_lw * 0.5, cy=y_leaf - lt * 0.5, cz=hz)

        # Post leaf (negative X from pivot)
        _b(bm, post_lw, lt, hh,
           cx=-post_lw * 0.5, cy=y_leaf - lt * 0.5, cz=hz)

        # 3 knuckles distributed along the hinge height
        for kz_off in (-hh * 0.33, 0.0, hh * 0.33):
            _cyl(bm, knk_r, lt * 2.5,
                 cx=0.0, cy=y_leaf - lt * 0.5, cz=hz + kz_off, axis='Z')

        # Central pin (90 % of hinge height to stay inside knuckles)
        _cyl(bm, pin_r, hh * 0.90,
             cx=0.0, cy=y_leaf - lt * 0.5, cz=hz, axis='Z')

    if not is_left:
        _mirror(bm)

    if bm.faces:
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces)

    bm.to_mesh(mesh)
    bm.free()
    return obj


# ──────────────────────────────────────────────────────────────────────────────
def create_locking_hardware(name, width, height, is_left, floor_z_offset=0.108):
    """All locking mechanism geometry in a single mesh tagged *is_hardware = True*.

    Includes:
      • 2 vertical locking bars (rods)
      • Guide brackets evenly spaced along each bar
      • Cam disc + cam holder bracket at top and bottom of each bar
      • Handle assembly (mounting plate, grip rod, grip arms, latch body)

    Bar X positions in left-door canonical space:
      bar_x1 = width – BAR1_EDGE             (170 mm from the free/closing edge)
      bar_x2 = bar_x1 – BAR2_OFFSET          (420 mm from bar_x1 toward hinge)

    Handle grip Z is placed at (HANDLE_HEIGHT – floor_z_offset) in door-local Z,
    so the grip sits at ~900 mm from the container floor in world space.

    floor_z_offset  the world-Z of the door pivot / door bottom (= cz + rh/2).
    """
    obj, mesh = _make_obj(name, is_hardware=True)
    bm = bmesh.new()

    bar_r   = 0.016     # locking bar rod radius
    bar_ext = 0.040     # bars extend beyond door top / bottom
    y_bar   = -0.022    # bars proud of outer door face (–Y)

    # Guide bracket dims (width, height, depth)
    gw, gh, gd = 0.050, 0.040, 0.030
    # Cam disc + holder dims
    cam_r, cam_t = 0.032, 0.018
    chw, chh, chd = 0.080, 0.058, 0.036

    # Bar X positions (from hinge side x = 0)
    bar_x1 = max(0.010, width - BAR1_EDGE)
    bar_x2 = max(0.010, bar_x1 - BAR2_OFFSET)
    bar_xs = [bx for bx in (bar_x1, bar_x2) if 0.010 < bx < width - 0.010]

    for bx in bar_xs:

        # ── Locking rod ───────────────────────────────────────────────────────
        _cyl(bm, bar_r, height + 2 * bar_ext,
             cx=bx, cy=y_bar, cz=height * 0.5, axis='Z', segs=10)

        # ── Guide brackets (evenly spaced) ────────────────────────────────────
        n_guides = max(3, int(height / 0.520) + 1)
        for i in range(n_guides):
            gz = (i + 0.5) * height / n_guides
            _b(bm, gw, gd, gh, cx=bx, cy=y_bar - gd * 0.5, cz=gz)

        # ── Cam disc + cam holder at top and bottom of bar ────────────────────
        for cz_cam in (0.030, height - 0.030):
            # Cam disc (cylindrical, axis = Y so it rotates the bar)
            _cyl(bm, cam_r, cam_t,
                 cx=bx, cy=y_bar, cz=cz_cam, axis='Y', segs=10)
            # Cam holder bracket (fixed mounting block)
            _b(bm, chw, chd, chh,
               cx=bx, cy=y_bar - chd * 0.5, cz=cz_cam)

    # ── Handle assembly (on bar_x1) ───────────────────────────────────────────
    if bar_xs:
        bx = bar_xs[0]
        # door-local Z where the handle grip sits (= world 900 mm from floor)
        hz = max(0.050, HANDLE_HEIGHT - floor_z_offset)

        # Mounting plate (vertical, centred on handle zone)
        _b(bm, 0.120, 0.012, 0.260,
           cx=bx, cy=y_bar - 0.006, cz=hz)

        # Grip rod (horizontal cylinder the user grabs)
        _cyl(bm, 0.014, 0.115,
             cx=bx, cy=y_bar - 0.065, cz=hz, axis='Y', segs=8)

        # Two short arms connecting plate to grip rod
        for dz in (-0.080, 0.080):
            _b(bm, 0.020, 0.060, 0.018,
               cx=bx, cy=y_bar - 0.034, cz=hz + dz)

        # Latch body (lower part of the handle assembly)
        _b(bm, 0.062, 0.032, 0.065,
           cx=bx, cy=y_bar - 0.016, cz=hz - 0.100)

    if not is_left:
        _mirror(bm)

    if bm.faces:
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces)

    bm.to_mesh(mesh)
    bm.free()
    return obj
