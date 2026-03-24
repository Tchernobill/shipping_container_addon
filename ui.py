import bpy
from .utils import find_container_root


# ─────────────────────────────────────────────────────────────────────────────
#  Helper
# ─────────────────────────────────────────────────────────────────────────────

def _section(layout, props, expanded_prop, label, icon='NONE'):
    """Draw a collapsible section header inside a box.

    Returns (box, is_open) — callers draw their content into *box* only
    when *is_open* is True.
    """
    box = layout.box()
    row = box.row(align=True)
    is_open = getattr(props, expanded_prop)
    row.prop(props, expanded_prop,
             icon='TRIA_DOWN' if is_open else 'TRIA_RIGHT',
             icon_only=True, emboss=False)
    row.label(text=label, icon=icon)
    return box, is_open


# ─────────────────────────────────────────────────────────────────────────────
#  Main draw function — shared by N-panel and Properties editor
# ─────────────────────────────────────────────────────────────────────────────

def draw_container_controls(layout, obj):
    root = find_container_root(obj)

    if not root:
        layout.operator("object.create_shipping_container",
                        text="Create Container", icon='MESH_CUBE')
        return

    if obj is not root:
        layout.label(text=f"Root: {root.name}", icon='EMPTY_ARROWS')

    props = root.shipping_container

    # ── Core properties ────────────────────────────────────────────────────────
    layout.prop(props, "container_size")
    layout.prop(props, "detail_level")
    layout.separator()
    layout.prop(props, "door_open_angle")
    layout.prop(props, "door_corrugations")
    layout.prop(props, "door_hinge_count")

    # ── Bake ──────────────────────────────────────────────────────────────────
    layout.separator()
    layout.operator("object.bake_container_to_single_mesh",
                    text="Bake to Single Mesh", icon='MESH_DATA')

    # ── Parts toggles (collapsible) ────────────────────────────────────────────
    layout.separator()
    box, open_ = _section(layout, props, "ui_parts_expanded",
                           "Parts", icon='RESTRICT_VIEW_OFF')
    if open_:
        col = box.column(align=True)
        col.prop(props, "show_front_panel")
        if props.show_front_panel:
            sub_row = col.row()
            sub_row.separator(factor=2.0)
            sub_col = sub_row.column(align=True)
            sub_col.prop(props, "show_left_door")
            sub_col.prop(props, "show_right_door")
        col.prop(props, "show_back_panel")
        col.prop(props, "show_left_panel")
        col.prop(props, "show_right_panel")
        col.prop(props, "show_floor")
        col.prop(props, "show_roof")

    # ── Shader (collapsible) ───────────────────────────────────────────────────
    layout.separator()
    box, open_ = _section(layout, props, "ui_shader_expanded",
                           "Shader", icon='MATERIAL')
    if open_:
        col = box.column(align=True)
        col.prop(props, "shader_rust_strength",     slider=True)
        col.prop(props, "shader_stain_intensity",   slider=True)
        col.prop(props, "shader_dust_intensity",    slider=True)
        col.prop(props, "shader_scratch_intensity", slider=True)
        box.separator()
        col2 = box.column(align=True)
        col2.prop(props, "shader_color_override_amount", slider=True)
        col2.prop(props, "shader_color_override")

    # ── Stack Creator (collapsible) ────────────────────────────────────────────
    layout.separator()
    box, open_ = _section(layout, props, "ui_stack_expanded",
                           "Stack Creator", icon='MOD_ARRAY')
    if open_:
        col = box.column(align=True)
        col.prop(props, "stack_width",  text="Width  (X)")
        col.prop(props, "stack_depth",  text="Depth  (Y)")
        col.prop(props, "stack_height", text="Height (Z)")

        box.separator()

        col2 = box.column(align=True)
        col2.prop(props, "stack_random_orient")
        col2.prop(props, "stack_seed")

        box.separator()

        total = props.stack_width * props.stack_depth * props.stack_height
        box.label(text=f"Total slots: {total}", icon='INFO')
        box.operator("object.create_container_stack",
                     text="Create Stack", icon='OUTLINER_COLLECTION')


# ─────────────────────────────────────────────────────────────────────────────
#  Panels
# ─────────────────────────────────────────────────────────────────────────────

class OBJECT_PT_shipping_container(bpy.types.Panel):
    """Shipping Container — 3D Viewport N-panel (Container tab)."""
    bl_label       = "Shipping Container"
    bl_idname      = "OBJECT_PT_shipping_container"
    bl_space_type  = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category    = 'Container'

    def draw(self, context):
        draw_container_controls(self.layout, context.active_object)


class OBJECT_PT_shipping_container_properties(bpy.types.Panel):
    """Shipping Container — Object Properties editor panel."""
    bl_label       = "Shipping Container"
    bl_idname      = "OBJECT_PT_shipping_container_properties"
    bl_space_type  = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context     = 'object'
    bl_order       = 1

    def draw(self, context):
        draw_container_controls(self.layout, context.object)


# ─────────────────────────────────────────────────────────────────────────────
#  Add menu
# ─────────────────────────────────────────────────────────────────────────────

def menu_func(self, _context):
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
