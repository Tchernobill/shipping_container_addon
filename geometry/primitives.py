import bpy


def _q(v, step=1.0e-6):
    return int(round(float(v) / step))


def _box_mesh_name(sx, sy, sz):
    return f"_ISO_Box_{_q(sx)}_{_q(sy)}_{_q(sz)}"


def _plane_xy_mesh_name(sx, sy):
    return f"_ISO_PlaneXY_{_q(sx)}_{_q(sy)}"


def _plane_xz_mesh_name(sx, sz):
    return f"_ISO_PlaneXZ_{_q(sx)}_{_q(sz)}"


def create_object_from_mesh(
    name,
    mesh,
    *,
    location=None,
    rotation=None,
    tag_container_part=True,
    extra_props=None,
):
    obj = bpy.data.objects.new(name, mesh)
    if location is not None:
        obj.location = location
    if rotation is not None:
        obj.rotation_euler = rotation

    if tag_container_part:
        obj["is_container_part"] = True

    if extra_props:
        for k, v in extra_props.items():
            obj[k] = v
    return obj


def create_mesh_object(
    name,
    verts,
    faces,
    *,
    location=None,
    rotation=None,
    tag_container_part=True,
    extra_props=None,
):
    """Create a mesh object from raw verts/faces.

    `verts` is an iterable of (x, y, z).
    `faces` is an iterable of index sequences (tris/quads/ngons).
    """
    mesh = bpy.data.meshes.new(name)
    mesh.from_pydata(list(verts), [], list(faces))
    mesh.update()
    return create_object_from_mesh(
        name,
        mesh,
        location=location,
        rotation=rotation,
        tag_container_part=tag_container_part,
        extra_props=extra_props,
    )


def append_box(verts, faces, *, center=(0.0, 0.0, 0.0), size=(1.0, 1.0, 1.0)):
    """Append a box (axis-aligned) to `verts`/`faces`.

    `center` is the box center; `size` is full extents (sx, sy, sz).
    Faces are quads with outward-facing winding.
    """
    cx, cy, cz = center
    sx, sy, sz = size
    hx, hy, hz = sx * 0.5, sy * 0.5, sz * 0.5

    base = len(verts)
    verts.extend(
        [
            (cx - hx, cy - hy, cz - hz),  # 0
            (cx + hx, cy - hy, cz - hz),  # 1
            (cx + hx, cy + hy, cz - hz),  # 2
            (cx - hx, cy + hy, cz - hz),  # 3
            (cx - hx, cy - hy, cz + hz),  # 4
            (cx + hx, cy - hy, cz + hz),  # 5
            (cx + hx, cy + hy, cz + hz),  # 6
            (cx - hx, cy + hy, cz + hz),  # 7
        ]
    )

    faces.extend(
        [
            (base + 0, base + 3, base + 2, base + 1),  # bottom  (-Z)
            (base + 4, base + 5, base + 6, base + 7),  # top     (+Z)
            (base + 0, base + 1, base + 5, base + 4),  # -Y
            (base + 1, base + 2, base + 6, base + 5),  # +X
            (base + 2, base + 3, base + 7, base + 6),  # +Y
            (base + 0, base + 4, base + 7, base + 3),  # -X
        ]
    )


def get_or_create_box_mesh(sx, sy, sz, *, keep=True):
    """Return a cached axis-aligned box mesh centered at origin."""
    mesh_name = _box_mesh_name(sx, sy, sz)
    mesh = bpy.data.meshes.get(mesh_name)
    if mesh is not None:
        return mesh

    verts = []
    faces = []
    append_box(verts, faces, center=(0.0, 0.0, 0.0), size=(sx, sy, sz))
    mesh = bpy.data.meshes.new(mesh_name)
    mesh.from_pydata(verts, [], faces)
    mesh.update()
    if keep:
        mesh.use_fake_user = True
    return mesh


def get_or_create_plane_mesh_xy(sx, sy, *, keep=True):
    """Return a cached XY plane mesh centered at origin, +Z normal."""
    mesh_name = _plane_xy_mesh_name(sx, sy)
    mesh = bpy.data.meshes.get(mesh_name)
    if mesh is not None:
        return mesh

    verts = []
    faces = []
    append_plane_xy(verts, faces, center=(0.0, 0.0, 0.0), size=(sx, sy))
    mesh = bpy.data.meshes.new(mesh_name)
    mesh.from_pydata(verts, [], faces)
    mesh.update()
    if keep:
        mesh.use_fake_user = True
    return mesh


def get_or_create_plane_mesh_xz(sx, sz, *, keep=True):
    """Return a cached XZ plane mesh centered at origin."""
    mesh_name = _plane_xz_mesh_name(sx, sz)
    mesh = bpy.data.meshes.get(mesh_name)
    if mesh is not None:
        return mesh

    verts = []
    faces = []
    append_plane_xz(verts, faces, center=(0.0, 0.0, 0.0), size=(sx, sz))
    mesh = bpy.data.meshes.new(mesh_name)
    mesh.from_pydata(verts, [], faces)
    mesh.update()
    if keep:
        mesh.use_fake_user = True
    return mesh


def append_plane_xy(verts, faces, *, center=(0.0, 0.0, 0.0), size=(1.0, 1.0)):
    """Append a quad in the XY plane at Z=center.z.

    `size` is full extents (sx, sy). Winding gives +Z normal.
    """
    cx, cy, cz = center
    sx, sy = size
    hx, hy = sx * 0.5, sy * 0.5

    base = len(verts)
    verts.extend(
        [
            (cx - hx, cy - hy, cz),
            (cx + hx, cy - hy, cz),
            (cx + hx, cy + hy, cz),
            (cx - hx, cy + hy, cz),
        ]
    )
    faces.append((base + 0, base + 1, base + 2, base + 3))


def append_plane_xz(verts, faces, *, center=(0.0, 0.0, 0.0), size=(1.0, 1.0)):
    """Append a quad in the XZ plane at Y=center.y.

    `size` is full extents (sx, sz). Winding matches existing logo-plane behavior.
    """
    cx, cy, cz = center
    sx, sz = size
    hx, hz = sx * 0.5, sz * 0.5

    base = len(verts)
    verts.extend(
        [
            (cx - hx, cy, cz - hz),
            (cx + hx, cy, cz - hz),
            (cx + hx, cy, cz + hz),
            (cx - hx, cy, cz + hz),
        ]
    )
    faces.append((base + 0, base + 1, base + 2, base + 3))
