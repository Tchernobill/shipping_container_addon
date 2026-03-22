bl_info = {
    "name": "Procedural ISO Shipping Container",
    "author": "AI Engineer",
    "version": (1, 10, 0),
    "blender": (5, 0, 0),
    "location": "View3D > Add > Mesh",
    "description": "Generates procedural ISO-668 compliant shipping containers",
    "category": "Add Mesh",
}

import bpy
import importlib

if "utils" in locals():
    # Reload submodules in a dependency-friendly order.
    importlib.reload(utils)

    importlib.reload(panels)
    importlib.reload(frame)
    importlib.reload(corrugation)
    importlib.reload(doors)
    importlib.reload(castings)
    importlib.reload(roof)
    importlib.reload(floor)
    importlib.reload(decals)
    importlib.reload(proxy)

    importlib.reload(materials)
    importlib.reload(rebuild)

    importlib.reload(properties)
    importlib.reload(operators)
    importlib.reload(ui)
else:
    from . import utils
    from . import properties
    from . import ui
    from . import operators

    # Imported for dev reload convenience (called by rebuild/material systems).
    from .geometry import panels
    from .geometry import frame
    from .geometry import corrugation
    from .geometry import doors
    from .geometry import castings
    from .geometry import roof
    from .geometry import floor
    from .geometry import decals
    from .geometry import proxy

    from .systems import materials
    from .systems import rebuild

modules = [
    properties,
    operators,
    ui,
]

def register():
    for mod in modules:
        if hasattr(mod, "register"):
            mod.register()

def unregister():
    for mod in reversed(modules):
        if hasattr(mod, "unregister"):
            mod.unregister()
    # Clean up the cached casting mesh
    if "ISO_Casting_Master_Mesh" in bpy.data.meshes:
        m = bpy.data.meshes["ISO_Casting_Master_Mesh"]
        m.use_fake_user = False
        bpy.data.meshes.remove(m)

if __name__ == "__main__":
    register()
