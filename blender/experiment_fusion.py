"""Congela y compara una malla Q3 con su fusión parcial; no modifica originales."""
import argparse
import copy
import hashlib
import json
from pathlib import Path
import sys
import time

import bpy
from mathutils import Vector, Euler
from mathutils.bvhtree import BVHTree

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'src'))
sys.path.insert(0, str(ROOT/'blender'))
from generate_oak import mesh_report, render_views
from treegen.crown import measure_crown
from foliage_fusion import fuse, VERSION


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def crown(mesh, height):
    mesh.calc_loop_triangles()
    return measure_crown([tuple(v.co) for v in mesh.vertices],
        [(mesh.materials[t.material_index].name, tuple(t.vertices)) for t in mesh.loop_triangles], height)


def wood_surface_hash(mesh):
    faces = sorted((p.use_smooth, sorted(tuple(v for v in mesh.vertices[i].co) for i in p.vertices))
                   for p in mesh.polygons if mesh.materials[p.material_index].name == 'Oak_Bark')
    return hashlib.sha256(json.dumps(faces).encode()).hexdigest()


def shading():
    scene = bpy.context.scene
    keys = ('light', 'studio_light', 'studiolight_rotate_z', 'color_type', 'show_shadows',
            'show_cavity', 'cavity_type', 'background_type', 'curvature_ridge_factor',
            'curvature_valley_factor', 'cavity_ridge_factor', 'cavity_valley_factor')
    return {'engine': scene.render.engine, 'shading': {k: getattr(scene.display.shading, k) for k in keys},
            'world_color': list(scene.world.color), 'view_transform': scene.view_settings.view_transform,
            'look': scene.view_settings.look, 'exposure': scene.view_settings.exposure,
            'gamma': scene.view_settings.gamma,
            'materials': {m.name: list(m.diffuse_color) for m in bpy.data.objects['Oak'].data.materials if m}}


def render(obj, output, framing, frozen_cameras=None):
    output.mkdir(parents=True, exist_ok=False)
    for other in bpy.data.objects:
        if other.type == 'MESH':
            other.hide_render = other != obj
    cameras = render_views(obj, output, framing=framing)
    cameras.update(render_views(obj, output, [('below', (1.3, -1.8, -.65))], framing=framing))
    scene = bpy.context.scene
    # Una toma distante en perspectiva, con el mismo centro y focal de 50 mm.
    cam = scene.camera
    cam.data.type = 'PERSP'
    center = Vector(framing['center'])
    cam.location = center+Vector((1.3, -1.8, .65)).normalized()*framing['span']*7.5
    cam.rotation_euler = (center-cam.location).to_track_quat('-Z', 'Y').to_euler()
    cam.data.lens = 50
    cameras['game'] = {'type': 'PERSP', 'location': list(cam.location), 'rotation_euler': list(cam.rotation_euler),
                       'lens_mm': cam.data.lens, 'ortho_scale': cam.data.ortho_scale, 'resolution': [900, 900]}
    scene.render.filepath = str(output/'game.png')
    bpy.ops.render.render(write_still=True)
    if frozen_cameras is not None:
        assert cameras == frozen_cameras, 'Cambió una cámara'
    return cameras, shading()


