import bpy
import random
from .primitives import create_object_from_mesh, get_or_create_plane_mesh_xz

# ---------------------------------------------------------------------------
# Shipping company brand registry
# Each entry drives both the logo text colour and the logo material.
# Colors are sRGB hex strings (converted to linear by the material helper).
# ---------------------------------------------------------------------------
SHIPPING_COMPANIES = [
    {"name": "MAERSK",       "color": "#42A4D5"},  # Maersk blue
    {"name": "MSC",          "color": "#1B2F6E"},  # MSC navy
    {"name": "COSCO",        "color": "#CC1F1A"},  # COSCO red
    {"name": "CMA CGM",      "color": "#E31837"},  # CMA red
    {"name": "EVERGREEN",    "color": "#006341"},  # Evergreen green
    {"name": "HAPAG-LLOYD",  "color": "#F07D00"},  # Hapag orange
    {"name": "ONE",          "color": "#E4007F"},  # ONE magenta
    {"name": "YANG MING",    "color": "#C8102E"},  # Yang Ming crimson
    {"name": "ZIM",          "color": "#005DAA"},  # ZIM blue
    {"name": "PIL",          "color": "#003087"},  # PIL dark blue
]


def get_company_for_seed(seed):
    """Returns a shipping company dict deterministically from the container seed.

    A separate RNG offset (+7919) is used so the company choice is independent
    from the colour seed already stored on the container root object.
    """
    rng = random.Random(int(seed * 1_000_000) + 7919)
    return rng.choice(SHIPPING_COMPANIES)


# ---------------------------------------------------------------------------
# Container ID decal
# ---------------------------------------------------------------------------

def generate_container_id(seed=None):
    """Generates a random standard container ID based on the container's seed."""
    rng = random.Random(seed) if seed is not None else random

    letters = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    owner_code = "".join(rng.choices(letters, k=3)) + "U"
    serial = "".join(rng.choices("0123456789", k=6))
    check_digit = rng.choice("0123456789")

    return f"{owner_code} {serial} {check_digit}"


def create_text_decal(name, text, size=0.15, align_x='LEFT', align_y='TOP'):
    """Creates a 3D text object for small informational decals.

    The font curve lies in the local XY plane.  Callers must apply
    rotation_euler = (pi/2, 0, 0) to orient text in the world XZ plane
    (readable when looking at the door from -Y).
    Place the object at Y = -0.001 so it sits just in front of the door face
    and avoids Z-fighting with the background surface.
    """
    font_curve = bpy.data.curves.new(type="FONT", name=name)
    font_curve.body = text
    font_curve.extrude = 0.002   # Very thin — just enough to be visible
    font_curve.size = size
    font_curve.align_x = align_x
    font_curve.align_y = align_y

    obj = bpy.data.objects.new(name, font_curve)
    obj["is_container_part"] = True
    return obj


# ---------------------------------------------------------------------------
# Company logo decal  (3-D extruded text, centred on its local origin)
# ---------------------------------------------------------------------------

def create_logo_text(name, company_name, size=0.42):
    """Creates a large company-name logo as a 3-D font object.

    Tagged with ``is_logo_decal = True`` so the generic material assignment
    pass in rebuild.py skips it (brand / white material is assigned directly).
    align_x = 'CENTER' / align_y = 'CENTER' so the pivot is the text midpoint.
    """
    font_curve = bpy.data.curves.new(type="FONT", name=name)
    font_curve.body = company_name
    font_curve.extrude = 0.003   # Slightly thicker than small decals
    font_curve.size = size
    font_curve.align_x = 'CENTER'
    font_curve.align_y = 'CENTER'

    obj = bpy.data.objects.new(name, font_curve)
    obj["is_container_part"] = True
    obj["is_logo_decal"] = True
    return obj


# ---------------------------------------------------------------------------
# Logo backing plane
# ---------------------------------------------------------------------------

def create_logo_plane(name, width, height):
    """Flat quad in the XZ plane used as a coloured backing for a company logo.

    The face lies at Y = 0 and is visible from the -Y direction (viewer).
    Callers should offset by location.y = -0.001 to sit just in front of the
    door background and avoid Z-fighting.

    Tagged ``is_logo_decal = True`` so the generic material loop skips it;
    the brand material is assigned by the caller immediately after creation.
    """
    mesh = get_or_create_plane_mesh_xz(width, height, keep=True)
    return create_object_from_mesh(
        name,
        mesh,
        tag_container_part=True,
        extra_props={"is_logo_decal": True},
    )
