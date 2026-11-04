"""OF10: abanicos inclinados arraigados hacia huecos intermedios de la copa."""
import copy
import math
from .branch_structure import add, sub, mul, dot, length
from .oak_growth import unit, cross, sample
from .oak_foliage_regions import build as build_v9, centroid
from .oak_foliage_gaps_contract import validate_canopy
from .oak_foliage_cards import rooted_panels
from .oak_foliage_canopy import minimum_radius
from .oak_foliage_balance import plane_points
from .oak_foliage_top import opaque_points
from .oak_crossed import PLANES


def gap_plan(regions, height, core):
    """Interfaces cercanas con centro exterior; conservar grandes separaciones."""
    pairs=[]
    for i,a in enumerate(regions):
        for b in regions[i+1:]:
            pa,pb=a['center_m'],b['center_m'];d=math.dist(pa,pb)
            midpoint=mul(add(pa,pb),.5)
            va=unit((pa[0],pa[1],0));vb=unit((pb[0],pb[1],0))
            angle=math.acos(max(-1,min(1,dot(va,vb))))
            if not .32 < angle < 1.85:continue
            if not height*.24 < d < height*1.02:continue
            if abs(pa[2]-pb[2]) > height*.40:continue
            # Objetivo sobre un arco periférico, no sobre una cuerda que cruza
            # el núcleo: permite expansión en los flancos de brazos separados.
            direction=unit(add(va,vb))
            radius=max(core+height*.12, .90*(math.hypot(*pa[:2])+math.hypot(*pb[:2]))/2)
            midpoint=[direction[0]*radius,direction[1]*radius,midpoint[2]]
            # Evitar pares con otra región interpuesta en XY.
            delta=sub(pb,pa);den=dot(delta,delta)
            if any(.15 < dot(sub(q['center_m'],pa),delta)/den < .85 and
                   length(sub(q['center_m'],add(pa,mul(delta,dot(sub(q['center_m'],pa),delta)/den)))) < height*.12
                   for q in regions if q not in (a,b)):continue
            pairs.append({'id':a['id']+'~'+b['id'],'arms':[a['primary_id'],b['primary_id']],
                          'endpoints_m':[pa,pb], 'center_m':midpoint,'distance_m':d})
    # Dar prioridad a interfaces con menos alternativas por brazo; limitar grados
    # para no gastar el cupo en varios enlaces de un único sector muy poblado.
    chosen=[];degrees={}
    for q in sorted(pairs,key=lambda q:(q['distance_m'],q['id'])):
        if any(degrees.get(b,0)>=2 for b in q['arms']):continue
        chosen.append(q)
        for b in q['arms']:degrees[b]=degrees.get(b,0)+1
        if len(chosen)==5:break
    return chosen


def fan_group(g, target, plane, scale, incline):
    """Orientar el centro de la pintura hacia el hueco, raíz opaca conservada."""
    a,b=PLANES[plane];depth=({0,1,2}-{a,b}).pop()
    delta=sub(target,g['anchor_m']);distance=math.hypot(*delta[:2])
    forward=unit((delta[0],delta[1],max(-.35*distance,min(.35*distance,delta[2]))))
    side=unit((-forward[1],forward[0],0));vertical=unit(cross(forward,side))
    up=add(mul(side,math.cos(incline)),mul(vertical,math.sin(incline)))
    # beta lo proporciona la media opaca del plano, no su rectángulo transparente.
    beta=g['_fan_beta'];c,s=math.cos(beta),math.sin(beta)
    axis_a=sub(mul(forward,c),mul(up,s));axis_b=add(mul(forward,s),mul(up,c))
    axes=[None,None,None];axes[a]=axis_a;axes[b]=axis_b
    axes[depth]=mul(unit(cross(axis_a,axis_b)),-1 if (a,b)==(0,2) else 1)
    size=[v*scale for v in g['size_m']]
    center=sub(g['anchor_m'],[sum(g['root_normalized'][j]*size[j]*axes[j][k] for j in range(3)) for k in range(3)])
    return {**{k:v for k,v in g.items() if k!='_fan_beta'},'axes':axes,'size_m':size,'center_m':center}


