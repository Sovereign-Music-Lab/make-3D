"""Import a rigged FBX into the open Unreal editor, stand it on the floor at a real height,
and loop its animation. Uses only the editor's MCP server (no Unreal Python needed).

    python3 ue_import_character.py --fbx /abs/char.fbx --folder /Game/Characters/Hero \
        --name SK_Hero --height-cm 170 --at 0 0 --floor-z 0 [--level /Game/Maps/MyLevel] [--no-anim]

* Creates SkeletalMesh, Skeleton, AnimSequence, materials and textures in --folder.
* Spawns an actor in the CURRENT level (or loads --level first) and saves the level.
* Never overwrites: refuses if --folder/--name already exists.
"""
import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from ue_mcp import T, call, get_props, ref, set_props  # noqa: E402


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--fbx', required=True)
    p.add_argument('--folder', required=True)
    p.add_argument('--name', required=True)
    p.add_argument('--height-cm', type=float, required=True, help='target standing height')
    p.add_argument('--at', type=float, nargs=2, default=(0, 0), metavar=('X', 'Y'))
    p.add_argument('--floor-z', type=float, default=0.0)
    p.add_argument('--yaw', type=float, default=0.0)
    p.add_argument('--level', help='load this level first (must be saved)')
    p.add_argument('--no-anim', action='store_true')
    a = p.parse_args()

    mesh_path = f'{a.folder}/{a.name}'
    if call(T.ASSET, 'exists', {'path': mesh_path}):
        sys.exit(f'{mesh_path} already exists; pick a new --name or folder (nothing overwritten)')
    if a.level:
        call(T.SCENE, 'load_level', {'level_path': a.level})
    level = call(T.SCENE, 'get_current_level', {})

    call(T.ASSET, 'create_folder', {'path': a.folder})
    mesh = call(T.SKELETAL_MESH, 'import_file', {
        'folder_path': a.folder, 'asset_name': a.name, 'source_file': os.path.abspath(a.fbx),
        'skeleton': None, 'import_materials': True, 'import_textures': True,
        'import_animations': not a.no_anim, 'create_physics_asset': False})[0]
    b = call(T.SKELETAL_MESH, 'get_bounds', {'mesh': mesh})
    half_h = b['boxExtent']['z']
    bottom = b['origin']['z'] - half_h
    scale = a.height_cm / (2 * half_h)
    z = a.floor_z - bottom * scale
    print(f'imported {mesh["refPath"]}: {2 * half_h:.2f} cm tall -> scale {scale:.4f}')

    actor = call(T.SCENE, 'add_to_scene_from_asset', {
        'asset_path': mesh_path, 'name': a.name,
        'xform': {'location': {'x': a.at[0], 'y': a.at[1], 'z': z},
                  'rotation': {'pitch': 0, 'yaw': a.yaw, 'roll': 0},
                  'scale': {'x': scale, 'y': scale, 'z': scale}},
        'parent': None, 'snap_to_ground': False})
    # Save EVERYTHING the import created (materials and textures too). Saving only the mesh
    # leaves the auto-created materials/textures in memory; if the editor closes they are
    # lost and the character comes back grey.
    saved = [level] + list(call(T.ASSET, 'find_assets', {
        'folder_path': a.folder, 'name': '', 'asset_type': None, 'recursive': True, 'tags': None}) or [])
    anim_path = f'{mesh_path}_Anim'
    if not a.no_anim and call(T.ASSET, 'exists', {'path': anim_path}):
        comp = {'refPath': actor['refPath'] + '.SkeletalMeshComponent0'}
        set_props(comp, {'AnimationMode': 'AnimationSingleNode', 'AnimationData': {
            'animToPlay': ref(anim_path), 'bSavedLooping': True, 'bSavedPlaying': True,
            'savedPosition': 0, 'savedPlayRate': 1}})
        print('animation', get_props(comp, ['AnimationMode']))
    print('saved', call(T.ASSET, 'save_assets', {'asset_paths': saved}))
    print(json.dumps({'actor': actor, 'level': level, 'scale': scale}, indent=2))


if __name__ == '__main__':
    main()
