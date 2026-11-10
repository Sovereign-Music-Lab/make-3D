"""Attach an imported groom (+ binding) to a character actor through MCP.

    python3 ue_attach_groom.py --actor "<actor refPath>" --groom /Game/Hair/Groom_X \
        [--binding /Game/Hair/GB_Groom_X] [--material /Game/Hair/M_Hair] [--name Groom_X]

Adds a GroomComponent under the actor's SkeletalMeshComponent (so it follows the animation)
and saves the level.
"""
import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from ue_mcp import T, call, get_props, ref, set_props  # noqa: E402


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--actor', required=True)
    p.add_argument('--groom', required=True)
    p.add_argument('--binding')
    p.add_argument('--material')
    p.add_argument('--name', default='Groom')
    a = p.parse_args()
    skc = {'refPath': a.actor + '.SkeletalMeshComponent0'}
    comp = call(T.ACTOR, 'add_component', {'owner': skc, 'component_type': {'refPath': '/Script/HairStrandsCore.GroomComponent'},
                                           'name': a.name})
    vals = {'GroomAsset': ref(a.groom)}
    if a.binding:
        vals['BindingAsset'] = ref(a.binding)
    if a.material:
        vals['OverrideMaterials'] = [ref(a.material)]
    set_props(comp, vals)
    print('component', comp['refPath'], get_props(comp, ['GroomAsset', 'BindingAsset']))
    level = call(T.SCENE, 'get_current_level', {})
    print('saved', call(T.ASSET, 'save_assets', {'asset_paths': [level]}))


if __name__ == '__main__':
    main()
