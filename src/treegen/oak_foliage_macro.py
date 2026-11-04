"""OF5: macromasas espaciales y pocas reasignaciones sobre madera real."""
import copy
import math
from collections import Counter
from .branch_structure import add,sub,mul,length,dot
from .oak_growth import sample,frame,unit,cross
from .oak_foliage_peripheral import build as build_v4
from .oak_foliage_macro_contract import validate_canopy
from .oak_foliage_canopy import minimum_radius
from .oak_foliage_layout import surface_point
from .oak_foliage_cards import rooted_panels


def macro_plan(groups,masses,h):
    """Tres conjuntos espaciales, sin sectores radiales ni cámaras preferidas."""
    points={m['id']:[sum(g['anchor_m'][k] for g in groups if g['mass_id']==m['id'])/m['group_count'] for k in range(3)] for m in masses}
    ids=sorted(points);centers=[points[max(ids,key=lambda i:(points[i][2],i))]]
    while len(centers)<min(3,len(ids)):
        centers.append(points[max(ids,key=lambda i:(min(length(sub(points[i],p)) for p in centers),i))])
    assignments={}
    for _ in range(6):
        assignments={i:min(range(len(centers)),key=lambda j:(length(sub(points[i],centers[j])),j)) for i in ids}
        for j in range(len(centers)):
            members=[points[i] for i in ids if assignments[i]==j]
            if members:centers[j]=[sum(p[k] for p in members)/len(members) for k in range(3)]
    macros=[{'id':f'macro:{j}','center_m':c,'mass_ids':[i for i in ids if assignments[i]==j]} for j,c in enumerate(centers)]
    edges=[]
    for m in macros:
        members=m['mass_ids'];visited={members[0]} if members else set()
        while len(visited)<len(members):
            a,b=min(((a,b) for a in visited for b in members if b not in visited),key=lambda ab:(length(sub(points[ab[0]],points[ab[1]])),ab))
            edges.append((a,b));visited.add(b)
    return macros,edges,assignments


