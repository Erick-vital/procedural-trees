"""Adaptador Blender. Recibe un trabajo validado por el ejecutor."""
import hashlib
import json
import math
from pathlib import Path
import sys

import bpy
from mathutils import Vector

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'blender'))
sys.path.insert(0, str(ROOT / 'src'))
from oak_nodes import PARAMETERS, Graph, GEO
from treegen.crown import measure_crown


def structure_report(structure, values, params, secondary_per_primary=2):
    """Muestrea curvas nativas para comprobar uniones; no genera una estructura Python."""
    debug = Graph('Oak_Diagnostic', [], [('Geometry', GEO)])
    node = debug.group(structure.tree)
    for name in structure.sockets:
        debug.set(node, name, values[name])
    points = debug.node('GeometryNodeCurveToPoints', mode='COUNT')
    debug.set(points, 'Count', 64)
    debug.set(points, 'Curve', node.outputs['Curves'])
    vertices = debug.node('GeometryNodePointsToVertices')
    debug.set(vertices, 'Points', points.outputs['Points'])
    debug.set(debug.output, 'Geometry', vertices.outputs['Mesh'])
    obj = bpy.data.objects.new('Diagnostic', bpy.data.meshes.new('DiagnosticHost'))
    bpy.context.collection.objects.link(obj)
    mod = obj.modifiers.new('Diagnostic', 'NODES')
    mod.node_group = debug.tree
    bpy.context.view_layer.update()
    graph = bpy.context.evaluated_depsgraph_get()
    mesh = bpy.data.meshes.new_from_object(obj.evaluated_get(graph), depsgraph=graph)
    coords = [v.co.copy() for v in mesh.vertices]
    count = params['primary_branches']
    expected = 1 + count * (1 + secondary_per_primary if params['max_depth'] == 2 else 1)
    assert len(coords) == expected * 64, (len(coords), expected)
    curves = [coords[k:k + 64] for k in range(0, len(coords), 64)]
    # Join Geometry antepone cada enlace nuevo en Blender 5.2.1.
    trunk, primary, secondary = curves[-1], curves[-1 - count:-1], curves[:-1 - count]
    assert trunk[0].length < 1e-6

    def distance_to_curve(point, curve):
        distances = []
        for a, b in zip(curve, curve[1:]):
            delta = b - a
            t = max(0., min(1., (point - a).dot(delta) / delta.length_squared))
            distances.append((point - (a + delta * t)).length)
        return min(distances)

    errors = [distance_to_curve(curve[0], trunk) for curve in primary]
    errors += [min(distance_to_curve(curve[0], parent) for parent in primary) for curve in secondary]
    maximum_error = max(errors, default=0.)
    assert maximum_error < .003, f'Unión separada: {maximum_error} m'
    result = {'curves': expected, 'primary_branches': count,
              'secondary_branches': secondary_per_primary * count if params['max_depth'] == 2 else 0,
              'samples_per_curve': 64, 'max_attachment_error_m': maximum_error,
              'structure_sha256': hashlib.sha256(json.dumps([
                  [round(c, 6) for c in v] for v in coords]).encode()).hexdigest()}
    bpy.data.objects.remove(obj, do_unlink=True)
    bpy.data.meshes.remove(mesh)
    bpy.data.node_groups.remove(debug.tree)
    return result


def material(name, color):
    mat = bpy.data.materials.new(name)
    mat.diffuse_color = (*color, 1)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get('Principled BSDF')
    bsdf.inputs['Base Color'].default_value = (*color, 1)
    bsdf.inputs['Roughness'].default_value = .88
    return mat


