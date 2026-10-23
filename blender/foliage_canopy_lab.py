"""RF3: madera completa Q3 congelada, moldes globales y copa exportable."""
import argparse
import json
from pathlib import Path
import sys
import time

import bpy
from mathutils import Vector
from mathutils.kdtree import KDTree
from mathutils.bvhtree import BVHTree

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT/'src'), str(ROOT/'blender')]
from foliage_lab import configure, evaluated, leaf_geometry, render, sha, write
from foliage_branch_lab import combine, mesh_from, record, wood_hash
from foliage_molds_lab import callbacks
from foliage_fusion import extract
from generate_oak import material, mesh_report
from oak_nodes import Graph, GEO
from treegen.foliage import digest
from treegen.foliage_molds import connection_geometry
from treegen.foliage_canopy import (VERSION, budget, load_canopy, profile_molds,
    sample_exposed, select_canopy, validate_guides, TREE_TRIANGLE_LIMIT)


def components(mesh, faces):
    parents = {}
    def find(i):
        parents.setdefault(i, i)
        while parents[i] != i:
            parents[i] = parents[parents[i]]
            i = parents[i]
        return i
    for face in faces:
        for i in face.vertices[1:]:
            parents[find(i)] = find(face.vertices[0])
    groups = {}
    for face in faces:
        groups.setdefault(find(face.vertices[0]), []).append(face)
    return sorted(groups.values(), key=lambda fs: min(p.index for p in fs))


def export_tree(obj, output):
    bpy.ops.object.select_all(action='DESELECT')
    obj.hide_set(False)
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    bpy.ops.export_scene.gltf(filepath=str(output/'tree.glb'), export_format='GLB', use_selection=True, export_yup=True)
    bpy.ops.wm.save_as_mainfile(filepath=str(output/'tree.blend'))


def projection_clips(mesh, cameras):
    result = {}
    for name, camera in cameras.items():
        count = 0
        for vertex in mesh.vertices:
            local = [x-y for x, y in zip(vertex.co, camera['location'])]
            if any(abs(sum(x*y for x, y in zip(local, axis))) > camera['ortho_scale']*.5+.0001
                   for axis in camera['basis_columns'][:2]):
                count += 1
        result[name] = {'vertices_outside_frame': count, 'intentional_detail': name.startswith('detail-')}
    return result


def tube_planes(coords, triangles):
    # Los tubos rectos son prismas truncados convexos. Cada cara exterior
    # delimita un semiespacio; esto evita depender de una dirección de rayo.
    points = [Vector(v) for v in coords]
    return [(points[a], (points[b]-points[a]).cross(points[c]-points[a]).normalized()) for a, b, c in triangles]


def check_tube(planes, point):
    distance = max(normal.dot(Vector(point)-origin) for origin, normal in planes)
    if distance > 1e-6:
        raise ValueError(f'Raíz fuera del tubo convexo: {distance} m')
    return distance


