"""Face animation for characters whose eyes and mouth are painted on the texture (no face bones/morphs).

Builds a material in the open Unreal editor through MCP that, using a face-mask texture,
  * blinks automatically: every BlinkPeriod seconds an eyelid sweeps down over the eye
    (EyelidColor) with a dark lash line at its edge, then opens again (~0.24 s);
  * opens the mouth with the MouthOpen parameter (0..1): a dark band grows between the lips.
BlinkManual (0..1) overrides for posing/lip-sync; the larger of auto and manual wins.

Mask texture (from split_parts_face_masks.py), in the face texture's UV space:
  R = eye mask, G = mouth mask, B = vertical position inside eye/mouth (0 top .. 1 bottom).

    python3 ue_face_anim_material.py --folder /Game/Characters/Hero --name M_Hero_FaceAnim \
        --base-texture /Game/Characters/Hero/Image_3 --mask-file /abs/hero_facemask.png \
        [--eyelid 0.80 0.62 0.55] [--assign-actor <actor refPath> --slot-name AF_Face]
Refuses to overwrite existing assets.
"""
import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from ue_mcp import T, call, get_props, ref, set_props  # noqa: E402
from ue_sequin_material import Graph  # noqa: E402


def build(folder, name, base_tex, mask_tex, eyelid):
    path = f'{folder}/{name}'
    if call(T.ASSET, 'exists', {'path': path}):
        sys.exit(f'{path} exists; choose another --name (nothing overwritten)')
    m = call(T.MATERIAL, 'create_material', {'folder_path': folder, 'asset_name': name})
    g = Graph(m)
    base = g.add('TextureSampleParameter2D', ParameterName='BaseTex', Texture=ref(base_tex))
    mask = g.add('TextureSampleParameter2D', ParameterName='FaceMask', Texture=ref(mask_tex),
                 SamplerType='SAMPLERTYPE_LinearColor')
    R = g.add('ComponentMask', R=True, G=False, B=False, A=False); g.link(mask, R, 'Input')
    G = g.add('ComponentMask', R=False, G=True, B=False, A=False); g.link(mask, G, 'Input')
    B = g.add('ComponentMask', R=False, G=False, B=True, A=False); g.link(mask, B, 'Input')

    # auto blink: phase = frac(t / P) * P ; close = saturate(1 - |phase - 0.12| / 0.12)
    period = g.scalar('BlinkPeriod', 3.6)
    t = g.add('Time')
    tp = g.add('Divide'); g.link(t, tp, 'A'); g.link(period, tp, 'B')
    fr = g.add('Frac'); g.link(tp, fr, 'Input')
    ph = g.add('Multiply'); g.link(fr, ph, 'A'); g.link(period, ph, 'B')
    d = g.add('Subtract', ConstB=0.12); g.link(ph, d, 'A')
    ad = g.add('Abs'); g.link(d, ad, 'Input')
    dv = g.add('Divide', ConstB=0.12); g.link(ad, dv, 'A')
    om = g.add('OneMinus'); g.link(dv, om, 'Input')
    auto = g.add('Saturate'); g.link(om, auto, 'Input')
    autoon = g.add('Multiply'); g.link(auto, autoon, 'A'); g.link(g.scalar('AutoBlink', 1.0), autoon, 'B')
    close = g.add('Max'); g.link(autoon, close, 'A'); g.link(g.scalar('BlinkManual', 0.0), close, 'B')

    # eyelid covers the eye from the top down to 'close*1.1'
    edge = g.add('Multiply', ConstB=1.1); g.link(close, edge, 'A')
    diff = g.add('Subtract'); g.link(edge, diff, 'A'); g.link(B, diff, 'B')
    sharp = g.add('Multiply', ConstB=10.0); g.link(diff, sharp, 'A')
    lidm = g.add('Saturate'); g.link(sharp, lidm, 'Input')
    lid = g.add('Multiply'); g.link(lidm, lid, 'A'); g.link(R, lid, 'B')
    # lash line: thin band at the lid edge while closing
    e2 = g.add('Subtract'); g.link(B, e2, 'A'); g.link(edge, e2, 'B')
    e2a = g.add('Abs'); g.link(e2, e2a, 'Input')
    e2m = g.add('Multiply', ConstB=12.0); g.link(e2a, e2m, 'A')
    e2o = g.add('OneMinus'); g.link(e2m, e2o, 'Input')
    band = g.add('Saturate'); g.link(e2o, band, 'Input')
    lash0 = g.add('Multiply'); g.link(band, lash0, 'A'); g.link(R, lash0, 'B')
    closing = g.add('Multiply', ConstB=6.0); g.link(close, closing, 'A')
    closing_s = g.add('Saturate'); g.link(closing, closing_s, 'Input')
    lash = g.add('Multiply'); g.link(lash0, lash, 'A'); g.link(closing_s, lash, 'B')

    col = g.lerp(base, g.color('EyelidColor', eyelid), lid)
    col = g.lerp(col, g.color('LashColor', (0.05, 0.03, 0.03)), lash)

    # mouth: dark band centred at MouthCentre that widens with MouthOpen
    mo = g.scalar('MouthOpen', 0.0)
    mc = g.add('Subtract'); g.link(B, mc, 'A'); g.link(g.scalar('MouthCentre', 0.55), mc, 'B')
    mca = g.add('Abs'); g.link(mc, mca, 'Input')
    half = g.add('Multiply', ConstB=0.35); g.link(mo, half, 'A')
    gap = g.add('Subtract'); g.link(half, gap, 'A'); g.link(mca, gap, 'B')
    gs = g.add('Multiply', ConstB=20.0); g.link(gap, gs, 'A')
    gsat = g.add('Saturate'); g.link(gs, gsat, 'Input')
    mouth = g.add('Multiply'); g.link(gsat, mouth, 'A'); g.link(G, mouth, 'B')
    col = g.lerp(col, g.color('MouthColor', (0.22, 0.05, 0.05)), mouth)

    call(T.MATERIAL, 'connect_to_output', {'expression': col, 'output_name': '', 'material_property': 'MP_BaseColor'})
    rough = g.add('Constant', R=0.55)
    call(T.MATERIAL, 'connect_to_output', {'expression': rough, 'output_name': '', 'material_property': 'MP_Roughness'})
    call(T.MATERIAL, 'layout_expressions', {'material_or_function': m})
    call(T.MATERIAL, 'recompile', {'material_or_function': m})
    call(T.ASSET, 'save_assets', {'asset_paths': [path]})
    return m


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--folder', required=True)
    p.add_argument('--name', required=True)
    p.add_argument('--base-texture', required=True, help='content path of the face colour texture')
    p.add_argument('--mask-file', required=True, help='face mask PNG on disk')
    p.add_argument('--eyelid', type=float, nargs=3, default=(0.80, 0.62, 0.55))
    p.add_argument('--assign-actor')
    p.add_argument('--slot-name', default='AF_Face')
    a = p.parse_args()

    mask_name = 'T_' + a.name.replace('M_', '', 1) + '_Mask'
    mask_path = f'{a.folder}/{mask_name}'
    if call(T.ASSET, 'exists', {'path': mask_path}):
        sys.exit(f'{mask_path} exists (nothing overwritten)')
    tex = call(T.TEXTURE, 'import_file', {'folder_path': a.folder, 'asset_name': mask_name,
                                          'source_file': os.path.abspath(a.mask_file)})[0]
    set_props(tex, {'SRGB': False, 'CompressionSettings': 'TC_VectorDisplacementmap'})
    call(T.ASSET, 'save_assets', {'asset_paths': [mask_path]})
    m = build(a.folder, a.name, a.base_texture, mask_path, a.eyelid)
    print('built', m)
    if a.assign_actor:
        comp = {'refPath': a.assign_actor + '.SkeletalMeshComponent0'}
        mesh = get_props(comp, ['SkeletalMeshAsset'])['SkeletalMeshAsset']
        slots = call(T.SKELETAL_MESH, 'get_material_slots', {'mesh': mesh})
        ov = get_props(comp, ['OverrideMaterials'])['OverrideMaterials']
        ov = (ov + [None] * len(slots))[:len(slots)]
        ov[slots.index(a.slot_name)] = m
        set_props(comp, {'OverrideMaterials': ov})
        print('assigned to', a.slot_name)


if __name__ == '__main__':
    main()
