"""Inspección reproducible de addons instalados; ejecutar en Blender aislado.

No instala extensiones, guarda preferencias ni modifica sus fuentes. Las pruebas
acotadas evalúan grafos y geometría; no constituyen una comparación estética.
"""
import argparse
import ast
import hashlib
import json
from pathlib import Path
import sys
import tomllib

import bpy


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def value(item):
    if isinstance(item, (str, int, float, bool)) or item is None:
        return item
    if hasattr(item, 'name'):
        return {'datablock': item.name}
    try:
        return list(item)
    except TypeError:
        return str(item)


def mesh_hash(mesh):
    payload = [[list(v.co) for v in mesh.vertices], [list(p.vertices) for p in mesh.polygons]]
    return hashlib.sha256(json.dumps(payload).encode()).hexdigest()


def easy_tree(root, output):
    asset = root/'easy_tree/assets/assets.blend'
    with bpy.data.libraries.load(str(asset), link=False) as (_, loaded):
        loaded.node_groups = ['Simple Tree Generator']
    graphs = {}
    for group in bpy.data.node_groups:
        graphs[group.name] = {
            'inputs': [{'name': s.name, 'id': s.identifier, 'type': s.socket_type,
                        'default': value(getattr(s, 'default_value', None))}
                       for s in group.interface.items_tree if s.item_type == 'SOCKET' and s.in_out == 'INPUT'],
            'nodes': [{'name': n.name, 'type': n.bl_idname,
                       'group': n.node_tree.name if n.bl_idname == 'GeometryNodeGroup' else None,
                       'properties': {k: value(getattr(n, k)) for k in
                           ('operation', 'data_type', 'domain', 'mode', 'input_type', 'axis', 'integer') if hasattr(n, k)},
                       'defaults': {s.identifier: value(s.default_value) for s in n.inputs
                                    if not s.is_linked and hasattr(s, 'default_value')}} for n in group.nodes],
            'links': [[l.from_node.name, l.from_socket.identifier, l.to_node.name, l.to_socket.identifier]
                      for l in group.links]}
    (output/'easy-tree-graphs.json').write_text(json.dumps(graphs, indent=2)+'\n')
    group = bpy.data.node_groups['Simple Tree Generator']
    modifier = bpy.context.object.modifiers.new('EasyTreeAudit', 'NODES')
    modifier.node_group = group
    try:
        modifier['Socket_16'] = 17
        legacy = 'passed'
    except TypeError as exc:
        legacy = type(exc).__name__+': '+str(exc)
    # Comprobar la API actual de sockets sin cambiar el addon instalado.
    for s in group.interface.items_tree:
        controls = {'Num Levels': 2, 'Trunk Height': 1, 'Treetop Height': 1,
                    'Branch Length': 2, 'Seed': 17, 'Add Leaves': False, 'Wind': False}
        if s.item_type == 'SOCKET' and s.in_out == 'INPUT' and s.name in controls:
            getattr(modifier.properties.inputs, s.identifier).value = controls[s.name]
    bpy.context.object.update_tag()
    bpy.context.view_layer.update()
    graph = bpy.context.evaluated_depsgraph_get()
    mesh = bpy.data.meshes.new_from_object(bpy.context.object.evaluated_get(graph), depsgraph=graph)
    mesh.calc_loop_triangles()
    minimal = {'vertices': len(mesh.vertices), 'triangles': len(mesh.loop_triangles)}
    bpy.data.meshes.remove(mesh)
    bpy.context.object.modifiers.remove(modifier)

    def evaluate(name, controls):
        wrapper = bpy.data.node_groups.new('AuditWrapper', 'GeometryNodeTree')
        wrapper.interface.new_socket(name='Geometry', in_out='OUTPUT', socket_type='NodeSocketGeometry')
        node = wrapper.nodes.new('GeometryNodeGroup')
        node.node_tree = bpy.data.node_groups[name]
        for key, v in controls.items():
            node.inputs[key].default_value = v
        realize = wrapper.nodes.new('GeometryNodeRealizeInstances')
        wrapper.links.new(node.outputs[0], realize.inputs['Geometry'])
        out = wrapper.nodes.new('NodeGroupOutput')
        wrapper.links.new(realize.outputs['Geometry'], out.inputs[0])
        obj = bpy.data.objects.new('Audit', bpy.data.meshes.new('AuditHost'))
        bpy.context.collection.objects.link(obj)
        mod = obj.modifiers.new('Audit', 'NODES')
        mod.node_group = wrapper
        bpy.context.view_layer.update()
        graph = bpy.context.evaluated_depsgraph_get()
        mesh = bpy.data.meshes.new_from_object(obj.evaluated_get(graph), depsgraph=graph)
        mesh.calc_loop_triangles()
        row = {'group': name, 'controls': controls, 'vertices': len(mesh.vertices),
               'polygons': len(mesh.polygons), 'triangles': len(mesh.loop_triangles),
               'geometry_sha256': mesh_hash(mesh),
               'triangles_by_material': {m.name: sum(t.material_index == i for t in mesh.loop_triangles)
                                         for i, m in enumerate(mesh.materials) if m}}
        bpy.data.objects.remove(obj, do_unlink=True)
        bpy.data.meshes.remove(mesh)
        bpy.data.node_groups.remove(wrapper)
        return row

    probes = {
        'leaf_low': evaluate('Make Leaf', {'X Divisions': 2, 'Y Divisions': 2}),
        'leaf_twig_resolution': evaluate('Make Leaf', {'X Divisions': 3, 'Y Divisions': 4}),
        'twig': evaluate('Make Twig & Leaf', {'Count': 7}),
        'twig_repeat': evaluate('Make Twig & Leaf', {'Count': 7}),
        'small_tree': evaluate('Simple Tree Generator', {'Num Levels': 2, 'Trunk Height': 1,
            'Treetop Height': 1, 'Branch Length': 2, 'Min Height': 1, 'Leaf Density': 2., 'Seed': 17})}
    assert probes['twig']['geometry_sha256'] == probes['twig_repeat']['geometry_sha256']
    return {'groups': {name: len(g['nodes']) for name, g in graphs.items()},
            'inputs': graphs['Simple Tree Generator']['inputs'], 'legacy_assignment': legacy,
            'modern_input_evaluation': minimal, 'probes': probes,
            'leaf_material_alpha_sources': {m.name: [l.from_node.image.name for l in m.node_tree.links
                if l.to_socket.name == 'Alpha' and l.from_node.bl_idname == 'ShaderNodeTexImage' and l.from_node.image]
                for m in bpy.data.materials if m.node_tree and 'Leaves' in m.name},
            'images': [{'name': i.name, 'filepath': i.filepath, 'packed': bool(i.packed_file)} for i in bpy.data.images]}


