"""systems/materials.py
ISO Container procedural materials — Blender 5.0+

ISO_Container_Metal  ·  v5 shader (attribute-driven controls)
──────────────────────────────────────────────────────────────
ALL per-container variation — colour, rust, stain, dust, scratches,
AND the six user-facing shader controls — are driven by object custom
properties read via ShaderNodeAttribute (attribute_type='OBJECT').

This means:
  • Every mesh child of one container renders identically (same seed,
    same shader settings) — no more per-object colour differences.
  • Changing a shader slider in the UI updates the render instantly
    without any geometry rebuild.

Object custom properties used by this shader
─────────────────────────────────────────────
  container_seed           float 0–1   colour + weathering pattern
  shader_rust_strength     float 0–2   edge rust amount         (default 0.35)
  shader_stain_intensity   float 0–1   water stains             (default 0.60)
  shader_dust_intensity    float 0–1   dust / grime             (default 0.65)
  shader_scratch_intensity float 0–1   horizontal scratches     (default 0.25)
  shader_color_override_amt float 0–1  blend toward manual col  (default 0.00)
  shader_color_override    float[4]    manual RGBA paint colour (default warm red)

All of these are stamped onto every metal mesh child by rebuild.py and
by the update_shader_props callback in properties.py.
"""

import bpy


# ─────────────────────────────────────────────────────────────────────
#  Shared helpers
# ─────────────────────────────────────────────────────────────────────

def hex_to_linear_rgba(hex_str):
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
#  v5 shader constants
# ─────────────────────────────────────────────────────────────────────

_MAT_NAME   = "ISO_Container_Metal"
_GROUP_NAME = "ISO_Container_Shader"

_Z_BOTTOM = 0.0     # world Z at container floor
_Z_TOP    = 2.591   # world Z at container roof (ISO 668 standard height)
_Z_MID    = 1.295   # midpoint

_W_SCALE = {
    "N_Roughness":  7.31,
    "N_Specular" : 13.73,
    "N_RustPat"  :  5.03,
    "N_RustBump" : 17.39,
    "N_Stain"    : 11.93,
    "N_Dust"     :  3.71,
    "N_Scratch"  : 19.13,
}
_W_BASE = {
    "N_Roughness":  3.0,
    "N_Specular" :  1.0,
    "N_RustPat"  :  0.0,
    "N_RustBump" :  0.0,
    "N_Stain"    :  0.0,
    "N_Dust"     :  0.0,
    "N_Scratch"  :  0.0,
}

_PALETTE = [
    (0.000, (0.021, 0.095, 0.270, 1.0)),
    (0.125, (0.007, 0.022, 0.056, 1.0)),
    (0.250, (0.027, 0.133, 0.381, 1.0)),
    (0.375, (0.292, 0.047, 0.026, 1.0)),
    (0.500, (0.184, 0.032, 0.019, 1.0)),
    (0.625, (0.120, 0.022, 0.014, 1.0)),
    (0.750, (0.009, 0.061, 0.006, 1.0)),
    (0.875, (0.216, 0.216, 0.216, 1.0)),
]


# ─────────────────────────────────────────────────────────────────────
#  Private node-graph helpers
# ─────────────────────────────────────────────────────────────────────

def _nd(nodes, typ, name, loc, **attrs):
    n = nodes.new(typ)
    n.name = n.label = name
    n.location = loc
    for k, v in attrs.items():
        setattr(n, k, v)
    return n


def _attr_obj(nodes, node_name, attr_name, loc):
    """ShaderNodeAttribute reading a named object custom property."""
    n = _nd(nodes, "ShaderNodeAttribute", node_name, loc)
    n.attribute_type = 'OBJECT'
    n.attribute_name = attr_name
    return n


def _noise(nodes, name, loc, *,
           ntype='FBM', normalize=True,
           scale=5.0, detail=8.0, rough=0.6, lac=2.0,
           w_sock=None, w_base=0.0):
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
    """W = W_BASE + seed × W_SCALE  → returns the ADD output socket."""
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
    n = _nd(nodes, "ShaderNodeMapping", name, loc, vector_type='POINT')
    n.inputs[3].default_value = scale
    return n


def _math(nodes, name, loc, op, v0=None, v1=None, clamp=False):
    n = _nd(nodes, "ShaderNodeMath", name, loc,
            operation=op, use_clamp=clamp)
    if v0 is not None: n.inputs[0].default_value = v0
    if v1 is not None: n.inputs[1].default_value = v1
    return n


