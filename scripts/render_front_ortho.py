"""Orthographic front render of a GLB region (headless Blender, Workbench, texture colours, flat light).
blender -b --factory-startup -P render_front_ortho.py -- in.glb out.png cx cz size [res]
Camera looks along +Y (character faces -Y after glTF import). Pixel (px,py) of the
res x res image maps to model x = cx - size/2 + px/res*size, z = cz + size/2 - py/res*size.
"""
import sys, bpy, math

a = sys.argv[sys.argv.index('--') + 1:]
src, dst, cx, cz, size = a[0], a[1], float(a[2]), float(a[3]), float(a[4])
res = int(a[5]) if len(a) > 5 else 800
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=src)
for o in [o for o in bpy.data.objects if o.type == 'MESH' and not o.vertex_groups]:
    bpy.data.objects.remove(o, do_unlink=True)
sc = bpy.context.scene
cam = bpy.data.objects.new('cam', bpy.data.cameras.new('cam'))
sc.collection.objects.link(cam); sc.camera = cam
cam.data.type = 'ORTHO'; cam.data.ortho_scale = size
cam.location = (cx, -2.0, cz); cam.rotation_euler = (math.radians(90), 0, 0)
sc.render.engine = 'BLENDER_WORKBENCH'
sh = sc.display.shading
sh.light = 'FLAT'; sh.color_type = 'TEXTURE'
sc.render.resolution_x = sc.render.resolution_y = res
sc.render.filepath = dst
sc.view_settings.view_transform = 'Standard'
bpy.ops.render.render(write_still=True)
print('rendered', dst)
