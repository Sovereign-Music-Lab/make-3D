"""Unreal-side (run with ue_python.py): set strand width/taper + physics on an existing groom
and create its binding to a skeletal mesh. Never overwrites an existing binding.

    python3 ue_python.py ue_groom_setup.py <groom_path> <skeletal_mesh_path> [width_cm=0.012] [simulate=0]

simulate=1 switches hair physics on. UE 5.8.4 + Interchange-imported grooms: turning it on from
Python and saving crashes the editor (thumbnail -> AllocateInterpolationResources assert, no
interpolation data built). Leave it 0 and enable physics in the Groom editor UI instead.
"""
import sys

import unreal

a = sys.argv[1:]
groom_path, mesh_path = a[:2]
width = float(a[2]) if len(a) > 2 else 0.012
simulate = len(a) > 3 and a[3] == '1'
eal = unreal.EditorAssetLibrary
groom = unreal.load_asset(groom_path)
if not isinstance(groom, unreal.GroomAsset):
    raise RuntimeError(f'{groom_path} is not a GroomAsset')
render = list(groom.get_editor_property('hair_groups_rendering'))
for g in render:
    geo = g.get_editor_property('geometry_settings')
    geo.set_editor_property('hair_width', width)
    geo.set_editor_property('hair_root_scale', 1.0)
    geo.set_editor_property('hair_tip_scale', 0.2)
    g.set_editor_property('geometry_settings', geo)
groom.set_editor_property('hair_groups_rendering', render)
phys = list(groom.get_editor_property('hair_groups_physics'))
for g in phys:
    sol = g.get_editor_property('solver_settings')
    sol.set_editor_property('enable_simulation', simulate)
    g.set_editor_property('solver_settings', sol)
groom.set_editor_property('hair_groups_physics', phys)
eal.save_loaded_asset(groom)
print('groom settings saved', width)

folder, name = groom_path.rsplit('/', 1)
bpath = f'{folder}/GB_{name}'
if eal.does_asset_exist(bpath):
    print('binding exists (kept)', bpath)
else:
    mesh = unreal.load_asset(mesh_path)
    binding = unreal.GroomLibrary.create_new_groom_binding_asset_with_path(bpath, groom, mesh, 30, None, 0)
    print('binding', binding.get_path_name() if binding else None)
    if binding:
        eal.save_loaded_asset(binding)
