"""R3: contraer bifurcaciones ocultas conservando mallas visibles y conexiones."""
import copy
from collections import defaultdict
from .branch_sample import segment_mesh

VERSION='branch-interior-collapse-0.1.0'


def proposals(network,protected_ids):
    edges=network['edges'];index={e['id']:e for e in edges};protected=set(protected_ids)
    if len(index)!=len(edges) or not 1<=len(edges)<=720 or protected-set(index):raise ValueError('Red/protección inválida')
    children=defaultdict(list)
    for e in edges:
        if e['parent'] is not None and e['parent'] not in index:raise ValueError('Padre desconocido')
        children[e['parent']].append(e)
    result=[]
    for edge in edges:
        kids=children[edge['id']]
        if edge['parent'] is None or edge['id'] in protected or not 1<=len(kids)<=2:continue
        if any(c['id'] in protected for c in kids):continue
        if len(children[edge['parent']])-1+len(kids)>3:continue
        replacements=[]
        for child in kids:
            candidate=copy.deepcopy(child);candidate['parent']=edge['parent']
            candidate['points']=[edge['points'][0],child['points'][-1]]
            candidate['mesh']=segment_mesh(candidate['points'],[child['radii'][0],child['radii'][-1]],child['terminal'])
            candidate['radii']=[child['radii'][0],child['radii'][-1]]
            replacements.append(candidate)
        saving=sum(len(f)-2 for f in edge['mesh']['polygons'])+sum(sum(len(f)-2 for f in c['mesh']['polygons']) for c in kids)-sum(sum(len(f)-2 for f in c['mesh']['polygons']) for c in replacements)
        if saving>0:result.append({'removed':edge['id'],'parent':edge['parent'],'replacements':replacements,'saving':saving})
    return result


def apply_proposals(network,options,hidden_replacement_ids):
    hidden=set(hidden_replacement_ids);result=copy.deepcopy(network);used=set();removed=set();replace={};accepted=[]
    for option in options:
        touched={option['removed'],option['parent'],*(e['id'] for e in option['replacements'])}
        if touched & used:continue
        if not all(option['removed']+'>'+e['id'] in hidden for e in option['replacements']):continue
        used.update(touched);removed.add(option['removed'])
        replace.update({e['id']:copy.deepcopy(e) for e in option['replacements']});accepted.append(option['removed'])
    result['edges']=[replace.get(e['id'],e) for e in result['edges'] if e['id'] not in removed]
    result['triangles']=sum(sum(len(f)-2 for f in e['mesh']['polygons']) for e in result['edges'])
    assert not ({v['edge_id'] for v in result['connections'].values()} & removed)
    index={e['id']:e for e in result['edges']};children=defaultdict(int)
    for e in result['edges']:
        if e['parent'] is not None:
            assert e['parent'] in index
            assert e['points'][0]==index[e['parent']]['points'][-1]
            children[e['parent']]+=1
    assert max(children.values(),default=0)<=3
    return result,{'version':VERSION,'accepted':accepted,'removed_triangles':network['triangles']-result['triangles']}
