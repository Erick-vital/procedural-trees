"""Representación piloto 0.1.0: atlas aprobado y soportes solo en secundarias."""
from .oak_painted_sample import leaf_card, wood_uv
from .pine_painted_sample import canonical_hash
from .foliage_molds import connection_geometry

VERSION='oak-painted-tree-pilot-0.1.0'


def retained_supports(reference,supports):
    branches=reference['branches']
    if not 1<=len(branches)<=64 or len(supports)>360:
        raise ValueError('Presupuesto de ramas/soportes excedido')
    parents={b['id']:b['parent_id'] for b in branches}
    if len(parents)!=len(branches):raise ValueError('Ramas duplicadas')
    depths={}
    for identifier in parents:
        current=identifier;seen=set()
        while current is not None:
            if current not in parents or current in seen:raise ValueError('Jerarquía incompleta o cíclica')
            seen.add(current);current=parents[current]
        depths[identifier]=len(seen)-1
    if len({s['id'] for s in supports})!=len(supports):raise ValueError('Soportes duplicados')
    if any(s['parent_branch_id'] not in depths for s in supports):raise ValueError('Padre de soporte desconocido')
    return [s for s in supports if depths[s['parent_branch_id']]>=2]


def build(reference,source,atlas,paint_seed):
    supports=source['supports'];leaves=source['placements']
    kept=retained_supports(reference,supports)
    if not leaves or len(leaves)>2160 or len(leaves)!=6*len(supports):
        raise ValueError('Presupuesto de hojas o grupos inválido')
    support_ids={s['id'] for s in supports}
    if any(l['support_id'] not in support_ids or l['variant']!='diamond' or l['fold_deg']!=0 for l in leaves):
        raise ValueError('Hoja incompatible con RF3')
    if type(paint_seed) is not int or not 0<=paint_seed<=2147483647:raise ValueError('Semilla de pintura inválida')
    wood=[(b['mesh'],0,wood_uv(b)) for b in reference['branches']]
    twigs=[]
    for s in supports:
        v,f=connection_geometry(s,source['canopy_spec'])
        uv=[[i%3/3,0 if i<3 else s['length_m']/1.4] for i in range(len(v))]
        twigs.append((s['id'],({'vertices':v,'polygons':f},0,uv)))
    cards=[]
    for leaf in leaves:
        variant=int(canonical_hash([paint_seed,leaf['id']])[:8],16)%4
        cards.append(leaf_card(leaf,atlas['leaf_regions'][variant],atlas['files']['foliage.png']['size']))
    foliage=[(c,1,c['uv']) for c in cards]
    kept_ids={s['id'] for s in kept}
    full=wood+[piece for _,piece in twigs]
    pruned=wood+[piece for identifier,piece in twigs if identifier in kept_ids]
    return {'wood-full':full,'wood':pruned,'painted-full':full+foliage,'painted':pruned+foliage},cards,kept
