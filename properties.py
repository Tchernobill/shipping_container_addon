import bpy
from .systems import rebuild as rebuild_system


def update_container_rebuild(self, context):
    """Full geometry rebuild triggered by structural property changes."""
    rebuild_system.rebuild_container(self.id_data, context=context)


def update_door_angle(self, context):
    """Fast path for door animation — skips rebuild when only pivots need moving."""
    root_obj = self.id_data
    if rebuild_system.update_door_pivots(root_obj):
        return
    rebuild_system.rebuild_container(root_obj, context=context)


def update_shader_props(self, context):
    """Stamp shader control values onto all metal mesh children.

    No geometry rebuild is needed — the v5 shader reads these values via
    ShaderNodeAttribute (attribute_type='OBJECT'), so changing the custom
    property on a mesh child is sufficient to update the rendered result.
    """
    root_obj = self.id_data
    if not root_obj:
        return
    p = self
    color = list(p.shader_color_override)   # [r, g, b, a]

    for child in root_obj.children_recursive:
        if child.type == 'MESH':
            child["shader_rust_strength"]      = p.shader_rust_strength
            child["shader_stain_intensity"]    = p.shader_stain_intensity
            child["shader_dust_intensity"]     = p.shader_dust_intensity
            child["shader_scratch_intensity"]  = p.shader_scratch_intensity
            child["shader_color_override_amt"] = p.shader_color_override_amount
            child["shader_color_override"]     = color


