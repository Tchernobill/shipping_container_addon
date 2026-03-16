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
        # 20cm, assuming 1 Blender unit == 1 meter (default scene scale).
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
        # Allow baking from the root or any descendant object.
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
        
        # --- NEW: Recursive function to find ALL nested children ---
        def get_visible_mesh_descendants(obj, mesh_list):
            for child in obj.children:
                # Only grab it if it's a mesh AND it's currently visible (respects your UI toggles)
                if child.type == 'MESH' and child.visible_get():
                    mesh_list.append(child)
                # Dig deeper into this child's children
                get_visible_mesh_descendants(child, mesh_list)
                
        meshes_to_join = []
        get_visible_mesh_descendants(root_obj, meshes_to_join)
                
        if not meshes_to_join:
            self.report({'WARNING'}, "No visible meshes found inside the container!")
            return {'CANCELLED'}
            
        # 1. Deselect everything
        bpy.ops.object.select_all(action='DESELECT')
        
        # 2. Select all the meshes we found
        for mesh in meshes_to_join:
            mesh.select_set(True)
            
        # 3. Duplicate the selected meshes so we don't destroy the procedural original
        bpy.ops.object.duplicate(linked=False)
        
        # The duplicated objects are now selected. Let's grab them.
        baked_meshes = context.selected_objects
        
        if not baked_meshes:
            self.report({'WARNING'}, "Duplication failed!")
            return {'CANCELLED'}
        
        # 4. Make the first duplicated mesh the active object
        context.view_layer.objects.active = baked_meshes[0]
        
        # 5. Convert to mesh (this applies all modifiers like Arrays, Mirrors, etc.)
        bpy.ops.object.convert(target='MESH')
        
        # 6. Join them all into a single object
        if len(baked_meshes) > 1:
            bpy.ops.object.join()
        
        # 7. Rename the final object and clear its parent
        final_mesh = context.active_object
        size = root_obj.shipping_container.container_size
        detail = root_obj.shipping_container.detail_level
        final_mesh.name = f"Baked_{size}_{detail}"
        
        # Clear parent but keep transformation
        old_matrix = final_mesh.matrix_world.copy()
        final_mesh.parent = None
        final_mesh.matrix_world = old_matrix
        
        # 8. Move it to a new collection for GeoNodes
        collection_name = "GeoNodes_Assets"
        if collection_name not in bpy.data.collections:
            new_col = bpy.data.collections.new(collection_name)
            context.scene.collection.children.link(new_col)
        
        # Unlink from current collections and link to the new one
        for col in list(final_mesh.users_collection):
            col.objects.unlink(final_mesh)
        bpy.data.collections[collection_name].objects.link(final_mesh)
        
        self.report({'INFO'}, f"Successfully baked to {final_mesh.name}!")
        return {'FINISHED'}

CLASSES = (
    MESH_OT_add_shipping_container,
    OBJECT_OT_bake_container_to_single_mesh,
)

def register():
    for cls in CLASSES:
        bpy.utils.register_class(cls)

def unregister():
    for cls in reversed(CLASSES):
        bpy.utils.unregister_class(cls)
