"""RF2: extrae un subárbol Q3 y evalúa hojas sobre portadores invisibles."""
import argparse
import hashlib
import json
import math
from pathlib import Path
import sys

import bpy
from mathutils import Vector
from mathutils.bvhtree import BVHTree
from mathutils.kdtree import KDTree

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT/'src'), str(ROOT/'blender')]
from foliage_lab import configure, evaluated, leaf_geometry, render, rig, sha, write
from foliage_fusion import extract
from generate_oak import material, mesh_report
from oak_nodes import Graph, GEO
from treegen.foliage import digest
from treegen.foliage_branch import branch_placements, load_branch, supports, VERSION


def record(mesh):
    return {'vertices': [list(v.co) for v in mesh.vertices],
            'polygons': [list(p.vertices) for p in mesh.polygons],
            'smooth': [p.use_smooth for p in mesh.polygons]}


def mesh_from(data, name):
    mesh = bpy.data.meshes.new(name)
    mesh.from_pydata(data['vertices'], [], data['polygons'])
    for p, smooth in zip(mesh.polygons, data['smooth']):
        p.use_smooth = smooth
    mesh.update()
    return mesh


def combine(wood, leaf_vertices, leaf_faces, leaf_material):
    data = record(wood)
    count = len(data['polygons'])
    offset = len(data['vertices'])
    data['vertices'].extend(list(v) for v in leaf_vertices)
    data['polygons'].extend([i+offset for i in face] for face in leaf_faces)
    data['smooth'].extend([False]*len(leaf_faces))
    mesh = mesh_from(data, 'RF2_Subtree')
    mesh.materials.append(bpy.data.materials['Oak_Bark'])
    mesh.materials.append(leaf_material)
    for p in mesh.polygons:
        p.material_index = int(p.index >= count)
    return mesh


def wood_hash(mesh):
    faces = [p for p in mesh.polygons if mesh.materials[p.material_index].name == 'Oak_Bark']
    ids = sorted({i for p in faces for i in p.vertices})
    mapping = {v: i for i, v in enumerate(ids)}
    return digest({'vertices': [list(mesh.vertices[i].co) for i in ids],
        'polygons': [[mapping[i] for i in p.vertices] for p in faces],
        'smooth': [p.use_smooth for p in faces]})


def export(obj, output):
    bpy.ops.object.select_all(action='DESELECT')
    obj.hide_set(False)
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    bpy.ops.export_scene.gltf(filepath=str(output/'branch.glb'), export_format='GLB',
                             use_selection=True, export_yup=True)
    bpy.ops.wm.save_as_mainfile(filepath=str(output/'scene.blend'))


