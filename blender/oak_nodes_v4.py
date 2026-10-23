"""Q3: formas asimétricas, jerarquía y cantidad por rama; madera Q2 intacta."""
import math
from oak_nodes import Graph, GEO, FLOAT, INT
from oak_nodes_v3 import build_generator as build_q2

VERSION = '0.4.0'


def integer(g, operation, a, b):
    node = g.node('FunctionNodeIntegerMath', operation=operation)
    g.set(node,0,a)
    g.set(node,1,b)
    return node.outputs[0]


def random(g, seed, low, high, stream=0, vector=False, constant=False):
    # Mezclar enteros evita perder streams al sumar números grandes como float32.
    node = g.node('FunctionNodeRandomValue',data_type='FLOAT_VECTOR' if vector else 'FLOAT')
    g.set(node,'Min',low)
    g.set(node,'Max',high)
    reduced = integer(g,'FLOORED_MODULO',seed,2147480000)
    g.set(node,'Seed',integer(g,'ADD',reduced,stream*17))
    g.set(node,'ID',0 if constant else g.node('GeometryNodeInputIndex').outputs['Index'])
    return node.outputs['Value']


def named(g, name, kind='FLOAT'):
    n = g.node('GeometryNodeInputNamedAttribute', data_type=kind)
    g.set(n, 'Name', name)
    return n.outputs['Attribute']


def store(g, geometry, name, value, kind='FLOAT', domain='POINT'):
    n = g.node('GeometryNodeStoreNamedAttribute', data_type=kind, domain=domain)
    g.set(n, 'Geometry', geometry)
    g.set(n, 'Name', name)
    g.set(n, 'Value', value)
    return n.outputs['Geometry']


def select(g, index, values):
    n = g.node('GeometryNodeIndexSwitch', data_type='FLOAT')
    n.index_switch_items.clear()
    for _ in values:
        n.index_switch_items.new()
    g.set(n, 'Index', index)
    for k,value in enumerate(values):
        g.set(n, k+1, value)
    return n.outputs['Output']


def vector_math(g, operation, a, b):
    n = g.node('ShaderNodeVectorMath', operation=operation)
    g.set(n, 0, a)
    g.set(n, 1, b)
    return n.outputs['Vector']


def prototype(family):
    """Seis familias generativas; ruido espacial suave, semilla por árbol."""
    g = Graph(f'Oak_FoliageShape_{family}_v{VERSION}', [('Foliage Seed', INT)],
              [('Geometry', GEO), ('Raw Geometry', GEO), ('Min Z', FLOAT), ('Max Z', FLOAT)])
    ico = g.node('GeometryNodeMeshIcoSphere')
    g.set(ico, 'Radius', 1.)
    g.set(ico, 'Subdivisions', 2 if family < 4 else 1)
    p = g.node('GeometryNodeInputPosition').outputs['Position']
    xyz = g.node('ShaderNodeSeparateXYZ')
    g.set(xyz, 'Vector', p)
    x,y,z = (xyz.outputs[k] for k in ('X','Y','Z'))
    phase = random(g,g.input.outputs['Foliage Seed'], (-15.,-15.,-15.), (15.,15.,15.), vector=True, stream=100+family,constant=True)
    noise = g.node('ShaderNodeTexNoise', noise_dimensions='3D')
    g.set(noise, 'Vector', vector_math(g, 'ADD', p, phase))
    g.set(noise, 'Scale', 1.25)
    g.set(noise, 'Detail', 0.)
    theta = g.op('ARCTAN2', y, x)
    wave = g.op('SINE', g.op('ADD', g.op('MULTIPLY', 3 if family == 2 else 2, theta), family*.93))
    lobe = g.op('MULTIPLY', .19 if family == 2 else .08, g.op('MULTIPLY', wave, g.op('SUBTRACT', 1, g.op('MULTIPLY', z,z))))
    radial = g.op('ADD', g.op('ADD', 1, lobe), g.op('MULTIPLY', .28, g.op('SUBTRACT', noise.outputs['Factor'], .5)))
    radial = g.op('ADD', radial, g.op('MULTIPLY', .10, x))
    radial = g.op('MINIMUM', 1.28, g.op('MAXIMUM', .74, radial))
    stretch = [(1.,1.,1.), (1.28,.77,.93), (1.06,1.02,.90), (.91,1.16,.97), (1.,.92,1.), (1.18,.85,.95)][family]
    # Curvatura de contorno a gran escala, sin ruido independiente por vértice.
    coords = [g.op('ADD', g.op('MULTIPLY', x,radial), g.op('MULTIPLY', .12, g.op('MULTIPLY', z,z))),
              g.op('ADD', g.op('MULTIPLY', y,radial), g.op('MULTIPLY', .08, g.op('MULTIPLY', x,z))),
              g.op('ADD', g.op('MULTIPLY', z,radial), g.op('MULTIPLY', .16 if family == 3 else .07, x))]
    move = g.node('GeometryNodeSetPosition')
    g.set(move, 'Geometry', ico.outputs['Mesh'])
    g.set(move, 'Position', g.vector(*(g.op('MULTIPLY', v,k) for v,k in zip(coords,stretch))))
    box = g.node('GeometryNodeBoundBox')
    g.set(box, 'Geometry', move.outputs['Geometry'])
    g.set(g.output, 'Geometry', move.outputs['Geometry'])
    g.set(g.output, 'Raw Geometry', ico.outputs['Mesh'])
    for output,socket in [('Min Z','Min'),('Max Z','Max')]:
        separate = g.node('ShaderNodeSeparateXYZ')
        g.set(separate, 'Vector', box.outputs[socket])
        g.set(g.output, output, separate.outputs['Z'])
    return g


