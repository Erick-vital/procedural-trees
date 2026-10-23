"""oak_geometry_nodes 0.2.0: revisión Q1 de la estructura, sin cambiar la copa.

Las curvas se calculan en nodos. El grupo 0.1.0 queda congelado en oak_nodes.py;
se reutilizan sus adaptadores de grafo, volumen, follaje y ajuste final de altura.
"""
import math
from oak_nodes import Graph, GEO, FLOAT, INT, PARAMETERS, tapered_curve, tips, volume_group, foliage_group

VERSION = '0.2.0'


def random(g, seed, minimum, maximum, stream, constant=False):
    value = g.random(seed, minimum, maximum, stream=stream)
    # ID explícito: evita depender de atributos heredados de las instancias.
    identity = g.op('ADD', 0, 0) if constant else g.node('GeometryNodeInputIndex').outputs['Index']
    g.set(value.node, 'ID', identity)
    return value


def attribute(g, name, kind='FLOAT'):
    node = g.node('GeometryNodeInputNamedAttribute', data_type=kind)
    g.set(node, 'Name', name)
    return node.outputs['Attribute']


def store(g, geometry, name, value, kind='FLOAT'):
    node = g.node('GeometryNodeStoreNamedAttribute', data_type=kind, domain='POINT')
    g.set(node, 'Geometry', geometry)
    g.set(node, 'Name', name)
    g.set(node, 'Value', value)
    return node.outputs['Geometry']


def clamp(g, value, low, high):
    return g.op('MINIMUM', g.op('MAXIMUM', value, low), high)


def branch_curves(g, roots, prefix, length, radius, azimuth, inclination, bend, resolution):
    """Propagar los controles de cada nacimiento a una curva, y deformarla en nodos."""
    fields = {'root': g.node('GeometryNodeInputPosition').outputs['Position'],
              'length': length, 'radius': radius, 'azimuth': azimuth,
              'inclination': inclination, 'bend': bend}
    for name, value in fields.items():
        roots = store(g, roots, prefix + name, value, 'FLOAT_VECTOR' if name == 'root' else 'FLOAT')
    line = g.node('GeometryNodeCurvePrimitiveLine')
    g.set(line, 'End', (0., 0., 1.))
    resample = g.node('GeometryNodeResampleCurve')
    g.set(resample, 'Curve', line.outputs['Curve'])
    g.set(resample, 'Count', resolution)
    instance = g.node('GeometryNodeInstanceOnPoints')
    g.set(instance, 'Points', roots)
    g.set(instance, 'Instance', resample.outputs['Curve'])
    realize = g.node('GeometryNodeRealizeInstances')
    g.set(realize, 'Geometry', instance.outputs['Instances'])
    values = {name: attribute(g, prefix + name, 'FLOAT_VECTOR' if name == 'root' else 'FLOAT') for name in fields}
    t = g.node('GeometryNodeSplineParameter').outputs['Factor']
    t2 = g.op('MULTIPLY', t, t)
    radians = g.op('MULTIPLY', values['inclination'], math.pi/180)
    # Crecimiento exterior y elevación progresiva de la punta: los controles de
    # inclinación/bend varían por rama, en lugar de rotar una única plantilla.
    outward = g.op('MULTIPLY', values['length'], g.op('MULTIPLY', g.op('SINE', radians),
                    g.op('SUBTRACT', t, g.op('MULTIPLY', .22, t2))))
    upward = g.op('MULTIPLY', values['length'], g.op('ADD', g.op('MULTIPLY', g.op('COSINE', radians), t),
                                                               g.op('MULTIPLY', values['bend'], t2)))
    offset = g.vector(g.op('MULTIPLY', outward, g.op('COSINE', values['azimuth'])),
                      g.op('MULTIPLY', outward, g.op('SINE', values['azimuth'])), upward)
    add = g.node('ShaderNodeVectorMath', operation='ADD')
    g.set(add, 0, values['root'])
    g.set(add, 1, offset)
    position = g.node('GeometryNodeSetPosition')
    g.set(position, 'Geometry', realize.outputs['Geometry'])
    g.set(position, 'Position', add.outputs['Vector'])
    taper = g.node('GeometryNodeSetCurveRadius')
    g.set(taper, 'Curve', position.outputs['Geometry'])
    g.set(taper, 'Radius', g.op('MULTIPLY', values['radius'], g.op('SUBTRACT', 1, g.op('MULTIPLY', .93, t))))
    return taper.outputs['Curve']


