"""Comparación acotada de addons instalados con Q3; no modifica instalaciones."""
import argparse
import ast
import hashlib
import json
import math
from pathlib import Path
import sys
import time
import tomllib

import bpy
import bmesh

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT/'src'), str(ROOT/'blender')]
from foliage_lab import configure, leaf_geometry, render, rig, sha, write
from generate_oak import material, mesh_report
from treegen.foliage import digest


def raw_stats(mesh):
    mesh.calc_loop_triangles()
    if not mesh.vertices or len(mesh.loop_triangles) > 300000:
        raise ValueError(f'Malla fuera del ensayo: {len(mesh.vertices)} vértices / {len(mesh.loop_triangles)} triángulos; máximo intermedio 300000')
    bounds = [[fn(v.co[k] for v in mesh.vertices) for k in range(3)] for fn in (min, max)]
    return {'vertices': len(mesh.vertices), 'triangles': len(mesh.loop_triangles), 'bounds_blender': bounds,
        'triangles_by_material': {m.name if m else 'None': sum(t.material_index == i for t in mesh.loop_triangles)
            for i, m in enumerate(mesh.materials)},
        'degenerate_triangles': sum(t.area <= 1e-10 for t in mesh.loop_triangles)}


def evaluated(obj):
    obj.update_tag()
    bpy.context.view_layer.update()
    graph = bpy.context.evaluated_depsgraph_get()
    return bpy.data.meshes.new_from_object(obj.evaluated_get(graph), depsgraph=graph)


def easy(addons, attempt):
    with bpy.data.libraries.load(str(addons/'easy_tree/assets/assets.blend'), link=False) as (_, loaded):
        loaded.node_groups = ['Simple Tree Generator']
    group = bpy.data.node_groups['Simple Tree Generator']
    # El adaptador usa nombres y API vigente; no ejecuta la asignación histórica
    # a modifier['Socket_*'] que ya falló en esta versión de Blender.
    wrapper = bpy.data.node_groups.new('AddonComparisonEasy', 'GeometryNodeTree')
    wrapper.interface.new_socket(name='Geometry', in_out='OUTPUT', socket_type='NodeSocketGeometry')
    node = wrapper.nodes.new('GeometryNodeGroup')
    node.node_tree = group
    initial = {s.name: str(s.default_value) if s.type in ('MATERIAL', 'OBJECT', 'MENU') else s.default_value
        for s in node.inputs if hasattr(s, 'default_value') and s.type not in ('VECTOR', 'ROTATION')}
    controls = {**attempt['controls'], 'Seed': attempt['seed'], 'Wind': False, 'Add Leaves': True}
    if not 1 <= controls.get('Num Levels', 6) <= 6:
        raise ValueError('Demasiados niveles Easy Tree')
    for key, value in controls.items():
        node.inputs[key].default_value = value
    adaptations = []
    settings = attempt.get('graph', {})
    if 'wood_profile' in settings:
        bpy.data.node_groups['Tree to Mesh'].nodes['Curve Circle'].inputs['Resolution'].default_value = settings['wood_profile']
        adaptations.append('Resolución del perfil de madera en el grupo cargado: '+str(settings['wood_profile']))
    twig = bpy.data.node_groups['Tree to Mesh and Leaves'].nodes['Make Twig & Leaf']
    for key in ('Count', 'X Divisions', 'Y Divisions'):
        if key in settings:
            twig.inputs[key].default_value = settings[key]
            adaptations.append('Entrada interna de ramilla '+key+'='+str(settings[key]))
    if settings.get('geometric_leaf'):
        # Sustitución local de la hoja texturizada, conservando la ramilla,
        # inserciones y distribución del addon. No se altera su archivo .blend.
        p = {'variant': 'folded-hex', 'length_m': settings.get('leaf_length', .22),
             'width_ratio': .65, 'fold_deg': 25, 'origin_m': [0, 0, 0],
             'axes': [[0, 1, 0], [-1, 0, 0], [0, 0, 1]]}
        coords, faces = leaf_geometry(p)
        mesh = bpy.data.meshes.new('ComparisonLeaf')
        mesh.from_pydata(coords, [], faces)
        mesh.materials.append(material('Comparison_Leaves', (.23, .43, .065)))
        leaf = bpy.data.objects.new('ComparisonLeaf', mesh)
        bpy.context.collection.objects.link(leaf)
        leaf.hide_render = True
        tree = bpy.data.node_groups['Make Leaf']
        info = tree.nodes.new('GeometryNodeObjectInfo')
        info.inputs['Object'].default_value = leaf
        out = next(n for n in tree.nodes if n.type == 'GROUP_OUTPUT')
        tree.links.new(info.outputs['Geometry'], out.inputs[0])
        adaptations.append('Sustitución en memoria de Make Leaf por hoja geométrica opaca RF1; ramilla nativa conservada')
    realize = wrapper.nodes.new('GeometryNodeRealizeInstances')
    out = wrapper.nodes.new('NodeGroupOutput')
    wrapper.links.new(node.outputs[0], realize.inputs['Geometry'])
    wrapper.links.new(realize.outputs['Geometry'], out.inputs[0])
    obj = bpy.data.objects.new('EasyTree', bpy.data.meshes.new('EasyHost'))
    bpy.context.collection.objects.link(obj)
    mod = obj.modifiers.new('Easy', 'NODES')
    mod.node_group = wrapper
    mesh = evaluated(obj)
    obj.hide_set(True)
    obj.hide_render = True
    return mesh, {'starting_preset': 'TALL' if attempt['age'] == 'adulto' else 'LARGE',
        'initial_group_inputs': initial, 'controls': controls, 'graph_adaptations': adaptations,
        'native_leaf_materials': [m.name for m in mesh.materials if m and 'Leaves' in m.name],
        'algorithm': 'Geometry Nodes del asset Easy Tree instalado'}


