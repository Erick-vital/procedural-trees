"""Adaptador RF2 revisada: base Q3 intacta, ramillas y comparación acotada."""
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
from generate_oak import material, mesh_report
from treegen.foliage import digest
from treegen.foliage_twigs import (VERSION, budget, build_layout, load_twigs,
                                   target_region, twig_geometry)


def freeze_target(reference_path, output):
    ref = json.loads(reference_path.read_text())
    bpy.ops.wm.open_mainfile(filepath=str(reference_path.parent/'scene.blend'), load_ui=False)
    obj = bpy.data.objects['RF2_Q3Subtree']
    assert mesh_report(obj.data) == ref['q3_metrics']
    points = [obj.data.vertices[i].co for p in obj.data.polygons
              if obj.data.materials[p.material_index].name == 'Oak_Leaves' for i in p.vertices]
    bounds = [[fn(p[k] for p in points) for k in range(3)] for fn in (min, max)]
    target = target_region(bounds, sha(reference_path))
    cameras = json.loads(json.dumps(ref['cameras']))
    for name, fraction in [('near', .5), ('medium', .25), ('far', .1)]:
        cameras[name] = dict(cameras['front'], ortho_scale=ref['q3_metrics']['height_m']/fraction,
                             target_height_fraction=fraction)
    target['cameras'] = cameras
    write(output/'target.json', target)
    write(output/'cameras.json', cameras)
    render(obj, output, cameras)
    export(obj, output)
    write(output/'manifest.json', {'version': 'q3-subtree-0.4.0', 'wood_sha256': wood_hash(obj.data),
          'metrics': mesh_report(obj.data), 'cameras_sha256': digest(cameras),
          'reference_sha256': sha(reference_path), 'target_sha256': sha(output/'target.json')})


def check_inside(bvh, point):
    # Malla cerrada con normales exteriores: desde dentro, el primer cruce sale.
    direction = Vector((.3121, .7893, .5297)).normalized()
    position, normal, _, distance = bvh.ray_cast(Vector(point), direction)
    if position is None or normal.dot(direction) <= 0 or distance > .15:
        raise ValueError('Raíz fuera de la ramilla visible')
    return distance