class ShippingContainerProperties(bpy.types.PropertyGroup):
    is_container: bpy.props.BoolProperty(
        name="Is Container",
        default=False,
        description="Identifies this object as a Shipping Container root",
    ) # type: ignore

    container_size: bpy.props.EnumProperty(
        name="Size",
        description="Standard ISO container size",
        items=[
            ('10FT', "10ft", "10 foot container"),
            ('20FT', "20ft", "20 foot container"),
            ('40FT', "40ft", "40 foot container"),
        ],
        default='20FT',
        update=update_container_rebuild,
    ) # type: ignore

    detail_level: bpy.props.EnumProperty(
        name="Detail Level",
        description="Level of detail for the container",
        items=[
            ('HIGH', "High (Full Geometry)", "Generates all individual parts"),
            ('LOW',  "Low (Textured Box)",   "Generates a simple proxy box with procedural materials"),
        ],
        default='HIGH',
        update=update_container_rebuild,
    ) # type: ignore

    door_open_angle: bpy.props.FloatProperty(
        name="Door Angle",
        description="How far the doors are open",
        default=0.0,
        min=0.0,
        max=4.71239,
        subtype='ANGLE',
        update=update_door_angle,
    ) # type: ignore

    door_corrugations: bpy.props.IntProperty(
        name="Door Corrugations",
        description=(
            "Number of horizontal corrugation ribs on each door panel. "
            "0 = flat recessed panel.  Maximum that fits depends on door height "
            "(auto-clamped with a 15 mm minimum gap)."
        ),
        default=3,
        min=0,
        max=5,
        update=update_container_rebuild,
    ) # type: ignore

    # ── Panel visibility toggles ───────────────────────────────────────────────
    ui_parts_expanded: bpy.props.BoolProperty(
        name="Parts Toggles",
        description="Expand / collapse the Parts visibility toggles",
        default=False,
    ) # type: ignore
    
    show_front_panel: bpy.props.BoolProperty(
        name="Front Frame & Doors", default=True,  update=update_container_rebuild) # type: ignore
    show_left_door:   bpy.props.BoolProperty(
        name="Left Door",           default=True,  update=update_container_rebuild) # type: ignore
    show_right_door:  bpy.props.BoolProperty(
        name="Right Door",          default=True,  update=update_container_rebuild) # type: ignore
    show_back_panel:  bpy.props.BoolProperty(
        name="Back Panel",          default=True,  update=update_container_rebuild) # type: ignore
    show_left_panel:  bpy.props.BoolProperty(
        name="Left Panel",          default=True,  update=update_container_rebuild) # type: ignore
    show_right_panel: bpy.props.BoolProperty(
        name="Right Panel",         default=True,  update=update_container_rebuild) # type: ignore
    show_floor:       bpy.props.BoolProperty(
        name="Floor",               default=True,  update=update_container_rebuild) # type: ignore
    show_roof:        bpy.props.BoolProperty(
        name="Roof",                default=True,  update=update_container_rebuild) # type: ignore

    # ── Shader controls ────────────────────────────────────────────────────────
    # These values are stamped as object custom properties onto every metal mesh
    # child by update_shader_props() so the v5 ShaderNodeAttribute nodes pick
    # them up.  Changing a value here updates the render instantly without any
    # geometry rebuild.

    ui_shader_expanded: bpy.props.BoolProperty(
        name="Shader",
        description="Expand / collapse the Shader section",
        default=False,
    ) # type: ignore

    shader_rust_strength: bpy.props.FloatProperty(
        name="Rust Strength",
        description="Amount of edge rust and rust patches",
        default=0.35,
        min=0.0,
        max=2.0,
        update=update_shader_props,
    ) # type: ignore

    shader_stain_intensity: bpy.props.FloatProperty(
        name="Water Stain",
        description="Intensity of water-streak stains (upper half of container)",
        default=0.60,
        min=0.0,
        max=1.0,
        update=update_shader_props,
    ) # type: ignore

    shader_dust_intensity: bpy.props.FloatProperty(
        name="Dust / Grime",
        description="Amount of dust and grime (lower half + recessed areas)",
        default=0.65,
        min=0.0,
        max=1.0,
        update=update_shader_props,
    ) # type: ignore

    shader_scratch_intensity: bpy.props.FloatProperty(
        name="Scratches",
        description="Density of horizontal surface scratches",
        default=0.25,
        min=0.0,
        max=1.0,
        update=update_shader_props,
    ) # type: ignore

    shader_color_override_amount: bpy.props.FloatProperty(
        name="Color Override Blend",
        description="0 = seed-driven palette colour, 1 = use Override Color",
        default=0.0,
        min=0.0,
        max=1.0,
        update=update_shader_props,
    ) # type: ignore

    shader_color_override: bpy.props.FloatVectorProperty(
        name="Override Color",
        description="Manual paint colour used when Color Override Blend > 0",
        subtype='COLOR',
        size=4,
        min=0.0,
        max=1.0,
        default=(0.55, 0.07, 0.04, 1.0),
        update=update_shader_props,
    ) # type: ignore

    # ── Stack Creator settings ─────────────────────────────────────────────────
    ui_stack_expanded: bpy.props.BoolProperty(
        name="Stack",
        description="Expand / collapse the Stack section",
        default=False,
    ) # type: ignore

    stack_width: bpy.props.IntProperty(
        name="Width",
        description="Number of containers side by side (X axis)",
        default=4, min=1, max=20,
    ) # type: ignore

    stack_depth: bpy.props.IntProperty(
        name="Depth",
        description="Number of containers front to back (Y axis)",
        default=2, min=1, max=20,
    ) # type: ignore

    stack_height: bpy.props.IntProperty(
        name="Height",
        description="Number of containers stacked vertically (Z axis)",
        default=6, min=1, max=20,
    ) # type: ignore

    stack_random_orient: bpy.props.BoolProperty(
        name="Random Orientation",
        description=(
            "Randomly rotate each container 180° around Z so doors face "
            "either the front or the back of the stack"
        ),
        default=False,
    ) # type: ignore

    stack_seed: bpy.props.IntProperty(
        name="Seed",
        description="Random seed controlling container colours and orientations",
        default=42, min=0,
    ) # type: ignore


def register():
    bpy.utils.register_class(ShippingContainerProperties)
    bpy.types.Object.shipping_container = bpy.props.PointerProperty(
        type=ShippingContainerProperties)


def unregister():
    del bpy.types.Object.shipping_container
    bpy.utils.unregister_class(ShippingContainerProperties)