def mesh_report(mesh):
    mesh.calc_loop_triangles()
    assert mesh.vertices and mesh.loop_triangles, 'Malla vacía'
    assert len(mesh.loop_triangles) <= 10000, 'Presupuesto excedido'
    assert all(math.isfinite(c) for v in mesh.vertices for c in v.co), 'Coordenadas no finitas'
    bad = [t for t in mesh.loop_triangles if t.area <= 1e-10]
    assert not bad, f'Triángulos degenerados: {len(bad)}; ejemplos ' + str([
        (t.material_index, [tuple(mesh.vertices[i].co) for i in t.vertices]) for t in bad[:3]])
    assert all(mesh.materials[t.material_index] for t in mesh.loop_triangles), 'Material ausente'
    vertices = sorted(tuple(round(c, 6) for c in v.co) for v in mesh.vertices)
    triangles = sorted((mesh.materials[t.material_index].name,
                        sorted(tuple(round(c, 6) for c in mesh.vertices[i].co) for i in t.vertices))
                       for t in mesh.loop_triangles)
    bounds = [[min(v[k] for v in vertices) for k in range(3)],
              [max(v[k] for v in vertices) for k in range(3)]]
    by_material = {mat.name: sum(t.material_index == i for t in mesh.loop_triangles)
                   for i, mat in enumerate(mesh.materials) if mat}
    return {'vertices': len(vertices), 'triangles': len(triangles), 'bounds_blender': bounds,
            'height_m': bounds[1][2] - bounds[0][2], 'triangles_by_material': by_material,
            'geometry_sha256': hashlib.sha256(json.dumps([vertices, triangles]).encode()).hexdigest()}


def evaluated_output(generator, values, channel):
    debug = Graph('Oak_Output_Diagnostic', [], [('Geometry', GEO)])
    node = debug.group(generator.tree)
    for name in generator.sockets:
        debug.set(node, name, values[name])
    geometry = node.outputs[channel]
    if channel in ('Anchors', 'Centers'):
        vertices = debug.node('GeometryNodePointsToVertices')
        debug.set(vertices, 'Points', geometry)
        geometry = vertices.outputs['Mesh']
    debug.set(debug.output, 'Geometry', geometry)
    obj = bpy.data.objects.new('OutputDiagnostic', bpy.data.meshes.new('OutputHost'))
    bpy.context.collection.objects.link(obj)
    mod = obj.modifiers.new('Diagnostic', 'NODES')
    mod.node_group = debug.tree
    bpy.context.view_layer.update()
    graph = bpy.context.evaluated_depsgraph_get()
    mesh = bpy.data.meshes.new_from_object(obj.evaluated_get(graph), depsgraph=graph)
    bpy.data.objects.remove(obj, do_unlink=True)
    bpy.data.node_groups.remove(debug.tree)
    return mesh


def foliage_report(generator, values, params, crown):
    """Controles de Q3 sobre los atributos realmente evaluados por los nodos."""
    from collections import Counter, defaultdict
    mesh = evaluated_output(generator, values, 'Centers')
    records = []
    for k in range(len(mesh.vertices)):
        records.append({name:mesh.attributes['q3_'+name].data[k].value
                        for name in ('level','branch','rank','role','detail','kind','count')})
    assert len(records) == crown['leaf_mass_count']
    assert crown['leaf_triangles'] == sum(80 if r['detail'] else 20 for r in records)
    groups = defaultdict(list)
    for r in records:
        assert r['level'] in (0,1,2) and r['role'] in (0,1,2) and 0 <= r['kind'] < 6
        assert bool(r['detail']) == (r['kind'] < 4)
        groups[(r['level'],r['branch'])].append(r)
    for (level,branch), rows in groups.items():
        assert len(rows) <= (2,3,2)[level]
        assert all(r['count'] == len(rows) for r in rows)
        assert sorted(r['rank'] for r in rows) == list(range(len(rows)))
    count = params['primary_branches']
    assert len(records) <= 2+3*count+(6*count if params['max_depth']==2 else 0)
    report = {'mass_count':len(records), 'triangles_expected':sum(80 if r['detail'] else 20 for r in records),
        'counts_by_level':{name:sum(r['level']==k for r in records) for k,name in enumerate(('trunk','primary','secondary'))},
        'counts_by_role':{name:sum(r['role']==k for r in records) for k,name in enumerate(('dominant','medium','small'))},
        'families':{str(k):v for k,v in sorted(Counter(r['kind'] for r in records).items())},
        'high_detail_masses':sum(bool(r['detail']) for r in records),
        'branch_count_histogram':{name:{str(n):v for n,v in sorted(Counter(len(rows) for (level,branch),rows in groups.items() if level==k).items())}
                                for k,name in enumerate(('trunk','primary','secondary'))}}
    if generator.tree.name.startswith('Oak_Generator_v0.4.1'):
        for k,r in enumerate(records):
            for name in ('radius','parent_radius','support'):
                r[name] = mesh.attributes['q3_'+name].data[k].value
            r['scale_product_m3'] = math.prod(mesh.attributes['q3_scale'].data[k].vector)
            assert r['radius'] > 0 and r['scale_product_m3'] > 0
        report['branches'] = [
            {'level':level,'branch':branch,'radius_m':rows[0]['radius'],
             'parent_radius_m':rows[0]['parent_radius'],'support':rows[0]['support'],
             'masses':len(rows),'scale_product_sum_m3':sum(r['scale_product_m3'] for r in rows)}
            for (level,branch),rows in sorted(groups.items())]
    bpy.data.meshes.remove(mesh)
    return report