def sapling(addons, attempt):
    sys.path.insert(0, str(addons))
    import sapling_tree_gen as addon
    addon.register()
    preset = addons/'sapling_tree_gen/presets/small_maple.py'
    initial = ast.literal_eval(preset.read_text())
    controls = {**initial, **attempt['controls'], 'seed': attempt['seed'],
        'scale': 10 if attempt['age'] == 'adulto' else 9, 'showLeaves': True,
        'useArm': False, 'armAnim': False, 'leafAnim': False, 'prune': False, 'makeMesh': False}
    # El módulo declara handleType dos veces; la definición efectiva es ENUM.
    # Consultar el RNA evita inferir el tipo desde la primera declaración.
    properties = bpy.ops.curve.tree_add.get_rna_type().properties
    rna_adaptations = []
    for key, value in list(controls.items()):
        if key not in properties:
            controls.pop(key)
        elif properties[key].type == 'ENUM':
            controls[key] = str(value)
        elif properties[key].type == 'INT' and isinstance(value, str):
            controls[key] = int(value)
        if key in controls and type(controls[key]) is not type(value):
            rna_adaptations.append({'parameter': key, 'original': value, 'adapted': controls[key], 'rna_type': properties[key].type})
    if controls['levels'] > 3 or controls['branches'][1] > 30 or controls['branches'][2] > 10:
        raise ValueError('Ramificación Sapling fuera del ensayo acotado')
    bpy.ops.curve.tree_add('EXEC_DEFAULT', **controls)
    objects = [o for o in bpy.data.objects if o.type in ('CURVE', 'MESH')]
    coords, faces, mats, smooth = [], [], [], []
    for obj in objects:
        mesh = evaluated(obj)
        offset = len(coords)
        coords.extend(tuple(obj.matrix_world@v.co) for v in mesh.vertices)
        faces.extend(tuple(i+offset for i in p.vertices) for p in mesh.polygons)
        mats.extend([1 if obj.name.startswith('leaves') else 0]*len(mesh.polygons))
        smooth.extend(p.use_smooth for p in mesh.polygons)
        obj.hide_set(True)
        obj.hide_render = True
        bpy.data.meshes.remove(mesh)
    result = bpy.data.meshes.new('SaplingEvaluated')
    result.from_pydata(coords, [], faces)
    result.materials.append(material('Sapling_Bark', (.24, .105, .045)))
    result.materials.append(material('Sapling_Leaves', (.23, .43, .065)))
    for p, mat, shade in zip(result.polygons, mats, smooth):
        p.material_index, p.use_smooth = mat, shade
    result.update()
    changes = {k: v for k, v in controls.items() if k not in initial or v != initial[k]}
    return result, {'starting_preset': 'small_maple', 'starting_preset_sha256': sha(preset),
        'controls': controls, 'changes_from_preset': changes, 'graph_adaptations': [], 'rna_type_adaptations': rna_adaptations,
        'native_species_claim': False, 'algorithm': 'Sapling instalado; preset de arce como base de copa ancha, no un roble botánico'}


def normalize(mesh, height):
    low = min(v.co.z for v in mesh.vertices)
    high = max(v.co.z for v in mesh.vertices)
    scale = height/(high-low)
    for v in mesh.vertices:
        v.co = (v.co.x*scale, v.co.y*scale, (v.co.z-low)*scale)
    mesh.update()
    return {'type': 'uniform_scale_and_base_translation', 'scale': scale, 'original_z': [low, high], 'height_m': height}