def sapling(root):
    sys.path.insert(0, str(root))
    import sapling_tree_gen as addon
    addon.register()

    def generate(changes):
        bpy.ops.object.select_all(action='SELECT')
        bpy.ops.object.delete(use_global=False)
        controls = dict(seed=17, levels=3, branches=(0, 5, 3, 1), curveRes=(4, 4, 3, 1),
            segSplits=(0., 0., 0., 0.), baseSplits=0, showLeaves=True, leaves=12, leafShape='hex',
            scale=6., scaleV=0., useArm=False, armAnim=False, leafAnim=False, prune=False,
            makeMesh=False, bevel=True, bevelRes=0, resU=2)
        controls.update(changes)
        bpy.ops.curve.tree_add('EXEC_DEFAULT', **controls)
        tree = next(o for o in bpy.data.objects if o.type == 'CURVE')
        leaves = next(o for o in bpy.data.objects if o.name.startswith('leaves') and o.type == 'MESH')
        curves = [[list(p.co)+list(p.handle_left)+list(p.handle_right)+[p.radius]
                   for p in s.bezier_points] for s in tree.data.splines]
        leaves.data.calc_loop_triangles()
        return {'controls': controls, 'splines': len(tree.data.splines),
                'wood_curve_sha256': hashlib.sha256(json.dumps(curves).encode()).hexdigest(),
                'leaf_vertices': len(leaves.data.vertices), 'leaf_faces': len(leaves.data.polygons),
                'leaf_triangles': len(leaves.data.loop_triangles), 'leaf_geometry_sha256': mesh_hash(leaves.data)}

    probes = {label: generate(changes) for label, changes in (
        ('base', {}), ('repeat', {}), ('scale', {'leafScale': .35}), ('density', {'leaves': 24}),
        ('fan', {'leaves': -5}), ('rectangle', {'leafShape': 'rect'}),
        ('orientation', {'leafRotate': -90., 'leafDownAngle': 65.}))}
    repeat = probes['base']['leaf_geometry_sha256'] == probes['repeat']['leaf_geometry_sha256']
    same_wood = all(r['wood_curve_sha256'] == probes['base']['wood_curve_sha256'] for r in probes.values())
    assert repeat and same_wood
    fields = ('levels', 'branches', 'shape', 'shapeS', 'leafDist', 'leafShape', 'leaves',
              'leafScale', 'leafScaleX', 'leafRotate', 'leafDownAngle', 'attractUp')
    presets = {}
    for name in ('small_maple', 'weeping_willow', 'small_pine'):
        values = ast.literal_eval((root/'sapling_tree_gen/presets'/f'{name}.py').read_text())
        presets[name] = {k: values.get(k) for k in fields}
    return {'probes': probes, 'repeat_geometry': repeat, 'wood_preserved_by_tested_leaf_controls': same_wood,
            'preset_fields': presets}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--addons', type=Path, default=Path.home()/f'.config/blender/{bpy.app.version[0]}.{bpy.app.version[1]}/extensions/blender_org')
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args(sys.argv[sys.argv.index('--')+1:])
    args.output.mkdir(parents=True, exist_ok=False)
    sources = sorted(p for name in ('easy_tree', 'sapling_tree_gen') for p in (args.addons/name).rglob('*')
                     if p.is_file() and (p.suffix in ('.py', '.toml', '.blend') or p.name == 'README.md'))
    hashes = {str(p.relative_to(args.addons)): sha(p) for p in sources}
    report = {'blender': bpy.app.version_string, 'build': bpy.app.build_hash.decode(),
        'addons_root': str(args.addons), 'versions': {name: tomllib.loads((args.addons/name/'blender_manifest.toml').read_text())['version']
                                                   for name in ('easy_tree', 'sapling_tree_gen')},
        'sources_sha256': hashes, 'inspection_script_sha256': sha(Path(__file__)),
        'easy_tree': easy_tree(args.addons, args.output), 'sapling': sapling(args.addons),
        'visual_comparison_performed': False, 'godot_export_tested': False}
    assert hashes == {str(p.relative_to(args.addons)): sha(p) for p in sources}
    report['addon_sources_unchanged'] = True
    (args.output/'summary.json').write_text(json.dumps(report, indent=2)+'\n')
    print('Inspección y pruebas acotadas completadas; addons intactos. Sin evaluación estética ni exportación Godot.', flush=True)


if __name__ == '__main__':
    main()
