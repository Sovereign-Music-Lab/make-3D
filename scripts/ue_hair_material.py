"""Unreal-side (run with ue_python.py): make a strand-hair material (Hair shading model,
Used with Hair Strands) with BaseColor/Roughness/Scatter parameters. Never overwrites.

    python3 ue_python.py ue_hair_material.py <folder> <name> [R G B linear=0.035 0.02 0.012]
"""
import sys

import unreal

a = sys.argv[1:]
folder, name = a[:2]
rgb = tuple(map(float, a[2:5])) if len(a) >= 5 else (0.035, 0.02, 0.012)
path = f'{folder}/{name}'
if unreal.EditorAssetLibrary.does_asset_exist(path):
    raise RuntimeError(f'{path} exists (nothing overwritten)')
mel = unreal.MaterialEditingLibrary
m = unreal.AssetToolsHelpers.get_asset_tools().create_asset(name, folder, unreal.Material, unreal.MaterialFactoryNew())
m.set_editor_property('shading_model', unreal.MaterialShadingModel.MSM_HAIR)
m.set_editor_property('used_with_hair_strands', True)


def param(cls, pname, value, prop, y):
    e = mel.create_material_expression(m, cls, -400, y)
    e.set_editor_property('parameter_name', pname)
    e.set_editor_property('default_value', value)
    mel.connect_material_property(e, '', prop)


param(unreal.MaterialExpressionVectorParameter, 'HairColor', unreal.LinearColor(*rgb, 1), unreal.MaterialProperty.MP_BASE_COLOR, 0)
param(unreal.MaterialExpressionScalarParameter, 'Roughness', 0.38, unreal.MaterialProperty.MP_ROUGHNESS, 200)
param(unreal.MaterialExpressionScalarParameter, 'Scatter', 0.25, unreal.MaterialProperty.MP_METALLIC, 300)  # Hair: Metallic pin = Scatter
param(unreal.MaterialExpressionScalarParameter, 'Specular', 0.5, unreal.MaterialProperty.MP_SPECULAR, 400)
mel.recompile_material(m)
unreal.EditorAssetLibrary.save_loaded_asset(m)
print('material', m.get_path_name())
