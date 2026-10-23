#!/usr/bin/env python3
"""Diagnóstico de curvas de assets F2 guardados; ejecutar con Blender --python.

No modifica el generador ni guarda los .blend. Mide las curvas nativas y el ajuste Z.
"""
import argparse
import hashlib
import json
import math
from pathlib import Path
import sys

import bpy
from mathutils import Vector

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'blender'))
from oak_nodes import Graph, GEO


def evaluated_mesh(tree):
    obj = bpy.data.objects.new('Diagnosis', bpy.data.meshes.new('DiagnosisHost'))
    bpy.context.collection.objects.link(obj)
    modifier = obj.modifiers.new('Diagnosis', 'NODES')
    modifier.node_group = tree
    bpy.context.view_layer.update()
    graph = bpy.context.evaluated_depsgraph_get()
    mesh = bpy.data.meshes.new_from_object(obj.evaluated_get(graph), depsgraph=graph)
    bpy.data.objects.remove(obj, do_unlink=True)
    return mesh


def curves(structure, values, channel):
    g = Graph('Diagnosis_' + channel, [], [('Geometry', GEO)])
    node = g.group(structure)
    for socket in node.inputs:
        if socket.name in values:
            g.set(node, socket.name, values[socket.name])
    store = g.node('GeometryNodeStoreNamedAttribute', data_type='FLOAT', domain='POINT')
    g.set(store, 'Geometry', node.outputs[channel])
    g.set(store, 'Name', 'diagnostic_radius')
    g.set(store, 'Value', g.node('GeometryNodeInputRadius').outputs['Radius'])
    points = g.node('GeometryNodeCurveToPoints', mode='COUNT')
    g.set(points, 'Curve', store.outputs['Geometry'])
    g.set(points, 'Count', 64)
    vertices = g.node('GeometryNodePointsToVertices')
    g.set(vertices, 'Points', points.outputs['Points'])
    g.set(g.output, 'Geometry', vertices.outputs['Mesh'])
    mesh = evaluated_mesh(g.tree)
    if not mesh.vertices:
        bpy.data.meshes.remove(mesh)
        bpy.data.node_groups.remove(g.tree)
        return []
    positions = [v.co.copy() for v in mesh.vertices]
    radii = [r.value for r in mesh.attributes['diagnostic_radius'].data]
    result = [(positions[i:i+64], radii[i:i+64]) for i in range(0, len(positions), 64)]
    bpy.data.meshes.remove(mesh)
    bpy.data.node_groups.remove(g.tree)
    return result


def closest(point, candidate):
    points, radii = candidate
    best = None
    for a,b,ra,rb in zip(points, points[1:], radii, radii[1:]):
        direction = b-a
        t = max(0., min(1., (point-a).dot(direction)/direction.length_squared))
        distance = (point-(a+t*direction)).length
        result = (distance, direction.normalized(), ra+t*(rb-ra))
        if best is None or distance < best[0]:
            best = result
    return best


def direction(points):
    return (points[-1]-points[0]).normalized()


def angle(a,b):
    return math.degrees(math.acos(max(-1., min(1., a.dot(b)))))


