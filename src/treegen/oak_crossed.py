"""Ensayo de grupos cruzados; proyecciones horneadas de la pintura aprobada."""
import math
from .pine_painted_sample import canonical_hash

VERSION='oak-crossed-trial-0.1.0'
TEMPLATE_COUNT=8
GRID=5
TILE=400
USABLE=.92
PLANES=((0,1),(0,2),(1,2))


def dot(a,b):return sum(x*y for x,y in zip(a,b))
def sub(a,b):return [x-y for x,y in zip(a,b)]
def unit(v):
    length=math.sqrt(dot(v,v))
    if not math.isfinite(length) or length<1e-9:raise ValueError('Eje de grupo inválido')
    return [x/length for x in v]
def cross(a,b):return [a[1]*b[2]-a[2]*b[1],a[2]*b[0]-a[0]*b[2],a[0]*b[1]-a[1]*b[0]]


def groups(source,cards):
    supports=source['supports'];leaves=source['placements']
    if not 1<=len(supports)<=360 or len(cards)!=len(leaves) or len(cards)>2160:
        raise ValueError('Presupuesto de grupos/hojas inválido')
    by_id={l['id']:l for l in leaves};by_support={s['id']:[] for s in supports}
    if len(by_id)!=len(leaves) or len(by_support)!=len(supports):raise ValueError('IDs duplicados')
    for c in cards:
        leaf=by_id[c['source_leaf_id']]
        by_support[leaf['support_id']].append(c)
    result=[]
    for s in supports:
        cards_in=sorted(by_support[s['id']],key=lambda c:c['source_leaf_id'])
        if len(cards_in)!=6:raise ValueError('Se requieren seis hojas por grupo')
        x=unit(sub(s['points_m'][-1],s['points_m'][-2]));n=s['normal_end']
        y=sub(n,[dot(n,x)*v for v in x])
        if dot(y,y)<1e-8:
            axis=min(([1,0,0],[0,1,0],[0,0,1]),key=lambda a:abs(dot(a,x)))
            y=cross(x,axis)
        y=unit(y);axes=[x,y,unit(cross(x,y))];origin=s['points_m'][-1]
        local=[[[dot(sub(v,origin),a) for a in axes] for v in c['vertices']] for c in cards_in]
        lo=[min(v[k] for row in local for v in row) for k in range(3)]
        hi=[max(v[k] for row in local for v in row) for k in range(3)]
        sizes=[hi[k]-lo[k] for k in range(3)]
        if min(sizes)<.01 or not all(math.isfinite(t) for t in sizes):raise ValueError('Grupo plano o no finito')
        middle=[(a+b)/2 for a,b in zip(lo,hi)]
        normalized=[[[ (v[k]-middle[k])/sizes[k] for k in range(3)] for v in row] for row in local]
        center=[origin[k]+sum(middle[j]*axes[j][k] for j in range(3)) for k in range(3)]
        result.append({'id':s['id'],'parent_branch_id':s['parent_branch_id'],'center_m':center,'axes':axes,'size_m':sizes,
            'normalized_vertices':normalized,'source_cards':cards_in,'descriptor':[v for row in normalized for p in row for v in p]})
    return result


def fit_templates(items,count=TEMPLATE_COUNT):
    if not 1<=count<=TEMPLATE_COUNT or len(items)<count:raise ValueError('Número de plantillas inválido')
    def distance(a,b):return sum((x-y)**2 for x,y in zip(a['descriptor'],b['descriptor']))
    ordered=sorted(items,key=lambda g:canonical_hash(g['id']))
    chosen=[ordered[0]]
    while len(chosen)<count:
        options=[g for g in ordered if g not in chosen]
        chosen.append(max(options,key=lambda g:min(distance(g,t) for t in chosen)))
    assignments={g['id']:min(range(count),key=lambda i:distance(g,chosen[i])) for g in items}
    return chosen,assignments


def panels(group,template_index,plane_count):
    if plane_count not in (2,3) or not 0<=template_index<TEMPLATE_COUNT:raise ValueError('Perfil cruzado inválido')
    result=[]
    for plane,(a,b) in enumerate(PLANES[:plane_count]):
        tile=template_index*3+plane;col,row=tile%GRID,tile//GRID
        vertices=[];uv=[]
        for u,v in ((0,0),(1,0),(1,1),(0,1)):
            vertices.append([group['center_m'][k]+(u-.5)*group['size_m'][a]/USABLE*group['axes'][a][k]+(v-.5)*group['size_m'][b]/USABLE*group['axes'][b][k] for k in range(3)])
            uv.append([(col+u)/GRID,(row+v)/GRID])
        result.append({'vertices':vertices,'polygons':[[0,1,2],[0,2,3]],'uv':uv,
            'source_support_id':group['id'],'template_index':template_index,'plane':plane})
    return result
