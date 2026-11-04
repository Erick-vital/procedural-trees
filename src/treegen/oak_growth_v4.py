"""O4: desarrollo periférico, núcleo despejado y hábitos por brazo."""
import math
from .seeds import derive_seed
from .branch_structure import add,sub,mul,dot,length
from .oak_growth_contract import validate_seed
from .oak_volume_contract import VERSION,validate_preset,EXTRA_TRIANGLES,WOOD_LIMIT
from .oak_crown_balance import CrownField
RANDOM_VERSION="oak-growth-0.1.0"


from .oak_growth import unit,cross,frame,sample,assign_radii


def generate(preset,seed,*,max_order=4,spatial=True):
    p=validate_preset(preset);validate_seed(seed)
    if type(max_order) is not int or not 1<=max_order<=4 or type(spatial) is not bool:raise ValueError('Ablación inválida')
    # La topología base se toma de O2: B/C no consumen triángulos extra.
    from .oak_growth_v2 import generate as previous
    reference=previous({**p,'version':'oak-growth-0.2.0'},seed,max_order=max_order,spatial=spatial)
    child_counts={}
    for b in reference['branches']:
        child_counts[b['parent_id']]=child_counts.get(b['parent_id'],0)+1
    base_triangles=sum((len(b['points'])-1)*2*b['sides']+b['sides']-2+(b['sides']-2 if b['order']==0 else 0) for b in reference['branches'])
    h=p['height_m'];m=p['maturity'];old=max(0.,(m-.65)/.35);apical=1-.88*m;branches=[];occupied={};cell=h*.13
    def rnd(identity,stream,lo=0.,hi=1.):return lo+(hi-lo)*derive_seed(seed,f'{RANDOM_VERSION}:{identity}:{stream}')/2147483647
    phase=rnd('tree','regional-phase',-math.pi,math.pi)
    field=CrownField(p,phase)
    def habit(identity):
        # Cada brazo mantiene un hábito; hijos con variación menor correlada.
        bough=identity.split('/')[0];v=rnd(bough,'habit')
        return 'lateral' if v<.28 else 'weighted' if v<.53 else 'seeking' if v<.80 else 'twisting'
    def influences(identity,order):
        kind=habit(identity)
        light,weight={'lateral':(.20,1.0),'weighted':(.05,1.7),'seeking':(1.45,.45),'twisting':(.55,1.05)}[kind]
        light=(1-m)+m*light
        if order==1:light*=.10
        return kind,light*rnd(identity,'light-response',.75,1.25),(1-m)+m*weight
    def regional(yaw,z):return max(.55,min(1.2,.9+.16*math.sin(yaw+phase)+.12*math.cos(2*yaw-.7*phase)+.07*z/h))
    def key(v):return tuple(math.floor(x/cell) for x in v)
    def freedom(point,parent,root):
        if not spatial or p['competition']==0:return 1.
        base=key(point);crowd=0.
        for x in range(base[0]-1,base[0]+2):
            for y in range(base[1]-1,base[1]+2):
                for z in range(base[2]-1,base[2]+2):
                    for q,identity in occupied.get((x,y,z),()):
                        if identity==parent and length(sub(q,root))<h*.14:continue
                        d=length(sub(point,q))/cell
                        if d<1.3:crowd+=((1.3-d)/1.3)**2
        return 1/(1+crowd*.65)
    def register(branch):
        branches.append(branch)
        for a,b in zip(branch['points'],branch['points'][1:]):
            for t in (0,.5,1):
                q=add(a,mul(sub(b,a),t));occupied.setdefault(key(q),[]).append((q,branch['id']))
    trunk_h=h*(.88-.55*m)*(1-.12*old);lean=rnd('trunk','lean',0,2*math.pi)
    trunk_points=[(h*.024*math.sin(t*1.4)*math.cos(lean),h*.018*t*t*math.sin(lean),trunk_h*t) for t in [i/12 for i in range(13)]]
    trunk={'id':'trunk','parent_id':None,'order':0,'parent_t':None,'points':trunk_points,'vigor':p['vigor'],'phase':phase,'role':'axis','sides':8,'bough_path_to_root':0.}
    register(trunk)
    def grow(identity,parent,order,t,size,direction,vigor,role):
        root,tangent=sample(parent['points'],t);rule=p['orders'][order-1]
        path_to_root=0. if order==1 else parent['bough_path_to_root']+sum(length(sub(b,a)) for a,b in zip(parent['points'],parent['points'][1:]))*t
        requested_size=size;size=field.axis_budget(size,root,path_to_root,order)
        kind,light_response,weight_response=influences(identity,order)
        direction=unit(direction);heading=unit(add(mul(direction,.87),mul(tangent,.13)))
        yaw=math.atan2(direction[1],direction[0]);incl=math.asin(direction[2])
        curl=p['curvature']*rule['curvature_scale']*(.65+.35*m)*(1+.35*old if order==1 else 1);wave=parent['phase']*.5+rnd(identity,'phase',-2,2)
        bend=rnd(identity,'bend',-.7,.7);twist=rnd(identity,'twist',-.6,.6)
        if kind=='twisting':curl*=1+.25*m
        points=[root];frees=[]
        for i in range(1,rule['points']):
            u=i/(rule['points']-1)
            ease=min(1.,u*1.8)**2
            desired_yaw=yaw+ease*curl*2.2*(math.sin(u*math.pi*2+wave)-math.sin(wave))+twist*u*u*.25
            # Los brazos sostienen peso; la búsqueda ascendente corresponde a sus hijos.
            light_weight=light_response*(1.15 if order==2 else .70 if order>2 else 1.)
            weight=(.45+.55*u) if order==1 else .22*math.sin(math.pi*u)
            lift=p['light_tropism']*(.4+vigor)*u*light_weight-p['gravity']*m*weight*(1-abs(direction[2]))*(1+old)*weight_response
            desired_incl=max(-.36,min(1.4,incl+lift+ease*curl*bend*(math.sin(u*math.pi*2+wave)-math.sin(wave))))
            # La zona alta pierde dominancia: desviar hacia volumen lateral,
            # en lugar de alargar todos los órdenes verticalmente sin límite.
            ceiling=max(0.,min(1.,(h*(.92+.16*apical)-points[-1][2])/(h*.18)))
            if desired_incl>0:desired_incl*=ceiling
            wanted=(math.cos(desired_yaw)*math.cos(desired_incl),math.sin(desired_yaw)*math.cos(desired_incl),math.sin(desired_incl))
            wanted=unit(add(mul(heading,.58),mul(wanted,.42)))
            n,up=frame(wanted);step=size/(rule['points']-1)*field.growth_factor(points[-1])
            candidates=[wanted]
            for turn,lift2 in ((.20,.08),(-.20,.08),(.08,.20),(-.08,-.12),(.30,.35),(-.30,.35)):
                candidates.append(unit(add(wanted,add(mul(n,turn),mul(up,lift2)))))
            scores=[]
            for index,d in enumerate(candidates):
                q=add(points[-1],mul(d,step));free=freedom(q,parent['id'],root)
                # Suavidad direccional y espacio pesan más que el azar.
                envelope=max(0,math.hypot(q[0],q[1])/(h*(.72+.18*m)*p['crown_spread'])-1)**2
                return_to_core=max(0.,(math.hypot(points[-1][0],points[-1][1])-math.hypot(q[0],q[1]))/h)
                score=p['competition']*free+.32*dot(d,wanted)-envelope*.8-field.penalty(q)-index*.001-(12*return_to_core**2 if order>1 else 0)
                scores.append((score,d,free))
            _,heading,free=max(scores,key=lambda row:row[0]);points.append(add(points[-1],mul(heading,step)));frees.append(free)
        branch={'id':identity,'parent_id':parent['id'],'order':order,'parent_t':t,'points':points,'vigor':vigor,
                'phase':wave,'growth_habit':kind,'light_response':light_response,'weight_response':weight_response,'role':role,'sides':rule['sides'],'space_availability':sum(frees)/len(frees),'bough_path_to_root':path_to_root,
                'requested_length_m':requested_size,'budgeted_length_m':size}
        register(branch);return branch
    count=min(p['orders'][0]['max_children'],5+round(3*m)+(rnd('tree','primary-count')>1-p['orders'][0]['branching_probability']))
    weights=[rnd('primary:'+str(i),'height-step',.65,1.45) for i in range(count)]
    low=(.42-.28*m+(p['orders'][0]['attachment_min']-.3)*.18)/(.88-.55*m);high=.94
    factors=[];acc=0.
    for w in weights:
        factors.append(low+(high-low)*acc/max(sum(weights[:-1]),1e-8));acc+=w
    primary=[]
    for i,t in enumerate(factors):
        identity=f'p:{i}';rank=i/max(1,count-1);root,tangent=sample(trunk_points,t)
        if rank<.34:incl=rnd(identity,'incl',-.10,.28)
        elif rank<.67:incl=rnd(identity,'incl',.23,.65)
        else:incl=rnd(identity,'incl',.72,1.12)
        incl-=old*(.10+.45*rank)
        incl=max(-.3,min(1.4,math.pi/2-(math.pi/2-incl)*p['orders'][0]['fork_angle_deg']/60))
        young_dominance=(1-m)**2
        incl=incl*(1-young_dominance)+.94*young_dominance*(.45+.55*rank)
        candidates=[]
        for j in range(10):
            yaw=rnd(identity,'yaw:'+str(j),-math.pi,math.pi)
            target=add(root,(h*.46*math.cos(yaw),h*.46*math.sin(yaw),h*.22))
            crowding=sum(math.exp(3*(math.cos(yaw-math.atan2(b['points'][-1][1],b['points'][-1][0]))-1)) for b in primary)
            score=.20*regional(yaw,root[2])-.34*crowding+.15*freedom(target,'trunk',root)
            candidates.append((score,yaw))
        yaw=max(candidates)[1];vig=p['vigor']*regional(yaw,root[2])*rnd(identity,'vigor',.88,1.08)
        size=h*p['orders'][0]['length_ratio']*(.65+.35*m)*p['crown_spread']*(.78+.22*vig)*(1-.10*rank)*(1+old*(.35-.20*rank))*(.62+.38*m+.25*rank*(1-m))*rnd(identity,'length',.87,1.12)
        size*=1+old*(.20*math.sin(yaw+phase)+.08*math.cos(2*yaw-phase))
        direction=(math.cos(yaw)*math.cos(incl),math.sin(yaw)*math.cos(incl),math.sin(incl))
        primary.append(grow(identity,trunk,1,t,size,direction,vig,'scaffold'))
    for order in range(2,max_order+1):
        rule=p['orders'][order-1]
        for parent in [b for b in list(branches) if b['order']==order-1]:
            identity=parent['id'];avail=parent['space_availability'];v=parent['vigor']
            n=rule['max_children']
            n=child_counts.get(identity,0)
            length_parent=sum(length(sub(b,a)) for a,b in zip(parent['points'],parent['points'][1:]))
            # Une continuation y laterales: raíces escalonadas, nunca una estrella.
            # Laterales repartidas a lo largo del padre; no concentrarlas en su raíz.
            start=max(rule['attachment_min'],.42 if order==2 else .44)
            ts=[rnd(identity,f'attach:{order}:{j}',start+( .70-start)*j/max(1,n-2),start+.08+(.67-start)*j/max(1,n-2)) for j in range(max(0,n-1))]+[rnd(identity,f'continuation:{order}',.86,.93)]
            for j,t in enumerate(sorted(ts)):
                child=identity+f'/{j}';root,tangent=sample(parent['points'],t);continuation=j==n-1
                nvec,up=frame(tangent)
                angle=math.radians(rule['fork_angle_deg'])*rnd(child,'fork',.65,1.25)*(.55 if continuation else 1)*(.6+.4*m)
                size=length_parent*rule['length_ratio']*rnd(child,'length',.73,1.18)*(1.05 if continuation else .8)*(.72+.28*avail)*(.75+.25*m)
                size*=.78 if continuation else 1.10
                _,child_light,_=influences(child,order)
                options=[]
                for k in range(6):
                    az=parent['phase']+j*2.4+rnd(child,'fork-plane:'+str(k),-math.pi,math.pi)
                    radial=add(mul(up,math.cos(az)),mul(nvec,math.sin(az)))
                    d=unit(add(mul(tangent,math.cos(angle)),mul(radial,math.sin(angle))))
                    d=unit(add(d,(0,0,p['light_tropism']*child_light*(1.10 if order==2 else .60))))
                    future=add(root,mul(d,size*.7))
                    outward=unit((root[0],root[1],h*.02))
                    # Exposición y espacio eligen el plano de bifurcación; el
                    # crecimiento conserva correlación con el eje de origen.
                    return_to_core=max(0.,(math.hypot(root[0],root[1])-math.hypot(future[0],future[1]))/h)
                    score=p['competition']*freedom(future,parent['id'],root)+.14*dot(d,outward)+.08*dot(d,tangent)-field.penalty(future)-12*return_to_core**2
                    options.append((score,d))
                direction=max(options,key=lambda row:row[0])[1]
                yaw=math.atan2(direction[1],direction[0]);vig=max(.55,min(1.3,v*.75+regional(yaw,root[2])*.25))
                grow(child,parent,order,t,size,direction,vig,'continuation' if continuation else 'lateral')
    # Redistribuir el mismo cupo: ejes secundarios ramificados sobre brazos
    # vacíos antes de añadir ramillas a secundarias ya desarrolladas.
    extra_budget=min(660,EXTRA_TRIANGLES,WOOD_LIMIT-base_triangles);spent=0
    if max_order==4:
        def cost(order):
            r=p['orders'][order-1]
            return (r['points']-1)*2*r['sides']+r['sides']-2
        # Seis unidades de 100 tris y, si cabe, una de 60: no sumar otro cupo.
        primary_candidates=[]
        for parent in primary:
            for j in range(3):
                t=rnd(parent['id'],f'infill-slot:{j}',.48+j*.09,.56+j*.09)
                root,axis=sample(parent['points'],t)
                children=[b for b in branches if b['parent_id']==parent['id']]
                spacing=min(abs(t-b['parent_t']) for b in children) if children else 1.
                priority=spacing+.18*freedom(root,parent['id'],root)+.04*rnd(parent['id'],f'infill-priority:{j}')
                primary_candidates.append((priority,parent,t))
        used=set()
        for _,parent,t in sorted(primary_candidates,key=lambda row:row[0],reverse=True):
            cluster_cost=sum(cost(o) for o in (2,3,4))
            if len(used)>=6 or spent+cluster_cost>extra_budget:break
            if parent['id'] in used:continue
            identity=parent['id']+'/infill';root,axis=sample(parent['points'],t);side,up=frame(axis)
            options=[]
            for j in range(8):
                az=rnd(identity,f'plane:{j}',-math.pi,math.pi)
                radial=add(mul(side,math.cos(az)),mul(up,math.sin(az)))
                direction=unit(add(mul(axis,.70),mul(radial,.72)))
                future=add(root,mul(direction,h*.18))
                outward=unit((root[0],root[1],0))
                score=.30*dot(direction,outward)+p['competition']*freedom(future,parent['id'],root)-field.penalty(future)
                options.append((score,direction))
            direction=max(options,key=lambda row:row[0])[1]
            extent=sum(length(sub(b,a)) for a,b in zip(parent['points'],parent['points'][1:]))
            twig=grow(identity,parent,2,t,extent*rnd(identity,'size',.36,.48),direction,parent['vigor']*.92,'infill')
            _,axis=sample(twig['points'],.68);side,up=frame(axis)
            d=unit(add(axis,add(mul(side,.64),mul(up,.20))))
            tip=grow(identity+'/0',twig,3,.68,extent*.20,d,twig['vigor'],'infill')
            _,axis=sample(tip['points'],.74);side,up=frame(axis)
            grow(identity+'/0/0',tip,4,.74,extent*.11,unit(add(axis,mul(side,-.55))),tip['vigor'],'infill')
            spent+=cluster_cost;used.add(parent['id'])
        candidates=[]
        for parent in [b for b in branches if b['order']==2 and '/infill' not in b['id']]:
            t=rnd(parent['id'],'infill-outer-slot',.56,.76);root,_=sample(parent['points'],t)
            priority=freedom(root,parent['id'],root)+.20*math.hypot(root[0],root[1])/h
            candidates.append((priority,parent,t))
        for _,parent,t in sorted(candidates,key=lambda row:row[0],reverse=True):
            cluster_cost=cost(3)+2*cost(4)
            if spent+cluster_cost>extra_budget:break
            identity=parent['id']+'/infill';root,axis=sample(parent['points'],t);side,up=frame(axis)
            direction=unit(add(axis,add(mul(side,.72),mul(up,.25))))
            extent=sum(length(sub(b,a)) for a,b in zip(parent['points'],parent['points'][1:]))
            twig=grow(identity,parent,3,t,extent*.36,direction,parent['vigor']*.85,'infill')
            for j,t2 in enumerate((.54,.88)):
                _,axis=sample(twig['points'],t2);side,up=frame(axis)
                grow(identity+f'/{j}',twig,4,t2,extent*.14,unit(add(axis,mul(side,.6 if j==0 else -.6))),twig['vigor'],'infill')
            spent+=cluster_cost
    # Escala uniforme: mantiene proporciones 3D, a diferencia de Q2 solo Z.
    top=max(v[2] for b in branches for v in b['points']);scale=h/top
    for b in branches:b['points']=[mul(v,scale) for v in b['points']]
    assign_radii(branches,p)
    from .oak_growth_joins import fit_root_rings
    fit_root_rings(branches)
    return {'version':VERSION,'seed':seed,'preset':p,'max_order':max_order,'spatial':spatial,
            'branching_budget':{'base_triangles':base_triangles,'extra_triangles':spent,'extra_limit':EXTRA_TRIANGLES,'wood_limit':WOOD_LIMIT},
            'apical_dominance':apical,'uniform_scale':scale,'branches':branches,
            'balance':{'random_namespace':RANDOM_VERSION,'path_budget_m':field.path_budget,'radial_reference_m':field.radius}}