def foliage_group():
    shapes = [prototype(k) for k in range(6)]
    g = Graph('Oak_Foliage_v'+VERSION,
              [('Curves', GEO), ('Height', FLOAT), ('Mass Count', INT), ('Scale', FLOAT),
               ('Foliage Seed', INT), ('Level', INT), ('Leaves', 'NodeSocketMaterial')],
              [('Mesh', GEO), ('Anchors', GEO), ('Centers', GEO)])
    i = g.input.outputs
    seed = integer(g,'ADD',integer(g,'FLOORED_MODULO',i['Foliage Seed'],2147480000),integer(g,'MULTIPLY',i['Level'],409))
    length = g.node('GeometryNodeSplineLength').outputs['Length']
    index = g.node('GeometryNodeInputIndex').outputs['Index']
    density = i['Mass Count']
    by_length = g.op('FLOOR', g.op('ADD', g.op('ADD', g.op('MULTIPLY', density,
        g.op('DIVIDE', length, g.op('MULTIPLY', i['Height'], select(g,i['Level'],[1.,.65,.42])))), .5), random(g,seed,-.18,.18,stream=1)))
    count = select(g, i['Level'], [g.op('CEIL',g.op('DIVIDE',density,2)), by_length, by_length])
    count = g.op('MAXIMUM',1,g.op('MINIMUM',count,g.op('MINIMUM',density,select(g,i['Level'],[2,3,2]))))
    curves = i['Curves']
    for name,value,kind in [('q3_count',count,'INT'),('q3_branch',g.op('ADD',index,g.op('MULTIPLY',i['Level'],100)),'INT'),
                             ('q3_level',i['Level'],'INT'),('q3_length',length,'FLOAT')]:
        curves = store(g,curves,name,value,kind,domain='CURVE')
    count = named(g,'q3_count','INT')
    end = random(g,seed,.91,.99,stream=2)
    start = select(g,i['Level'],[random(g,seed,.66,.75,stream=3),random(g,seed,.40,.55,stream=3),random(g,seed,.43,.62,stream=3)])
    switch = g.node('GeometryNodeSwitch',input_type='FLOAT')
    g.set(switch,'Switch',g.op('GREATER_THAN',count,1))
    g.set(switch,'True',start)
    g.set(switch,'False',g.op('SUBTRACT',end,.001))
    trim = g.node('GeometryNodeTrimCurve')
    g.set(trim,'Curve',curves)
    g.set(trim,'Start',switch.outputs['Output'])
    g.set(trim,'End',end)
    curves = store(g,trim.outputs['Curve'],'q3_u',g.node('GeometryNodeSplineParameter').outputs['Factor'])
    sample = g.node('GeometryNodeCurveToPoints',mode='COUNT')
    g.set(sample,'Curve',curves)
    g.set(sample,'Count',count)
    rank = g.op('FLOOR',g.op('ADD',g.op('MULTIPLY',g.op('SUBTRACT',count,1),named(g,'q3_u')),.5))
    role = select(g,i['Level'],[1,rank,g.op('ADD',1,rank)])
    high = g.op('MULTIPLY',g.op('LESS_THAN',i['Level'],1.5),g.op('LESS_THAN',rank,1.5))
    family = g.op('FLOOR',random(g,seed,0.,3.999,stream=4))
    kind = g.node('GeometryNodeSwitch',input_type='FLOAT')
    g.set(kind,'Switch',high)
    g.set(kind,'True',family)
    g.set(kind,'False',g.op('ADD',4,g.op('MODULO',family,2)))
    size = g.op('MULTIPLY',g.op('MINIMUM',i['Scale'],g.op('MULTIPLY',.24,i['Height'])),select(g,role,[1.50,1.03,.62]))
    axes = vector_math(g,'MULTIPLY',random(g,seed,(.90,.80,.65),(1.20,1.12,.95),stream=5,vector=True),g.vector(size,size,size))
    geo = sample.outputs['Points']
    for name,value,kind_type in [('q3_rank',rank,'INT'),('q3_role',role,'INT'),('q3_detail',high,'INT'),
                                ('q3_kind',kind.outputs['Output'],'INT'),('q3_scale',axes,'FLOAT_VECTOR'),
                                ('q3_anchor',g.node('GeometryNodeInputPosition').outputs['Position'],'FLOAT_VECTOR'),
                                ('q3_spin',random(g,seed,0.,2*math.pi,stream=6),'FLOAT'),
                                ('q3_warp',random(g,seed,-1.,1.,stream=7),'FLOAT')]:
        geo = store(g,geo,name,value,kind_type)
    prototypes = [g.group(shape.tree,**{'Foliage Seed':i['Foliage Seed']}) for shape in shapes]
    kind = named(g,'q3_kind','INT')
    scale_z = g.node('ShaderNodeSeparateXYZ')
    g.set(scale_z,'Vector',named(g,'q3_scale','FLOAT_VECTOR'))
    low = g.op('MULTIPLY',select(g,kind,[p.outputs['Min Z'] for p in prototypes]),scale_z.outputs['Z'])
    high = g.op('MULTIPLY',select(g,kind,[p.outputs['Max Z'] for p in prototypes]),scale_z.outputs['Z'])
    anchor = g.node('ShaderNodeSeparateXYZ')
    g.set(anchor,'Vector',named(g,'q3_anchor','FLOAT_VECTOR'))
    offset = random(g,seed,(-.10,-.10,0.),(.10,.10,0.),stream=8,vector=True)
    offset = vector_math(g,'MULTIPLY',offset,g.vector(size,size,size))
    xy = g.node('ShaderNodeSeparateXYZ')
    g.set(xy,'Vector',offset)
    center = g.vector(g.op('ADD',anchor.outputs['X'],xy.outputs['X']),g.op('ADD',anchor.outputs['Y'],xy.outputs['Y']),
        g.op('MINIMUM',g.op('MAXIMUM',anchor.outputs['Z'],g.op('MULTIPLY',low,-1)),g.op('SUBTRACT',i['Height'],high)))
    geo = store(g,geo,'q3_center',center,'FLOAT_VECTOR')
    move = g.node('GeometryNodeSetPosition')
    g.set(move,'Geometry',geo)
    g.set(move,'Position',named(g,'q3_center','FLOAT_VECTOR'))
    realized=[]
    for k,p in enumerate(prototypes):
        instance=g.node('GeometryNodeInstanceOnPoints')
        g.set(instance,'Points',move.outputs['Geometry'])
        g.set(instance,'Selection',g.op('LESS_THAN',g.op('ABSOLUTE',g.op('SUBTRACT',kind,k)),.1))
        g.set(instance,'Instance',p.outputs['Geometry'])
        r=g.node('GeometryNodeRealizeInstances')
        g.set(r,'Geometry',instance.outputs['Instances'])
        realized.append(r.outputs['Geometry'])
    mesh=g.join(*realized)
    local=vector_math(g,'SUBTRACT',g.node('GeometryNodeInputPosition').outputs['Position'],named(g,'q3_center','FLOAT_VECTOR'))
    xyz=g.node('ShaderNodeSeparateXYZ')
    g.set(xyz,'Vector',local)
    x,y,z=(xyz.outputs[k] for k in ('X','Y','Z'))
    warp=named(g,'q3_warp')
    # Deformación continua por masa, adicional a la familia. Z no cambia: límites exactos.
    x=g.op('ADD',g.op('MULTIPLY',x,g.op('ADD',1,g.op('MULTIPLY',.12,g.op('MULTIPLY',warp,z)))),
             g.op('MULTIPLY',.10,g.op('MULTIPLY',warp,g.op('MULTIPLY',y,y))))
    y=g.op('SUBTRACT',y,g.op('MULTIPLY',.08,g.op('MULTIPLY',warp,g.op('MULTIPLY',xyz.outputs['X'],z))))
    scaled=vector_math(g,'MULTIPLY',g.vector(x,y,z),named(g,'q3_scale','FLOAT_VECTOR'))
    rotate=g.node('ShaderNodeVectorRotate',rotation_type='AXIS_ANGLE')
    g.set(rotate,'Vector',scaled)
    g.set(rotate,'Axis',(0.,0.,1.))
    g.set(rotate,'Angle',named(g,'q3_spin'))
    shape=g.node('GeometryNodeSetPosition')
    g.set(shape,'Geometry',mesh)
    g.set(shape,'Position',vector_math(g,'ADD',rotate.outputs['Vector'],named(g,'q3_center','FLOAT_VECTOR')))
    mat=g.node('GeometryNodeSetMaterial')
    g.set(mat,'Geometry',shape.outputs['Geometry'])
    g.set(mat,'Material',i['Leaves'])
    anchor_points=g.node('GeometryNodeSetPosition')
    g.set(anchor_points,'Geometry',geo)
    g.set(anchor_points,'Position',named(g,'q3_anchor','FLOAT_VECTOR'))
    for name,geometry in [('Mesh',mat.outputs['Geometry']),('Anchors',anchor_points.outputs['Geometry']),('Centers',move.outputs['Geometry'])]:
        switch=g.node('GeometryNodeSwitch',input_type='GEOMETRY')
        g.set(switch,'Switch',g.op('GREATER_THAN',density,0))
        g.set(switch,'True',geometry)
        g.set(g.output,name,switch.outputs['Output'])
    return g


