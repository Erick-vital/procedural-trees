"""Muestra artística aislada: rama RF3 congelada; sin optimización de geometría."""
import math
from .pine_painted_sample import canonical_hash
BRANCH_ID='q3:primary:100'
PAINT_SEED=2718


def secondary_supports(wood, supports):
    """Ensayo de madera: conservar solo soportes nacidos de secundarias."""
    parents={b['id']:b['parent_id'] for b in wood}
    if BRANCH_ID not in parents or any(s['parent_branch_id'] not in parents for s in supports):
        raise ValueError('Jerarquía de muestra incompleta')
    return [s for s in supports if parents[s['parent_branch_id']]==BRANCH_ID]


def twig_spec(spec, profile='original'):
    """Perfil experimental sin añadir anillos ni alterar el eje del soporte."""
    if profile not in ('original', 'fuller-v1'):
        raise ValueError('Perfil de ramilla desconocido')
    result = dict(spec)
    if profile == 'fuller-v1':
        result['twig_radius_m'] *= 1.25
        result['tip_radius_ratio'] = .5
    return result


def select(reference,manifest):
    selected={BRANCH_ID}
    for _ in range(3):
        selected.update(b['id'] for b in reference['branches'] if b['parent_id'] in selected)
    wood=[b for b in reference['branches'] if b['id'] in selected]
    if not wood or wood[0]['id']!=BRANCH_ID:raise ValueError('Rama primaria de muestra ausente')
    supports=[s for s in manifest['supports'] if s['parent_branch_id'] in selected]
    leaves=[leaf for leaf in manifest['placements'] if leaf['parent_branch_id'] in selected]
    if not leaves or len(leaves)!=6*len(supports):raise ValueError('Muestra sin seis hojas por soporte')
    return wood,supports,leaves


def leaf_card(leaf,region,size):
    """UV sobre PNG íntegro; raíz del pecíolo y envolvente nominal conservadas."""
    width,height=size;left,top,right,bottom=region['uv_crop_px'];x0,y0,x1,y1=region['opaque_bbox_px'];root_x,root_y=region['root_px']
    vertices=[];uv=[]
    for px,py in ((left,bottom),(right,bottom),(right,top),(left,top)):
        along=(root_y-py)/(y1-y0)*leaf['length_m']
        across=(px-root_x)/(x1-x0)*leaf['length_m']*.6
        vertices.append([leaf['origin_m'][k]+along*leaf['axes'][0][k]+across*leaf['axes'][1][k] for k in range(3)])
        uv.append([px/width,1-py/height])
    # Lateral primero, longitudinal después: invertir para coincidir con normales RF3.
    return {'vertices':vertices,'polygons':[[0,2,1],[0,3,2]],'uv':uv,
        'source_leaf_id':leaf['id'],'atlas_variant':region['variant'],'origin_m':leaf['origin_m']}


def variant_for(leaf):return int(canonical_hash([PAINT_SEED,leaf['id']])[:8],16)%4


def wood_uv(branch):
    vertices=branch['mesh']['vertices'];sides=8
    if len(vertices)%sides:raise ValueError('Anillos de madera no reconocidos')
    centers=[[sum(v[k] for v in vertices[i:i+sides])/sides for k in range(3)] for i in range(0,len(vertices),sides)]
    lengths=[0.]
    for a,b in zip(centers,centers[1:]):lengths.append(lengths[-1]+math.dist(a,b))
    return [[(i%sides)/sides,lengths[i//sides]/1.4] for i in range(len(vertices))]
