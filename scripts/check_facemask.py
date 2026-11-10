"""Run (headless). Render the head front with the face mask (R eyes, G mouth) shown on the face, for checking.
blender -b --factory-startup -P check_facemask.py -- parts.glb facemask.png out.png cx cz size"""
import sys, bpy, math
a = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=a[0])
mask = bpy.data.images.load(a[1])
for m in bpy.data.materials:
    if m.name.startswith('AF_Face') or m.name.endswith('_Head'):
        nt = m.node_tree; bsdf = next(n for n in nt.nodes if n.type == 'BSDF_PRINCIPLED')
        base = bsdf.inputs['Base Color'].links[0].from_node
        tex = nt.nodes.new('ShaderNodeTexImage'); tex.image = mask
        mix = nt.nodes.new('ShaderNodeMix'); mix.data_type = 'RGBA'
        sep = nt.nodes.new('ShaderNodeSeparateColor')
        nt.links.new(tex.outputs['Color'], sep.inputs['Color'])
        mx = nt.nodes.new('ShaderNodeMath'); mx.operation = 'MAXIMUM'
        nt.links.new(sep.outputs[0], mx.inputs[0]); nt.links.new(sep.outputs[1], mx.inputs[1])
        nt.links.new(mx.outputs[0], mix.inputs['Factor'])
        nt.links.new(base.outputs['Color'], mix.inputs['A'])
        mix.inputs['B'].default_value = (0, 1, 0.2, 1)
        nt.links.new(mix.outputs['Result'], bsdf.inputs['Base Color'])
sc = bpy.context.scene
cam = bpy.data.objects.new('cam', bpy.data.cameras.new('cam')); sc.collection.objects.link(cam); sc.camera = cam
cam.data.type = 'ORTHO'; cam.data.ortho_scale = float(a[5]); cam.location = (float(a[3]), -2, float(a[4])); cam.rotation_euler = (math.radians(90), 0, 0)
sc.render.engine = 'BLENDER_EEVEE_NEXT' if 'BLENDER_EEVEE_NEXT' in [e.identifier for e in bpy.types.RenderSettings.bl_rna.properties['engine'].enum_items] else 'BLENDER_EEVEE'
w = bpy.data.worlds.new('w'); sc.world = w; w.use_nodes = True; w.node_tree.nodes['Background'].inputs[1].default_value = 1.5
sc.render.resolution_x = sc.render.resolution_y = 700; sc.render.filepath = a[2]
sc.view_settings.view_transform = 'Standard'
bpy.ops.render.render(write_still=True); print('rendered', a[2])
