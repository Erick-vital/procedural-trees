"""Q1b: recuperar extensión y peso de ramas, con tres secundarias por primaria.

Conserva follaje/normalización de Q1. Helpers y fuentes 0.1.0/0.2.0 congelados.
"""
import math
from oak_nodes import Graph, GEO, INT, PARAMETERS, tapered_curve, tips, volume_group, foliage_group
from oak_nodes_v2 import random, attribute, store, clamp, branch_curves

VERSION = '0.2.1'


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
                  g.op('MULTIPLY', g.op('SUBTRACT', 1.60, g.op('MULTIPLY', .42, step)), variation))
    angle = clamp(g, g.op('ADD', g.op('SUBTRACT', g.op('ADD', i['Inclination'], 8), g.op('MULTIPLY', 12, step)),
                    random(g, seed, -8., 8., 14)), 18, 96)
    radius = g.op('MULTIPLY', sample.outputs['Value'], random(g, seed, .72, .84, 15))
    bend = random(g, seed, -.02, .12, 16)
    primary = branch_curves(g, attach.outputs['Geometry'], 'q1p_', length, radius, azimuth, angle, bend, 9)
    # Tres secundarias escalonadas por primaria, con lado alternado por padre.
    # Se conserva la jerarquía local de radios y los dos niveles del contrato.
    parent_radius = store(g, primary, 'q1_parent_radius', g.node('GeometryNodeInputRadius').outputs['Radius'])
    trim = g.node('GeometryNodeTrimCurve')
    g.set(trim, 'Curve', parent_radius)
    g.set(trim, 'Start', .38)
    g.set(trim, 'End', .84)
    points = g.node('GeometryNodeCurveToPoints', mode='COUNT')
    g.set(points, 'Curve', trim.outputs['Curve'])
    g.set(points, 'Count', 3)
    tangent = g.node('ShaderNodeSeparateXYZ')
    g.set(tangent, 'Vector', points.outputs['Tangent'])
    side = g.op('SUBTRACT', g.op('MULTIPLY', g.op('MODULO', index, 2), 2), 1)
    child_step = g.op('DIVIDE', g.op('MODULO', index, 3), 2)
    parent_yaw = g.op('ARCTAN2', tangent.outputs['Y'], tangent.outputs['X'])
    secondary_yaw = g.op('ADD', parent_yaw, g.op('MULTIPLY', side, random(g, seed, .60, 1.05, 21)))
    parent_tilt = g.op('MULTIPLY', g.op('ARCCOSINE', clamp(g, tangent.outputs['Z'], -1, 1)), 180/math.pi)
    secondary_tilt = clamp(g, g.op('ADD', parent_tilt, random(g, seed, -14., 8., 22)), 20, 92)
    secondary_length = g.op('MULTIPLY', attribute(g, 'q1p_length'),
                            g.op('SUBTRACT', .50, g.op('MULTIPLY', .20, child_step)))
    secondary_radius = g.op('MULTIPLY', attribute(g, 'q1_parent_radius'), random(g, seed, .58, .70, 23))
    secondary = branch_curves(g, points.outputs['Points'], 'q1s_', secondary_length, secondary_radius,
                             secondary_yaw, secondary_tilt, random(g, seed, .04, .16, 24), 7)
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
