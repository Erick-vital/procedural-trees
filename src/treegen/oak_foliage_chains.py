"""OF2: seleccionar segmentos y componer masas relacionadas por brazo."""
import math
from .branch_structure import add,sub,mul,length,dot
from .oak_growth import sample,frame,unit,cross
from .seeds import derive_seed
from .oak_foliage_chain_contract import validate_sample
from .oak_foliage_layout import plan,allocate,surface_point
from .oak_foliage_cards import template_geometry,rooted_panels

PROFILES={
    'A':{'name':'Terminales y laterales','spread':.070,'bridge':.28,'tip_bias':2.8,'mass_offset':-1},
    'B':{'name':'Cadena con continuidad media','spread':.125,'bridge':1.4,'tip_bias':.6,'mass_offset':0},
    'C':{'name':'Cadena fragmentada','spread':.050,'bridge':.65,'tip_bias':1.0,'mass_offset':1},
}


def build(structure,spec,templates,*,prepared=None):
    p=validate_sample(spec);base={k:v for k,v in p.items() if k!='mass_variant'};base['version']='oak-foliage-sample-0.1.0'
    ledger=plan(structure,base);bid=p['branch_id'];h=structure['preset']['height_m'];m=structure['preset']['maturity'];profile=PROFILES[p['mass_variant']]
    selected=[b for b in structure['branches'] if b['id']==bid or b['id'].startswith(bid+'/')]
    index={b['id']:b for b in selected};primary=index[bid];quota=ledger['primary_quotas'][bid]
    def rnd(identity,stream):return derive_seed(p['layout_seed'],f'of2:{identity}:{stream}')/2147483647
    flow=unit(sub(primary['points'][-1],primary['points'][0]));horizontal=unit((flow[0],flow[1],.08))
    floor=sample(primary['points'],.65)[0][2]-.015*h
    lengths={b['id']:sum(length(sub(c,a)) for a,c in zip(b['points'],b['points'][1:])) for b in selected}
    starts={bid:0.}
    for b in sorted(selected,key=lambda b:b['order']):
        if b['id']!=bid:starts[b['id']]=starts[b['parent_id']]+lengths[b['parent_id']]*b['parent_t']
    candidates=[];rejected_lower=0
    for b in selected:
        if b['order']<2:continue
        for j in range(32):
            low=.35 if b['order']==2 else .24;t=low+(.96-low)*(j+.5)/32
            point,tangent=sample(b['points'],t);radius=math.hypot(point[0],point[1])/h
            if radius<p['core_radius_over_height']+.015:continue
            if point[2]<floor and tangent[2]<.12:rejected_lower+=1;continue
            role='bridge' if b['order']==2 and t<.72 else 'terminal' if b['order']==4 or t>.80 else 'lateral'
            weight=b['vigor']*({2:.58,3:1.2,4:.90}[b['order']])*(.65+.35*min(1.,radius/.6))
            weight*=profile['bridge'] if role=='bridge' else 1+profile['tip_bias']*max(0.,t-.55)
            if b['order']==4 and lengths[b['id']]<h*.025:weight*=.3
            candidates.append({'id':b['id']+f':segment:{j}','branch':b,'t':t,'point':point,'tangent':tangent,
                'role':role,'weight':weight,'progress':starts[b['id']]+lengths[b['id']]*t})
    if len(candidates)<quota:raise ValueError('Segmentos elegibles insuficientes')
    count=max(2,min(5,round(2+3*m)+profile['mass_offset']))
    centers=[]
    if p['mass_variant'] in ('A','C'):
        pool=[c for c in candidates if c['t']>.65] if p['mass_variant']=='A' else candidates
        centers=[max(pool,key=lambda c:(c['weight'],c['id']))]
        while len(centers)<count:
            centers.append(max((c for c in pool if c not in centers),key=lambda c:min(length(sub(c['point'],q['point'])) for q in centers)*c['weight']**.35))
    else:
        ordered=sorted(candidates,key=lambda c:(c['progress'],c['id']))
        for i in range(count):
            bucket=ordered[len(ordered)*i//count:len(ordered)*(i+1)//count]
            total=sum(c['weight'] for c in bucket);mean=[sum(c['point'][k]*c['weight'] for c in bucket)/total for k in range(3)]
            centers.append(min(bucket,key=lambda c:(length(sub(c['point'],mean)),c['id'])))
    centers=sorted(centers,key=lambda c:(c['progress'],c['id']))
    side,up=frame(horizontal)
    def separation(c,center):
        q=sub(c['point'],center['point']);s=h*profile['spread']
        return math.sqrt((dot(q,horizontal)/(s*1.2))**2+(dot(q,side)/s)**2+(dot(q,up)/(s*.85))**2)
    bins={i:[] for i in range(count)}
    for c in candidates:bins[min(bins,key=lambda i:separation(c,centers[i]))].append(c)
    weights={str(i):sum(c['weight'] for c in bins[i]) for i in bins if bins[i]}
    quotas=allocate(quota,weights);groups=[];cards=[];used=set();axis_counts={};masses=[]
    geometry=prepared or [template_geometry(t) for t in templates]
    for mass_index,center in enumerate(centers):
        n=quotas.get(str(mass_index),0)
        if not n:continue
        pool=bins[mass_index];taken=[]
        for local in range(n):
            options=[c for c in pool if c['id'] not in used and axis_counts.get(c['branch']['id'],0)<12]
            if not options:raise ValueError('Masa sin segmentos suficientes dentro del cupo')
            def score(c):
                distance=separation(c,center)
                # C conserva huecos explícitos entre las zonas de influencia;
                # B distribuye puentes por una envolvente más amplia.
                closeness=math.exp(-distance*distance*(1.5 if p['mass_variant']=='C' else .65))
                spacing=min((length(sub(c['point'],q['point'])) for q in taken),default=h*.12)
                spread_factor=(.25+1.4*min(1.,spacing/(h*.08))) if p['mass_variant']=='B' else (1+.35*min(1.,spacing/(h*.05)))
                return closeness*(.5+.5*c['weight'])*spread_factor
            c=max(options,key=lambda c:(score(c),c['id']));used.add(c['id']);taken.append(c);b=c['branch'];axis_counts[b['id']]=axis_counts.get(b['id'],0)+1
            i=len(groups);identity=f'{bid}:of2:group:{i:03d}';tangent=c['tangent'];normal,vertical=frame(tangent)
            outward=unit((c['point'][0],c['point'][1],0))
            radial=sub(add((0,0,1),mul(outward,.35)),mul(tangent,dot(add((0,0,1),mul(outward,.35)),tangent)))
            if length(radial)<1e-8:radial=normal
            radial=unit(add(unit(radial),mul(normal,(rnd(c['id'],'side')-.5)*.4)))
            anchor=surface_point(b,c['t'],radial)
            x=unit(add(mul(horizontal,.65),add(mul(tangent,.25),mul(outward,.10))));y=unit(cross((0,0,1),x));z=unit(cross(x,y))
            # Mismo orden de tamaños/plantillas en las tres variantes.
            template=derive_seed(p['paint_seed'],identity)%len(geometry);g=geometry[template]
            span=h*p['span_over_height']*(.88+.24*rnd(identity,'size'))*(.82+.28*m)
            size=[span*g['aspect'][0]*1.12,span*g['aspect'][1]*1.32,span*g['aspect'][2]*.55]
            basis=[x,y,z];origin=sub(anchor,[sum(g['root_normalized'][a]*size[a]*basis[a][k] for a in range(3)) for k in range(3)])
            group={'id':identity,'parent_branch_id':b['id'],'parent_t':c['t'],'center_m':origin,'axes':basis,'size_m':size,
                'root_normalized':g['root_normalized'],'anchor_m':anchor,'template_index':template,'role':c['role'],
                'mass_id':f'mass:{mass_index}','candidate_id':c['id']}
            pieces=rooted_panels(group,template)
            if any(v[2]<0 for p2 in pieces for v in p2['vertices']):raise ValueError('Follaje bajo suelo')
            groups.append(group);cards.extend(pieces)
        masses.append({'id':f'mass:{mass_index}','type':'bridge' if mass_index==0 and p['mass_variant']=='B' else center['role'],
            'center_m':center['point'],'group_count':n,'candidate_count':len(pool),'progress_m':center['progress']})
    if len(groups)!=quota:raise ValueError('Cupo OF2 incompleto')
    return {'version':p['version'],'spec':p,'ledger':ledger,'wood':selected,'groups':groups,'foliage':cards,'axis_quotas':axis_counts,
        'masses':masses,'mass_links':[[a['id'],b['id']] for a,b in zip(masses,masses[1:])],
        'diagnostics':{'candidate_count':len(candidates),'rejected_lower_segments':rejected_lower,'lower_height_limit_m':floor,
                       'profile':profile,'maturity':m,'materialized_scope':'same mature branch; no full-tree foliage'}}
