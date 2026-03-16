import bpy
import bmesh

def create_plane(name, width, height, location, rotation):
    """Creates a basic plane with specific dimensions, location, and rotation."""
    mesh = bpy.data.meshes.new(name)
    obj = bpy.data.objects.new(name, mesh)
    
    bm = bmesh.new()
    # size=0.5 creates a 1x1 unit plane centered at origin
    bmesh.ops.create_grid(bm, x_segments=1, y_segments=1, size=0.5)
    
    # Scale to target dimensions
    bmesh.ops.scale(bm, vec=(width, height, 1.0), verts=bm.verts)
    
    bm.to_mesh(mesh)
    bm.free()
    
    obj.location = location
    obj.rotation_euler = rotation
    
    # Tag it so the rebuild system knows it's safe to delete
    obj["is_container_part"] = True
    
    return obj