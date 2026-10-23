"""Grafos propios oak_geometry_nodes 0.1.0. Sin construcción de ramas en Python."""
import math
import json
from pathlib import Path
import bpy

VERSION = '0.1.0'
PARAMETERS = {
    'height_m': ('Height', 'NodeSocketFloat'),
    'base_radius_m': ('Base Radius', 'NodeSocketFloat'),
    'curvature': ('Curvature', 'NodeSocketFloat'),
    'primary_branches': ('Primary Count', 'NodeSocketInt'),
    'max_depth': ('Depth', 'NodeSocketInt'),
    'branch_length_ratio': ('Branch Ratio', 'NodeSocketFloat'),
    'inclination_deg': ('Inclination', 'NodeSocketFloat'),
    'asymmetry': ('Asymmetry', 'NodeSocketFloat'),
    'foliage_density': ('Density', 'NodeSocketFloat'),
    'foliage_scale_m': ('Foliage Scale', 'NodeSocketFloat'),
}
_RULES = json.loads((Path(__file__).resolve().parents[1] / 'schemas/tree-spec.schema.json').read_text())['properties']['parameters']['properties']
SOCKET_LIMITS = {PARAMETERS[key][0]: (rule['minimum'], rule['maximum']) for key, rule in _RULES.items()}
SOCKET_LIMITS.update({'Structure Seed': (0, 2147483646), 'Foliage Seed': (0, 2147483646),
                      'Mass Count': (0, 4), 'Profile Resolution': (8, 8), 'Scale': (.2, 3.)})


