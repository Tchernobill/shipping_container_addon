"""systems/materials.py
ISO Container procedural materials — Blender 5.0+

ISO_Container_Metal  ·  v6 shader (attribute-driven controls)
──────────────────────────────────────────────────────────────
v6 upgrades over v5
────────────────────
  [Priority 1]  Wave-based scratches  (replaces noise-blob §9)
    WaveTexture (BANDS, DIAGONAL) rotated -85° on X gives true
    horizontal cargo scratches.  A 4-D seed-driven noise distorts
    them so they are not perfectly parallel.  Result: scratches that
    look like forklift straps and sliding cargo rather than random
    blobs.

  [Priority 2]  Three-BSDF mixing  (extends §11)
    BSDF_Worn (bare steel) sits between BSDF_Paint and BSDF_Rust.
    It is blended in by the edge-detection mask so areas where paint
    chips first expose warm grey bare metal before full orange rust.

  [Priority 3]  Edge roughness output  (extends §11)
    The edge mask (cr_edge) adds up to +0.30 roughness at sharp
    edges, making them visibly more matte even when not yet rusted
    — physically: chipped paint edges are micro-rough.

Everything else is identical to v5.

Object custom properties used by this shader
─────────────────────────────────────────────
  container_seed           float 0–1   colour + weathering pattern
  shader_rust_strength     float 0–2   edge rust amount         (default 0.35)
  shader_stain_intensity   float 0–1   water stains             (default 0.60)
  shader_dust_intensity    float 0–1   dust / grime             (default 0.65)
  shader_scratch_intensity float 0–1   horizontal scratches     (default 0.25)
  shader_color_override_amt float 0–1  blend toward manual col  (default 0.00)
  shader_color_override    float[4]    manual RGBA paint colour (default warm red)

All stamped onto every metal mesh child by rebuild.py and
update_shader_props() in properties.py.
"""

import bpy


# ─────────────────────────────────────────────────────────────────────
#  Shared helpers
# ─────────────────────────────────────────────────────────────────────

def hex_to_linear_rgba(hex_str):
    """sRGB hex string → linear-space RGBA tuple."""
    hex_str = hex_str.lstrip('#')
    if len(hex_str) == 8:
        r, g, b, a = (int(hex_str[i:i+2], 16) / 255.0 for i in (0, 2, 4, 6))
    else:
        r, g, b = (int(hex_str[i:i+2], 16) / 255.0 for i in (0, 2, 4))
        a = 1.0
    def s2l(c):
        return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4
    return (s2l(r), s2l(g), s2l(b), a)


# ─────────────────────────────────────────────────────────────────────
#  v6 shader constants
# ─────────────────────────────────────────────────────────────────────

_MAT_NAME   = "ISO_Container_Metal"
_GROUP_NAME = "ISO_Container_Shader"

_Z_BOTTOM = 0.0     # world Z at container floor
_Z_TOP    = 2.591   # world Z at container roof (ISO 668 standard height)
_Z_MID    = 1.295   # midpoint

# Per-noise prime W-offset scales.  Each noise uses a different prime so
# its pattern is decorrelated from the others even with one shared seed.
_W_SCALE = {
    "N_Roughness"  :  7.31,
    "N_Specular"   : 13.73,
    "N_RustPat"    :  5.03,
    "N_RustBump"   : 17.39,
    "N_Stain"      : 11.93,
    "N_Dust"       :  3.71,
    # v6: N_Scratch now drives the wave-distortion noise W offset
    "N_Scratch"    : 19.13,
}
_W_BASE = {
    "N_Roughness"  :  3.0,
    "N_Specular"   :  1.0,
    "N_RustPat"    :  0.0,
    "N_RustBump"   :  0.0,
    "N_Stain"      :  0.0,
    "N_Dust"       :  0.0,
    "N_Scratch"    :  0.0,
}

# 8-colour constant palette — each stop is one of the main container colours.
# CR_Palette (CONSTANT interpolation) snaps to the nearest stop.
_PALETTE = [
    (0.000, (0.021, 0.095, 0.270, 1.0)),   # dark navy
    (0.125, (0.007, 0.022, 0.056, 1.0)),   # very dark blue
    (0.250, (0.027, 0.133, 0.381, 1.0)),   # mid blue
    (0.375, (0.292, 0.047, 0.026, 1.0)),   # dark red
    (0.500, (0.184, 0.032, 0.019, 1.0)),   # standard red
    (0.625, (0.120, 0.022, 0.014, 1.0)),   # deep red
    (0.750, (0.009, 0.061, 0.006, 1.0)),   # evergreen
    (0.875, (0.216, 0.216, 0.216, 1.0)),   # steel grey
]


# ─────────────────────────────────────────────────────────────────────
#  Private node-graph helpers
# ─────────────────────────────────────────────────────────────────────

def _nd(nodes, typ, name, loc, **attrs):
    """Create a new node, set name/label/location, apply extra attrs."""
    n = nodes.new(typ)
    n.name = n.label = name
    n.location = loc
    for k, v in attrs.items():
        setattr(n, k, v)
    return n


def _attr_obj(nodes, node_name, attr_name, loc):
    """ShaderNodeAttribute that reads a named object custom property."""
    n = _nd(nodes, "ShaderNodeAttribute", node_name, loc)
    n.attribute_type = 'OBJECT'
    n.attribute_name = attr_name
    return n


def _noise(nodes, name, loc, *,
           ntype='FBM', normalize=True,
           scale=5.0, detail=8.0, rough=0.6, lac=2.0,
           w_sock=None, w_base=0.0):
    """4-D ShaderNodeTexNoise.  w_sock wires the per-instance W offset."""
    n = _nd(nodes, "ShaderNodeTexNoise", name, loc)
    n.noise_dimensions        = '4D'
    n.noise_type              = ntype
    n.normalize               = normalize
    n.inputs[2].default_value = scale
    n.inputs[3].default_value = detail
    n.inputs[4].default_value = rough
    n.inputs[5].default_value = lac
    n.inputs[1].default_value = w_base
    if w_sock is not None:
        nodes.id_data.links.new(w_sock, n.inputs[1])
    return n


