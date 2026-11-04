"""OF1: cupos por brazo y distribución sobre ejes finos reales de O5."""
import math
from .branch_structure import add,sub,mul,length,dot
from .oak_growth import sample,frame,unit,cross
from .oak_growth_mesh import tube
from .surface_evaluation import closest_point_on_triangle
from .seeds import derive_seed
from .oak_foliage_contract import validate_sample
from .oak_foliage_cards import template_geometry,rooted_panels


def allocate(total,weights):
    if not weights or min(weights.values())<=0:raise ValueError('Copa sin desarrollo elegible')
    raw={k:total*v/sum(weights.values()) for k,v in weights.items()};counts={k:math.floor(v) for k,v in raw.items()}
    for k in sorted(raw,key=lambda k:(-(raw[k]-counts[k]),k))[:total-sum(counts.values())]:counts[k]+=1
    return counts


def plan(structure,spec):
    p=validate_sample(spec);h=structure['preset']['height_m'];branches=structure['branches']
    primary=[b for b in branches if b['order']==1];weights={b['id']:0. for b in primary};eligible=[]
    for b in branches:
        if b['order']<2:continue
        span=sum(length(sub(c,a)) for a,c in zip(b['points'],b['points'][1:]))
        stations=(.60,.70,.80,.92) if b['order']==2 else (.35,.55,.75,.95)
        fraction=sum(math.hypot(*sample(b['points'],t)[0][:2])>=h*p['core_radius_over_height'] for t in stations)/4
        if not fraction:continue
        weight=span*b['vigor']*({2:.42,3:1.,4:.85}[b['order']])*fraction
        weights[b['id'].split('/')[0]]+=weight
        eligible.append((b,weight))
    # Si un brazo no tiene ejes elegibles, conserva cupo cero y se documenta.
    active={k:v for k,v in weights.items() if v>0};quotas=allocate(p['tree_groups'],active)
    full_wood=sum((len(b['points'])-1)*2*b['sides']+b['sides']-2+(b['sides']-2 if b['order']==0 else 0) for b in branches)
    if full_wood+6*p['tree_groups']>6999:raise ValueError('Presupuesto completo excedido')
    return {'total_groups':p['tree_groups'],'group_triangles':6,'foliage_triangles':6*p['tree_groups'],
        'tree_wood_triangles':full_wood,'tree_projected_triangles':full_wood+6*p['tree_groups'],
        'primary_weights':weights,'primary_quotas':{k:quotas.get(k,0) for k in weights},
        'eligible':[(b['id'],w) for b,w in eligible]}


def surface_point(branch,t,direction):
    center,_=sample(branch['points'],t);mesh=tube(branch)
    triangles=[(face[0],face[j],face[j+1]) for face in mesh['polygons'] for j in range(1,len(face)-1)]
    # Proyectar desde fuera en el lado elegido sobre triángulos reales.
    target=add(center,mul(direction,max(branch['radii'])*2))
    return min((closest_point_on_triangle(target,*(mesh['vertices'][i] for i in tri)) for tri in triangles),key=lambda q:length(sub(q,target)))


def build(structure,spec,templates,*,prepared=None):
    p=validate_sample(spec);ledger=plan(structure,p);branch_id=p['branch_id'];h=structure['preset']['height_m']
    if not ledger['primary_quotas'].get(branch_id):raise ValueError('La rama seleccionada no tiene cupo')
    selected=[b for b in structure['branches'] if b['id']==branch_id or b['id'].startswith(branch_id+'/')]
    eligible=dict(ledger['eligible']);axes=[b for b in selected if b['id'] in eligible]
    quota=ledger['primary_quotas'][branch_id];axis_quotas=allocate(quota,{b['id']:eligible[b['id']] for b in axes})
    geometry=prepared or [template_geometry(t) for t in templates];groups=[];cards=[];candidates=[]
    def rnd(identity,stream):return derive_seed(p['layout_seed'],f'of1:{identity}:{stream}')/2147483647
    # Cupos por eje: varias inserciones longitudinales, sin llenar solo puntas.
    for b in axes:
        count=axis_quotas[b['id']]
        if count>16:raise ValueError('Demasiados grupos en un solo eje')
        options=[]
        for j in range(32):
            start=.56 if b['order']==2 else .24
            t=start+(.96-start)*(j+.5)/32;point,tangent=sample(b['points'],t)
            if math.hypot(*point[:2])<h*p['core_radius_over_height']:continue
            options.append((t,point,tangent))
        if len(options)<count:raise ValueError('Eje sin candidatos exteriores suficientes')
        chosen=[]
        for i in range(count):
            # Mayor separación en recorrido primero; desempate estable por eje.
            target=(.60+.32*(i+.5)/max(1,count)) if b['order']==2 else (.32+.62*(i+.5)/max(1,count))
            item=min((q for q in options if q not in chosen),key=lambda q:(abs(q[0]-target),q[0]));chosen.append(item)
        for i,(t,point,tangent) in enumerate(chosen):
            identity=b['id']+f':foliage:{i:02d}';n,up=frame(tangent)
            roll=2*math.pi*rnd(identity,'roll');radial=unit(add(mul(n,math.cos(roll)),mul(up,math.sin(roll))))
            anchor=surface_point(b,t,radial)
            x=unit(add(tangent,mul(radial,.28)));y,z=frame(x)
            spin=2*math.pi*rnd(identity,'spin');y1=add(mul(y,math.cos(spin)),mul(z,math.sin(spin)));z1=unit(cross(x,y1))
            index=derive_seed(p['paint_seed'],identity)%len(geometry);g=geometry[index]
            span=h*p['span_over_height']*(.88+.24*rnd(identity,'size'))
            size=[v*span for v in g['aspect']];basis=[x,y1,z1]
            center=sub(anchor,[sum(g['root_normalized'][a]*size[a]*basis[a][k] for a in range(3)) for k in range(3)])
            group={'id':identity,'parent_branch_id':b['id'],'parent_t':t,'center_m':center,'axes':basis,'size_m':size,
                   'root_normalized':g['root_normalized'],'anchor_m':anchor,'template_index':index,'role':'longitudinal_cluster'}
            pieces=rooted_panels(group,index)
            if any(v[2]<0 for piece in pieces for v in piece['vertices']):raise ValueError('Lámina bajo el suelo')
            groups.append(group);cards.extend(pieces)
    if len(groups)!=quota:raise ValueError('Cupo incompleto')
    return {'version':p['version'],'spec':p,'ledger':ledger,'wood':selected,'groups':groups,'foliage':cards,'axis_quotas':axis_quotas}
