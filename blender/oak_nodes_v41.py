"""Q3b: copa abierta y grupos ligados al radio real, conservando la madera Q2."""
import math
from oak_nodes import Graph, GEO, FLOAT, INT
from oak_nodes_v3 import build_generator as build_q2
from oak_nodes_v4 import integer, random, named, store, select, vector_math, prototype

VERSION = '0.4.1'


def clamp(g, value, low, high):
    return g.op('MINIMUM',high,g.op('MAXIMUM',low,value))


def foliage_group():
    shapes = [prototype(k) for k in range(6)]
    g = Graph('Oak_Foliage_v'+VERSION,
              [('Curves', GEO), ('Height', FLOAT), ('Mass Count', INT), ('Scale', FLOAT),
               ('Foliage Seed', INT), ('Level', INT), ('Base Radius', FLOAT), ('Leaves', 'NodeSocketMaterial')],
              [('Mesh', GEO), ('Anchors', GEO), ('Centers', GEO)])
    i = g.input.outputs
    seed = integer(g,'ADD',integer(g,'FLOORED_MODULO',i['Foliage Seed'],2147480000),integer(g,'MULTIPLY',i['Level'],409))
    length = g.node('GeometryNodeSplineLength').outputs['Length']
    index = g.node('GeometryNodeInputIndex').outputs['Index']
    density = i['Mass Count']
    # q1p_radius se hereda también en secundarias; q1s_radius es su radio propio.
    parent_radius = select(g,i['Level'],[i['Base Radius'],named(g,'q1p_radius'),named(g,'q1p_radius')])
    radius = select(g,i['Level'],[i['Base Radius'],named(g,'q1p_radius'),named(g,'q1s_radius')])
    support = clamp(g,g.op('DIVIDE',g.op('SUBTRACT',g.op('DIVIDE',parent_radius,i['Base Radius']),.12),.46),0.,1.)
    local_support = clamp(g,g.op('DIVIDE',radius,g.op('MAXIMUM',parent_radius,.001)),.08,1.)
    weight = g.op('MULTIPLY',g.op('ADD',.65,g.op('MULTIPLY',.50,support)),
                  select(g,i['Level'],[.62,1.,g.op('ADD',.68,g.op('MULTIPLY',.32,local_support))]))
    length_weight = clamp(g,g.op('DIVIDE',length,g.op('MULTIPLY',i['Height'],select(g,i['Level'],[1.,.65,.42]))),.75,1.15)
    amount = g.op('FLOOR',g.op('ADD',1.15,g.op('MULTIPLY',g.op('SUBTRACT',density,1),
        g.op('MULTIPLY',support,g.op('MULTIPLY',length_weight,select(g,i['Level'],[0.,1.,.50]))))))
    count = clamp(g,amount,1,g.op('MINIMUM',density,select(g,i['Level'],[1,3,2])))
    # La secundaria intermedia de cada padre queda sin hojas: corredor visible.
    is_middle = g.op('LESS_THAN',g.op('ABSOLUTE',g.op('SUBTRACT',g.op('MODULO',index,3),1)),.1)
    bare = g.op('MULTIPLY',g.op('GREATER_THAN',i['Level'],1.5),is_middle)
    count = g.op('MULTIPLY',count,g.op('SUBTRACT',1,bare))
    curves = i['Curves']
    cluster_u = clamp(g,g.op('ADD',g.op('ADD',.52,g.op('MULTIPLY',.37,g.op('SUBTRACT',1,support))),
        random(g,seed,-.055,.055,stream=23)),.48,.95)
    sparse_cluster = g.node('GeometryNodeSwitch',input_type='FLOAT')
    g.set(sparse_cluster,'Switch',g.op('GREATER_THAN',density,2))
    g.set(sparse_cluster,'True',cluster_u)
    g.set(sparse_cluster,'False',random(g,seed,.88,.97,stream=27))
    cluster_u = select(g,i['Level'],[.86,sparse_cluster.outputs['Output'],sparse_cluster.outputs['Output']])
    width = random(g,seed,.12,.22,stream=24)
    start = select(g,i['Level'],[.84,g.op('SUBTRACT',cluster_u,width),g.op('SUBTRACT',cluster_u,width)])
    end = select(g,i['Level'],[.88,g.op('MINIMUM',.985,g.op('ADD',cluster_u,width)),g.op('MINIMUM',.985,g.op('ADD',cluster_u,width))])
    for name,value,kind in [('q3_count',count,'INT'),('q3_branch',g.op('ADD',index,g.op('MULTIPLY',i['Level'],100)),'INT'),
        ('q3_level',i['Level'],'INT'),('q3_length',length,'FLOAT'),('q3_radius',radius,'FLOAT'),
        ('q3_parent_radius',parent_radius,'FLOAT'),('q3_support',support,'FLOAT'),('q3_weight',weight,'FLOAT'),
        ('q3_ceiling_margin',random(g,seed,.06,.42,stream=26),'FLOAT'),('q3_cluster_u',cluster_u,'FLOAT'),
        ('q3_flatness',g.op('MULTIPLY',random(g,seed,.75,1.2,stream=25),
            g.op('SUBTRACT',1.30,g.op('MULTIPLY',.60,support))),'FLOAT'),('q3_start',start,'FLOAT'),('q3_end',end,'FLOAT')]:
        curves = store(g,curves,name,value,kind,domain='CURVE')
    count = named(g,'q3_count','INT')
    switch = g.node('GeometryNodeSwitch',input_type='FLOAT')
    g.set(switch,'Switch',g.op('GREATER_THAN',count,1))
    g.set(switch,'True',named(g,'q3_start'))
    g.set(switch,'False',named(g,'q3_cluster_u'))
    trim = g.node('GeometryNodeTrimCurve')
    g.set(trim,'Curve',curves)
    g.set(trim,'Start',switch.outputs['Output'])
    g.set(trim,'End',named(g,'q3_end'))
    curves = store(g,trim.outputs['Curve'],'q3_u',g.node('GeometryNodeSplineParameter').outputs['Factor'])
    sample = g.node('GeometryNodeCurveToPoints',mode='COUNT')
    g.set(sample,'Curve',curves)
    g.set(sample,'Count',g.op('MAXIMUM',1,count))
    rank = g.op('FLOOR',g.op('ADD',g.op('MULTIPLY',g.op('SUBTRACT',count,1),named(g,'q3_u')),.5))
    role = select(g,i['Level'],[1,rank,g.op('ADD',1,rank)])
    high = g.op('MULTIPLY',g.op('LESS_THAN',i['Level'],1.5),g.op('LESS_THAN',rank,1.5))
    family = g.op('FLOOR',random(g,seed,0.,3.999,stream=4))
    kind = g.node('GeometryNodeSwitch',input_type='FLOAT')
    g.set(kind,'Switch',high)
    g.set(kind,'True',family)
    g.set(kind,'False',g.op('ADD',4,g.op('MODULO',family,2)))
    size = g.op('MULTIPLY',g.op('MINIMUM',i['Scale'],g.op('MULTIPLY',.24,i['Height'])),g.op('MULTIPLY',named(g,'q3_weight'),select(g,role,[1.24,.88,.56])))
    size = g.op('MULTIPLY',size,g.op('ADD',.90,g.op('MULTIPLY',.10,g.op('GREATER_THAN',density,2))))
    axes = vector_math(g,'MULTIPLY',random(g,seed,(.90,.80,.72),(1.20,1.12,.98),stream=5,vector=True),
                       g.vector(size,size,g.op('MULTIPLY',size,named(g,'q3_flatness'))))
    delete = g.node('GeometryNodeDeleteGeometry',domain='POINT')
    g.set(delete,'Geometry',sample.outputs['Points'])
    g.set(delete,'Selection',g.op('LESS_THAN',count,.5))
    geo = delete.outputs['Geometry']
    for name,value,kind_type in [('q3_rank',rank,'INT'),('q3_role',role,'INT'),('q3_detail',high,'INT'),
                                ('q3_kind',kind.outputs['Output'],'INT'),('q3_scale',axes,'FLOAT_VECTOR'),
                                ('q3_anchor',g.node('GeometryNodeInputPosition').outputs['Position'],'FLOAT_VECTOR'),
                                ('q3_spin',random(g,seed,0.,2*math.pi,stream=6),'FLOAT'),
                                ('q3_warp',random(g,seed,-1.,1.,stream=7),'FLOAT')]:
        geo = store(g,geo,name,value,kind_type)
    prototypes = [g.group(shape.tree,**{'Foliage Seed':i['Foliage Seed']}) for shape in shapes]
    kind = named(g,'q3_kind','INT')
    anchor = g.node('ShaderNodeSeparateXYZ')
    g.set(anchor,'Vector',named(g,'q3_anchor','FLOAT_VECTOR'))
    scale = g.node('ShaderNodeSeparateXYZ')
    g.set(scale,'Vector',named(g,'q3_scale','FLOAT_VECTOR'))
    low = select(g,kind,[p.outputs['Min Z'] for p in prototypes])
    high = select(g,kind,[p.outputs['Max Z'] for p in prototypes])
    # Mantener espesor cerca del techo: ajustar el centro, con margen distinto
    # por rama. La cota elegida contiene el anclaje y admite toda la altura local.
    extent = g.op('MAXIMUM',g.op('MULTIPLY',low,-1),high)
    z_scale = g.op('MINIMUM',scale.outputs['Z'],g.op('DIVIDE',g.op('MULTIPLY',.46,i['Height']),extent))
    geo = store(g,geo,'q3_scale',g.vector(scale.outputs['X'],scale.outputs['Y'],z_scale),'FLOAT_VECTOR')
    low_z,high_z = g.op('MULTIPLY',low,z_scale),g.op('MULTIPLY',high,z_scale)
    ceiling = g.op('MAXIMUM',anchor.outputs['Z'],g.op('MAXIMUM',g.op('SUBTRACT',high_z,low_z),
        g.op('SUBTRACT',i['Height'],g.op('MULTIPLY',named(g,'q3_ceiling_margin'),g.op('MINIMUM',i['Scale'],g.op('MULTIPLY',.24,i['Height']))))))
    center = g.vector(anchor.outputs['X'],anchor.outputs['Y'],
        g.op('MINIMUM',g.op('MAXIMUM',anchor.outputs['Z'],g.op('MULTIPLY',low_z,-1)),g.op('SUBTRACT',ceiling,high_z)))
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
        for name,parent in [('Height','Height'),('Scale','Foliage Scale'),('Foliage Seed','Foliage Seed'),('Base Radius','Base Radius')]:
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
