"""OF6: envolventes compartidas y extensión hacia masas vecinas reales."""
import copy
import math
from .branch_structure import add,sub,mul,length,dot
from .oak_growth import unit,cross,frame
from .oak_foliage_macro import build as build_v5
from .oak_foliage_volume_contract import validate_canopy
from .oak_foliage_canopy import minimum_radius
from .oak_foliage_cards import rooted_panels


def envelope_plan(groups,macros):
    """El volumen se calcula desde anclajes reales; no desde cámaras/semillas."""
    result=[]
    for macro in macros:
        gs=[g for g in groups if g['macro_id']==macro['id']]
        center=[sum(g['anchor_m'][k] for g in gs)/len(gs) for k in range(3)]
        # Dirección horizontal principal por iteración de potencia, reproducible.
        xx=sum((g['anchor_m'][0]-center[0])**2 for g in gs)
        xy=sum((g['anchor_m'][0]-center[0])*(g['anchor_m'][1]-center[1]) for g in gs)
        yy=sum((g['anchor_m'][1]-center[1])**2 for g in gs)
        v=(1.,.618,0.)
        for _ in range(8):
            q=(xx*v[0]+xy*v[1],xy*v[0]+yy*v[1],0.)
            if length(q)>1e-9:v=unit(q)
        side=(-v[1],v[0],0.)
        radii=[max(abs(dot(sub(g['anchor_m'],center),axis)) for g in gs) for axis in (v,side,(0,0,1))]
        result.append({'id':macro['id'],'center_m':center,'long_axis':v,'side_axis':side,'radii_m':radii,'group_count':len(gs)})
    return result


def build(structure,spec,templates,*,prepared=None):
    p=validate_canopy(spec);result=copy.deepcopy(build_v5(structure,{**p,'version':'oak-foliage-canopy-0.5.0'},templates,prepared=prepared))
    groups=result['groups'];h=structure['preset']['height_m'];core=h*p['core_radius_over_height']
    envelopes=envelope_plan(groups,result['macros']);envs={e['id']:e for e in envelopes}
    by_mass={m['id']:[g for g in groups if g['mass_id']==m['id']] for m in result['masses']}
    centers={mid:[sum(g['anchor_m'][k] for g in gs)/len(gs) for k in range(3)] for mid,gs in by_mass.items()}
    # Seleccionar por interfaz entre masas, no por identidad aleatoria de grupo.
    targets={};scores={}
    for g in groups:
        others=[q for q in groups if q['macro_id']==g['macro_id'] and q['mass_id']!=g['mass_id']]
        if not others:continue
        q=min(others,key=lambda q:(length(sub(q['anchor_m'],g['anchor_m'])),q['id']))
        delta=sub(q['anchor_m'],g['anchor_m']);d=length(delta)
        targets[g['id']]=(q,delta,d)
        # Interfaces más separadas reciben alcance; se limita el número de grupos
        # extensores para no convertir cada conjunto en una placa compacta.
        scores[g['id']]=d
    extenders=set()
    for envelope in envelopes:
        members=[g for g in groups if g['macro_id']==envelope['id'] and g['id'] in targets
                 and g['parent_t']<.82 and h*.035<targets[g['id']][2]<h*.27]
        extenders.update(g['id'] for g in sorted(members,key=lambda g:(-scores[g['id']],g['id']))[:max(1,round(len(members)*.68))])
    transformed=[];attempts=0;records=[]
    for g in groups:
        e=envs[g['macro_id']];target=targets.get(g['id']);old_size=g['size_m']
        old_x=g['axes'][0];macro_flow=e['long_axis']
        if dot(old_x,macro_flow)<0:macro_flow=mul(macro_flow,-1)
        direction=unit(add(mul(old_x,.78),mul(macro_flow,.22)))
        scale=1.10;kind='shared_envelope'
        if target and g['id'] in extenders:
            kind='interface_extension'
            # Ampliar el grupo completo, sin estirar las hojas de la pintura.
            scale=1.22+.24*min(1.,target[2]/(h*.20))
        if g['parent_t']>.84:scale=1.0
        chosen=None
        # Cerca del núcleo el tamaño previo es un límite de seguridad. La
        # reducción de alcance no cambia el contacto ni la pintura.
        for trial,(flow,factor) in enumerate(((direction,scale),(old_x,scale),(old_x,1.))):
            y=sub(g['axes'][1],mul(flow,dot(g['axes'][1],flow)))
            if length(y)<1e-8:y=frame(flow)[0]
            y=unit(y);basis=[flow,y,unit(cross(flow,y))];size=[v*factor for v in old_size]
            attempts+=1
            origin=sub(g['anchor_m'],[sum(g['root_normalized'][a]*size[a]*basis[a][k] for a in range(3)) for k in range(3)])
            new={**g,'center_m':origin,'axes':basis,'size_m':size,'volume_role':kind if factor>1 else ('tip_preserved' if scale==1. else 'core_protected'),
                 'volume_trial':trial,'volume_scale':factor}
            pieces=rooted_panels(new,new['template_index'])
            if minimum_radius(pieces)<core or min(v[2] for pc in pieces for v in pc['vertices'])<0:continue
            chosen=new;break
        if chosen is None:chosen={**g,'volume_role':'core_protected','volume_trial':None,'volume_scale':1.}
        transformed.append(chosen)
        if chosen['axes']!=g['axes'] or chosen['size_m']!=g['size_m']:
            records.append({'id':g['id'],'macro_id':g['macro_id'],'role':chosen['volume_role'],'size_before_m':old_size,'size_after_m':chosen['size_m'],
                            'neighbor_id':target[0]['id'] if target else None,'anchor_distance_m':target[2] if target else None})
    cards=[pc for g in transformed for pc in rooted_panels(g,g['template_index'])]
    result.update(version=p['version'],spec=p,groups=transformed,foliage=cards,envelopes=envelopes,volume_changes=records,
                  volume_attempts=attempts,minimum_card_radius_m=minimum_radius(cards),scope='mature pilot: shared geometric volumes; no seed overrides')
    return result