def standardize(mesh):
    materials = [m.name if m else 'None' for m in mesh.materials]
    kinds = [int('leav' in materials[p.material_index].lower()) if p.material_index < len(materials) else 0 for p in mesh.polygons]
    mesh.materials.clear()
    for name, color in [('Oak_Bark', (.24, .105, .045)), ('Oak_Leaves', (.23, .43, .065))]:
        mat = material(name, color)
        mat.use_backface_culling = False
        mesh.materials.append(mat)
    for p, kind in zip(mesh.polygons, kinds):
        p.material_index = kind
        p.use_smooth = False
    return materials


def generate(attempt, addons, output):
    started = time.monotonic()
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete(use_global=False)
    sources = {str(p.relative_to(addons)): sha(p) for name in ('easy_tree', 'sapling_tree_gen')
        for p in sorted((addons/name).rglob('*')) if p.is_file() and p.suffix in ('.py', '.toml', '.blend')}
    mesh, details = (easy if attempt['engine'] == 'easy' else sapling)(addons, attempt)
    raw = raw_stats(mesh)
    native_hash = digest({'vertices': [list(v.co) for v in mesh.vertices],
        'polygons': [(list(p.vertices), p.material_index, p.use_smooth) for p in mesh.polygons]})
    target = 10 if attempt['age'] == 'adulto' else 9
    transform = normalize(mesh, target)
    original_materials = standardize(mesh)
    # Limpiar solo caras degeneradas (por ejemplo las puntas de curvas); no
    # simplificar ocultamente para cumplir el presupuesto.
    bm = bmesh.new()
    bm.from_mesh(mesh)
    bmesh.ops.triangulate(bm, faces=list(bm.faces))
    bad = [f for f in bm.faces if f.calc_area() <= 1e-10]
    removed = len(bad)
    if bad:
        bmesh.ops.delete(bm, geom=bad, context='FACES')
    loose = [v for v in bm.verts if not v.link_faces]
    if loose:
        bmesh.ops.delete(bm, geom=loose, context='VERTS')
    bm.to_mesh(mesh)
    bm.free()
    mesh.update()
    final_stats = raw_stats(mesh)
    metrics = mesh_report(mesh) if final_stats['triangles'] <= 10000 and not final_stats['degenerate_triangles'] else final_stats
    obj = bpy.data.objects.new('ComparisonTree', mesh)
    bpy.context.collection.objects.link(obj)
    bpy.ops.object.select_all(action='DESELECT')
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    configure()
    bpy.ops.wm.save_as_mainfile(filepath=str(output/'tree.blend'))
    within = metrics['triangles'] <= 10000 and metrics.get('degenerate_triangles', 0) == 0
    if within:
        bpy.ops.export_scene.gltf(filepath=str(output/'tree.glb'), export_format='GLB', use_selection=True, export_yup=True)
    row = {'version': 'addon-comparison-0.1.0', 'attempt': attempt, 'details': details,
        'raw': raw, 'normalization': transform, 'metrics': metrics, 'original_materials': original_materials,
        'removed_degenerate_faces': removed, 'within_budget': within, 'exported': within,
        'sources_sha256': sources, 'addon_sources_unchanged': sources == {p: sha(addons/p) for p in sources},
        'addon_versions': {n: tomllib.loads((addons/n/'blender_manifest.toml').read_text())['version'] for n in ('easy_tree', 'sapling_tree_gen')},
        'blender': bpy.app.version_string, 'blender_build': bpy.app.build_hash.decode(), 'blender_python': sys.version,
        'duration_seconds': round(time.monotonic()-started, 3), 'native_geometry_sha256': native_hash,
        'adapter_sources_sha256': {str(p.relative_to(ROOT)): sha(p) for p in
            [Path(__file__), ROOT/'blender/foliage_lab.py', ROOT/'blender/generate_oak.py', ROOT/'src/treegen/foliage.py']},
        'files_sha256': {p.name: sha(p) for p in output.iterdir() if p.suffix in ('.blend', '.glb')}}
    assert row['addon_sources_unchanged']
    write(output/'manifest.json', row)
    print(json.dumps({'id': attempt['id'], 'triangles': metrics['triangles'], 'within_budget': within}), flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--attempt', type=Path, required=True)
    parser.add_argument('--addons', type=Path, default=Path.home()/'.config/blender/5.2/extensions/blender_org')
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args(sys.argv[sys.argv.index('--')+1:])
    assert bpy.app.version[:3] == (5, 2, 1)
    args.output.mkdir(parents=True, exist_ok=False)
    generate(json.loads(args.attempt.read_text()), args.addons, args.output.resolve())


if __name__ == '__main__':
    main()
