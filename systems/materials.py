import bpy

def hex_to_linear_rgba(hex_str):
    """Converts a hex color string to a linear RGBA tuple for Blender materials."""
    hex_str = hex_str.lstrip('#')
    if len(hex_str) == 8:
        r, g, b, a = tuple(int(hex_str[i:i+2], 16) / 255.0 for i in (0, 2, 4, 6))
    else:
        r, g, b = tuple(int(hex_str[i:i+2], 16) / 255.0 for i in (0, 2, 4))
        a = 1.0
        
    def srgb_to_linear(c):
        return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4
        
    return (srgb_to_linear(r), srgb_to_linear(g), srgb_to_linear(b), a)

def get_or_create_container_material():
    mat_name = "ISO_Container_Metal"
    if mat_name in bpy.data.materials:
        return bpy.data.materials[mat_name]
        
    mat = bpy.data.materials.new(name=mat_name)
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    nodes.clear()
    
    out_node = nodes.new('ShaderNodeOutputMaterial')
    out_node.location = (300, 0)
    
    bsdf = nodes.new('ShaderNodeBsdfPrincipled')
    bsdf.location = (0, 0)
    bsdf.inputs['Roughness'].default_value = 0.5
    bsdf.inputs['Metallic'].default_value = 0.3
    
    ramp = nodes.new('ShaderNodeValToRGB')
    ramp.location = (-300, 0)
    ramp.color_ramp.interpolation = 'CONSTANT'
    
    colors = [
        (0.000, "#28578EFF"), (0.125, "#132943FF"), (0.250, "#2E66A6FF"), (0.375, "#933D2DFF"), 
        (0.500, "#773226FF"), (0.625, "#61291FFF"), (0.850, "#184612FF"), (0.975, "#308F25FF")
    ]
    elements = ramp.color_ramp.elements
    if len(elements) < len(colors):
        for _ in range(len(colors) - len(elements)):
            elements.new(0.5)
            
    for i, (pos, hex_c) in enumerate(colors):
        elements[i].position = pos
        elements[i].color = hex_to_linear_rgba(hex_c)
        
    
    obj_info = nodes.new('ShaderNodeObjectInfo')
    obj_info.location = (-500, -200)
    
    links.new(obj_info.outputs['Random'], ramp.inputs['Fac'])
    links.new(ramp.outputs['Color'], bsdf.inputs['Base Color'])
    links.new(bsdf.outputs['BSDF'], out_node.inputs['Surface'])
    
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
        bsdf.inputs['Roughness'].default_value = 0.8
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
        bsdf.inputs['Roughness'].default_value = 0.4
        bsdf.inputs['Metallic'].default_value = 0.0
    return mat

