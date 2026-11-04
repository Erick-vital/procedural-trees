"""O6 experimental: rama central ascendente añadida a O5 sin alterar su madera."""
import copy
import math
from .branch_structure import add,sub,mul,dot,length
from .oak_growth import sample,unit
from .oak_growth_mesh import tube
from .oak_growth_joins import fit_root_rings
from .seeds import derive_seed
VERSION='oak-growth-central-0.1.0'


def add_central_branch(structure):
    if structure.get('version')!='oak-growth-0.5.0' or structure['preset']['stage']!='maduro':
        raise ValueError('La rama central solo admite la estructura O5 madura')
    result=copy.deepcopy(structure);h=structure['preset']['height_m'];seed=structure['seed']
    trunk=next(b for b in result['branches'] if b['id']=='trunk')
    root,_=sample(trunk['points'],.88)
    # Elegir el vacío central superior con una búsqueda angular finita común.
    wood=[sample(b['points'],t)[0] for b in structure['branches'] if b['order'] in (1,2) for t in (.4,.65,.9)]
    phase=derive_seed(seed,VERSION+':phase')/2147483647*2*math.pi
    options=[]
    for i in range(16):
        yaw=phase+i*math.pi/8;target=(h*.12*math.cos(yaw),h*.12*math.sin(yaw),h*.78)
        score=min(math.dist(target,q) for q in wood)
        options.append((score,-i,yaw))
    yaw=max(options)[2];forward=(math.cos(yaw),math.sin(yaw),0);side=(-forward[1],forward[0],0)
    tip=add(mul(forward,h*.14),(0,0,h*.80))
    def curve(start,end,count,sideways):
        return [add(add(mul(start,1-u),mul(end,u)),mul(side,sideways*math.sin(math.pi*u))) for u in (i/(count-1) for i in range(count))]
    def branch(identity,parent,t,end,count,sides,radius,tip_radius,order,sideways):
        start,_=sample(parent['points'],t)
        return {'id':identity,'parent_id':parent['id'],'order':order,'parent_t':t,
                'points':curve(start,end,count,sideways),'radii':[radius*(1-i/(count-1))+tip_radius*i/(count-1) for i in range(count)],
                'sides':sides,'vigor':parent['vigor']*.90,'phase':yaw,'role':'central_crown_support',
                'join_radius_scale':1.,'space_availability':1.}
    primary=branch('central',trunk,.88,tip,7,5,h*.015,h*.0048,1,h*.025)
    added=[primary]
    for j,sign in enumerate((-1,1)):
        end=add(add(tip,mul(side,sign*h*.12)),add(mul(forward,h*(.035 if j else -.025)),(0,0,h*(.045 if j else .015))))
        sec=branch(f'central/{j}',primary,.60+.18*j,end,4,4,h*.0045,h*.0015,2,sign*h*.015);added.append(sec)
        for k in range(2):
            end3=add(end,add(mul(forward,h*(.07 if k else -.055)),(0,0,h*(.055 if k else .025))))
            added.append(branch(f'central/{j}/{k}',sec,.57+.25*k,end3,3,3,h*.0017,h*.0005,3,sign*h*.007))
    # Dos brotes adicionales, predominantemente verticales, desde primarias
    # interiores cercanas a la copa. Elegir espacio entre ejes, sin sectores fijos.
    used_parents=set();upright_records=[]
    for shoot in range(2):
        candidates=[]
        for parent_branch in structure['branches']:
            if parent_branch['order']!=1 or parent_branch['id'] in used_parents:continue
            for t in (.42,.58,.72):
                start,_=sample(parent_branch['points'],t)
                if not h*.42 <= start[2] <= h*.62:continue
                end=(start[0]*.82+side[0]*h*.025*(-1 if shoot else 1),
                     start[1]*.82+side[1]*h*.025*(-1 if shoot else 1),h*(.79+.025*shoot))
                clearance=min(math.dist(end,q) for q in wood)
                separation=min(math.dist(end,b['points'][-1]) for b in added)
                candidates.append((min(clearance,separation),parent_branch['id'],t,end,parent_branch))
        if not candidates:raise ValueError('No hay primaria apta para brotes de copa verticales')
        _,_,t,end,parent_branch=max(candidates,key=lambda q:q[:3]);used_parents.add(parent_branch['id'])
        identity=f'upright:{shoot}'
        axis=branch(identity,parent_branch,t,end,7,4,h*.0065,h*.0022,2,h*.012*(-1 if shoot else 1));added.append(axis)
        upright_records.append({'id':identity,'parent_id':parent_branch['id'],'parent_t':t})
        for j,sign in enumerate((-1,1)):
            end2=add(end,add(mul(side,sign*h*.075),add(mul(forward,h*.035),(0,0,h*(.045 if j else .015)))))
            secondary=branch(identity+f'/{j}',axis,.63+.17*j,end2,4,4,h*.0026,h*.001,3,sign*h*.008);added.append(secondary)
            for k in range(2):
                end3=add(end2,add(mul(forward,h*(.045 if k else -.04)),(0,0,h*(.045 if k else .02))))
                added.append(branch(identity+f'/{j}/{k}',secondary,.60+.22*k,end3,3,3,h*.0012,h*.00045,4,sign*h*.006))
    # Solo se ajusta lo nuevo: el tubo padre y todos los ejes O5 quedan exactos.
    parents=[]
    for original in result['branches']:
        if original['id'] not in {'trunk',*used_parents}:continue
        parent=copy.deepcopy(original);parent['parent_id']=None;parents.append(parent)
    fit_root_rings([*parents,*added])
    tris=lambda bs:sum(sum(len(face)-2 for face in tube(b)['polygons']) for b in bs)
    extra=tris(added)
    if extra>600 or tris(result['branches'])+extra+1296>6999:
        raise ValueError('La rama central excede su reserva de madera/follaje')
    result['branches'].extend(added)
    result.update(version=VERSION,central_extension={'source_version':structure['version'],'branch_ids':[b['id'] for b in added],
                  'added_wood_triangles':extra,'root_t':.88,'target_yaw_rad':yaw,'angular_candidates':16,'upright_shoots':upright_records,'structural_axes':3})
    return result
