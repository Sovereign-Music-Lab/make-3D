"""Split a fused AssetFurnace character into part material slots and bake face-animation masks.

blender -b --factory-startup -P split_parts_face_masks.py -- in.glb out.glb face.json [preview_dir]

face.json (model units, from an orthographic front render, see render_front_ortho.py):
  {"face_zone": [x0, x1, z0, z1],
   "eyes":  [[cx, cz, rx, rz], [cx, cz, rx, rz]],
   "mouth": [cx, cz, rx, rz]}

Parts (new material slots, each a copy of the source material so textures are kept):
  AF_Skin, AF_Face, AF_Hair, AF_Dress, AF_Sleeves, AF_Bows, AF_Shoes
Skin weights, rig and animation are untouched (only material indices change).

Face masks: writes <out>_facemask.png in the head texture's UV space:
  R = eye mask, G = mouth mask, B = vertical position inside the eye or the mouth
  (0 top .. 1 bottom; the regions never overlap), A = 1.
"""
import colorsys
import json
import os
import sys

import bmesh
import bpy
import numpy as np

args = sys.argv[sys.argv.index('--') + 1:]
src, dst, face_json = args[:3]
preview = args[3] if len(args) > 3 else None
cfg = json.load(open(face_json))

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=src)
for o in [o for o in bpy.data.objects if o.type == 'MESH' and not o.vertex_groups]:
    bpy.data.objects.remove(o, do_unlink=True)
obj = [o for o in bpy.data.objects if o.type == 'MESH'][0]
me = obj.data


def base_image(mat):
    bsdf = next(n for n in mat.node_tree.nodes if n.type == 'BSDF_PRINCIPLED')
    n = bsdf.inputs['Base Color'].links[0].from_node
    while n.type != 'TEX_IMAGE':
        n = next(s for s in n.inputs if s.is_linked).links[0].from_node
    return n.image


src_mats = list(me.materials)
texs = []
for m in src_mats:
    img = base_image(m)
    w, h = img.size
    texs.append(np.array(img.pixels[:], dtype=np.float32).reshape(h, w, 4))
head_idx = int(np.argmax([sum(1 for f in me.polygons if f.material_index == i and f.center.z > 0.30) /
                          max(1, sum(1 for f in me.polygons if f.material_index == i)) for i in range(len(src_mats))]))
print('materials', [m.name for m in src_mats], 'head material index', head_idx)

uvl = me.uv_layers.active.data
n = len(me.polygons)
cen = np.array([f.center[:] for f in me.polygons])
nor = np.array([f.normal[:] for f in me.polygons])
mat = np.array([f.material_index for f in me.polygons])
hsv = np.zeros((n, 3))
for f in me.polygons:
    t = texs[f.material_index]; th, tw = t.shape[:2]
    cs = []
    for l in f.loop_indices:  # average the corners and the centre: steadier than one sample
        u, v = uvl[l].uv
        cs.append(t[min(th - 1, max(0, int(v * th))), min(tw - 1, max(0, int(u * tw))), :3])
    hsv[f.index] = colorsys.rgb_to_hsv(*np.mean(cs, axis=0))

PARTS = ['AF_Skin', 'AF_Face', 'AF_Hair', 'AF_Dress', 'AF_Sleeves', 'AF_Bows', 'AF_Shoes']
SKIN, FACE, HAIR, DRESS, SLEEVES, BOWS, SHOES = range(7)
fx0, fx1, fz0, fz1 = cfg['face_zone']
lab = np.zeros(n, int)
for i in range(n):
    h, s, v = hsv[i]; x, y, z = cen[i]; ax = abs(x)
    if mat[i] == head_idx:
        in_face = fx0 < x < fx1 and fz0 < z < fz1 and nor[i, 1] < -0.25
        if in_face:  # first: eye whites are bright and grey but belong to the face
            lab[i] = FACE
        elif v > 0.78 and s < 0.10:
            lab[i] = BOWS
        elif v < 0.58:
            lab[i] = HAIR
        else:
            lab[i] = FACE if s > 0.12 else BOWS
    else:
        if v > 0.85 and s < 0.07 and z > 0.28:
            lab[i] = BOWS
        elif v < 0.45 and z > cfg.get('hair_min_z', 0.02):  # hair ends mid-back; darker skirt below is dress
            lab[i] = HAIR
        elif z < -0.36:
            lab[i] = SHOES if s < 0.22 else SKIN
        elif z < cfg.get('hem_z', -0.08):  # below the skirt hem: legs only
            lab[i] = SKIN
        elif s >= 0.19 and v > 0.45:
            lab[i] = SKIN
        elif ax > cfg.get('torso_half_width', 0.075) and z > cfg.get('sleeve_min_z', 0.03):
            lab[i] = SLEEVES
        elif ax > 0.07 and -0.14 < z < 0.25 and s < 0.08 and v > 0.74:  # white organza only, not champagne skirt
            lab[i] = SLEEVES
        elif -0.24 < z < 0.25:
            lab[i] = DRESS
        else:
            lab[i] = SKIN

