"""OF7: cruzadas inclinadas y extensión opaca dirigida a huecos periféricos."""
import copy
import math
from .branch_structure import add,sub,mul,length,dot
from .oak_growth import unit,cross
from .oak_foliage_volume import build as build_v6
from .oak_foliage_top_contract import validate_canopy
from .oak_foliage_canopy import minimum_radius
from .oak_foliage_cards import rooted_panels
from .oak_crossed import PLANES,GRID,USABLE


def prepare_opaque_samples(geometry,image):
    """Muestreo acotado del PNG original para guiar orientación, sin repintar."""
    result=copy.deepcopy(geometry)
    for index,g in enumerate(result):
        samples=[]
        for plane,(a,b) in enumerate(PLANES):
            tile=index*3+plane;col,row=tile%GRID,tile//GRID;points=[]
            for iy in range(16):
                for ix in range(16):
                    u=(ix+.5)/16;v=(iy+.5)/16
                    px=min(image.width-1,round((col+u)*image.width/GRID));py=min(image.height-1,round((1-(row+v)/GRID)*image.height))
                    if image.getpixel((px,py))[3]<192:continue
                    q=[0.,0.,0.];q[a]=(u-.5)/USABLE;q[b]=(v-.5)/USABLE
                    depth=({0,1,2}-{a,b}).pop();q[depth]=g['root_normalized'][depth];points.append(q)
            samples.extend(points)
        if not samples:raise ValueError('Plantilla sin pintura opaca muestreada')
        g['opaque_samples']=samples
    return result


def balanced_basis(yaw,tilt):
    """Tres normales con componente vertical: ninguna lámina vertical de partida."""
    r=math.sqrt(2/3);z=math.sqrt(1/3)
    x=(r*math.cos(yaw),r*math.sin(yaw),z)
    y=(r*math.cos(yaw+2*math.pi/3),r*math.sin(yaw+2*math.pi/3),z)
    basis=[x,y,unit(cross(x,y))]
    # Variación suave de inclinación, sin formar una capa horizontal plana.
    return [(v[0],v[1]*math.cos(tilt)-v[2]*math.sin(tilt),v[1]*math.sin(tilt)+v[2]*math.cos(tilt)) for v in basis]


def opaque_points(group,geometry):
    return [[group['center_m'][k]+sum(q[a]*group['size_m'][a]*group['axes'][a][k] for a in range(3)) for k in range(3)] for q in geometry[group['template_index']]['opaque_samples']]


def edge_fraction(groups):
    return sum(abs(axis[2])<.15 for g in groups for axis in g['axes'])/(3*len(groups))


def build(structure,spec,templates,*,prepared=None):
    p=validate_canopy(spec)
    if prepared is None or any('opaque_samples' not in g for g in prepared):raise ValueError('OF7 requiere muestreo opaco del atlas')
    result=copy.deepcopy(build_v6(structure,{**p,'version':'oak-foliage-canopy-0.6.0'},templates,prepared=prepared))
    old=result['groups'];h=structure['preset']['height_m'];core=h*p['core_radius_over_height'];envs={e['id']:e for e in result['envelopes']}
    transformed=[];changes=[];attempts=0;fallbacks=0
    for g in old:
        # Conservar los marcos sin cantos pronunciados; no reorientar una masa
        # que ya aporta espesor superior y continuidad en otras direcciones.
        if min(abs(a[2]) for a in g['axes'])>=.15 or g['role'] in ('bridge','macro_bridge','tip_retreat','inner_redundancy'):
            transformed.append({**g,'top_trial':None,'top_role':'existing_volume'});continue
        old_points=opaque_points(g,prepared)
        old_centroid=[sum(v[k] for v in old_points)/len(old_points) for k in range(3)]
        neighbors=[q for q in old if q['mass_id']!=g['mass_id'] and q['macro_id']==g['macro_id']]
        q=min(neighbors,key=lambda q:(math.dist(g['anchor_m'][:2],q['anchor_m'][:2]),q['id'])) if neighbors else None
        target=mul(add(g['anchor_m'],q['anchor_m']),.5) if q else envs[g['macro_id']]['center_m']
        flow=sub(target,g['anchor_m']);yaw=math.atan2(flow[1],flow[0])
        tilt=.08*math.tanh((g['anchor_m'][2]-envs[g['macro_id']]['center_m'][2])/(h*.15))
        candidates=[]
        for trial in range(8):
            basis=balanced_basis(yaw+trial*math.pi/12,tilt);attempts+=1
            origin=sub(g['anchor_m'],[sum(g['root_normalized'][a]*g['size_m'][a]*basis[a][k] for a in range(3)) for k in range(3)])
            new={**g,'center_m':origin,'axes':basis,'top_trial':trial,'top_role':'inclined_crosses'}
            panels=rooted_panels(new,new['template_index'])
            if minimum_radius(panels)<core or min(v[2] for pc in panels for v in pc['vertices'])<0:continue
            points=opaque_points(new,prepared)
            # Favorecer pintura opaca hacia el hueco entre masas, no los bordes
            # transparentes de una tarjeta. Coordenadas XY físicas, sin cámara.
            distances=[(v[0]-target[0])**2+(v[1]-target[1])**2 for v in points]
            affinity=sum(math.exp(-d/(h*.065)**2) for d in distances)/len(distances)
            reach=math.exp(-min(distances)/(h*.09)**2)
            centroid=[sum(v[k] for v in points)/len(points) for k in range(3)]
            preservation=math.exp(-sum((a-b)**2 for a,b in zip(centroid,old_centroid))/(h*.08)**2)
            contact_volume=sum(math.exp(-sum((v[k]-target[k])**2 for k in range(3))/(h*.08)**2) for v in points)/len(points)
            score=.30*affinity+.15*reach+.35*preservation+.20*contact_volume
            candidates.append((score,-trial,new))
        if candidates:new=max(candidates,key=lambda row:row[:2])[2]
        else:new={**g,'top_trial':None,'top_role':'core_protected'};fallbacks+=1
        transformed.append(new)
        if new['axes']!=g['axes']:changes.append({'id':g['id'],'trial':new['top_trial'],'neighbor_id':q['id'] if q else None,'target_xy_m':target[:2]})
    cards=[pc for g in transformed for pc in rooted_panels(g,g['template_index'])]
    result.update(version=p['version'],spec=p,groups=transformed,foliage=cards,top_changes=changes,top_attempts=attempts,top_fallbacks=fallbacks,
        top_edge_fraction_before=edge_fraction(old),top_edge_fraction_after=edge_fraction(transformed),
        minimum_card_radius_m=minimum_radius(cards),scope='mature pilot; world-up canopy refinement, no camera dependence or seed overrides')
    return result
