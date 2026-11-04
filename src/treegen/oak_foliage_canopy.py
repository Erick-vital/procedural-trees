"""OF3: cadenas B ramificadas, con cupos por bifurcación y masas variadas."""
import math
from collections import Counter
from .branch_structure import add,sub,mul,length,dot
from .oak_growth import sample,frame,unit,cross
from .seeds import derive_seed
from .oak_foliage_canopy_contract import validate_canopy
from .oak_foliage_layout import plan,allocate,surface_point
from .oak_foliage_cards import template_geometry,rooted_panels


def minimum_radius(cards):
    """Distancia al cilindro central sobre toda lámina, no solo vértices."""
    best=float('inf')
    for card in cards:
        vs=card['vertices']
        for face in card['polygons']:
            poly=[vs[i] for i in face];signs=[]
            for a,b in zip(poly,poly[1:]+poly[:1]):
                dx,dy=b[0]-a[0],b[1]-a[1];den=dx*dx+dy*dy
                t=max(0,min(1,-(a[0]*dx+a[1]*dy)/den)) if den else 0
                best=min(best,math.hypot(a[0]+t*dx,a[1]+t*dy))
                signs.append(dx*(-a[1])-dy*(-a[0]))
            # Proyección convexa con área no nula: comprobar interior.
            area=sum(a[0]*b[1]-b[0]*a[1] for a,b in zip(poly,poly[1:]+poly[:1]))
            if abs(area)>1e-12 and (min(signs)>=0 or max(signs)<=0):return 0.
    return best


