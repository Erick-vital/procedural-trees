"""OF11: redistribuir 24 grupos en madera central alta, sin tapar horquillas bajas."""
import copy
import math
from collections import Counter
from .branch_structure import sub,mul,length
from .oak_growth import sample,unit
from .oak_growth_central import add_central_branch
from .oak_foliage_gaps import build as build_v10
from .oak_foliage_central_contract import validate_canopy
from .oak_foliage_layout import surface_point,allocate
from .oak_foliage_top import balanced_basis
from .oak_foliage_cards import rooted_panels
from .oak_foliage_canopy import minimum_radius


def minimum_radius_below(cards,height):
    """Recortar caras contra Z antes de comprobar el radio; protege caras enteras."""
    clipped=[]
    for card in cards:
        for face in card['polygons']:
            poly=[card['vertices'][i] for i in face];out=[]
            for a,b in zip(poly,poly[1:]+poly[:1]):
                if a[2]<=height:out.append(a)
                if (a[2]<=height)!=(b[2]<=height):
                    t=(height-a[2])/(b[2]-a[2]);out.append([a[k]+t*(b[k]-a[k]) for k in range(3)])
            if out:clipped.append({'vertices':out,'polygons':[list(range(len(out)))]})
    return minimum_radius(clipped)


def build(structure,spec,templates,*,prepared=None):
    p=validate_canopy(spec)
    base=build_v10(structure,{**p,'version':'oak-foliage-canopy-0.10.0'},templates,prepared=prepared)
    result=copy.deepcopy(base);extended=add_central_branch(structure);h=structure['preset']['height_m']
    floor=h*.62;core=h*p['core_radius_over_height'];groups=result['groups']
    # No mover grupos que ya tienen complementos: todos esos planos se conservan.
    blocked={q['group_id'] for q in result['lateral_complements']+result['gap_fans']}
    by_arm={bid:[g for g in groups if g['parent_branch_id'].split('/')[0]==bid and g['id'] not in blocked]
            for bid in result['ledger']['primary_quotas']}
    quotas=allocate(24,{bid:len(gs) for bid,gs in by_arm.items() if gs})
    donors=[]
    for bid,gs in by_arm.items():
        n=quotas.get(bid,0)
        if n>len(gs):raise ValueError('No hay donantes centrales suficientes')
        def density(g):return sum(math.dist(g['anchor_m'],q['anchor_m'])<h*.13 for q in groups if q['id']!=g['id'])
        donors.extend(sorted(gs,key=lambda g:(-density(g),g['id']))[:n])
    new_ids=set(extended['central_extension']['branch_ids']);parents={b['parent_id'] for b in extended['branches'] if b['id'] in new_ids}
    supports=[b for b in extended['branches'] if b['id'] in new_ids and b['id'] not in parents]
    per_support=math.ceil(len(donors)/len(supports))
    placed={};records=[];attempts=0
    for i,g in enumerate(donors):
        b=supports[i%len(supports)];rank=i//len(supports);t=.22+.66*(rank+.5)/per_support
        point,tangent=sample(b['points'],t)
        radial=unit((math.cos(i*2.399963),math.sin(i*2.399963),.65))
        anchor=surface_point(b,t,radial);chosen=None
        for trial in range(12):
            attempts+=1;basis=balanced_basis(i*2.399963+trial*math.pi/6,.12*math.sin(i))
            center=sub(anchor,[sum(g['root_normalized'][a]*g['size_m'][a]*basis[a][k] for a in range(3)) for k in range(3)])
            new={**g,'parent_branch_id':b['id'],'parent_t':t,'anchor_m':anchor,'center_m':center,'axes':basis,
                 'region_id':'central-upper','candidate_id':f'{b["id"]}:of11:{t:.8f}', 'central_trial':trial}
            cards=rooted_panels(new,new['template_index'])
            if min(v[2] for c in cards for v in c['vertices'])<floor:continue
            if max(v[2] for c in cards for v in c['vertices'])>h*1.12:continue
            chosen=new;break
        if chosen is None:raise ValueError('Grupo central invade la protección inferior o altura: '+g['id'])
        placed[g['id']]=chosen;records.append({'id':g['id'],'from_branch':g['parent_branch_id'],'from_anchor_m':g['anchor_m'],
                                             'to_branch':b['id'],'to_anchor_m':anchor,'trial':trial})
    result['groups']=[placed.get(g['id'],g) for g in groups]
    # Tres láminas por grupo en el mismo orden; complementos OF8/OF10 exactos.
    result['foliage']=[c for g in result['groups'] for c in rooted_panels(g,g['template_index'])]+copy.deepcopy(base['foliage'][648:])
    extra=extended['central_extension']['added_wood_triangles']
    result['ledger'].update(of10_tree_triangles=base['ledger']['tree_projected_triangles'],
                            added_central_wood_triangles=extra,tree_wood_triangles=base['ledger']['tree_wood_triangles']+extra,
                            tree_projected_triangles=base['ledger']['tree_projected_triangles']+extra)
    if result['ledger']['tree_projected_triangles']>6999:raise ValueError('Presupuesto central excedido')
    result.update(version=p['version'],spec=p,wood=extended['branches'],structure=extended,
                  central_changes=records,central_attempts=attempts,central_extension=extended['central_extension'],
                  central_protection={'radius_m':core,'maximum_protected_z_m':floor,'relocated_groups':24},
                  minimum_card_radius_m=minimum_radius(result['foliage']),
                  minimum_lower_card_radius_m=minimum_radius_below(result['foliage'],floor),
                  scope='mature pilot; real upper central branch and 24 relocated groups; lower forks protected')
    result['axis_quotas']=dict(Counter(g['parent_branch_id'] for g in result['groups']))
    return result