def silhouette(mesh, camera, resolution=192):
    """Máscara ortográfica de follaje, sin iluminación; no mide naturalidad."""
    mesh.calc_loop_triangles()
    triangles = [tuple(t.vertices) for t in mesh.loop_triangles if mesh.materials[t.material_index].name == 'Oak_Leaves']
    bvh = BVHTree.FromPolygons([v.co for v in mesh.vertices], triangles, all_triangles=True)
    rotation = Euler(camera['rotation_euler']).to_matrix()
    right, up, forward = [rotation@Vector(v) for v in ((1, 0, 0), (0, 1, 0), (0, 0, -1))]
    mask = set()
    for row in range(resolution):
        for col in range(resolution):
            x = ((col+.5)/resolution-.5)*camera['ortho_scale']
            y = ((row+.5)/resolution-.5)*camera['ortho_scale']
            origin = Vector(camera['location'])+right*x+up*y
            if bvh.ray_cast(origin, forward)[2] is not None:
                mask.add((row, col))
    return mask


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, required=True)
    parser.add_argument('--cameras', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args(sys.argv[sys.argv.index('--')+1:])
    assert bpy.app.version[:3] == (5, 2, 1)
    source, output = args.source.resolve(), args.output.resolve()
    started = time.monotonic()
    original_files = {name: sha(source/name) for name in ('manifest.json', 'tree.blend', 'tree.glb')}
    original = json.loads((source/'manifest.json').read_text())
    assert original['spec']['algorithm_version'] == '0.4.0'
    output.mkdir(parents=True, exist_ok=False)
    candidate = output/'candidate'
    candidate.mkdir()
    historical = json.loads(args.cameras.read_text())
    bpy.ops.wm.open_mainfile(filepath=str(source/'tree.blend'), load_ui=False)
    obj = bpy.data.objects['Oak']
    before_mesh = obj.data
    assert mesh_report(before_mesh) == original['metrics'], 'La malla Q3 no coincide con el manifiesto'
    height = original['spec']['parameters']['height_m']
    before = crown(before_mesh, height)
    assert before == original['crown_checks']
    before_mesh.use_fake_user = True
    cameras, lights = render(obj, output/'base', historical['framing'])
    for name in ('front', 'side', 'top', 'perspective'):
        assert cameras[name] == historical['cameras'][name], 'Cambió cámara histórica Q3'
    frozen = {'source_files_sha256': original_files, 'spec': original['spec'], 'seeds': original['seeds'],
              'framing': historical['framing'], 'cameras': cameras, 'lighting': lights,
              'materials_source': 'Q3 guardada, sin cambios',
              'historical_cameras_sha256': sha(args.cameras),
              'generator_sources_sha256': {p: sha(ROOT/p) for p in original['sources_sha256'] if Path(p).name.startswith('oak_nodes')},
              'input_geometry_sha256': original['metrics']['geometry_sha256'],
              'input_foliage_checks': original['foliage_checks']}
    assert all(h == original['sources_sha256'][p] for p, h in frozen['generator_sources_sha256'].items()), 'Cambió una fuente histórica'
    (output/'reference-lock.json').write_text(json.dumps(frozen, indent=2)+'\n')
    effective = min(original['spec']['parameters']['foliage_scale_m'], .24*height)
    result, report = fuse(before_mesh, effective, height)
    obj.data = result
    metrics, after = mesh_report(result), crown(result, height)
    assert before['wood_geometry_sha256'] == after['wood_geometry_sha256'], 'Cambió la madera'
    assert wood_surface_hash(before_mesh) == wood_surface_hash(result), 'Cambió la superficie/sombreado de madera'
    assert after['leaf_bounds_blender'][0][2] >= -1e-5 and after['leaf_bounds_blender'][1][2] <= height+1e-5
    masks = {}
    for view in ('front', 'side', 'top', 'below'):
        a, b = silhouette(before_mesh, cameras[view]), silhouette(result, cameras[view])
        masks[view] = {'resolution': 192, 'iou': len(a & b)/len(a | b),
                       'projected_area_ratio': len(b)/len(a)}
    other_cameras, other_lights = render(obj, output/'fused', historical['framing'], cameras)
    assert lights == other_lights, 'Cambió iluminación o materiales'
    bpy.ops.object.select_all(action='DESELECT')
    obj.hide_set(False)
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    bpy.ops.export_scene.gltf(filepath=str(candidate/'tree.glb'), export_format='GLB', use_selection=True, export_yup=True)
    bpy.ops.wm.save_as_mainfile(filepath=str(candidate/'tree.blend'))
    manifest = {k: copy.deepcopy(original[k]) for k in ('spec', 'spec_sha256', 'seeds', 'socket_values',
        'structure_checks', 'normalization', 'blender', 'blender_build', 'blender_python')}
    manifest.update(status='completed', metrics=metrics, crown_checks=after, cameras=cameras,
                    required_views=[], glb_sha256=sha(candidate/'tree.glb'),
                    postprocess={**report, 'base_geometry_sha256': original['metrics']['geometry_sha256'],
                                 'base_spec_unchanged': True, 'base_foliage_checks': original['foliage_checks']},
                    sources_sha256={str(p.relative_to(ROOT)): sha(p) for p in
                        [Path(__file__), ROOT/'blender/foliage_fusion.py', ROOT/'blender/generate_oak.py', ROOT/'src/treegen/crown.py']})
    manifest['files_sha256'] = {n: sha(candidate/n) for n in ('tree.blend', 'tree.glb')}
    (candidate/'manifest.json').write_text(json.dumps(manifest, indent=2)+'\n')
    assert original_files == {name: sha(source/name) for name in original_files}, 'Se alteró Q3'
    summary = {'experiment': VERSION, 'case': source.name, 'same_final_wood': True,
               'same_wood_surface_and_smoothing': True,
               'same_input_masses_parameters_and_seeds': True, 'same_cameras_and_lighting': True,
               'source_unchanged': True, 'before': before, 'after': after, 'silhouette': masks,
               'fusion': report, 'duration_seconds': round(time.monotonic()-started, 3),
               'visual_acceptance': 'pending'}
    (output/'report.json').write_text(json.dumps(summary, indent=2)+'\n')
    print(json.dumps(summary), flush=True)


if __name__ == '__main__':
    main()
