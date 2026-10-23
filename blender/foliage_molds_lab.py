"""Adaptador RF2: extrae moldes Q3 originales y exporta solo hojas/conexiones."""
import argparse
import json
from pathlib import Path
import sys
import time

import bpy
from mathutils import Vector
from mathutils.bvhtree import BVHTree

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT/'src'), str(ROOT/'blender')]
from foliage_lab import configure, leaf_geometry, render, sha, write
from foliage_branch_lab import combine, export, mesh_from, record, wood_hash
from foliage_twigs_lab import check_inside
from foliage_fusion import extract
from generate_oak import material, mesh_report
from treegen.foliage import digest
from treegen.foliage_molds import (VERSION, budget, load_mold_spec, mold_placements,
    sample_surface, select_supports, validate_molds, connection_geometry)
from treegen.foliage_mold_density import (VERSION as DENSITY_VERSION, load_density,
    density_placements, budget as density_budget, TREE_TRIANGLE_LIMIT, BRANCH_ADDED_LIMIT)


def prepare(reference_path, cameras_path, output):
    ref = json.loads(reference_path.read_text())
    source = Path(ref['source'])
    assert ref['source_files_sha256'] == {name: sha(source/name) for name in ref['source_files_sha256']}
    bpy.ops.wm.open_mainfile(filepath=str(source/'tree.blend'), load_ui=False)
    mesh = bpy.data.objects['Oak'].data
    faces = [mesh.polygons[i] for i in ref['q3_leaf_source_polygon_indices']]
    # Componentes por índices compartidos: cada masa Q3 tiene vértices propios.
    parent = {}
    def find(i):
        parent.setdefault(i, i)
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i
    for face in faces:
        root = find(face.vertices[0])
        for i in face.vertices[1:]:
            parent[find(i)] = root
    components = {}
    for face in faces:
        components.setdefault(find(face.vertices[0]), []).append(face)
    molds = []
    for selected in sorted(components.values(), key=lambda fs: min(p.index for p in fs)):
        first = selected[0].vertices[0]
        level = mesh.attributes['q3_level'].data[first].value
        branch = mesh.attributes['q3_branch'].data[first].value
        branch_id = f'q3:{"primary" if level == 1 else "secondary"}:{branch}'
        assert branch_id in {b['id'] for b in ref['branches']}
        part = extract(mesh, selected, 'Q3_InvisibleMold')
        part.calc_loop_triangles()
        molds.append({'id': f'{branch_id}:mold:{min(p.index for p in selected):05d}',
            'parent_branch_id': branch_id, 'vertices': [list(v.co) for v in part.vertices],
            'triangles': [list(t.vertices) for t in part.loop_triangles],
            'source_polygon_indices': [p.index for p in selected]})
        bpy.data.meshes.remove(part)
    validate_molds(molds)
    assert sum(len(m['triangles']) for m in molds) == 300
    write(output/'molds.json', {'version': 'q3-branch-molds-0.1.0', 'reference_sha256': sha(reference_path),
        'source_files_sha256': ref['source_files_sha256'], 'molds': molds, 'molds_sha256': digest(molds),
        'cameras': json.loads(cameras_path.read_text())})


def callbacks(ref, molds):
    bvhs = {m['id']: BVHTree.FromPolygons(m['vertices'], m['triangles'], all_triangles=True) for m in molds}
    boxes = {m['id']: [[fn(v[k] for v in m['vertices']) for k in range(3)] for fn in (min, max)] for m in molds}
    branches = {b['id']: BVHTree.FromPolygons(b['mesh']['vertices'], b['mesh']['polygons']) for b in ref['branches']}
    direction = Vector((.3121, .7893, .5297)).normalized()

    def exposed(mold_id, point):
        for other, bvh in bvhs.items():
            if other == mold_id:
                continue
            low, high = boxes[other]
            if any(p < a or p > b for p, a, b in zip(point, low, high)):
                continue
            hit, normal, _, _ = bvh.ray_cast(Vector(point), direction)
            if hit is not None and normal.dot(direction) > 0:
                return False
        return True

    def project(mold_id, point):
        hit, normal, _, _ = bvhs[mold_id].find_nearest(Vector(point))
        return tuple(hit), tuple(normal)

    def parent_surface(branch_id, point):
        hit, normal, _, _ = branches[branch_id].find_nearest(Vector(point))
        return tuple(hit), tuple(normal)

    return exposed, project, parent_surface


