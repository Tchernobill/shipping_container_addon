import bpy
import random
from .systems.rebuild import rebuild_container
from .utils import find_container_root

class MESH_OT_add_shipping_container(bpy.types.Operator):
    """Add a Procedural Shipping Container"""
    bl_idname = "object.create_shipping_container"
    bl_label = "Shipping Container"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        if context.mode != 'OBJECT':
            try:
                bpy.ops.object.mode_set(mode='OBJECT')
            except RuntimeError:
                pass

        root_empty = bpy.data.objects.new("ISO_Container_Root", None)
        root_empty.empty_display_type = 'CUBE'
        root_empty.empty_display_size = 0.1

        (context.collection or context.scene.collection).objects.link(root_empty)
        root_empty.location = context.scene.cursor.location
        root_empty.shipping_container.is_container = True

        bpy.ops.object.select_all(action='DESELECT')
        root_empty.select_set(True)
        context.view_layer.objects.active = root_empty

        rebuild_container(root_empty, context=context)

        self.report({'INFO'}, "Shipping Container: Generated successfully.")
        return {'FINISHED'}


class OBJECT_OT_bake_container_to_single_mesh(bpy.types.Operator):
    """Bakes the procedural container into a single optimized mesh for Geometry Nodes/Export"""
    bl_idname = "object.bake_container_to_single_mesh"
    bl_label = "Bake Container to Single Mesh"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return bool(find_container_root(context.active_object))

    def execute(self, context):
        if context.mode != 'OBJECT':
            try:
                bpy.ops.object.mode_set(mode='OBJECT')
            except RuntimeError:
                pass

        root_obj = find_container_root(context.active_object)
        if not root_obj:
            self.report({'WARNING'}, "No Shipping Container root found for the active object.")
            return {'CANCELLED'}

        def get_visible_descendants(obj, result):
            """Collect all visible MESH and FONT children (recursive).

            FONT objects (text decals) are included so they get converted to
            mesh geometry and merged into the final bake, ensuring decals survive
            the bake operation.
            """
            for child in obj.children:
                if child.type in ('MESH', 'FONT') and child.visible_get():
                    result.append(child)
                get_visible_descendants(child, result)

        objects_to_bake = []
        get_visible_descendants(root_obj, objects_to_bake)

        if not objects_to_bake:
            self.report({'WARNING'}, "No visible meshes found inside the container!")
            return {'CANCELLED'}

        bpy.ops.object.select_all(action='DESELECT')
        for obj in objects_to_bake:
            obj.select_set(True)

        bpy.ops.object.duplicate(linked=False)
        baked_objects = list(context.selected_objects)

        if not baked_objects:
            self.report({'WARNING'}, "Duplication failed!")
            return {'CANCELLED'}

        context.view_layer.objects.active = baked_objects[0]

        # Convert converts FONT → MESH and applies modifiers on all selected objects.
        bpy.ops.object.convert(target='MESH')

        if len(baked_objects) > 1:
            bpy.ops.object.join()

        final_mesh = context.active_object
        size   = root_obj.shipping_container.container_size
        detail = root_obj.shipping_container.detail_level
        final_mesh.name = f"Baked_{size}_{detail}"

        # Assign a new unique seed so the baked object gets its own colour
        # variation in any seed-driven material (Principled BSDF via Object Info).
        final_mesh["container_seed"] = random.random() * 0.999 + 0.001

        old_matrix = final_mesh.matrix_world.copy()
        final_mesh.parent = None
        final_mesh.matrix_world = old_matrix

        collection_name = "GeoNodes_Assets"
        if collection_name not in bpy.data.collections:
            new_col = bpy.data.collections.new(collection_name)
            context.scene.collection.children.link(new_col)

        for col in list(final_mesh.users_collection):
            col.objects.unlink(final_mesh)
        bpy.data.collections[collection_name].objects.link(final_mesh)

        self.report({'INFO'}, f"Successfully baked to {final_mesh.name}!")
        return {'FINISHED'}


class OBJECT_OT_create_container_stack(bpy.types.Operator):
    """Creates an optimized baked container stack — only visible faces are kept per container"""
    bl_idname = "object.create_container_stack"
    bl_label  = "Create Container Stack"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return bool(find_container_root(context.active_object))

    def execute(self, context):
        if context.mode != 'OBJECT':
            try:
                bpy.ops.object.mode_set(mode='OBJECT')
            except RuntimeError:
                pass

        root_obj = find_container_root(context.active_object)
        if not root_obj:
            self.report({'WARNING'}, "No Shipping Container root found.")
            return {'CANCELLED'}

        from .systems.stack import create_container_stack

        stack_col, message = create_container_stack(root_obj, context)

        if stack_col is None:
            self.report({'WARNING'}, message)
            return {'CANCELLED'}

        self.report({'INFO'}, message)
        return {'FINISHED'}


CLASSES = (
    MESH_OT_add_shipping_container,
    OBJECT_OT_bake_container_to_single_mesh,
    OBJECT_OT_create_container_stack,
)

def register():
    for cls in CLASSES:
        bpy.utils.register_class(cls)

def unregister():
    for cls in reversed(CLASSES):
        bpy.utils.unregister_class(cls)