def prepare(rf0_path, acceptance_path, output):
    rf0 = json.loads(rf0_path.read_text())
    accepted = json.loads(acceptance_path.read_text())
    case = Path(accepted['case_directory'])
    assert accepted['decision'] == 'approved_by_user' and accepted['case'] == 'leaves-144'
    assert sha(case/'manifest.json') == accepted['manifest_sha256'] and sha(case/'branch.glb') == accepted['glb_sha256']
    source = Path(rf0['source'])
    assert rf0['source_files_sha256'] == {name: sha(source/name) for name in rf0['source_files_sha256']}
    original_manifest = json.loads((source/'manifest.json').read_text())
    bpy.ops.wm.open_mainfile(filepath=str(source/'tree.blend'), load_ui=False)
    obj = bpy.data.objects['Oak']
    original = obj.data
    assert mesh_report(original) == original_manifest['metrics']
    wood_faces = [p for p in original.polygons if original.materials[p.material_index].name == 'Oak_Bark']
    wood_ids = sorted({i for p in wood_faces for i in p.vertices})
    kd = KDTree(len(wood_ids))
    for i in wood_ids:
        kd.insert(original.vertices[i].co, i)
    kd.balance()
    generator = bpy.data.objects['OakProcedural'].modifiers[0].node_group
    structure = next(n.node_tree for n in generator.nodes if n.type == 'GROUP' and n.node_tree.name.startswith('Oak_Structure'))
    volume = next(n.node_tree for n in generator.nodes if n.type == 'GROUP' and n.node_tree.name.startswith('Oak_Volume'))
    primary_count = original_manifest['spec']['parameters']['primary_branches']
    branches, assigned, reconstruction_error = [], set(), 0.
    for channel, count, kind, base_id in [('Trunk', 1, 'trunk', 0), ('Primary', primary_count, 'primary', 100),
                                         ('Secondary', primary_count*3, 'secondary', 200)]:
        graph = Graph('RF3_OriginalChannel', [], [('Geometry', GEO)])
        node = graph.group(structure)
        for item in structure.interface.items_tree:
            if item.item_type == 'SOCKET' and item.in_out == 'INPUT':
                graph.set(node, item.name, original_manifest['socket_values'][item.name])
        marker = graph.node('GeometryNodeStoreNamedAttribute', domain='CURVE', data_type='INT')
        graph.set(marker, 'Geometry', node.outputs[channel])
        graph.set(marker, 'Name', 'rf3_curve_index')
        graph.set(marker, 'Value', graph.node('GeometryNodeInputIndex').outputs['Index'])
        mesh = graph.group(volume, Curves=marker.outputs['Geometry'], Bark=bpy.data.materials['Oak_Bark'])
        graph.set(mesh, 'Profile Resolution', 8)
        transform = graph.node('GeometryNodeTransform')
        graph.set(transform, 'Geometry', mesh.outputs['Mesh'])
        graph.set(transform, 'Scale', original_manifest['normalization']['scale'])
        graph.set(transform, 'Translation', original_manifest['normalization']['translation'])
        graph.set(graph.output, 'Geometry', transform.outputs['Geometry'])
        estimated = evaluated(graph)
        assert 'rf3_curve_index' in estimated.attributes
        by_index = {i: set() for i in range(count)}
        for v in estimated.vertices:
            _, original_index, error = kd.find(v.co)
            reconstruction_error = max(reconstruction_error, error)
            assert error < .00001
            by_index[estimated.attributes['rf3_curve_index'].data[v.index].value].add(original_index)
        for index in range(count):
            selected = [p for p in wood_faces if all(i in by_index[index] for i in p.vertices)]
            assert selected
            indices = {p.index for p in selected}
            assert not assigned.intersection(indices)
            assigned.update(indices)
            frozen = extract(original, selected, 'RF3_FrozenBranch')
            parent_id = None if kind == 'trunk' else 'q3:trunk:0' if kind == 'primary' else f'q3:primary:{100+index//3}'
            branches.append({'id': f'q3:{kind}:{base_id+index}', 'parent_id': parent_id,
                'mesh': record(frozen), 'source_polygon_indices': sorted(indices)})
            bpy.data.meshes.remove(frozen)
        bpy.data.meshes.remove(estimated)
    assert assigned == {p.index for p in wood_faces} and len(branches) <= 49
    wood = extract(original, wood_faces, 'RF3_ExactWood')
    wood.materials.append(bpy.data.materials['Oak_Bark'])
    molds = []
    leaf_faces = [p for p in original.polygons if original.materials[p.material_index].name == 'Oak_Leaves']
    for selected in components(original, leaf_faces):
        first = selected[0].vertices[0]
        level = original.attributes['q3_level'].data[first].value
        branch = original.attributes['q3_branch'].data[first].value
        kind = ('trunk', 'primary', 'secondary')[level]
        branch_id = f'q3:{kind}:{branch}'
        assert branch_id in {b['id'] for b in branches}
        part = extract(original, selected, 'RF3_InvisibleMold')
        part.calc_loop_triangles()
        molds.append({'id': f'{branch_id}:mold:{min(p.index for p in selected):05d}',
            'parent_branch_id': branch_id, 'vertices': [list(v.co) for v in part.vertices],
            'triangles': [list(t.vertices) for t in part.loop_triangles],
            'source_polygon_indices': [p.index for p in selected]})
        bpy.data.meshes.remove(part)
    validate_guides(molds)
    assert len(molds) == 89 and sum(len(m['triangles']) for m in molds) == 3220
    points = [v for m in molds for v in m['vertices']]
    bounds = [[fn(v[k] for v in points) for k in range(3)] for fn in (min, max)]
    center = [(a+b)/2 for a, b in zip(*bounds)]
    cameras = rf0['tree_cameras']
    cameras.update({k: v for k, v in json.loads((case/'cameras.json').read_text()).items() if k.startswith('detail-')})
    write(output/'cameras.json', cameras)
    ref = {'version': 'rf3-q3-reference-0.1.0', 'case': 'viejo-09', 'source': str(source),
        'source_files_sha256': rf0['source_files_sha256'], 'rf0_sha256': sha(rf0_path),
        'rf2_acceptance_sha256': sha(acceptance_path), 'accepted_rf2_spec': json.loads((case/'manifest.json').read_text())['spec'],
        'spec': original_manifest['spec'], 'seeds': original_manifest['seeds'],
        'normalization': original_manifest['normalization'], 'matrix_world': [list(row) for row in obj.matrix_world],
        'wood_mesh': record(wood), 'wood_sha256': wood_hash(original), 'wood_material': rf0['materials']['Oak_Bark'],
        'wood_triangles': mesh_report(wood)['triangles'], 'wood_source_polygon_indices': sorted(assigned),
        'branches': branches, 'molds': molds, 'molds_sha256': digest(molds),
        'profile_center_m': center, 'profile_bounds_m': bounds, 'height_m': 9.,
        'max_reconstruction_error_m': reconstruction_error, 'cameras': cameras, 'lighting': rf0['lighting']}
    write(output/'reference.json', ref)
    render(obj, output, cameras)
    export_tree(obj, output)
    write(output/'manifest.json', {'version': 'q3-reference-0.4.0', 'metrics': mesh_report(original),
        'wood_sha256': wood_hash(original), 'cameras_sha256': digest(cameras),
        'projection_clips': projection_clips(original, cameras),
        'files_sha256': {n: sha(output/n) for n in ('tree.glb', 'tree.blend')}})