def _make_w_sock(nodes, noise_name, seed_sock, loc_base):
    """Build W = W_BASE + seed × W_SCALE and return the ADD output socket."""
    lx, ly = loc_base[0] - 350, loc_base[1]
    mul = _nd(nodes, "ShaderNodeMath", f"W_Mul_{noise_name}", (lx, ly + 60),
              operation='MULTIPLY')
    nodes.id_data.links.new(seed_sock, mul.inputs[0])
    mul.inputs[1].default_value = _W_SCALE[noise_name]
    add = _nd(nodes, "ShaderNodeMath", f"W_Add_{noise_name}", (lx, ly - 60),
              operation='ADD')
    add.inputs[0].default_value = _W_BASE[noise_name]
    nodes.id_data.links.new(mul.outputs[0], add.inputs[1])
    return add.outputs[0]


def _color_ramp(nodes, name, loc, stops, interp='LINEAR'):
    """Create a ValToRGB node with explicit colour stops."""
    n = _nd(nodes, "ShaderNodeValToRGB", name, loc)
    n.color_ramp.interpolation = interp
    els = n.color_ramp.elements
    while len(els) > 1:
        els.remove(els[-1])
    els[0].position = stops[0][0]
    els[0].color    = stops[0][1]
    for pos, col in stops[1:]:
        els.new(pos).color = col
    return n


def _mapping(nodes, name, loc, scale=(1.0, 1.0, 1.0)):
    """Mapping node (POINT type) with a preset scale."""
    n = _nd(nodes, "ShaderNodeMapping", name, loc, vector_type='POINT')
    n.inputs[3].default_value = scale
    return n


def _math(nodes, name, loc, op, v0=None, v1=None, clamp=False):
    """Math node with optional constant defaults on inputs 0 and 1."""
    n = _nd(nodes, "ShaderNodeMath", name, loc,
            operation=op, use_clamp=clamp)
    if v0 is not None: n.inputs[0].default_value = v0
    if v1 is not None: n.inputs[1].default_value = v1
    return n


def _mix_rgba(nodes, name, loc, mode, fac=None, b_col=None):
    """Mix RGBA node (UNIFORM factor mode)."""
    n = _nd(nodes, "ShaderNodeMix", name, loc,
            blend_type=mode, data_type='RGBA',
            factor_mode='UNIFORM', clamp_factor=True)
    if fac   is not None: n.inputs[0].default_value = fac
    if b_col is not None: n.inputs[7].default_value = b_col
    return n


def _map_range(nodes, name, loc, lo_in, hi_in, lo_out, hi_out):
    """MapRange node (clamped)."""
    n = _nd(nodes, "ShaderNodeMapRange", name, loc, clamp=True)
    n.inputs[1].default_value = lo_in;  n.inputs[2].default_value = hi_in
    n.inputs[3].default_value = lo_out; n.inputs[4].default_value = hi_out
    return n


def _principled(nodes, name, loc):
    """Principled BSDF with MULTI_GGX distribution and RANDOM_WALK SSS."""
    n = nodes.new("ShaderNodeBsdfPrincipled")
    n.name = n.label = name
    n.location = loc
    n.distribution      = 'MULTI_GGX'
    n.subsurface_method = 'RANDOM_WALK'
    n.inputs[4].default_value  = 1.0   # Alpha
    n.inputs[28].default_value = 0.0   # Emission Strength
    return n


# ─────────────────────────────────────────────────────────────────────
#  v6 Shader group builder
# ─────────────────────────────────────────────────────────────────────