# majority smoothing over face neighbours (shared edges), never across head/body sections
bm = bmesh.new(); bm.from_mesh(me); bm.faces.ensure_lookup_table()
nbrs = [[g.index for e in f.edges for g in e.link_faces if g.index != f.index] for f in bm.faces]
bm.free()
for _ in range(3):
    new = lab.copy()
    for i in range(n):
        if lab[i] in (FACE,):  # keep face labels exact (eyes/brows are dark but belong to the face)
            continue
        c = np.bincount([lab[j] for j in nbrs[i] if mat[j] == mat[i]] + [lab[i]], minlength=7)
        if c.max() > c[lab[i]] + 1:
            new[i] = int(c.argmax())
    lab = new

new_mats = []
for p in PARTS:
    srcm = src_mats[head_idx] if p == 'AF_Face' else src_mats[1 - head_idx if len(src_mats) == 2 else 0]
    m = srcm.copy(); m.name = p; new_mats.append(m)
# parts on the head section must keep the head texture: give them head copies
head_copies = {}
me.materials.clear()
for m in new_mats:
    me.materials.append(m)
for i, f in enumerate(me.polygons):
    p = lab[i]
    if mat[i] == head_idx and p != FACE:
        key = PARTS[p]
        if key not in head_copies:
            hm = src_mats[head_idx].copy(); hm.name = key + '_Head'; me.materials.append(hm)
            head_copies[key] = len(me.materials) - 1
        f.material_index = head_copies[key]
    else:
        f.material_index = p
counts = {me.materials[k].name: int(c) for k, c in enumerate(np.bincount([f.material_index for f in me.polygons], minlength=len(me.materials))) if c}
print('part faces', counts)

# ---- face masks in head-texture UV space ------------------------------------------------
th, tw = texs[head_idx].shape[:2]
mask = np.zeros((th, tw, 4), np.float32)


def ell(px, pz, e):
    cx, cz, rx, rz = e
    d = ((px - cx) / rx) ** 2 + ((pz - cz) / rz) ** 2
    return d, (cz + rz - pz) / (2 * rz)  # 0 top .. 1 bottom


regions = [(e, 0, 2) for e in cfg['eyes']] + [(cfg['mouth'], 1, 2)]  # B holds vertical position of eye OR mouth
verts = np.array([v.co[:] for v in me.vertices])
for f in me.polygons:
    if lab[f.index] != FACE or len(f.loop_indices) < 3:
        continue
    c = cen[f.index]
    hits = [r for r in regions if ell(c[0], c[2], (r[0][0], r[0][1], r[0][2] * 1.6, r[0][3] * 1.6))[0] < 1]
    if not hits:
        continue
    li = list(f.loop_indices)
    for k in range(1, len(li) - 1):  # fan-triangulate
        tri = [li[0], li[k], li[k + 1]]
        uv = np.array([uvl[l].uv[:] for l in tri]) * [tw, th]
        p3 = np.array([verts[me.loops[l].vertex_index] for l in tri])
        x0, y0 = np.floor(uv.min(0)).astype(int); x1, y1 = np.ceil(uv.max(0)).astype(int)
        xs, ys = np.meshgrid(np.arange(max(0, x0), min(tw, x1 + 1)), np.arange(max(0, y0), min(th, y1 + 1)))
        P = np.stack([xs.ravel() + 0.5, ys.ravel() + 0.5], 1)
        a, b, cc = uv
        den = (b[1] - cc[1]) * (a[0] - cc[0]) + (cc[0] - b[0]) * (a[1] - cc[1])
        if abs(den) < 1e-9:
            continue
        w1 = ((b[1] - cc[1]) * (P[:, 0] - cc[0]) + (cc[0] - b[0]) * (P[:, 1] - cc[1])) / den
        w2 = ((cc[1] - a[1]) * (P[:, 0] - cc[0]) + (a[0] - cc[0]) * (P[:, 1] - cc[1])) / den
        w3 = 1 - w1 - w2
        inside = (w1 >= -0.01) & (w2 >= -0.01) & (w3 >= -0.01)
        if not inside.any():
            continue
        W = np.stack([w1, w2, w3], 1)[inside]
        pos = W @ p3
        X, Y = P[inside, 0].astype(int), P[inside, 1].astype(int)
        for e, ch_mask, ch_v in hits:
            d, vpos = ell(pos[:, 0], pos[:, 2], e)
            m = np.clip((1.0 - d) / 0.25, 0, 1)  # soft edge
            sel = m > mask[Y, X, ch_mask]
            mask[Y[sel], X[sel], ch_mask] = m[sel]
            mask[Y[sel], X[sel], ch_v] = np.clip(vpos[sel], 0, 1)