def candidate(reference_path, spec_path, output, no_render, layout_leaf_length_m):
    started = time.monotonic()
    ref = json.loads(reference_path.read_text())
    spec = load_canopy(spec_path)
    maximum = budget(ref['wood_triangles'], spec['group_count'])
    assert ref['source_files_sha256'] == {name: sha(Path(ref['source'])/name) for name in ref['source_files_sha256']}
    guides = profile_molds(spec, ref['molds'], ref['profile_center_m'])
    exposed, _, parent_surface = callbacks(ref, guides)
    pool, sampling = sample_exposed(spec, guides, ref['profile_center_m'], exposed)
    carriers, leaves, selection = select_canopy(spec, pool, parent_surface, ref['height_m'], layout_leaf_length_m=layout_leaf_length_m)
    work = budget(ref['wood_triangles'], len(carriers))
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete(use_global=False)
    bark = material('Oak_Bark', ref['wood_material']['principled_base'][:3])
    bark.diffuse_color = ref['wood_material']['diffuse']
    bark.use_backface_culling = ref['wood_material']['backface_culling']
    bark.node_tree.nodes['Principled BSDF'].inputs['Roughness'].default_value = ref['wood_material']['roughness']
    wood = mesh_from(ref['wood_mesh'], 'RF3_ExactWood')
    wood.materials.append(bark)
    vertices, faces = [], []
    for leaf in leaves:
        coords, triangles = leaf_geometry(leaf)
        offset = len(vertices)
        vertices.extend(coords)
        faces.extend([i+offset for i in t] for t in triangles)
    leaf_mat = material('RF1_Leaf', (.23, .43, .065))
    leaf_mat.use_backface_culling = False
    combined = combine(wood, vertices, faces, leaf_mat)
    data = record(combined)
    twig_start = len(data['polygons'])
    twig_bvhs, planes_by_twig, twig_records = {}, {}, []
    for carrier in carriers:
        coords, triangles = connection_geometry(carrier, spec)
        offset = len(data['vertices'])
        data['vertices'].extend(coords)
        data['polygons'].extend([[i+offset for i in t] for t in triangles])
        data['smooth'].extend([False]*len(triangles))
        twig_bvhs[carrier['id']] = BVHTree.FromPolygons(coords, triangles, all_triangles=True)
        planes_by_twig[carrier['id']] = tube_planes(coords, triangles)
        twig_records.append({'id': carrier['id'], 'vertices': coords, 'triangles': triangles})
    mesh = mesh_from(data, 'RF3_Canopy')
    for mat in combined.materials:
        mesh.materials.append(mat)
    twig_mat = bark.copy()
    twig_mat.name = 'RF2_Twig'
    mesh.materials.append(twig_mat)
    for p in mesh.polygons:
        p.material_index = 2 if p.index >= twig_start else combined.polygons[p.index].material_index
    assert wood_hash(mesh) == ref['wood_sha256']
    for carrier in carriers:
        check_tube(planes_by_twig[carrier['id']], carrier['points_m'][0])
    maximum_signed_distance, legacy_long_rays = -1., 0
    for leaf in leaves:
        maximum_signed_distance = max(maximum_signed_distance,
            check_tube(planes_by_twig[leaf['support_id']], leaf['origin_m']))
        # Diagnóstico del comprobador RF2: un rayo casi paralelo al tubo podía
        # recorrer >.15 m desde un punto interior y rechazar una raíz válida.
        direction = Vector((.3121, .7893, .5297)).normalized()
        hit, normal, _, distance = twig_bvhs[leaf['support_id']].ray_cast(Vector(leaf['origin_m']), direction)
        if hit is not None and normal.dot(direction) > 0 and distance > .15:
            legacy_long_rays += 1
    base_bvh = BVHTree.FromPolygons(ref['wood_mesh']['vertices'], ref['wood_mesh']['polygons'])
    errors = [base_bvh.find_nearest(Vector(c['points_m'][0]))[3] for c in carriers]
    assert max(errors) < .0001
    metrics = mesh_report(mesh, triangle_limit=TREE_TRIANGLE_LIMIT)
    assert metrics['triangles'] == work['triangles'] <= maximum['triangles']
    assert min(v.co.z for v in mesh.vertices) >= -1e-5 and max(v.co.z for v in mesh.vertices) <= ref['height_m']+1e-5
    obj = bpy.data.objects.new('RF3_Oak', mesh)
    bpy.context.collection.objects.link(obj)
    write(output/'cameras.json', ref['cameras'])
    generation_s = time.monotonic()-started
    if not no_render:
        render(obj, output, ref['cameras'])
    configure()
    export_tree(obj, output)
    assert len([o for o in bpy.context.scene.objects if o.type == 'MESH']) == 1
    write(output/'manifest.json', {'version': VERSION, 'spec': spec, 'reference_sha256': sha(reference_path),
        'accepted_rf2_spec': ref['accepted_rf2_spec'], 'wood_sha256': wood_hash(mesh),
        'base_spec': ref['spec'], 'normalization': ref['normalization'], 'base_seeds': ref['seeds'],
        'base_matrix_world': ref['matrix_world'], 'output_matrix_world': [list(row) for row in obj.matrix_world],
        'molds_sha256': digest(guides), 'molds_exported': False,
        'metrics': metrics, 'budget': work, 'budget_before_selection': maximum,
        'support_count': len(carriers), 'leaf_count': len(leaves), 'sampling': sampling, 'selection': selection,
        'supports': carriers, 'supports_sha256': digest(carriers), 'placements': leaves,
        'placements_sha256': digest(leaves), 'twigs_sha256': digest(twig_records),
        'contacts': {'all_insertions_on_q3_and_inside_twig': True, 'all_leaf_roots_inside_own_twig': True,
                     'max_insertion_error_m': max(errors), 'method': 'convex_tube_face_halfspaces',
                     'maximum_leaf_signed_face_distance_m': maximum_signed_distance,
                     'legacy_fixed_ray_long_paths': legacy_long_rays},
        'height_check': {'requested_m': ref['height_m'], 'actual_m': metrics['height_m'], 'tolerance_m': .0001},
        'layout_leaf_length_m': layout_leaf_length_m or spec['leaf_length_m'], 'cameras_sha256': digest(ref['cameras']),
        'projection_clips': projection_clips(mesh, ref['cameras']),
        'blender': bpy.app.version_string, 'blender_build': bpy.app.build_hash.decode(), 'blender_python': sys.version,
        'generation_before_render_export_s': generation_s, 'total_s': time.monotonic()-started,
        'glb_bytes': (output/'tree.glb').stat().st_size,
        'files_sha256': {n: sha(output/n) for n in ('tree.glb', 'tree.blend')}})


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('mode', choices=('prepare', 'candidate'))
    parser.add_argument('--rf0', type=Path, default=ROOT/'docs/evidence/rf0-rf1/reference-lock.json')
    parser.add_argument('--acceptance', type=Path, default=ROOT/'docs/evidence/rediseno-follaje/rf2-densidad/aceptacion.json')
    parser.add_argument('--reference', type=Path)
    parser.add_argument('--spec', type=Path)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--no-render', action='store_true')
    parser.add_argument('--layout-leaf-length-m', type=float)
    args = parser.parse_args(sys.argv[sys.argv.index('--')+1:])
    assert bpy.app.version[:3] == (5, 2, 1)
    args.output.mkdir(parents=True, exist_ok=False)
    if args.mode == 'prepare':
        prepare(args.rf0.resolve(), args.acceptance.resolve(), args.output.resolve())
    else:
        candidate(args.reference.resolve(), args.spec.resolve(), args.output.resolve(), args.no_render, args.layout_leaf_length_m)


if __name__ == '__main__':
    main()