def build(structure,spec,templates,*,prepared=None):
    p=validate_canopy(spec);old={**p,'version':'oak-foliage-sample-0.1.0','branch_id':'p:0'}
    ledger=plan(structure,old);h=structure['preset']['height_m'];core=h*p['core_radius_over_height']
    geometry=prepared or [template_geometry(t) for t in templates]
    branches=structure['branches'];index={b['id']:b for b in branches}
    lengths={b['id']:sum(length(sub(c,a)) for a,c in zip(b['points'],b['points'][1:])) for b in branches}
    def rnd(identity,stream):return derive_seed(p['layout_seed'],f'of3:{identity}:{stream}')/2147483647
    groups=[];cards=[];masses=[];axis_counts=Counter();fork_quotas={};diagnostics={};links=[]
    for bid,quota in ledger['primary_quotas'].items():
        if not quota:continue
        primary=index[bid];floor=sample(primary['points'],.65)[0][2]-.015*h
        candidates=[];rejected_lower=0
        for b in branches:
            if not b['id'].startswith(bid+'/') or b['order']<2:continue
            fork='/'.join(b['id'].split('/')[:2])
            for j in range(32):
                low=.32 if b['order']==2 else .22;t=low+(.96-low)*(j+.5)/32
                point,tangent=sample(b['points'],t);radius=math.hypot(*point[:2])
                if radius<core+h*.025:continue
                if point[2]<floor and tangent[2]<.12:rejected_lower+=1;continue
                exposure=.55+.45*min(1.,radius/(h*.62))
                weight=b['vigor']*exposure*{2:.8,3:1.15,4:.65}[b['order']]
                candidates.append({'id':b['id']+f':{j:02d}','branch':b,'fork':fork,'t':t,'point':point,'tangent':tangent,
                    'weight':weight,'exposure':exposure})
        forks=sorted({c['fork'] for c in candidates})
        # Longitud expuesta sublineal: evita que el eje más largo monopolice
        # el follaje y conserva diferencias de vigor y exposición reales.
        weights={f:sum(lengths[b['id']]*b['vigor']*sum(c['exposure'] for c in candidates if c['branch']['id']==b['id'])/32
                       for b in branches if b['id']==f or b['id'].startswith(f+'/'))**.6 for f in forks}
        quotas=allocate(quota,weights);fork_quotas.update(quotas)
        used=set();rejected_core=0;arm_masses=[]
        for fork in forks:
            pool=[c for c in candidates if c['fork']==fork];n=quotas[fork]
            # Masas ligadas a bifurcaciones, no una columna única por primaria.
            count=min(3,max(1,round(n/9)));ordered=sorted(pool,key=lambda c:(c['point'][2]+.35*c['t']*h,c['id']))
            centers=[]
            for k in range(count):
                bucket=ordered[len(ordered)*k//count:len(ordered)*(k+1)//count]
                mean=[sum(c['point'][a]*c['weight'] for c in bucket)/sum(c['weight'] for c in bucket) for a in range(3)]
                centers.append(min(bucket,key=lambda c:(length(sub(c['point'],mean)),c['id'])))
            mass_quotas=allocate(n,{str(k):1.+.3*rnd(fork+str(k),'quota') for k in range(count)})
            for k,center in enumerate(centers):
                mid=f'{fork}:mass:{k}';shape=('broad','elongated','bridge')[derive_seed(p['layout_seed'],mid)%3]
                dims={'broad':(1.03,1.65,.85),'elongated':(1.62,1.00,.68),'bridge':(.80,.94,.68)}[shape]
                # Orientación coherente por masa, diversificada entre masas.
                turn=(rnd(mid,'yaw')-.5)*1.8;pitch=(rnd(mid,'pitch')-.5)*.75
                taken=[]
                for local in range(mass_quotas[str(k)]):
                    options=[c for c in pool if c['id'] not in used and axis_counts[c['branch']['id']]<12]
                    def score(c):
                        distance=length(sub(c['point'],center['point']))/(h*.17)
                        spacing=min((length(sub(c['point'],q['point'])) for q in taken),default=h*.12)
                        return math.exp(-distance*distance*.65)*c['weight']*(.25+1.4*min(1.,spacing/(h*.075)))
                    placed=None
                    for c in sorted(options,key=lambda c:(-score(c),c['id'])):
                        b=c['branch'];identity=f'{mid}:group:{local:02d}';tangent=c['tangent'];normal,up=frame(tangent)
                        # Lados alternos alrededor del eje: arriba, lateral y abajo.
                        roll=2*math.pi*(local*.381966+rnd(mid,'roll'))
                        radial=unit(add(mul(normal,math.cos(roll)),mul(up,math.sin(roll))))
                        anchor=surface_point(b,c['t'],radial)
                        heading=math.atan2(tangent[1],tangent[0])+turn+(rnd(identity,'yaw')-.5)*.55
                        tilt=.18+pitch+(rnd(identity,'tilt')-.5)*.45
                        template=derive_seed(p['paint_seed'],identity)%len(geometry)
                        span=h*p['span_over_height']*(.82+.36*rnd(mid,'size'))*(.9+.2*rnd(identity,'size'))
                        # Pruebas de orientación acotadas antes de descartar el
                        # segmento; nunca desplazar el contacto ni invadir núcleo.
                        for turn_index in range(6):
                            angle=heading+(0,1,-1,2,-2,3)[turn_index]*math.pi/3
                            x=(math.cos(angle)*math.cos(tilt),math.sin(angle)*math.cos(tilt),math.sin(tilt))
                            y,z=frame(x);spin=(rnd(mid,'spin')-.5)*.9
                            y=add(mul(y,math.cos(spin)),mul(z,math.sin(spin)));z=unit(cross(x,y));basis=[x,y,z]
                            g=geometry[template];size=[span*g['aspect'][a]*dims[a] for a in range(3)]
                            origin=sub(anchor,[sum(g['root_normalized'][a]*size[a]*basis[a][v] for a in range(3)) for v in range(3)])
                            group={'id':identity,'parent_branch_id':b['id'],'parent_t':c['t'],'center_m':origin,'axes':basis,'size_m':size,
                                'root_normalized':g['root_normalized'],'anchor_m':anchor,'template_index':template,'mass_id':mid,
                                'role':'bridge' if shape=='bridge' else 'lateral' if local%3 else 'terminal','shape':shape,'candidate_id':c['id'],
                                'orientation_attempt':turn_index}
                            pieces=rooted_panels(group,template)
                            if minimum_radius(pieces)<core or min(v[2] for pc in pieces for v in pc['vertices'])<0:
                                rejected_core+=1;continue
                            placed=(c,group,pieces);break
                        if placed is not None:break
                    if placed is None:raise ValueError(f'Cupo periférico imposible: {mid}; no invadir núcleo ni añadir triángulos')
                    c,group,pieces=placed;groups.append(group);cards.extend(pieces);used.add(c['id']);taken.append(c);axis_counts[c['branch']['id']]+=1
                masses.append({'id':mid,'primary_id':bid,'fork_id':fork,'shape':shape,'group_count':len(taken),'center_m':center['point']})
                arm_masses.append(mid)
            links.extend([[f'{fork}:mass:{k}',f'{fork}:mass:{k+1}'] for k in range(count-1)])
        diagnostics[bid]={'candidate_count':len(candidates),'rejected_lower_segments':rejected_lower,'rejected_core_placements':rejected_core,
            'fork_weights':weights,'lower_height_limit_m':floor,'mass_ids':arm_masses}
    if len(groups)!=p['tree_groups']:raise ValueError('Cupo global incompleto')
    return {'version':p['version'],'spec':p,'ledger':ledger,'wood':branches,'groups':groups,'foliage':cards,
        'axis_quotas':dict(axis_counts),'fork_quotas':fork_quotas,'masses':masses,'mass_links':links,'diagnostics':diagnostics,
        'minimum_card_radius_m':minimum_radius(cards),'scope':'full mature pilot; no other ages or production recipe'}
