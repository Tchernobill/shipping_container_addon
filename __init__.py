bl_info = {
    "name": "Procedural ISO Shipping Container",
    "author": "Yan + AI",
    "version": (1, 10, 0),
    "blender": (5, 1, 0),
    "location": "View3D > Add > Mesh",
    "description": "Generates procedural ISO standards compliant shipping containers",
    "category": "Add Mesh",
}

import bpy  # noqa: E402
import importlib  # noqa: E402

# Detect Blender "live reload" (the module globals persist between runs).
_IS_RELOAD = "utils" in globals()

from . import utils  # noqa: E402
from . import properties  # noqa: E402
from . import ui  # noqa: E402
from . import operators  # noqa: E402

# Imported for dev reload convenience (called by rebuild/material systems).
from .geometry import panels  # noqa: E402
from .geometry import frame  # noqa: E402
from .geometry import corrugation  # noqa: E402
from .geometry import doors  # noqa: E402
from .geometry import castings  # noqa: E402
from .geometry import roof  # noqa: E402
from .geometry import floor  # noqa: E402
from .geometry import decals  # noqa: E402
from .geometry import proxy  # noqa: E402

from .systems import materials  # noqa: E402
from .systems import rebuild  # noqa: E402

_RELOAD_ORDER = [
    # Core utils first.
    utils,
    # Geometry builders.
    panels,
    frame,
    corrugation,
    doors,
    castings,
    roof,
    floor,
    decals,
    proxy,
    # Systems (depend on geometry + utils).
    materials,
    rebuild,
    # UI-facing modules.
    properties,
    operators,
    ui,
]

if _IS_RELOAD:
    for reload_module in _RELOAD_ORDER:
        importlib.reload(reload_module)

modules = [
    properties,
    operators,
    ui,
]

def register():
    for addon_module in modules:
        if hasattr(addon_module, "register"):
            addon_module.register()

def unregister():
    for addon_module in reversed(modules):
        if hasattr(addon_module, "unregister"):
            addon_module.unregister()
    # Clean up the cached casting mesh
    if "ISO_Casting_Master_Mesh" in bpy.data.meshes:
        m = bpy.data.meshes["ISO_Casting_Master_Mesh"]
        m.use_fake_user = False
        bpy.data.meshes.remove(m)

if __name__ == "__main__":
    register()
