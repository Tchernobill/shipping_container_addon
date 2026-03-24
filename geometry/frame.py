from .primitives import create_object_from_mesh, get_or_create_box_mesh

def create_box(name, width, depth, height, location):
    """Creates a basic box mesh used for posts and rails."""
    mesh = get_or_create_box_mesh(width, depth, height, keep=True)
    return create_object_from_mesh(name, mesh, location=location, tag_container_part=True)
