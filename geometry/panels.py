from .primitives import create_object_from_mesh, get_or_create_plane_mesh_xy

def create_plane(name, width, height, location, rotation):
    """Creates a basic plane with specific dimensions, location, and rotation."""
    mesh = get_or_create_plane_mesh_xy(width, height, keep=True)
    return create_object_from_mesh(
        name,
        mesh,
        location=location,
        rotation=rotation,
        tag_container_part=True,
    )