def _build_shader_group():
    """Build the ISO_Container_Shader v6 node group.

    All user-facing controls are read from object custom properties via
    ShaderNodeAttribute (attribute_type='OBJECT') — no group inputs.
    The group interface exposes only the single Shader output socket.
    """
    grp = bpy.data.node_groups.new(_GROUP_NAME, 'ShaderNodeTree')
    N   = grp.nodes
    def L(a, b): grp.links.new(a, b)

    # Single output — everything is driven by per-object attributes
    grp.interface.new_socket("Shader", in_out='OUTPUT',
                              socket_type='NodeSocketShader')
    go = _nd(N, "NodeGroupOutput", "GroupOutput", (2800, 0))

    # ── §1  Coordinates ───────────────────────────────────────────────
    tc  = _nd(N, "ShaderNodeTexCoord",    "TexCoord", (-2800, 300))
    tc.from_instancer = False

    # World-space position — height-based effects (dust, stains) must use
    # world Z so the gradient is consistent regardless of each mesh child's
    # local origin.
    geo_coord = _nd(N, "ShaderNodeNewGeometry", "GeoCoord", (-3000, -100))

    sep = _nd(N, "ShaderNodeSeparateXYZ", "SepXYZ",  (-2800, -100))
    L(geo_coord.outputs[0], sep.inputs[0])   # world Position → separate Z

    mp  = _mapping(N, "Mapping", (-2500, 0))
    L(tc.outputs[3], mp.inputs[0])           # object coords for noise patterns
    vmp = mp.outputs[0]

    # ── §2  Seed ← 'container_seed' object attribute ──────────────────
    # One Attribute node drives everything that varies per container:
    #   • colour palette selection
    #   • W offset of every 4-D noise (pattern uniqueness)
    attr_seed = _attr_obj(N, "Attr_Seed", "container_seed", (-2800, 700))
    seed_fac  = attr_seed.outputs[2]   # Fac (0–1 float)

    # ── §3  Per-container shader controls ← object custom properties ──
    # These replace the old group inputs.  Values are stamped onto every
    # metal mesh child by rebuild.py and update_shader_props().
    attr_rust    = _attr_obj(N, "Attr_Rust",    "shader_rust_strength",      (-3200,  -700))
    attr_stain_i = _attr_obj(N, "Attr_StainI",  "shader_stain_intensity",    (-3200,  -800))
    attr_dust_i  = _attr_obj(N, "Attr_DustI",   "shader_dust_intensity",     (-3200,  -900))
    attr_scratch = _attr_obj(N, "Attr_Scratch", "shader_scratch_intensity",  (-3200, -1000))
    attr_col_ovr = _attr_obj(N, "Attr_ColOvr",  "shader_color_override",     (-3200, -1100))
    attr_col_amt = _attr_obj(N, "Attr_ColAmt",  "shader_color_override_amt", (-3200, -1200))

    rust_sock    = attr_rust.outputs[2]      # Fac → rust multiplier
    stain_i_sock = attr_stain_i.outputs[2]  # Fac → stain intensity
    dust_i_sock  = attr_dust_i.outputs[2]   # Fac → dust intensity
    scratch_sock = attr_scratch.outputs[2]  # Fac → scratch intensity
    col_ovr_sock = attr_col_ovr.outputs[0]  # Color → paint override colour
    col_amt_sock = attr_col_amt.outputs[2]  # Fac → override blend amount

    # ── §4  Base paint colour — palette indexed by seed ────────────────
    # CONSTANT interpolation snaps to nearest stop → 8 distinct colours
    cr_pal = _color_ramp(N, "CR_Palette", (-2500, 700), _PALETTE, 'CONSTANT')
    L(seed_fac, cr_pal.inputs[0])
    paint_color = cr_pal.outputs[0]

    # ── §5  Roughness & Specular variation (4-D, per-instance W) ──────
    w_rough = _make_w_sock(N, "N_Roughness", seed_fac, (-1700, 350))
    n_rough = _noise(N, "N_Roughness", (-1700, 350),
                     scale=3.5, detail=15.0, rough=0.76,
                     w_sock=w_rough, w_base=_W_BASE["N_Roughness"])
    L(vmp, n_rough.inputs[0])
    cr_rough = _color_ramp(N, "CR_Roughness", (-1400, 350),
        [(0.0, (0.36, 0.36, 0.36, 1.0)), (1.0, (1.0, 1.0, 1.0, 1.0))], 'EASE')
    L(n_rough.outputs[0], cr_rough.inputs[0])

    w_spec = _make_w_sock(N, "N_Specular", seed_fac, (-1700, 50))
    n_spec = _noise(N, "N_Specular", (-1700, 50),
                    scale=5.0, detail=10.0, rough=0.76,
                    w_sock=w_spec, w_base=_W_BASE["N_Specular"])
    L(vmp, n_spec.inputs[0])
    cr_spec = _color_ramp(N, "CR_Specular", (-1400, 50),
        [(0.0, (0.36, 0.36, 0.36, 1.0)), (1.0, (1.0, 1.0, 1.0, 1.0))], 'EASE')
    L(n_spec.outputs[0], cr_spec.inputs[0])

    # ── §6  Rust system (4-D, per-instance W on both noises) ──────────
    # Edge detection: dot product of surface normal with bevelled normal.
    # High values = flat; low values approaching 1 = sharp edges.
    geo = _nd(N, "ShaderNodeNewGeometry", "Geometry_Normals", (-2800, -400))
    bev = _nd(N, "ShaderNodeBevel",       "Bevel",            (-2800, -650))
    bev.samples = 4; bev.inputs[0].default_value = 0.05

    vm_dot = _nd(N, "ShaderNodeVectorMath", "VM_Dot", (-2500, -510),
                 operation='DOT_PRODUCT')
    L(geo.outputs[1], vm_dot.inputs[0])   # surface normal
    L(bev.outputs[0], vm_dot.inputs[1])   # bevelled normal

    # cr_edge: white where edges are sharpest, black on flat surfaces
    # Used in §11 for: (a) worn-metal blend, (b) edge roughness bump
    cr_edge = _color_ramp(N, "CR_EdgeMask", (-2200, -510),
        [(0.954, (1.0, 1.0, 1.0, 1.0)),
         (1.000, (0.0, 0.0, 0.0, 1.0))], 'CARDINAL')
    L(vm_dot.outputs[1], cr_edge.inputs[0])

    # Rust pattern — MULTIFRACTAL noise shaped by a ramp
    w_rp = _make_w_sock(N, "N_RustPat", seed_fac, (-1700, -800))
    n_rp = _noise(N, "N_RustPat", (-1700, -800),
                  ntype='MULTIFRACTAL', normalize=False,
                  scale=1.0, detail=14.0, rough=1.0, lac=1.55,
                  w_sock=w_rp, w_base=_W_BASE["N_RustPat"])
    L(vmp, n_rp.inputs[0])
    cr_rp = _color_ramp(N, "CR_RustPat", (-1400, -800),
        [(0.848, (0.0, 0.0, 0.0, 1.0)),
         (1.000, (1.0, 1.0, 1.0, 1.0))], 'LINEAR')
    L(n_rp.outputs[0], cr_rp.inputs[0])

    # Combined rust mask = edge presence × noise pattern × user strength
    mx_rust_mask = _mix_rgba(N, "MX_RustMask", (-1100, -650), 'MULTIPLY', fac=1.0)
    L(cr_edge.outputs[0], mx_rust_mask.inputs[6])
    L(cr_rp.outputs[0],   mx_rust_mask.inputs[7])

    math_rust = _math(N, "Math_Rust", (-750, -650), 'MULTIPLY')
    L(mx_rust_mask.outputs[2], math_rust.inputs[0])
    L(rust_sock,               math_rust.inputs[1])   # ← object attribute

    # Rust bump texture — drives normal + colour of rusty BSDF
    w_rb = _make_w_sock(N, "N_RustBump", seed_fac, (-1700, -1100))
    n_rb = _noise(N, "N_RustBump", (-1700, -1100),
                  scale=350.0, detail=2.0, rough=0.5,
                  w_sock=w_rb, w_base=_W_BASE["N_RustBump"])
    L(vmp, n_rb.inputs[0])
    cr_rb = _color_ramp(N, "CR_RustBump", (-1400, -1100),
        [(0.000, (1.0,   1.0,   1.0,   1.0)),
         (0.422, (0.146, 0.045, 0.016, 1.0)),
         (1.000, (0.214, 0.027, 0.020, 1.0))], 'LINEAR')
    L(n_rb.outputs[0], cr_rb.inputs[0])

    bump = _nd(N, "ShaderNodeBump", "Bump", (-500, -1000))
    bump.invert = False
    bump.inputs[0].default_value = 0.208   # Strength
    bump.inputs[1].default_value = 1.0    # Distance
    bump.inputs[2].default_value = 0.1    # Filter Width (unused but kept)
    L(cr_rb.outputs[0], bump.inputs[3])   # Height

    # ── §7  Water stains (4-D, per-instance W) ────────────────────────
    # Streaks appear on the upper half only (world Z > _Z_MID).
    mp_stain = _mapping(N, "MP_Stain", (-2200, 1300), scale=(8.0, 8.0, 0.25))
    L(tc.outputs[3], mp_stain.inputs[0])

    w_stain = _make_w_sock(N, "N_Stain", seed_fac, (-1700, 1300))
    n_stain = _noise(N, "N_Stain", (-1700, 1300),
                     scale=14.0, detail=3.0, rough=0.65,
                     w_sock=w_stain, w_base=_W_BASE["N_Stain"])
    L(mp_stain.outputs[0], n_stain.inputs[0])

    cr_stain = _color_ramp(N, "CR_Stain", (-1400, 1300),
        [(0.55, (0.0, 0.0, 0.0, 1.0)),
         (0.80, (1.0, 1.0, 1.0, 1.0))], 'LINEAR')
    L(n_stain.outputs[0], cr_stain.inputs[0])

    # Height mask: stains fade in from midpoint to top of container
    mr_stain_h = _map_range(N, "MR_StainH", (-2200, 1550), _Z_MID, _Z_TOP, 0.0, 1.0)
    L(sep.outputs[2], mr_stain_h.inputs[0])   # world Z

    cr_stain_h = _color_ramp(N, "CR_StainH", (-1900, 1550),
        [(0.0, (0.0, 0.0, 0.0, 1.0)),
         (1.0, (1.0, 1.0, 1.0, 1.0))], 'EASE')
    L(mr_stain_h.outputs[0], cr_stain_h.inputs[0])

    math_stain = _math(N, "Math_Stain", (-1100, 1400), 'MULTIPLY')
    L(cr_stain.outputs[0],   math_stain.inputs[0])
    L(cr_stain_h.outputs[0], math_stain.inputs[1])

    math_stain_i = _math(N, "Math_StainI", (-800, 1400), 'MULTIPLY')
    L(math_stain.outputs[0], math_stain_i.inputs[0])
    L(stain_i_sock,          math_stain_i.inputs[1])   # ← object attribute

    # ── §8  Dust / grime (world-Z height + AO, 4-D W) ─────────────────
    # MR_DustH: fully dusty at Z=0 (floor), gone by Z=0.5 m.
    # World-space Z ensures consistency across all mesh children.
    mr_dust_h = _map_range(N, "MR_DustH", (-2200, 1800),
                            _Z_BOTTOM, _Z_BOTTOM + 0.5, 1.0, 0.0)
    L(sep.outputs[2], mr_dust_h.inputs[0])   # world Z

    w_dust = _make_w_sock(N, "N_Dust", seed_fac, (-1700, 1800))
    n_dust = _noise(N, "N_Dust", (-1700, 1800),
                    scale=5.0, detail=4.0, rough=0.7,
                    w_sock=w_dust, w_base=_W_BASE["N_Dust"])
    L(vmp, n_dust.inputs[0])

    math_dust_h = _math(N, "Math_DustH", (-1400, 1800), 'MULTIPLY')
    L(mr_dust_h.outputs[0], math_dust_h.inputs[0])
    L(n_dust.outputs[0],    math_dust_h.inputs[1])

    cr_dust_h = _color_ramp(N, "CR_DustH", (-1100, 1800),
        [(0.00, (0.0, 0.0, 0.0, 1.0)),
         (1.00, (1.0, 1.0, 1.0, 1.0))], 'EASE')
    L(math_dust_h.outputs[0], cr_dust_h.inputs[0])

    # AO mask adds extra grime in concave / sheltered areas
    ao = _nd(N, "ShaderNodeAmbientOcclusion", "AO", (-1900, 2100))
    ao.samples = 16; ao.only_local = False; ao.inside = False
    ao.inputs[1].default_value = 1.0

    math_ao_inv = _math(N, "Math_AOInv", (-1600, 2100), 'SUBTRACT', v0=1.0)
    L(ao.outputs[1], math_ao_inv.inputs[1])

    cr_ao = _color_ramp(N, "CR_AO", (-1300, 2100),
        [(0.00, (0.0, 0.0, 0.0, 1.0)),
         (0.35, (0.0, 0.0, 0.0, 1.0)),
         (0.65, (1.0, 1.0, 1.0, 1.0)),
         (1.00, (1.0, 1.0, 1.0, 1.0))], 'EASE')
    L(math_ao_inv.outputs[0], cr_ao.inputs[0])

    # Combine height-based and AO-based dust with MAX
    math_dust_max = _math(N, "Math_DustMax", (-800, 1950), 'MAXIMUM')
    L(cr_dust_h.outputs[0], math_dust_max.inputs[0])
    L(cr_ao.outputs[0],     math_dust_max.inputs[1])

    math_dust_i = _math(N, "Math_DustI", (-500, 1950), 'MULTIPLY', clamp=True)
    L(math_dust_max.outputs[0], math_dust_i.inputs[0])
    L(dust_i_sock,              math_dust_i.inputs[1])   # ← object attribute

    # ── §9  Wave-based scratches (v6 — replaces noise-blob v5 §9) ─────
    #
    # Problem with v5: ShaderNodeTexNoise produces random blobs, not
    # directional scratches.
    #
    # v6 solution pipeline:
    #   tc.Object
    #    → VectorRotate(-85°, X)          — tilt coords so waves are horizontal
    #    → MP_Wave (scale_x = 3.6)        — stretch into long bands
    #    → WaveTexture (BANDS, DIAGONAL)  — generate angled band pattern
    #      + phase π/2                    — align result to near-horizontal
    #
    #   tc.Object → MP_ScratchCoord (slight rotation)
    #    → SepXYZ → CombineXYZ(X, wave_color, Z) — replace Y with wave
    #    → N_ScratchDist (4-D, FBM, seed W)       — noise distorts the bands
    #    → CR_Scratch (tight ramp, 0.68–0.82)      — extract sharp bands
    #    → Math_ScratchI × scratch_sock

    # 1. Rotate object coords so the wave normal points roughly downward
    #    → resulting bands run left-to-right (horizontal scratches)
    vec_rot_scratch = _nd(N, "ShaderNodeVectorRotate", "VecRot_Scratch",
                          (-2800, 2800), rotation_type='X_AXIS')
    vec_rot_scratch.inputs[3].default_value = -1.487   # ≈ -85.2° in radians
    L(tc.outputs[3], vec_rot_scratch.inputs[0])        # object coords in

    # 2. Stretch X to produce long horizontal bands (shorter Y/Z keep them thin)
    mp_wave = _mapping(N, "MP_Wave", (-2500, 2800), scale=(3.6, 1.0, 1.0))
    L(vec_rot_scratch.outputs[0], mp_wave.inputs[0])

    # 3. Wave bands — DIAGONAL + SIN profile + phase π/2 ≈ horizontal result
    wave_tex = _nd(N, "ShaderNodeTexWave", "WaveTex", (-2200, 2800),
                   wave_type='BANDS', bands_direction='DIAGONAL',
                   wave_profile='SIN')
    wave_tex.inputs[1].default_value = 1.0    # Scale
    wave_tex.inputs[2].default_value = 0.0    # Distortion (set to 0; we distort externally)
    wave_tex.inputs[3].default_value = 0.9    # Detail
    wave_tex.inputs[4].default_value = 1.0    # Detail Scale
    wave_tex.inputs[5].default_value = 0.5    # Detail Roughness
    wave_tex.inputs[6].default_value = 1.571  # Phase Offset ≈ π/2
    L(mp_wave.outputs[0], wave_tex.inputs[0])

    # 4. Distortion coord prep: slight tilt + replace Y with wave output
    #    The tilt prevents perfectly straight scratch borders, giving
    #    a more organic look matching real cargo-handling wear.
    mp_scratch_coord = _nd(N, "ShaderNodeMapping", "MP_ScratchCoord",
                            (-2800, 2500), vector_type='POINT')
    mp_scratch_coord.inputs[1].default_value = (0.0, 0.0, 0.0)          # Location
    mp_scratch_coord.inputs[2].default_value = (0.009, -0.093, -0.335)  # Rotation (slight tilt)
    mp_scratch_coord.inputs[3].default_value = (1.0, 1.0, 1.0)          # Scale
    L(tc.outputs[3], mp_scratch_coord.inputs[0])

    sep_scratch  = _nd(N, "ShaderNodeSeparateXYZ", "Sep_Scratch",  (-2500, 2500))
    L(mp_scratch_coord.outputs[0], sep_scratch.inputs[0])

    comb_scratch = _nd(N, "ShaderNodeCombineXYZ",  "Comb_Scratch", (-2200, 2550))
    L(sep_scratch.outputs[0], comb_scratch.inputs[0])   # X unchanged
    L(wave_tex.outputs[1],    comb_scratch.inputs[1])   # Y ← wave Fac (main distortion)
    L(sep_scratch.outputs[2], comb_scratch.inputs[2])   # Z unchanged

    # 5. Seed-driven distortion noise scale (range 5–8 across containers)
    math_wave_scale = _math(N, "Math_WaveScale", (-2000, 2750),
                             'MULTIPLY_ADD', v0=3.0, v1=5.0)
    L(seed_fac, math_wave_scale.inputs[0])

    # 6. 4-D distortion noise — W seeded for per-container uniqueness
    #    FBM with high detail and near-1 roughness = fine, dense texture
    #    The distorted vector (comb_scratch) drives X/Y/Z; seed drives W.
    w_scratch = _make_w_sock(N, "N_Scratch", seed_fac, (-1700, 2600))
    n_scratch_dist = _noise(N, "N_ScratchDist", (-1700, 2600),
                            ntype='FBM', normalize=False,
                            scale=5.0, detail=14.0, rough=0.999, lac=1.55,
                            w_sock=w_scratch, w_base=_W_BASE["N_Scratch"])
    L(comb_scratch.outputs[0],    n_scratch_dist.inputs[0])   # distorted vector
    L(math_wave_scale.outputs[0], n_scratch_dist.inputs[2])   # seed-driven scale

    # 7. Tight ramp — defines the width of visible scratch bands.
    #    Positions 0.68–0.82 extract a narrow band around the wave crests.
    cr_scratch = _color_ramp(N, "CR_Scratch", (-1400, 2600),
        [(0.68, (0.0, 0.0, 0.0, 1.0)),
         (0.82, (1.0, 1.0, 1.0, 1.0))], 'LINEAR')
    L(n_scratch_dist.outputs[0], cr_scratch.inputs[0])

    # 8. Scale by user intensity slider
    math_scratch_i = _math(N, "Math_ScratchI", (-1100, 2600), 'MULTIPLY')
    L(cr_scratch.outputs[0], math_scratch_i.inputs[0])
    L(scratch_sock,          math_scratch_i.inputs[1])   # ← object attribute

    # ── §10  Colour composite pipeline (unchanged from v5) ─────────────
    # Stain darkens the paint in upper areas (MULTIPLY)
    mx_stain = _mix_rgba(N, "MX_Stain", (-200, 1300), 'MULTIPLY',
                          b_col=(0.07, 0.045, 0.02, 1.0))
    L(math_stain_i.outputs[0], mx_stain.inputs[0])
    L(paint_color,             mx_stain.inputs[6])

    # Dust mixes a sandy colour into lower areas (MIX)
    mx_dust = _mix_rgba(N, "MX_Dust", (-200, 1000), 'MIX',
                         b_col=(0.38, 0.30, 0.17, 1.0))
    L(math_dust_i.outputs[0], mx_dust.inputs[0])
    L(mx_stain.outputs[2],    mx_dust.inputs[6])

    # Scratches add a light metallic sheen through the dust (SCREEN)
    mx_scratch = _mix_rgba(N, "MX_Scratch", (-200, 700), 'SCREEN',
                            b_col=(0.55, 0.50, 0.42, 1.0))
    L(math_scratch_i.outputs[0], mx_scratch.inputs[0])
    L(mx_dust.outputs[2],        mx_scratch.inputs[6])

    # Manual colour override — fully blends when override_amount = 1
    mx_override = _mix_rgba(N, "MX_Override", (-200, 400), 'MIX')
    L(col_amt_sock,           mx_override.inputs[0])   # ← object attribute (blend)
    L(mx_scratch.outputs[2],  mx_override.inputs[6])
    L(col_ovr_sock,           mx_override.inputs[7])   # ← object attribute (color)

    # ── §11  BSDFs + three-way shader mix (v6) ────────────────────────
    #
    # v6 ADDS two things to the shader output stage:
    #
    #   [Priority 3] Edge roughness bump
    #     cr_edge (white at sharp edges) × 0.30 is added to the
    #     base roughness so edges become visibly more matte even before
    #     paint fully chips off.
    #
    #   [Priority 2] BSDF_Worn — bare steel exposed at paint chips
    #     Third BSDF sits between paint and rust in the mix chain.
    #     It represents the warm grey bare steel visible at edges where
    #     paint has chipped but surface has not yet turned orange with rust.
    #
    # Three-way mixing chain:
    #   BSDF_Paint ↔ BSDF_Worn  (driven by cr_edge: edges show bare metal)
    #       ↕  Mix_Worn
    #   BSDF_Rust               (driven by math_rust: rust overlays both)
    #       ↕  Mix_Rust
    #   → Group Output

    # ── Priority 3: Edge roughness contribution ───────────────────────
    # cr_edge outputs white at the sharpest mesh edges (0.954–1.0 dot range).
    # Plugging its Color into a Math node works: Blender converts greyscale
    # Color → Float via luminance, which equals the value for achromatic colours.
    math_edge_rough_mul = _math(N, "Math_EdgeRoughMul", (-50, 500),
                                 'MULTIPLY', v1=0.30)
    L(cr_edge.outputs[0], math_edge_rough_mul.inputs[0])   # edge mask → float

    # Add edge contribution to base roughness; clamp to keep in [0, 1]
    math_edge_rough_add = _math(N, "Math_EdgeRoughAdd", (150, 500),
                                 'ADD', clamp=True)
    L(cr_rough.outputs[0],            math_edge_rough_add.inputs[0])
    L(math_edge_rough_mul.outputs[0], math_edge_rough_add.inputs[1])
    # Result: base roughness 0.36–1.0 + up to 0.30 at sharp edges, clamped ≤ 1.0

    # ── BSDF_Paint — seed-driven colour, edge-corrected roughness ─────
    bsdf_paint = _principled(N, "BSDF_Paint", (200, 600))
    bsdf_paint.inputs[1].default_value  = 0.65    # Metallic (low — it's painted)
    bsdf_paint.inputs[3].default_value  = 1.45    # IOR
    L(mx_override.outputs[2],         bsdf_paint.inputs[0])   # Base Color
    L(math_edge_rough_add.outputs[0], bsdf_paint.inputs[2])   # Roughness + edge bump
    L(cr_spec.outputs[0],             bsdf_paint.inputs[13])  # Specular IOR Level

    # ── Priority 2: BSDF_Worn — bare steel at paint chip edges ────────
    # Physical basis: where paint chips, metal is exposed.  It is:
    #   • more metallic than paint (no pigment layer)
    #   • slightly rough (micro-scratched, residual primer)
    #   • warm grey — slightly oxidised but not yet orange rust
    # Roughness inherits the edge-corrected value (freshly exposed edges are rough)
    bsdf_worn = _principled(N, "BSDF_Worn", (200, -200))
    bsdf_worn.inputs[0].default_value  = (0.25, 0.22, 0.20, 1.0)  # warm dark steel (linear)
    bsdf_worn.inputs[1].default_value  = 0.80   # high metallic — bare steel
    bsdf_worn.inputs[3].default_value  = 1.45   # IOR
    bsdf_worn.inputs[13].default_value = 0.70   # elevated specular
    L(math_edge_rough_add.outputs[0], bsdf_worn.inputs[2])   # Roughness (same as paint edges)

    # ── BSDF_Rust — unchanged from v5 ─────────────────────────────────
    bsdf_rust = _principled(N, "BSDF_Rust", (200, -700))
    bsdf_rust.inputs[1].default_value  = 0.75   # Metallic
    bsdf_rust.inputs[2].default_value  = 0.95   # Roughness (very rough — powdery rust)
    bsdf_rust.inputs[3].default_value  = 1.50   # IOR
    bsdf_rust.inputs[13].default_value = 0.08   # low specular
    L(cr_rb.outputs[0], bsdf_rust.inputs[0])    # Base Color (rust colour from bump texture)
    L(bump.outputs[0],  bsdf_rust.inputs[5])    # Normal (rust bump)

    # ── Three-way mix — Stage 1: Paint ↔ Worn at edges ────────────────
    # cr_edge is white (1.0) at sharp edges → Shader B (worn) shows there
    # cr_edge is black (0.0) on flat surfaces → Shader A (paint) dominates
    mix_worn = _nd(N, "ShaderNodeMixShader", "Mix_Worn", (550, 200))
    L(cr_edge.outputs[0],   mix_worn.inputs[0])   # factor = edge mask
    L(bsdf_paint.outputs[0], mix_worn.inputs[1])  # Shader A: fresh paint
    L(bsdf_worn.outputs[0],  mix_worn.inputs[2])  # Shader B: bare steel at edges

    # ── Three-way mix — Stage 2: [Paint/Worn] ↔ Rust ──────────────────
    # math_rust drives the rust overlay over whichever surface state exists.
    # Rust appearing at edges is physically correct: edges chip and rust first.
    mix_rust = _nd(N, "ShaderNodeMixShader", "Mix_Rust", (750, -100))
    L(math_rust.outputs[0],  mix_rust.inputs[0])  # factor = rust mask
    L(mix_worn.outputs[0],   mix_rust.inputs[1])  # Shader A: paint/worn composite
    L(bsdf_rust.outputs[0],  mix_rust.inputs[2])  # Shader B: full rust

    L(mix_rust.outputs[0], go.inputs[0])

    return grp


