import bpy
import bmesh

def create_roof_bows(name, width, length, spacing=0.6):
    """Generates transverse roof bows (structural support beams)."""
    mesh = bpy.data.meshes.new(name)
    obj = bpy.data.objects.new(name, mesh)
    bm = bmesh.new()
    
    # Typical roof bow dimensions
    bow_w = width
    bow_l = 0.04 # 40mm wide
    bow_h = 0.02 # 20mm high
    
    # Calculate number of bows based on length and spacing
    num_bows = max(1, int(length / spacing))
    actual_spacing = length / num_bows
    
    # Generate bows (skipping the very ends as the frame rails support those)
    for i in range(1, num_bows):
        y_pos = -length/2 + i * actual_spacing
        
        geom = bmesh.ops.create_cube(bm, size=1.0)
        bmesh.ops.scale(bm, verts=geom['verts'], vec=(bow_w, bow_l, bow_h))
        bmesh.ops.translate(bm, verts=geom['verts'], vec=(0, y_pos, 0))
        
    bm.to_mesh(mesh)
    bm.free()
    
    obj["is_container_part"] = True
    return obj