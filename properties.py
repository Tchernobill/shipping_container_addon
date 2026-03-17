import bpy
from .systems import rebuild as rebuild_system

def update_container_rebuild(self, context):
    """Callback triggered whenever a container property changes and requires a full rebuild."""
    rebuild_system.rebuild_container(self.id_data, context=context)

def update_door_angle(self, context):
    """Fast path for door animation without a full rebuild when possible."""
    root_obj = self.id_data
    if rebuild_system.update_door_pivots(root_obj):
        return
    rebuild_system.rebuild_container(root_obj, context=context)

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
        update=update_container_rebuild
    )
    
    detail_level: bpy.props.EnumProperty(
        name="Detail Level",
        description="Level of detail for the container",
        items=[
            ('HIGH', "High (Full Geometry)", "Generates all individual parts"),
            ('LOW', "Low (Textured Box)", "Generates a simple proxy box with procedural materials")
        ],
        default='HIGH',
        update=update_container_rebuild
    )
    
    door_open_angle: bpy.props.FloatProperty(
        name="Door Angle",
        description="Angle of the doors",
        default=0.0,
        min=0.0,
        max=4.71239,
        subtype='ANGLE',
        update=update_door_angle
    )
    
    # Panel toggles
    show_front_panel: bpy.props.BoolProperty(name="Front Frame & Doors", default=True, update=update_container_rebuild)
    show_left_door: bpy.props.BoolProperty(name="Left Door", default=True, update=update_container_rebuild)
    show_right_door: bpy.props.BoolProperty(name="Right Door", default=True, update=update_container_rebuild)
    
    show_back_panel: bpy.props.BoolProperty(name="Back Panel", default=True, update=update_container_rebuild)
    show_left_panel: bpy.props.BoolProperty(name="Left Panel", default=True, update=update_container_rebuild)
    show_right_panel: bpy.props.BoolProperty(name="Right Panel", default=True, update=update_container_rebuild)
    show_floor: bpy.props.BoolProperty(name="Floor", default=True, update=update_container_rebuild)
    show_roof: bpy.props.BoolProperty(name="Roof", default=True, update=update_container_rebuild)

def register():
    bpy.utils.register_class(ShippingContainerProperties)
    bpy.types.Object.shipping_container = bpy.props.PointerProperty(type=ShippingContainerProperties)

def unregister():
    del bpy.types.Object.shipping_container
    bpy.utils.unregister_class(ShippingContainerProperties)
