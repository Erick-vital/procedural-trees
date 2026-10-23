"""Q2: estructura Q1b; altura de madera independiente de la copa, X/Y intactos."""
from oak_nodes import Graph, GEO, FLOAT, INT, PARAMETERS, volume_group
from oak_nodes_v21 import structure_group

VERSION = '0.3.0'


def random(g, seed, low, high, stream=0, vector=False):
    value = g.random(seed, low, high, stream=stream, vector=vector)
    g.set(value.node, 'ID', g.node('GeometryNodeInputIndex').outputs['Index'])
    return value


def transform(g, geometry, scale_z, translate_z):
    node = g.node('GeometryNodeTransform')
    g.set(node, 'Geometry', geometry)
    g.set(node, 'Scale', g.vector(1., 1., scale_z))
    g.set(node, 'Translation', g.vector(z=translate_z))
    return node.outputs['Geometry']


def foliage_group():
    g = Graph('Oak_Foliage_v' + VERSION,
              [('Curves', GEO), ('Height', FLOAT), ('Mass Count', INT), ('Scale', FLOAT),
               ('Foliage Seed', INT), ('Leaves', 'NodeSocketMaterial')],
              [('Mesh', GEO), ('Anchors', GEO), ('Centers', GEO)])
    i = g.input.outputs
    trim = g.node('GeometryNodeTrimCurve')
    g.set(trim, 'Curve', i['Curves'])
    start = g.node('GeometryNodeSwitch', input_type='FLOAT')
    g.set(start, 'Switch', g.op('GREATER_THAN', i['Mass Count'], 1))
    g.set(start, 'False', .999)
    g.set(start, 'True', random(g, i['Foliage Seed'], .42, .58, stream=5))
    g.set(trim, 'Start', start.outputs['Output'])
    end = g.node('GeometryNodeSwitch', input_type='FLOAT')
    g.set(end, 'Switch', g.op('GREATER_THAN', i['Mass Count'], 1))
    g.set(end, 'False', 1.)
    g.set(end, 'True', random(g, i['Foliage Seed'], .90, .99, stream=6))
    g.set(trim, 'End', end.outputs['Output'])
    points = g.node('GeometryNodeCurveToPoints', mode='COUNT')
    g.set(points, 'Curve', trim.outputs['Curve'])
    g.set(points, 'Count', g.op('MAXIMUM', i['Mass Count'], 1))
    # Acotar masas en combinaciones extremas de altura pequeña/escala grande.
    scale = g.op('MINIMUM', i['Scale'], g.op('MULTIPLY', .24, i['Height']))
    ico = g.node('GeometryNodeMeshIcoSphere')
    g.set(ico, 'Radius', scale)
    g.set(ico, 'Subdivisions', 1)
    mat = g.node('GeometryNodeSetMaterial')
    g.set(mat, 'Geometry', ico.outputs['Mesh'])
    g.set(mat, 'Material', i['Leaves'])
    sizes = random(g, i['Foliage Seed'], (.85, .75, .58), (1.20, 1.08, .85), stream=1, vector=True)
    axes = g.node('ShaderNodeSeparateXYZ')
    g.set(axes, 'Vector', sizes)
    bounds = g.node('GeometryNodeBoundBox')
    g.set(bounds, 'Geometry', ico.outputs['Mesh'])
    high = g.node('ShaderNodeSeparateXYZ')
    g.set(high, 'Vector', bounds.outputs['Max'])
    radius_z = g.op('MULTIPLY', high.outputs['Z'], axes.outputs['Z'])
    # Rotar solo en Z permite conocer exactamente el alcance vertical de cada masa.
    offset = g.node('ShaderNodeVectorMath', operation='SCALE')
    g.set(offset, 0, random(g, i['Foliage Seed'], (-.10, -.10, 0.), (.10, .10, 0.), vector=True))
    g.set(offset, 'Scale', scale)
    add = g.node('ShaderNodeVectorMath', operation='ADD')
    g.set(add, 0, g.node('GeometryNodeInputPosition').outputs['Position'])
    g.set(add, 1, offset.outputs['Vector'])
    xyz = g.node('ShaderNodeSeparateXYZ')
    g.set(xyz, 'Vector', add.outputs['Vector'])
    z = g.op('MINIMUM', g.op('MAXIMUM', xyz.outputs['Z'], radius_z), g.op('SUBTRACT', i['Height'], radius_z))
    move = g.node('GeometryNodeSetPosition')
    g.set(move, 'Geometry', points.outputs['Points'])
    g.set(move, 'Position', g.vector(xyz.outputs['X'], xyz.outputs['Y'], z))
    instances = g.node('GeometryNodeInstanceOnPoints')
    g.set(instances, 'Points', move.outputs['Geometry'])
    g.set(instances, 'Instance', mat.outputs['Geometry'])
    g.set(instances, 'Scale', sizes)
    g.set(instances, 'Rotation', g.vector(z=random(g, i['Foliage Seed'], 0., 6.283185, stream=2)))
    realized = g.node('GeometryNodeRealizeInstances')
    g.set(realized, 'Geometry', instances.outputs['Instances'])
    for name, geometry in [('Mesh', realized.outputs['Geometry']),
                           ('Anchors', points.outputs['Points']), ('Centers', move.outputs['Geometry'])]:
        switch = g.node('GeometryNodeSwitch', input_type='GEOMETRY')
        g.set(switch, 'Switch', g.op('GREATER_THAN', i['Mass Count'], 0))
        g.set(switch, 'True', geometry)
        g.set(g.output, name, switch.outputs['Output'])
    return g


