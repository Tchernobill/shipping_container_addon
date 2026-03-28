import bpy
import mathutils
import os
import typing


def iso_container_shader_1_node_group(node_tree_names: dict[typing.Callable, str]):
    """Initialize ISO_Container_Shader node group"""
    iso_container_shader_1 = bpy.data.node_groups.new(type = 'ShaderNodeTree', name = "ISO_Container_Shader")

    iso_container_shader_1.color_tag = 'NONE'
    iso_container_shader_1.description = ""
    iso_container_shader_1.default_group_node_width = 140
    # iso_container_shader_1 interface

    # Socket Shader
    shader_socket = iso_container_shader_1.interface.new_socket(name="Shader", in_out='OUTPUT', socket_type='NodeSocketShader')
    shader_socket.attribute_domain = 'POINT'
    shader_socket.default_input = 'VALUE'
    shader_socket.structure_type = 'AUTO'

    # Initialize iso_container_shader_1 nodes

    # Node GroupOutput
    groupoutput = iso_container_shader_1.nodes.new("NodeGroupOutput")
    groupoutput.label = "GroupOutput"
    groupoutput.name = "GroupOutput"
    groupoutput.is_active_output = True

    # Node TexCoord
    texcoord = iso_container_shader_1.nodes.new("ShaderNodeTexCoord")
    texcoord.label = "TexCoord"
    texcoord.name = "TexCoord"
    texcoord.from_instancer = False

    # Node GeoCoord
    geocoord = iso_container_shader_1.nodes.new("ShaderNodeNewGeometry")
    geocoord.label = "GeoCoord"
    geocoord.name = "GeoCoord"

    # Node SepXYZ
    sepxyz = iso_container_shader_1.nodes.new("ShaderNodeSeparateXYZ")
    sepxyz.label = "SepXYZ"
    sepxyz.name = "SepXYZ"

    # Node Mapping
    mapping = iso_container_shader_1.nodes.new("ShaderNodeMapping")
    mapping.label = "Mapping"
    mapping.name = "Mapping"
    mapping.vector_type = 'POINT'
    # Location
    mapping.inputs[1].default_value = (0.0, 0.0, 0.0)
    # Rotation
    mapping.inputs[2].default_value = (0.0, 0.0, 0.0)
    # Scale
    mapping.inputs[3].default_value = (1.0, 1.0, 1.0)

    # Node Attr_Seed
    attr_seed = iso_container_shader_1.nodes.new("ShaderNodeAttribute")
    attr_seed.label = "Attr_Seed"
    attr_seed.name = "Attr_Seed"
    attr_seed.attribute_name = "container_seed"
    attr_seed.attribute_type = 'OBJECT'

    # Node Attr_Rust
    attr_rust = iso_container_shader_1.nodes.new("ShaderNodeAttribute")
    attr_rust.label = "Attr_Rust"
    attr_rust.name = "Attr_Rust"
    attr_rust.attribute_name = "shader_rust_strength"
    attr_rust.attribute_type = 'OBJECT'

    # Node Attr_StainI
    attr_staini = iso_container_shader_1.nodes.new("ShaderNodeAttribute")
    attr_staini.label = "Attr_StainI"
    attr_staini.name = "Attr_StainI"
    attr_staini.attribute_name = "shader_stain_intensity"
    attr_staini.attribute_type = 'OBJECT'

    # Node Attr_DustI
    attr_dusti = iso_container_shader_1.nodes.new("ShaderNodeAttribute")
    attr_dusti.label = "Attr_DustI"
    attr_dusti.name = "Attr_DustI"
    attr_dusti.attribute_name = "shader_dust_intensity"
    attr_dusti.attribute_type = 'OBJECT'

    # Node Attr_Scratch
    attr_scratch = iso_container_shader_1.nodes.new("ShaderNodeAttribute")
    attr_scratch.label = "Attr_Scratch"
    attr_scratch.name = "Attr_Scratch"
    attr_scratch.attribute_name = "shader_scratch_intensity"
    attr_scratch.attribute_type = 'OBJECT'

    # Node Attr_ColOvr
    attr_colovr = iso_container_shader_1.nodes.new("ShaderNodeAttribute")
    attr_colovr.label = "Attr_ColOvr"
    attr_colovr.name = "Attr_ColOvr"
    attr_colovr.attribute_name = "shader_color_override"
    attr_colovr.attribute_type = 'OBJECT'

    # Node Attr_ColAmt
    attr_colamt = iso_container_shader_1.nodes.new("ShaderNodeAttribute")
    attr_colamt.label = "Attr_ColAmt"
    attr_colamt.name = "Attr_ColAmt"
    attr_colamt.attribute_name = "shader_color_override_amt"
    attr_colamt.attribute_type = 'OBJECT'

    # Node CR_Palette
    cr_palette = iso_container_shader_1.nodes.new("ShaderNodeValToRGB")
    cr_palette.label = "CR_Palette"
    cr_palette.name = "CR_Palette"
    cr_palette.color_ramp.color_mode = 'RGB'
    cr_palette.color_ramp.hue_interpolation = 'NEAR'
    cr_palette.color_ramp.interpolation = 'CONSTANT'

    # Initialize color ramp elements
    cr_palette.color_ramp.elements.remove(cr_palette.color_ramp.elements[0])
    cr_palette_cre_0 = cr_palette.color_ramp.elements[0]
    cr_palette_cre_0.position = 0.0
    cr_palette_cre_0.alpha = 1.0
    cr_palette_cre_0.color = (0.02, 0.09, 0.27, 1.0)

    cr_palette_cre_1 = cr_palette.color_ramp.elements.new(0.125)
    cr_palette_cre_1.alpha = 1.0
    cr_palette_cre_1.color = (0.01, 0.02, 0.06, 1.0)

    cr_palette_cre_2 = cr_palette.color_ramp.elements.new(0.25)
    cr_palette_cre_2.alpha = 1.0
    cr_palette_cre_2.color = (0.03, 0.13, 0.38, 1.0)

    cr_palette_cre_3 = cr_palette.color_ramp.elements.new(0.375)
    cr_palette_cre_3.alpha = 1.0
    cr_palette_cre_3.color = (0.29, 0.05, 0.03, 1.0)

    cr_palette_cre_4 = cr_palette.color_ramp.elements.new(0.5)
    cr_palette_cre_4.alpha = 1.0
    cr_palette_cre_4.color = (0.18, 0.03, 0.02, 1.0)

    cr_palette_cre_5 = cr_palette.color_ramp.elements.new(0.625)
    cr_palette_cre_5.alpha = 1.0
    cr_palette_cre_5.color = (0.12, 0.02, 0.01, 1.0)

    cr_palette_cre_6 = cr_palette.color_ramp.elements.new(0.75)
    cr_palette_cre_6.alpha = 1.0
    cr_palette_cre_6.color = (0.01, 0.06, 0.01, 1.0)

    cr_palette_cre_7 = cr_palette.color_ramp.elements.new(0.875)
    cr_palette_cre_7.alpha = 1.0
    cr_palette_cre_7.color = (0.22, 0.22, 0.22, 1.0)


    # Node N_Roughness
    n_roughness = iso_container_shader_1.nodes.new("ShaderNodeTexNoise")
    n_roughness.label = "N_Roughness"
    n_roughness.name = "N_Roughness"
    n_roughness.noise_dimensions = '3D'
    n_roughness.noise_type = 'FBM'
    n_roughness.normalize = True
    # Scale
    n_roughness.inputs[2].default_value = 3.5
    # Detail
    n_roughness.inputs[3].default_value = 15.0
    # Roughness
    n_roughness.inputs[4].default_value = 0.76
    # Lacunarity
    n_roughness.inputs[5].default_value = 2.0
    # Distortion
    n_roughness.inputs[8].default_value = 0.0

    # Node CR_Roughness
    cr_roughness = iso_container_shader_1.nodes.new("ShaderNodeValToRGB")
    cr_roughness.label = "CR_Roughness"
    cr_roughness.name = "CR_Roughness"
    cr_roughness.color_ramp.color_mode = 'RGB'
    cr_roughness.color_ramp.hue_interpolation = 'NEAR'
    cr_roughness.color_ramp.interpolation = 'EASE'

    # Initialize color ramp elements
    cr_roughness.color_ramp.elements.remove(cr_roughness.color_ramp.elements[0])
    cr_roughness_cre_0 = cr_roughness.color_ramp.elements[0]
    cr_roughness_cre_0.position = 0.0
    cr_roughness_cre_0.alpha = 1.0
    cr_roughness_cre_0.color = (0.36, 0.36, 0.36, 1.0)

    cr_roughness_cre_1 = cr_roughness.color_ramp.elements.new(1.0)
    cr_roughness_cre_1.alpha = 1.0
    cr_roughness_cre_1.color = (1.0, 1.0, 1.0, 1.0)


    # Node N_Specular
    n_specular = iso_container_shader_1.nodes.new("ShaderNodeTexNoise")
    n_specular.label = "N_Specular"
    n_specular.name = "N_Specular"
    n_specular.noise_dimensions = '3D'
    n_specular.noise_type = 'FBM'
    n_specular.normalize = True
    # Scale
    n_specular.inputs[2].default_value = 5.0
    # Detail
    n_specular.inputs[3].default_value = 10.0
    # Roughness
    n_specular.inputs[4].default_value = 0.76
    # Lacunarity
    n_specular.inputs[5].default_value = 2.0
    # Distortion
    n_specular.inputs[8].default_value = 0.0

    # Node CR_Specular
    cr_specular = iso_container_shader_1.nodes.new("ShaderNodeValToRGB")
    cr_specular.label = "CR_Specular"
    cr_specular.name = "CR_Specular"
    cr_specular.color_ramp.color_mode = 'RGB'
    cr_specular.color_ramp.hue_interpolation = 'NEAR'
    cr_specular.color_ramp.interpolation = 'EASE'

    # Initialize color ramp elements
    cr_specular.color_ramp.elements.remove(cr_specular.color_ramp.elements[0])
    cr_specular_cre_0 = cr_specular.color_ramp.elements[0]
    cr_specular_cre_0.position = 0.0
    cr_specular_cre_0.alpha = 1.0
    cr_specular_cre_0.color = (0.36, 0.36, 0.36, 1.0)

    cr_specular_cre_1 = cr_specular.color_ramp.elements.new(1.0)
    cr_specular_cre_1.alpha = 1.0
    cr_specular_cre_1.color = (1.0, 1.0, 1.0, 1.0)


    # Node Geometry_Normals
    geometry_normals = iso_container_shader_1.nodes.new("ShaderNodeNewGeometry")
    geometry_normals.label = "Geometry_Normals"
    geometry_normals.name = "Geometry_Normals"

    # Node Bevel
    bevel = iso_container_shader_1.nodes.new("ShaderNodeBevel")
    bevel.label = "Bevel"
    bevel.name = "Bevel"
    bevel.samples = 4
    # Radius
    bevel.inputs[0].default_value = 0.05
    # Normal
    bevel.inputs[1].default_value = (0.0, 0.0, 0.0)

    # Node VM_Dot
    vm_dot = iso_container_shader_1.nodes.new("ShaderNodeVectorMath")
    vm_dot.label = "VM_Dot"
    vm_dot.name = "VM_Dot"
    vm_dot.operation = 'DOT_PRODUCT'

    # Node CR_EdgeMask
    cr_edgemask = iso_container_shader_1.nodes.new("ShaderNodeValToRGB")
    cr_edgemask.label = "CR_EdgeMask"
    cr_edgemask.name = "CR_EdgeMask"
    cr_edgemask.color_ramp.color_mode = 'RGB'
    cr_edgemask.color_ramp.hue_interpolation = 'NEAR'
    cr_edgemask.color_ramp.interpolation = 'CARDINAL'

    # Initialize color ramp elements
    cr_edgemask.color_ramp.elements.remove(cr_edgemask.color_ramp.elements[0])
    cr_edgemask_cre_0 = cr_edgemask.color_ramp.elements[0]
    cr_edgemask_cre_0.position = 0.95
    cr_edgemask_cre_0.alpha = 1.0
    cr_edgemask_cre_0.color = (1.0, 1.0, 1.0, 1.0)

    cr_edgemask_cre_1 = cr_edgemask.color_ramp.elements.new(1.0)
    cr_edgemask_cre_1.alpha = 1.0
    cr_edgemask_cre_1.color = (0.0, 0.0, 0.0, 1.0)


    # Node N_RustPat
    n_rustpat = iso_container_shader_1.nodes.new("ShaderNodeTexNoise")
    n_rustpat.label = "N_RustPat"
    n_rustpat.name = "N_RustPat"
    n_rustpat.noise_dimensions = '3D'
    n_rustpat.noise_type = 'MULTIFRACTAL'
    n_rustpat.normalize = False
    # Scale
    n_rustpat.inputs[2].default_value = 1.0
    # Detail
    n_rustpat.inputs[3].default_value = 14.0
    # Roughness
    n_rustpat.inputs[4].default_value = 1.0
    # Lacunarity
    n_rustpat.inputs[5].default_value = 1.55
    # Distortion
    n_rustpat.inputs[8].default_value = 0.0

    # Node CR_RustPat
    cr_rustpat = iso_container_shader_1.nodes.new("ShaderNodeValToRGB")
    cr_rustpat.label = "CR_RustPat"
    cr_rustpat.name = "CR_RustPat"
    cr_rustpat.color_ramp.color_mode = 'RGB'
    cr_rustpat.color_ramp.hue_interpolation = 'NEAR'
    cr_rustpat.color_ramp.interpolation = 'LINEAR'

    # Initialize color ramp elements
    cr_rustpat.color_ramp.elements.remove(cr_rustpat.color_ramp.elements[0])
    cr_rustpat_cre_0 = cr_rustpat.color_ramp.elements[0]
    cr_rustpat_cre_0.position = 0.85
    cr_rustpat_cre_0.alpha = 1.0
    cr_rustpat_cre_0.color = (0.0, 0.0, 0.0, 1.0)

    cr_rustpat_cre_1 = cr_rustpat.color_ramp.elements.new(1.0)
    cr_rustpat_cre_1.alpha = 1.0
    cr_rustpat_cre_1.color = (1.0, 1.0, 1.0, 1.0)


    # Node MX_RustMask
    mx_rustmask = iso_container_shader_1.nodes.new("ShaderNodeMix")
    mx_rustmask.label = "MX_RustMask"
    mx_rustmask.name = "MX_RustMask"
    mx_rustmask.blend_type = 'MULTIPLY'
    mx_rustmask.clamp_factor = True
    mx_rustmask.clamp_result = False
    mx_rustmask.data_type = 'RGBA'
    mx_rustmask.factor_mode = 'UNIFORM'
    # Factor_Float
    mx_rustmask.inputs[0].default_value = 1.0

    # Node Math_Rust
    math_rust = iso_container_shader_1.nodes.new("ShaderNodeMath")
    math_rust.label = "Math_Rust"
    math_rust.name = "Math_Rust"
    math_rust.operation = 'MULTIPLY'
    math_rust.use_clamp = False

    # Node W_Mul_N_RustBump
    w_mul_n_rustbump = iso_container_shader_1.nodes.new("ShaderNodeMath")
    w_mul_n_rustbump.label = "W_Mul_N_RustBump"
    w_mul_n_rustbump.name = "W_Mul_N_RustBump"
    w_mul_n_rustbump.operation = 'MULTIPLY'
    w_mul_n_rustbump.use_clamp = False
    # Value_001
    w_mul_n_rustbump.inputs[1].default_value = 17.39

    # Node W_Add_N_RustBump
    w_add_n_rustbump = iso_container_shader_1.nodes.new("ShaderNodeMath")
    w_add_n_rustbump.label = "W_Add_N_RustBump"
    w_add_n_rustbump.name = "W_Add_N_RustBump"
    w_add_n_rustbump.operation = 'ADD'
    w_add_n_rustbump.use_clamp = False
    # Value
    w_add_n_rustbump.inputs[0].default_value = 0.0

    # Node N_RustBump
    n_rustbump = iso_container_shader_1.nodes.new("ShaderNodeTexNoise")
    n_rustbump.label = "N_RustBump"
    n_rustbump.name = "N_RustBump"
    n_rustbump.noise_dimensions = '3D'
    n_rustbump.noise_type = 'FBM'
    n_rustbump.normalize = True
    # Scale
    n_rustbump.inputs[2].default_value = 350.0
    # Detail
    n_rustbump.inputs[3].default_value = 2.0
    # Roughness
    n_rustbump.inputs[4].default_value = 0.5
    # Lacunarity
    n_rustbump.inputs[5].default_value = 2.0
    # Distortion
    n_rustbump.inputs[8].default_value = 0.0

    # Node CR_RustBump
    cr_rustbump = iso_container_shader_1.nodes.new("ShaderNodeValToRGB")
    cr_rustbump.label = "CR_RustBump"
    cr_rustbump.name = "CR_RustBump"
    cr_rustbump.color_ramp.color_mode = 'RGB'
    cr_rustbump.color_ramp.hue_interpolation = 'NEAR'
    cr_rustbump.color_ramp.interpolation = 'LINEAR'

    # Initialize color ramp elements
    cr_rustbump.color_ramp.elements.remove(cr_rustbump.color_ramp.elements[0])
    cr_rustbump_cre_0 = cr_rustbump.color_ramp.elements[0]
    cr_rustbump_cre_0.position = 0.0
    cr_rustbump_cre_0.alpha = 1.0
    cr_rustbump_cre_0.color = (1.0, 1.0, 1.0, 1.0)

    cr_rustbump_cre_1 = cr_rustbump.color_ramp.elements.new(0.42)
    cr_rustbump_cre_1.alpha = 1.0
    cr_rustbump_cre_1.color = (0.15, 0.05, 0.02, 1.0)

    cr_rustbump_cre_2 = cr_rustbump.color_ramp.elements.new(1.0)
    cr_rustbump_cre_2.alpha = 1.0
    cr_rustbump_cre_2.color = (0.21, 0.03, 0.02, 1.0)


    # Node Bump
    bump = iso_container_shader_1.nodes.new("ShaderNodeBump")
    bump.label = "Bump"
    bump.name = "Bump"
    bump.invert = False
    # Strength
    bump.inputs[0].default_value = 0.21
    # Distance
    bump.inputs[1].default_value = 1.0
    # Filter Width
    bump.inputs[2].default_value = 0.10
    # Normal
    bump.inputs[4].default_value = (0.0, 0.0, 0.0)

    # Node MP_Stain
    mp_stain = iso_container_shader_1.nodes.new("ShaderNodeMapping")
    mp_stain.label = "MP_Stain"
    mp_stain.name = "MP_Stain"
    mp_stain.vector_type = 'POINT'
    # Location
    mp_stain.inputs[1].default_value = (0.0, 0.0, 0.0)
    # Rotation
    mp_stain.inputs[2].default_value = (0.0, 0.0, 0.0)
    # Scale
    mp_stain.inputs[3].default_value = (8.0, 8.0, 0.25)

    # Node W_Mul_N_Stain
    w_mul_n_stain = iso_container_shader_1.nodes.new("ShaderNodeMath")
    w_mul_n_stain.label = "W_Mul_N_Stain"
    w_mul_n_stain.name = "W_Mul_N_Stain"
    w_mul_n_stain.operation = 'MULTIPLY'
    w_mul_n_stain.use_clamp = False
    # Value_001
    w_mul_n_stain.inputs[1].default_value = 11.93

    # Node W_Add_N_Stain
    w_add_n_stain = iso_container_shader_1.nodes.new("ShaderNodeMath")
    w_add_n_stain.label = "W_Add_N_Stain"
    w_add_n_stain.name = "W_Add_N_Stain"
    w_add_n_stain.operation = 'ADD'
    w_add_n_stain.use_clamp = False
    # Value
    w_add_n_stain.inputs[0].default_value = 0.0

    # Node N_Stain
    n_stain = iso_container_shader_1.nodes.new("ShaderNodeTexNoise")
    n_stain.label = "N_Stain"
    n_stain.name = "N_Stain"
    n_stain.noise_dimensions = '4D'
    n_stain.noise_type = 'FBM'
    n_stain.normalize = True
    # Scale
    n_stain.inputs[2].default_value = 14.0
    # Detail
    n_stain.inputs[3].default_value = 3.0
    # Roughness
    n_stain.inputs[4].default_value = 0.65
    # Lacunarity
    n_stain.inputs[5].default_value = 2.0
    # Distortion
    n_stain.inputs[8].default_value = 0.0

    # Node CR_Stain
    cr_stain = iso_container_shader_1.nodes.new("ShaderNodeValToRGB")
    cr_stain.label = "CR_Stain"
    cr_stain.name = "CR_Stain"
    cr_stain.color_ramp.color_mode = 'RGB'
    cr_stain.color_ramp.hue_interpolation = 'NEAR'
    cr_stain.color_ramp.interpolation = 'LINEAR'

    # Initialize color ramp elements
    cr_stain.color_ramp.elements.remove(cr_stain.color_ramp.elements[0])
    cr_stain_cre_0 = cr_stain.color_ramp.elements[0]
    cr_stain_cre_0.position = 0.55
    cr_stain_cre_0.alpha = 1.0
    cr_stain_cre_0.color = (0.0, 0.0, 0.0, 1.0)

    cr_stain_cre_1 = cr_stain.color_ramp.elements.new(0.80)
    cr_stain_cre_1.alpha = 1.0
    cr_stain_cre_1.color = (1.0, 1.0, 1.0, 1.0)


    # Node MR_StainH
    mr_stainh = iso_container_shader_1.nodes.new("ShaderNodeMapRange")
    mr_stainh.label = "MR_StainH"
    mr_stainh.name = "MR_StainH"
    mr_stainh.clamp = True
    mr_stainh.data_type = 'FLOAT'
    mr_stainh.interpolation_type = 'LINEAR'
    # From Min
    mr_stainh.inputs[1].default_value = 1.29
    # From Max
    mr_stainh.inputs[2].default_value = 2.59
    # To Min
    mr_stainh.inputs[3].default_value = 0.0
    # To Max
    mr_stainh.inputs[4].default_value = 1.0

    # Node CR_StainH
    cr_stainh = iso_container_shader_1.nodes.new("ShaderNodeValToRGB")
    cr_stainh.label = "CR_StainH"
    cr_stainh.name = "CR_StainH"
    cr_stainh.color_ramp.color_mode = 'RGB'
    cr_stainh.color_ramp.hue_interpolation = 'NEAR'
    cr_stainh.color_ramp.interpolation = 'EASE'

    # Initialize color ramp elements
    cr_stainh.color_ramp.elements.remove(cr_stainh.color_ramp.elements[0])
    cr_stainh_cre_0 = cr_stainh.color_ramp.elements[0]
    cr_stainh_cre_0.position = 0.0
    cr_stainh_cre_0.alpha = 1.0
    cr_stainh_cre_0.color = (0.0, 0.0, 0.0, 1.0)

    cr_stainh_cre_1 = cr_stainh.color_ramp.elements.new(1.0)
    cr_stainh_cre_1.alpha = 1.0
    cr_stainh_cre_1.color = (1.0, 1.0, 1.0, 1.0)


    # Node Math_Stain
    math_stain = iso_container_shader_1.nodes.new("ShaderNodeMath")
    math_stain.label = "Math_Stain"
    math_stain.name = "Math_Stain"
    math_stain.operation = 'MULTIPLY'
    math_stain.use_clamp = False

    # Node Math_StainI
    math_staini = iso_container_shader_1.nodes.new("ShaderNodeMath")
    math_staini.label = "Math_StainI"
    math_staini.name = "Math_StainI"
    math_staini.operation = 'MULTIPLY'
    math_staini.use_clamp = False

    # Node MR_DustH
    mr_dusth = iso_container_shader_1.nodes.new("ShaderNodeMapRange")
    mr_dusth.label = "MR_DustH"
    mr_dusth.name = "MR_DustH"
    mr_dusth.clamp = True
    mr_dusth.data_type = 'FLOAT'
    mr_dusth.interpolation_type = 'LINEAR'
    # From Min
    mr_dusth.inputs[1].default_value = 0.0
    # From Max
    mr_dusth.inputs[2].default_value = 0.5
    # To Min
    mr_dusth.inputs[3].default_value = 1.0
    # To Max
    mr_dusth.inputs[4].default_value = 0.0

    # Node W_Mul_N_Dust
    w_mul_n_dust = iso_container_shader_1.nodes.new("ShaderNodeMath")
    w_mul_n_dust.label = "W_Mul_N_Dust"
    w_mul_n_dust.name = "W_Mul_N_Dust"
    w_mul_n_dust.operation = 'MULTIPLY'
    w_mul_n_dust.use_clamp = False
    # Value_001
    w_mul_n_dust.inputs[1].default_value = 3.71

    # Node W_Add_N_Dust
    w_add_n_dust = iso_container_shader_1.nodes.new("ShaderNodeMath")
    w_add_n_dust.label = "W_Add_N_Dust"
    w_add_n_dust.name = "W_Add_N_Dust"
    w_add_n_dust.operation = 'ADD'
    w_add_n_dust.use_clamp = False
    # Value
    w_add_n_dust.inputs[0].default_value = 0.0

    # Node N_Dust
    n_dust = iso_container_shader_1.nodes.new("ShaderNodeTexNoise")
    n_dust.label = "N_Dust"
    n_dust.name = "N_Dust"
    n_dust.noise_dimensions = '4D'
    n_dust.noise_type = 'FBM'
    n_dust.normalize = True
    # Scale
    n_dust.inputs[2].default_value = 5.0
    # Detail
    n_dust.inputs[3].default_value = 4.0
    # Roughness
    n_dust.inputs[4].default_value = 0.70
    # Lacunarity
    n_dust.inputs[5].default_value = 2.0
    # Distortion
    n_dust.inputs[8].default_value = 0.0

    # Node Math_DustH
    math_dusth = iso_container_shader_1.nodes.new("ShaderNodeMath")
    math_dusth.label = "Math_DustH"
    math_dusth.name = "Math_DustH"
    math_dusth.operation = 'MULTIPLY'
    math_dusth.use_clamp = False

    # Node CR_DustH
    cr_dusth = iso_container_shader_1.nodes.new("ShaderNodeValToRGB")
    cr_dusth.label = "CR_DustH"
    cr_dusth.name = "CR_DustH"
    cr_dusth.color_ramp.color_mode = 'RGB'
    cr_dusth.color_ramp.hue_interpolation = 'NEAR'
    cr_dusth.color_ramp.interpolation = 'EASE'

    # Initialize color ramp elements
    cr_dusth.color_ramp.elements.remove(cr_dusth.color_ramp.elements[0])
    cr_dusth_cre_0 = cr_dusth.color_ramp.elements[0]
    cr_dusth_cre_0.position = 0.0
    cr_dusth_cre_0.alpha = 1.0
    cr_dusth_cre_0.color = (0.0, 0.0, 0.0, 1.0)

    cr_dusth_cre_1 = cr_dusth.color_ramp.elements.new(1.0)
    cr_dusth_cre_1.alpha = 1.0
    cr_dusth_cre_1.color = (1.0, 1.0, 1.0, 1.0)


    # Node AO
    ao = iso_container_shader_1.nodes.new("ShaderNodeAmbientOcclusion")
    ao.label = "AO"
    ao.name = "AO"
    ao.inside = False
    ao.only_local = False
    ao.samples = 16
    # Color
    ao.inputs[0].default_value = (1.0, 1.0, 1.0, 1.0)
    # Distance
    ao.inputs[1].default_value = 1.0
    # Normal
    ao.inputs[2].default_value = (0.0, 0.0, 0.0)

    # Node Math_AOInv
    math_aoinv = iso_container_shader_1.nodes.new("ShaderNodeMath")
    math_aoinv.label = "Math_AOInv"
    math_aoinv.name = "Math_AOInv"
    math_aoinv.operation = 'SUBTRACT'
    math_aoinv.use_clamp = False
    # Value
    math_aoinv.inputs[0].default_value = 1.0

    # Node CR_AO
    cr_ao = iso_container_shader_1.nodes.new("ShaderNodeValToRGB")
    cr_ao.label = "CR_AO"
    cr_ao.name = "CR_AO"
    cr_ao.color_ramp.color_mode = 'RGB'
    cr_ao.color_ramp.hue_interpolation = 'NEAR'
    cr_ao.color_ramp.interpolation = 'EASE'

    # Initialize color ramp elements
    cr_ao.color_ramp.elements.remove(cr_ao.color_ramp.elements[0])
    cr_ao_cre_0 = cr_ao.color_ramp.elements[0]
    cr_ao_cre_0.position = 0.0
    cr_ao_cre_0.alpha = 1.0
    cr_ao_cre_0.color = (0.0, 0.0, 0.0, 1.0)

    cr_ao_cre_1 = cr_ao.color_ramp.elements.new(0.35)
    cr_ao_cre_1.alpha = 1.0
    cr_ao_cre_1.color = (0.0, 0.0, 0.0, 1.0)

    cr_ao_cre_2 = cr_ao.color_ramp.elements.new(0.65)
    cr_ao_cre_2.alpha = 1.0
    cr_ao_cre_2.color = (1.0, 1.0, 1.0, 1.0)

    cr_ao_cre_3 = cr_ao.color_ramp.elements.new(1.0)
    cr_ao_cre_3.alpha = 1.0
    cr_ao_cre_3.color = (1.0, 1.0, 1.0, 1.0)


    # Node Math_DustMax
    math_dustmax = iso_container_shader_1.nodes.new("ShaderNodeMath")
    math_dustmax.label = "Math_DustMax"
    math_dustmax.name = "Math_DustMax"
    math_dustmax.operation = 'MAXIMUM'
    math_dustmax.use_clamp = False

    # Node Math_DustI
    math_dusti = iso_container_shader_1.nodes.new("ShaderNodeMath")
    math_dusti.label = "Math_DustI"
    math_dusti.name = "Math_DustI"
    math_dusti.operation = 'MULTIPLY'
    math_dusti.use_clamp = True

    # Node VecRot_Scratch
    vecrot_scratch = iso_container_shader_1.nodes.new("ShaderNodeVectorRotate")
    vecrot_scratch.label = "VecRot_Scratch"
    vecrot_scratch.name = "VecRot_Scratch"
    vecrot_scratch.invert = False
    vecrot_scratch.rotation_type = 'X_AXIS'
    # Center
    vecrot_scratch.inputs[1].default_value = (0.0, 0.0, 0.0)
    # Angle
    vecrot_scratch.inputs[3].default_value = -1.49

    # Node MP_Wave
    mp_wave = iso_container_shader_1.nodes.new("ShaderNodeMapping")
    mp_wave.label = "MP_Wave"
    mp_wave.name = "MP_Wave"
    mp_wave.vector_type = 'POINT'
    # Location
    mp_wave.inputs[1].default_value = (0.0, 0.0, 0.0)
    # Rotation
    mp_wave.inputs[2].default_value = (0.0, 0.0, 0.0)
    # Scale
    mp_wave.inputs[3].default_value = (3.60, 1.0, 1.0)

    # Node WaveTex
    wavetex = iso_container_shader_1.nodes.new("ShaderNodeTexWave")
    wavetex.label = "WaveTex"
    wavetex.name = "WaveTex"
    wavetex.bands_direction = 'DIAGONAL'
    wavetex.rings_direction = 'X'
    wavetex.wave_profile = 'SIN'
    wavetex.wave_type = 'BANDS'
    # Scale
    wavetex.inputs[1].default_value = 1.0
    # Distortion
    wavetex.inputs[2].default_value = 0.0
    # Detail
    wavetex.inputs[3].default_value = 0.90
    # Detail Scale
    wavetex.inputs[4].default_value = 1.0
    # Detail Roughness
    wavetex.inputs[5].default_value = 0.5
    # Phase Offset
    wavetex.inputs[6].default_value = 1.57

    # Node MP_ScratchCoord
    mp_scratchcoord = iso_container_shader_1.nodes.new("ShaderNodeMapping")
    mp_scratchcoord.label = "MP_ScratchCoord"
    mp_scratchcoord.name = "MP_ScratchCoord"
    mp_scratchcoord.vector_type = 'POINT'
    # Location
    mp_scratchcoord.inputs[1].default_value = (0.0, 0.0, 0.0)
    # Rotation
    mp_scratchcoord.inputs[2].default_value = (0.01, -0.09, -0.34)
    # Scale
    mp_scratchcoord.inputs[3].default_value = (1.0, 1.0, 1.0)

    # Node Sep_Scratch
    sep_scratch = iso_container_shader_1.nodes.new("ShaderNodeSeparateXYZ")
    sep_scratch.label = "Sep_Scratch"
    sep_scratch.name = "Sep_Scratch"

    # Node Comb_Scratch
    comb_scratch = iso_container_shader_1.nodes.new("ShaderNodeCombineXYZ")
    comb_scratch.label = "Comb_Scratch"
    comb_scratch.name = "Comb_Scratch"

    # Node Math_WaveScale
    math_wavescale = iso_container_shader_1.nodes.new("ShaderNodeMath")
    math_wavescale.label = "Math_WaveScale"
    math_wavescale.name = "Math_WaveScale"
    math_wavescale.operation = 'MULTIPLY_ADD'
    math_wavescale.use_clamp = False
    # Value_001
    math_wavescale.inputs[1].default_value = 5.0
    # Value_002
    math_wavescale.inputs[2].default_value = 0.5

    # Node W_Mul_N_Scratch
    w_mul_n_scratch = iso_container_shader_1.nodes.new("ShaderNodeMath")
    w_mul_n_scratch.label = "W_Mul_N_Scratch"
    w_mul_n_scratch.name = "W_Mul_N_Scratch"
    w_mul_n_scratch.operation = 'MULTIPLY'
    w_mul_n_scratch.use_clamp = False
    # Value_001
    w_mul_n_scratch.inputs[1].default_value = 19.13

    # Node W_Add_N_Scratch
    w_add_n_scratch = iso_container_shader_1.nodes.new("ShaderNodeMath")
    w_add_n_scratch.label = "W_Add_N_Scratch"
    w_add_n_scratch.name = "W_Add_N_Scratch"
    w_add_n_scratch.operation = 'ADD'
    w_add_n_scratch.use_clamp = False
    # Value
    w_add_n_scratch.inputs[0].default_value = 0.0

    # Node N_ScratchDist
    n_scratchdist = iso_container_shader_1.nodes.new("ShaderNodeTexNoise")
    n_scratchdist.label = "N_ScratchDist"
    n_scratchdist.name = "N_ScratchDist"
    n_scratchdist.noise_dimensions = '4D'
    n_scratchdist.noise_type = 'FBM'
    n_scratchdist.normalize = False
    # Detail
    n_scratchdist.inputs[3].default_value = 14.0
    # Roughness
    n_scratchdist.inputs[4].default_value = 1.00
    # Lacunarity
    n_scratchdist.inputs[5].default_value = 1.55
    # Distortion
    n_scratchdist.inputs[8].default_value = 0.0

    # Node CR_Scratch
    cr_scratch = iso_container_shader_1.nodes.new("ShaderNodeValToRGB")
    cr_scratch.label = "CR_Scratch"
    cr_scratch.name = "CR_Scratch"
    cr_scratch.color_ramp.color_mode = 'RGB'
    cr_scratch.color_ramp.hue_interpolation = 'NEAR'
    cr_scratch.color_ramp.interpolation = 'LINEAR'

    # Initialize color ramp elements
    cr_scratch.color_ramp.elements.remove(cr_scratch.color_ramp.elements[0])
    cr_scratch_cre_0 = cr_scratch.color_ramp.elements[0]
    cr_scratch_cre_0.position = 0.68
    cr_scratch_cre_0.alpha = 1.0
    cr_scratch_cre_0.color = (0.0, 0.0, 0.0, 1.0)

    cr_scratch_cre_1 = cr_scratch.color_ramp.elements.new(0.82)
    cr_scratch_cre_1.alpha = 1.0
    cr_scratch_cre_1.color = (1.0, 1.0, 1.0, 1.0)


    # Node Math_ScratchI
    math_scratchi = iso_container_shader_1.nodes.new("ShaderNodeMath")
    math_scratchi.label = "Math_ScratchI"
    math_scratchi.name = "Math_ScratchI"
    math_scratchi.operation = 'MULTIPLY'
    math_scratchi.use_clamp = False

    # Node MX_Stain
    mx_stain = iso_container_shader_1.nodes.new("ShaderNodeMix")
    mx_stain.label = "MX_Stain"
    mx_stain.name = "MX_Stain"
    mx_stain.blend_type = 'MULTIPLY'
    mx_stain.clamp_factor = True
    mx_stain.clamp_result = False
    mx_stain.data_type = 'RGBA'
    mx_stain.factor_mode = 'UNIFORM'
    # B_Color
    mx_stain.inputs[7].default_value = (0.07, 0.05, 0.02, 1.0)

    # Node MX_Dust
    mx_dust = iso_container_shader_1.nodes.new("ShaderNodeMix")
    mx_dust.label = "MX_Dust"
    mx_dust.name = "MX_Dust"
    mx_dust.blend_type = 'MIX'
    mx_dust.clamp_factor = True
    mx_dust.clamp_result = False
    mx_dust.data_type = 'RGBA'
    mx_dust.factor_mode = 'UNIFORM'
    # B_Color
    mx_dust.inputs[7].default_value = (0.38, 0.30, 0.17, 1.0)

    # Node MX_Scratch
    mx_scratch = iso_container_shader_1.nodes.new("ShaderNodeMix")
    mx_scratch.label = "MX_Scratch"
    mx_scratch.name = "MX_Scratch"
    mx_scratch.blend_type = 'SCREEN'
    mx_scratch.clamp_factor = True
    mx_scratch.clamp_result = False
    mx_scratch.data_type = 'RGBA'
    mx_scratch.factor_mode = 'UNIFORM'
    # B_Color
    mx_scratch.inputs[7].default_value = (0.55, 0.5, 0.42, 1.0)

    # Node MX_Override
    mx_override = iso_container_shader_1.nodes.new("ShaderNodeMix")
    mx_override.label = "MX_Override"
    mx_override.name = "MX_Override"
    mx_override.blend_type = 'MIX'
    mx_override.clamp_factor = True
    mx_override.clamp_result = False
    mx_override.data_type = 'RGBA'
    mx_override.factor_mode = 'UNIFORM'

    # Node Math_EdgeRoughMul
    math_edgeroughmul = iso_container_shader_1.nodes.new("ShaderNodeMath")
    math_edgeroughmul.label = "Math_EdgeRoughMul"
    math_edgeroughmul.name = "Math_EdgeRoughMul"
    math_edgeroughmul.operation = 'MULTIPLY'
    math_edgeroughmul.use_clamp = False
    # Value_001
    math_edgeroughmul.inputs[1].default_value = 0.30

    # Node Math_EdgeRoughAdd
    math_edgeroughadd = iso_container_shader_1.nodes.new("ShaderNodeMath")
    math_edgeroughadd.label = "Math_EdgeRoughAdd"
    math_edgeroughadd.name = "Math_EdgeRoughAdd"
    math_edgeroughadd.operation = 'ADD'
    math_edgeroughadd.use_clamp = True

    # Node BSDF_Paint
    bsdf_paint = iso_container_shader_1.nodes.new("ShaderNodeBsdfPrincipled")
    bsdf_paint.label = "BSDF_Paint"
    bsdf_paint.name = "BSDF_Paint"
    bsdf_paint.distribution = 'MULTI_GGX'
    bsdf_paint.subsurface_method = 'RANDOM_WALK'
    # Metallic
    bsdf_paint.inputs[1].default_value = 0.65
    # IOR
    bsdf_paint.inputs[3].default_value = 1.45
    # Alpha
    bsdf_paint.inputs[4].default_value = 1.0
    # Normal
    bsdf_paint.inputs[5].default_value = (0.0, 0.0, 0.0)
    # Diffuse Roughness
    bsdf_paint.inputs[7].default_value = 0.0
    # Subsurface Weight
    bsdf_paint.inputs[8].default_value = 0.0
    # Subsurface Radius
    bsdf_paint.inputs[9].default_value = (1.0, 0.20, 0.10)
    # Subsurface Scale
    bsdf_paint.inputs[10].default_value = 0.05
    # Subsurface Anisotropy
    bsdf_paint.inputs[12].default_value = 0.0
    # Specular Tint
    bsdf_paint.inputs[14].default_value = (1.0, 1.0, 1.0, 1.0)
    # Anisotropic
    bsdf_paint.inputs[15].default_value = 0.0
    # Anisotropic Rotation
    bsdf_paint.inputs[16].default_value = 0.0
    # Tangent
    bsdf_paint.inputs[17].default_value = (0.0, 0.0, 0.0)
    # Transmission Weight
    bsdf_paint.inputs[18].default_value = 0.0
    # Coat Weight
    bsdf_paint.inputs[19].default_value = 0.0
    # Coat Roughness
    bsdf_paint.inputs[20].default_value = 0.03
    # Coat IOR
    bsdf_paint.inputs[21].default_value = 1.5
    # Coat Tint
    bsdf_paint.inputs[22].default_value = (1.0, 1.0, 1.0, 1.0)
    # Coat Normal
    bsdf_paint.inputs[23].default_value = (0.0, 0.0, 0.0)
    # Sheen Weight
    bsdf_paint.inputs[24].default_value = 0.0
    # Sheen Roughness
    bsdf_paint.inputs[25].default_value = 0.5
    # Sheen Tint
    bsdf_paint.inputs[26].default_value = (1.0, 1.0, 1.0, 1.0)
    # Emission Color
    bsdf_paint.inputs[27].default_value = (1.0, 1.0, 1.0, 1.0)
    # Emission Strength
    bsdf_paint.inputs[28].default_value = 0.0
    # Thin Film Thickness
    bsdf_paint.inputs[29].default_value = 0.0
    # Thin Film IOR
    bsdf_paint.inputs[30].default_value = 1.33

    # Node BSDF_Worn
    bsdf_worn = iso_container_shader_1.nodes.new("ShaderNodeBsdfPrincipled")
    bsdf_worn.label = "BSDF_Worn"
    bsdf_worn.name = "BSDF_Worn"
    bsdf_worn.distribution = 'MULTI_GGX'
    bsdf_worn.subsurface_method = 'RANDOM_WALK'
    # Base Color
    bsdf_worn.inputs[0].default_value = (0.25, 0.22, 0.20, 1.0)
    # Metallic
    bsdf_worn.inputs[1].default_value = 0.80
    # IOR
    bsdf_worn.inputs[3].default_value = 1.45
    # Alpha
    bsdf_worn.inputs[4].default_value = 1.0
    # Normal
    bsdf_worn.inputs[5].default_value = (0.0, 0.0, 0.0)
    # Diffuse Roughness
    bsdf_worn.inputs[7].default_value = 0.0
    # Subsurface Weight
    bsdf_worn.inputs[8].default_value = 0.0
    # Subsurface Radius
    bsdf_worn.inputs[9].default_value = (1.0, 0.20, 0.10)
    # Subsurface Scale
    bsdf_worn.inputs[10].default_value = 0.05
    # Subsurface Anisotropy
    bsdf_worn.inputs[12].default_value = 0.0
    # Specular IOR Level
    bsdf_worn.inputs[13].default_value = 0.70
    # Specular Tint
    bsdf_worn.inputs[14].default_value = (1.0, 1.0, 1.0, 1.0)
    # Anisotropic
    bsdf_worn.inputs[15].default_value = 0.0
    # Anisotropic Rotation
    bsdf_worn.inputs[16].default_value = 0.0
    # Tangent
    bsdf_worn.inputs[17].default_value = (0.0, 0.0, 0.0)
    # Transmission Weight
    bsdf_worn.inputs[18].default_value = 0.0
    # Coat Weight
    bsdf_worn.inputs[19].default_value = 0.0
    # Coat Roughness
    bsdf_worn.inputs[20].default_value = 0.03
    # Coat IOR
    bsdf_worn.inputs[21].default_value = 1.5
    # Coat Tint
    bsdf_worn.inputs[22].default_value = (1.0, 1.0, 1.0, 1.0)
    # Coat Normal
    bsdf_worn.inputs[23].default_value = (0.0, 0.0, 0.0)
    # Sheen Weight
    bsdf_worn.inputs[24].default_value = 0.0
    # Sheen Roughness
    bsdf_worn.inputs[25].default_value = 0.5
    # Sheen Tint
    bsdf_worn.inputs[26].default_value = (1.0, 1.0, 1.0, 1.0)
    # Emission Color
    bsdf_worn.inputs[27].default_value = (1.0, 1.0, 1.0, 1.0)
    # Emission Strength
    bsdf_worn.inputs[28].default_value = 0.0
    # Thin Film Thickness
    bsdf_worn.inputs[29].default_value = 0.0
    # Thin Film IOR
    bsdf_worn.inputs[30].default_value = 1.33

    # Node BSDF_Rust
    bsdf_rust = iso_container_shader_1.nodes.new("ShaderNodeBsdfPrincipled")
    bsdf_rust.label = "BSDF_Rust"
    bsdf_rust.name = "BSDF_Rust"
    bsdf_rust.distribution = 'MULTI_GGX'
    bsdf_rust.subsurface_method = 'RANDOM_WALK'
    # Metallic
    bsdf_rust.inputs[1].default_value = 0.75
    # Roughness
    bsdf_rust.inputs[2].default_value = 0.95
    # IOR
    bsdf_rust.inputs[3].default_value = 1.5
    # Alpha
    bsdf_rust.inputs[4].default_value = 1.0
    # Diffuse Roughness
    bsdf_rust.inputs[7].default_value = 0.0
    # Subsurface Weight
    bsdf_rust.inputs[8].default_value = 0.0
    # Subsurface Radius
    bsdf_rust.inputs[9].default_value = (1.0, 0.20, 0.10)
    # Subsurface Scale
    bsdf_rust.inputs[10].default_value = 0.05
    # Subsurface Anisotropy
    bsdf_rust.inputs[12].default_value = 0.0
    # Specular IOR Level
    bsdf_rust.inputs[13].default_value = 0.08
    # Specular Tint
    bsdf_rust.inputs[14].default_value = (1.0, 1.0, 1.0, 1.0)
    # Anisotropic
    bsdf_rust.inputs[15].default_value = 0.0
    # Anisotropic Rotation
    bsdf_rust.inputs[16].default_value = 0.0
    # Tangent
    bsdf_rust.inputs[17].default_value = (0.0, 0.0, 0.0)
    # Transmission Weight
    bsdf_rust.inputs[18].default_value = 0.0
    # Coat Weight
    bsdf_rust.inputs[19].default_value = 0.0
    # Coat Roughness
    bsdf_rust.inputs[20].default_value = 0.03
    # Coat IOR
    bsdf_rust.inputs[21].default_value = 1.5
    # Coat Tint
    bsdf_rust.inputs[22].default_value = (1.0, 1.0, 1.0, 1.0)
    # Coat Normal
    bsdf_rust.inputs[23].default_value = (0.0, 0.0, 0.0)
    # Sheen Weight
    bsdf_rust.inputs[24].default_value = 0.0
    # Sheen Roughness
    bsdf_rust.inputs[25].default_value = 0.5
    # Sheen Tint
    bsdf_rust.inputs[26].default_value = (1.0, 1.0, 1.0, 1.0)
    # Emission Color
    bsdf_rust.inputs[27].default_value = (1.0, 1.0, 1.0, 1.0)
    # Emission Strength
    bsdf_rust.inputs[28].default_value = 0.0
    # Thin Film Thickness
    bsdf_rust.inputs[29].default_value = 0.0
    # Thin Film IOR
    bsdf_rust.inputs[30].default_value = 1.33

    # Node Mix_Worn
    mix_worn = iso_container_shader_1.nodes.new("ShaderNodeMixShader")
    mix_worn.label = "Mix_Worn"
    mix_worn.name = "Mix_Worn"

    # Node Mix_Rust
    mix_rust = iso_container_shader_1.nodes.new("ShaderNodeMixShader")
    mix_rust.label = "Mix_Rust"
    mix_rust.name = "Mix_Rust"

    # Node Frame
    frame = iso_container_shader_1.nodes.new("NodeFrame")
    frame.label = "Dust"
    frame.name = "Frame"
    frame.label_size = 20
    frame.shrink = True

    # Node Frame.001
    frame_001 = iso_container_shader_1.nodes.new("NodeFrame")
    frame_001.label = "Stains"
    frame_001.name = "Frame.001"
    frame_001.label_size = 20
    frame_001.shrink = True

    # Node Frame.002
    frame_002 = iso_container_shader_1.nodes.new("NodeFrame")
    frame_002.label = "Scratch"
    frame_002.name = "Frame.002"
    frame_002.label_size = 20
    frame_002.shrink = True

    # Set parents
    iso_container_shader_1.nodes["Attr_StainI"].parent = iso_container_shader_1.nodes["Frame.001"]
    iso_container_shader_1.nodes["Attr_DustI"].parent = iso_container_shader_1.nodes["Frame"]
    iso_container_shader_1.nodes["Attr_Scratch"].parent = iso_container_shader_1.nodes["Frame.002"]
    iso_container_shader_1.nodes["MP_Stain"].parent = iso_container_shader_1.nodes["Frame.001"]
    iso_container_shader_1.nodes["W_Mul_N_Stain"].parent = iso_container_shader_1.nodes["Frame.001"]
    iso_container_shader_1.nodes["W_Add_N_Stain"].parent = iso_container_shader_1.nodes["Frame.001"]
    iso_container_shader_1.nodes["N_Stain"].parent = iso_container_shader_1.nodes["Frame.001"]
    iso_container_shader_1.nodes["CR_Stain"].parent = iso_container_shader_1.nodes["Frame.001"]
    iso_container_shader_1.nodes["MR_StainH"].parent = iso_container_shader_1.nodes["Frame.001"]
    iso_container_shader_1.nodes["CR_StainH"].parent = iso_container_shader_1.nodes["Frame.001"]
    iso_container_shader_1.nodes["Math_Stain"].parent = iso_container_shader_1.nodes["Frame.001"]
    iso_container_shader_1.nodes["Math_StainI"].parent = iso_container_shader_1.nodes["Frame.001"]
    iso_container_shader_1.nodes["MR_DustH"].parent = iso_container_shader_1.nodes["Frame"]
    iso_container_shader_1.nodes["W_Mul_N_Dust"].parent = iso_container_shader_1.nodes["Frame"]
    iso_container_shader_1.nodes["W_Add_N_Dust"].parent = iso_container_shader_1.nodes["Frame"]
    iso_container_shader_1.nodes["N_Dust"].parent = iso_container_shader_1.nodes["Frame"]
    iso_container_shader_1.nodes["Math_DustH"].parent = iso_container_shader_1.nodes["Frame"]
    iso_container_shader_1.nodes["CR_DustH"].parent = iso_container_shader_1.nodes["Frame"]
    iso_container_shader_1.nodes["AO"].parent = iso_container_shader_1.nodes["Frame"]
    iso_container_shader_1.nodes["Math_AOInv"].parent = iso_container_shader_1.nodes["Frame"]
    iso_container_shader_1.nodes["CR_AO"].parent = iso_container_shader_1.nodes["Frame"]
    iso_container_shader_1.nodes["Math_DustMax"].parent = iso_container_shader_1.nodes["Frame"]
    iso_container_shader_1.nodes["Math_DustI"].parent = iso_container_shader_1.nodes["Frame"]
    iso_container_shader_1.nodes["VecRot_Scratch"].parent = iso_container_shader_1.nodes["Frame.002"]
    iso_container_shader_1.nodes["MP_Wave"].parent = iso_container_shader_1.nodes["Frame.002"]
    iso_container_shader_1.nodes["WaveTex"].parent = iso_container_shader_1.nodes["Frame.002"]
    iso_container_shader_1.nodes["MP_ScratchCoord"].parent = iso_container_shader_1.nodes["Frame.002"]
    iso_container_shader_1.nodes["Sep_Scratch"].parent = iso_container_shader_1.nodes["Frame.002"]
    iso_container_shader_1.nodes["Comb_Scratch"].parent = iso_container_shader_1.nodes["Frame.002"]
    iso_container_shader_1.nodes["Math_WaveScale"].parent = iso_container_shader_1.nodes["Frame.002"]
    iso_container_shader_1.nodes["W_Mul_N_Scratch"].parent = iso_container_shader_1.nodes["Frame.002"]
    iso_container_shader_1.nodes["W_Add_N_Scratch"].parent = iso_container_shader_1.nodes["Frame.002"]
    iso_container_shader_1.nodes["N_ScratchDist"].parent = iso_container_shader_1.nodes["Frame.002"]
    iso_container_shader_1.nodes["CR_Scratch"].parent = iso_container_shader_1.nodes["Frame.002"]
    iso_container_shader_1.nodes["Math_ScratchI"].parent = iso_container_shader_1.nodes["Frame.002"]

    # Set locations
    iso_container_shader_1.nodes["GroupOutput"].location = (2695.73, -131.46)
    iso_container_shader_1.nodes["TexCoord"].location = (-2802.43, 958.43)
    iso_container_shader_1.nodes["GeoCoord"].location = (-3002.66, 1989.60)
    iso_container_shader_1.nodes["SepXYZ"].location = (-2807.42, 2055.65)
    iso_container_shader_1.nodes["Mapping"].location = (-2545.53, 210.37)
    iso_container_shader_1.nodes["Attr_Seed"].location = (-2801.27, 1141.62)
    iso_container_shader_1.nodes["Attr_Rust"].location = (1641.51, 289.42)
    iso_container_shader_1.nodes["Attr_StainI"].location = (856.46, -556.71)
    iso_container_shader_1.nodes["Attr_DustI"].location = (1145.91, -403.14)
    iso_container_shader_1.nodes["Attr_Scratch"].location = (1091.69, -286.12)
    iso_container_shader_1.nodes["Attr_ColOvr"].location = (322.47, 539.43)
    iso_container_shader_1.nodes["Attr_ColAmt"].location = (331.30, 722.32)
    iso_container_shader_1.nodes["CR_Palette"].location = (-1018.50, 1285.24)
    iso_container_shader_1.nodes["N_Roughness"].location = (792.64, -64.90)
    iso_container_shader_1.nodes["CR_Roughness"].location = (969.64, -145.44)
    iso_container_shader_1.nodes["N_Specular"].location = (803.03, -363.28)
    iso_container_shader_1.nodes["CR_Specular"].location = (967.27, -364.90)
    iso_container_shader_1.nodes["Geometry_Normals"].location = (378.43, 196.65)
    iso_container_shader_1.nodes["Bevel"].location = (382.54, -50.61)
    iso_container_shader_1.nodes["VM_Dot"].location = (564.66, 59.19)
    iso_container_shader_1.nodes["CR_EdgeMask"].location = (740.97, 213.41)
    iso_container_shader_1.nodes["N_RustPat"].location = (1250.86, 566.02)
    iso_container_shader_1.nodes["CR_RustPat"].location = (1413.70, 564.38)
    iso_container_shader_1.nodes["MX_RustMask"].location = (1719.96, 564.73)
    iso_container_shader_1.nodes["Math_Rust"].location = (1879.09, 464.23)
    iso_container_shader_1.nodes["W_Mul_N_RustBump"].location = (1130.15, -987.12)
    iso_container_shader_1.nodes["W_Add_N_RustBump"].location = (1281.48, -988.45)
    iso_container_shader_1.nodes["N_RustBump"].location = (989.09, -666.78)
    iso_container_shader_1.nodes["CR_RustBump"].location = (1150.52, -664.79)
    iso_container_shader_1.nodes["Bump"].location = (1418.26, -777.10)
    iso_container_shader_1.nodes["MP_Stain"].location = (31.74, -36.32)
    iso_container_shader_1.nodes["W_Mul_N_Stain"].location = (29.96, -412.06)
    iso_container_shader_1.nodes["W_Add_N_Stain"].location = (197.93, -282.78)
    iso_container_shader_1.nodes["N_Stain"].location = (388.05, -123.47)
    iso_container_shader_1.nodes["CR_Stain"].location = (566.62, -133.60)
    iso_container_shader_1.nodes["MR_StainH"].location = (391.38, -449.72)
    iso_container_shader_1.nodes["CR_StainH"].location = (570.58, -378.47)
    iso_container_shader_1.nodes["Math_Stain"].location = (850.43, -386.25)
    iso_container_shader_1.nodes["Math_StainI"].location = (1035.08, -414.62)
    iso_container_shader_1.nodes["MR_DustH"].location = (354.79, -35.76)
    iso_container_shader_1.nodes["W_Mul_N_Dust"].location = (30.01, -331.83)
    iso_container_shader_1.nodes["W_Add_N_Dust"].location = (191.00, -324.35)
    iso_container_shader_1.nodes["N_Dust"].location = (353.08, -292.60)
    iso_container_shader_1.nodes["Math_DustH"].location = (698.73, -112.50)
    iso_container_shader_1.nodes["CR_DustH"].location = (858.32, -114.37)
    iso_container_shader_1.nodes["AO"].location = (530.08, -343.04)
    iso_container_shader_1.nodes["Math_AOInv"].location = (699.03, -344.92)
    iso_container_shader_1.nodes["CR_AO"].location = (864.25, -339.29)
    iso_container_shader_1.nodes["Math_DustMax"].location = (1143.35, -213.71)
    iso_container_shader_1.nodes["Math_DustI"].location = (1312.30, -213.71)
    iso_container_shader_1.nodes["VecRot_Scratch"].location = (29.71, -35.53)
    iso_container_shader_1.nodes["MP_Wave"].location = (190.47, -35.90)
    iso_container_shader_1.nodes["WaveTex"].location = (346.91, -36.65)
    iso_container_shader_1.nodes["MP_ScratchCoord"].location = (197.33, -404.65)
    iso_container_shader_1.nodes["Sep_Scratch"].location = (359.23, -350.87)
    iso_container_shader_1.nodes["Comb_Scratch"].location = (532.67, -196.95)
    iso_container_shader_1.nodes["Math_WaveScale"].location = (687.59, -206.84)
    iso_container_shader_1.nodes["W_Mul_N_Scratch"].location = (524.26, -40.58)
    iso_container_shader_1.nodes["W_Add_N_Scratch"].location = (686.17, -45.05)
    iso_container_shader_1.nodes["N_ScratchDist"].location = (840.35, -43.83)
    iso_container_shader_1.nodes["CR_Scratch"].location = (1007.43, -43.83)
    iso_container_shader_1.nodes["Math_ScratchI"].location = (1271.86, -43.83)
    iso_container_shader_1.nodes["MX_Stain"].location = (-681.78, 1511.00)
    iso_container_shader_1.nodes["MX_Dust"].location = (171.51, 1250.94)
    iso_container_shader_1.nodes["MX_Scratch"].location = (391.23, 999.95)
    iso_container_shader_1.nodes["MX_Override"].location = (606.49, 759.85)
    iso_container_shader_1.nodes["Math_EdgeRoughMul"].location = (1148.72, 27.60)
    iso_container_shader_1.nodes["Math_EdgeRoughAdd"].location = (1306.31, 26.97)
    iso_container_shader_1.nodes["BSDF_Paint"].location = (1600.81, 92.74)
    iso_container_shader_1.nodes["BSDF_Worn"].location = (1594.16, -267.02)
    iso_container_shader_1.nodes["BSDF_Rust"].location = (1591.03, -647.03)
    iso_container_shader_1.nodes["Mix_Worn"].location = (2032.53, -164.01)
    iso_container_shader_1.nodes["Mix_Rust"].location = (2319.35, -118.21)
    iso_container_shader_1.nodes["Frame"].location = (-2355.0, 2557.0)
    iso_container_shader_1.nodes["Frame.001"].location = (-2273.0, 1847.0)
    iso_container_shader_1.nodes["Frame.002"].location = (-1215.0, 1067.0)

    # Set dimensions
    iso_container_shader_1.nodes["GroupOutput"].width  = 140.0
    iso_container_shader_1.nodes["GroupOutput"].height = 100.0

    iso_container_shader_1.nodes["TexCoord"].width  = 140.0
    iso_container_shader_1.nodes["TexCoord"].height = 100.0

    iso_container_shader_1.nodes["GeoCoord"].width  = 140.0
    iso_container_shader_1.nodes["GeoCoord"].height = 100.0

    iso_container_shader_1.nodes["SepXYZ"].width  = 140.0
    iso_container_shader_1.nodes["SepXYZ"].height = 100.0

    iso_container_shader_1.nodes["Mapping"].width  = 140.0
    iso_container_shader_1.nodes["Mapping"].height = 100.0

    iso_container_shader_1.nodes["Attr_Seed"].width  = 140.0
    iso_container_shader_1.nodes["Attr_Seed"].height = 100.0

    iso_container_shader_1.nodes["Attr_Rust"].width  = 140.0
    iso_container_shader_1.nodes["Attr_Rust"].height = 100.0

    iso_container_shader_1.nodes["Attr_StainI"].width  = 140.0
    iso_container_shader_1.nodes["Attr_StainI"].height = 100.0

    iso_container_shader_1.nodes["Attr_DustI"].width  = 140.0
    iso_container_shader_1.nodes["Attr_DustI"].height = 100.0

    iso_container_shader_1.nodes["Attr_Scratch"].width  = 140.0
    iso_container_shader_1.nodes["Attr_Scratch"].height = 100.0

    iso_container_shader_1.nodes["Attr_ColOvr"].width  = 140.0
    iso_container_shader_1.nodes["Attr_ColOvr"].height = 100.0

    iso_container_shader_1.nodes["Attr_ColAmt"].width  = 140.0
    iso_container_shader_1.nodes["Attr_ColAmt"].height = 100.0

    iso_container_shader_1.nodes["CR_Palette"].width  = 240.0
    iso_container_shader_1.nodes["CR_Palette"].height = 100.0

    iso_container_shader_1.nodes["N_Roughness"].width  = 145.0
    iso_container_shader_1.nodes["N_Roughness"].height = 100.0

    iso_container_shader_1.nodes["CR_Roughness"].width  = 240.0
    iso_container_shader_1.nodes["CR_Roughness"].height = 100.0

    iso_container_shader_1.nodes["N_Specular"].width  = 145.0
    iso_container_shader_1.nodes["N_Specular"].height = 100.0

    iso_container_shader_1.nodes["CR_Specular"].width  = 240.0
    iso_container_shader_1.nodes["CR_Specular"].height = 100.0

    iso_container_shader_1.nodes["Geometry_Normals"].width  = 140.0
    iso_container_shader_1.nodes["Geometry_Normals"].height = 100.0

    iso_container_shader_1.nodes["Bevel"].width  = 140.0
    iso_container_shader_1.nodes["Bevel"].height = 100.0

    iso_container_shader_1.nodes["VM_Dot"].width  = 140.0
    iso_container_shader_1.nodes["VM_Dot"].height = 100.0

    iso_container_shader_1.nodes["CR_EdgeMask"].width  = 240.0
    iso_container_shader_1.nodes["CR_EdgeMask"].height = 100.0

    iso_container_shader_1.nodes["N_RustPat"].width  = 145.0
    iso_container_shader_1.nodes["N_RustPat"].height = 100.0

    iso_container_shader_1.nodes["CR_RustPat"].width  = 240.0
    iso_container_shader_1.nodes["CR_RustPat"].height = 100.0

    iso_container_shader_1.nodes["MX_RustMask"].width  = 140.0
    iso_container_shader_1.nodes["MX_RustMask"].height = 100.0

    iso_container_shader_1.nodes["Math_Rust"].width  = 140.0
    iso_container_shader_1.nodes["Math_Rust"].height = 100.0

    iso_container_shader_1.nodes["W_Mul_N_RustBump"].width  = 140.0
    iso_container_shader_1.nodes["W_Mul_N_RustBump"].height = 100.0

    iso_container_shader_1.nodes["W_Add_N_RustBump"].width  = 140.0
    iso_container_shader_1.nodes["W_Add_N_RustBump"].height = 100.0

    iso_container_shader_1.nodes["N_RustBump"].width  = 145.0
    iso_container_shader_1.nodes["N_RustBump"].height = 100.0

    iso_container_shader_1.nodes["CR_RustBump"].width  = 240.0
    iso_container_shader_1.nodes["CR_RustBump"].height = 100.0

    iso_container_shader_1.nodes["Bump"].width  = 140.0
    iso_container_shader_1.nodes["Bump"].height = 100.0

    iso_container_shader_1.nodes["MP_Stain"].width  = 140.0
    iso_container_shader_1.nodes["MP_Stain"].height = 100.0

    iso_container_shader_1.nodes["W_Mul_N_Stain"].width  = 140.0
    iso_container_shader_1.nodes["W_Mul_N_Stain"].height = 100.0

    iso_container_shader_1.nodes["W_Add_N_Stain"].width  = 140.0
    iso_container_shader_1.nodes["W_Add_N_Stain"].height = 100.0

    iso_container_shader_1.nodes["N_Stain"].width  = 145.0
    iso_container_shader_1.nodes["N_Stain"].height = 100.0

    iso_container_shader_1.nodes["CR_Stain"].width  = 240.0
    iso_container_shader_1.nodes["CR_Stain"].height = 100.0

    iso_container_shader_1.nodes["MR_StainH"].width  = 140.0
    iso_container_shader_1.nodes["MR_StainH"].height = 100.0

    iso_container_shader_1.nodes["CR_StainH"].width  = 240.0
    iso_container_shader_1.nodes["CR_StainH"].height = 100.0

    iso_container_shader_1.nodes["Math_Stain"].width  = 140.0
    iso_container_shader_1.nodes["Math_Stain"].height = 100.0

    iso_container_shader_1.nodes["Math_StainI"].width  = 140.0
    iso_container_shader_1.nodes["Math_StainI"].height = 100.0

    iso_container_shader_1.nodes["MR_DustH"].width  = 140.0
    iso_container_shader_1.nodes["MR_DustH"].height = 100.0

    iso_container_shader_1.nodes["W_Mul_N_Dust"].width  = 140.0
    iso_container_shader_1.nodes["W_Mul_N_Dust"].height = 100.0

    iso_container_shader_1.nodes["W_Add_N_Dust"].width  = 140.0
    iso_container_shader_1.nodes["W_Add_N_Dust"].height = 100.0

    iso_container_shader_1.nodes["N_Dust"].width  = 145.0
    iso_container_shader_1.nodes["N_Dust"].height = 100.0

    iso_container_shader_1.nodes["Math_DustH"].width  = 140.0
    iso_container_shader_1.nodes["Math_DustH"].height = 100.0

    iso_container_shader_1.nodes["CR_DustH"].width  = 240.0
    iso_container_shader_1.nodes["CR_DustH"].height = 100.0

    iso_container_shader_1.nodes["AO"].width  = 140.0
    iso_container_shader_1.nodes["AO"].height = 100.0

    iso_container_shader_1.nodes["Math_AOInv"].width  = 140.0
    iso_container_shader_1.nodes["Math_AOInv"].height = 100.0

    iso_container_shader_1.nodes["CR_AO"].width  = 240.0
    iso_container_shader_1.nodes["CR_AO"].height = 100.0

    iso_container_shader_1.nodes["Math_DustMax"].width  = 140.0
    iso_container_shader_1.nodes["Math_DustMax"].height = 100.0

    iso_container_shader_1.nodes["Math_DustI"].width  = 140.0
    iso_container_shader_1.nodes["Math_DustI"].height = 100.0

    iso_container_shader_1.nodes["VecRot_Scratch"].width  = 140.0
    iso_container_shader_1.nodes["VecRot_Scratch"].height = 100.0

    iso_container_shader_1.nodes["MP_Wave"].width  = 140.0
    iso_container_shader_1.nodes["MP_Wave"].height = 100.0

    iso_container_shader_1.nodes["WaveTex"].width  = 160.0
    iso_container_shader_1.nodes["WaveTex"].height = 100.0

    iso_container_shader_1.nodes["MP_ScratchCoord"].width  = 140.0
    iso_container_shader_1.nodes["MP_ScratchCoord"].height = 100.0

    iso_container_shader_1.nodes["Sep_Scratch"].width  = 140.0
    iso_container_shader_1.nodes["Sep_Scratch"].height = 100.0

    iso_container_shader_1.nodes["Comb_Scratch"].width  = 140.0
    iso_container_shader_1.nodes["Comb_Scratch"].height = 100.0

    iso_container_shader_1.nodes["Math_WaveScale"].width  = 140.0
    iso_container_shader_1.nodes["Math_WaveScale"].height = 100.0

    iso_container_shader_1.nodes["W_Mul_N_Scratch"].width  = 140.0
    iso_container_shader_1.nodes["W_Mul_N_Scratch"].height = 100.0

    iso_container_shader_1.nodes["W_Add_N_Scratch"].width  = 140.0
    iso_container_shader_1.nodes["W_Add_N_Scratch"].height = 100.0

    iso_container_shader_1.nodes["N_ScratchDist"].width  = 145.0
    iso_container_shader_1.nodes["N_ScratchDist"].height = 100.0

    iso_container_shader_1.nodes["CR_Scratch"].width  = 240.0
    iso_container_shader_1.nodes["CR_Scratch"].height = 100.0

    iso_container_shader_1.nodes["Math_ScratchI"].width  = 140.0
    iso_container_shader_1.nodes["Math_ScratchI"].height = 100.0

    iso_container_shader_1.nodes["MX_Stain"].width  = 140.0
    iso_container_shader_1.nodes["MX_Stain"].height = 100.0

    iso_container_shader_1.nodes["MX_Dust"].width  = 140.0
    iso_container_shader_1.nodes["MX_Dust"].height = 100.0

    iso_container_shader_1.nodes["MX_Scratch"].width  = 140.0
    iso_container_shader_1.nodes["MX_Scratch"].height = 100.0

    iso_container_shader_1.nodes["MX_Override"].width  = 140.0
    iso_container_shader_1.nodes["MX_Override"].height = 100.0

    iso_container_shader_1.nodes["Math_EdgeRoughMul"].width  = 140.0
    iso_container_shader_1.nodes["Math_EdgeRoughMul"].height = 100.0

    iso_container_shader_1.nodes["Math_EdgeRoughAdd"].width  = 140.0
    iso_container_shader_1.nodes["Math_EdgeRoughAdd"].height = 100.0

    iso_container_shader_1.nodes["BSDF_Paint"].width  = 240.0
    iso_container_shader_1.nodes["BSDF_Paint"].height = 100.0

    iso_container_shader_1.nodes["BSDF_Worn"].width  = 240.0
    iso_container_shader_1.nodes["BSDF_Worn"].height = 100.0

    iso_container_shader_1.nodes["BSDF_Rust"].width  = 240.0
    iso_container_shader_1.nodes["BSDF_Rust"].height = 100.0

    iso_container_shader_1.nodes["Mix_Worn"].width  = 140.0
    iso_container_shader_1.nodes["Mix_Worn"].height = 100.0

    iso_container_shader_1.nodes["Mix_Rust"].width  = 140.0
    iso_container_shader_1.nodes["Mix_Rust"].height = 100.0

    iso_container_shader_1.nodes["Frame"].width  = 1482.0
    iso_container_shader_1.nodes["Frame"].height = 626.0

    iso_container_shader_1.nodes["Frame.001"].width  = 1205.0
    iso_container_shader_1.nodes["Frame.001"].height = 757.0

    iso_container_shader_1.nodes["Frame.002"].width  = 1442.0
    iso_container_shader_1.nodes["Frame.002"].height = 786.0


    # Initialize iso_container_shader_1 links

    # geocoord.Position -> sepxyz.Vector
    iso_container_shader_1.links.new(
        iso_container_shader_1.nodes["GeoCoord"].outputs[0],
        iso_container_shader_1.nodes["SepXYZ"].inputs[0]
    )
    # texcoord.Object -> mapping.Vector
    iso_container_shader_1.links.new(
        iso_container_shader_1.nodes["TexCoord"].outputs[3],
        iso_container_shader_1.nodes["Mapping"].inputs[0]
    )
    # attr_seed.Factor -> cr_palette.Factor
    iso_container_shader_1.links.new(
        iso_container_shader_1.nodes["Attr_Seed"].outputs[2],
        iso_container_shader_1.nodes["CR_Palette"].inputs[0]
    )
    # mapping.Vector -> n_roughness.Vector
    iso_container_shader_1.links.new(
        iso_container_shader_1.nodes["Mapping"].outputs[0],
        iso_container_shader_1.nodes["N_Roughness"].inputs[0]
    )
    # n_roughness.Factor -> cr_roughness.Factor
    iso_container_shader_1.links.new(
        iso_container_shader_1.nodes["N_Roughness"].outputs[0],
        iso_container_shader_1.nodes["CR_Roughness"].inputs[0]
    )
    # mapping.Vector -> n_specular.Vector
    iso_container_shader_1.links.new(
        iso_container_shader_1.nodes["Mapping"].outputs[0],
        iso_container_shader_1.nodes["N_Specular"].inputs[0]
    )
    # n_specular.Factor -> cr_specular.Factor
    iso_container_shader_1.links.new(
        iso_container_shader_1.nodes["N_Specular"].outputs[0],
        iso_container_shader_1.nodes["CR_Specular"].inputs[0]
    )
    # geometry_normals.Normal -> vm_dot.Vector
    iso_container_shader_1.links.new(
        iso_container_shader_1.nodes["Geometry_Normals"].outputs[1],
        iso_container_shader_1.nodes["VM_Dot"].inputs[0]
    )
    # bevel.Normal -> vm_dot.Vector
    iso_container_shader_1.links.new(
        iso_container_shader_1.nodes["Bevel"].outputs[0],
        iso_container_shader_1.nodes["VM_Dot"].inputs[1]
    )
    # vm_dot.Value -> cr_edgemask.Factor
    iso_container_shader_1.links.new(
        iso_container_shader_1.nodes["VM_Dot"].outputs[1],
        iso_container_shader_1.nodes["CR_EdgeMask"].inputs[0]
    )
    # mapping.Vector -> n_rustpat.Vector
    iso_container_shader_1.links.new(
        iso_container_shader_1.nodes["Mapping"].outputs[0],
        iso_container_shader_1.nodes["N_RustPat"].inputs[0]
    )
    # n_rustpat.Factor -> cr_rustpat.Factor
    iso_container_shader_1.links.new(
        iso_container_shader_1.nodes["N_RustPat"].outputs[0],
        iso_container_shader_1.nodes["CR_RustPat"].inputs[0]
    )
    # cr_edgemask.Color -> mx_rustmask.A
    iso_container_shader_1.links.new(
        iso_container_shader_1.nodes["CR_EdgeMask"].outputs[0],
        iso_container_shader_1.nodes["MX_RustMask"].inputs[6]
    )
    # cr_rustpat.Color -> mx_rustmask.B
    iso_container_shader_1.links.new(
        iso_container_shader_1.nodes["CR_RustPat"].outputs[0],
        iso_container_shader_1.nodes["MX_RustMask"].inputs[7]
    )
    # mx_rustmask.Result -> math_rust.Value
    iso_container_shader_1.links.new(
        iso_container_shader_1.nodes["MX_RustMask"].outputs[2],
        iso_container_shader_1.nodes["Math_Rust"].inputs[0]
    )
    # attr_rust.Factor -> math_rust.Value
    iso_container_shader_1.links.new(
        iso_container_shader_1.nodes["Attr_Rust"].outputs[2],
        iso_container_shader_1.nodes["Math_Rust"].inputs[1]
    )
    # attr_seed.Factor -> w_mul_n_rustbump.Value
    iso_container_shader_1.links.new(
        iso_container_shader_1.nodes["Attr_Seed"].outputs[2],
        iso_container_shader_1.nodes["W_Mul_N_RustBump"].inputs[0]
    )
    # w_mul_n_rustbump.Value -> w_add_n_rustbump.Value
    iso_container_shader_1.links.new(
        iso_container_shader_1.nodes["W_Mul_N_RustBump"].outputs[0],
        iso_container_shader_1.nodes["W_Add_N_RustBump"].inputs[1]
    )
    # w_add_n_rustbump.Value -> n_rustbump.W
    iso_container_shader_1.links.new(
        iso_container_shader_1.nodes["W_Add_N_RustBump"].outputs[0],
        iso_container_shader_1.nodes["N_RustBump"].inputs[1]
    )
    # mapping.Vector -> n_rustbump.Vector
    iso_container_shader_1.links.new(
        iso_container_shader_1.nodes["Mapping"].outputs[0],
        iso_container_shader_1.nodes["N_RustBump"].inputs[0]
    )
    # n_rustbump.Factor -> cr_rustbump.Factor
    iso_container_shader_1.links.new(
        iso_container_shader_1.nodes["N_RustBump"].outputs[0],
        iso_container_shader_1.nodes["CR_RustBump"].inputs[0]
    )
    # cr_rustbump.Color -> bump.Height
    iso_container_shader_1.links.new(
        iso_container_shader_1.nodes["CR_RustBump"].outputs[0],
        iso_container_shader_1.nodes["Bump"].inputs[3]
    )
    # texcoord.Object -> mp_stain.Vector
    iso_container_shader_1.links.new(
        iso_container_shader_1.nodes["TexCoord"].outputs[3],
        iso_container_shader_1.nodes["MP_Stain"].inputs[0]
    )
    # attr_seed.Factor -> w_mul_n_stain.Value
    iso_container_shader_1.links.new(
        iso_container_shader_1.nodes["Attr_Seed"].outputs[2],
        iso_container_shader_1.nodes["W_Mul_N_Stain"].inputs[0]
    )
    # w_mul_n_stain.Value -> w_add_n_stain.Value
    iso_container_shader_1.links.new(
        iso_container_shader_1.nodes["W_Mul_N_Stain"].outputs[0],
        iso_container_shader_1.nodes["W_Add_N_Stain"].inputs[1]
    )
    # w_add_n_stain.Value -> n_stain.W
    iso_container_shader_1.links.new(
        iso_container_shader_1.nodes["W_Add_N_Stain"].outputs[0],
        iso_container_shader_1.nodes["N_Stain"].inputs[1]
    )
    # mp_stain.Vector -> n_stain.Vector
    iso_container_shader_1.links.new(
        iso_container_shader_1.nodes["MP_Stain"].outputs[0],
        iso_container_shader_1.nodes["N_Stain"].inputs[0]
    )
    # n_stain.Factor -> cr_stain.Factor
    iso_container_shader_1.links.new(
        iso_container_shader_1.nodes["N_Stain"].outputs[0],
        iso_container_shader_1.nodes["CR_Stain"].inputs[0]
    )
    # sepxyz.Z -> mr_stainh.Value
    iso_container_shader_1.links.new(
        iso_container_shader_1.nodes["SepXYZ"].outputs[2],
        iso_container_shader_1.nodes["MR_StainH"].inputs[0]
    )
    # mr_stainh.Result -> cr_stainh.Factor
    iso_container_shader_1.links.new(
        iso_container_shader_1.nodes["MR_StainH"].outputs[0],
        iso_container_shader_1.nodes["CR_StainH"].inputs[0]
    )
    # cr_stain.Color -> math_stain.Value
    iso_container_shader_1.links.new(
        iso_container_shader_1.nodes["CR_Stain"].outputs[0],
        iso_container_shader_1.nodes["Math_Stain"].inputs[0]
    )
    # cr_stainh.Color -> math_stain.Value
    iso_container_shader_1.links.new(
        iso_container_shader_1.nodes["CR_StainH"].outputs[0],
        iso_container_shader_1.nodes["Math_Stain"].inputs[1]
    )
    # math_stain.Value -> math_staini.Value
    iso_container_shader_1.links.new(
        iso_container_shader_1.nodes["Math_Stain"].outputs[0],
        iso_container_shader_1.nodes["Math_StainI"].inputs[0]
    )
    # attr_staini.Factor -> math_staini.Value
    iso_container_shader_1.links.new(
        iso_container_shader_1.nodes["Attr_StainI"].outputs[2],
        iso_container_shader_1.nodes["Math_StainI"].inputs[1]
    )
    # sepxyz.Z -> mr_dusth.Value
    iso_container_shader_1.links.new(
        iso_container_shader_1.nodes["SepXYZ"].outputs[2],
        iso_container_shader_1.nodes["MR_DustH"].inputs[0]
    )
    # attr_seed.Factor -> w_mul_n_dust.Value
    iso_container_shader_1.links.new(
        iso_container_shader_1.nodes["Attr_Seed"].outputs[2],
        iso_container_shader_1.nodes["W_Mul_N_Dust"].inputs[0]
    )
    # w_mul_n_dust.Value -> w_add_n_dust.Value
    iso_container_shader_1.links.new(
        iso_container_shader_1.nodes["W_Mul_N_Dust"].outputs[0],
        iso_container_shader_1.nodes["W_Add_N_Dust"].inputs[1]
    )
    # w_add_n_dust.Value -> n_dust.W
    iso_container_shader_1.links.new(
        iso_container_shader_1.nodes["W_Add_N_Dust"].outputs[0],
        iso_container_shader_1.nodes["N_Dust"].inputs[1]
    )
    # mapping.Vector -> n_dust.Vector
    iso_container_shader_1.links.new(
        iso_container_shader_1.nodes["Mapping"].outputs[0],
        iso_container_shader_1.nodes["N_Dust"].inputs[0]
    )
    # mr_dusth.Result -> math_dusth.Value
    iso_container_shader_1.links.new(
        iso_container_shader_1.nodes["MR_DustH"].outputs[0],
        iso_container_shader_1.nodes["Math_DustH"].inputs[0]
    )
    # n_dust.Factor -> math_dusth.Value
    iso_container_shader_1.links.new(
        iso_container_shader_1.nodes["N_Dust"].outputs[0],
        iso_container_shader_1.nodes["Math_DustH"].inputs[1]
    )
    # math_dusth.Value -> cr_dusth.Factor
    iso_container_shader_1.links.new(
        iso_container_shader_1.nodes["Math_DustH"].outputs[0],
        iso_container_shader_1.nodes["CR_DustH"].inputs[0]
    )
    # ao.AO -> math_aoinv.Value
    iso_container_shader_1.links.new(
        iso_container_shader_1.nodes["AO"].outputs[1],
        iso_container_shader_1.nodes["Math_AOInv"].inputs[1]
    )
    # math_aoinv.Value -> cr_ao.Factor
    iso_container_shader_1.links.new(
        iso_container_shader_1.nodes["Math_AOInv"].outputs[0],
        iso_container_shader_1.nodes["CR_AO"].inputs[0]
    )
    # cr_dusth.Color -> math_dustmax.Value
    iso_container_shader_1.links.new(
        iso_container_shader_1.nodes["CR_DustH"].outputs[0],
        iso_container_shader_1.nodes["Math_DustMax"].inputs[0]
    )
    # cr_ao.Color -> math_dustmax.Value
    iso_container_shader_1.links.new(
        iso_container_shader_1.nodes["CR_AO"].outputs[0],
        iso_container_shader_1.nodes["Math_DustMax"].inputs[1]
    )
    # math_dustmax.Value -> math_dusti.Value
    iso_container_shader_1.links.new(
        iso_container_shader_1.nodes["Math_DustMax"].outputs[0],
        iso_container_shader_1.nodes["Math_DustI"].inputs[0]
    )
    # attr_dusti.Factor -> math_dusti.Value
    iso_container_shader_1.links.new(
        iso_container_shader_1.nodes["Attr_DustI"].outputs[2],
        iso_container_shader_1.nodes["Math_DustI"].inputs[1]
    )
    # texcoord.Object -> vecrot_scratch.Vector
    iso_container_shader_1.links.new(
        iso_container_shader_1.nodes["TexCoord"].outputs[3],
        iso_container_shader_1.nodes["VecRot_Scratch"].inputs[0]
    )
    # vecrot_scratch.Vector -> mp_wave.Vector
    iso_container_shader_1.links.new(
        iso_container_shader_1.nodes["VecRot_Scratch"].outputs[0],
        iso_container_shader_1.nodes["MP_Wave"].inputs[0]
    )
    # mp_wave.Vector -> wavetex.Vector
    iso_container_shader_1.links.new(
        iso_container_shader_1.nodes["MP_Wave"].outputs[0],
        iso_container_shader_1.nodes["WaveTex"].inputs[0]
    )
    # texcoord.Object -> mp_scratchcoord.Vector
    iso_container_shader_1.links.new(
        iso_container_shader_1.nodes["TexCoord"].outputs[3],
        iso_container_shader_1.nodes["MP_ScratchCoord"].inputs[0]
    )
    # mp_scratchcoord.Vector -> sep_scratch.Vector
    iso_container_shader_1.links.new(
        iso_container_shader_1.nodes["MP_ScratchCoord"].outputs[0],
        iso_container_shader_1.nodes["Sep_Scratch"].inputs[0]
    )
    # sep_scratch.X -> comb_scratch.X
    iso_container_shader_1.links.new(
        iso_container_shader_1.nodes["Sep_Scratch"].outputs[0],
        iso_container_shader_1.nodes["Comb_Scratch"].inputs[0]
    )
    # wavetex.Factor -> comb_scratch.Y
    iso_container_shader_1.links.new(
        iso_container_shader_1.nodes["WaveTex"].outputs[1],
        iso_container_shader_1.nodes["Comb_Scratch"].inputs[1]
    )
    # sep_scratch.Z -> comb_scratch.Z
    iso_container_shader_1.links.new(
        iso_container_shader_1.nodes["Sep_Scratch"].outputs[2],
        iso_container_shader_1.nodes["Comb_Scratch"].inputs[2]
    )
    # attr_seed.Factor -> math_wavescale.Value
    iso_container_shader_1.links.new(
        iso_container_shader_1.nodes["Attr_Seed"].outputs[2],
        iso_container_shader_1.nodes["Math_WaveScale"].inputs[0]
    )
    # attr_seed.Factor -> w_mul_n_scratch.Value
    iso_container_shader_1.links.new(
        iso_container_shader_1.nodes["Attr_Seed"].outputs[2],
        iso_container_shader_1.nodes["W_Mul_N_Scratch"].inputs[0]
    )
    # w_mul_n_scratch.Value -> w_add_n_scratch.Value
    iso_container_shader_1.links.new(
        iso_container_shader_1.nodes["W_Mul_N_Scratch"].outputs[0],
        iso_container_shader_1.nodes["W_Add_N_Scratch"].inputs[1]
    )
    # w_add_n_scratch.Value -> n_scratchdist.W
    iso_container_shader_1.links.new(
        iso_container_shader_1.nodes["W_Add_N_Scratch"].outputs[0],
        iso_container_shader_1.nodes["N_ScratchDist"].inputs[1]
    )
    # comb_scratch.Vector -> n_scratchdist.Vector
    iso_container_shader_1.links.new(
        iso_container_shader_1.nodes["Comb_Scratch"].outputs[0],
        iso_container_shader_1.nodes["N_ScratchDist"].inputs[0]
    )
    # math_wavescale.Value -> n_scratchdist.Scale
    iso_container_shader_1.links.new(
        iso_container_shader_1.nodes["Math_WaveScale"].outputs[0],
        iso_container_shader_1.nodes["N_ScratchDist"].inputs[2]
    )
    # n_scratchdist.Factor -> cr_scratch.Factor
    iso_container_shader_1.links.new(
        iso_container_shader_1.nodes["N_ScratchDist"].outputs[0],
        iso_container_shader_1.nodes["CR_Scratch"].inputs[0]
    )
    # cr_scratch.Color -> math_scratchi.Value
    iso_container_shader_1.links.new(
        iso_container_shader_1.nodes["CR_Scratch"].outputs[0],
        iso_container_shader_1.nodes["Math_ScratchI"].inputs[0]
    )
    # attr_scratch.Factor -> math_scratchi.Value
    iso_container_shader_1.links.new(
        iso_container_shader_1.nodes["Attr_Scratch"].outputs[2],
        iso_container_shader_1.nodes["Math_ScratchI"].inputs[1]
    )
    # math_staini.Value -> mx_stain.Factor
    iso_container_shader_1.links.new(
        iso_container_shader_1.nodes["Math_StainI"].outputs[0],
        iso_container_shader_1.nodes["MX_Stain"].inputs[0]
    )
    # cr_palette.Color -> mx_stain.A
    iso_container_shader_1.links.new(
        iso_container_shader_1.nodes["CR_Palette"].outputs[0],
        iso_container_shader_1.nodes["MX_Stain"].inputs[6]
    )
    # math_dusti.Value -> mx_dust.Factor
    iso_container_shader_1.links.new(
        iso_container_shader_1.nodes["Math_DustI"].outputs[0],
        iso_container_shader_1.nodes["MX_Dust"].inputs[0]
    )
    # mx_stain.Result -> mx_dust.A
    iso_container_shader_1.links.new(
        iso_container_shader_1.nodes["MX_Stain"].outputs[2],
        iso_container_shader_1.nodes["MX_Dust"].inputs[6]
    )
    # math_scratchi.Value -> mx_scratch.Factor
    iso_container_shader_1.links.new(
        iso_container_shader_1.nodes["Math_ScratchI"].outputs[0],
        iso_container_shader_1.nodes["MX_Scratch"].inputs[0]
    )
    # mx_dust.Result -> mx_scratch.A
    iso_container_shader_1.links.new(
        iso_container_shader_1.nodes["MX_Dust"].outputs[2],
        iso_container_shader_1.nodes["MX_Scratch"].inputs[6]
    )
    # attr_colamt.Factor -> mx_override.Factor
    iso_container_shader_1.links.new(
        iso_container_shader_1.nodes["Attr_ColAmt"].outputs[2],
        iso_container_shader_1.nodes["MX_Override"].inputs[0]
    )
    # mx_scratch.Result -> mx_override.A
    iso_container_shader_1.links.new(
        iso_container_shader_1.nodes["MX_Scratch"].outputs[2],
        iso_container_shader_1.nodes["MX_Override"].inputs[6]
    )
    # attr_colovr.Color -> mx_override.B
    iso_container_shader_1.links.new(
        iso_container_shader_1.nodes["Attr_ColOvr"].outputs[0],
        iso_container_shader_1.nodes["MX_Override"].inputs[7]
    )
    # cr_edgemask.Color -> math_edgeroughmul.Value
    iso_container_shader_1.links.new(
        iso_container_shader_1.nodes["CR_EdgeMask"].outputs[0],
        iso_container_shader_1.nodes["Math_EdgeRoughMul"].inputs[0]
    )
    # cr_roughness.Color -> math_edgeroughadd.Value
    iso_container_shader_1.links.new(
        iso_container_shader_1.nodes["CR_Roughness"].outputs[0],
        iso_container_shader_1.nodes["Math_EdgeRoughAdd"].inputs[0]
    )
    # math_edgeroughmul.Value -> math_edgeroughadd.Value
    iso_container_shader_1.links.new(
        iso_container_shader_1.nodes["Math_EdgeRoughMul"].outputs[0],
        iso_container_shader_1.nodes["Math_EdgeRoughAdd"].inputs[1]
    )
    # mx_override.Result -> bsdf_paint.Base Color
    iso_container_shader_1.links.new(
        iso_container_shader_1.nodes["MX_Override"].outputs[2],
        iso_container_shader_1.nodes["BSDF_Paint"].inputs[0]
    )
    # math_edgeroughadd.Value -> bsdf_paint.Roughness
    iso_container_shader_1.links.new(
        iso_container_shader_1.nodes["Math_EdgeRoughAdd"].outputs[0],
        iso_container_shader_1.nodes["BSDF_Paint"].inputs[2]
    )
    # cr_specular.Color -> bsdf_paint.Specular IOR Level
    iso_container_shader_1.links.new(
        iso_container_shader_1.nodes["CR_Specular"].outputs[0],
        iso_container_shader_1.nodes["BSDF_Paint"].inputs[13]
    )
    # math_edgeroughadd.Value -> bsdf_worn.Roughness
    iso_container_shader_1.links.new(
        iso_container_shader_1.nodes["Math_EdgeRoughAdd"].outputs[0],
        iso_container_shader_1.nodes["BSDF_Worn"].inputs[2]
    )
    # cr_rustbump.Color -> bsdf_rust.Base Color
    iso_container_shader_1.links.new(
        iso_container_shader_1.nodes["CR_RustBump"].outputs[0],
        iso_container_shader_1.nodes["BSDF_Rust"].inputs[0]
    )
    # bump.Normal -> bsdf_rust.Normal
    iso_container_shader_1.links.new(
        iso_container_shader_1.nodes["Bump"].outputs[0],
        iso_container_shader_1.nodes["BSDF_Rust"].inputs[5]
    )
    # cr_edgemask.Color -> mix_worn.Factor
    iso_container_shader_1.links.new(
        iso_container_shader_1.nodes["CR_EdgeMask"].outputs[0],
        iso_container_shader_1.nodes["Mix_Worn"].inputs[0]
    )
    # bsdf_paint.BSDF -> mix_worn.Shader
    iso_container_shader_1.links.new(
        iso_container_shader_1.nodes["BSDF_Paint"].outputs[0],
        iso_container_shader_1.nodes["Mix_Worn"].inputs[1]
    )
    # bsdf_worn.BSDF -> mix_worn.Shader
    iso_container_shader_1.links.new(
        iso_container_shader_1.nodes["BSDF_Worn"].outputs[0],
        iso_container_shader_1.nodes["Mix_Worn"].inputs[2]
    )
    # math_rust.Value -> mix_rust.Factor
    iso_container_shader_1.links.new(
        iso_container_shader_1.nodes["Math_Rust"].outputs[0],
        iso_container_shader_1.nodes["Mix_Rust"].inputs[0]
    )
    # mix_worn.Shader -> mix_rust.Shader
    iso_container_shader_1.links.new(
        iso_container_shader_1.nodes["Mix_Worn"].outputs[0],
        iso_container_shader_1.nodes["Mix_Rust"].inputs[1]
    )
    # bsdf_rust.BSDF -> mix_rust.Shader
    iso_container_shader_1.links.new(
        iso_container_shader_1.nodes["BSDF_Rust"].outputs[0],
        iso_container_shader_1.nodes["Mix_Rust"].inputs[2]
    )
    # mix_rust.Shader -> groupoutput.Shader
    iso_container_shader_1.links.new(
        iso_container_shader_1.nodes["Mix_Rust"].outputs[0],
        iso_container_shader_1.nodes["GroupOutput"].inputs[0]
    )

    return iso_container_shader_1