img = bpy.data.images.new('facemask', tw, th, alpha=True, float_buffer=False)
img.colorspace_settings.name = 'Non-Color'
mask[..., 3] = 1.0  # alpha stays opaque: a zero alpha makes PNG tools drop the colour data
img.pixels[:] = mask.ravel()
mpath = os.path.splitext(dst)[0] + '_facemask.png'
img.filepath_raw = mpath; img.file_format = 'PNG'; img.save()
print('mask', mpath, 'eye texels', int((mask[..., 0] > 0.5).sum()), 'mouth texels', int((mask[..., 1] > 0.5).sum()))

# ---- optional part preview ----------------------------------------------------------------
if preview:
    import math
    cols = {'AF_Skin': (0.95, 0.7, 0.55), 'AF_Face': (1, 0.85, 0.2), 'AF_Hair': (0.35, 0.15, 0.05), 'AF_Dress': (0.2, 0.6, 1),
            'AF_Sleeves': (0.6, 1, 0.6), 'AF_Bows': (1, 0.2, 0.8), 'AF_Shoes': (0.5, 0.5, 0.5)}
    for m in me.materials:
        m.diffuse_color = (*cols[m.name.replace('_Head', '')], 1)
    sc = bpy.context.scene
    sc.render.engine = 'BLENDER_WORKBENCH'; sc.display.shading.light = 'STUDIO'; sc.display.shading.color_type = 'MATERIAL'
    sc.render.resolution_x, sc.render.resolution_y = 500, 800
    cam = bpy.data.objects.new('cam', bpy.data.cameras.new('cam')); sc.collection.objects.link(cam); sc.camera = cam
    cam.data.type = 'ORTHO'; cam.data.ortho_scale = 0.95
    os.makedirs(preview, exist_ok=True)
    for name, ang in (('front', 0), ('side', 90), ('back', 180)):
        r = math.radians(ang)
        cam.location = (2 * math.sin(r), -2 * math.cos(r), 0.0)
        cam.rotation_euler = (math.radians(90), 0, r)
        sc.render.filepath = os.path.join(preview, f'parts_{name}.png')
        bpy.ops.render.render(write_still=True)
    # restore real textures for export: re-copy from source materials
    for m in me.materials:
        m.diffuse_color = (1, 1, 1, 1)

# Weld vertices split at UV seams (AssetFurnace atlases are very fragmented) and rebuild smooth
# normals; otherwise every seam is a hard normal break and the face looks faceted in Unreal.
bm = bmesh.new(); bm.from_mesh(me)
n0 = len(bm.verts); bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-5)
print('welded seam vertices', n0 - len(bm.verts))
bm.to_mesh(me); bm.free()
if me.has_custom_normals:
    with bpy.context.temp_override(object=obj, active_object=obj):
        bpy.ops.mesh.customdata_custom_splitnormals_clear()
for poly in me.polygons:
    poly.use_smooth = True
me.update()
bpy.ops.export_scene.gltf(filepath=dst, export_format='GLB', export_animations=True, export_skins=True)
print('exported', dst)