def build_generator(bark, leaves):
    # Reutilizar el ensamblado Q2 asegura la misma malla de madera y transformación.
    g,structure=build_q2(bark,leaves)
    g.tree.name='Oak_Generator_v'+VERSION
    original=next(n for n in g.tree.nodes if n.bl_idname=='GeometryNodeGroup' and n.node_tree.name.startswith('Oak_Foliage_v'))
    old_tree=original.node_tree
    wood=g.output.inputs['Wood'].links[0].from_socket
    wood_transform=wood.node
    source=next(n for n in g.tree.nodes if n.bl_idname=='GeometryNodeGroup' and n.node_tree.name.startswith('Oak_Structure_v'))
    foliage=foliage_group()
    nodes=[]
    for level,channel in enumerate(('Trunk','Primary','Secondary')):
        transform=g.node('GeometryNodeTransform')
        g.set(transform,'Geometry',source.outputs[channel])
        for name in ('Scale','Translation'):
            g.set(transform,name,wood_transform.inputs[name].links[0].from_socket)
        f=g.group(foliage.tree,Curves=transform.outputs['Geometry'],Leaves=leaves,Level=level)
        for name,parent in [('Height','Height'),('Scale','Foliage Scale'),('Foliage Seed','Foliage Seed')]:
            g.set(f,name,g.input.outputs[parent])
        g.set(f,'Mass Count',g.op('FLOOR',g.op('ADD',g.op('MULTIPLY',g.input.outputs['Density'],4),.5)))
        nodes.append(f)
    g.set(g.output,'Geometry',g.join(wood,*(n.outputs['Mesh'] for n in nodes)))
    for name in ('Anchors','Centers'):
        g.set(g.output,name,g.join(*(n.outputs[name] for n in nodes)))
    g.tree.nodes.remove(original)
    if old_tree.users==0:
        import bpy
        bpy.data.node_groups.remove(old_tree)
    return g,structure
