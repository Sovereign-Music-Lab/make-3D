"""Convert a rigged/animated GLB to an FBX that Unreal imports with working animation.

Run (headless): blender -b --factory-startup -P glb_to_fbx_unreal.py -- in.glb out.fbx [--scale 100] [--fps 24]

Why this exists (all three broke a real import):
  * Blender's glTF importer adds a bone-display Icosphere mesh; it is dropped (not skinned).
  * The factory scene is frames 1-250; the action is baked over that, so a 4 s idle became
    10.4 s. The scene range is set to the action's range.
  * Units: with apply_unit_scale only, Unreal received the mesh in cm but the animation
    translations in m, so the character vanished the moment the animation played.
    With FBX_SCALE_ALL alone the mesh arrived 0.9 cm tall and its normals broke.
    Fix: multiply mesh, rest bones and location keys by --scale (100), then export with
    FBX_SCALE_ALL, so mesh and animation both arrive in cm.
  * Smoothing: glTF splits vertices at UV seams; Unreal then builds normals per UV island
    and the face looks faceted. Vertices are welded (--no-weld to skip), normals rebuilt
    smooth, and mesh_smooth_type='FACE' writes smoothing groups.
The input file is only read.
"""
import argparse
import sys

import bpy


def parse():
    argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
    p = argparse.ArgumentParser()
    p.add_argument('src')
    p.add_argument('dst')
    p.add_argument('--scale', type=float, default=100.0, help='unit bake factor (m -> cm = 100)')
    p.add_argument('--fps', type=int, default=24)
    p.add_argument('--no-weld', action='store_true', help='keep vertices split at UV seams')
    return p.parse_args(argv)


def location_fcurves(action):
    """Location F-curves of an action, for both the layered (4.4+) and legacy API."""
    if hasattr(action, 'layers') and action.layers:
        for layer in action.layers:
            for strip in layer.strips:
                for bag in strip.channelbags:
                    yield from (fc for fc in bag.fcurves if fc.data_path.endswith('.location'))
    else:
        yield from (fc for fc in action.fcurves if fc.data_path.endswith('.location'))


def main():
    a = parse()
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=a.src)
    arms = [o for o in bpy.data.objects if o.type == 'ARMATURE']
    for o in [o for o in bpy.data.objects if o.type == 'MESH']:
        skinned = any(m.type == 'ARMATURE' for m in o.modifiers) or (o.parent in arms and o.vertex_groups)
        if not skinned:
            print('drop helper mesh', o.name)
            bpy.data.objects.remove(o, do_unlink=True)

    if not a.no_weld:
        # glTF splits vertices at every UV seam. AssetFurnace atlases are very fragmented, so
        # Unreal computes normals per island and every seam shows as a hard patch. Weld (UVs
        # stay on the loops) and rebuild smooth normals.
        import bmesh
        for o in [o for o in bpy.data.objects if o.type == 'MESH']:
            bm = bmesh.new(); bm.from_mesh(o.data)
            n0 = len(bm.verts); bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-5)
            bm.to_mesh(o.data); bm.free()
            if o.data.has_custom_normals:
                with bpy.context.temp_override(object=o, active_object=o):
                    bpy.ops.mesh.customdata_custom_splitnormals_clear()
            for poly in o.data.polygons:
                poly.use_smooth = True
            print('welded', o.name, n0 - len(o.data.vertices))
    if bpy.data.actions:
        s, e = bpy.data.actions[0].frame_range
        sc = bpy.context.scene
        sc.render.fps = a.fps
        sc.frame_start, sc.frame_end = max(0, round(s)), round(e)
        print('frames', sc.frame_start, sc.frame_end)

    for arm in arms:
        for o in bpy.data.objects:
            o.select_set(o in arms or o.type == 'MESH')
        bpy.context.view_layer.objects.active = arm
        arm.scale = (a.scale,) * 3
        bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    for act in bpy.data.actions:
        for fc in location_fcurves(act):
            for k in fc.keyframe_points:
                k.co[1] *= a.scale
                k.handle_left[1] *= a.scale
                k.handle_right[1] *= a.scale

    for o in bpy.data.objects:
        print('object', o.name, o.type, tuple(round(v, 2) for v in o.dimensions))
    bpy.ops.export_scene.fbx(
        filepath=a.dst, use_selection=False, object_types={'ARMATURE', 'MESH'},
        add_leaf_bones=False, bake_anim=True, bake_anim_use_all_actions=False,
        bake_anim_use_nla_strips=False, bake_anim_force_startend_keying=True,
        bake_anim_step=1.0, bake_anim_simplify_factor=0.0, path_mode='COPY',
        embed_textures=True, mesh_smooth_type='FACE', apply_unit_scale=True, apply_scale_options='FBX_SCALE_ALL',
        armature_nodetype='NULL')
    print('exported', a.dst)


main()
