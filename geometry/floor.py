import bpy
import bmesh

def create_floor_cross_members(name, width, length, spacing=0.3, pocket_spacing=2.05):
    """Generates transverse floor cross members (structural support beams)."""
    mesh = bpy.data.meshes.new(name)
    obj = bpy.data.objects.new(name, mesh)
    bm = bmesh.new()
    
    # Typical floor cross member dimensions (C-channel or I-beam)
    beam_w = width
    beam_l = 0.05 # 50mm wide
    beam_h = 0.0975 # Match rail height perfectly
    
    # Calculate number of cross members based on length and spacing
    num_beams = max(1, int(length / spacing))
    actual_spacing = length / num_beams
    
    pocket_w = 0.300 # Scaled pocket width
    pocket_y1 = -pocket_spacing/2
    pocket_y2 = pocket_spacing/2
    
    # Generate cross members
    for i in range(1, num_beams):
        y_pos = -length/2 + i * actual_spacing
        
        # Skip cross members that intersect with the forklift pockets
        if (abs(y_pos - pocket_y1) < pocket_w/2 + 0.05) or (abs(y_pos - pocket_y2) < pocket_w/2 + 0.05):
            continue
            
        geom = bmesh.ops.create_cube(bm, size=1.0)
        bmesh.ops.scale(bm, verts=geom['verts'], vec=(beam_w, beam_l, beam_h))
        bmesh.ops.translate(bm, verts=geom['verts'], vec=(0, y_pos, 0))
        
    bm.to_mesh(mesh)
    bm.free()
    
    obj["is_container_part"] = True
    return obj

def create_wooden_floor(name, width, length):
    """Generates the marine plywood floor panels."""
    mesh = bpy.data.meshes.new(name)
    obj = bpy.data.objects.new(name, mesh)
    bm = bmesh.new()
    
    # Standard marine plywood thickness is 28mm
    thickness = 0.028
    
    # Create the main floor board
    bmesh.ops.create_cube(bm, size=1.0)
    bmesh.ops.scale(bm, verts=bm.verts, vec=(width, length, thickness))
    
    bm.to_mesh(mesh)
    bm.free()
    
    obj["is_container_part"] = True
    return obj

def create_forklift_pocket_cutters(name, width, spacing=2.05):
    """Creates boolean cutters for punching holes in the side rails."""
    mesh = bpy.data.meshes.new(name)
    obj = bpy.data.objects.new(name, mesh)
    bm = bmesh.new()
    
    pocket_w = 0.300 
    pocket_h = 0.080 
    pocket_d = width + 0.5 # Extra wide to ensure it cuts completely through
    
    geom1 = bmesh.ops.create_cube(bm, size=1.0)
    bmesh.ops.scale(bm, verts=geom1['verts'], vec=(pocket_d, pocket_w, pocket_h))
    bmesh.ops.translate(bm, verts=geom1['verts'], vec=(0, -spacing/2, 0))
    
    geom2 = bmesh.ops.create_cube(bm, size=1.0)
    bmesh.ops.scale(bm, verts=geom2['verts'], vec=(pocket_d, pocket_w, pocket_h))
    bmesh.ops.translate(bm, verts=geom2['verts'], vec=(0, spacing/2, 0))
    
    bm.to_mesh(mesh)
    bm.free()
    
    return obj

def create_forklift_pocket_tubes(name, width, spacing=2.05):
    """Generates the structural tubes for the forklift pockets."""
    mesh = bpy.data.meshes.new(name)
    obj = bpy.data.objects.new(name, mesh)
    bm = bmesh.new()
    
    pocket_w = 0.300
    pocket_h = 0.080
    t = 0.006 # 6mm steel thickness
    
    for y_offset in [-spacing/2, spacing/2]:
        # Top plate
        top = bmesh.ops.create_cube(bm, size=1.0)
        bmesh.ops.scale(bm, verts=top['verts'], vec=(width, pocket_w + 2*t, t))
        bmesh.ops.translate(bm, verts=top['verts'], vec=(0, y_offset, pocket_h/2 + t/2))
        
        # Bottom plate
        bot = bmesh.ops.create_cube(bm, size=1.0)
        bmesh.ops.scale(bm, verts=bot['verts'], vec=(width, pocket_w + 2*t, t))
        bmesh.ops.translate(bm, verts=bot['verts'], vec=(0, y_offset, -pocket_h/2 - t/2))
        
        # Front plate
        front = bmesh.ops.create_cube(bm, size=1.0)
        bmesh.ops.scale(bm, verts=front['verts'], vec=(width, t, pocket_h))
        bmesh.ops.translate(bm, verts=front['verts'], vec=(0, y_offset - pocket_w/2 - t/2, 0))
        
        # Back plate
        back = bmesh.ops.create_cube(bm, size=1.0)
        bmesh.ops.scale(bm, verts=back['verts'], vec=(width, t, pocket_h))
        bmesh.ops.translate(bm, verts=back['verts'], vec=(0, y_offset + pocket_w/2 + t/2, 0))
        
    bm.to_mesh(mesh)
    bm.free()
    
    obj["is_container_part"] = True
    return obj