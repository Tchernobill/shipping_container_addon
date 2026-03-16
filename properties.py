import bpy
from .systems.rebuild import rebuild_container

def update_container(self, context):
    """Callback triggered whenever a container property changes."""
    rebuild_container(self.id_data)

class ShippingContainerProperties(bpy.types.PropertyGroup):
    is_container: bpy.props.BoolProperty(
        name="Is Container", 
        default=False,
        description="Identifies this object as a Shipping Container root"
    )
    
    container_size: bpy.props.EnumProperty(
        name="Size",
        description="Standard ISO container size",
        items=[
            ('10FT', "10ft", "10 foot container"),
            ('20FT', "20ft", "20 foot standard container"),
            ('40FT', "40ft", "40 foot standard container"),
        ],
        default='20FT',
        update=update_container
    )
    
    detail_level: bpy.props.EnumProperty(
        name="Detail Level",
        description="Level of detail for the container",
        items=[
            ('HIGH', "High (Full Geometry)", "Generates all individual parts"),
            ('LOW', "Low (Textured Box)", "Generates a simple proxy box with procedural materials")
        ],
        default='HIGH',
        update=update_container
    )
    
    door_open_angle: bpy.props.FloatProperty(
        name="Door Angle",
        description="Angle of the doors",
        default=0.0,
        min=0.0,
        max=4.71239,
        subtype='ANGLE',
        update=update_container
    )
    
    container_lod: bpy.props.EnumProperty(
        name="LOD",
        description="Level of Detail",
        items=[
            ('LOD0', "LOD0 (High)", "Full detail"),
            ('LOD1', "LOD1 (Medium)", "Simplified"),
            ('LOD2', "LOD2 (Low)", "Simple box"),
        ],
        default='LOD0',
        update=update_container
    )
    
    # Panel toggles
    show_front_panel: bpy.props.BoolProperty(name="Front Frame & Doors", default=True, update=update_container)
    show_left_door: bpy.props.BoolProperty(name="Left Door", default=True, update=update_container)
    show_right_door: bpy.props.BoolProperty(name="Right Door", default=True, update=update_container)
    
    show_back_panel: bpy.props.BoolProperty(name="Back Panel", default=True, update=update_container)
    show_left_panel: bpy.props.BoolProperty(name="Left Panel", default=True, update=update_container)
    show_right_panel: bpy.props.BoolProperty(name="Right Panel", default=True, update=update_container)
    show_floor: bpy.props.BoolProperty(name="Floor", default=True, update=update_container)
    show_roof: bpy.props.BoolProperty(name="Roof", default=True, update=update_container)

def register():
    bpy.utils.register_class(ShippingContainerProperties)
    bpy.types.Object.shipping_container = bpy.props.PointerProperty(type=ShippingContainerProperties)

def unregister():
    del bpy.types.Object.shipping_container
    bpy.utils.unregister_class(ShippingContainerProperties)