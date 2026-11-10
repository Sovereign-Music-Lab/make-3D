"""Unreal-side (run with ue_python.py): add a GroomComponent under a character's
SkeletalMeshComponent, set groom + binding (+ optional material) and save the level.
Use this when the MCP add_component call hangs (seen right after a level load in UE 5.8.4).

    python3 ue_python.py ue_attach_groom_py.py <actor_label_or_name> <groom_path> <binding_path> [material_path] [comp_name=Groom]
"""
import sys

import unreal

a = sys.argv[1:]
actor_name, groom_path, binding_path = a[:3]
mat_path = a[3] if len(a) > 3 and a[3] != '-' else None
comp_name = a[4] if len(a) > 4 else 'Groom'
actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors()
actor = next(x for x in actors if actor_name in (x.get_name(), x.get_actor_label()))
if any(isinstance(c, unreal.GroomComponent) for c in actor.get_components_by_class(unreal.GroomComponent)):
    raise RuntimeError('actor already has a GroomComponent (nothing changed)')
sds = unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem)
handles = sds.k2_gather_subobject_data_for_instance(actor)
bfl = unreal.SubobjectDataBlueprintFunctionLibrary
skel = next(h for h in handles if isinstance(bfl.get_object(bfl.get_data(h)), unreal.SkeletalMeshComponent))
params = unreal.AddNewSubobjectParams(parent_handle=skel, new_class=unreal.GroomComponent)
new, fail = sds.add_new_subobject(params)
if not fail.is_empty():
    raise RuntimeError(str(fail))
sds.rename_subobject(new, unreal.Text(comp_name))
comp = bfl.get_object(bfl.get_data(new))
comp.set_editor_property('binding_asset', unreal.load_asset(binding_path))
comp.set_groom_asset(unreal.load_asset(groom_path))
if mat_path:
    comp.set_material(0, unreal.load_asset(mat_path))
print('attached', comp.get_path_name(), 'parent', comp.get_attach_parent().get_name())
unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_current_level()
print('level saved')