def build_generator(bark, leaves):
    structure, volume, foliage = structure_group(), volume_group(), foliage_group()
    g = Graph('Oak_Generator_v' + VERSION,
              list(PARAMETERS.values()) + [('Structure Seed', INT), ('Foliage Seed', INT), ('Profile Resolution', INT)],
              [('Geometry', GEO), ('Raw Wood', GEO), ('Wood', GEO), ('Anchors', GEO), ('Centers', GEO)])
    s = g.group(structure.tree)
    for name in structure.sockets:
        g.set(s, name, g.input.outputs[name])
    v = g.group(volume.tree, Curves=s.outputs['Curves'], Bark=bark)
    g.set(v, 'Profile Resolution', g.input.outputs['Profile Resolution'])
    box = g.node('GeometryNodeBoundBox')
    g.set(box, 'Geometry', v.outputs['Mesh'])
    low, high = g.node('ShaderNodeSeparateXYZ'), g.node('ShaderNodeSeparateXYZ')
    g.set(low, 'Vector', box.outputs['Min'])
    g.set(high, 'Vector', box.outputs['Max'])
    scale_z = g.op('DIVIDE', g.input.outputs['Height'], g.op('SUBTRACT', high.outputs['Z'], low.outputs['Z']))
    translate_z = g.op('MULTIPLY', g.op('MULTIPLY', low.outputs['Z'], -1), scale_z)
    wood = transform(g, v.outputs['Mesh'], scale_z, translate_z)
    # Las posiciones de apoyo usan exactamente la misma transformación que la madera.
    curves = transform(g, s.outputs['Curves'], scale_z, translate_z)
    f = g.group(foliage.tree, Curves=curves, Leaves=leaves)
    for name, parent in [('Scale', 'Foliage Scale'), ('Foliage Seed', 'Foliage Seed'), ('Height', 'Height')]:
        g.set(f, name, g.input.outputs[parent])
    g.set(f, 'Mass Count', g.op('FLOOR', g.op('ADD', g.op('MULTIPLY', g.input.outputs['Density'], 4), .5)))
    g.set(g.output, 'Geometry', g.join(wood, f.outputs['Mesh']))
    for name, geo in [('Raw Wood', v.outputs['Mesh']), ('Wood', wood), ('Anchors', f.outputs['Anchors']), ('Centers', f.outputs['Centers'])]:
        g.set(g.output, name, geo)
    return g, structure