# ─────────────────────────────────────────────────────────────────────
#  Public material functions
# ─────────────────────────────────────────────────────────────────────

def get_or_create_container_material():
    """Return the ISO_Container_Metal v6 material, building it if absent.

    v6 upgrades over v5:
      • Wave-based directional scratches (horizontal, cargo-realistic)
      • Three-BSDF chain: paint → worn bare steel → rust
      • Edge roughness bump (edges matte before fully rusting)

    To force full regeneration:
      bpy.data.materials.remove(bpy.data.materials['ISO_Container_Metal'])
      bpy.data.node_groups.remove(bpy.data.node_groups['ISO_Container_Shader'])
    Then rebuild any container to regenerate.
    """
    if _MAT_NAME in bpy.data.materials:
        return bpy.data.materials[_MAT_NAME]

    # Ensure the group is also fresh (no stale v5 group lingering)
    if _GROUP_NAME in bpy.data.node_groups:
        bpy.data.node_groups.remove(bpy.data.node_groups[_GROUP_NAME])

    grp = _build_shader_group()

    mat = bpy.data.materials.new(_MAT_NAME)
    mat.use_nodes             = True
    mat.blend_method          = 'HASHED'
    mat.displacement_method   = 'BUMP'
    mat.surface_render_method = 'DITHERED'

    mt = mat.node_tree
    mt.nodes.clear()

    mat_out = mt.nodes.new("ShaderNodeOutputMaterial")
    mat_out.location         = (400, 0)
    mat_out.is_active_output = True
    mat_out.target           = 'ALL'

    grp_node           = mt.nodes.new("ShaderNodeGroup")
    grp_node.node_tree = grp
    grp_node.location  = (-50, 0)
    mt.links.new(grp_node.outputs[0], mat_out.inputs[0])

    return mat