iso_container_metal = bpy.data.materials.new(name = "ISO_Container_Metal")
if bpy.app.version < (5, 0, 0):
    iso_container_metal.use_nodes = True


iso_container_metal.alpha_threshold = 0.5
iso_container_metal.line_priority = 0
iso_container_metal.max_vertex_displacement = 0.0
iso_container_metal.metallic = 0.0
iso_container_metal.paint_active_slot = 0
iso_container_metal.paint_clone_slot = 0
iso_container_metal.pass_index = 0
iso_container_metal.refraction_depth = 0.0
iso_container_metal.roughness = 0.4
iso_container_metal.show_transparent_back = True
iso_container_metal.specular_intensity = 0.5
iso_container_metal.use_backface_culling = False
iso_container_metal.use_backface_culling_lightprobe_volume = True
iso_container_metal.use_backface_culling_shadow = False
iso_container_metal.use_preview_world = False
iso_container_metal.use_raytrace_refraction = False
iso_container_metal.use_screen_refraction = False
iso_container_metal.use_sss_translucency = False
iso_container_metal.use_thickness_from_shadow = False
iso_container_metal.use_transparency_overlap = True
iso_container_metal.use_transparent_shadow = True
iso_container_metal.blend_method = 'HASHED'
iso_container_metal.displacement_method = 'BUMP'
iso_container_metal.preview_render_type = 'SPHERE'
iso_container_metal.surface_render_method = 'DITHERED'
iso_container_metal.thickness_mode = 'SPHERE'
iso_container_metal.volume_intersection_method = 'FAST'
iso_container_metal.specular_color = (1.0, 1.0, 1.0)
iso_container_metal.diffuse_color = (0.8, 0.8, 0.8, 1.0)
iso_container_metal.line_color = (0.0, 0.0, 0.0, 0.0)

