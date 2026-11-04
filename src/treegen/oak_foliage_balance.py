"""OF8: recuperar huella lateral con una lámina inclinada donde hace falta."""
import copy
import math
from .branch_structure import add,sub,mul,length,dot
from .oak_growth import unit,cross
from .oak_foliage_balance_contract import validate_canopy
from .oak_foliage_top import build as build_v7,opaque_points
from .oak_foliage_volume import build as build_v6
from .oak_foliage_cards import rooted_panels
from .oak_foliage_canopy import minimum_radius
from .oak_crossed import PLANES


def footprint(points,yaw,cell):
    # Muestreo simétrico del horizonte, independiente de cámaras Godot.
    right=(-math.sin(yaw),math.cos(yaw),0.)
    up=(-.1*math.cos(yaw),-.1*math.sin(yaw),1.)
    pixels=set()
    for p in points:
        x=math.floor(dot(p,right)/cell);y=math.floor(dot(p,up)/cell)
        pixels.update((x+dx,y+dy) for dx,dy in ((0,0),(-1,0),(1,0),(0,-1),(0,1)))
    return pixels


def rotate(v,axis,angle):
    return add(add(mul(v,math.cos(angle)),mul(cross(axis,v),math.sin(angle))),mul(axis,dot(axis,v)*(1-math.cos(angle))))


def complementary_group(g,plane):
    a,b=PLANES[plane];depth=({0,1,2}-{a,b}).pop();normal=g['axes'][depth]
    if normal[2]<0:normal=mul(normal,-1)
    basis=g['axes']
    if normal[2]<.24:
        axis=unit(cross(normal,(0,0,1)))
        angle=math.acos(max(-1,min(1,normal[2])))-math.acos(.24)
        basis=[rotate(v,axis,angle) for v in basis]
    origin=sub(g['anchor_m'],[sum(g['root_normalized'][j]*g['size_m'][j]*basis[j][k] for j in range(3)) for k in range(3)])
    return {**g,'id':g['id']+':lateral','axes':basis,'center_m':origin}


def plane_points(g,geometry,plane):
    a,b=PLANES[plane];depth=({0,1,2}-{a,b}).pop()
    samples=[q for q in geometry[g['template_index']]['opaque_samples'] if abs(q[depth]-g['root_normalized'][depth])<1e-10]
    return [[g['center_m'][k]+sum(q[j]*g['size_m'][j]*g['axes'][j][k] for j in range(3)) for k in range(3)] for q in samples]


def build(structure,spec,templates,*,prepared=None):
    p=validate_canopy(spec);result=copy.deepcopy(build_v7(structure,{**p,'version':'oak-foliage-canopy-0.7.0'},templates,prepared=prepared))
    previous=build_v6(structure,{**p,'version':'oak-foliage-canopy-0.6.0'},templates,prepared=prepared)
    old={g['id']:g for g in previous['groups']};h=structure['preset']['height_m'];core=h*p['core_radius_over_height'];directions=[i*math.pi/4 for i in range(8)]
    proposals=[];attempts=0
    for g in result['groups']:
        ref=old[g['id']]
        if g['axes']==ref['axes']:continue
        original_points=opaque_points(ref,prepared);current_points=opaque_points(g,prepared)
        before=[footprint(original_points,a,h*.012) for a in directions];now=[footprint(current_points,a,h*.012) for a in directions]
        loss=sum(len(a-b)/max(1,len(a)) for a,b in zip(before,now))/8
        if loss<.18:continue
        options=[]
        for plane in range(3):
            attempts+=1;extra=complementary_group(ref,plane);card=rooted_panels(extra,extra['template_index'])[plane]
            if minimum_radius([card])<core or min(v[2] for v in card['vertices'])<0:continue
            points=plane_points(extra,prepared,plane)
            masks=[footprint(points,a,h*.012) for a in directions]
            gain=sum(len((a-b)&c)/max(1,len(a)) for a,b,c in zip(before,now,masks))/8
            options.append((gain,-plane,extra,card))
        if not options:continue
        gain,neg_plane,extra,card=max(options,key=lambda row:row[:2])
        if gain>=.10:proposals.append({'group_id':g['id'],'plane':-neg_plane,'loss':loss,'gain':gain,'group':extra,'card':card})
    # Una sola lámina por grupo y límite global previo a mallar. No gastar el
    # margen en láminas que no recuperan una huella lateral significativa.
    cap=max(0,min(64,(6999-result['ledger']['tree_projected_triangles'])//2,
                  (6999-5415-6*p['tree_groups'])//2,(1584-6*p['tree_groups'])//2))
    proposals=sorted(proposals,key=lambda q:(-q['gain'],q['group_id']))[:cap]
    cards=[q.pop('card') for q in proposals]
    result['foliage'].extend(cards)
    result['ledger'].update(base_projected_triangles=result['ledger']['tree_projected_triangles'],complementary_planes=len(cards),
        foliage_triangles=result['ledger']['foliage_triangles']+2*len(cards),tree_projected_triangles=result['ledger']['tree_projected_triangles']+2*len(cards))
    result.update(version=p['version'],spec=p,lateral_complements=proposals,lateral_attempts=attempts,
        minimum_card_radius_m=minimum_radius(result['foliage']),scope='mature pilot; 216 groups with sparse lateral complements; <=6999 triangles')
    return result
