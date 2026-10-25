"""Adaptador Blender del pino experimental; usa el ejecutor y exportador comunes."""
import json
import hashlib
from pathlib import Path
import sys
import time

import bpy

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT/'src'), str(ROOT/'blender')]
from treegen.pine import build_pine, check_parameters
from generate_blueprint import apply_material
from generate_oak import mesh_report
from foliage_lab import write, sha, configure, rig, render
from foliage_canopy_lab import export_tree, projection_clips
from foliage_branch_lab import mesh_from, record


def canonical_hash(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':'),
                                    ensure_ascii=False, allow_nan=False).encode()).hexdigest()


def generate(job):
    started = time.monotonic()
    r = job['resolved_blueprint']
    frozen = dict(r)
    expected_hash = frozen.pop('resolved_sha256')
    assert canonical_hash(frozen) == expected_hash, 'Resolución alterada'
    import fastjsonschema
    schema = json.loads((ROOT/'schemas/tree-blueprint-pine.schema.json').read_text())
    fastjsonschema.compile(schema['$defs']['parameters'])(r['parameters'])
    version = r['base_spec']['algorithm_version']
    assert version in ('0.1.0','0.2.0')
    assert r['blueprint_definition']['components'] == {
        'base':'pine-whorls@'+version, 'distribution':'pine-distal@0.1.0', 'representation':'pine-needle-pairs@0.1.0'}
    assert check_parameters(r['parameters'],r['limits']) == r['budget_upper_bound']
    assert job['spec'] == r['base_spec'] and job['seeds'] == r['base_seeds']
    assert r['base_spec']['algorithm'] == 'pine-whorls'
    assert job['spec_sha256'] == canonical_hash(job['spec'])
    out = Path(job['output'])
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete(use_global=False)
    for mat in list(bpy.data.materials):
        bpy.data.materials.remove(mat)
    bark = apply_material('Pine_Bark', r['appearance']['bark'])
    leaf_mat = apply_material('Pine_Needles', r['appearance']['leaf'])
    branches, needles = build_pine(r)
    vertices, faces = [], []
    for b in branches:
        offset = len(vertices)
        vertices.extend(b['mesh']['vertices'])
        faces.extend([[i+offset for i in f] for f in b['mesh']['polygons']])
    wood = mesh_from({'vertices':vertices, 'polygons':faces, 'smooth':[False]*len(faces)}, 'PineWood')
    wood.materials.append(bark)
    wood_data = record(wood)
    wood_triangles = len(faces)
    for needle in needles:
        offset = len(vertices)
        vertices.extend(needle['vertices'])
        faces.extend([[i+offset for i in f] for f in needle['triangles']])
    mesh = mesh_from({'vertices':vertices, 'polygons':faces, 'smooth':[False]*len(faces)}, 'PineTree')
    mesh.materials.append(bark)
    mesh.materials.append(leaf_mat)
    for p in mesh.polygons:
        p.material_index = int(p.index >= wood_triangles)
    metrics = mesh_report(mesh, triangle_limit=r['limits']['triangles'])
    assert metrics['triangles'] == r['budget_upper_bound']['triangles_max']
    assert abs(metrics['height_m']-r['parameters']['base']['height_m']) < .0001
    obj = bpy.data.objects.new('Pine', mesh)
    bpy.context.collection.objects.link(obj)
    low, high = metrics['bounds_blender']
    center = [(a+b)/2 for a,b in zip(low,high)]
    # Encuadre de inspección, separado de los parámetros generativos.
    cameras = rig(center, max(b-a for a,b in zip(low,high)), metrics['height_m'])
    ref = {'version':'pine-reference-0.1.0', 'wood_mesh':wood_data,
           'wood_sha256':canonical_hash(wood_data), 'branches':branches,
           'wood_triangles':wood_triangles, 'height_m':metrics['height_m'], 'cameras':cameras}
    write(out/'base-reference.json',ref)
    write(out/'cameras.json',cameras)
    if job['render']:
        render(obj,out,cameras)
    configure()
    export_tree(obj,out)
    sources = {Path(m.__file__).resolve() for m in list(sys.modules.values())
               if getattr(m,'__file__',None) and str(m.__file__).endswith('.py')}
    sources.update((ROOT/'schemas').glob('*.json'))
    manifest = {'status':'completed', 'kind':'blueprint', 'adapter_version':'pine-blender-0.1.0',
        'version':'pine-whorls-'+version, 'spec':job['spec'], 'spec_sha256':job['spec_sha256'],
        'seeds':job['seeds'], 'base_seeds':r['base_seeds'], 'canopy_spec':r['canopy_spec'],
        'resolved_blueprint':r, 'metrics':metrics, 'cameras':cameras,
        'projection_clips':projection_clips(mesh,cameras),
        'wood_sha256':canonical_hash(wood_data), 'branch_count':len(branches), 'leaf_count':len(needles),
        'placements':[{'support_id':n['support_id'],'origin_m':n['origin_m']} for n in needles],
        'placements_sha256':canonical_hash(needles), 'budget':r['budget_upper_bound'],
        'external_geometry_inputs':[], 'base_generation':'pine_in_memory',
        'runner_python':job['runner_python'], 'jsonschema_version':job['jsonschema_version'],
        'blender':bpy.app.version_string, 'blender_build':bpy.app.build_hash.decode(), 'blender_python':sys.version,
        'sources_sha256':{str(p.relative_to(ROOT)):sha(p) for p in sorted(sources) if p.is_relative_to(ROOT)},
        'glb_sha256':sha(out/'tree.glb'), 'glb_bytes':(out/'tree.glb').stat().st_size,
        'generation_before_finalize_s':time.monotonic()-started,
        'files_sha256':{n:sha(out/n) for n in ('tree.glb','tree.blend')}}
    write(out/'manifest.json',manifest)
    print(json.dumps(metrics))


if __name__ == '__main__':
    assert bpy.app.version[:3] == (5,2,1)
    generate(json.loads(Path(sys.argv[sys.argv.index('--')+1]).read_text()))
