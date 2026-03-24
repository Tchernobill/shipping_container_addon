import bpy

from .primitives import append_box, create_object_from_mesh

def create_roof_bows(name, width, length, spacing=0.6):
    """Generates transverse roof bows (structural support beams)."""
    # Typical roof bow dimensions
    bow_w = width
    bow_l = 0.04 # 40mm wide
    bow_h = 0.02 # 20mm high

    # Calculate number of bows based on length and spacing
    num_bows = max(1, int(length / spacing))
    actual_spacing = length / num_bows

    mesh_name = f"_ISO_RoofBows_{int(round(width*1e6))}_{int(round(length*1e6))}_{int(round(spacing*1e6))}"
    mesh = bpy.data.meshes.get(mesh_name)
    if mesh is None:
        verts = []
        faces = []

        # Generate bows (skipping the very ends as the frame rails support those)
        for i in range(1, num_bows):
            y_pos = -length / 2 + i * actual_spacing
            append_box(verts, faces, center=(0.0, y_pos, 0.0), size=(bow_w, bow_l, bow_h))

        mesh = bpy.data.meshes.new(mesh_name)
        mesh.from_pydata(verts, [], faces)
        mesh.update()
        mesh.use_fake_user = True

    return create_object_from_mesh(name, mesh, tag_container_part=True)