def shader_nodetree_node_group(node_tree_names: dict[typing.Callable, str]):
    """Initialize Shader Nodetree node group"""
    shader_nodetree = iso_container_metal.node_tree

    # Start with a clean node tree
    for node in shader_nodetree.nodes:
        shader_nodetree.nodes.remove(node)
    shader_nodetree.color_tag = 'NONE'
    shader_nodetree.description = ""
    shader_nodetree.default_group_node_width = 140
    # Initialize shader_nodetree nodes

    # Node Material Output
    material_output = shader_nodetree.nodes.new("ShaderNodeOutputMaterial")
    material_output.name = "Material Output"
    material_output.is_active_output = True
    material_output.target = 'ALL'
    # Displacement
    material_output.inputs[2].default_value = (0.0, 0.0, 0.0)
    # Thickness
    material_output.inputs[3].default_value = 0.0

    # Node Group
    group = shader_nodetree.nodes.new("ShaderNodeGroup")
    group.name = "Group"
    group.node_tree = bpy.data.node_groups[node_tree_names[iso_container_shader_1_node_group]]

    # Set locations
    shader_nodetree.nodes["Material Output"].location = (400.0, 0.0)
    shader_nodetree.nodes["Group"].location = (117.39, -20.95)

    # Set dimensions
    shader_nodetree.nodes["Material Output"].width  = 140.0
    shader_nodetree.nodes["Material Output"].height = 100.0

    shader_nodetree.nodes["Group"].width  = 140.0
    shader_nodetree.nodes["Group"].height = 100.0


    # Initialize shader_nodetree links

    # group.Shader -> material_output.Surface
    shader_nodetree.links.new(
        shader_nodetree.nodes["Group"].outputs[0],
        shader_nodetree.nodes["Material Output"].inputs[0]
    )

    return shader_nodetree


if __name__ == "__main__":
    # Maps node tree creation functions to the node tree 
    # name, such that we don't recreate node trees unnecessarily
    node_tree_names : dict[typing.Callable, str] = {}

    iso_container_shader = iso_container_shader_1_node_group(node_tree_names)
    node_tree_names[iso_container_shader_1_node_group] = iso_container_shader.name

    shader_nodetree = shader_nodetree_node_group(node_tree_names)
    node_tree_names[shader_nodetree_node_group] = shader_nodetree.name

