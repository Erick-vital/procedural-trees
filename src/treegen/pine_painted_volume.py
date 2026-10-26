"""Cruzadas 0.2.0: refuerzo común de volumen, creciente hacia la parte superior."""
import copy
import math
from .pine import point_on,sub,unit,cross
from .pine_painted_sample import panels,canonical_hash


def budget(parameters,limits):
    from .pine_painted import check_parameters
    result=check_parameters(parameters,limits)
    n=parameters['base']['whorl_count']*parameters['base']['branches_per_whorl']
    groups=9*n+3  # primaria + dos por secundaria; tres grupos en el eje.
    total=result['wood_triangles']+12*groups
    if total>limits['triangles']:
        raise ValueError('Presupuesto de volumen pintado excedido')
    return {**result,'groups_max':groups,'added_triangles_max':12*groups,'triangles_max':total}


def expand(group,axis,upper,*,extra=False):
    origin=group['origin_m'];axis=unit(axis)
    distances=[sum((v[i]-origin[i])*axis[i] for i in range(3)) for v in group['vertices']]
    old_length=max(distances)
    length=max(old_length*(1.12+.38*upper),.35+.50*upper)
    axial=length/old_length
    transverse=axial*(1.55+.55*upper)
    # El grupo añadido gira 32 grados alrededor del eje: sigue siendo dos láminas ortogonales.
    angle=math.radians(32 if extra else 0)
    vertices=[]
    for v in group['vertices']:
        delta=sub(v,origin);along=sum(x*y for x,y in zip(delta,axis))
        radial=[delta[i]-along*axis[i] for i in range(3)]
        turned=cross(axis,radial)
        vertices.append([origin[i]+along*axis[i]*axial+transverse*(radial[i]*math.cos(angle)+turned[i]*math.sin(angle)) for i in range(3)])
    # Acotar el grupo completo por homotecia, sin cortar puntas ni cambiar el anclaje.
    highest=max(v[2] for v in vertices)
    cap=min(1,(11.97-origin[2])/(highest-origin[2])) if highest>11.97 else 1
    group['vertices']=[[origin[i]+(v[i]-origin[i])*cap for i in range(3)] for v in vertices]
    group['volume_rule']={'upper_weight':upper,'length_gain':axial,'width_gain':transverse,'rotation_deg':32 if extra else 0,'height_scale':cap}
    return group


def build(resolved):
    from .pine_painted import build as original_build,check_parameters
    historical=copy.deepcopy(resolved)
    historical['blueprint_definition']['components']['representation']='pine-painted-crossed@0.1.0'
    historical['budget_upper_bound']=check_parameters(resolved['parameters'],resolved['limits'])
    branches,wood,old_groups=original_build(historical)
    result=[]
    for b,g in zip(branches,old_groups):
        if b['parent_id'] is None:
            for index,t in enumerate((.78,.86,.93)):
                origin=point_on(b,t);end=point_on(b,min(.995,t+.09))
                axis=unit(sub(end,origin));side=unit(cross(axis,[0,1,0]));up=cross(axis,side)
                length=math.dist(origin,end)
                atlas=int(canonical_hash([resolved['paint_seed'],b['id'],index])[:8],16)%3
                proxy={'id':b['id'],'points_m':[[0,0,0],[length/1.06,0,0]]}
                leader=panels(proxy,'crossed',atlas)
                leader['vertices']=[[origin[i]+v[0]*axis[i]-v[1]*side[i]-v[2]*up[i] for i in range(3)] for v in leader['vertices']]
                leader.update(origin_m=origin,anchor_t=t,replacement='leader-needles',group_id=f'{b["id"]}:volume:{index}')
                result.append(expand(leader,axis,1))
            continue
        # Peso por altura de anclaje, mismo continuo en los cuatro casos.
        upper=max(0,min(1,(g['origin_m'][2]/12-.2)/.68))
        axis=sub(b['points_m'][-1],g['origin_m'])
        g['group_id']=b['id']+':volume:0'
        result.append(expand(g,axis,upper))
        if b['parent_id']!='pine:trunk':
            origin=point_on(b,.40)
            proxy={'id':b['id'],'points_m':[origin,b['points_m'][-1]]}
            atlas=int(canonical_hash([resolved['paint_seed'],b['id'],'fill'])[:8],16)%3
            added=panels(proxy,'crossed',atlas)
            added.update(anchor_t=.40,replacement='secondary-volume',group_id=b['id']+':volume:1')
            result.append(expand(added,sub(b['points_m'][-1],origin),upper,extra=True))
    assert len(result)==resolved['budget_upper_bound']['groups_max']
    return branches,wood,result