def diagnose(folder):
    manifest = json.loads((folder / 'manifest.json').read_text())
    bpy.ops.wm.open_mainfile(filepath=str(folder / 'tree.blend'), load_ui=False)
    structure = next(g for g in bpy.data.node_groups if g.name.startswith('Oak_Structure_v'))
    generator = next(g for g in bpy.data.node_groups if g.name.startswith('Oak_Generator_v'))
    values = manifest['socket_values']
    channels = {name: curves(structure, values, name) for name in ('Trunk', 'Primary', 'Secondary')}
    count = manifest['spec']['parameters']['primary_branches']
    assert len(channels['Trunk']) == 1
    assert len(channels['Primary']) == count
    assert len(channels['Secondary']) == manifest['structure_checks']['secondary_branches']
    normalization = manifest.get('normalization')
    if normalization:
        raw_bounds = normalization['raw_bounds_blender']
        low, high = raw_bounds[0][2], raw_bounds[1][2]
        scale_z = normalization['scale'][2]
        bounds = [[row[0], row[1], (row[2]-low)*scale_z] for row in raw_bounds]
        measured = manifest['crown_checks']['wood_bounds_blender']
        assert all(abs(a-b)<1e-4 for row, expected in zip(bounds, measured) for a,b in zip(row, expected))
    else:
        # Evaluar la unión previa al ajuste vertical del generador, sin tocar la fuente.
        raw = generator.copy()
        transform = next(n for n in raw.nodes if n.bl_idname == 'GeometryNodeTransform')
        output = next(n for n in raw.nodes if n.bl_idname == 'NodeGroupOutput')
        raw.links.new(transform.inputs['Geometry'].links[0].from_socket, output.inputs['Geometry'])
        wrapper = Graph('Diagnosis_Raw', [], [('Geometry', GEO)])
        n = wrapper.group(raw)
        for socket in n.inputs:
            if socket.name in values:
                wrapper.set(n, socket.name, values[socket.name])
        wrapper.set(wrapper.output, 'Geometry', n.outputs['Geometry'])
        mesh = evaluated_mesh(wrapper.tree)
        low, high = min(v.co.z for v in mesh.vertices), max(v.co.z for v in mesh.vertices)
        scale_z = manifest['spec']['parameters']['height_m']/(high-low)
        raw_bounds = [[fn(v.co[k] for v in mesh.vertices) for k in range(3)] for fn in (min,max)]
        final_bounds = [[row[0],row[1],(row[2]-low)*scale_z] for row in raw_bounds]
        assert all(abs(a-b)<1e-4 for row,expected in zip(final_bounds,manifest['metrics']['bounds_blender'])
                   for a,b in zip(row,expected)), 'El ajuste medido no reproduce la caja exportada'
        bpy.data.meshes.remove(mesh)
    rows = []
    for name, branches in channels.items():
        parents = channels['Trunk'] if name == 'Primary' else channels['Primary']
        for index,(points,radii) in enumerate(branches):
            d = direction(points)
            final_direction = Vector((d.x,d.y,d.z*scale_z)).normalized()
            row = {'channel':name, 'index':index, 'start':list(points[0]), 'tip':list(points[-1]),
                   'radius_start_m':radii[0], 'radius_end_m':radii[-1],
                   'inclination_raw_deg':angle(d,Vector((0,0,1))),
                   'inclination_final_deg':angle(final_direction,Vector((0,0,1))),
                   'azimuth_deg':math.degrees(math.atan2(d.y,d.x)),
                   'length_m':sum((b-a).length for a,b in zip(points,points[1:])),
                   'length_final_m':sum(Vector((b.x-a.x,b.y-a.y,(b.z-a.z)*scale_z)).length
                                        for a,b in zip(points,points[1:]))}
            if name != 'Trunk':
                parent,match = min(enumerate(closest(points[0],p) for p in parents), key=lambda p:p[1][0])
                row.update(parent_index=parent, attachment_error_m=match[0],
                           parent_radius_m=match[2], radius_ratio_to_parent=radii[0]/match[2],
                           divergence_from_parent_deg=angle(d,match[1]))
                assert match[0]<.003, 'No se pudo identificar una unión con precisión suficiente'
            rows.append(row)
    primary_dirs = [direction(c[0]) for c in channels['Primary']]
    gaps = sorted((math.degrees(math.atan2(v.y,v.x))%360) for v in primary_dirs)
    gaps = [b-a for a,b in zip(gaps,gaps[1:]+[gaps[0]+360])]
    secondary_pairs=[]
    for parent in range(len(channels['Primary'])):
        children=[r for r in rows if r['channel']=='Secondary' and r['parent_index']==parent]
        ds=[(Vector(c['tip'])-Vector(c['start'])).normalized() for c in children]
        secondary_pairs.extend(angle(a, b) for i,a in enumerate(ds) for b in ds[i+1:])
    positions = [p for branches in channels.values() for points,radii in branches for p in points]
    skeleton_dimensions = [max(p[k] for p in positions)-min(p[k] for p in positions) for k in range(3)]
    primary_rows = sorted((r for r in rows if r['channel']=='Primary'), key=lambda r:r['start'][2])
    lower_count = max(1, len(primary_rows)//3)
    summary = {'skeleton_width_xy_m':max(skeleton_dimensions[:2]),
               'skeleton_dimensions_raw_m':skeleton_dimensions,
               'primary_length_total_m':sum(r['length_m'] for r in primary_rows),
               'primary_length_final_total_m':sum(r['length_final_m'] for r in primary_rows),
               'curve_length_total_m':sum(r['length_m'] for r in rows),
               'lower_primary_mean_radius_m':sum(r['radius_start_m'] for r in primary_rows[:lower_count])/lower_count,
               'primary_inclinations_raw_deg':[r['inclination_raw_deg'] for r in rows if r['channel']=='Primary'],
               'primary_azimuth_min_gap_deg':min(gaps),
               'primary_azimuth_max_gap_deg':max(gaps),
               'primary_radius_larger_than_parent':sum(r['radius_ratio_to_parent']>1 for r in rows if r['channel']=='Primary'),
               'secondary_radius_larger_than_parent':sum(r['radius_ratio_to_parent']>1 for r in rows if r['channel']=='Secondary'),
               'secondary_sibling_direction_angles_deg':secondary_pairs}
    return {'id':folder.name,'seed':manifest['spec']['seed'],'spec':manifest['spec'],
            'blend_sha256':hashlib.sha256((folder/'tree.blend').read_bytes()).hexdigest(),
            'manifest_sha256':hashlib.sha256((folder/'manifest.json').read_bytes()).hexdigest(),
            'seeds':manifest['seeds'],'geometry_sha256':manifest['metrics']['geometry_sha256'],
            'raw_bounds_z':[low,high],'final_z_scale':scale_z,'summary':summary,'curves':rows}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--batch',type=Path,default=ROOT/'artifacts/f2/lote-final')
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--cases',nargs='+',default=['viejo-00','viejo-03','viejo-09','adulto-00','joven-00'])
    args=parser.parse_args(sys.argv[sys.argv.index('--')+1:])
    args.output.mkdir(parents=True,exist_ok=False)
    reports=[]
    for case in args.cases:
        report=diagnose(args.batch.resolve()/case)
        reports.append(report)
        print(json.dumps({'id':case,'summary':report['summary']}),flush=True)
    output={'blender':bpy.app.version_string,'blender_build':bpy.app.build_hash.decode(),
            'script_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
            'graph_helper_sha256':hashlib.sha256((ROOT/'blender/oak_nodes.py').read_bytes()).hexdigest(),
            'cases':reports}
    (args.output/'diagnosis.json').write_text(json.dumps(output,indent=2)+'\n')


if __name__=='__main__':
    main()