def candidate(reference_path, molds_path, spec_path, output, no_render):
    started = time.monotonic()
    ref = json.loads(reference_path.read_text())
    frozen = json.loads(molds_path.read_text())
    assert frozen['reference_sha256'] == sha(reference_path)
    assert frozen['molds_sha256'] == digest(frozen['molds'])
    assert ref['source_files_sha256'] == {name: sha(Path(ref['source'])/name) for name in ref['source_files_sha256']}
    density = json.loads(spec_path.read_text()).get('version') == DENSITY_VERSION
    spec = load_density(spec_path) if density else load_mold_spec(spec_path)
    base = spec['base'] if density else spec
    exposed, project, parent_surface = callbacks(ref, frozen['molds'])
    candidates, diagnostics = sample_surface(base, frozen['molds'], exposed)
    carriers, selection = select_supports(base, candidates, project, parent_surface, exposed)
    diagnostics.update(selection)
    leaves = density_placements(spec, carriers) if density else mold_placements(spec, carriers)
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete(use_global=False)
    bark = material('Oak_Bark', ref['wood_material']['principled_base'][:3])
    bark.diffuse_color = ref['wood_material']['diffuse']
    bark.use_backface_culling = ref['wood_material']['backface_culling']
    bark.node_tree.nodes['Principled BSDF'].inputs['Roughness'].default_value = ref['wood_material']['roughness']
    wood = mesh_from(ref['wood_mesh'], 'RF2_ExactWood')
    wood.materials.append(bark)
    vertices, faces = [], []
    for leaf in leaves:
        coords, triangles = leaf_geometry(leaf)
        offset = len(vertices)
        vertices.extend(coords)
        faces.extend([i+offset for i in triangle] for triangle in triangles)
    leaf_material = material('RF1_Leaf', (.23, .43, .065))
    leaf_material.use_backface_culling = False
    combined = combine(wood, vertices, faces, leaf_material)
    data = record(combined)
    twig_start = len(data['polygons'])
    twig_records, twig_bvhs = [], {}
    for carrier in carriers:
        coords, triangles = connection_geometry(carrier, base)
        offset = len(data['vertices'])
        data['vertices'].extend(coords)
        data['polygons'].extend([[i+offset for i in triangle] for triangle in triangles])
        data['smooth'].extend([False]*len(triangles))
        twig_records.append({'id': carrier['id'], 'vertices': coords, 'triangles': triangles})
        twig_bvhs[carrier['id']] = BVHTree.FromPolygons(coords, triangles, all_triangles=True)
    mesh = mesh_from(data, 'RF2_MoldLeaves')
    for mat in combined.materials:
        mesh.materials.append(mat)
    twig_material = bark.copy()
    twig_material.name = 'RF2_Twig'
    mesh.materials.append(twig_material)
    for p in mesh.polygons:
        p.material_index = 2 if p.index >= twig_start else combined.polygons[p.index].material_index
    assert wood_hash(mesh) == ref['wood_sha256']
    for carrier in carriers:
        check_inside(twig_bvhs[carrier['id']], carrier['points_m'][0])
    for leaf in leaves:
        check_inside(twig_bvhs[leaf['support_id']], leaf['origin_m'])
    base_bvh = BVHTree.FromPolygons(ref['wood_mesh']['vertices'], ref['wood_mesh']['polygons'])
    insertion_errors = [base_bvh.find_nearest(Vector(c['points_m'][0]))[3] for c in carriers]
    assert max(insertion_errors) < .0001
    metrics = mesh_report(mesh)
    work = density_budget(spec) if density else budget(spec)
    assert metrics['triangles'] == 464+work['added_triangles']
    assert min(v.co.z for v in mesh.vertices) >= 0 and max(v.co.z for v in mesh.vertices) <= 9.00001
    obj = bpy.data.objects.new('RF2_MoldLeaves', mesh)
    bpy.context.collection.objects.link(obj)
    cameras = frozen['cameras']
    write(output/'cameras.json', cameras)
    generation_s = time.monotonic()-started
    if not no_render:
        render(obj, output, cameras)
    configure()
    export(obj, output)
    assert len([o for o in bpy.context.scene.objects if o.type == 'MESH']) == 1
    write(output/'manifest.json', {'version': DENSITY_VERSION if density else VERSION,
        'spec': spec, 'reference_sha256': sha(reference_path),
        'molds_sha256': frozen['molds_sha256'], 'molds_file_sha256': sha(molds_path),
        'wood_sha256': wood_hash(mesh), 'base_matrix_world': ref['matrix_world'],
        'output_matrix_world': [list(row) for row in obj.matrix_world], 'normalization': ref['normalization'],
        'base_seeds': ref['seeds'], 'leaf_count': len(leaves), 'group_count': len(carriers),
        'supports': carriers, 'supports_sha256': digest(carriers), 'placements': leaves,
        'placements_sha256': digest(leaves), 'twigs_sha256': digest(twig_records), 'metrics': metrics,
        'budget': work, 'sampling': diagnostics, 'cameras_sha256': digest(cameras),
        'triangle_limits': {'tree': TREE_TRIANGLE_LIMIT if density else 10000,
                            'branch_added': BRANCH_ADDED_LIMIT if density else 428},
        'contacts': {'all_insertions_on_q3_and_inside_twig': True, 'all_leaf_roots_inside_own_twig': True,
                     'max_insertion_error_m': max(insertion_errors)},
        'connection_lengths_m': {'minimum': min(c['length_m'] for c in carriers),
                                 'maximum': max(c['length_m'] for c in carriers)},
        'molds_exported': False, 'generation_before_render_export_s': generation_s,
        'total_s': time.monotonic()-started, 'glb_bytes': (output/'branch.glb').stat().st_size,
        'blender': bpy.app.version_string, 'blender_build': bpy.app.build_hash.decode(), 'blender_python': sys.version,
        'files_sha256': {name: sha(output/name) for name in ('branch.glb', 'scene.blend')}})


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('mode', choices=('prepare', 'candidate'))
    parser.add_argument('--reference', type=Path, required=True)
    parser.add_argument('--cameras', type=Path)
    parser.add_argument('--molds', type=Path)
    parser.add_argument('--spec', type=Path)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--no-render', action='store_true')
    args = parser.parse_args(sys.argv[sys.argv.index('--')+1:])
    assert bpy.app.version[:3] == (5, 2, 1)
    args.output.mkdir(parents=True, exist_ok=False)
    if args.mode == 'prepare':
        prepare(args.reference.resolve(), args.cameras.resolve(), args.output.resolve())
    else:
        candidate(args.reference.resolve(), args.molds.resolve(), args.spec.resolve(), args.output.resolve(), args.no_render)


if __name__ == '__main__':
    main()
