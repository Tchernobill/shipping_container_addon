import bpy
import bmesh

def map_range(value, in_min, in_max, out_min, out_max):
    if in_max == in_min: return out_min
    return out_min + (((value - in_min) / (in_max - in_min)) * (out_max - out_min))

def create_proxy_box(name, W, L, H):
    """Creates a 9-sliced low-poly box with perfect UV mapping for LODs."""
    mesh = bpy.data.meshes.new(name)
    obj = bpy.data.objects.new(name, mesh)
    bm = bmesh.new()

    # Casting margins
    mx, my, mz = 0.162, 0.178, 0.118

    # X, Y, Z coordinates for the 9-slice grid
    xs = [0, mx, W-mx, W]
    ys = [0, my, L-my, L]
    zs = [0, mz, H-mz, H]

    # Create 64 vertices
    verts = [[[None for _ in range(4)] for _ in range(4)] for _ in range(4)]
    for i, x in enumerate(xs):
        for j, y in enumerate(ys):
            for k, z in enumerate(zs):
                verts[i][j][k] = bm.verts.new((x, y, z))

    # Helper to create faces safely
    def make_face(v1, v2, v3, v4):
        try:
            bm.faces.new((v1, v2, v3, v4))
        except ValueError:
            pass

    # Bottom (k=0) and Top (k=3)
    for i in range(3):
        for j in range(3):
            make_face(verts[i][j][0], verts[i+1][j][0], verts[i+1][j+1][0], verts[i][j+1][0])
            make_face(verts[i][j][3], verts[i][j+1][3], verts[i+1][j+1][3], verts[i+1][j][3])

    # Front (j=0) and Back (j=3)
    for i in range(3):
        for k in range(3):
            make_face(verts[i][0][k], verts[i][0][k+1], verts[i+1][0][k+1], verts[i+1][0][k])
            make_face(verts[i][3][k], verts[i+1][3][k], verts[i+1][3][k+1], verts[i][3][k+1])

    # Left (i=0) and Right (i=3)
    for j in range(3):
        for k in range(3):
            make_face(verts[0][j][k], verts[0][j+1][k], verts[0][j+1][k+1], verts[0][j][k+1])
            make_face(verts[3][j][k], verts[3][j][k+1], verts[3][j+1][k+1], verts[3][j+1][k])

    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    
    # --- 9-SLICE UV MAPPING ---
    base_W, base_L, base_H = 2.438, 6.058, 2.591
    
    def get_uv_coord(val, max_val, margin, base_max):
        if val <= margin + 0.001:
            return val / base_max
        elif val >= max_val - margin - 0.001:
            return (base_max - (max_val - val)) / base_max
        else:
            return map_range(val, margin, max_val-margin, margin/base_max, (base_max-margin)/base_max)

    uv_layer = bm.loops.layers.uv.verify()
    for face in bm.faces:
        normal = face.normal
        nx, ny, nz = abs(normal.x), abs(normal.y), abs(normal.z)
        
        for loop in face.loops:
            v = loop.vert.co
            if nx > ny and nx > nz: # Left/Right
                u = get_uv_coord(v.y, L, my, base_L)
                v_coord = get_uv_coord(v.z, H, mz, base_H)
            elif ny > nx and ny > nz: # Front/Back
                u = get_uv_coord(v.x, W, mx, base_W)
                v_coord = get_uv_coord(v.z, H, mz, base_H)
            else: # Top/Bottom
                u = get_uv_coord(v.x, W, mx, base_W)
                v_coord = get_uv_coord(v.y, L, my, base_L)
                
            loop[uv_layer].uv = (u, v_coord)

    bm.to_mesh(mesh)
    bm.free()
    
    obj["is_container_part"] = True
    return obj
