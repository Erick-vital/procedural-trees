"""B2: base Q3 en memoria y representación RF3, sin entradas de laboratorio."""
import hashlib
import json
from pathlib import Path
import sys
import time

import bpy
from mathutils import Vector
from mathutils.kdtree import KDTree
from mathutils.bvhtree import BVHTree

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / 'src'), str(ROOT / 'blender')]
from generate_oak import material, mesh_report, evaluated_output
from oak_nodes import Graph, GEO, PARAMETERS
from oak_nodes_v4 import build_generator
from foliage_lab import evaluated, leaf_geometry, render, configure, write, sha
from foliage_branch_lab import combine, mesh_from, record, wood_hash
from foliage_fusion import extract
from foliage_molds_lab import callbacks
from foliage_canopy_lab import components, tube_planes, check_tube, projection_clips, export_tree
from mesh_contacts import insertion_errors, CONTACT_TOLERANCE_M
from treegen.foliage import digest
from treegen.foliage_canopy import (VERSION, budget, validate_canopy, validate_guides,
                                  profile_molds, sample_exposed, select_canopy)
from treegen.foliage_molds import connection_geometry


def apply_material(name, settings):
    mat = material(name, settings['color_rgba'][:3])
    mat.diffuse_color = settings['color_rgba']
    mat.use_backface_culling = not settings['double_sided']
    shader = mat.node_tree.nodes['Principled BSDF']
    shader.inputs['Roughness'].default_value = settings['roughness']
    shader.inputs['Metallic'].default_value = settings['metallic']
    return mat


def base_reference(resolved, cameras):
    spec, params = resolved['base_spec'], resolved['base_spec']['parameters']
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete(use_global=False)
    bark = apply_material('Oak_Bark', resolved['appearance']['bark'])
    leaves = apply_material('Oak_Leaves', resolved['appearance']['leaf'])
    generator, _ = build_generator(bark, leaves)
    obj = bpy.data.objects.new('OakProcedural', bpy.data.meshes.new('OakHost'))
    bpy.context.collection.objects.link(obj)
    modifier = obj.modifiers.new('OakGenerator', 'NODES')
    modifier.node_group = generator.tree
    values = {PARAMETERS[k][0]: v for k, v in params.items()}
    values.update({'Structure Seed': resolved['base_seeds']['structure'],
                   'Foliage Seed': resolved['base_seeds']['foliage'], 'Profile Resolution': 8})
    for name, value in values.items():
        getattr(modifier.properties.inputs, generator.sockets[name]).value = value
    obj.update_tag()
    bpy.context.view_layer.update()
    depsgraph = bpy.context.evaluated_depsgraph_get()
    original = bpy.data.meshes.new_from_object(obj.evaluated_get(depsgraph), depsgraph=depsgraph)
    raw = evaluated_output(generator, values, 'Raw Wood')
    bounds = mesh_report(raw)['bounds_blender']
    scale_z = params['height_m'] / (bounds[1][2] - bounds[0][2])
    normalization = {'basis': 'wood_bounds', 'raw_bounds_blender': bounds,
                     'scale': [1, 1, scale_z], 'translation': [0, 0, -bounds[0][2] * scale_z]}
    bpy.data.meshes.remove(raw)
    original_manifest = {'spec': spec, 'socket_values': values, 'normalization': normalization}
    structure = next(n.node_tree for n in generator.tree.nodes if n.type == 'GROUP'
                     and n.node_tree.name.startswith('Oak_Structure'))
    volume = next(n.node_tree for n in generator.tree.nodes if n.type == 'GROUP'
                  and n.node_tree.name.startswith('Oak_Volume'))
    wood_faces = [p for p in original.polygons if original.materials[p.material_index].name == 'Oak_Bark']
    wood_ids = sorted({i for p in wood_faces for i in p.vertices})
    kd = KDTree(len(wood_ids))
    for i in wood_ids:
        kd.insert(original.vertices[i].co, i)
    kd.balance()
    primary_count = original_manifest['spec']['parameters']['primary_branches']
    branches, assigned, reconstruction_error = [], set(), 0.
    for channel, count, kind, base_id in [('Trunk', 1, 'trunk', 0), ('Primary', primary_count, 'primary', 100),
                                         ('Secondary', primary_count*3 if params['max_depth'] == 2 else 0, 'secondary', 200)]:
        if count == 0:
            continue
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
    points = [v for m in molds for v in m['vertices']]
    bounds = [[fn(v[k] for v in points) for k in range(3)] for fn in (min, max)]
    center = [(a+b)/2 for a, b in zip(*bounds)]
    return {'version': 'q3-generated-reference-1.0.0', 'spec': spec,
            'seeds': resolved['base_seeds'], 'normalization': normalization,
            'matrix_world': [list(row) for row in obj.matrix_world],
            'wood_mesh': record(wood), 'wood_sha256': wood_hash(original),
            'wood_triangles': mesh_report(wood)['triangles'],
            'branches': branches, 'molds': molds, 'molds_sha256': digest(molds),
            'profile_center_m': center, 'profile_bounds_m': bounds,
            'height_m': params['height_m'], 'cameras': cameras,
            'max_reconstruction_error_m': reconstruction_error}


