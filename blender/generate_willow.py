"""Adaptador del blueprint de sauce; recursos y representación de la rama aprobada."""
import json
from pathlib import Path
import sys
import time

import bpy

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT/'src'), str(ROOT/'blender')]
from treegen.pine_painted_sample import canonical_hash
from treegen.willow import build, budget, validate_resources
from willow_sample import painted
from pine_painted_sample import create, render as render_painted
from foliage_lab import write, sha, rig, configure
from foliage_canopy_lab import export_tree, projection_clips
from generate_oak import mesh_report


def generate(job):
    started = time.monotonic()
    r = job['resolved_blueprint']
    frozen = dict(r)
    assert frozen.pop('resolved_sha256') == canonical_hash(frozen)
    assert job['spec'] == r['base_spec'] and job['seeds'] == r['base_seeds']
    assert job['spec_sha256'] == canonical_hash(job['spec'])
    validate_resources(r['resources'])
    assert budget(r['parameters'], r['limits'], version=r['base_spec']['algorithm_version']) == r['budget_upper_bound']
    out = Path(job['output'])
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete(use_global=False)
    for mat in list(bpy.data.materials):
        bpy.data.materials.remove(mat)
    branches, wood, groups = build(r)
    bark, leaf = painted('Painted_Bark', 'bark.png'), painted('Painted_Foliage', 'foliage.png', True)
    pieces = [(b['mesh'], 0, b['uv']) for b in wood]+[(g, 1, g['uv']) for g in groups]
    obj = create('PaintedWillow', pieces, [bark, leaf])
    for polygon in obj.data.polygons:
        polygon.use_smooth = polygon.material_index == 0
    metrics = mesh_report(obj.data, triangle_limit=r['limits']['triangles'])
    assert metrics['triangles'] <= r['budget_upper_bound']['triangles_max'] < 7000
    low, high = metrics['bounds_blender']
    cameras = rig([(a+b)/2 for a, b in zip(low, high)], max(b-a for a, b in zip(low, high)), r['parameters']['base']['height_m'])
    for settings in cameras.values():
        settings['resolution'] = [480, 480]
    write(out/'base-reference.json', {'version': 'willow-reference-0.1.0', 'branches': branches,
          'retained_ids': [b['id'] for b in wood], 'wood_optimization': {b['id']: b['wood_optimization'] for b in wood}})
    write(out/'placements.json', groups)
    write(out/'cameras.json', cameras)
    configure()
    scene = bpy.context.scene
    scene.render.engine = 'CYCLES'
    scene.cycles.samples = 4
    scene.cycles.device = 'CPU'
    scene.cycles.use_denoising = False
    scene.render.resolution_x = scene.render.resolution_y = 480
    scene.render.threads_mode = 'FIXED'
    scene.render.threads = 1
    scene.world.use_nodes = True
    scene.world.node_tree.nodes['Background'].inputs[0].default_value = (.35, .35, .35, 1)
    scene.world.node_tree.nodes['Background'].inputs[1].default_value = .35
    sun = bpy.data.objects.new('WillowReviewSun', bpy.data.lights.new('WillowReviewSun', 'SUN'))
    bpy.context.collection.objects.link(sun)
    sun.rotation_euler = (.45, -.5, -.5)
    sun.data.energy = .75
    if job['render']:
        render_painted(obj, out, cameras)
    for image in bpy.data.images:
        if image.source == 'FILE':
            image.pack()
    export_tree(obj, out)
    wood_obj = create('PaintedWood', pieces[:len(wood)], [bark])
    for polygon in wood_obj.data.polygons:
        polygon.use_smooth = True
    write(out/'wood-metrics.json', mesh_report(wood_obj.data, triangle_limit=6999))
    bpy.ops.object.select_all(action='DESELECT')
    wood_obj.select_set(True)
    bpy.context.view_layer.objects.active = wood_obj
    bpy.ops.export_scene.gltf(filepath=str(out/'wood.glb'), export_format='GLB', use_selection=True, export_yup=True)
    sources = {Path(m.__file__).resolve() for m in list(sys.modules.values()) if getattr(m, '__file__', None) and str(m.__file__).endswith('.py')}
    sources.update((ROOT/'schemas').glob('*.json'))
    manifest = {'status': 'completed', 'kind': 'blueprint', 'adapter_version': 'willow-blender-0.1.0',
        'version': 'willow-painted-crossed-'+r['blueprint_definition']['components']['representation'].split('@')[1], 'spec': job['spec'], 'spec_sha256': job['spec_sha256'],
        'seeds': job['seeds'], 'base_seeds': r['base_seeds'], 'canopy_spec': r['canopy_spec'], 'resolved_blueprint': r,
        'metrics': metrics, 'cameras': cameras, 'projection_clips': projection_clips(obj.data, cameras),
        'wood_sha256': canonical_hash([b['mesh'] for b in wood]), 'placements_sha256': canonical_hash(groups),
        'branch_count': len(wood), 'group_count': len(groups), 'paint_seed': r['paint_seed'], 'resources': r['resources'],
        'budget': r['budget_upper_bound'], 'external_geometry_inputs': [], 'base_generation': 'willow_paths_in_memory',
        'runner_python': job['runner_python'], 'jsonschema_version': job['jsonschema_version'],
        'blender': bpy.app.version_string, 'blender_build': bpy.app.build_hash.decode(), 'blender_python': sys.version,
        'sources_sha256': {str(p.relative_to(ROOT)): sha(p) for p in sorted(sources) if p.is_relative_to(ROOT)},
        'glb_sha256': sha(out/'tree.glb'), 'glb_bytes': (out/'tree.glb').stat().st_size,
        'generation_before_finalize_s': time.monotonic()-started,
        'files_sha256': {name: sha(out/name) for name in ('tree.glb', 'tree.blend', 'placements.json', 'wood.glb', 'wood-metrics.json')}}
    write(out/'manifest.json', manifest)


if __name__ == '__main__':
    assert bpy.app.version[:3] == (5, 2, 1)
    generate(json.loads(Path(sys.argv[sys.argv.index('--')+1]).read_text()))
