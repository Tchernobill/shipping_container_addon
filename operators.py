import bpy
from .systems.rebuild import rebuild_container
from .utils import find_container_root

class MESH_OT_add_shipping_container(bpy.types.Operator):
    """Add a Procedural Shipping Container"""
    bl_idname = "object.create_shipping_container"
    bl_label = "Shipping Container"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        # Ensure a predictable context for object creation/selection.
        if context.mode != 'OBJECT':
            try:
                bpy.ops.object.mode_set(mode='OBJECT')
            except RuntimeError:
                pass

        # Create the root EMPTY object
        root_empty = bpy.data.objects.new("ISO_Container_Root", None)
        root_empty.empty_display_type = 'CUBE'
        root_empty.empty_display_size = 0.2

        (context.collection or context.scene.collection).objects.link(root_empty)
        root_empty.location = context.scene.cursor.location
        root_empty.shipping_container.is_container = True

        # Select the new object and make it active
        bpy.ops.object.select_all(action='DESELECT')
        root_empty.select_set(True)
        context.view_layer.objects.active = root_empty

        # Trigger initial geometry generation
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

        def get_visible_mesh_descendants(obj, mesh_list):
            for child in obj.children:
                if child.type == 'MESH' and child.visible_get():
                    mesh_list.append(child)
                get_visible_mesh_descendants(child, mesh_list)

        meshes_to_join = []
        get_visible_mesh_descendants(root_obj, meshes_to_join)

        if not meshes_to_join:
            self.report({'WARNING'}, "No visible meshes found inside the container!")
            return {'CANCELLED'}

        bpy.ops.object.select_all(action='DESELECT')

        for mesh in meshes_to_join:
            mesh.select_set(True)

        bpy.ops.object.duplicate(linked=False)

        baked_meshes = context.selected_objects

        if not baked_meshes:
            self.report({'WARNING'}, "Duplication failed!")
            return {'CANCELLED'}

        context.view_layer.objects.active = baked_meshes[0]

        bpy.ops.object.convert(target='MESH')

        if len(baked_meshes) > 1:
            bpy.ops.object.join()

        final_mesh = context.active_object
        size = root_obj.shipping_container.container_size
        detail = root_obj.shipping_container.detail_level
        final_mesh.name = f"Baked_{size}_{detail}"

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

        # Lazy import keeps the module graph clean
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