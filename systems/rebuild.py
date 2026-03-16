import bpy
import math
import random
from ..utils import CONTAINER_SIZES, clear_container_children, remove_object_and_orphan_data
from ..geometry.panels import create_plane
from ..geometry.frame import create_box
from ..geometry.corrugation import create_corrugated_panel
from ..geometry.doors import create_door_component
from ..geometry.castings import create_corner_casting_instance
from ..geometry.roof import create_roof_bows
from ..geometry.floor import create_floor_cross_members, create_wooden_floor, create_forklift_pocket_cutters, create_forklift_pocket_tubes
from ..geometry.decals import generate_container_id, create_text_decal
from ..geometry.proxy import create_proxy_box
from .materials import get_or_create_container_material, get_or_create_wood_material, get_or_create_decal_material, get_or_create_proxy_material

def _get_collection_for_root(root_obj, context=None):
    if root_obj.users_collection:
        return root_obj.users_collection[0]
    if context is not None:
        if getattr(context, "collection", None) is not None:
            return context.collection
        if getattr(context, "scene", None) is not None:
            return context.scene.collection
    return bpy.context.scene.collection

def _get_depsgraph(context=None):
    if context is not None and hasattr(context, "evaluated_depsgraph_get"):
        return context.evaluated_depsgraph_get()
    return bpy.context.evaluated_depsgraph_get()

def update_door_pivots(root_obj):
    """Update door pivot rotations in-place for fast animation updates.

    Returns True if the update succeeded or wasn't needed, False if a rebuild is recommended.
    """
    if not root_obj or not hasattr(root_obj, "shipping_container"):
        return False
    if not root_obj.shipping_container.is_container:
        return False

    props = root_obj.shipping_container
    if props.detail_level == 'LOW':
        return True
    if not props.show_front_panel:
        return True

    angle = props.door_open_angle
    updated_any = False

    for child in root_obj.children:
        if child.type != 'EMPTY':
            continue
        if child.name.startswith("Left_Door_Pivot"):
            child.rotation_euler = (0.0, 0.0, -angle)
            updated_any = True
        elif child.name.startswith("Right_Door_Pivot"):
            child.rotation_euler = (0.0, 0.0, angle)
            updated_any = True

    # If pivots are expected but missing (e.g., user deleted them), fall back to rebuild.
    if (props.show_left_door or props.show_right_door) and not updated_any:
        return False
    return True