def structure_group():
    definitions = [value for key, value in PARAMETERS.items() if not key.startswith('foliage')]
    g = Graph('Oak_Structure_v' + VERSION, definitions + [('Structure Seed', INT)],
              [('Curves', GEO), ('Tips', GEO), ('Trunk', GEO), ('Primary', GEO), ('Secondary', GEO)])
    i = g.input.outputs
    seed = i['Structure Seed']
    trunk = tapered_curve(g, i['Height'], i['Base Radius'], 0., i['Curvature'], 12)
    roots = g.node('GeometryNodeMeshLine')
    g.set(roots, 'Count', i['Primary Count'])
    index = g.node('GeometryNodeInputIndex').outputs['Index']
    step = g.op('DIVIDE', index, g.op('MAXIMUM', g.op('SUBTRACT', i['Primary Count'], 1), 1))
    factor = g.op('ADD', .33, g.op('MULTIPLY', step, .53))
    sample = g.node('GeometryNodeSampleCurve', mode='FACTOR', data_type='FLOAT')
    g.set(sample, 'Curves', trunk)
    g.set(sample, 'Factor', factor)
    g.set(sample, 'Value', g.node('GeometryNodeInputRadius').outputs['Radius'])
    attach = g.node('GeometryNodeSetPosition')
    g.set(attach, 'Geometry', roots.outputs['Mesh'])
    g.set(attach, 'Position', sample.outputs['Position'])
    # Sectores completos; alternar lados con la altura evita una escalera espiral.
    half = g.op('CEIL', g.op('DIVIDE', i['Primary Count'], 2))
    odd = g.op('MODULO', index, 2)
    sector = g.op('ADD', g.op('FLOOR', g.op('DIVIDE', index, 2)), g.op('MULTIPLY', odd, half))
    width = g.op('DIVIDE', 2*math.pi, i['Primary Count'])
    phase = random(g, seed, -math.pi, math.pi, 11, constant=True)
    jitter = g.op('MULTIPLY', i['Asymmetry'], random(g, seed, -.16, .16, 12))
    azimuth = g.op('ADD', phase, g.op('MULTIPLY', width, g.op('ADD', sector, jitter)))
    variation = g.op('ADD', 1, g.op('MULTIPLY', i['Asymmetry'], random(g, seed, -.18, .12, 13)))
    length = g.op('MULTIPLY', g.op('MULTIPLY', i['Height'], i['Branch Ratio']),
                  g.op('MULTIPLY', g.op('SUBTRACT', .95, g.op('MULTIPLY', .38, step)), variation))
    angle = clamp(g, g.op('ADD', g.op('SUBTRACT', g.op('SUBTRACT', i['Inclination'], 6), g.op('MULTIPLY', 32, step)),
                    random(g, seed, -6., 6., 14)), 12, 76)
    radius = g.op('MULTIPLY', sample.outputs['Value'], random(g, seed, .58, .70, 15))
    bend = random(g, seed, .12, .25, 16)
    primary = branch_curves(g, attach.outputs['Geometry'], 'q1p_', length, radius, azimuth, angle, bend, 9)
    # Dos secundarias por primaria; conservar el número y los nacimientos de la base.
    # El radio y la longitud proceden ahora del padre, la orientación se abre a ambos lados.
    parent_radius = store(g, primary, 'q1_parent_radius', g.node('GeometryNodeInputRadius').outputs['Radius'])
    trim = g.node('GeometryNodeTrimCurve')
    g.set(trim, 'Curve', parent_radius)
    g.set(trim, 'Start', .48)
    g.set(trim, 'End', .78)
    points = g.node('GeometryNodeCurveToPoints', mode='COUNT')
    g.set(points, 'Curve', trim.outputs['Curve'])
    g.set(points, 'Count', 2)
    tangent = g.node('ShaderNodeSeparateXYZ')
    g.set(tangent, 'Vector', points.outputs['Tangent'])
    side = g.op('SUBTRACT', g.op('MULTIPLY', g.op('MODULO', index, 2), 2), 1)
    parent_yaw = g.op('ARCTAN2', tangent.outputs['Y'], tangent.outputs['X'])
    secondary_yaw = g.op('ADD', parent_yaw, g.op('MULTIPLY', side, random(g, seed, .65, .95, 21)))
    parent_tilt = g.op('MULTIPLY', g.op('ARCCOSINE', clamp(g, tangent.outputs['Z'], -1, 1)), 180/math.pi)
    secondary_tilt = clamp(g, g.op('SUBTRACT', parent_tilt, random(g, seed, 6., 20., 22)), 15, 68)
    secondary_length = g.op('MULTIPLY', attribute(g, 'q1p_length'),
                            g.op('SUBTRACT', .38, g.op('MULTIPLY', .12, g.op('MODULO', index, 2))))
    secondary_radius = g.op('MULTIPLY', attribute(g, 'q1_parent_radius'), random(g, seed, .50, .60, 23))
    secondary = branch_curves(g, points.outputs['Points'], 'q1s_', secondary_length, secondary_radius,
                             secondary_yaw, secondary_tilt, random(g, seed, .10, .20, 24), 7)
    switch = g.node('GeometryNodeSwitch', input_type='GEOMETRY')
    g.set(switch, 'Switch', g.op('GREATER_THAN', i['Depth'], 1))
    g.set(switch, 'True', secondary)
    all_curves = g.join(trunk, primary, switch.outputs['Output'])
    g.set(g.output, 'Curves', all_curves)
    g.set(g.output, 'Tips', tips(g, all_curves))
    for name, curves in [('Trunk', trunk), ('Primary', primary), ('Secondary', switch.outputs['Output'])]:
        g.set(g.output, name, curves)
    return g


def build_generator(bark, leaves):
    structure, volume, foliage = structure_group(), volume_group(), foliage_group()
    g = Graph('Oak_Generator_v' + VERSION,
              list(PARAMETERS.values()) + [('Structure Seed', INT), ('Foliage Seed', INT), ('Profile Resolution', INT)],
              [('Geometry', GEO)])
    s = g.group(structure.tree)
    for name in structure.sockets:
        g.set(s, name, g.input.outputs[name])
    v = g.group(volume.tree, Curves=s.outputs['Curves'], Bark=bark)
    g.set(v, 'Profile Resolution', g.input.outputs['Profile Resolution'])
    f = g.group(foliage.tree, Tips=s.outputs['Tips'], Leaves=leaves)
    g.set(f, 'Scale', g.input.outputs['Foliage Scale'])
    g.set(f, 'Foliage Seed', g.input.outputs['Foliage Seed'])
    count = g.op('FLOOR', g.op('ADD', g.op('MULTIPLY', g.input.outputs['Density'], 4), .5))
    g.set(f, 'Mass Count', count)
    joined = g.join(v.outputs['Mesh'], f.outputs['Mesh'])
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
