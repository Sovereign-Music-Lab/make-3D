"""Run (headless). Grow groom strands over a character's hair-mesh surface and export Alembic.

blender -b --factory-startup -P strands_from_hair_mesh.py -- parts.glb out.abc [--count 40000]
        [--length 0.07] [--points 10] [--lift 0.0015] [--wave 0.004] [--scale 100] [--preview p.png]

* Hair surface = faces whose material name starts with --material-prefix (default AF_Hair),
  e.g. the slots made by split_parts_face_masks.py.
* Each strand starts at a random point on that surface (area-weighted) and walks "downhill":
  gravity projected onto the surface tangent plane, re-snapped to the surface each step and
  lifted a little off it (--lift) so it never sinks in. Small sideways waves give a soft look.
  Many short overlapping strands cover long hair like a pelt that follows the mesh flow.
* Coordinates: the GLB's rest pose (the skinned mesh), scaled by --scale (100 = metres -> cm,
  matching scripts/glb_to_fbx_unreal.py), so the groom lines up with the imported skeletal mesh.
* Output is a Blender Curves object exported as Alembic curves for Unreal's Groom importer.
"""
import argparse
import math
import sys

import bpy
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree

argv = sys.argv[sys.argv.index('--') + 1:]
p = argparse.ArgumentParser()
p.add_argument('src'); p.add_argument('dst')
p.add_argument('--count', type=int, default=40000)
p.add_argument('--length', type=float, default=0.07, help='strand length in model units (m)')
p.add_argument('--points', type=int, default=10)
p.add_argument('--lift', type=float, default=0.0015)
p.add_argument('--wave', type=float, default=0.004)
p.add_argument('--scale', type=float, default=100.0)
p.add_argument('--material-prefix', default='AF_Hair')
p.add_argument('--seed', type=int, default=7)
p.add_argument('--preview')
a = p.parse_args(argv)
rng = np.random.default_rng(a.seed)

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=a.src)
obj = [o for o in bpy.data.objects if o.type == 'MESH' and o.vertex_groups][0]
for o in [o for o in bpy.data.objects if o.type == 'MESH' and o != obj]:
    bpy.data.objects.remove(o, do_unlink=True)
me = obj.data
hair_mats = {i for i, m in enumerate(me.materials) if m and m.name.startswith(a.material_prefix)}
assert hair_mats, f'no material slot starting with {a.material_prefix}'

verts = np.array([v.co[:] for v in me.vertices])
tris, areas = [], []
for f in me.polygons:
    if f.material_index in hair_mats:
        vi = list(f.vertices)
        for k in range(1, len(vi) - 1):
            t = (vi[0], vi[k], vi[k + 1]); tris.append(t)
            v0, v1, v2 = verts[list(t)]
            areas.append(0.5 * np.linalg.norm(np.cross(v1 - v0, v2 - v0)))
tris = np.array(tris); areas = np.array(areas)
print('hair triangles', len(tris), 'area m2', round(areas.sum(), 4))
bvh = BVHTree.FromPolygons([Vector(v) for v in verts], [tuple(t) for t in tris])

# area-weighted root samples
pick = rng.choice(len(tris), size=a.count, p=areas / areas.sum())
r1, r2 = rng.random(a.count), rng.random(a.count)
s1 = np.sqrt(r1)
bary = np.stack([1 - s1, s1 * (1 - r2), s1 * r2], 1)
roots = np.einsum('nk,nkd->nd', bary, verts[tris[pick]])

down = Vector((0, 0, -1))
step = a.length / (a.points - 1)
strands = []
for n in range(a.count):
    loc, nor, _, _ = bvh.find_nearest(Vector(roots[n]))
    if loc is None:
        continue
    pts = [loc + nor * a.lift]
    phase = rng.random() * 2 * math.pi
    side_amp = a.wave * (0.5 + rng.random())
    L = 0.6 + 0.8 * rng.random()  # vary length
    for k in range(1, a.points):
        cur = pts[-1]
        hit, nrm, _, _ = bvh.find_nearest(cur)
        if hit is None:
            break
        t = down - nrm * down.dot(nrm)  # gravity on the tangent plane
        if t.length < 1e-4:  # surface faces straight up/down: drift outward-down
            t = (down + nrm * 0.3)
        t.normalize()
        side = nrm.cross(t)
        nxt = cur + t * step * L + side * side_amp * math.sin(phase + k * 0.9) * step / a.length
        snap, nrm2, _, _ = bvh.find_nearest(nxt)
        if snap is not None:
            nxt = snap + nrm2 * a.lift * (1 + 0.5 * k / a.points)
        pts.append(nxt)
    if len(pts) == a.points:
        strands.append(pts)
print('strands', len(strands))

# build a Curves object (new hair curves type) in centimetres
cv = bpy.data.hair_curves.new('Groom') if hasattr(bpy.data, 'hair_curves') else None
curves = bpy.data.curves.new('GroomCurves', 'CURVE') if cv is None else None
if cv is not None:
    cv.add_curves([a.points] * len(strands))
    pos = np.array([[c * a.scale for c in pt] for s in strands for pt in s], dtype=np.float32)
    cv.attributes['position'].data.foreach_set('vector', pos.ravel())
    gobj = bpy.data.objects.new('Groom', cv)
else:
    curves.dimensions = '3D'
    for s in strands:
        sp = curves.splines.new('POLY'); sp.points.add(len(s) - 1)
        for i, pt in enumerate(s):
            sp.points[i].co = (pt[0] * a.scale, pt[1] * a.scale, pt[2] * a.scale, 1)
    gobj = bpy.data.objects.new('Groom', curves)
bpy.context.scene.collection.objects.link(gobj)
bpy.data.objects.remove(obj, do_unlink=True)
for o in [o for o in bpy.data.objects if o.type == 'ARMATURE']:
    bpy.data.objects.remove(o, do_unlink=True)
for o in bpy.data.objects:
    o.select_set(o == gobj)
bpy.context.view_layer.objects.active = gobj
bpy.ops.wm.alembic_export(filepath=a.dst, selected=True, export_hair=True, export_particles=False,
                          curves_as_mesh=False, start=1, end=1)
print('exported', a.dst, 'curves type', type(gobj.data).__name__)

if a.preview:
    sc = bpy.context.scene
    cam = bpy.data.objects.new('cam', bpy.data.cameras.new('cam')); sc.collection.objects.link(cam); sc.camera = cam
    cam.data.type = 'ORTHO'; cam.data.ortho_scale = 0.5 * a.scale
    cam.location = (0, -2 * a.scale, 0.2 * a.scale); cam.rotation_euler = (math.radians(90), 0, 0)
    cam.data.clip_end = 10 * a.scale
    sc.render.engine = 'BLENDER_WORKBENCH'; sc.render.resolution_x = sc.render.resolution_y = 600
    sc.render.filepath = a.preview; bpy.ops.render.render(write_still=True)