class Graph:
    def __init__(self, name, inputs, outputs):
        self.tree = bpy.data.node_groups.new(name, 'GeometryNodeTree')
        self.sockets = {}
        for direction, definitions in [('INPUT', inputs), ('OUTPUT', outputs)]:
            for name, kind in definitions:
                socket = self.tree.interface.new_socket(name=name, in_out=direction, socket_type=kind)
                if direction == 'INPUT':
                    self.sockets[name] = socket.identifier
                    if name in SOCKET_LIMITS:
                        socket.min_value, socket.max_value = SOCKET_LIMITS[name]
        self.input = self.node('NodeGroupInput')
        self.output = self.node('NodeGroupOutput')

    def node(self, kind, **properties):
        node = self.tree.nodes.new(kind)
        for key, value in properties.items():
            setattr(node, key, value)
        # Posiciones legibles al abrir el .blend; cada nodo conserva su nombre de tipo.
        index = len(self.tree.nodes) - 1
        node.location = ((index % 8) * 210, -(index // 8) * 210)
        return node

    def set(self, node, socket, value):
        target = node.inputs[socket]
        if isinstance(value, bpy.types.NodeSocket):
            self.tree.links.new(value, target)
        else:
            target.default_value = value
        return node

    def op(self, operation, a, b=None):
        n = self.node('ShaderNodeMath', operation=operation)
        self.set(n, 0, a)
        if b is not None:
            self.set(n, 1, b)
        return n.outputs[0]

    def vector(self, x=0., y=0., z=0.):
        n = self.node('ShaderNodeCombineXYZ')
        for key, value in zip(('X', 'Y', 'Z'), (x, y, z)):
            self.set(n, key, value)
        return n.outputs[0]

    def random(self, seed, minimum, maximum, vector=False, stream=0):
        n = self.node('FunctionNodeRandomValue', data_type='FLOAT_VECTOR' if vector else 'FLOAT')
        self.set(n, 'Min', minimum)
        self.set(n, 'Max', maximum)
        self.set(n, 'Seed', self.op('ADD', seed, stream))
        return n.outputs['Value']

    def group(self, tree, **inputs):
        n = self.node('GeometryNodeGroup')
        n.node_tree = tree
        for key, value in inputs.items():
            self.set(n, key, value)
        return n

    def join(self, *geometries):
        n = self.node('GeometryNodeJoinGeometry')
        for geometry in geometries:
            self.set(n, 'Geometry', geometry)
        return n.outputs[0]


GEO = 'NodeSocketGeometry'
FLOAT = 'NodeSocketFloat'
INT = 'NodeSocketInt'


def tapered_curve(g, length, radius, angle, curvature, count):
    """Una curva canónica en XZ, radio en metros almacenado por punto."""
    line = g.node('GeometryNodeCurvePrimitiveLine')
    g.set(line, 'End', g.vector(z=length))
    resample = g.node('GeometryNodeResampleCurve')
    g.set(resample, 'Mode', 'Count')
    g.set(resample, 'Curve', line.outputs['Curve'])
    g.set(resample, 'Count', count)
    factor = g.node('GeometryNodeSplineParameter').outputs['Factor']
    distance = g.op('MULTIPLY', factor, length)
    radians = g.op('MULTIPLY', angle, math.pi / 180)
    bend = g.op('MULTIPLY', g.op('MULTIPLY', factor, factor), curvature)
    x = g.op('ADD', g.op('MULTIPLY', distance, g.op('SINE', radians)),
             g.op('MULTIPLY', length, bend))
    z = g.op('MULTIPLY', distance, g.op('COSINE', radians))
    pos = g.node('GeometryNodeSetPosition')
    g.set(pos, 'Geometry', resample.outputs['Curve'])
    g.set(pos, 'Position', g.vector(x=x, z=z))
    taper = g.node('GeometryNodeSetCurveRadius')
    g.set(taper, 'Curve', pos.outputs['Geometry'])
    g.set(taper, 'Radius', g.op('MULTIPLY', radius,
                              g.op('SUBTRACT', 1, g.op('MULTIPLY', factor, .93))))
    return taper.outputs['Curve']


def tips(g, curves):
    trim = g.node('GeometryNodeTrimCurve')
    g.set(trim, 'Curve', curves)
    g.set(trim, 'Start', .999)
    g.set(trim, 'End', 1.)
    pts = g.node('GeometryNodeCurveToPoints', mode='COUNT')
    g.set(pts, 'Curve', trim.outputs['Curve'])
    g.set(pts, 'Count', 1)
    return pts.outputs['Points']


def structure_group():
    definitions = [value for key, value in PARAMETERS.items() if not key.startswith('foliage')]
    g = Graph('Oak_Structure_v' + VERSION, definitions + [('Structure Seed', INT)],
              [('Curves', GEO), ('Tips', GEO), ('Trunk', GEO), ('Primary', GEO), ('Secondary', GEO)])
    i = g.input.outputs
    trunk = tapered_curve(g, i['Height'], i['Base Radius'], 0., i['Curvature'], 12)
    # Puntos distribuidos sobre la curva real: las uniones siguen su curvatura.
    points = g.node('GeometryNodeMeshLine')
    g.set(points, 'Count', i['Primary Count'])
    index = g.node('GeometryNodeInputIndex').outputs['Index']
    step = g.op('DIVIDE', index, g.op('MAXIMUM', g.op('SUBTRACT', i['Primary Count'], 1), 1))
    factor = g.op('ADD', .38, g.op('MULTIPLY', step, .42))
    sample = g.node('GeometryNodeSampleCurve', mode='FACTOR')
    g.set(sample, 'Curves', trunk)
    g.set(sample, 'Factor', factor)
    attach = g.node('GeometryNodeSetPosition')
    g.set(attach, 'Geometry', points.outputs['Mesh'])
    g.set(attach, 'Position', sample.outputs['Position'])
    branch = tapered_curve(g, g.op('MULTIPLY', i['Height'], i['Branch Ratio']),
                           g.op('MULTIPLY', i['Base Radius'], .42), i['Inclination'], .1, 7)
    azimuth = g.op('ADD', g.op('MULTIPLY', index, 2.399963),
                   g.random(i['Structure Seed'], -math.pi, math.pi, stream=1))
    variation = g.op('ADD', 1., g.op('MULTIPLY', i['Asymmetry'],
                                    g.random(i['Structure Seed'], -.35, .25, stream=2)))
    primary = g.node('GeometryNodeInstanceOnPoints')
    g.set(primary, 'Points', attach.outputs['Geometry'])
    g.set(primary, 'Instance', branch)
    g.set(primary, 'Rotation', g.vector(z=azimuth))
    g.set(primary, 'Scale', g.vector(variation, variation, variation))
    realize = g.node('GeometryNodeRealizeInstances')
    g.set(realize, 'Geometry', primary.outputs['Instances'])
    primary_curves = realize.outputs['Geometry']
    # Dos secundarios por primario. El tangente y la posición proceden de sus curvas.
    trim = g.node('GeometryNodeTrimCurve')
    g.set(trim, 'Curve', primary_curves)
    g.set(trim, 'Start', .48)
    g.set(trim, 'End', .78)
    secondary_points = g.node('GeometryNodeCurveToPoints', mode='COUNT')
    g.set(secondary_points, 'Curve', trim.outputs['Curve'])
    g.set(secondary_points, 'Count', 2)
    secondary_curve = tapered_curve(g, g.op('MULTIPLY', i['Height'], g.op('MULTIPLY', i['Branch Ratio'], .48)),
                                    g.op('MULTIPLY', i['Base Radius'], .15), 48., .05, 5)
    rotate = g.node('FunctionNodeRotateEuler', rotation_type='EULER', space='LOCAL')
    g.set(rotate, 'Rotation', secondary_points.outputs['Rotation'])
    g.set(rotate, 'Rotate By', g.vector(z=g.random(i['Structure Seed'], -math.pi, math.pi, stream=3)))
    secondary = g.node('GeometryNodeInstanceOnPoints')
    g.set(secondary, 'Points', secondary_points.outputs['Points'])
    g.set(secondary, 'Instance', secondary_curve)
    g.set(secondary, 'Rotation', rotate.outputs['Rotation'])
    secondary_realize = g.node('GeometryNodeRealizeInstances')
    g.set(secondary_realize, 'Geometry', secondary.outputs['Instances'])
    switch = g.node('GeometryNodeSwitch', input_type='GEOMETRY')
    g.set(switch, 'Switch', g.op('GREATER_THAN', i['Depth'], 1))
    g.set(switch, 'True', secondary_realize.outputs['Geometry'])
    all_curves = g.join(trunk, primary_curves, switch.outputs['Output'])
    g.set(g.output, 'Curves', all_curves)
    g.set(g.output, 'Tips', tips(g, all_curves))
    for name, curves in [('Trunk', trunk), ('Primary', primary_curves), ('Secondary', switch.outputs['Output'])]:
        g.set(g.output, name, curves)
    return g


def volume_group():
    g = Graph('Oak_Volume_v' + VERSION,
              [('Curves', GEO), ('Profile Resolution', INT), ('Bark', 'NodeSocketMaterial')], [('Mesh', GEO)])
    circle = g.node('GeometryNodeCurvePrimitiveCircle')
    g.set(circle, 'Resolution', g.input.outputs['Profile Resolution'])
    g.set(circle, 'Radius', 1.)
    mesh = g.node('GeometryNodeCurveToMesh')
    g.set(mesh, 'Curve', g.input.outputs['Curves'])
    g.set(mesh, 'Profile Curve', circle.outputs['Curve'])
    g.set(mesh, 'Scale', g.node('GeometryNodeInputRadius').outputs['Radius'])
    g.set(mesh, 'Fill Caps', True)
    mat = g.node('GeometryNodeSetMaterial')
    g.set(mat, 'Geometry', mesh.outputs['Mesh'])
    g.set(mat, 'Material', g.input.outputs['Bark'])
    g.set(g.output, 'Mesh', mat.outputs['Geometry'])
    return g


def foliage_group():
    g = Graph('Oak_Foliage_v' + VERSION,
              [('Tips', GEO), ('Mass Count', INT), ('Scale', FLOAT), ('Foliage Seed', INT),
               ('Leaves', 'NodeSocketMaterial')], [('Mesh', GEO)])
    i = g.input.outputs
    points = g.node('GeometryNodeMeshLine')
    # Count 0 en Mesh Line se limita a 1: el switch inferior gestiona copa vacía.
    g.set(points, 'Count', g.op('MAXIMUM', i['Mass Count'], 1))
    move = g.node('GeometryNodeSetPosition')
    g.set(move, 'Geometry', points.outputs['Mesh'])
    random_offset = g.random(i['Foliage Seed'], (-.32, -.32, -.18), (.32, .32, .18), vector=True)
    scale_offset = g.node('ShaderNodeVectorMath', operation='SCALE')
    g.set(scale_offset, 0, random_offset)
    g.set(scale_offset, 'Scale', i['Scale'])
    g.set(move, 'Position', scale_offset.outputs['Vector'])
    ico = g.node('GeometryNodeMeshIcoSphere')
    g.set(ico, 'Radius', i['Scale'])
    g.set(ico, 'Subdivisions', 1)
    material = g.node('GeometryNodeSetMaterial')
    g.set(material, 'Geometry', ico.outputs['Mesh'])
    g.set(material, 'Material', i['Leaves'])
    cluster = g.node('GeometryNodeInstanceOnPoints')
    g.set(cluster, 'Points', move.outputs['Geometry'])
    g.set(cluster, 'Instance', material.outputs['Geometry'])
    g.set(cluster, 'Scale', g.random(i['Foliage Seed'], (.9, .8, .65), (1.3, 1.1, .9), vector=True, stream=1))
    g.set(cluster, 'Rotation', g.random(i['Foliage Seed'], (0., 0., 0.), (.3, .3, 6.28), vector=True, stream=2))
    instances = g.node('GeometryNodeInstanceOnPoints')
    g.set(instances, 'Points', i['Tips'])
    g.set(instances, 'Instance', cluster.outputs['Instances'])
    g.set(instances, 'Rotation', g.random(i['Foliage Seed'], (0., 0., 0.), (.15, .15, 6.28), vector=True, stream=3))
    realized = g.node('GeometryNodeRealizeInstances')
    g.set(realized, 'Geometry', instances.outputs['Instances'])
    switch = g.node('GeometryNodeSwitch', input_type='GEOMETRY')
    g.set(switch, 'Switch', g.op('GREATER_THAN', i['Mass Count'], 0))
    g.set(switch, 'True', realized.outputs['Geometry'])
    g.set(g.output, 'Mesh', switch.outputs['Output'])
    return g


def build_generator(bark, leaves):
    structure, volume, foliage = structure_group(), volume_group(), foliage_group()
    g = Graph('Oak_Generator_v' + VERSION,
              list(PARAMETERS.values()) + [('Structure Seed', INT), ('Foliage Seed', INT),
                                            ('Profile Resolution', INT)], [('Geometry', GEO)])
    structure_node = g.group(structure.tree)
    for name in structure.sockets:
        g.set(structure_node, name, g.input.outputs[name])
    volume_node = g.group(volume.tree, Curves=structure_node.outputs['Curves'], Bark=bark)
    g.set(volume_node, 'Profile Resolution', g.input.outputs['Profile Resolution'])
    foliage_node = g.group(foliage.tree, Tips=structure_node.outputs['Tips'], Leaves=leaves)
    for name, parent in [('Scale', 'Foliage Scale'), ('Foliage Seed', 'Foliage Seed')]:
        g.set(foliage_node, name, g.input.outputs[parent])
    count = g.op('FLOOR', g.op('ADD', g.op('MULTIPLY', g.input.outputs['Density'], 4), .5))
    g.set(foliage_node, 'Mass Count', count)
    joined = g.join(volume_node.outputs['Mesh'], foliage_node.outputs['Mesh'])
    box = g.node('GeometryNodeBoundBox')
    g.set(box, 'Geometry', joined)
    low, high = g.node('ShaderNodeSeparateXYZ'), g.node('ShaderNodeSeparateXYZ')
    g.set(low, 'Vector', box.outputs['Min'])
    g.set(high, 'Vector', box.outputs['Max'])
    scale_z = g.op('DIVIDE', g.input.outputs['Height'], g.op('SUBTRACT', high.outputs['Z'], low.outputs['Z']))
    transform = g.node('GeometryNodeTransform')
    g.set(transform, 'Geometry', joined)
    g.set(transform, 'Scale', g.vector(1., 1., scale_z))
    g.set(transform, 'Translation', g.vector(z=g.op('MULTIPLY', g.op('MULTIPLY', low.outputs['Z'], -1), scale_z)))
    g.set(g.output, 'Geometry', transform.outputs['Geometry'])
    return g, structure
