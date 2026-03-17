import bpy
from .utils import find_container_root

def draw_container_controls(layout, obj):
    """Draw shared UI controls for both the N-panel and the Properties editor panel."""
    root = find_container_root(obj)

    # If nothing is selected, or it's not part of a container, show the Create button.
    if not root:
        layout.operator("object.create_shipping_container", text="Create Container", icon='MESH_CUBE')
        return

    if obj is not root:
        layout.label(text=f"Editing Root: {root.name}")

    props = root.shipping_container

    # Main properties
    layout.prop(props, "container_size")
    layout.prop(props, "detail_level")
    layout.prop(props, "door_open_angle")

    # Bake
    layout.separator()
    layout.operator("object.bake_container_to_single_mesh", text="Bake to Single Object", icon='MESH_DATA')
    layout.separator()

    # Visibility toggles
    box = layout.box()
    box.label(text="Visibility Toggles:", icon='RESTRICT_VIEW_OFF')

    col = box.column(align=True)
    col.prop(props, "show_front_panel")

    # Indent the door toggles under the front panel
    if props.show_front_panel:
        row = col.row()
        row.separator(factor=2.0)
        sub_col = row.column(align=True)
        sub_col.prop(props, "show_left_door")
        sub_col.prop(props, "show_right_door")

    col.prop(props, "show_back_panel")
    col.prop(props, "show_left_panel")
    col.prop(props, "show_right_panel")
    col.prop(props, "show_floor")
    col.prop(props, "show_roof")

class OBJECT_PT_shipping_container(bpy.types.Panel):
    bl_label = "Shipping Container"
    bl_idname = "OBJECT_PT_shipping_container"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Container' # This is the tab name on the right side of the 3D viewport

    def draw(self, context):
        draw_container_controls(self.layout, context.active_object)

class OBJECT_PT_shipping_container_properties(bpy.types.Panel):
    bl_label = "Shipping Container"
    bl_idname = "OBJECT_PT_shipping_container_properties"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = 'object'

    bl_order = 1 # Ensure this panel appears near the top of the Object properties

    def draw(self, context):
        draw_container_controls(self.layout, context.object)

# --- This function adds it to the Shift+A > Mesh menu ---
def menu_func(self, context):
    self.layout.operator("object.create_shipping_container", text="Shipping Container", icon='MESH_CUBE')

def register():
    bpy.utils.register_class(OBJECT_PT_shipping_container)
    bpy.utils.register_class(OBJECT_PT_shipping_container_properties)
    # Append to the Add > Mesh menu
    bpy.types.VIEW3D_MT_mesh_add.append(menu_func)

def unregister():
    bpy.utils.unregister_class(OBJECT_PT_shipping_container_properties)
    bpy.utils.unregister_class(OBJECT_PT_shipping_container)
    # Remove from the Add > Mesh menu
    bpy.types.VIEW3D_MT_mesh_add.remove(menu_func)
