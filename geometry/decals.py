import bpy
import random

def generate_container_id(seed=None):
    """Generates a random standard container ID based on the container's seed."""
    rng = random.Random(seed) if seed is not None else random

    letters = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    owner_code = "".join(rng.choices(letters, k=3)) + "U"
    serial = "".join(rng.choices("0123456789", k=6))
    check_digit = rng.choice("0123456789")

    return f"{owner_code} {serial} {check_digit}"

def create_text_decal(name, text, size=0.15, align_x='LEFT', align_y='TOP'):
    """Creates a 3D text object for decals."""
    font_curve = bpy.data.curves.new(type="FONT", name=name)
    font_curve.body = text
    font_curve.extrude = 0.002 # Very thin, just enough to be visible
    font_curve.size = size
    font_curve.align_x = align_x
    font_curve.align_y = align_y
    
    obj = bpy.data.objects.new(name, font_curve)
    obj["is_container_part"] = True
    return obj
