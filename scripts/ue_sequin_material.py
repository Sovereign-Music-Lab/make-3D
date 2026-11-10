"""Build a sequin + sheer-sleeve dress material in the open Unreal editor through MCP.

    python3 ue_sequin_material.py --folder /Game/Characters/Hero/Materials --name M_Sequin \
        [--sleeve-start 17 --sleeve-end 20] [--assign-actor <actor refPath> --slot 3]

* Sequins: per-cell random normal tilt + champagne/silver tint (VectorNoise cellnoise on the
  pre-skinned position, so the pattern sticks to the body while it animates).
* Sheer sleeves for meshes where dress and sleeves share ONE material slot: points farther than
  --sleeve-start..end cm from the body's centre line (|local X|) fade to dithered transparency.
  Set --sleeve-start very large (e.g. 999) to disable.
* All looks are parameters: make a Material Instance and tune SequinCellsPerCm, SequinTilt,
  SequinMetallic, SequinRoughness, SequinChampagne, SequinSilver, SleeveOrganza, SleeveOpacity.
* Refuses to overwrite an existing asset.
"""
import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from ue_mcp import T, call, get_props, set_props  # noqa: E402


class Graph:
    def __init__(self, mat):
        self.m, self.n = mat, 0

    def add(self, cls, **props):
        self.n += 1
        e = call(T.MATERIAL, 'add_expression', {
            'material_or_function': self.m,
            'expression_class': {'refPath': '/Script/Engine.MaterialExpression' + cls},
            'x': -1800 + 220 * (self.n % 8), 'y': 160 * (self.n // 8)})
        if props:
            set_props(e, props)
        return e

    def link(self, src, dst, inp, out=''):
        names = call(T.MATERIAL, 'get_expression_input_names', {'expression': dst})
        if inp not in names and len(names) == 1:
            inp = names[0]  # a single unnamed input is reported as 'None'
        tries = [inp, ''] if inp == 'None' else [inp]
        for i, name in enumerate(tries):
            try:
                return call(T.MATERIAL, 'connect_expressions', {
                    'from_expression': src, 'from_output_name': out,
                    'to_expression': dst, 'to_input_name': name})
            except RuntimeError:
                if i == len(tries) - 1:
                    raise

    def scalar(self, name, v):
        return self.add('ScalarParameter', ParameterName=name, DefaultValue=v)

    def color(self, name, rgb):
        return self.add('VectorParameter', ParameterName=name,
                        DefaultValue={'r': rgb[0], 'g': rgb[1], 'b': rgb[2], 'a': 1})

    def lerp(self, a, b, alpha):
        e = self.add('LinearInterpolate')
        for k, v in (('A', a), ('B', b)):
            if isinstance(v, (int, float)):
                set_props(e, {'Const' + k: v})
            else:
                self.link(v, e, k)
        self.link(alpha, e, 'Alpha')
        return e


def build(folder, name, s0, s1):
    path = f'{folder}/{name}'
    if call(T.ASSET, 'exists', {'path': path}):
        sys.exit(f'{path} exists; choose another --name (nothing overwritten)')
    m = call(T.MATERIAL, 'create_material', {'folder_path': folder, 'asset_name': name})
    g = Graph(m)
    p_vs = g.add('PreSkinnedPosition')            # vertex shader only
    P = g.add('VertexInterpolator'); g.link(p_vs, P, 'VS')
    px = g.add('ComponentMask', R=True, G=False, B=False, A=False); g.link(P, px, 'Input')
    ax = g.add('Abs'); g.link(px, ax, 'Input')
    sleeve = g.add('SmoothStep')
    g.link(g.scalar('SleeveStartCm', s0), sleeve, 'Min')
    g.link(g.scalar('SleeveEndCm', s1), sleeve, 'Max')
    g.link(ax, sleeve, 'Value')

    sp = g.add('Multiply'); g.link(P, sp, 'A'); g.link(g.scalar('SequinCellsPerCm', 3.6), sp, 'B')
    vn = g.add('VectorNoise', NoiseFunction='VNF_CellnoiseALU'); g.link(sp, vn, 'Position')
    c = g.add('Subtract', ConstB=0.5); g.link(vn, c, 'A')
    tv = g.add('Multiply'); g.link(c, tv, 'A'); g.link(g.scalar('SequinTilt', 0.8), tv, 'B')
    xy = g.add('ComponentMask', R=True, G=True, B=False, A=False); g.link(tv, xy, 'Input')
    nv = g.add('AppendVector'); g.link(xy, nv, 'A'); g.link(g.add('Constant', R=1.0), nv, 'B')
    nn = g.add('Normalize'); g.link(nv, nn, 'VectorInput')
    normal = g.lerp(nn, g.add('Constant3Vector', Constant={'r': 0, 'g': 0, 'b': 1, 'a': 1}), sleeve)

    gch = g.add('ComponentMask', R=False, G=True, B=False, A=False); g.link(vn, gch, 'Input')
    seq = g.lerp(g.color('SequinChampagne', (0.88, 0.75, 0.62)), g.color('SequinSilver', (0.97, 0.95, 0.94)), gch)
    base = g.lerp(seq, g.color('SleeveOrganza', (0.95, 0.94, 0.93)), sleeve)
    metal = g.lerp(g.scalar('SequinMetallic', 0.45), 0.0, sleeve)
    rough = g.lerp(g.scalar('SequinRoughness', 0.28), g.scalar('SleeveRoughness', 0.5), sleeve)
    alpha = g.lerp(1.0, g.scalar('SleeveOpacity', 0.58), sleeve)
    dither = g.add('MaterialFunctionCall', MaterialFunction={
        'refPath': '/Engine/Functions/Engine_MaterialFunctions02/Utility/DitherTemporalAA.DitherTemporalAA'})
    g.link(alpha, dither, 'Alpha Threshold')

    for e, prop in ((base, 'MP_BaseColor'), (metal, 'MP_Metallic'), (rough, 'MP_Roughness'),
                    (normal, 'MP_Normal'), (dither, 'MP_OpacityMask')):
        call(T.MATERIAL, 'connect_to_output', {'expression': e, 'material_property': prop,
                                               'output_name': 'Result' if e is dither else ''})
    set_props(m, {'BlendMode': 'BLEND_Masked', 'TwoSided': True})
    call(T.MATERIAL, 'layout_expressions', {'material_or_function': m})
    call(T.MATERIAL, 'recompile', {'material_or_function': m})
    call(T.ASSET, 'save_assets', {'asset_paths': [path]})
    return m


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--folder', required=True)
    p.add_argument('--name', required=True)
    p.add_argument('--sleeve-start', type=float, default=17.0)
    p.add_argument('--sleeve-end', type=float, default=20.0)
    p.add_argument('--assign-actor', help='actor refPath whose SkeletalMeshComponent0 gets it')
    p.add_argument('--slot', type=int, help='material slot index for --assign-actor')
    a = p.parse_args()
    m = build(a.folder, a.name, a.sleeve_start, a.sleeve_end)
    print('built', m)
    if a.assign_actor and a.slot is not None:
        comp = {'refPath': a.assign_actor + '.SkeletalMeshComponent0'}
        ov = get_props(comp, ['OverrideMaterials'])['OverrideMaterials']
        mesh = get_props(comp, ['SkeletalMeshAsset'])['SkeletalMeshAsset']
        slots = call(T.SKELETAL_MESH, 'get_material_slots', {'mesh': mesh})
        ov = (ov + [None] * len(slots))[:len(slots)]
        ov[a.slot] = m
        set_props(comp, {'OverrideMaterials': ov})
        print('assigned to slot', a.slot, json.dumps(get_props(comp, ['OverrideMaterials']))[:300])


if __name__ == '__main__':
    main()
