"""Adaptador experimental F5: curvas Python → procesadores Q3 congelados."""
import json
from pathlib import Path
import sys
import bpy
from mathutils import Vector

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT/'src'), str(ROOT/'blender')]
from treegen.branch_structure import generate_structure
from treegen.branch_space import separate, measure
from oak_nodes import Graph, GEO, INT, PARAMETERS, tips
from oak_nodes_v4 import build_generator as historical_build
from generate_oak import evaluated_output, mesh_report
from foliage_lab import evaluated


def index_value(g, values, data_type):
    node = g.node('GeometryNodeIndexSwitch', data_type=data_type)
    node.index_switch_items.clear()
    for _ in values:
        node.index_switch_items.new()
    g.set(node, 'Index', g.node('GeometryNodeInputIndex').outputs['Index'])
    for i, value in enumerate(values):
        g.set(node, i+1, value)
    return node.outputs['Output']


def curve_graph(structure):
    definitions = [v for k, v in PARAMETERS.items() if not k.startswith('foliage')]
    g = Graph('Oak_Structure_F5_Baked_v0.1.0', definitions+[('Structure Seed', INT)],
              [(s, GEO) for s in ('Curves', 'Tips', 'Trunk', 'Primary', 'Secondary')])
    channels = {i: [] for i in range(3)}
    for branch in structure.branches:
        line = g.node('GeometryNodeMeshLine')
        g.set(line, 'Count', len(branch.points))
        position = g.node('GeometryNodeSetPosition')
        g.set(position, 'Geometry', line.outputs['Mesh'])
        g.set(position, 'Position', index_value(g, branch.points, 'VECTOR'))
        curve = g.node('GeometryNodeMeshToCurve')
        g.set(curve, 'Mesh', position.outputs['Geometry'])
        radius = g.node('GeometryNodeSetCurveRadius')
        g.set(radius, 'Curve', curve.outputs['Curve'])
        g.set(radius, 'Radius', index_value(g, branch.radii, 'FLOAT'))
        channels[branch.level].append(radius.outputs['Curve'])
    outputs = []
    for level, name in enumerate(('Trunk', 'Primary', 'Secondary')):
        geometry = g.join(*reversed(channels[level]))
        g.set(g.output, name, geometry)
        outputs.append(geometry)
    all_curves = g.join(*outputs)
    g.set(g.output, 'Curves', all_curves)
    g.set(g.output, 'Tips', tips(g, all_curves))
    return g


def processor(structure, audit):
    def build(bark, leaves):
        generator, _ = historical_build(bark, leaves)
        node = next(n for n in generator.tree.nodes if n.type=='GROUP' and n.node_tree.name.startswith('Oak_Structure'))
        old = node.node_tree
        graph = curve_graph(structure)
        # Cambiar el grupo preserva la interfaz; reconectar salidas explícitamente.
        outgoing = [(link.from_socket.name, link.to_socket) for output in node.outputs for link in list(output.links)]
        node.node_tree = graph.tree
        for name, target in outgoing:
            generator.tree.links.new(node.outputs[name], target)
        if old.users == 0:
            bpy.data.node_groups.remove(old)
        values = {PARAMETERS[k][0]: v for k, v in audit['spec']['parameters'].items()}
        values.update({'Structure Seed':structure.seed, 'Foliage Seed':audit['foliage_seed'], 'Profile Resolution':8})
        raw = evaluated_output(generator, values, 'Raw Wood')
        bounds = mesh_report(raw)['bounds_blender']
        scale_z = audit['spec']['parameters']['height_m']/(bounds[1][2]-bounds[0][2])
        bpy.data.meshes.remove(raw)
        errors, radius_errors = [], []
        # Auditar directamente los puntos/radios de los canales que alimentan volumen.
        for level, channel in enumerate(('Trunk','Primary','Secondary')):
            selected = [b for b in structure.branches if b.level==level]
            if not selected:
                continue
            debug = Graph('F5_AxisAudit', [], [('Geometry',GEO)])
            source = debug.group(graph.tree)
            store = debug.node('GeometryNodeStoreNamedAttribute', data_type='FLOAT', domain='POINT')
            debug.set(store,'Geometry',source.outputs[channel]);debug.set(store,'Name','f5_radius')
            debug.set(store,'Value',debug.node('GeometryNodeInputRadius').outputs['Radius'])
            mesh = debug.node('GeometryNodeCurveToMesh')
            debug.set(mesh,'Curve',store.outputs['Geometry'])
            debug.set(debug.output,'Geometry',mesh.outputs['Mesh'])
            data = evaluated(debug)
            expected = [p for b in selected for p in b.points]
            radii = [r for b in selected for r in b.radii]
            assert len(data.vertices)==len(expected), (channel,len(data.vertices),len(expected))
            for i, p in enumerate(expected):
                errors.append((data.vertices[i].co-Vector(p)).length)
                radius_errors.append(abs(data.attributes['f5_radius'].data[i].value-radii[i]))
            bpy.data.meshes.remove(data)
        assert max(errors)<1e-5 and max(radius_errors)<1e-6, (max(errors),max(radius_errors))
        audit.update(axis_max_error_m=max(errors), radius_max_error_m=max(radius_errors),
                     final_metric=measure(structure,scale_z), raw_metric=measure(structure),
                     actual_normalization_scale_z=scale_z)
        return generator, graph
    return build


def main(path):
    job = json.loads(Path(path).read_text())
    from generate_crossed_oak import generate
    import generate_blueprint
    from foliage_lab import write
    structure = generate_structure(job['spec'])
    rule = None
    if job['f5_variant']=='candidate':
        structure, rule = separate(structure)
    elif job['f5_variant']!='baseline':
        raise ValueError('Variante F5 inválida')
    audit = {'spec':job['spec'], 'foliage_seed':job['seeds']['foliage'], 'rule':rule,
             'structure_sha256':structure.digest(), 'structure':structure.document(),
             'variant':job['f5_variant'], 'production_recipe':False}
    generate_blueprint.build_generator = processor(structure, audit)
    generate(job)
    out = Path(job['output'])
    manifest = json.loads((out/'manifest.json').read_text())
    assert manifest['metrics']['triangles']<7000
    assert len(manifest['metrics']['triangles_by_material'])<=2
    assert abs(manifest['normalization']['scale'][2]-audit['actual_normalization_scale_z'])<1e-8
    manifest.update(f5=audit, base_generation='f5_python_experimental',
                    experimental=True, historical_recipe_used_as_processor=True)
    # El procesador referencia el componente histórico; este campo declara la
    # sustitución experimental para evitar atribuir el GLB a la receta aprobada.
    manifest['experimental_base_substitution']='branch-structure-0.1.0'
    write(out/'manifest.json',manifest)
    write(out/'structure.json',audit)


if __name__=='__main__':
    main(sys.argv[sys.argv.index('--')+1])
