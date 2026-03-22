import bpy
from .utils import find_container_root


def draw_container_controls(layout, obj):
    """Draw shared UI controls for both the N-panel and the Properties editor panel."""
    root = find_container_root(obj)

    if not root:
        layout.operator("object.create_shipping_container",
                        text="Create Container", icon='MESH_CUBE')
        return

    if obj is not root:
        layout.label(text=f"Editing Root: {root.name}")

    props = root.shipping_container

    # ── Main properties ────────────────────────────────────────────────────────
    layout.prop(props, "container_size")
    layout.prop(props, "detail_level")
    layout.prop(props, "door_open_angle")
    layout.prop(props, "door_corrugations")

    layout.separator()

    # ── Bake ──────────────────────────────────────────────────────────────────
    layout.operator("object.bake_container_to_single_mesh",
                    text="Bake to Single Object", icon='MESH_DATA')
    
    layout.separator()

    # ── Parts visibility toggles ───────────────────────────────────────────────
    parts_box = layout.box()
    header = parts_box.row(align=True)
    header.prop(props, "ui_parts_expanded",
                icon='TRIA_DOWN' if props.ui_parts_expanded else 'TRIA_RIGHT',
                icon_only=True, emboss=False)
    header.label(text="Parts Toggles:", icon='RESTRICT_VIEW_OFF')

    if props.ui_parts_expanded:
        col = parts_box.column(align=True)
        col.prop(props, "show_front_panel")

        if props.show_front_panel:
            row = col.row()
            row.separator(factor=2.0)
            sub = row.column(align=True)
            sub.prop(props, "show_left_door")
            sub.prop(props, "show_right_door")

        col.prop(props, "show_back_panel")
        col.prop(props, "show_left_panel")
        col.prop(props, "show_right_panel")
        col.prop(props, "show_floor")
        col.prop(props, "show_roof")

    layout.separator()

    # ── Shader controls (collapsible) ─────────────────────────────────────────
    shader_box = layout.box()
    header = shader_box.row(align=True)
    header.prop(props, "ui_shader_expanded",
                icon='TRIA_DOWN' if props.ui_shader_expanded else 'TRIA_RIGHT',
                icon_only=True, emboss=False)
    header.label(text="Shader", icon='MATERIAL')

    if props.ui_shader_expanded:
        col = shader_box.column(align=True)
        col.prop(props, "shader_rust_strength",       slider=True)
        col.prop(props, "shader_stain_intensity",     slider=True)
        col.prop(props, "shader_dust_intensity",      slider=True)
        col.prop(props, "shader_scratch_intensity",   slider=True)
        shader_box.separator()
        col2 = shader_box.column(align=True)
        col2.prop(props, "shader_color_override_amount", slider=True)
        col2.prop(props, "shader_color_override")

    layout.separator()

    # ── Stack Creator ──────────────────────────────────────────────────────────
    stack_box = layout.box()
    header = stack_box.row(align=True)
    header.prop(props, "ui_stack_expanded",
                icon='TRIA_DOWN' if props.ui_stack_expanded else 'TRIA_RIGHT',
                icon_only=True, emboss=False)
    header.label(text="Stack Creator:", icon='MOD_ARRAY')

    if props.ui_stack_expanded:
        dim_col = stack_box.column(align=True)
        dim_col.prop(props, "stack_width",  text="Width  (X)")
        dim_col.prop(props, "stack_depth",  text="Depth  (Y)")
        dim_col.prop(props, "stack_height", text="Height (Z)")

        stack_box.separator()

        orient_col = stack_box.column(align=True)
        orient_col.prop(props, "stack_random_orient")
        orient_col.prop(props, "stack_seed")

        stack_box.separator()

        total = props.stack_width * props.stack_depth * props.stack_height
        stack_box.label(text=f"Total slots: {total}", icon='INFO')
        stack_box.operator("object.create_container_stack",
                        text="Create Stack", icon='OUTLINER_COLLECTION')


# ── 3-D Viewport N-panel ──────────────────────────────────────────────────────

class OBJECT_PT_shipping_container(bpy.types.Panel):
    bl_label       = "Shipping Container"
    bl_idname      = "OBJECT_PT_shipping_container"
    bl_space_type  = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category    = 'Container'

    def draw(self, context):
        draw_container_controls(self.layout, context.active_object)


# ── Object Properties editor panel ───────────────────────────────────────────

class OBJECT_PT_shipping_container_properties(bpy.types.Panel):
    bl_label       = "Shipping Container"
    bl_idname      = "OBJECT_PT_shipping_container_properties"
    bl_space_type  = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context     = 'object'
    bl_order       = 1

    def draw(self, context):
        draw_container_controls(self.layout, context.object)


# ── Add > Mesh menu entry ─────────────────────────────────────────────────────

def menu_func(self, context):
    self.layout.operator("object.create_shipping_container",
                         text="Shipping Container", icon='MESH_CUBE')


def register():
    bpy.utils.register_class(OBJECT_PT_shipping_container)
    bpy.utils.register_class(OBJECT_PT_shipping_container_properties)
    bpy.types.VIEW3D_MT_mesh_add.append(menu_func)


def unregister():
    bpy.types.VIEW3D_MT_mesh_add.remove(menu_func)
    bpy.utils.unregister_class(OBJECT_PT_shipping_container_properties)
    bpy.utils.unregister_class(OBJECT_PT_shipping_container)