def rebuild_container(root_obj, context=None):
    """Rebuilds the container geometry based on current properties."""
    if not root_obj or not root_obj.shipping_container.is_container:
        return
        
    # Generate a random seed for this specific container if it doesn't have one
    if "container_seed" not in root_obj:
        # Keep strictly > 0.0 so shader fallbacks can reliably detect presence.
        root_obj["container_seed"] = (random.random() * 0.999) + 0.001
    container_seed = float(root_obj["container_seed"])
    if container_seed <= 0.0:
        container_seed = 0.001
        root_obj["container_seed"] = container_seed
    
    # Generate the unique ID for this container
    container_id = generate_container_id(container_seed)
        
    props = root_obj.shipping_container
    size_data = CONTAINER_SIZES[props.container_size]
    
    L = size_data['length']
    W = size_data['width']
    H = size_data['height']
    
    clear_container_children(root_obj)
    col = _get_collection_for_root(root_obj, context=context)
    
    # --- LOD CHECK: IF LOW, SPAWN PROXY AND EXIT ---
    if props.detail_level == 'LOW':
        proxy = create_proxy_box("Container_Proxy", W, L, H)
        col.objects.link(proxy)
        proxy.parent = root_obj
        
        proxy_mat = get_or_create_proxy_material()
        proxy["container_seed"] = container_seed
        if proxy.data.materials:
            proxy.data.materials[0] = proxy_mat
        else:
            proxy.data.materials.append(proxy_mat)
        return
    
    # Frame profile dimensions (35% smaller than 0.15m)
    pw = 0.0975 
    rh = 0.0975 
    
    # ISO 1161 Casting Dimensions
    cw = 0.162 
    cl = 0.178 
    ch = 0.118 
    
    # Casting Centers (Offsets from absolute corners)
    cx = cw / 2
    cy = cl / 2
    cz = ch / 2
    
    # --- Generate Corner Castings ---
    castings = [
        ("Casting_BLF", (0, 0, 0), False, True, True),
        ("Casting_BRF", (W, 0, 0), False, True, False),
        ("Casting_BLB", (0, L, 0), False, False, True),
        ("Casting_BRB", (W, L, 0), False, False, False),
        ("Casting_TLF", (0, 0, H), True, True, True),
        ("Casting_TRF", (W, 0, H), True, True, False),
        ("Casting_TLB", (0, L, H), True, False, True),
        ("Casting_TRB", (W, L, H), True, False, False),
    ]
    
    for name, loc, is_top, is_front, is_left in castings:
        casting = create_corner_casting_instance(name, loc, is_top, is_front, is_left, context=context)
        col.objects.link(casting)
        casting.parent = root_obj

    # --- Generate Frame (Aligned to Casting Centers) ---
    post_h = H - (2 * ch)
    posts = [
        ("Front_Left_Post",  (cx, cy, H/2)),
        ("Front_Right_Post", (W - cx, cy, H/2)),
        ("Back_Left_Post",   (cx, L - cy, H/2)),
        ("Back_Right_Post",  (W - cx, L - cy, H/2)),
    ]
    for name, loc in posts:
        post = create_box(name, pw, pw, post_h, loc)
        col.objects.link(post)
        post.parent = root_obj

    fb_rail_len = W - (2 * cw)
    fb_rails = [
        ("Front_Bottom_Rail", (W/2, cy, cz)),
        ("Front_Top_Rail",    (W/2, cy, H - cz)),
        ("Back_Bottom_Rail",  (W/2, L - cy, cz)),
        ("Back_Top_Rail",     (W/2, L - cy, H - cz)),
    ]
    for name, loc in fb_rails:
        rail = create_box(name, fb_rail_len, pw, rh, loc)
        col.objects.link(rail)
        rail.parent = root_obj

    side_rail_len = L - (2 * cl)
    side_rails = [
        ("Left_Bottom_Rail",  (cx, L/2, cz)),
        ("Left_Top_Rail",     (cx, L/2, H - cz)),
        ("Right_Bottom_Rail", (W - cx, L/2, cz)),
        ("Right_Top_Rail",    (W - cx, L/2, H - cz)),
    ]
    
    # Create cutters for forklift pockets (only for bottom rails)
    pocket_cutters = create_forklift_pocket_cutters("Pocket_Cutters", W)
    col.objects.link(pocket_cutters)
    
    for name, loc in side_rails:
        rail = create_box(name, pw, side_rail_len, rh, loc)
        col.objects.link(rail)
        rail.parent = root_obj
        
        # Apply boolean cut to bottom rails for forklift pockets
        if "Bottom" in name:
            mod = rail.modifiers.new(name="Forklift_Hole", type='BOOLEAN')
            mod.object = pocket_cutters
            mod.operation = 'DIFFERENCE'
            mod.solver = 'FLOAT'
            
            # Apply modifier immediately for performance
            depsgraph = _get_depsgraph(context=context)
            eval_obj = rail.evaluated_get(depsgraph)
            new_mesh = bpy.data.meshes.new_from_object(eval_obj)
            
            old_mesh = rail.data
            rail.data = new_mesh
            bpy.data.meshes.remove(old_mesh)
            rail.modifiers.clear()
            
    # Remove the cutter object after applying
    remove_object_and_orphan_data(pocket_cutters)

    # --- Generate Panels & Doors ---
    panel_w = W - (2 * cx) - pw
    panel_l = L - (2 * cy) - pw
    panel_h = H - (2 * cz) - rh
    
    if props.show_front_panel:
        door_w = panel_w / 2
        door_h = panel_h
        
        if props.show_left_door:
            left_pivot = bpy.data.objects.new("Left_Door_Pivot", None)
            left_pivot.empty_display_type = 'ARROWS'
            left_pivot.empty_display_size = 0.3
            left_pivot.location = (cx + pw/2, cy, cz + rh/2)
            left_pivot.rotation_euler = (0, 0, -props.door_open_angle)
            col.objects.link(left_pivot)
            left_pivot.parent = root_obj
            left_pivot["is_container_part"] = True
            
            for comp in ['PANEL', 'BARS', 'HINGES', 'HANDLES']:
                obj = create_door_component(f"Left_{comp.capitalize()}", comp, door_w, door_h, True)
                col.objects.link(obj)
                obj.parent = left_pivot
                
        if props.show_right_door:
            right_pivot = bpy.data.objects.new("Right_Door_Pivot", None)
            right_pivot.empty_display_type = 'ARROWS'
            right_pivot.empty_display_size = 0.3
            right_pivot.location = (W - cx - pw/2, cy, cz + rh/2)
            right_pivot.rotation_euler = (0, 0, props.door_open_angle)
            col.objects.link(right_pivot)
            right_pivot.parent = root_obj
            right_pivot["is_container_part"] = True
            
            for comp in ['PANEL', 'BARS', 'HINGES', 'HANDLES']:
                obj = create_door_component(f"Right_{comp.capitalize()}", comp, door_w, door_h, False)
                col.objects.link(obj)
                obj.parent = right_pivot
                
            # --- ADD DECALS TO RIGHT DOOR ---
            # Container ID (Top Right)
            decal_id = create_text_decal("Decal_ID", container_id, size=0.12, align_x='RIGHT')
            decal_id.location = (-0.1, -0.05, door_h - 0.3)
            decal_id.rotation_euler = (math.radians(90), 0, 0)
            col.objects.link(decal_id)
            decal_id.parent = right_pivot
            
            # Weight Specs (Middle Left)
            specs_text = "MAX GROSS  30,480 KG\nTARE       2,200 KG\nNET        28,280 KG\nCU. CAP.   33.2 CU.M"
            decal_specs = create_text_decal("Decal_Specs", specs_text, size=0.06, align_x='LEFT')
            decal_specs.location = (-door_w + 0.1, -0.05, door_h / 2)
            decal_specs.rotation_euler = (math.radians(90), 0, 0)
            col.objects.link(decal_specs)
            decal_specs.parent = right_pivot

    if props.show_back_panel:
        back = create_corrugated_panel("Back_Assembly", panel_w, panel_h, (W/2, L - cy, H/2), (math.radians(90), 0, math.radians(180)))
        col.objects.link(back)
        back.parent = root_obj
        
    if props.show_left_panel:
        left = create_corrugated_panel("Left_Side_Assembly", panel_l, panel_h, (cx, L/2, H/2), (math.radians(90), 0, math.radians(-90)))
        col.objects.link(left)
        left.parent = root_obj
        
    if props.show_right_panel:
        right = create_corrugated_panel("Right_Side_Assembly", panel_l, panel_h, (W - cx, L/2, H/2), (math.radians(90), 0, math.radians(90)))
        col.objects.link(right)
        right.parent = root_obj
        
    if props.show_floor:
        # Group floor components under an Empty
        floor_assembly = bpy.data.objects.new("Floor_Assembly", None)
        floor_assembly.empty_display_type = 'PLAIN_AXES'
        floor_assembly.empty_display_size = 0.5
        
        # Position the floor assembly near the bottom rails
        floor_z = cz + rh/2
        floor_assembly.location = (W/2, L/2, floor_z)
        col.objects.link(floor_assembly)
        floor_assembly.parent = root_obj
        floor_assembly["is_container_part"] = True
        
        # 1. Floor Cross Members (Steel beams)
        cross_members = create_floor_cross_members("Floor_Cross_Members", panel_w, panel_l)
        # Offset downward so they sit perfectly flush with the bottom of the side rails
        cross_members.location = (0, 0, -rh/2) 
        col.objects.link(cross_members)
        cross_members.parent = floor_assembly
        
        # 2. Wooden Floor (Marine Plywood)
        wood_floor = create_wooden_floor("Wooden_Floor", panel_w, panel_l)
        # Offset upward so it sits perfectly on top of the cross members
        wood_floor.location = (0, 0, 0.014) 
        col.objects.link(wood_floor)
        wood_floor.parent = floor_assembly
        
        # 3. Forklift Pocket Tubes
        pocket_tubes = create_forklift_pocket_tubes("Forklift_Pockets", panel_w)
        pocket_tubes.location = (0, 0, -rh/2)
        col.objects.link(pocket_tubes)
        pocket_tubes.parent = floor_assembly
        
    if props.show_roof:
        # Group roof components under an Empty
        roof_assembly = bpy.data.objects.new("Roof_Assembly", None)
        roof_assembly.empty_display_type = 'PLAIN_AXES'
        roof_assembly.empty_display_size = 0.5
        
        # Position the roof assembly at the top of the frame
        roof_z = H - cz - rh/2
        roof_assembly.location = (W/2, L/2, roof_z)
        col.objects.link(roof_assembly)
        roof_assembly.parent = root_obj
        roof_assembly["is_container_part"] = True
        
        # 1. Corrugated Roof Panel
        # Roof corrugation is a different spec than side wall corrugation; keep the legacy profile for now.
        roof_panel = create_corrugated_panel(
            "Roof_Panel",
            panel_l,
            panel_w,
            (0, 0, 0),
            (0, 0, math.radians(90)),
            profile="LEGACY",
        )
        col.objects.link(roof_panel)
        roof_panel.parent = roof_assembly
        
        # 2. Roof Bows
        bows = create_roof_bows("Roof_Bows", panel_w, panel_l)
        bows.location = (0, 0, -0.024) # Offset downward by the depth of the corrugation
        col.objects.link(bows)
        bows.parent = roof_assembly

    # --- Apply Materials ---
    metal_mat = get_or_create_container_material()
    wood_mat = get_or_create_wood_material()
    decal_mat = get_or_create_decal_material()
    
    for obj in root_obj.children_recursive:
        if obj.type == 'MESH':
            # Assign the seed to the object so the Attribute node can read it
            obj["container_seed"] = container_seed
            
            # Assign material
            mat_to_assign = wood_mat if "Wood" in obj.name else metal_mat
            if obj.data.materials:
                obj.data.materials[0] = mat_to_assign
            else:
                obj.data.materials.append(mat_to_assign)
                
        elif obj.type == 'FONT':
            if obj.data.materials:
                obj.data.materials[0] = decal_mat
            else:
                obj.data.materials.append(decal_mat)
