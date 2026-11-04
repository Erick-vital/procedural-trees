"""R2: retener ramas visibles y sus ancestros; sin dependencias de Blender."""
import copy
import math

VERSION='branch-visibility-prune-0.1.0'


def directions(offset_deg=0.):
    if type(offset_deg) not in (int,float) or not math.isfinite(offset_deg):
        raise ValueError('Ángulo inválido')
    result=[]
    for elevation in (-.65,.1,.65):
        for i in range(12):
            angle=math.radians(offset_deg+30*i);v=(math.cos(angle),math.sin(angle),elevation)
            size=math.sqrt(sum(x*x for x in v));result.append(tuple(x/size for x in v))
    if offset_deg==0:result += [(0.,0.,1.),(0.,0.,-1.)]
    return result


def surface_samples(mesh):
    vertices=mesh['vertices']
    points=[tuple(p) for p in vertices]
    for face in mesh['polygons']:
        points.append(tuple(sum(vertices[i][k] for i in face)/len(face) for k in range(3)))
        for i,j in zip(face,face[1:]+face[:1]):
            # Fracciones próximas al borde conservan ramas que asoman por huecos.
            for t in (.25,.5,.75):
                points.append(tuple(vertices[i][k]*(1-t)+vertices[j][k]*t for k in range(3)))
    return sorted(set(points))


def prune_network(network,exposed_ids):
    edges=network['edges']
    if not 1<=len(edges)<=720 or len({e['id'] for e in edges})!=len(edges):
        raise ValueError('Red inválida')
    index={e['id']:e for e in edges}
    exposed=set(exposed_ids)
    if exposed-set(index):raise ValueError('Tramo desconocido')
    for edge in edges:
        seen=set();current=edge['id']
        while current is not None:
            if current not in index or current in seen:raise ValueError('Jerarquía incompleta o cíclica')
            seen.add(current);current=index[current]['parent']
    protected=exposed | {e['id'] for e in edges if e['parent'] is None}
    for identifier in list(protected):
        current=index[identifier]['parent']
        while current is not None:
            protected.add(current);current=index[current]['parent']
    kept=[copy.deepcopy(e) for e in edges if e['id'] in protected]
    removed=[e['id'] for e in edges if e['id'] not in protected]
    result=copy.deepcopy(network);result['edges']=kept
    result['connections']={k:v for k,v in network['connections'].items() if v['edge_id'] in protected}
    result['triangles']=sum(sum(len(f)-2 for f in e['mesh']['polygons']) for e in kept)
    return result,{'version':VERSION,'exposed_ids':sorted(exposed),'kept_ids':[e['id'] for e in kept],
                   'removed_ids':removed,'kept_triangles':result['triangles'],
                   'removed_triangles':network['triangles']-result['triangles'],
                   'connection_targets_retained':len(result['connections']),
                   'leafless_use':False,'invisibility_claim':'only_tested_directions_and_samples'}