def _mix_rgba(nodes, name, loc, mode, fac=None, b_col=None):
    n = _nd(nodes, "ShaderNodeMix", name, loc,
            blend_type=mode, data_type='RGBA',
            factor_mode='UNIFORM', clamp_factor=True)
    if fac   is not None: n.inputs[0].default_value = fac
    if b_col is not None: n.inputs[7].default_value = b_col
    return n


def _map_range(nodes, name, loc, lo_in, hi_in, lo_out, hi_out):
    n = _nd(nodes, "ShaderNodeMapRange", name, loc, clamp=True)
    n.inputs[1].default_value = lo_in;  n.inputs[2].default_value = hi_in
    n.inputs[3].default_value = lo_out; n.inputs[4].default_value = hi_out
    return n


def _principled(nodes, name, loc):
    n = nodes.new("ShaderNodeBsdfPrincipled")
    n.name = n.label = name
    n.location = loc
    n.distribution      = 'MULTI_GGX'
    n.subsurface_method = 'RANDOM_WALK'
    n.inputs[4].default_value  = 1.0
    n.inputs[28].default_value = 0.0
    return n


# ─────────────────────────────────────────────────────────────────────
#  Shader group builder
# ─────────────────────────────────────────────────────────────────────

def _build_shader_group():
    """Build the ISO_Container_Shader node group.

    All six user-facing controls are read from object custom properties
    via ShaderNodeAttribute nodes — no group inputs required.  The group
    interface therefore only exposes the single Shader output socket.
    """
    grp = bpy.data.node_groups.new(_GROUP_NAME, 'ShaderNodeTree')
    N   = grp.nodes
    def L(a, b): grp.links.new(a, b)

    # Output socket only — inputs are all driven by object attributes
    grp.interface.new_socket("Shader", in_out='OUTPUT',
                              socket_type='NodeSocketShader')
    go = _nd(N, "NodeGroupOutput", "GroupOutput", (2800, 0))

    # ── §1  Coordinates ───────────────────────────────────────────────
    tc  = _nd(N, "ShaderNodeTexCoord",    "TexCoord", (-2800, 300))
    tc.from_instancer = False

    # World-space position — used for height-based effects (dust, stains)
    # so they are consistent regardless of each mesh child's local origin.
    geo_coord = _nd(N, "ShaderNodeNewGeometry", "GeoCoord", (-3000, -100))

    sep = _nd(N, "ShaderNodeSeparateXYZ", "SepXYZ",  (-2800, -100))
    # Use world Position (not object coords) so Z is unified across all parts
    L(geo_coord.outputs[0], sep.inputs[0])

    mp  = _mapping(N, "Mapping", (-2500, 0))
    L(tc.outputs[3], mp.inputs[0])   # object coords for noise texture patterns
    vmp = mp.outputs[0]

    # ── §2  Seed ← 'container_seed' ───────────────────────────────────
    attr_seed = _attr_obj(N, "Attr_Seed", "container_seed", (-2800, 700))
    seed_fac  = attr_seed.outputs[2]   # Fac

    # ── §3  Per-container shader controls ← object custom properties ──
    # Fac output of each attribute node feeds directly where group inputs
    # used to go.  The attribute reads the value stamped on the mesh child
    # by rebuild.py and update_shader_props().
    attr_rust    = _attr_obj(N, "Attr_Rust",     "shader_rust_strength",      (-3200,  -700))
    attr_stain_i = _attr_obj(N, "Attr_StainI",   "shader_stain_intensity",    (-3200,  -800))
    attr_dust_i  = _attr_obj(N, "Attr_DustI",    "shader_dust_intensity",     (-3200,  -900))
    attr_scratch = _attr_obj(N, "Attr_Scratch",  "shader_scratch_intensity",  (-3200, -1000))
    attr_col_ovr = _attr_obj(N, "Attr_ColOvr",   "shader_color_override",     (-3200, -1100))
    attr_col_amt = _attr_obj(N, "Attr_ColAmt",   "shader_color_override_amt", (-3200, -1200))

    rust_sock    = attr_rust.outputs[2]       # Fac  → rust multiplier
    stain_i_sock = attr_stain_i.outputs[2]   # Fac  → stain intensity
    dust_i_sock  = attr_dust_i.outputs[2]    # Fac  → dust intensity
    scratch_sock = attr_scratch.outputs[2]   # Fac  → scratch intensity
    col_ovr_sock = attr_col_ovr.outputs[0]   # Color → override colour
    col_amt_sock = attr_col_amt.outputs[2]   # Fac  → override blend

    # ── §4  Base paint colour (palette driven by seed) ─────────────────
    cr_pal = _color_ramp(N, "CR_Palette", (-2500, 700), _PALETTE, 'CONSTANT')
    L(seed_fac, cr_pal.inputs[0])
    paint_color = cr_pal.outputs[0]

    # ── §5  Roughness & Specular ───────────────────────────────────────
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

    # ── §6  Rust system ────────────────────────────────────────────────
    geo = _nd(N, "ShaderNodeNewGeometry", "Geometry_Normals", (-2800, -400))
    bev = _nd(N, "ShaderNodeBevel",       "Bevel",    (-2800, -650))
    bev.samples = 4; bev.inputs[0].default_value = 0.05

    vm_dot = _nd(N, "ShaderNodeVectorMath", "VM_Dot", (-2500, -510),
                 operation='DOT_PRODUCT')
    L(geo.outputs[1], vm_dot.inputs[0])
    L(bev.outputs[0], vm_dot.inputs[1])

    cr_edge = _color_ramp(N, "CR_EdgeMask", (-2200, -510),
        [(0.954, (1.0, 1.0, 1.0, 1.0)),
         (1.000, (0.0, 0.0, 0.0, 1.0))], 'CARDINAL')
    L(vm_dot.outputs[1], cr_edge.inputs[0])

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

    mx_rust_mask = _mix_rgba(N, "MX_RustMask", (-1100, -650), 'MULTIPLY', fac=1.0)
    L(cr_edge.outputs[0], mx_rust_mask.inputs[6])
    L(cr_rp.outputs[0],   mx_rust_mask.inputs[7])

    math_rust = _math(N, "Math_Rust", (-750, -650), 'MULTIPLY')
    L(mx_rust_mask.outputs[2], math_rust.inputs[0])
    L(rust_sock,               math_rust.inputs[1])   # ← object attribute

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
    bump.inputs[0].default_value = 0.208
    bump.inputs[1].default_value = 1.0
    bump.inputs[2].default_value = 0.1
    L(cr_rb.outputs[0], bump.inputs[3])

    # ── §7  Water stains ───────────────────────────────────────────────
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

    mr_stain_h = _map_range(N, "MR_StainH", (-2200, 1550), _Z_MID, _Z_TOP, 0.0, 1.0)
    L(sep.outputs[2], mr_stain_h.inputs[0])

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

    # ── §8  Dust / grime ───────────────────────────────────────────────
    # MR_DustH: world Z 0.0 (floor) → 0.5 m maps intensity 1.0 → 0.0
    # Dust is fully visible at the very bottom and completely gone above 0.5 m.
    mr_dust_h = _map_range(N, "MR_DustH", (-2200, 1800),
                            _Z_BOTTOM, _Z_BOTTOM + 0.5, 1.0, 0.0)
    L(sep.outputs[2], mr_dust_h.inputs[0])

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
         (0.15, (0.5, 0.5, 0.5, 1.0)),
         (1.00, (1.0, 1.0, 1.0, 1.0))], 'EASE')
    L(math_dust_h.outputs[0], cr_dust_h.inputs[0])

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

    math_dust_max = _math(N, "Math_DustMax", (-800, 1950), 'MAXIMUM')
    L(cr_dust_h.outputs[0], math_dust_max.inputs[0])
    L(cr_ao.outputs[0],     math_dust_max.inputs[1])

    math_dust_i = _math(N, "Math_DustI", (-500, 1950), 'MULTIPLY', clamp=True)
    L(math_dust_max.outputs[0], math_dust_i.inputs[0])
    L(dust_i_sock,              math_dust_i.inputs[1])   # ← object attribute

    # ── §9  Scratches ──────────────────────────────────────────────────
    mp_scratch = _mapping(N, "MP_Scratch", (-2200, 2600), scale=(1.0, 1.0, 0.04))
    L(tc.outputs[3], mp_scratch.inputs[0])

    w_scratch = _make_w_sock(N, "N_Scratch", seed_fac, (-1700, 2600))
    n_scratch = _noise(N, "N_Scratch", (-1700, 2600),
                       scale=40.0, detail=2.0, rough=0.8, lac=2.5,
                       w_sock=w_scratch, w_base=_W_BASE["N_Scratch"])
    L(mp_scratch.outputs[0], n_scratch.inputs[0])

    cr_scratch = _color_ramp(N, "CR_Scratch", (-1400, 2600),
        [(0.00, (0.0, 0.0, 0.0, 1.0)),
         (0.92, (1.0, 1.0, 1.0, 1.0))], 'CONSTANT')
    L(n_scratch.outputs[0], cr_scratch.inputs[0])

    math_scratch_i = _math(N, "Math_ScratchI", (-1100, 2600), 'MULTIPLY')
    L(cr_scratch.outputs[0], math_scratch_i.inputs[0])
    L(scratch_sock,          math_scratch_i.inputs[1])   # ← object attribute

    # ── §10  Colour composite ──────────────────────────────────────────
    mx_stain = _mix_rgba(N, "MX_Stain", (-200, 1300), 'MULTIPLY',
                          b_col=(0.07, 0.045, 0.02, 1.0))
    L(math_stain_i.outputs[0], mx_stain.inputs[0])
    L(paint_color,             mx_stain.inputs[6])

    mx_dust = _mix_rgba(N, "MX_Dust", (-200, 1000), 'MIX',
                         b_col=(0.38, 0.30, 0.17, 1.0))
    L(math_dust_i.outputs[0], mx_dust.inputs[0])
    L(mx_stain.outputs[2],    mx_dust.inputs[6])

    mx_scratch = _mix_rgba(N, "MX_Scratch", (-200, 700), 'SCREEN',
                            b_col=(0.55, 0.50, 0.42, 1.0))
    L(math_scratch_i.outputs[0], mx_scratch.inputs[0])
    L(mx_dust.outputs[2],        mx_scratch.inputs[6])

    mx_override = _mix_rgba(N, "MX_Override", (-200, 400), 'MIX')
    L(col_amt_sock,           mx_override.inputs[0])   # ← object attribute (blend)
    L(mx_scratch.outputs[2],  mx_override.inputs[6])
    L(col_ovr_sock,           mx_override.inputs[7])   # ← object attribute (color)

    # ── §11  BSDFs + mix ───────────────────────────────────────────────
    bsdf_paint = _principled(N, "BSDF_Paint", (200, 600))
    bsdf_paint.inputs[1].default_value  = 0.65
    bsdf_paint.inputs[3].default_value  = 1.45
    L(mx_override.outputs[2], bsdf_paint.inputs[0])
    L(cr_rough.outputs[0],    bsdf_paint.inputs[2])
    L(cr_spec.outputs[0],     bsdf_paint.inputs[13])

    bsdf_rust = _principled(N, "BSDF_Rust", (200, -700))
    bsdf_rust.inputs[1].default_value  = 0.75
    bsdf_rust.inputs[2].default_value  = 0.95
    bsdf_rust.inputs[3].default_value  = 1.5
    bsdf_rust.inputs[13].default_value = 0.08
    L(cr_rb.outputs[0], bsdf_rust.inputs[0])
    L(bump.outputs[0],  bsdf_rust.inputs[5])

    mix_shader = _nd(N, "ShaderNodeMixShader", "MixShader", (700, -100))
    L(math_rust.outputs[0],  mix_shader.inputs[0])
    L(bsdf_paint.outputs[0], mix_shader.inputs[1])
    L(bsdf_rust.outputs[0],  mix_shader.inputs[2])
    L(mix_shader.outputs[0], go.inputs[0])

    return grp


# ─────────────────────────────────────────────────────────────────────
#  Public material functions
# ─────────────────────────────────────────────────────────────────────

def get_or_create_container_material():
    """Return the ISO_Container_Metal material, building it if absent.

    To force full regeneration delete 'ISO_Container_Metal' from
    bpy.data.materials and 'ISO_Container_Shader' from bpy.data.node_groups.
    """
    if _MAT_NAME in bpy.data.materials:
        return bpy.data.materials[_MAT_NAME]

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

    attr = nodes.new('ShaderNodeAttribute')
    attr.location       = (-1000, 200)
    attr.attribute_name = "container_seed"
    attr.attribute_type = 'OBJECT'

    obj_info = nodes.new('ShaderNodeObjectInfo')
    obj_info.location = (-1000, 0)

    cr = nodes.new('ShaderNodeValToRGB')
    cr.location = (-800, 200)
    cr.color_ramp.interpolation = 'CONSTANT'
    els = cr.color_ramp.elements
    for i, (pos, col) in enumerate(_PALETTE):
        if i < len(els):
            els[i].position = pos; els[i].color = col
        else:
            els.new(pos).color = col

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
