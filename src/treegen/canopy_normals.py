"""Ensayo T4: campos elipsoidales locales acotados; sin cambiar geometría."""
import math
from .season_calendar import validate_groups, validate_calendar, digest

VERSION = 'canopy-local-normals-0.1.0'


def dot(a,b):return sum(x*y for x,y in zip(a,b))
def sub(a,b):return [x-y for x,y in zip(a,b)]
def unit(v):
    length=math.sqrt(dot(v,v))
    if not math.isfinite(length) or length<1e-12:raise ValueError('Vector degenerado')
    return [x/length for x in v]
def vector(v):
    return isinstance(v,(tuple,list)) and len(v)==3 and all(type(x) in (float,int) and math.isfinite(x) and abs(x)<=1000 for x in v)
def godot(v):return [v[0],v[2],-v[1]]


def inverse(a):
    # Matriz simétrica definida positiva, regularizada antes de invertir.
    x,y,z=a[0];_,u,v=a[1];_,_,w=a[2]
    c=[[u*w-v*v,z*v-y*w,y*v-z*u],[z*v-y*w,x*w-z*z,y*z-x*v],[y*v-z*u,y*z-x*v,x*u-y*y]]
    det=x*c[0][0]+y*c[0][1]+z*c[0][2]
    if not math.isfinite(det) or det<=1e-18:raise ValueError('Volumen local singular')
    return [[n/det for n in row] for row in c]


def build_fields(groups,calendar):
    groups=validate_groups(groups);validate_calendar(calendar)
    by_id={g['id']:g for g in groups}
    if set(by_id)!={r['id'] for r in calendar['groups']} or digest(groups)!=calendar['groups_sha256']:
        raise ValueError('Vecindad/calendario no corresponden a los volúmenes')
    result={}
    for row in calendar['groups']:
        g=by_id[row['id']];radius=max(g['size_m'])/2
        if len(row['neighbors'])>24:raise ValueError('Más de 24 vecinos')
        members=[(g,1.0)]
        for identifier in sorted(row['neighbors']):
            other=by_id[identifier];distance=math.dist(g['center_m'],other['center_m'])
            if distance<=radius*2.5:
                members.append((other,.5*math.exp(-(distance/(1.5*radius))**2)))
        total=sum(w for _,w in members)
        center=[sum(w*m['center_m'][k] for m,w in members)/total for k in range(3)]
        covariance=[[0.0]*3 for _ in range(3)]
        for m,weight in members:
            delta=sub(m['center_m'],center)
            for i in range(3):
                for j in range(3):
                    covariance[i][j]+=weight*(delta[i]*delta[j]+sum(axis[i]*axis[j]*(size/2)**2/3 for axis,size in zip(m['axes'],m['size_m'])))/total
        for k in range(3):covariance[k][k]+=.04*radius**2
        # Cambio de base Blender Z arriba -> glTF/Godot Y arriba.
        basis=[[1,0,0],[0,0,1],[0,-1,0]]
        transformed=[[sum(basis[i][a]*covariance[a][b]*basis[j][b] for a in range(3) for b in range(3)) for j in range(3)] for i in range(3)]
        result[g['id']]={'center':godot(center),'inverse_covariance':inverse(transformed),
                         'neighbors':[m['id'] for m,_ in members[1:]]}
    return {key:result[key] for key in sorted(result)}


def normal(position,original,field,strength,max_angle_deg=60.0):
    if not vector(position) or not vector(original) or abs(dot(original,original)-1)>.003:
        raise ValueError('Posición o normal original inválida')
    if type(strength) not in (int,float) or not math.isfinite(strength) or not 0<=strength<=.75:
        raise ValueError('Mezcla fuera de [0,.75]')
    if type(max_angle_deg) not in (int,float) or not math.isfinite(max_angle_deg) or not 0<max_angle_deg<=60:
        raise ValueError('Ángulo fuera de (0,60]')
    n=unit(original)
    if strength==0:return n
    delta=sub(position,field['center'])
    target=[dot(row,delta) for row in field['inverse_covariance']]
    if dot(target,target)<1e-20:return n
    target=unit(target)
    # El frente conserva el hemisferio original; el motor resuelve el reverso.
    if dot(target,n)<0:target=[-v for v in target]
    angle=math.acos(max(-1,min(1,dot(n,target))))
    angle=min(angle,max_angle_deg*math.pi/180)
    tangent=sub(target,[dot(target,n)*v for v in n])
    if dot(tangent,tangent)<1e-20:return n
    tangent=unit(tangent)
    # Interpolación angular: cota explícita y sin cancelación de antipodales.
    return unit([math.cos(angle*strength)*a+math.sin(angle*strength)*b for a,b in zip(n,tangent)])