def candidate(reference_path, target_path, spec_path, output, no_render):
    started = time.monotonic()
    ref = json.loads(reference_path.read_text())
    target = json.loads(target_path.read_text())
    assert target['reference_sha256'] == sha(reference_path)
    spec = load_twigs(spec_path)
    assert spec['base']['branch_id'] == ref['branch_id']
    assert ref['source_files_sha256'] == {name: sha(Path(ref['source'])/name) for name in ref['source_files_sha256']}
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete(use_global=False)
    bark = material('Oak_Bark', ref['wood_material']['principled_base'][:3])
    bark.diffuse_color = ref['wood_material']['diffuse']
    bark.use_backface_culling = ref['wood_material']['backface_culling']
    bark.node_tree.nodes['Principled BSDF'].inputs['Roughness'].default_value = ref['wood_material']['roughness']
    wood = mesh_from(ref['wood_mesh'], 'RF2_ExactWood')
    wood.materials.append(bark)
    bvh = BVHTree.FromPolygons(ref['wood_mesh']['vertices'], ref['wood_mesh']['polygons'])
    branch_bvhs = {b['id']: BVHTree.FromPolygons(b['mesh']['vertices'], b['mesh']['polygons']) for b in ref['branches']}

    def surface(branch_id, origin, direction):
        position, _, _, distance = branch_bvhs[branch_id].ray_cast(Vector(origin), Vector(direction))
        if position is None or distance > 1:
            raise ValueError('Inserción sin superficie Q3')
        return tuple(position)

    carriers, leaves, distribution = build_layout(spec, ref['branches'], surface, target)
    vertices, faces = [], []
    leaf_centers = []
    for leaf in leaves:
        coords, triangles = leaf_geometry(leaf)
        leaf_centers.append([sum(v[k] for v in coords)/len(coords) for k in range(3)])
        offset = len(vertices)
        vertices.extend(coords)
        faces.extend(tuple(i+offset for i in t) for t in triangles)
    leaf_material = material('RF1_Leaf', (.23, .43, .065))
    leaf_material.use_backface_culling = False
    combined = combine(wood, vertices, faces, leaf_material)
    data = record(combined)
    twig_start = len(data['polygons'])
    twig_bvhs, twig_records = {}, []
    if spec['twigs']['enabled']:
        for carrier in carriers:
            coords, triangles = twig_geometry(carrier, spec['twigs'])
            twig_records.append({'id': carrier['id'], 'vertices': coords, 'triangles': triangles})
            twig_bvhs[carrier['id']] = BVHTree.FromPolygons(coords, triangles, all_triangles=True)
            offset = len(data['vertices'])
            data['vertices'].extend(coords)
            data['polygons'].extend([[i+offset for i in face] for face in triangles])
            data['smooth'].extend([False]*len(triangles))
    mesh = mesh_from(data, 'RF2_Revised')
    for mat in combined.materials:
        mesh.materials.append(mat)
    if spec['twigs']['enabled']:
        twig_material = bark.copy()
        twig_material.name = 'RF2_Twig'
        mesh.materials.append(twig_material)
    for p in mesh.polygons:
        p.material_index = 2 if p.index >= twig_start else combined.polygons[p.index].material_index
    assert wood_hash(mesh) == ref['wood_sha256']
    attachments = [bvh.find_nearest(Vector(c['points_m'][0]))[3] for c in carriers]
    assert max(attachments) < .0001
    contacts = {}
    if twig_bvhs:
        for carrier in carriers:
            check_inside(twig_bvhs[carrier['id']], carrier['points_m'][0])
        depths = [check_inside(twig_bvhs[leaf['support_id']], leaf['origin_m']) for leaf in leaves]
        contacts = {'all_insertions_on_q3_and_inside_twig': True, 'all_leaf_roots_inside_own_twig': True,
                    'leaf_root_surface_distance_m': {'minimum': min(depths), 'maximum': max(depths)}}
    # Ocupación diagnóstica por centros reales; independiente del barrido usado
    # para seleccionar recorridos. No mide área proyectada ni densidad botánica.
    occupied = [i for i, cell in enumerate(target['cells_m'])
                if any((Vector(cell)-Vector(center)).length <= .28 for center in leaf_centers)]
    distribution['actual_leaf_center_cells_r028m'] = len(occupied)
    distribution['actual_leaf_center_cell_ids'] = occupied
    metrics = mesh_report(mesh)
    expected = budget(spec)
    assert metrics['triangles'] == 464+expected['added_triangles']
    assert not metrics.get('degenerate_triangles', 0)
    assert min(v.co.z for v in mesh.vertices) >= 0 and max(v.co.z for v in mesh.vertices) <= 9.00001
    obj = bpy.data.objects.new('RF2_RevisedBranch', mesh)
    bpy.context.collection.objects.link(obj)
    cameras = target['cameras']
    write(output/'cameras.json', cameras)
    generation_s = time.monotonic()-started
    if not no_render:
        render(obj, output, cameras)
    configure()
    export(obj, output)
    write(output/'manifest.json', {'version': VERSION, 'spec': spec, 'spec_sha256': digest(spec),
        'reference_sha256': sha(reference_path), 'target_sha256': sha(target_path),
        'wood_sha256': wood_hash(mesh), 'wood_material': ref['wood_material'],
        'base_matrix_world': ref['matrix_world'], 'output_matrix_world': [list(row) for row in obj.matrix_world],
        'normalization': ref['normalization'], 'seeds': ref['seeds'],
        'metrics': metrics, 'budget': expected, 'support_count': len(carriers), 'leaf_count': len(leaves),
        'supports': carriers, 'supports_sha256': digest(carriers), 'placements': leaves,
        'placements_sha256': digest(leaves), 'twigs_sha256': digest(twig_records),
        'distribution': distribution, 'contacts': contacts, 'max_insertion_error_m': max(attachments),
        'cameras_sha256': digest(cameras), 'generation_before_render_export_s': generation_s,
        'total_s': time.monotonic()-started, 'glb_bytes': (output/'branch.glb').stat().st_size,
        'blender': bpy.app.version_string, 'blender_build': bpy.app.build_hash.decode(),
        'blender_python': sys.version,
        'files_sha256': {name: sha(output/name) for name in ('branch.glb', 'scene.blend')}})


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('mode', choices=('target', 'candidate'))
    parser.add_argument('--reference', type=Path, required=True)
    parser.add_argument('--target', type=Path)
    parser.add_argument('--spec', type=Path)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--no-render', action='store_true')
    args = parser.parse_args(sys.argv[sys.argv.index('--')+1:])
    assert bpy.app.version[:3] == (5, 2, 1)
    args.output.mkdir(parents=True, exist_ok=False)
    if args.mode == 'target':
        freeze_target(args.reference.resolve(), args.output.resolve())
    else:
        candidate(args.reference.resolve(), args.target.resolve(), args.spec.resolve(), args.output.resolve(), args.no_render)


if __name__ == '__main__':
    main()
