"""R1: red binaria hacia grupos de follaje congelados, independiente de Blender."""
import math
from .seeds import derive_seed
from .branch_structure import add, sub, mul, length

VERSION = 'branch-sample-network-0.1.0'


def average(points):
    return tuple(sum(p[k] for p in points)/len(points) for k in range(3))


def ring_axes(a, b):
    direction = sub(b, a);size = length(direction)
    if size < 1e-6:
        raise ValueError('Tramo demasiado corto')
    t = mul(direction,1/size)
    axis = min(((1,0,0),(0,1,0),(0,0,1)),key=lambda v:abs(sum(x*y for x,y in zip(v,t))))
    def cross(x,y):return (x[1]*y[2]-x[2]*y[1],x[2]*y[0]-x[0]*y[2],x[0]*y[1]-x[1]*y[0])
    u=cross(t,axis);u=mul(u,1/length(u));v=cross(t,u)
    return u,v


def segment_mesh(points,radii,terminal=False):
    """Prismas triangulares; terminal en punta, con cuatro caras válidas."""
    vertices=[];uv=[];faces=[];distance=0.
    for i,p in enumerate(points):
        if i:distance+=length(sub(p,points[i-1]))
        if terminal and i==len(points)-1:
            vertices.append(p);uv.append((.5,distance/1.4));continue
        u,v=ring_axes(points[max(0,i-1)],points[min(len(points)-1,i+1)])
        for k in range(3):
            angle=2*math.pi*k/3
            vertices.append(add(p,mul(add(mul(u,math.cos(angle)),mul(v,math.sin(angle))),radii[i])))
            uv.append((k/3,distance/1.4))
    faces.append([2,1,0])
    for i in range(len(points)-1):
        start=i*3
        for k in range(3):
            if terminal and i==len(points)-2:
                faces.append([start+k,start+(k+1)%3,len(vertices)-1])
            else:faces.append([start+k,start+(k+1)%3,start+3+(k+1)%3,start+3+k])
    if not terminal:faces.append([len(vertices)-3,len(vertices)-2,len(vertices)-1])
    return {'vertices':[list(v) for v in vertices],'polygons':faces,'uv':[list(v) for v in uv]}


def make_network(axis_points,axis_radii,targets,seed):
    if type(seed) is not int or not 0<=seed<=2147483647:
        raise ValueError('Semilla inválida')
    if not 2<=len(axis_points)<=12 or len(axis_points)!=len(axis_radii):
        raise ValueError('Eje inválido')
    if not 1<=len(targets)<=360 or len({t['id'] for t in targets})!=len(targets):
        raise ValueError('Destinos inválidos')
    if any(len(p)!=3 or any(type(x) not in (int,float) or not math.isfinite(x) for x in p) for p in axis_points):
        raise ValueError('Coordenadas inválidas')
    if any(type(r) not in (int,float) or not math.isfinite(r) or not 0<r<=5 for r in axis_radii):
        raise ValueError('Radios inválidos')
    for t in targets:
        if not isinstance(t['id'],str) or len(t['point'])!=3 or any(type(v) not in (int,float) or not math.isfinite(v) for v in t['point']):
            raise ValueError('Destino no finito')
    sizes=[length(sub(b,a)) for a,b in zip(axis_points,axis_points[1:])]
    if min(sizes)<1e-6:raise ValueError('Eje degenerado')
    total=sum(sizes)

    def sample(factor):
        d=total*factor
        for i,size in enumerate(sizes):
            if d<=size or i==len(sizes)-1:
                f=min(1,max(0,d/size))
                return add(axis_points[i],mul(sub(axis_points[i+1],axis_points[i]),f)),axis_radii[i]*(1-f)+axis_radii[i+1]*f
            d-=size

    def projection(point):
        nearest=None;distance=0.
        for i,size in enumerate(sizes):
            v=sub(axis_points[i+1],axis_points[i]);w=sub(point,axis_points[i]);f=max(0,min(1,sum(a*b for a,b in zip(v,w))/(size*size)))
            error=length(sub(point,add(axis_points[i],mul(v,f))))
            candidate=(error,(distance+size*f)/total)
            if nearest is None or candidate<nearest:nearest=candidate
            distance+=size
        return nearest[1]

    buckets=[[] for _ in range(3)]
    anchors=(.32,.56,.79)
    # Cupos por rango longitudinal: impide que destinos más allá de la punta
    # concentren toda la ramificación en un único nacimiento.
    ordered=sorted(targets,key=lambda t:(projection(t['point']),t['point'][0],t['point'][1],t['id']))
    for rank,t in enumerate(ordered):
        buckets[min(2,rank*3//len(ordered))].append(t)
    edges=[];connections={}

    def grow(start,rows,radius,parent,identity,depth,curved=False):
        if depth>18:raise ValueError('Profundidad excesiva')
        center=average([t['point'] for t in rows]);terminal=len(rows)==1
        fraction=1 if terminal else .48+.12*derive_seed(seed,identity)/2147483647
        end=add(start,mul(sub(center,start),fraction))
        if length(sub(end,start))<1e-5:
            # No inventar una colocación alternativa silenciosa.
            raise ValueError('Destinos coincidentes con bifurcación')
        points=[start,end]
        end_radius=0. if terminal else radius*.86
        radii=[radius,end_radius]
        if curved and not terminal:
            middle=add(start,mul(sub(end,start),.5))
            # Arco suave ascendente, acotado al tamaño de la rama.
            middle=add(middle,(0,0,min(.06,total*.018)))
            points=[start,middle,end];radii=[radius,(radius+end_radius)/2,end_radius]
        edges.append({'id':identity,'parent':parent,'points':points,'radii':radii,
                      'terminal':terminal,'target_count':len(rows),'depth':depth,
                      'mesh':segment_mesh(points,radii,terminal)})
        if terminal:
            connections[rows[0]['id']]={'edge_id':identity,'point':list(end)};return
        spans=[max(t['point'][k] for t in rows)-min(t['point'][k] for t in rows) for k in range(3)]
        axis=max(range(3),key=lambda k:spans[k])
        ordered=sorted(rows,key=lambda t:(t['point'][axis],t['id']))
        split=max(1,min(len(rows)-1,round(len(rows)*.6)))
        for k,part in enumerate((ordered[:split],ordered[split:])):
            r=end_radius*math.sqrt(len(part)/len(rows))*.96
            grow(end,part,r,identity,identity+f':{k}',depth+1)

    for i,rows in enumerate(buckets):
        if not rows:continue
        start,radius=sample(anchors[i])
        # La sección hija queda dentro de la madera de origen al nacer.
        grow(start,rows,radius*.60,None,f'bough:{i}',0,True)
    triangles=sum(sum(len(f)-2 for f in e['mesh']['polygons']) for e in edges)
    assert triangles<=12*len(targets)+18
    return {'version':VERSION,'seed':seed,'edges':edges,'connections':connections,
            'triangles':triangles,'targets':len(targets),'max_depth':max(e['depth'] for e in edges),
            'anchors':anchors,'maximum_children':2,'joins':'overlapping_tapered_surfaces_not_welded'}