def render_views(obj, output, views=None, framing=None):
    scene = bpy.context.scene
    scene.render.engine = 'BLENDER_WORKBENCH'
    scene.render.resolution_x = 900
    scene.render.resolution_y = 900
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = 'PNG'
    scene.display.shading.light = 'STUDIO'
    scene.display.shading.studiolight_rotate_z = .5
    scene.display.shading.color_type = 'MATERIAL'
    scene.display.shading.show_shadows = True
    scene.display.shading.show_cavity = True
    scene.display.shading.cavity_type = 'BOTH'
    scene.display.shading.background_type = 'WORLD'
    scene.world.color = (.09, .11, .14)
    center = sum((obj.matrix_world @ Vector(p) for p in obj.bound_box), Vector()) / 8
    span = max(obj.dimensions)
    if framing is not None:
        center, span = Vector(framing['center']), framing['span']
    camera = bpy.data.objects.new('InspectionCamera', bpy.data.cameras.new('InspectionCamera'))
    scene.collection.objects.link(camera)
    scene.camera = camera
    cameras = {}
    for name, direction in (views or [('perspective', (1.3, -1.8, 1.0)), ('front', (0, -1, 0)),
                                     ('side', (1, 0, 0)), ('top', (0, 0, 1))]):
        camera.location = center + Vector(direction).normalized() * span * 2.5
        camera.rotation_euler = (center - camera.location).to_track_quat('-Z', 'Y').to_euler()
        camera.data.type = 'PERSP' if name == 'perspective' else 'ORTHO'
        camera.data.lens = 50
        camera.data.ortho_scale = span * 1.2
        cameras[name] = {'type': camera.data.type, 'location': list(camera.location),
                         'rotation_euler': list(camera.rotation_euler), 'ortho_scale': camera.data.ortho_scale,
                         'lens_mm': camera.data.lens, 'resolution': [900, 900]}
        scene.render.filepath = str(output / f'{name}.png')
        bpy.ops.render.render(write_still=True)
    return cameras


