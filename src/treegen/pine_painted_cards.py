"""Cruzadas 0.4.0: seis tris, mismos planos y mapa afín de pintura que 0.3.0."""
import copy
import math
from .pine_painted_sample import canonical_hash, ROW_CENTERS

# Envolver el octágono original conservando su corte superior distal.
# Las extensiones basal/inferior solo contienen alfa < .5 en el atlas congelado.
OUTLINE = ((.05,-.155),(.97,-.155),(.97,.12),(.65,.155),(.05,.155))
FACES = ((0,1,2),(0,2,3),(0,3,4))


def budget(parameters,limits):
    from .pine_painted_volume import budget as previous_budget
    result=previous_budget(parameters,dict(limits,triangles=12500))
    total=result['wood_triangles']+6*result['groups_max']
    if total>limits['triangles'] or limits['materials']<2:
        raise ValueError('Presupuesto de láminas optimizadas excedido')
    return {**result,'added_triangles_max':6*result['groups_max'],'triangles_max':total}


def optimize(group):
    result=copy.deepcopy(group);vertices=[];uv=[]
    center=ROW_CENTERS[group['atlas_variant']]
    for offset in (0,8):
        # Base afín derivada de la lámina ya colocada y ajustada 2.2.0.
        a,b,c=[group['vertices'][offset+i] for i in (0,1,2)]
        transverse=[(b[k]-a[k])/.09 for k in range(3)]
        axial=[(c[k]-a[k]+.110*transverse[k])/.18 for k in range(3)]
        for u,v in OUTLINE:
            vertices.append([a[k]+(u-.05)*axial[k]+(v+.045)*transverse[k] for k in range(3)])
            uv.append([u,center+v])
    # El orden del contorno es inverso al de las caras históricas.
    # Nueva solicitud: -10 % del volumen envolvente por grupo, longitud fija.
    from .pine import sub,unit
    # El borde lateral no es el eje: obtenerlo de la base UV afín anterior.
    a,b,c=[group['vertices'][i] for i in (0,1,2)]
    transverse=[(b[k]-a[k])/.09 for k in range(3)]
    axis=unit([(c[k]-a[k]+.110*transverse[k])/.18 for k in range(3)])
    origin=group['origin_m'];width=math.sqrt(.9)
    tuned=[]
    for v in vertices:
        delta=sub(v,origin);along=sum(delta[k]*axis[k] for k in range(3))
        tuned.append([origin[k]+along*axis[k]+width*(delta[k]-along*axis[k]) for k in range(3)])
    result['vertices']=tuned;result['uv']=uv
    result['crown_reduction']={'envelope_volume_ratio':.9,'length_scale':1,'width_scale':width}
    result['polygons']=[[offset+a,offset+c,offset+b] for offset in (0,5) for a,b,c in FACES]
    result['card_optimization']={'version':'pine-painted-cards-0.1.0','before_sha256':canonical_hash(group),
        'original_triangles':12,'triangles':6,'mapping':'same-affine-uv-planes'}
    return result


def build(resolved):
    from .pine_painted_wood import build as wood_build
    previous=copy.deepcopy(resolved)
    previous['blueprint_definition']['components']['representation']='pine-painted-crossed@0.3.0'
    branches,wood,groups=wood_build(previous)
    return branches,wood,[optimize(g) for g in groups]
