"""J2: copa joven completa, cupos por capacidad y madera O5 inmutable."""
import copy
import math
from collections import Counter
from .oak_young_sample import validate_sample
from .oak_foliage_layout import plan, allocate
from .oak_growth import sample
from .oak_young_distribution import build_branch

VERSION = 'oak-young-canopy-0.1.0'


def validate_canopy(spec):
    if not isinstance(spec,dict) or spec.get('version') != VERSION or any(k in spec for k in ('branch_id','mass_variant')):
        raise ValueError('Contrato de copa joven inválido')
    validate_sample({**spec,'version':'oak-young-sample-0.1.0','branch_id':'p:0','mass_variant':'B'})
    return copy.deepcopy(spec)


def capacity(structure,bid,p):
    """Mismos segmentos elegibles que B; máximo doce grupos por eje."""
    h=structure['preset']['height_m']
    primary=next(b for b in structure['branches'] if b['id']==bid)
    floor=sample(primary['points'],.65)[0][2]-.015*h
    per_axis={}
    for b in structure['branches']:
        if not b['id'].startswith(bid+'/') or b['order']<2:continue
        count=0
        for j in range(32):
            low=.35 if b['order']==2 else .24
            t=low+(.96-low)*(j+.5)/32;point,tangent=sample(b['points'],t)
            if math.hypot(point[0],point[1])/h < p['core_radius_over_height']+.015:continue
            if point[2]<floor and tangent[2]<.12:continue
            count+=1
        per_axis[b['id']]=count
    # B necesita dos centros distintos, incluso si hay un solo grupo.
    total=sum(min(12,n) for n in per_axis.values()) if sum(per_axis.values())>=2 else 0
    return {'groups_max':total,'candidate_count':sum(per_axis.values()),'per_axis':per_axis}


def build(structure,spec,templates,*,prepared=None):
    p=validate_canopy(spec)
    if structure.get('version')!='oak-growth-0.5.0' or structure['preset']['stage']!='joven' or structure['preset']['height_m']!=5 or structure['seed']!=p['seed']:
        raise ValueError('Copa joven requiere la estructura O5 joven de5 m y misma semilla')
    old={**p,'version':'oak-foliage-sample-0.1.0','branch_id':'p:0'}
    ledger=plan(structure,old)
    caps={bid:capacity(structure,bid,p) for bid in ledger['primary_quotas']}
    initial=copy.deepcopy(ledger['primary_quotas'])
    final={bid:min(q,caps[bid]['groups_max']) for bid,q in initial.items()}
    remaining=p['tree_groups']-sum(final.values())
    while remaining:
        spare={bid:ledger['primary_weights'][bid] for bid in final
               if caps[bid]['groups_max']>final[bid] and ledger['primary_weights'][bid]>0}
        if not spare:raise ValueError('Capacidad global joven insuficiente para144 grupos')
        addition=allocate(remaining,spare)
        placed=0
        for bid,n in addition.items():
            take=min(n,caps[bid]['groups_max']-final[bid]);final[bid]+=take;placed+=take
        if placed==0:raise ValueError('Reparto joven sin progreso')
        remaining-=placed
    ledger.update(primary_quotas=final,initial_primary_quotas=initial,capacities=caps,
                  redistributed_groups=sum(max(0,final[b]-q) for b,q in initial.items()),
                  family_wood_upper_bound=5415,family_complete_upper_bound=6279)
    if ledger['tree_wood_triangles']>5415:raise ValueError('Madera joven excede su cota')
    groups=[];foliage=[];masses={};diagnostics={}
    for bid,quota in final.items():
        if not quota:
            diagnostics[bid]={'skipped':True,'capacity':caps[bid]};continue
        r=build_branch(structure,{**p,'version':'oak-foliage-sample-0.2.0','branch_id':bid,'mass_variant':'B'},templates,ledger=ledger,prepared=prepared)
        groups.extend(r['groups']);foliage.extend(r['foliage']);masses[bid]=r['masses'];diagnostics[bid]=r['diagnostics']
    if len(groups)!=144 or len({g['id'] for g in groups})!=144:raise ValueError('Cupo joven incompleto o IDs repetidos')
    return {'version':VERSION,'spec':p,'structure':copy.deepcopy(structure),'wood':copy.deepcopy(structure['branches']),
            'groups':groups,'foliage':foliage,'ledger':ledger,'masses_by_primary':masses,'diagnostics':diagnostics,
            'axis_quotas':dict(Counter(g['parent_branch_id'] for g in groups))}