def get_or_create_wood_material():
    mat_name = "ISO_Container_Wood"
    if mat_name in bpy.data.materials:
        return bpy.data.materials[mat_name]
    mat = bpy.data.materials.new(name=mat_name)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    if bsdf:
        bsdf.inputs['Base Color'].default_value = hex_to_linear_rgba("#A67B5BFF")
        bsdf.inputs['Roughness'].default_value  = 0.8
    return mat


def get_or_create_decal_material():
    mat_name = "ISO_Container_Decal"
    if mat_name in bpy.data.materials:
        return bpy.data.materials[mat_name]
    mat = bpy.data.materials.new(name=mat_name)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    if bsdf:
        bsdf.inputs['Base Color'].default_value = (0.9, 0.9, 0.9, 1.0)
        bsdf.inputs['Roughness'].default_value  = 0.4
        bsdf.inputs['Metallic'].default_value   = 0.0
    return mat


def get_or_create_hardware_material():
    """Mid-grey metallic for locking bars, hinges, guides, and cam hardware."""
    mat_name = "ISO_Container_Hardware"
    if mat_name in bpy.data.materials:
        return bpy.data.materials[mat_name]
    mat = bpy.data.materials.new(name=mat_name)
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    nodes.clear()
    out  = nodes.new('ShaderNodeOutputMaterial'); out.location  = (300, 0)
    bsdf = nodes.new('ShaderNodeBsdfPrincipled'); bsdf.location = (0,   0)
    bsdf.inputs['Base Color'].default_value = (0.35, 0.35, 0.35, 1.0)
    bsdf.inputs['Roughness'].default_value  = 0.40
    bsdf.inputs['Metallic'].default_value   = 0.85
    links.new(bsdf.outputs['BSDF'], out.inputs['Surface'])
    return mat