def main(job_path):
    assert bpy.app.version[:3] == (5, 2, 1), bpy.app.version_string
    job = json.loads(Path(job_path).read_text())
    spec, params = job['spec'], job['spec']['parameters']
    if spec['algorithm_version'] == '0.1.0':
        from oak_nodes import VERSION, build_generator
        algorithm_source = ROOT / 'blender/oak_nodes.py'
    elif spec['algorithm_version'] == '0.2.0':
        from oak_nodes_v2 import VERSION, build_generator
        algorithm_source = ROOT / 'blender/oak_nodes_v2.py'
    elif spec['algorithm_version'] == '0.2.1':
        from oak_nodes_v21 import VERSION, build_generator
        algorithm_source = ROOT / 'blender/oak_nodes_v21.py'
    elif spec['algorithm_version'] == '0.3.0':
        from oak_nodes_v3 import VERSION, build_generator
        algorithm_source = ROOT / 'blender/oak_nodes_v3.py'
    elif spec['algorithm_version'] == '0.4.0':
        from oak_nodes_v4 import VERSION, build_generator
        algorithm_source = ROOT / 'blender/oak_nodes_v4.py'
    elif spec['algorithm_version'] == '0.4.1':
        from oak_nodes_v41 import VERSION, build_generator
        algorithm_source = ROOT / 'blender/oak_nodes_v41.py'
    else:
        raise ValueError('Versión de algoritmo no soportada')
    # Defensa local de límites aun si se invoca esta entrada interna directamente.
    schema = json.loads((ROOT / 'schemas/tree-spec.schema.json').read_text())
    assert spec['algorithm'] == 'oak_geometry_nodes' and spec['algorithm_version'] == VERSION
    assert set(params) == set(PARAMETERS)
    for key, value in params.items():
        rule = schema['properties']['parameters']['properties'][key]
        assert type(value) in (int, float) and math.isfinite(value)
        assert rule['minimum'] <= value <= rule['maximum'], key
        if rule['type'] == 'integer':
            assert type(value) is int, key
    output = Path(job['output']).resolve()
    output.mkdir(parents=True, exist_ok=True)
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete(use_global=False)
    bpy.context.scene.unit_settings.system = 'METRIC'
    bpy.context.scene.unit_settings.scale_length = 1
    bark = material('Oak_Bark', (.24, .105, .045))
    leaves = material('Oak_Leaves', (.23, .43, .065))
    generator, structure = build_generator(bark, leaves)
    obj = bpy.data.objects.new('OakProcedural', bpy.data.meshes.new('OakHost'))
    bpy.context.collection.objects.link(obj)
    modifier = obj.modifiers.new('OakGenerator', 'NODES')
    modifier.node_group = generator.tree
    values = {PARAMETERS[k][0]: v for k, v in params.items()}
    values.update({'Structure Seed': job['seeds']['structure'], 'Foliage Seed': job['seeds']['foliage'],
                   'Profile Resolution': 8})
    for name, value in values.items():
        getattr(modifier.properties.inputs, generator.sockets[name]).value = value
    obj.update_tag()
    diagnostics = structure_report(structure, values, params, 3 if VERSION in ('0.2.1', '0.3.0', '0.4.0', '0.4.1') else 2)
    bpy.context.view_layer.update()
    depsgraph = bpy.context.evaluated_depsgraph_get()
    mesh = bpy.data.meshes.new_from_object(obj.evaluated_get(depsgraph), depsgraph=depsgraph)
    metrics = mesh_report(mesh)
    crown = measure_crown([tuple(v.co) for v in mesh.vertices],
                          [(mesh.materials[t.material_index].name, tuple(t.vertices)) for t in mesh.loop_triangles], params['height_m'])
    normalization = None
    if VERSION in ('0.3.0','0.4.0','0.4.1'):
        raw = evaluated_output(generator, values, 'Raw Wood')
        bounds = mesh_report(raw)['bounds_blender']
        scale_z = params['height_m']/(bounds[1][2]-bounds[0][2])
        normalization = {'basis':'wood_bounds', 'raw_bounds_blender':bounds,
                         'scale':[1, 1, scale_z], 'translation':[0, 0, -bounds[0][2]*scale_z]}
        bpy.data.meshes.remove(raw)
    assert abs(metrics['height_m'] - params['height_m']) < .001, 'Altura final incorrecta'
    masses = math.floor(4 * params['foliage_density'] + .5)
    foliage_checks = None
    if VERSION in ('0.4.0','0.4.1'):
        foliage_checks = foliage_report(generator, values, params, crown)
    else:
        assert metrics['triangles_by_material'].get('Oak_Leaves', 0) == diagnostics['curves'] * masses * 20
    parameter_checks = {}
    if job.get('check_parameters'):
        alternatives = {'height_m': 8., 'base_radius_m': .3, 'curvature': .02,
                        'primary_branches': 6, 'max_depth': 1, 'branch_length_ratio': .3,
                        'inclination_deg': 40., 'asymmetry': .1, 'foliage_density': .5, 'foliage_scale_m': .8}
        for key, alternative in alternatives.items():
            name = PARAMETERS[key][0]
            socket = getattr(modifier.properties.inputs, generator.sockets[name])
            socket.value = alternative
            obj.update_tag()
            bpy.context.view_layer.update()
            graph = bpy.context.evaluated_depsgraph_get()
            changed = bpy.data.meshes.new_from_object(obj.evaluated_get(graph), depsgraph=graph)
            changed_report = mesh_report(changed)
            assert changed_report['geometry_sha256'] != metrics['geometry_sha256'], f'Parámetro sin efecto: {key}'
            parameter_checks[key] = changed_report['geometry_sha256']
            bpy.data.meshes.remove(changed)
            socket.value = values[name]
            obj.update_tag()
        bpy.context.view_layer.update()
    final = bpy.data.objects.new('Oak', mesh)
    bpy.context.collection.objects.link(final)
    obj.hide_render = True
    obj.hide_set(True)
    bpy.ops.object.select_all(action='DESELECT')
    final.select_set(True)
    bpy.context.view_layer.objects.active = final
    bpy.ops.export_scene.gltf(filepath=str(output / 'tree.glb'), export_format='GLB',
                              use_selection=True, export_yup=True)
    cameras = {}
    if job.get('render', True):
        cameras = render_views(final, output)
        # Revisión de uniones sin que la copa las oculte; se conserva la malla exportada.
        import bmesh
        branch_mesh = mesh.copy()
        bm = bmesh.new()
        bm.from_mesh(branch_mesh)
        bmesh.ops.delete(bm, geom=[f for f in bm.faces if branch_mesh.materials[f.material_index].name == 'Oak_Leaves'],
                         context='FACES')
        bm.to_mesh(branch_mesh)
        bm.free()
        branches = bpy.data.objects.new('InspectionBranches', branch_mesh)
        bpy.context.collection.objects.link(branches)
        final.hide_render = True
        render_views(branches, output, [('branches', (1.3, -1.8, .65))])
        bpy.data.objects.remove(branches, do_unlink=True)
        final.hide_render = False
    bpy.ops.wm.save_as_mainfile(filepath=str(output / 'tree.blend'))
    manifest = {'status': 'completed', 'cameras': cameras, 'spec': spec, 'spec_sha256': job['spec_sha256'],
                'seeds': job['seeds'], 'socket_values': values, 'socket_mapping': generator.sockets,
                'algorithm_version': VERSION, 'node_groups': {g.name: len(g.nodes) for g in bpy.data.node_groups},
                'blender': bpy.app.version_string, 'blender_build': bpy.app.build_hash.decode(),
                'runner_python': job['runner_python'], 'jsonschema_version': job['jsonschema_version'],
                'blender_python': sys.version, 'metrics': metrics, 'structure_checks': diagnostics,
                'crown_checks': crown, 'normalization': normalization,
                'foliage_checks': foliage_checks,
                'parameter_effect_checks': parameter_checks,
                'sources_sha256': {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest()
                                   for p in ({Path(__file__), ROOT / 'blender/oak_nodes.py', algorithm_source, ROOT / 'src/treegen/crown.py'}
                                             | ({ROOT / 'blender/oak_nodes_v2.py'} if VERSION in ('0.2.1', '0.3.0', '0.4.0', '0.4.1') else set())
                                             | ({ROOT / 'blender/oak_nodes_v21.py'} if VERSION in ('0.3.0','0.4.0','0.4.1') else set())
                                             | ({ROOT / 'blender/oak_nodes_v3.py'} if VERSION in ('0.4.0','0.4.1') else set())
                                             | ({ROOT / 'blender/oak_nodes_v4.py'} if VERSION == '0.4.1' else set()))},
                'glb_sha256': hashlib.sha256((output / 'tree.glb').read_bytes()).hexdigest()}
    (output / 'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
    print(json.dumps(metrics))


if __name__ == '__main__':
    main(sys.argv[sys.argv.index('--') + 1])