def get_or_create_hardware_material():
    """Grey metallic material for locking bars, guides, cams, handles, and all
    door hardware.  Objects must be tagged with obj["is_hardware"] = True by the
    geometry builders so the rebuild loop assigns this material automatically."""
    mat_name = "ISO_Container_Hardware"
    if mat_name in bpy.data.materials:
        return bpy.data.materials[mat_name]

    mat = bpy.data.materials.new(name=mat_name)
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    nodes.clear()

    out_node = nodes.new('ShaderNodeOutputMaterial')
    out_node.location = (300, 0)

    bsdf = nodes.new('ShaderNodeBsdfPrincipled')
    bsdf.location = (0, 0)
    # Mid-grey, slightly rough steel
    bsdf.inputs['Base Color'].default_value = (0.35, 0.35, 0.35, 1.0)
    bsdf.inputs['Roughness'].default_value  = 0.40
    bsdf.inputs['Metallic'].default_value   = 0.85

    links.new(bsdf.outputs['BSDF'], out_node.inputs['Surface'])
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
    
    out_node = nodes.new('ShaderNodeOutputMaterial')
    out_node.location = (300, 0)
    
    bsdf = nodes.new('ShaderNodeBsdfPrincipled')
    bsdf.location = (0, 0)
    
    attr = nodes.new('ShaderNodeAttribute')
    attr.location = (-1000, 200)
    attr.attribute_name = "container_seed"
    attr.attribute_type = 'OBJECT'

    obj_info = nodes.new('ShaderNodeObjectInfo')
    obj_info.location = (-1000, 0)
    
    color_ramp = nodes.new('ShaderNodeValToRGB')
    color_ramp.location = (-800, 200)
    color_ramp.color_ramp.interpolation = 'CONSTANT'
    
    colors = [
        (0.000, "#28578EFF"), (0.125, "#132943FF"), (0.250, "#2E66A6FF"), (0.375, "#933D2DFF"), 
        (0.500, "#773226FF"), (0.625, "#61291FFF"), (0.850, "#184612FF"), (0.975, "#308F25FF")
    ]

    elements = color_ramp.color_ramp.elements
    if len(elements) < len(colors):
        for _ in range(len(colors) - len(elements)):
            elements.new(0.5)
    for i, (pos, hex_c) in enumerate(colors):
        elements[i].position = pos
        elements[i].color = hex_to_linear_rgba(hex_c)

    has_seed = nodes.new('ShaderNodeMath')
    has_seed.location = (-600, 250)
    has_seed.operation = 'GREATER_THAN'
    has_seed.inputs[1].default_value = 0.0

    mix_seed = nodes.new('ShaderNodeMix')
    mix_seed.location = (-400, 250)
    mix_seed.data_type = 'FLOAT'
    mix_seed.blend_type = 'MIX'
        
    tex_coord = nodes.new('ShaderNodeTexCoord')
    tex_coord.location = (-1200, -200)
    
    img_diffuse = get_or_create_proxy_image("proxy_diffuse.png", (0.8, 0.8, 0.8, 1.0))
    node_diffuse = nodes.new('ShaderNodeTexImage')
    node_diffuse.location = (-800, -100)
    node_diffuse.image = img_diffuse
    
    mix_color = nodes.new('ShaderNodeMix')
    mix_color.data_type = 'RGBA'
    mix_color.blend_type = 'MULTIPLY'
    mix_color.location = (-200, 100)
    mix_color.inputs['Factor'].default_value = 1.0
    
    img_rough = get_or_create_proxy_image("proxy_roughness.png", (0.6, 0.6, 0.6, 1.0), is_data=True)
    node_rough = nodes.new('ShaderNodeTexImage')
    node_rough.location = (-800, -400)
    node_rough.image = img_rough
    
    img_normal = get_or_create_proxy_image("proxy_normal.png", (0.5, 0.5, 1.0, 1.0), is_data=True)
    node_normal = nodes.new('ShaderNodeTexImage')
    node_normal.location = (-800, -700)
    node_normal.image = img_normal
    
    normal_map = nodes.new('ShaderNodeNormalMap')
    normal_map.location = (-400, -700)
    
    links.new(tex_coord.outputs['UV'], node_diffuse.inputs['Vector'])
    links.new(tex_coord.outputs['UV'], node_rough.inputs['Vector'])
    links.new(tex_coord.outputs['UV'], node_normal.inputs['Vector'])
    
    links.new(attr.outputs['Fac'], has_seed.inputs[0])
    links.new(has_seed.outputs['Value'], mix_seed.inputs['Factor'])
    links.new(obj_info.outputs['Random'], mix_seed.inputs['A'])
    links.new(attr.outputs['Fac'], mix_seed.inputs['B'])

    links.new(mix_seed.outputs['Result'], color_ramp.inputs['Fac'])
    
    links.new(color_ramp.outputs['Color'], mix_color.inputs['A'])
    links.new(node_diffuse.outputs['Color'], mix_color.inputs['B'])
    
    links.new(mix_color.outputs['Result'], bsdf.inputs['Base Color'])
    links.new(node_rough.outputs['Color'], bsdf.inputs['Roughness'])
    
    links.new(node_normal.outputs['Color'], normal_map.inputs['Color'])
    links.new(normal_map.outputs['Normal'], bsdf.inputs['Normal'])
    
    links.new(bsdf.outputs['BSDF'], out_node.inputs['Surface'])
    
    return mat
