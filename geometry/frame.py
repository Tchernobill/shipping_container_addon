import bpy
import bmesh

def create_box(name, width, depth, height, location):
    """Creates a basic box mesh used for posts and rails."""
    mesh = bpy.data.meshes.new(name)
    obj = bpy.data.objects.new(name, mesh)
    
    bm = bmesh.new()
    # size=1.0 creates a 1x1x1 unit cube centered at origin
    bmesh.ops.create_cube(bm, size=1.0)
    
    # Scale to target dimensions
    bmesh.ops.scale(bm, vec=(width, depth, height), verts=bm.verts)
    
    bm.to_mesh(mesh)
    bm.free()
    
    obj.location = location
    
    # Tag it so the rebuild system knows it's safe to delete
    obj["is_container_part"] = True
    
    return obj