def build(structure,spec,templates,*,prepared=None):
    p=validate_canopy(spec);result=build_v4(structure,{**p,'version':'oak-foliage-canopy-0.4.0'},templates,prepared=prepared)
    result=copy.deepcopy(result);groups=result['groups'];masses=result['masses'];h=structure['preset']['height_m'];core=h*p['core_radius_over_height']
    index={b['id']:b for b in structure['branches']};macros,edges,assignments=macro_plan(groups,masses,h)
    mass_index={m['id']:m for m in masses};changed=set();changes=[];attempts=0
    # Mantener el 91.7% o más de los grupos exactamente; nada se añade.
    limit=min(18,len(groups)//12);bridge_limit=min(10,limit)
    def clearance(g):return math.hypot(*g['anchor_m'][:2])-core
    def density(g):return sum(length(sub(g['anchor_m'],q['anchor_m']))<h*.10 for q in groups if q['id']!=g['id'])
    def donor_score(g):return (2.5 if g['parent_t']>.80 else 0)+min(6,density(g))+(2 if clearance(g)<h*.09 else 0)
    candidates=[]
    for b in structure['branches']:
        if b['order']<2:continue
        for j in range(24):
            t=.24+(.78-.24)*(j+.5)/24;point,tangent=sample(b['points'],t)
            if math.hypot(*point[:2])<core+h*.025:continue
            candidates.append((b,t,point,tangent))
    def relocate(g,c,target_mass,role,scale=1.,direction=None):
        nonlocal attempts
        b,t,point,tangent=c;normal,up=frame(tangent)
        outward=unit((point[0],point[1],0));radial=unit(add(up,mul(outward,.35)))
        anchor=surface_point(b,t,radial)
        if direction is None:direction=tangent
        heading=math.atan2(direction[1],direction[0]);original=g['axes']
        bases=[original]
        for angle in (heading,heading+math.pi/3,heading-math.pi/3):
            x=(math.cos(angle)*.98,math.sin(angle)*.98,.198997487421324)
            y,z=frame(x);bases.append([x,y,unit(cross(x,y))])
        for basis in bases:
            attempts+=1;new=copy.deepcopy(g);size=[s*scale for s in g['size_m']]
            origin=sub(anchor,[sum(g['root_normalized'][a]*size[a]*basis[a][v] for a in range(3)) for v in range(3)])
            new.update(parent_branch_id=b['id'],parent_t=t,anchor_m=anchor,center_m=origin,axes=basis,size_m=size,mass_id=target_mass,
                       role=role,candidate_id=b['id']+f':of5:{t:.8f}',of5_reason=role)
            cards=rooted_panels(new,new['template_index'])
            if minimum_radius(cards)<core or min(v[2] for pc in cards for v in pc['vertices'])<0:continue
            return new
        return None
    # Enlaces espaciales entre masas del mismo conjunto. Solo donde existe madera
    # periférica próxima al hueco; no atravesar núcleo ni inventar soportes.
    gaps=[]
    for a,b in edges:
        ga=[g for g in groups if g['mass_id']==a];gb=[g for g in groups if g['mass_id']==b]
        left,right=min(((u,v) for u in ga for v in gb),key=lambda uv:length(sub(uv[0]['anchor_m'],uv[1]['anchor_m'])))
        gap=length(sub(left['anchor_m'],right['anchor_m']))
        if h*.065<gap<h*.36:gaps.append((gap,a,b,left['anchor_m'],right['anchor_m']))
    for gap,a,b,left,right in sorted(gaps,reverse=True):
        if len(changes)>=bridge_limit:break
        midpoint=mul(add(left,right),.5);flow=sub(right,left)
        pool=[c for c in candidates if min(length(sub(c[2],left)),length(sub(c[2],right)))>h*.035 and length(sub(c[2],midpoint))<min(h*.15,gap*.65)]
        donors=[g for g in groups if g['id'] not in changed and g['mass_id'] in (a,b) and mass_index[g['mass_id']]['group_count']>3]
        placed=None
        for c in sorted(pool,key=lambda c:(length(sub(c[2],midpoint)),c[0]['id'],c[1]))[:24]:
            for g in sorted(donors,key=lambda g:(-donor_score(g),g['id']))[:6]:
                if density(g)<2 or g['parent_branch_id'].split('/')[0]!=c[0]['id'].split('/')[0]:continue
                # Puentes pequeños: proceden de grupos redundantes, nunca extras.
                new=relocate(g,c,g['mass_id'],'macro_bridge',.78,flow)
                if new is not None:placed=(g,new);break
            if placed:break
        if placed:
            g,new=placed;groups[groups.index(g)]=new;changed.add(g['id']);changes.append({'id':g['id'],'reason':'macro_bridge','from_branch':g['parent_branch_id'],'from_t':g['parent_t'],'to_branch':new['parent_branch_id'],'to_t':new['parent_t'],'mass_pair':[a,b],'gap_m':gap})
    # Aliviar capuchones y ruido interior sin cambiar las masas que funcionan.
    donors=sorted((g for g in groups if g['id'] not in changed and (g['parent_t']>.82 or clearance(g)<h*.075) and density(g)>=2),key=lambda g:(-donor_score(g),g['id']))
    inner=[g for g in donors if g['parent_t']<=.82 and clearance(g)<h*.075]
    donors=inner+[g for g in donors if g not in inner];inner_count=0
    for g in donors:
        if len(changes)>=limit:break
        b=index[g['parent_branch_id']];reason='tip_retreat' if g['parent_t']>.82 else 'inner_redundancy'
        if reason=='inner_redundancy':
            if inner_count>=2:continue
            options=[]
            for j in range(20):
                t=.25+.53*j/19;point,tangent=sample(b['points'],t)
                if math.hypot(*point[:2])>math.hypot(*g['anchor_m'][:2])+h*.015:
                    options.append((b,t,point,tangent))
            options.sort(key=lambda c:length(sub(c[2],g['anchor_m'])))
        else:
            t=max(.25,g['parent_t']-.14);point,tangent=sample(b['points'],t);options=[(b,t,point,tangent)]
        new=None
        for c in options:
            new=relocate(g,c,g['mass_id'],reason)
            if new is not None:break
        if new is None:continue
        if reason=='inner_redundancy':inner_count+=1
        groups[groups.index(g)]=new;changed.add(g['id']);changes.append({'id':g['id'],'reason':reason,'from_branch':b['id'],'from_t':g['parent_t'],'to_branch':b['id'],'to_t':new['parent_t']})
    for g in groups:g['macro_id']=f"macro:{assignments[g['mass_id']]}"
    cards=[pc for g in groups for pc in rooted_panels(g,g['template_index'])]
    result.update(version=p['version'],spec=p,groups=groups,foliage=cards,macros=macros,macro_links=edges,refinements=changes,
                  refinement_attempts=attempts,minimum_card_radius_m=minimum_radius(cards),scope='mature pilot, bounded refinement of OF4; no seed overrides')
    result['axis_quotas']=dict(Counter(g['parent_branch_id'] for g in groups))
    result['fork_quotas']=dict(Counter('/'.join(g['parent_branch_id'].split('/')[:2]) for g in groups))
    return result