def prepare(rf0_path, output):
    rf0 = json.loads(rf0_path.read_text())
    source = Path(rf0['source'])
    assert rf0['source_files_sha256'] == {name: sha(source/name) for name in rf0['source_files_sha256']}
    manifest = json.loads((source/'manifest.json').read_text())
    bpy.ops.wm.open_mainfile(filepath=str(source/'tree.blend'), load_ui=False)
    obj = bpy.data.objects['Oak']
    original = obj.data
    assert mesh_report(original) == manifest['metrics']
    generator = bpy.data.objects['OakProcedural'].modifiers[0].node_group
    structure = next(n.node_tree for n in generator.nodes if n.type == 'GROUP' and n.node_tree.name.startswith('Oak_Structure'))
    volume = next(n.node_tree for n in generator.nodes if n.type == 'GROUP' and n.node_tree.name.startswith('Oak_Volume'))
    wood_ids = sorted({i for p in original.polygons if original.materials[p.material_index].name == 'Oak_Bark' for i in p.vertices})
    kd = KDTree(len(wood_ids))
    for i in wood_ids:
        kd.insert(original.vertices[i].co, i)
    kd.balance()

    def probe(channel, index, sample):
        graph = Graph('RF2_OriginalSelection', [], [('Geometry', GEO)])
        node = graph.group(structure)
        for item in structure.interface.items_tree:
            if item.item_type == 'SOCKET' and item.in_out == 'INPUT':
                graph.set(node, item.name, manifest['socket_values'][item.name])
        select = graph.node('GeometryNodeSeparateGeometry', domain='CURVE')
        graph.set(select, 'Geometry', node.outputs[channel])
        graph.set(select, 'Selection', graph.op('LESS_THAN', graph.op('ABSOLUTE',
            graph.op('SUBTRACT', graph.node('GeometryNodeInputIndex').outputs['Index'], index)), .5))
        geometry = select.outputs['Selection']
        if sample:
            points = graph.node('GeometryNodeCurveToPoints', mode='COUNT')
            graph.set(points, 'Curve', geometry)
            graph.set(points, 'Count', 64)
            verts = graph.node('GeometryNodePointsToVertices')
            graph.set(verts, 'Points', points.outputs['Points'])
            geometry = verts.outputs['Mesh']
        else:
            mesh = graph.group(volume, Curves=geometry, Bark=bpy.data.materials['Oak_Bark'])
            graph.set(mesh, 'Profile Resolution', 8)
            geometry = mesh.outputs['Mesh']
        transform = graph.node('GeometryNodeTransform')
        graph.set(transform, 'Geometry', geometry)
        graph.set(transform, 'Scale', manifest['normalization']['scale'])
        graph.set(transform, 'Translation', manifest['normalization']['translation'])
        graph.set(graph.output, 'Geometry', transform.outputs['Geometry'])
        return evaluated(graph)

    branches, face_indices = [], set()
    for channel, index, branch_id in [('Primary', 0, 'q3:primary:100')]+[
            ('Secondary', i, f'q3:secondary:{200+i}') for i in range(3)]:
        estimated = probe(channel, index, False)
        matches = [kd.find(v.co) for v in estimated.vertices]
        assert max(m[2] for m in matches) < .00001, branch_id
        selected = {m[1] for m in matches}
        faces = [p for p in original.polygons if original.materials[p.material_index].name == 'Oak_Bark'
                 and all(i in selected for i in p.vertices)]
        frozen = extract(original, faces, branch_id)
        frozen.materials.append(bpy.data.materials['Oak_Bark'])
        assert len(frozen.vertices) == len(estimated.vertices) and len(frozen.polygons) == len(estimated.polygons)
        points = probe(channel, index, True)
        assert len(points.vertices) == 64
        branch = {'id': branch_id, 'parent_id': 'q3:primary:100' if channel == 'Secondary' else 'q3:trunk',
            'points_final_m': [list(v.co) for v in points.vertices], 'mesh': record(frozen),
            'source_polygon_indices': [p.index for p in faces], 'metrics': mesh_report(frozen)}
        if channel == 'Primary':
            assert digest(branch['mesh']) == rf0['branch']['mesh_sha256'], 'Cambió la primaria RF0'
        branches.append(branch)
        face_indices.update(p.index for p in faces)
        for mesh in (estimated, points, frozen):
            bpy.data.meshes.remove(mesh)
    # Selección por atributos realmente guardados, no por proximidad a la copa.
    leaf_faces = []
    for p in original.polygons:
        if original.materials[p.material_index].name != 'Oak_Leaves':
            continue
        i = p.vertices[0]
        level = original.attributes['q3_level'].data[i].value
        branch = original.attributes['q3_branch'].data[i].value
        if (level == 1 and branch == 100) or (level == 2 and branch in (200, 201, 202)):
            leaf_faces.append(p)
    assert leaf_faces
    wood = extract(original, [original.polygons[i] for i in sorted(face_indices)], 'RF2_FrozenWood')
    wood.materials.append(bpy.data.materials['Oak_Bark'])
    leaves = extract(original, leaf_faces, 'RF2_Q3Leaves')
    baseline = combine(wood, [tuple(v.co) for v in leaves.vertices],
        [tuple(p.vertices) for p in leaves.polygons], bpy.data.materials['Oak_Leaves'])
    # Conservar también sombreado original de follaje Q3 en esta referencia.
    for p, source_face in zip(list(baseline.polygons)[len(wood.polygons):], leaf_faces):
        p.use_smooth = source_face.use_smooth
    compare = bpy.data.objects.new('RF2_Q3Subtree', baseline)
    bpy.context.collection.objects.link(compare)
    bounds = mesh_report(baseline)['bounds_blender']
    low, high = bounds
    cameras = rig([(a+b)/2 for a, b in zip(low, high)], max(b-a for a, b in zip(low, high)))
    # Acercamiento fijado desde la primaria RF0; común a Q3 y todos los candidatos.
    from treegen.foliage_branch import path_sample
    center = path_sample(branches[0]['points_final_m'], .82)[0]
    for name, config in rig(center, 1.8).items():
        if name in ('top', 'below', 'perspective'):
            cameras['detail-'+name] = config
    write(output/'cameras.json', cameras)
    render(compare, output, cameras)
    export(compare, output)
    reference = {'version': 'rf2-reference-0.1.0', 'rf0_lock_sha256': sha(rf0_path),
        'source': str(source), 'source_files_sha256': rf0['source_files_sha256'],
        'spec': manifest['spec'], 'seeds': manifest['seeds'], 'normalization': manifest['normalization'],
        'branch_id': rf0['branch']['id'], 'branches': branches, 'wood_mesh': record(wood),
        'wood_sha256': wood_hash(baseline), 'wood_material': rf0['materials']['Oak_Bark'],
        'wood_source_polygon_indices': sorted(face_indices), 'q3_leaf_source_polygon_indices': [p.index for p in leaf_faces],
        'q3_metrics': mesh_report(baseline), 'cameras': cameras, 'lighting': rf0['lighting'],
        'matrix_world': rf0['tree_matrix_world'], 'rf0_primary_identical': True}
    assert reference['source_files_sha256'] == {name: sha(source/name) for name in rf0['source_files_sha256']}
    write(output/'reference.json', reference)
    write(output/'manifest.json', {'metrics': mesh_report(baseline), 'cameras_sha256': digest(cameras),
        'wood_sha256': reference['wood_sha256'], 'version': 'q3-subtree-0.4.0',
        'files_sha256': {n: sha(output/n) for n in ('branch.glb', 'scene.blend')}})