def build(structure,spec,templates,*,prepared=None):
    p=validate_canopy(spec)
    result=copy.deepcopy(build_v9(structure,{**p,'version':'oak-foliage-canopy-0.9.0'},templates,prepared=prepared))
    h=structure['preset']['height_m'];core=h*p['core_radius_over_height']
    gaps=gap_plan(result['regions'],h,core)
    # Presupuesto autorizado relativo a OF9; no se aplica la reserva histórica
    # 1584 como nuevo límite. El techo real6999 prevalece en todas las semillas.
    cap=min(350,max(0,(6999-result['ledger']['tree_projected_triangles'])//2))
    original_count=len(result['foliage']);proposals=[];attempts=0
    base_points=[pt for g in result['groups'] for pt in opaque_points(g,prepared)]
    cell=h*.035
    def voxel(pt):return tuple(math.floor(x/cell) for x in pt)
    occupied={voxel(pt) for pt in base_points}
    protected=[sample(b['points'],t)[0] for b in structure['branches'] if b['order']==1 for t in (.08,.22,.38)]
    # Protección de lectura estructural en un anillo simétrico de direcciones,
    # independiente de las cámaras de revisión. Rejillas solo de planificación.
    visibility_points=[sample(b['points'],t)[0] for b in structure['branches'] if b['order']==0 for t in (0.,.15,.3,.45,.6,.75,.9)]
    visibility_points.extend(sample(b['points'],t)[0] for b in structure['branches'] if b['order']==1 for t in (0.,.1,.2,.3))
    visibility=[];vcell=h*.02
    for elevation in (.12,.30):
        for i in range(8):
            yaw=i*math.pi/4;right=(-math.sin(yaw),math.cos(yaw),0)
            up=unit((-elevation*math.cos(yaw),-elevation*math.sin(yaw),1))
            cells=set()
            for point in visibility_points:
                x=dot(point,right)/vcell;y=dot(point,up)/vcell
                for dx in range(-3,4):
                    for dy in range(-3,4):
                        ix=math.floor(x)+dx;iy=math.floor(y)+dy
                        if (ix+.5-x)**2+(iy+.5-y)**2<(.045*h/vcell)**2:cells.add((ix,iy))
            visibility.append((right,up,cells))
    def projection_obstruction(points):
        return max(sum((math.floor(dot(v,right)/vcell),math.floor(dot(v,up)/vcell)) in cells for v in points)/len(points)
                   for right,up,cells in visibility)
    for g in result['groups']:
        bid=g['parent_branch_id'].split('/')[0]
        interfaces=[q for q in gaps if bid in q['arms']]
        if not interfaces:continue
        # Como máximo dos láminas nuevas por grupo; algunos brazos no se unen.
        for gap in interfaces[:2]:
            target=gap['center_m'];delta=sub(target,g['anchor_m'])
            if length(delta)>h*.40:continue
            # Trabajar en los flancos, no prolongar radialmente una punta.
            radial=unit((g['anchor_m'][0],g['anchor_m'][1],0))
            lateral=unit((delta[0],delta[1],0))
            if abs(dot(radial,lateral))>.87:continue
            choices=[]
            for plane,(a,b) in enumerate(PLANES):
                samples=[q for q in prepared[g['template_index']]['opaque_samples']
                         if abs(q[({0,1,2}-{a,b}).pop()]-g['root_normalized'][({0,1,2}-{a,b}).pop()])<1e-10]
                if not samples:continue
                da=sum((q[a]-g['root_normalized'][a])*g['size_m'][a] for q in samples)/len(samples)
                db=sum((q[b]-g['root_normalized'][b])*g['size_m'][b] for q in samples)/len(samples)
                beta=math.atan2(db,da)
                for scale in (1.15,1.35,1.55):
                    for incline in (.55,.95,-.65):
                        attempts+=1
                        new=fan_group({**g,'_fan_beta':beta},target,plane,scale,incline)
                        card=rooted_panels(new,new['template_index'])[plane]
                        if minimum_radius([card])<core or min(v[2] for v in card['vertices'])<0:continue
                        points=plane_points(new,prepared,plane)
                        obstruction=projection_obstruction(points)
                        if obstruction>.25:continue
                        if min(math.dist(v,q) for v in points for q in protected)<h*.085:continue
                        # Expansión opaca hacia la interfaz y novedad volumétrica;
                        # no premiar bordes transparentes ni alcanzar el horizonte.
                        base_distance=min(math.dist(v,target) for v in opaque_points(g,prepared))
                        distance=min(math.dist(v,target) for v in points)
                        if distance>base_distance-h*.012:continue
                        gap_axis=unit(sub(gap['endpoints_m'][1],gap['endpoints_m'][0]))
                        near=[v for v in points if abs(dot(sub(v,target),gap_axis))<gap['distance_m']*.36
                              and math.dist(v,target)<h*.24]
                        novelty={voxel(v) for v in near}-occupied
                        if len(novelty)<3:continue
                        score=len(novelty)+10*(base_distance-distance)/h-2*(scale-1)
                        row=(score,-plane,-scale,-incline,new,card,points,novelty)
                        choices.append(row)
            ranked=sorted(choices,key=lambda row:row[:4],reverse=True)
            picked=[]
            for row in ranked:
                a,b=PLANES[-row[1]];depth=({0,1,2}-{a,b}).pop();normal=row[4]['axes'][depth]
                if any(abs(dot(normal,prior[4]['axes'][({0,1,2}-set(PLANES[-prior[1]])).pop()]))>.82 for prior in picked):continue
                picked.append(row)
                if len(picked)==2:break
            for score,negplane,negscale,negtilt,new,card,points,novelty in picked:
                proposals.append({'group_id':g['id'],'gap_id':gap['id'],'plane':-negplane,
                                  'scale':-negscale,'incline':-negtilt,'score':score,'group':new,
                                  '_card':card,'_points':points,'_novelty':novelty})
    # Selección global con actualización de ocupación; no gastar todos los tris
    # en varias láminas que vuelven a cubrir el mismo extremo del mismo brazo.
    selected=[];counts={};used_pairs=set()
    for q in sorted(proposals,key=lambda q:(-q['score'],q['group_id'],q['gap_id'])):
        if len(selected)>=cap:break
        gid=q['group_id'];pair=(gid,q['gap_id'],q['plane'],q['incline'])
        if counts.get(gid,0)>=2 or pair in used_pairs:continue
        if len(q['_novelty']-occupied)<2:continue
        occupied.update(voxel(v) for v in q['_points']);counts[gid]=counts.get(gid,0)+1;used_pairs.add(pair)
        result['foliage'].append(q.pop('_card'));q.pop('_points');q.pop('_novelty');selected.append(q)
    extra=2*len(selected)
    result['ledger'].update(of9_tree_triangles=result['ledger']['tree_projected_triangles'],
        gap_planes=len(selected),foliage_triangles=result['ledger']['foliage_triangles']+extra,
        tree_projected_triangles=result['ledger']['tree_projected_triangles']+extra)
    result.update(version=p['version'],spec=p,gaps=gaps,gap_fans=selected,gap_attempts=attempts,
                  projection_protection={'azimuths':8,'elevations':[.12,.30],'maximum_sample_overlap':.25,'cell_m':vcell,'roi_radius_m':.045*h},
                  base_plane_count=original_count,minimum_card_radius_m=minimum_radius(result['foliage']),
                  scope='mature pilot; anchored lateral fans toward selected inter-arm gaps; <=700 added triangles')
    return result