def generate(job):
    started = time.monotonic()
    resolved = job['resolved_blueprint']
    check = dict(resolved)
    expected_hash = check.pop('resolved_sha256')
    actual_hash = hashlib.sha256(json.dumps(check, sort_keys=True, separators=(',', ':'),
                                          ensure_ascii=False, allow_nan=False).encode()).hexdigest()
    assert actual_hash == expected_hash, 'Resolución alterada'
    components = resolved['blueprint_definition']['components']
    assert components['base'] == 'oak_geometry_nodes@0.4.0'
    assert components['representation'] == 'rf3-diamond-six@0.1.0'
    assert components['distribution'] in ('foliage-canopy@0.1.0', 'foliage-canopy@0.1.1')
    assert resolved['base_spec'] == job['spec'] and resolved['base_seeds'] == job['seeds']
    # Defensa del adaptador incluso si se invoca directamente.
    import fastjsonschema
    base_schema = json.loads((ROOT / 'schemas/tree-spec.schema.json').read_text())
    fastjsonschema.compile(base_schema)(job['spec'])
    assert job['spec']['algorithm_version'] == '0.4.0'
    spec = validate_canopy(resolved['canopy_spec'])
    assert spec['version'] == 'foliage-canopy-' + components['distribution'].split('@')[1]
    corrected = spec['version'] == 'foliage-canopy-0.1.1'
    triangle_limit = resolved['limits']['triangles']
    assert type(triangle_limit) is int and 1 <= triangle_limit <= 12500
    assert .2 <= resolved['layout_leaf_length_m'] <= 1
    output = Path(job['output']).resolve()
    inspection_path = ROOT / 'configs/inspection/rf3-v1.json'
    cameras = json.loads(inspection_path.read_text())['cameras']
    ref = base_reference(resolved, cameras)
    write(output / 'base-reference.json', ref)
    maximum = budget(ref['wood_triangles'], spec['group_count'])
    assert maximum['triangles'] <= triangle_limit
    layout_leaf_length_m = resolved['layout_leaf_length_m']
    no_render = not job['render']
    guides = profile_molds(spec, ref['molds'], ref['profile_center_m'])
    exposed, _, parent_surface = callbacks(ref, guides)
    projection = {'version': 'legacy-polygons-0.1.0', 'corrected_queries': 0}
    if corrected:
        from blueprint_surfaces import corrected_parent_surface
        parent_surface, projection = corrected_parent_surface(ref, parent_surface)
    pool, sampling = sample_exposed(spec, guides, ref['profile_center_m'], exposed)
    carriers, leaves, selection = select_canopy(spec, pool, parent_surface, ref['height_m'], layout_leaf_length_m=layout_leaf_length_m)
    work = budget(ref['wood_triangles'], len(carriers))
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete(use_global=False)
    for mat in list(bpy.data.materials):
        bpy.data.materials.remove(mat)
    bark = apply_material('Oak_Bark', resolved['appearance']['bark'])
    wood = mesh_from(ref['wood_mesh'], 'RF3_ExactWood')
    wood.materials.append(bark)
    vertices, faces = [], []
    for leaf in leaves:
        coords, triangles = leaf_geometry(leaf)
        offset = len(vertices)
        vertices.extend(coords)
        faces.extend([i+offset for i in t] for t in triangles)
    leaf_mat = apply_material('RF1_Leaf', resolved['appearance']['leaf'])
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
    # Evaluar la superficie que Blender exporta; el BVH de polígonos implícitos
    # puede dar falsos negativos en caras largas y estrechas (B3, extremo 20 m).
    if corrected:
        errors = insertion_errors(wood, [c['points_m'][0] for c in carriers])
    else:
        base_bvh = BVHTree.FromPolygons(ref['wood_mesh']['vertices'], ref['wood_mesh']['polygons'])
        errors = [base_bvh.find_nearest(Vector(c['points_m'][0]))[3] for c in carriers]
        assert max(errors) < CONTACT_TOLERANCE_M
    metrics = mesh_report(mesh, triangle_limit=triangle_limit)
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
    manifest = {'version': spec['version'], 'spec': job['spec'], 'canopy_spec': spec, 'reference_sha256': sha(output / 'base-reference.json'), 'wood_sha256': wood_hash(mesh),
        'base_spec': ref['spec'], 'normalization': ref['normalization'], 'base_seeds': ref['seeds'],
        'base_matrix_world': ref['matrix_world'], 'output_matrix_world': [list(row) for row in obj.matrix_world],
        'molds_sha256': digest(guides), 'molds_exported': False,
        'metrics': metrics, 'budget': work, 'budget_before_selection': maximum,
        'surface_projection': projection,
        'support_count': len(carriers), 'leaf_count': len(leaves), 'sampling': sampling, 'selection': selection,
        'supports': carriers, 'supports_sha256': digest(carriers), 'placements': leaves,
        'placements_sha256': digest(leaves), 'twigs_sha256': digest(twig_records),
        'contacts': {'all_insertions_on_q3_and_inside_twig': True, 'all_leaf_roots_inside_own_twig': True,
                     'max_insertion_error_m': max(errors),
                     'insertion_method': 'blender_loop_triangles_float64' if corrected else 'legacy_polygons_bvh',
                     'insertion_tolerance_m': CONTACT_TOLERANCE_M, 'method': 'convex_tube_face_halfspaces',
                     'maximum_leaf_signed_face_distance_m': maximum_signed_distance,
                     'legacy_fixed_ray_long_paths': legacy_long_rays},
        'height_check': {'requested_m': ref['height_m'], 'actual_m': metrics['height_m'], 'tolerance_m': .0001},
        'layout_leaf_length_m': layout_leaf_length_m or spec['leaf_length_m'], 'cameras_sha256': digest(ref['cameras']),
        'projection_clips': projection_clips(mesh, ref['cameras']),
        'blender': bpy.app.version_string, 'blender_build': bpy.app.build_hash.decode(), 'blender_python': sys.version,
        'generation_before_render_export_s': generation_s, 'total_s': time.monotonic()-started,
        'glb_bytes': (output/'tree.glb').stat().st_size,
        'files_sha256': {n: sha(output/n) for n in ('tree.glb', 'tree.blend')}}

    sources = {Path(module.__file__).resolve() for module in list(sys.modules.values())
               if getattr(module, '__file__', None) and str(module.__file__).endswith('.py')}
    sources.update((ROOT / 'schemas').glob('*.json'))
    sources.add(inspection_path)
    manifest.update(status='completed', kind='blueprint', adapter_version='blueprint-blender-1.1.0',
                    spec_sha256=job['spec_sha256'], seeds=job['seeds'],
                    resolved_blueprint=resolved, cameras=cameras,
                    runner_python=job['runner_python'], jsonschema_version=job['jsonschema_version'],
                    glb_sha256=sha(output / 'tree.glb'),
                    sources_sha256={str(p.relative_to(ROOT)): sha(p) for p in sorted(sources)
                                    if p.is_relative_to(ROOT)},
                    base_generation='q3_in_memory', external_geometry_inputs=[])
    write(output / 'manifest.json', manifest)
    print(json.dumps(metrics))


if __name__ == '__main__':
    assert bpy.app.version[:3] == (5, 2, 1), bpy.app.version_string
    generate(json.loads(Path(sys.argv[sys.argv.index('--') + 1]).read_text()))
