# ─────────────────────────────────────────────────────────────────────
#  systems/materials.py
#  ISO Shipping Container Add-on — Material system
#  v6 shader + all auxiliary material helpers
# ─────────────────────────────────────────────────────────────────────

import bpy

_MAT_NAME   = "ISO_Container_Metal"
_GROUP_NAME = "ISO_Container_Shader"

_Z_BOTTOM = 0.0
_Z_TOP    = 2.591
_Z_MID    = 1.295

_W_SCALE = {
    "N_Roughness": 7.31,
    "N_Specular":  13.73,
    "N_RustPat":   5.03,
    "N_RustBump":  17.39,
    "N_Stain":     11.93,
    "N_Dust":      3.71,
    "N_Scratch":   19.13,
}
_W_BASE = {
    "N_Roughness": 3.0,
    "N_Specular":  1.0,
    "N_RustPat":   0.0,
    "N_RustBump":  0.0,
    "N_Stain":     0.0,
    "N_Dust":      0.0,
    "N_Scratch":   0.0,
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
#  v6 Shader group builder
# ─────────────────────────────────────────────────────────────────────

def _build_shader_group():
    """Build and return the ISO_Container_Shader node group."""
    grp = bpy.data.node_groups.new(type='ShaderNodeTree', name="ISO_Container_Shader")
    grp.color_tag = 'NONE'
    grp.description = ""
    grp.default_group_node_width = 140

    sock = grp.interface.new_socket(name="Shader", in_out='OUTPUT', socket_type='NodeSocketShader')
    sock.attribute_domain = 'POINT'
    sock.default_input = 'VALUE'
    sock.structure_type = 'AUTO'

    N = grp.nodes
    L = grp.links.new

    # ── Outputs / Coordinates ────────────────────────────────────────
    groupoutput = N.new("NodeGroupOutput")
    groupoutput.name = groupoutput.label = "GroupOutput"
    groupoutput.is_active_output = True

    texcoord = N.new("ShaderNodeTexCoord")
    texcoord.name = texcoord.label = "TexCoord"
    texcoord.from_instancer = False

    geocoord = N.new("ShaderNodeNewGeometry")
    geocoord.name = geocoord.label = "GeoCoord"

    sepxyz = N.new("ShaderNodeSeparateXYZ")
    sepxyz.name = sepxyz.label = "SepXYZ"

    mapping = N.new("ShaderNodeMapping")
    mapping.name = mapping.label = "Mapping"
    mapping.vector_type = 'POINT'
    mapping.inputs[3].default_value = (1.0, 1.0, 1.0)

    # ── Attribute nodes ──────────────────────────────────────────────
    def _attr(node_name, attr_name):
        n = N.new("ShaderNodeAttribute")
        n.name = n.label = node_name
        n.attribute_type = 'OBJECT'
        n.attribute_name = attr_name
        return n

    attr_seed   = _attr("Attr_Seed",   "container_seed")
    attr_rust   = _attr("Attr_Rust",   "shader_rust_strength")
    attr_staini = _attr("Attr_StainI", "shader_stain_intensity")
    attr_dusti  = _attr("Attr_DustI",  "shader_dust_intensity")
    attr_scratch = _attr("Attr_Scratch", "shader_scratch_intensity")
    attr_colovr  = _attr("Attr_ColOvr",  "shader_color_override")
    attr_colamt  = _attr("Attr_ColAmt",  "shader_color_override_amt")

    # ── Colour palette ───────────────────────────────────────────────
    cr_palette = N.new("ShaderNodeValToRGB")
    cr_palette.name = cr_palette.label = "CR_Palette"
    cr_palette.color_ramp.color_mode = 'RGB'
    cr_palette.color_ramp.interpolation = 'CONSTANT'
    els = cr_palette.color_ramp.elements
    els.remove(els[0])
    e = els[0]
    e.position = _PALETTE[0][0]
    e.color = _PALETTE[0][1]
    for pos, col in _PALETTE[1:]:
        e = els.new(pos)
        e.color = col

    # ── Helper: Noise 3D ─────────────────────────────────────────────
    def _noise3d(node_name, ntype, normalize, scale, detail, rough, lac):
        n = N.new("ShaderNodeTexNoise")
        n.name = n.label = node_name
        n.noise_dimensions = '3D'
        n.noise_type = ntype
        n.normalize = normalize
        n.inputs[2].default_value = scale
        n.inputs[3].default_value = detail
        n.inputs[4].default_value = rough
        n.inputs[5].default_value = lac
        n.inputs[8].default_value = 0.0
        return n

    # ── Helper: Noise 4D ─────────────────────────────────────────────
    def _noise4d(node_name, ntype, normalize, scale, detail, rough, lac):
        n = N.new("ShaderNodeTexNoise")
        n.name = n.label = node_name
        n.noise_dimensions = '4D'
        n.noise_type = ntype
        n.normalize = normalize
        n.inputs[2].default_value = scale
        n.inputs[3].default_value = detail
        n.inputs[4].default_value = rough
        n.inputs[5].default_value = lac
        n.inputs[8].default_value = 0.0
        return n

    # ── Helper: colour ramp ──────────────────────────────────────────
    def _ramp(node_name, interp, stops):
        n = N.new("ShaderNodeValToRGB")
        n.name = n.label = node_name
        n.color_ramp.interpolation = interp
        e = n.color_ramp.elements
        e.remove(e[0])
        e0 = e[0]
        e0.position = stops[0][0]
        e0.color = stops[0][1]
        for pos, col in stops[1:]:
            ei = e.new(pos)
            ei.color = col
        return n

    # ── Helper: math node ────────────────────────────────────────────
    def _math(node_name, op, v0=None, v1=None, clamp=False):
        n = N.new("ShaderNodeMath")
        n.name = n.label = node_name
        n.operation = op
        n.use_clamp = clamp
        if v0 is not None:
            n.inputs[0].default_value = v0
        if v1 is not None:
            n.inputs[1].default_value = v1
        return n

    # ── Helper: W-offset pair ────────────────────────────────────────
    def _w_pair(noise_name, seed_sock):
        mul = _math(f"W_Mul_{noise_name}", 'MULTIPLY', v1=_W_SCALE[noise_name])
        L(seed_sock, mul.inputs[0])
        add = _math(f"W_Add_{noise_name}", 'ADD', v0=_W_BASE[noise_name])
        L(mul.outputs[0], add.inputs[1])
        return add.outputs[0]

    # ── Roughness / Specular (3D, no W needed — not per-instance) ────
    n_roughness = _noise3d("N_Roughness", 'FBM', True, 3.5, 15.0, 0.76, 2.0)
    cr_roughness = _ramp("CR_Roughness", 'EASE', [(0.0, (0.36, 0.36, 0.36, 1.0)), (1.0, (1.0, 1.0, 1.0, 1.0))])

    n_specular  = _noise3d("N_Specular",  'FBM', True, 5.0, 10.0, 0.76, 2.0)
    cr_specular  = _ramp("CR_Specular",  'EASE', [(0.0, (0.36, 0.36, 0.36, 1.0)), (1.0, (1.0, 1.0, 1.0, 1.0))])

    # ── Edge mask ────────────────────────────────────────────────────
    geom_nrm = N.new("ShaderNodeNewGeometry")
    geom_nrm.name = geom_nrm.label = "Geometry_Normals"

    bevel_nd = N.new("ShaderNodeBevel")
    bevel_nd.name = bevel_nd.label = "Bevel"
    bevel_nd.samples = 4
    bevel_nd.inputs[0].default_value = 0.05
    bevel_nd.inputs[1].default_value = (0.0, 0.0, 0.0)

    vm_dot = N.new("ShaderNodeVectorMath")
    vm_dot.name = vm_dot.label = "VM_Dot"
    vm_dot.operation = 'DOT_PRODUCT'

    cr_edgemask = _ramp("CR_EdgeMask", 'CARDINAL',
                        [(0.95, (1.0, 1.0, 1.0, 1.0)), (1.0, (0.0, 0.0, 0.0, 1.0))])

    # ── Rust pattern (3D) ────────────────────────────────────────────
    n_rustpat = _noise3d("N_RustPat", 'MULTIFRACTAL', False, 1.0, 14.0, 1.0, 1.55)
    cr_rustpat = _ramp("CR_RustPat", 'LINEAR',
                       [(0.85, (0.0, 0.0, 0.0, 1.0)), (1.0, (1.0, 1.0, 1.0, 1.0))])

    mx_rustmask = N.new("ShaderNodeMix")
    mx_rustmask.name = mx_rustmask.label = "MX_RustMask"
    mx_rustmask.blend_type = 'MULTIPLY'
    mx_rustmask.clamp_factor = True
    mx_rustmask.data_type = 'RGBA'
    mx_rustmask.factor_mode = 'UNIFORM'
    mx_rustmask.inputs[0].default_value = 1.0

    math_rust = _math("Math_Rust", 'MULTIPLY')

    # ── Rust bump (3D, W-driven) ──────────────────────────────────────
    w_rustbump = _w_pair("N_RustBump", attr_seed.outputs[2])
    n_rustbump = _noise3d("N_RustBump", 'FBM', True, 350.0, 2.0, 0.5, 2.0)
    L(w_rustbump, n_rustbump.inputs[1])

    cr_rustbump = _ramp("CR_RustBump", 'LINEAR', [
        (0.0,  (1.0,  1.0,  1.0,  1.0)),
        (0.42, (0.15, 0.05, 0.02, 1.0)),
        (1.0,  (0.21, 0.03, 0.02, 1.0)),
    ])

    bump_nd = N.new("ShaderNodeBump")
    bump_nd.name = bump_nd.label = "Bump"
    bump_nd.invert = False
    bump_nd.inputs[0].default_value = 0.21
    bump_nd.inputs[1].default_value = 1.0
    bump_nd.inputs[2].default_value = 0.10
    bump_nd.inputs[4].default_value = (0.0, 0.0, 0.0)

    # ── Stain (4D, W-driven) ─────────────────────────────────────────
    mp_stain = N.new("ShaderNodeMapping")
    mp_stain.name = mp_stain.label = "MP_Stain"
    mp_stain.vector_type = 'POINT'
    mp_stain.inputs[3].default_value = (8.0, 8.0, 0.25)

    w_stain = _w_pair("N_Stain", attr_seed.outputs[2])
    n_stain = _noise4d("N_Stain", 'FBM', True, 14.0, 3.0, 0.65, 2.0)
    L(w_stain, n_stain.inputs[1])

    cr_stain = _ramp("CR_Stain", 'LINEAR',
                     [(0.55, (0.0, 0.0, 0.0, 1.0)), (0.80, (1.0, 1.0, 1.0, 1.0))])

    mr_stainh = N.new("ShaderNodeMapRange")
    mr_stainh.name = mr_stainh.label = "MR_StainH"
    mr_stainh.clamp = True
    mr_stainh.data_type = 'FLOAT'
    mr_stainh.interpolation_type = 'LINEAR'
    mr_stainh.inputs[1].default_value = 1.29
    mr_stainh.inputs[2].default_value = 2.59
    mr_stainh.inputs[3].default_value = 0.0
    mr_stainh.inputs[4].default_value = 1.0

    cr_stainh = _ramp("CR_StainH", 'EASE',
                      [(0.0, (0.0, 0.0, 0.0, 1.0)), (1.0, (1.0, 1.0, 1.0, 1.0))])

    math_stain  = _math("Math_Stain",  'MULTIPLY')
    math_staini = _math("Math_StainI", 'MULTIPLY')

    # ── Dust (4D, W-driven) ──────────────────────────────────────────
    mr_dusth = N.new("ShaderNodeMapRange")
    mr_dusth.name = mr_dusth.label = "MR_DustH"
    mr_dusth.clamp = True
    mr_dusth.data_type = 'FLOAT'
    mr_dusth.interpolation_type = 'LINEAR'
    mr_dusth.inputs[1].default_value = 0.0
    mr_dusth.inputs[2].default_value = 0.5
    mr_dusth.inputs[3].default_value = 1.0
    mr_dusth.inputs[4].default_value = 0.0

    w_dust = _w_pair("N_Dust", attr_seed.outputs[2])
    n_dust = _noise4d("N_Dust", 'FBM', True, 5.0, 4.0, 0.70, 2.0)
    L(w_dust, n_dust.inputs[1])

    math_dusth = _math("Math_DustH", 'MULTIPLY')

    cr_dusth = _ramp("CR_DustH", 'EASE',
                     [(0.0, (0.0, 0.0, 0.0, 1.0)), (1.0, (1.0, 1.0, 1.0, 1.0))])

    ao_nd = N.new("ShaderNodeAmbientOcclusion")
    ao_nd.name = ao_nd.label = "AO"
    ao_nd.inside = False
    ao_nd.only_local = False
    ao_nd.samples = 16
    ao_nd.inputs[0].default_value = (1.0, 1.0, 1.0, 1.0)
    ao_nd.inputs[1].default_value = 1.0

    math_aoinv  = _math("Math_AOInv",  'SUBTRACT', v0=1.0)
    cr_ao = _ramp("CR_AO", 'EASE', [
        (0.0,  (0.0, 0.0, 0.0, 1.0)),
        (0.35, (0.0, 0.0, 0.0, 1.0)),
        (0.65, (1.0, 1.0, 1.0, 1.0)),
        (1.0,  (1.0, 1.0, 1.0, 1.0)),
    ])

    math_dustmax = _math("Math_DustMax", 'MAXIMUM')
    math_dusti   = _math("Math_DustI",   'MULTIPLY', clamp=True)

    # ── Scratch (4D, W-driven) ───────────────────────────────────────
    vecrot_scratch = N.new("ShaderNodeVectorRotate")
    vecrot_scratch.name = vecrot_scratch.label = "VecRot_Scratch"
    vecrot_scratch.invert = False
    vecrot_scratch.rotation_type = 'X_AXIS'
    vecrot_scratch.inputs[1].default_value = (0.0, 0.0, 0.0)
    vecrot_scratch.inputs[3].default_value = -1.49

    mp_wave = N.new("ShaderNodeMapping")
    mp_wave.name = mp_wave.label = "MP_Wave"
    mp_wave.vector_type = 'POINT'
    mp_wave.inputs[3].default_value = (3.60, 1.0, 1.0)

    wavetex = N.new("ShaderNodeTexWave")
    wavetex.name = wavetex.label = "WaveTex"
    wavetex.bands_direction = 'DIAGONAL'
    wavetex.rings_direction = 'X'
    wavetex.wave_profile = 'SIN'
    wavetex.wave_type = 'BANDS'
    wavetex.inputs[1].default_value = 1.0
    wavetex.inputs[2].default_value = 0.0
    wavetex.inputs[3].default_value = 0.90
    wavetex.inputs[4].default_value = 1.0
    wavetex.inputs[5].default_value = 0.5
    wavetex.inputs[6].default_value = 1.57

    mp_scratchcoord = N.new("ShaderNodeMapping")
    mp_scratchcoord.name = mp_scratchcoord.label = "MP_ScratchCoord"
    mp_scratchcoord.vector_type = 'POINT'
    mp_scratchcoord.inputs[2].default_value = (0.01, -0.09, -0.34)

    sep_scratch  = N.new("ShaderNodeSeparateXYZ")
    sep_scratch.name  = sep_scratch.label  = "Sep_Scratch"
    comb_scratch = N.new("ShaderNodeCombineXYZ")
    comb_scratch.name = comb_scratch.label = "Comb_Scratch"

    math_wavescale = _math("Math_WaveScale", 'MULTIPLY_ADD', v1=5.0)
    math_wavescale.inputs[2].default_value = 0.5

    w_scratch = _w_pair("N_Scratch", attr_seed.outputs[2])
    n_scratchdist = _noise4d("N_ScratchDist", 'FBM', False, 1.0, 14.0, 1.0, 1.55)
    L(w_scratch, n_scratchdist.inputs[1])

    cr_scratch = _ramp("CR_Scratch", 'LINEAR',
                       [(0.68, (0.0, 0.0, 0.0, 1.0)), (0.82, (1.0, 1.0, 1.0, 1.0))])
    math_scratchi = _math("Math_ScratchI", 'MULTIPLY')

    # ── Colour composite chain ────────────────────────────────────────
    def _mix_rgba(node_name, mode, b_col=None):
        n = N.new("ShaderNodeMix")
        n.name = n.label = node_name
        n.blend_type = mode
        n.clamp_factor = True
        n.data_type = 'RGBA'
        n.factor_mode = 'UNIFORM'
        if b_col is not None:
            n.inputs[7].default_value = b_col
        return n

    mx_stain    = _mix_rgba("MX_Stain",    'MULTIPLY', (0.07, 0.05, 0.02, 1.0))
    mx_dust     = _mix_rgba("MX_Dust",     'MIX',      (0.38, 0.30, 0.17, 1.0))
    mx_scratch  = _mix_rgba("MX_Scratch",  'SCREEN',   (0.55, 0.50, 0.42, 1.0))
    mx_override = _mix_rgba("MX_Override", 'MIX')

    # ── Edge roughness ────────────────────────────────────────────────
    math_edgeroughmul = _math("Math_EdgeRoughMul", 'MULTIPLY', v1=0.30)
    math_edgeroughadd = _math("Math_EdgeRoughAdd", 'ADD', clamp=True)

    # ── BSDFs ─────────────────────────────────────────────────────────
    def _principled(node_name):
        n = N.new("ShaderNodeBsdfPrincipled")
        n.name = n.label = node_name
        n.distribution = 'MULTI_GGX'
        n.subsurface_method = 'RANDOM_WALK'
        n.inputs[4].default_value  = 1.0   # Alpha
        n.inputs[28].default_value = 0.0   # Emission Strength
        return n

    bsdf_paint = _principled("BSDF_Paint")
    bsdf_paint.inputs[1].default_value  = 0.65   # Metallic
    bsdf_paint.inputs[3].default_value  = 1.45   # IOR

    bsdf_worn = _principled("BSDF_Worn")
    bsdf_worn.inputs[0].default_value   = (0.25, 0.22, 0.20, 1.0)
    bsdf_worn.inputs[1].default_value   = 0.80
    bsdf_worn.inputs[3].default_value   = 1.45
    bsdf_worn.inputs[13].default_value  = 0.70   # Specular IOR Level

    bsdf_rust = _principled("BSDF_Rust")
    bsdf_rust.inputs[1].default_value   = 0.75
    bsdf_rust.inputs[2].default_value   = 0.95
    bsdf_rust.inputs[3].default_value   = 1.50
    bsdf_rust.inputs[13].default_value  = 0.08

    mix_worn = N.new("ShaderNodeMixShader")
    mix_worn.name = mix_worn.label = "Mix_Worn"
    mix_rust = N.new("ShaderNodeMixShader")
    mix_rust.name = mix_rust.label = "Mix_Rust"

    # ── Wire everything together ──────────────────────────────────────
    L(geocoord.outputs[0],          sepxyz.inputs[0])
    L(texcoord.outputs[3],          mapping.inputs[0])
    L(attr_seed.outputs[2],         cr_palette.inputs[0])

    L(mapping.outputs[0],           n_roughness.inputs[0])
    L(n_roughness.outputs[0],       cr_roughness.inputs[0])
    L(mapping.outputs[0],           n_specular.inputs[0])
    L(n_specular.outputs[0],        cr_specular.inputs[0])

    L(geom_nrm.outputs[1],          vm_dot.inputs[0])
    L(bevel_nd.outputs[0],          vm_dot.inputs[1])
    L(vm_dot.outputs[1],            cr_edgemask.inputs[0])

    L(mapping.outputs[0],           n_rustpat.inputs[0])
    L(n_rustpat.outputs[0],         cr_rustpat.inputs[0])
    L(cr_edgemask.outputs[0],       mx_rustmask.inputs[6])
    L(cr_rustpat.outputs[0],        mx_rustmask.inputs[7])
    L(mx_rustmask.outputs[2],       math_rust.inputs[0])
    L(attr_rust.outputs[2],         math_rust.inputs[1])

    L(mapping.outputs[0],           n_rustbump.inputs[0])
    L(n_rustbump.outputs[0],        cr_rustbump.inputs[0])
    L(cr_rustbump.outputs[0],       bump_nd.inputs[3])

    L(texcoord.outputs[3],          mp_stain.inputs[0])
    L(mp_stain.outputs[0],          n_stain.inputs[0])
    L(n_stain.outputs[0],           cr_stain.inputs[0])
    L(sepxyz.outputs[2],            mr_stainh.inputs[0])
    L(mr_stainh.outputs[0],         cr_stainh.inputs[0])
    L(cr_stain.outputs[0],          math_stain.inputs[0])
    L(cr_stainh.outputs[0],         math_stain.inputs[1])
    L(math_stain.outputs[0],        math_staini.inputs[0])
    L(attr_staini.outputs[2],       math_staini.inputs[1])

    L(sepxyz.outputs[2],            mr_dusth.inputs[0])
    L(mapping.outputs[0],           n_dust.inputs[0])
    L(mr_dusth.outputs[0],          math_dusth.inputs[0])
    L(n_dust.outputs[0],            math_dusth.inputs[1])
    L(math_dusth.outputs[0],        cr_dusth.inputs[0])
    L(ao_nd.outputs[1],             math_aoinv.inputs[1])
    L(math_aoinv.outputs[0],        cr_ao.inputs[0])
    L(cr_dusth.outputs[0],          math_dustmax.inputs[0])
    L(cr_ao.outputs[0],             math_dustmax.inputs[1])
    L(math_dustmax.outputs[0],      math_dusti.inputs[0])
    L(attr_dusti.outputs[2],        math_dusti.inputs[1])

    L(texcoord.outputs[3],          vecrot_scratch.inputs[0])
    L(vecrot_scratch.outputs[0],    mp_wave.inputs[0])
    L(mp_wave.outputs[0],           wavetex.inputs[0])
    L(texcoord.outputs[3],          mp_scratchcoord.inputs[0])
    L(mp_scratchcoord.outputs[0],   sep_scratch.inputs[0])
    L(sep_scratch.outputs[0],       comb_scratch.inputs[0])
    L(wavetex.outputs[1],           comb_scratch.inputs[1])
    L(sep_scratch.outputs[2],       comb_scratch.inputs[2])
    L(attr_seed.outputs[2],         math_wavescale.inputs[0])
    L(comb_scratch.outputs[0],      n_scratchdist.inputs[0])
    L(math_wavescale.outputs[0],    n_scratchdist.inputs[2])
    L(n_scratchdist.outputs[0],     cr_scratch.inputs[0])
    L(cr_scratch.outputs[0],        math_scratchi.inputs[0])
    L(attr_scratch.outputs[2],      math_scratchi.inputs[1])

    L(math_staini.outputs[0],       mx_stain.inputs[0])
    L(cr_palette.outputs[0],        mx_stain.inputs[6])
    L(math_dusti.outputs[0],        mx_dust.inputs[0])
    L(mx_stain.outputs[2],          mx_dust.inputs[6])
    L(math_scratchi.outputs[0],     mx_scratch.inputs[0])
    L(mx_dust.outputs[2],           mx_scratch.inputs[6])
    L(attr_colamt.outputs[2],       mx_override.inputs[0])
    L(mx_scratch.outputs[2],        mx_override.inputs[6])
    L(attr_colovr.outputs[0],       mx_override.inputs[7])

    L(cr_edgemask.outputs[0],       math_edgeroughmul.inputs[0])
    L(cr_roughness.outputs[0],      math_edgeroughadd.inputs[0])
    L(math_edgeroughmul.outputs[0], math_edgeroughadd.inputs[1])

    L(mx_override.outputs[2],       bsdf_paint.inputs[0])
    L(math_edgeroughadd.outputs[0], bsdf_paint.inputs[2])
    L(cr_specular.outputs[0],       bsdf_paint.inputs[13])
    L(math_edgeroughadd.outputs[0], bsdf_worn.inputs[2])
    L(cr_rustbump.outputs[0],       bsdf_rust.inputs[0])
    L(bump_nd.outputs[0],           bsdf_rust.inputs[5])

    L(cr_edgemask.outputs[0],       mix_worn.inputs[0])
    L(bsdf_paint.outputs[0],        mix_worn.inputs[1])
    L(bsdf_worn.outputs[0],         mix_worn.inputs[2])
    L(math_rust.outputs[0],         mix_rust.inputs[0])
    L(mix_worn.outputs[0],          mix_rust.inputs[1])
    L(bsdf_rust.outputs[0],         mix_rust.inputs[2])
    L(mix_rust.outputs[0],          groupoutput.inputs[0])

    return grp


# ─────────────────────────────────────────────────────────────────────
#  Public material functions
# ─────────────────────────────────────────────────────────────────────

def get_or_create_container_material():
    """Return the ISO_Container_Metal v6 material, building it if absent.

    To force full regeneration, remove the material and node group from
    bpy.data before calling again.
    """
    mat_name = "ISO_Container_Metal"
    if mat_name in bpy.data.materials:
        return bpy.data.materials[mat_name]

    group_name = "ISO_Container_Shader"
    if group_name in bpy.data.node_groups:
        bpy.data.node_groups.remove(bpy.data.node_groups[group_name])

    grp = _build_shader_group()

    mat = bpy.data.materials.new(name=mat_name)
    mat.use_nodes = True
    mat.alpha_threshold              = 0.5
    mat.blend_method                 = 'HASHED'
    mat.displacement_method          = 'BUMP'
    mat.surface_render_method        = 'DITHERED'
    mat.use_backface_culling         = False
    mat.use_backface_culling_shadow  = False
    mat.use_transparent_shadow       = True
    mat.roughness                    = 0.4
    mat.diffuse_color                = (0.8, 0.8, 0.8, 1.0)

    tree = mat.node_tree
    for node in list(tree.nodes):
        tree.nodes.remove(node)

    out = tree.nodes.new("ShaderNodeOutputMaterial")
    out.name = "Material Output"
    out.is_active_output = True
    out.target = 'ALL'
    out.location = (400.0, 0.0)
    out.inputs[2].default_value = (0.0, 0.0, 0.0)
    out.inputs[3].default_value = 0.0

    grp_node = tree.nodes.new("ShaderNodeGroup")
    grp_node.name = "Group"
    grp_node.node_tree = grp
    grp_node.location = (117.39, -20.95)

    tree.links.new(grp_node.outputs[0], out.inputs[0])

    return mat


# ─────────────────────────────────────────────────────────────────────
#  Wood / floor material
# ─────────────────────────────────────────────────────────────────────

def get_or_create_wood_material():
    """Return a cached marine-plywood material, creating it if absent.

    A Noise-driven Principled BSDF simulates tropical hardwood grain
    without any image textures.
    """
    mat_name = "ISO_Container_Wood"
    if mat_name in bpy.data.materials:
        return bpy.data.materials[mat_name]

    mat = bpy.data.materials.new(name=mat_name)
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    nodes.clear()

    out = nodes.new("ShaderNodeOutputMaterial")
    out.location = (600, 0)

    bsdf = nodes.new("ShaderNodeBsdfPrincipled")
    bsdf.location = (300, 0)
    bsdf.distribution = "MULTI_GGX"
    bsdf.inputs["Metallic"].default_value  = 0.0
    bsdf.inputs["Roughness"].default_value = 0.72
    bsdf.inputs["IOR"].default_value       = 1.46

    tex_coord = nodes.new("ShaderNodeTexCoord")
    tex_coord.location = (-700, 100)

    mapping = nodes.new("ShaderNodeMapping")
    mapping.location = (-500, 100)
    mapping.vector_type = "POINT"
    mapping.inputs["Scale"].default_value = (1.0, 8.0, 1.0)

    noise = nodes.new("ShaderNodeTexNoise")
    noise.location = (-280, 100)
    noise.inputs["Scale"].default_value      = 6.0
    noise.inputs["Detail"].default_value     = 12.0
    noise.inputs["Roughness"].default_value  = 0.65
    noise.inputs["Distortion"].default_value = 0.4

    # Narrow warm-grain colour band (linear sRGB): mid-oak → dark heartwood
    ramp = nodes.new("ShaderNodeValToRGB")
    ramp.location = (-60, 100)
    ramp.color_ramp.interpolation = "LINEAR"
    ramp.color_ramp.elements[0].position = 0.30
    ramp.color_ramp.elements[0].color    = (0.404, 0.260, 0.122, 1.0)
    ramp.color_ramp.elements[1].position = 0.80
    ramp.color_ramp.elements[1].color    = (0.216, 0.110, 0.043, 1.0)

    links.new(tex_coord.outputs["Object"], mapping.inputs["Vector"])
    links.new(mapping.outputs["Vector"],   noise.inputs["Vector"])
    links.new(noise.outputs["Fac"],        ramp.inputs["Fac"])
    links.new(ramp.outputs["Color"],       bsdf.inputs["Base Color"])
    links.new(bsdf.outputs["BSDF"],        out.inputs["Surface"])

    return mat


# ─────────────────────────────────────────────────────────────────────
#  Decal / text material
# ─────────────────────────────────────────────────────────────────────

def get_or_create_decal_material():
    """Return a cached flat off-white material for ISO marking text decals.

    A small emission component keeps text legible in shadowed areas.
    """
    mat_name = "ISO_Container_Decal"
    if mat_name in bpy.data.materials:
        return bpy.data.materials[mat_name]

    mat = bpy.data.materials.new(name=mat_name)
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    nodes.clear()

    out = nodes.new("ShaderNodeOutputMaterial")
    out.location = (400, 0)

    bsdf = nodes.new("ShaderNodeBsdfPrincipled")
    bsdf.location = (160, 0)
    bsdf.distribution = "MULTI_GGX"
    bsdf.inputs["Base Color"].default_value         = (0.85, 0.84, 0.80, 1.0)
    bsdf.inputs["Metallic"].default_value           = 0.0
    bsdf.inputs["Roughness"].default_value          = 0.90
    bsdf.inputs["Emission Color"].default_value     = (0.85, 0.84, 0.80, 1.0)
    bsdf.inputs["Emission Strength"].default_value  = 0.25

    links.new(bsdf.outputs["BSDF"], out.inputs["Surface"])

    return mat


# ─────────────────────────────────────────────────────────────────────
#  Hardware / locking mechanism material
# ─────────────────────────────────────────────────────────────────────

def get_or_create_hardware_material():
    """Return a cached dark bare-steel material for door hardware.

    Higher metallic and moderate roughness gives hinges, locking rods,
    cams, and guide brackets the look of unpainted structural steel.
    """
    mat_name = "ISO_Container_Hardware"
    if mat_name in bpy.data.materials:
        return bpy.data.materials[mat_name]

    mat = bpy.data.materials.new(name=mat_name)
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    nodes.clear()

    out = nodes.new("ShaderNodeOutputMaterial")
    out.location = (400, 0)

    bsdf = nodes.new("ShaderNodeBsdfPrincipled")
    bsdf.location = (160, 0)
    bsdf.distribution = "MULTI_GGX"
    bsdf.inputs["Base Color"].default_value          = (0.18, 0.16, 0.14, 1.0)
    bsdf.inputs["Metallic"].default_value            = 0.92
    bsdf.inputs["Roughness"].default_value           = 0.55
    bsdf.inputs["IOR"].default_value                 = 2.50
    bsdf.inputs["Specular IOR Level"].default_value  = 0.50

    links.new(bsdf.outputs["BSDF"], out.inputs["Surface"])

    return mat


# ─────────────────────────────────────────────────────────────────────
#  Proxy / LOD material
# ─────────────────────────────────────────────────────────────────────

def get_or_create_proxy_material():
    """Return a cached simple material for LOW-detail proxy boxes.

    The full ISO_Container_Metal shader is applied at LOW detail when
    shader fidelity is requested; this simple fallback is provided for
    cases where speed matters more than visual quality.
    """
    mat_name = "ISO_Container_Proxy"
    if mat_name in bpy.data.materials:
        return bpy.data.materials[mat_name]

    mat = bpy.data.materials.new(name=mat_name)
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    nodes.clear()

    out = nodes.new("ShaderNodeOutputMaterial")
    out.location = (300, 0)

    bsdf = nodes.new("ShaderNodeBsdfPrincipled")
    bsdf.location = (60, 0)
    bsdf.distribution = "MULTI_GGX"
    bsdf.inputs["Base Color"].default_value = (0.35, 0.06, 0.04, 1.0)
    bsdf.inputs["Metallic"].default_value   = 0.55
    bsdf.inputs["Roughness"].default_value  = 0.70

    links.new(bsdf.outputs["BSDF"], out.inputs["Surface"])

    return mat


# ─────────────────────────────────────────────────────────────────────
#  Brand / company logo material
# ─────────────────────────────────────────────────────────────────────

def get_or_create_brand_material(company_name: str, hex_color: str):
    """Return (or create) a flat-colour material for a shipping company logo.

    One material datablock is created per company; subsequent calls with
    the same ``company_name`` return the cached version immediately.

    Args:
        company_name: e.g. ``"MAERSK"`` — used to form the material name.
        hex_color:    sRGB hex string, e.g. ``"#42A4D5"``.

    Returns:
        bpy.types.Material
    """
    mat_name = f"ISO_Brand_{company_name}"
    if mat_name in bpy.data.materials:
        return bpy.data.materials[mat_name]

    def _srgb_to_linear(c: float) -> float:
        """Approximate sRGB → linear conversion per IEC 61966-2-1."""
        return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4

    hx = hex_color.lstrip("#")
    if len(hx) == 6:
        r_lin = _srgb_to_linear(int(hx[0:2], 16) / 255.0)
        g_lin = _srgb_to_linear(int(hx[2:4], 16) / 255.0)
        b_lin = _srgb_to_linear(int(hx[4:6], 16) / 255.0)
    else:
        r_lin = g_lin = b_lin = 1.0

    mat = bpy.data.materials.new(name=mat_name)
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    nodes.clear()

    out = nodes.new("ShaderNodeOutputMaterial")
    out.location = (400, 0)

    bsdf = nodes.new("ShaderNodeBsdfPrincipled")
    bsdf.location = (160, 0)
    bsdf.distribution = "MULTI_GGX"
    bsdf.inputs["Base Color"].default_value         = (r_lin, g_lin, b_lin, 1.0)
    bsdf.inputs["Metallic"].default_value           = 0.0
    bsdf.inputs["Roughness"].default_value          = 0.85
    bsdf.inputs["Emission Color"].default_value     = (r_lin, g_lin, b_lin, 1.0)
    bsdf.inputs["Emission Strength"].default_value  = 0.15

    links.new(bsdf.outputs["BSDF"], out.inputs["Surface"])

    return mat
