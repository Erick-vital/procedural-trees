"""J3: cubrir todos los ejes jóvenes y el líder con grupos más voluminosos."""
import copy
import math
from collections import Counter
from .oak_growth_contract import validate_seed
from .oak_growth import sample,unit
from .branch_structure import sub,length
from .oak_foliage_layout import allocate,surface_point
from .oak_foliage_cards import rooted_panels
from .oak_foliage_top import balanced_basis
from .seeds import derive_seed

VERSION='oak-young-canopy-0.2.0'
FIXED={'preset':'presets/oak-growth/0.5.0/joven.json','tree_groups':264,
       'span_over_height':.16,'core_radius_over_height':0}
FIELDS={'version','seed','layout_seed','paint_seed',*FIXED}


def validate_canopy(spec):
    if not isinstance(spec,dict) or set(spec)!=FIELDS or spec.get('version')!=VERSION:
        raise ValueError('Contrato J3 inválido')
    for k in ('seed','layout_seed','paint_seed'):validate_seed(spec[k])
    if type(spec['tree_groups']) is not int:raise ValueError('Cupo J3 debe ser entero')
    for k,v in FIXED.items():
        if spec[k]!=v or (k in ('span_over_height','core_radius_over_height') and (type(spec[k]) not in (int,float) or not math.isfinite(spec[k]))):
            raise ValueError('J3 conserva perfil fijo: '+k)
    return copy.deepcopy(spec)


def build(structure,spec,templates,*,prepared=None):
    p=validate_canopy(spec)
    if structure.get('version')!='oak-growth-0.5.0' or structure['preset']['stage']!='joven' or structure['preset']['height_m']!=5 or structure['seed']!=p['seed']:
        raise ValueError('J3 requiere madera joven O5 de5 m y misma semilla')
    if prepared is None:raise ValueError('J3 requiere raíces opacas del atlas preparadas')
    h=structure['preset']['height_m'];branches=structure['branches']
    wood_triangles=sum((len(b['points'])-1)*2*b['sides']+b['sides']-2+(b['sides']-2 if b['order']==0 else 0) for b in branches)
    if wood_triangles>5415:raise ValueError('Cota de madera J3 excedida')
    if len(branches)>264:raise ValueError('Demasiados ejes para cubrir en264 grupos')
    weights={};candidates={};quota={b['id']:1 for b in branches}
    for b in branches:
        low=.74 if b['order']==0 else .40
        options=[]
        for j in range(32):
            t=low+(.96-low)*(j+.5)/32;point,tangent=sample(b['points'],t)
            if math.hypot(*point[:2])<h*p['core_radius_over_height']:continue
            options.append((t,point,tangent))
        if not options:raise ValueError('Eje sin candidatos J3: '+b['id'])
        candidates[b['id']]=options
        axis_length=sum(length(sub(c,a)) for a,c in zip(b['points'],b['points'][1:]))*(.96-low)
        weights[b['id']]=axis_length**.7*max(.1,b['vigor'])**.5*{0:1.2,1:.7,2:1.,3:1.1,4:.9}[b['order']]
    remaining=264-len(quota)
    while remaining:
        active={bid:w for bid,w in weights.items() if quota[bid]<12}
        if not active:raise ValueError('Capacidad J3 insuficiente')
        proposed=allocate(remaining,active);placed=0
        for bid,n in proposed.items():
            take=min(n,12-quota[bid]);quota[bid]+=take;placed+=take
        if not placed:raise ValueError('Reparto J3 sin progreso')
        remaining-=placed
    groups=[];foliage=[];coverage={}
    def rnd(identity,stream):return derive_seed(p['layout_seed'],'j3:'+identity+':'+stream)/2147483647
    for b in branches:
        bid=b['id'];n=quota[bid];options=candidates[bid];chosen=[]
        for i in range(n):
            # Primer grupo cerca del extremo; los demás llenan el recorrido útil.
            low=.74 if b['order']==0 else .40
            target=.91 if i==0 else low+(.87-low)*(i-.5)/max(1,n-1)
            item=min((o for o in options if o not in chosen),key=lambda o:(abs(o[0]-target),o[0]))
            chosen.append(item);t,point,tangent=item;identity=f'{bid}:j3:{i:02d}'
            yaw=math.atan2(tangent[1],tangent[0])+(rnd(bid,'yaw')-.5)*math.pi+(rnd(identity,'yaw')-.5)*.7
            basis=balanced_basis(yaw,(rnd(identity,'tilt')-.5)*.28)
            radial=unit((math.cos(yaw+.9),math.sin(yaw+.9),.7))
            anchor=surface_point(b,t,radial)
            index=derive_seed(p['paint_seed'],identity)%len(prepared);g=prepared[index]
            span=h*p['span_over_height']*(.90+.20*rnd(identity,'size'))
            # Recuperar espesor; evitar la compresión .55 de las cadenas B.
            size=[span*g['aspect'][a]*[1.02,1.15,.95][a] for a in range(3)]
            center=[anchor[k]-sum(g['root_normalized'][a]*size[a]*basis[a][k] for a in range(3)) for k in range(3)]
            group={'id':identity,'parent_branch_id':bid,'parent_t':t,'center_m':center,'axes':basis,'size_m':size,
                   'root_normalized':g['root_normalized'],'anchor_m':anchor,'template_index':index,
                   'role':'leader' if b['order']==0 else 'axis_tip' if i==0 else 'axis_fill'}
            cards=rooted_panels(group,index)
            if min(v[2] for c in cards for v in c['vertices'])<0:raise ValueError('Follaje J3 bajo suelo')
            groups.append(group);foliage.extend(cards)
        coverage[bid]={'group_count':n,'distal_t':chosen[0][0],'order':b['order']}
    if len(groups)!=264 or len({g['id'] for g in groups})!=264:raise ValueError('Cupo J3 incompleto')
    ledger={'total_groups':264,'group_triangles':6,'foliage_triangles':1584,'tree_wood_triangles':wood_triangles,
            'tree_projected_triangles':wood_triangles+1584,'family_wood_upper_bound':5415,'family_complete_upper_bound':6999,
            'axis_quotas':quota,'covered_axes':len(coverage),'required_axes':len(branches),'candidates_per_axis':32}
    return {'version':VERSION,'spec':p,'structure':copy.deepcopy(structure),'wood':copy.deepcopy(branches),
            'groups':groups,'foliage':foliage,'ledger':ledger,'masses_by_primary':{},'diagnostics':{'axis_coverage':coverage},
            'axis_quotas':dict(Counter(g['parent_branch_id'] for g in groups))}
