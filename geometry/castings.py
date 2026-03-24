import bpy
import bmesh
import math
import mathutils
from ..utils import remove_object_and_orphan_data

def create_pill_cutter(name, length, width, depth, axis):
    """Creates a pill-shaped cylinder for boolean cutting."""
    mesh = bpy.data.meshes.new(name)
    obj = bpy.data.objects.new(name, mesh)
    bm = bmesh.new()
    
    # Create base cylinder
    bmesh.ops.create_cone(bm, cap_ends=True, cap_tris=False, segments=24, radius1=width/2, radius2=width/2, depth=depth)
    
    # Stretch into a pill shape
    stretch = (length - width) / 2
    if stretch > 0:
        for v in bm.verts:
            if axis == 'Z': 
                if v.co.y > 0.001: v.co.y += stretch
                elif v.co.y < -0.001: v.co.y -= stretch
            elif axis == 'Y': 
                if v.co.x > 0.001: v.co.x += stretch
                elif v.co.x < -0.001: v.co.x -= stretch
            elif axis == 'X': 
                if v.co.x > 0.001: v.co.x += stretch
                elif v.co.y < -0.001: v.co.y -= stretch
                
    # Rotate to point along the correct axis
    if axis == 'Y':
        bmesh.ops.rotate(bm, verts=bm.verts, cent=(0,0,0), matrix=mathutils.Matrix.Rotation(math.radians(90), 3, 'X'))
    elif axis == 'X':
        bmesh.ops.rotate(bm, verts=bm.verts, cent=(0,0,0), matrix=mathutils.Matrix.Rotation(math.radians(90), 3, 'Y'))
        
    bm.to_mesh(mesh)
    bm.free()
    return obj

def get_or_create_master_casting_mesh(context=None):
    """Generates the master ISO 1161 Corner Casting mesh ONCE and caches it."""
    mesh_name = "ISO_Casting_Master_Mesh"
    
    # If it already exists, return it immediately (Zero boolean cost!)
    if mesh_name in bpy.data.meshes:
        return bpy.data.meshes[mesh_name]
        
    # ISO 1161 Casting corner dimensions
    cw = 0.162 
    cl = 0.178 
    ch = 0.118 
    
    # 1. Create Base Block
    mesh = bpy.data.meshes.new("temp_casting")
    obj = bpy.data.objects.new("temp_casting_obj", mesh)
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    bmesh.ops.scale(bm, vec=(cw, cl, ch), verts=bm.verts)
    bm.to_mesh(mesh)
    bm.free()
    
    # Link to scene temporarily to evaluate booleans
    scene = context.scene if context is not None and getattr(context, "scene", None) is not None else bpy.context.scene
    scene.collection.objects.link(obj)
    
    # 2. Create Cutters
    cut_top = create_pill_cutter("temp_cut_top", 0.110, 0.064, 0.300, 'Z')
    cut_top.location = (0, -0.008, 0)
    
    cut_front = create_pill_cutter("temp_cut_front", 0.080, 0.064, 0.300, 'Y')
    cut_front.location = (0, 0, 0)
    
    cut_side = create_pill_cutter("temp_cut_side", 0.0794, 0.0635, 0.300, 'X')
    cut_side.location = (0, 0.0125, 0)
    
    cutters = [cut_top, cut_front, cut_side]
    
    for cutter in cutters:
        scene.collection.objects.link(cutter)
        mod = obj.modifiers.new(name="Hole", type='BOOLEAN')
        mod.object = cutter
        mod.operation = 'DIFFERENCE'
        mod.solver = 'MANIFOLD'
        
    # 3. Evaluate modifiers and apply mesh
    depsgraph = context.evaluated_depsgraph_get() if context is not None and hasattr(context, "evaluated_depsgraph_get") else bpy.context.evaluated_depsgraph_get()
    eval_obj = obj.evaluated_get(depsgraph)
    new_mesh = bpy.data.meshes.new_from_object(eval_obj)
    new_mesh.name = mesh_name
    new_mesh.use_fake_user = True # Keep it in memory even if all containers are deleted
    
    # 4. Cleanup temporary objects
    remove_object_and_orphan_data(obj)
    for cutter in cutters:
        remove_object_and_orphan_data(cutter)
        
    return new_mesh

def create_corner_casting_instance(name, location, is_top, is_front, is_left, context=None):
    """Creates a lightweight instance of the master casting mesh."""
    master_mesh = get_or_create_master_casting_mesh(context=context)
    
    # Create an object that uses the cached mesh data
    obj = bpy.data.objects.new(name, master_mesh)
    
    # ISO 1161 Dimensions
    cw = 0.162 
    cl = 0.178 
    ch = 0.118 
    
    # Shift origin from center to the absolute outer corner
    x_offset = cw/2 if is_left else -cw/2
    y_offset = cl/2 if is_front else -cl/2
    z_offset = -ch/2 if is_top else ch/2
    
    obj.location = (location[0] + x_offset, location[1] + y_offset, location[2] + z_offset)
    
    # Mirroring via scale to ensure the asymmetrical holes align correctly
    scale_x = 1 if is_left else -1
    scale_y = 1 if is_front else -1
    scale_z = 1 if is_top else -1
    
    obj.scale = (scale_x, scale_y, scale_z)
    
    obj["is_container_part"] = True
    return obj