def get_or_create_brand_material(company_name, hex_color):
    """Flat-colour Principled BSDF for shipping-company logo text."""
    mat_name = f"ISO_Brand_{company_name.replace(' ', '_')}"
    if mat_name in bpy.data.materials:
        return bpy.data.materials[mat_name]
    mat = bpy.data.materials.new(name=mat_name)
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    nodes.clear()
    out  = nodes.new('ShaderNodeOutputMaterial'); out.location  = (300, 0)
    bsdf = nodes.new('ShaderNodeBsdfPrincipled'); bsdf.location = (0,   0)
    bsdf.inputs['Base Color'].default_value = hex_to_linear_rgba(hex_color)
    bsdf.inputs['Roughness'].default_value  = 0.50
    bsdf.inputs['Metallic'].default_value   = 0.0
    links.new(bsdf.outputs['BSDF'], out.inputs['Surface'])
    return mat


def get_or_create_proxy_image(name, color, is_data=False):
    if name in bpy.data.images:
        return bpy.data.images[name]
    img = bpy.data.images.new(name, width=1024, height=1024)
    img.generated_color = color
    if is_data:
        img.colorspace_settings.name = 'Non-Color'
    return img


def get_or_create_proxy_material():
    """Low-poly proxy material driven by container_seed for colour consistency."""
    mat_name = "ISO_Container_Proxy"
    if mat_name in bpy.data.materials:
        return bpy.data.materials[mat_name]

    mat = bpy.data.materials.new(name=mat_name)
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    nodes.clear()

    out_node = nodes.new('ShaderNodeOutputMaterial'); out_node.location = (300, 0)
    bsdf     = nodes.new('ShaderNodeBsdfPrincipled'); bsdf.location     = (0,   0)

    # Seed attribute: prefer container_seed; fall back to Object Info Random
    attr = nodes.new('ShaderNodeAttribute')
    attr.location       = (-1000, 200)
    attr.attribute_name = "container_seed"
    attr.attribute_type = 'OBJECT'

    obj_info = nodes.new('ShaderNodeObjectInfo')
    obj_info.location = (-1000, 0)

    # Same 8-stop CONSTANT palette as the full shader
    cr = nodes.new('ShaderNodeValToRGB')
    cr.location = (-800, 200)
    cr.color_ramp.interpolation = 'CONSTANT'
    els = cr.color_ramp.elements
    for i, (pos, col) in enumerate(_PALETTE):
        if i < len(els):
            els[i].position = pos; els[i].color = col
        else:
            els.new(pos).color = col

    # If seed is 0 (not set) fall back to Object Info Random for variation
    has_seed = nodes.new('ShaderNodeMath')
    has_seed.location  = (-600, 250)
    has_seed.operation = 'GREATER_THAN'
    has_seed.inputs[1].default_value = 0.0

    mix_seed = nodes.new('ShaderNodeMix')
    mix_seed.location   = (-400, 250)
    mix_seed.data_type  = 'FLOAT'
    mix_seed.blend_type = 'MIX'

    tex_coord = nodes.new('ShaderNodeTexCoord'); tex_coord.location = (-1200, -200)

    node_diffuse = nodes.new('ShaderNodeTexImage')
    node_diffuse.location = (-800, -100)
    node_diffuse.image    = get_or_create_proxy_image("proxy_diffuse.png",  (0.8, 0.8, 0.8, 1.0))

    mix_color = nodes.new('ShaderNodeMix')
    mix_color.data_type  = 'RGBA'
    mix_color.blend_type = 'MULTIPLY'
    mix_color.location   = (-200, 100)
    mix_color.inputs['Factor'].default_value = 1.0

    node_rough = nodes.new('ShaderNodeTexImage')
    node_rough.location = (-800, -400)
    node_rough.image    = get_or_create_proxy_image("proxy_roughness.png", (0.6, 0.6, 0.6, 1.0), is_data=True)

    node_normal = nodes.new('ShaderNodeTexImage')
    node_normal.location = (-800, -700)
    node_normal.image    = get_or_create_proxy_image("proxy_normal.png",   (0.5, 0.5, 1.0, 1.0), is_data=True)

    normal_map = nodes.new('ShaderNodeNormalMap'); normal_map.location = (-400, -700)

    links.new(tex_coord.outputs['UV'],    node_diffuse.inputs['Vector'])
    links.new(tex_coord.outputs['UV'],    node_rough.inputs['Vector'])
    links.new(tex_coord.outputs['UV'],    node_normal.inputs['Vector'])
    links.new(attr.outputs['Fac'],        has_seed.inputs[0])
    links.new(has_seed.outputs['Value'],  mix_seed.inputs['Factor'])
    links.new(obj_info.outputs['Random'], mix_seed.inputs['A'])
    links.new(attr.outputs['Fac'],        mix_seed.inputs['B'])
    links.new(mix_seed.outputs['Result'], cr.inputs['Fac'])
    links.new(cr.outputs['Color'],           mix_color.inputs['A'])
    links.new(node_diffuse.outputs['Color'], mix_color.inputs['B'])
    links.new(mix_color.outputs['Result'],   bsdf.inputs['Base Color'])
    links.new(node_rough.outputs['Color'],   bsdf.inputs['Roughness'])
    links.new(node_normal.outputs['Color'],  normal_map.inputs['Color'])
    links.new(normal_map.outputs['Normal'],  bsdf.inputs['Normal'])
    links.new(bsdf.outputs['BSDF'],          out_node.inputs['Surface'])

    return mat
