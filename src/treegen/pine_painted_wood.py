"""Madera 0.1.0: anillos adaptativos a 5 mm y tapas interiores verificadas."""
import copy
import math
from .pine import point_on,unit,sub
from .pine_painted_sample import canonical_hash

TOLERANCE_M=.005


def ring_error(vertices,sides,a,z):
    error=0.
    for ring in range(a+1,z):
        t=(ring-a)/(z-a)
        for j in range(sides):
            expected=[vertices[a*sides+j][k]*(1-t)+vertices[z*sides+j][k]*t for k in range(3)]
            error=max(error,math.dist(expected,vertices[ring*sides+j]))
    return error


def root_cap_inside(branch,trunk):
    sides=len(branch['mesh']['vertices'])//len(branch['points_m'])
    height=trunk['points_m'][-1][2]
    for vertex in branch['mesh']['vertices'][:sides]:
        t=vertex[2]/height
        if not 0<t<1:return False
        center=point_on(trunk,t)
        radius=trunk['radii_m'][0]*(1-t)+trunk['radii_m'][-1]*t
        # Círculo inscrito y margen de 1 mm; evita depender de una orientación de rayo.
        if math.hypot(vertex[0]-center[0],vertex[1]-center[1])>=radius*math.cos(math.pi/8)-.001:
            return False
    return True


def optimize(branch,trunk):
    b=copy.deepcopy(branch);v=b['mesh']['vertices'];points=b['points_m']
    sides=len(v)//len(points);kept=list(range(len(points)))
    while True:
        candidates=[]
        for pos in range(1,len(kept)-1):
            error=ring_error(v,sides,kept[pos-1],kept[pos+1])
            if error<=TOLERANCE_M:candidates.append((error,pos))
        if not candidates:break
        _,pos=min(candidates);kept.pop(pos)
    faces=[]
    for ring in range(len(kept)-1):
        for j in range(sides):
            a=ring*sides+j;c=ring*sides+(j+1)%sides
            faces.extend([[a,c,c+sides],[a,c+sides,a+sides]])
    removed_cap=branch['parent_id'] is not None and root_cap_inside(branch,trunk)
    for j in range(1,sides-1):
        if not removed_cap:faces.append([0,j+1,j])
        a=(len(kept)-1)*sides;faces.append([a,a+j,a+j+1])
    lengths=[0]
    for a,z in zip(points,points[1:]):lengths.append(lengths[-1]+math.dist(a,z))
    ids=[ring*sides+j for ring in kept for j in range(sides)]
    b['mesh']={'vertices':[v[i] for i in ids],'polygons':faces,'smooth':[False]*len(faces)}
    b['uv']=[[j/sides,lengths[ring]/.8] for ring in kept for j in range(sides)]
    b['wood_optimization']={'version':'pine-wood-rings-0.1.0','tolerance_m':TOLERANCE_M,
        'retained_rings':kept,'original_ring_count':len(points),'sides_unchanged':sides,
        'root_cap_removed':removed_cap,'original_triangles':len(branch['mesh']['polygons']),
        'triangles':len(faces),'ring_correspondence_error_m':max(ring_error(v,sides,a,z) for a,z in zip(kept,kept[1:]))}
    return b


def build(resolved):
    from .pine_painted_volume import build as volume_build,budget
    previous=copy.deepcopy(resolved)
    previous['blueprint_definition']['components']['representation']='pine-painted-crossed@0.2.0'
    previous['budget_upper_bound']=budget(resolved['parameters'],resolved['limits'])
    branches,wood,groups=volume_build(previous)
    optimized=[optimize(b,wood[0]) for b in wood]
    lookup={b['id']:b for b in branches}
    # Operación independiente: el ajuste de copa se realiza después de optimizar madera.
    for g in groups:
        original=canonical_hash(g)
        b=lookup[g['support_id']]
        axis=unit(sub(b['points_m'][-1],g['origin_m']))
        origin=g['origin_m'];vertices=[]
        for vertex in g['vertices']:
            delta=sub(vertex,origin);along=sum(x*y for x,y in zip(delta,axis))
            vertices.append([origin[i]+along*axis[i]*.98+(delta[i]-along*axis[i])*.94 for i in range(3)])
        g['vertices']=vertices
        g['crown_tuning']={'length_scale':.98,'width_scale':.94,'before_tuning_sha256':original}
    return branches,optimized,groups


def sampled_surface_error(original,optimized):
    """Comparación bidireccional local de las caras laterales (vértices, aristas y centros)."""
    from .surface_evaluation import point_triangle_distance
    sides=optimized['wood_optimization']['sides_unchanged']
    kept=optimized['wood_optimization']['retained_rings']
    old=original['mesh'];new=optimized['mesh'];maximum=0.
    def samples(mesh,face):
        a,b,c=[mesh['vertices'][i] for i in face]
        return [a,b,c]+[[(x[k]+y[k])/2 for k in range(3)] for x,y in [(a,b),(a,c),(b,c)]]+[[sum(v[k] for v in (a,b,c))/3 for k in range(3)]]
    def compare(source,faces,target,candidates):
        error=0.
        for face in faces:
            for point in samples(source,face):
                error=max(error,min(point_triangle_distance(point,*(target['vertices'][j] for j in candidate)) for candidate in candidates))
        return error
    for span,(a,z) in enumerate(zip(kept,kept[1:])):
        for side in range(sides):
            old_faces=[old['polygons'][ring*sides*2+side*2+i] for ring in range(a,z) for i in range(2)]
            new_faces=[new['polygons'][span*sides*2+side*2+i] for i in range(2)]
            maximum=max(maximum,compare(old,old_faces,new,new_faces),compare(new,new_faces,old,old_faces))
    return maximum