def candidate(reference_path, spec_path, output, no_render=False):
    ref = json.loads(reference_path.read_text())
    spec = load_branch(spec_path)
    assert spec['branch_id'] == ref['branch_id']
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete(use_global=False)
    bark = material('Oak_Bark', ref['wood_material']['principled_base'][:3])
    bark.diffuse_color = ref['wood_material']['diffuse']
    bark.use_backface_culling = ref['wood_material']['backface_culling']
    bark.node_tree.nodes['Principled BSDF'].inputs['Roughness'].default_value = ref['wood_material']['roughness']
    wood = mesh_from(ref['wood_mesh'], 'RF2_ExactWood')
    wood.materials.append(bark)
    wood.calc_loop_triangles()
    bvh_by_branch = {}
    for branch in ref['branches']:
        bvh_by_branch[branch['id']] = BVHTree.FromPolygons(branch['mesh']['vertices'], branch['mesh']['polygons'])
    def surface(branch_id, origin, direction):
        position, _, _, distance = bvh_by_branch[branch_id].ray_cast(Vector(origin), Vector(direction))
        if position is None or distance > 1:
            raise ValueError(f'Inserción sin superficie de madera: {branch_id}')
        return tuple(position)
    carriers = supports(spec, ref['branches'], surface)
    leaves = branch_placements(spec, carriers)
    vertices, faces = [], []
    for leaf in leaves:
        coords, triangles = leaf_geometry(leaf)
        offset = len(vertices)
        vertices.extend(coords)
        faces.extend(tuple(i+offset for i in t) for t in triangles)
    leaf_mat = material('RF1_Leaf', (.23, .43, .065))
    leaf_mat.use_backface_culling = False
    mesh = combine(wood, vertices, faces, leaf_mat)
    assert wood_hash(mesh) == ref['wood_sha256'], 'Cambió la madera'
    obj = bpy.data.objects.new('RF2_Branch', mesh)
    bpy.context.collection.objects.link(obj)
    cameras = ref['cameras']
    write(output/'cameras.json', cameras)
    if not no_render:
        render(obj, output, cameras)
    configure()
    export(obj, output)
    bvh = BVHTree.FromPolygons(ref['wood_mesh']['vertices'], ref['wood_mesh']['polygons'])
    distances = [bvh.find_nearest(Vector(leaf['origin_m']))[3] for leaf in leaves]
    attachment_errors = [bvh.find_nearest(Vector(c['points_m'][0]))[3] for c in carriers]
    assert max(attachment_errors) < .0001, [(c['id'], e) for c, e in zip(carriers, attachment_errors) if e >= .0001]
    metrics = mesh_report(mesh)
    manifest = {'version': VERSION, 'spec': spec, 'spec_sha256': digest(spec),
        'reference_sha256': sha(reference_path), 'wood_sha256': wood_hash(mesh),
        'wood_material': ref['wood_material'], 'same_final_wood': True,
        'metrics': metrics, 'leaf_count': len(leaves), 'support_count': len(carriers),
        'supports': carriers, 'supports_sha256': digest(carriers), 'placements': leaves,
        'placements_sha256': digest(leaves), 'cameras_sha256': digest(cameras),
        'max_support_attachment_error_m': max(attachment_errors),
        'leaf_root_distance_to_wood_m': {'minimum': min(distances), 'mean': sum(distances)/len(distances), 'maximum': max(distances)},
        'blender': bpy.app.version_string, 'blender_build': bpy.app.build_hash.decode(),
        'files_sha256': {n: sha(output/n) for n in ('branch.glb', 'scene.blend')}}
    write(output/'manifest.json', manifest)
    # Superposición diagnóstica: líneas de recorrido, ocultas en GLB/.blend final.
    if not no_render:
        overlay = bpy.data.curves.new('RF2_DiagnosticSupports', 'CURVE')
        overlay.dimensions = '3D'
        overlay.bevel_depth = .008
        overlay.bevel_resolution = 0
        for carrier in carriers:
            spline = overlay.splines.new('POLY')
            spline.points.add(len(carrier['points_m'])-1)
            for point, value in zip(spline.points, carrier['points_m']):
                point.co = (*value, 1)
        overlay.materials.append(material('RF2_DebugOnly', (.85, .15, .65)))
        debug = bpy.data.objects.new('RF2_DebugOnly', overlay)
        bpy.context.collection.objects.link(debug)
        # render() oculta otras mallas, pero mantiene esta curva diagnóstica.
        render(obj, output/'supports-debug', {k: v for k, v in cameras.items() if k in ('perspective', 'detail-perspective')})


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('mode', choices=('prepare', 'candidate'))
    parser.add_argument('--rf0', type=Path, default=ROOT/'docs/evidence/rf0-rf1/reference-lock.json')
    parser.add_argument('--reference', type=Path)
    parser.add_argument('--spec', type=Path)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--no-render', action='store_true')
    args = parser.parse_args(sys.argv[sys.argv.index('--')+1:])
    assert bpy.app.version[:3] == (5, 2, 1)
    args.output.mkdir(parents=True, exist_ok=False)
    if args.mode == 'prepare':
        prepare(args.rf0.resolve(), args.output.resolve())
    else:
        candidate(args.reference.resolve(), args.spec.resolve(), args.output.resolve(), args.no_render)


if __name__ == '__main__':
    main()
