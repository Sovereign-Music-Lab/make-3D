"""Unreal-side script (run with ue_python.py): import an Alembic groom, set strand width,
create a binding to a skeletal mesh and switch hair physics on.

    python3 ue_python.py ue_import_groom.py <abc> <folder> <name> <skeletal_mesh_path> \
        [width_cm=0.012] [rot_x=90] [scale_y=-1]

* Never overwrites: refuses if <folder>/<name> exists.
* Conversion: Blender exports Alembic Y-up; rotation (rot_x,0,0) and scale (1,scale_y,1)
  bring it back to Unreal's Z-up, left-handed space (the same flip the FBX importer does).
* Hair simulation is switched on for every group. Attach it to a character with
  ue_attach_groom.py (MCP), which adds a GroomComponent under the SkeletalMeshComponent.
"""
import sys

import unreal

a = sys.argv[1:]
abc, folder, name, mesh_path = a[:4]
width = float(a[4]) if len(a) > 4 else 0.012
rot_x = float(a[5]) if len(a) > 5 else 90.0
scale_y = float(a[6]) if len(a) > 6 else -1.0
eal = unreal.EditorAssetLibrary
path = f'{folder}/{name}'
if eal.does_asset_exist(path):
    raise RuntimeError(f'{path} exists (nothing overwritten)')

opts = unreal.GroomImportOptions()
cv = opts.get_editor_property('conversion_settings')
cv.set_editor_property('rotation', unreal.Vector(rot_x, 0, 0))
cv.set_editor_property('scale', unreal.Vector(1, scale_y, 1))
opts.set_editor_property('conversion_settings', cv)
task = unreal.AssetImportTask()
task.filename = abc; task.destination_path = folder; task.destination_name = name
task.automated = True; task.save = True; task.replace_existing = False; task.options = opts
# UE 5.8: the legacy GroomFactory/HairStrandsFactory list no formats; Alembic grooms come in through
# Interchange (AlembicHairImporter plugin) once its ABC feature flag is on. Without it the plain
# Alembic (static mesh) importer takes the file.
unreal.SystemLibrary.execute_console_command(None, 'Interchange.FeatureFlags.Import.ABC 1')
unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])
groom = next((o for o in task.get_objects() if isinstance(o, unreal.GroomAsset)), None)
if not groom:
    raise RuntimeError('no groom imported: ' + str(list(task.imported_object_paths)))
print('groom', groom.get_path_name(), 'groups', len(groom.get_editor_property('hair_groups_info')))

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
    sol.set_editor_property('enable_simulation', True)
    g.set_editor_property('solver_settings', sol)
groom.set_editor_property('hair_groups_physics', phys)
eal.save_loaded_asset(groom)

mesh = unreal.load_asset(mesh_path)
binding = unreal.GroomLibrary.create_new_groom_binding_asset_with_path(f'{folder}/GB_{name}', groom, mesh, 30, None, 0)
print('binding', binding.get_path_name() if binding else None)
if binding:
    eal.save_loaded_asset(binding)
