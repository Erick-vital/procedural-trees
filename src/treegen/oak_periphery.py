"""Redistribución acotada de subárboles; sin añadir malla ni ocupar el núcleo."""
import copy
import math
from .oak_growth import sample,frame
from .branch_structure import add,sub,mul,dot,length


STEPS=(0.,.07,.14)
TWISTS=(0.,-.28,.28)
SCALES=(1.,1.12,1.24)


def distribution(branches,h):
    core=0.;periphery=0.;inner_births=0;cells=set();middle=set()
    for b in branches:
        root=b['points'][0]
        inner_births+=math.hypot(root[0],root[1])<h*.30
        for a,c in zip(b['points'],b['points'][1:]):
            span=length(sub(c,a))/h/16
            for i in range(16):
                q=add(a,mul(sub(c,a),(i+.5)/16));radius=math.hypot(q[0],q[1])/h
                cell=tuple(math.floor(v/(h*.10)) for v in q)
                if radius<.30:core+=span
                elif radius>=.50:periphery+=span;cells.add(cell)
                elif radius>=.35:middle.add(cell)
    return core,periphery,inner_births,cells,middle


def redistribute(structure):
    """27 candidatos/eje secundario como máximo, con restricciones por subárbol."""
    h=structure['preset']['height_m'];branches=structure['branches'];index={b['id']:b for b in branches}
    children={b['id']:[] for b in branches}
    for b in branches:
        if b['parent_id'] is not None:children[b['parent_id']].append(b['id'])
    def descendants(identity):
        result=[identity]
        for child in children[identity]:result+=descendants(child)
        return result
    groups={b['id']:descendants(b['id']) for b in branches if b['order']==2}
    limit=max(math.hypot(v[0],v[1]) for b in branches for v in b['points'])*1.03
    ordered=sorted(groups,key=lambda k:(distribution([index[i] for i in groups[k]],h)[1],k))
    traces=[];tested=0
    for identity in ordered:
        ids=groups[identity];original=[copy.deepcopy(index[i]) for i in ids];axis=original[0];parent=index[axis['parent_id']]
        old_root,old_tangent=sample(parent['points'],axis['parent_t']);old_side,old_up=frame(old_tangent)
        before=distribution(original,h);others=distribution([b for b in branches if b['order']>=2 and b['id'] not in ids],h)
        anchor=max(v[2] for b in original for v in b['points'])>=h-1e-8
        occupied=before[3]|others[3]
        def score(metrics):
            return len(metrics[3]|others[3])+len(metrics[4]|others[4])*.12+metrics[1]*3
        best_score=score(before);best=None;choice=(0.,0.,1.);valid=0
        for delta in STEPS:
            t=min(.93,axis['parent_t']+delta)
            # No acumular nacimientos laterales en un punto distal común.
            siblings=[index[i] for i in children[parent['id']] if i!=identity]
            if delta and any(abs(t-b['parent_t'])<.065 for b in siblings):continue
            root,tangent=sample(parent['points'],t);side,up=frame(tangent)
            for twist in TWISTS:
                for scale in SCALES:
                    tested+=1
                    if delta==0 and twist==0 and scale==1:continue
                    c=math.cos(twist);s=math.sin(twist)
                    side2=add(mul(side,c),mul(up,s));up2=add(mul(up,c),mul(side,-s))
                    candidate=[]
                    for b in original:
                        points=[]
                        for point in b['points']:
                            offset=sub(point,old_root)
                            rotated=add(mul(tangent,dot(offset,old_tangent)),add(mul(side2,dot(offset,old_side)),mul(up2,dot(offset,old_up))))
                            points.append(add(root,mul(rotated,scale)))
                        candidate.append({**b,'points':points})
                    candidate[0]['parent_t']=t
                    allp=[v for b in candidate for v in b['points']]
                    top=max(v[2] for v in allp)
                    if top>h+1e-8 or min(v[2] for v in allp)<0:continue
                    if anchor and abs(top-h)>1e-8:continue
                    if max(math.hypot(v[0],v[1]) for v in allp)>limit:continue
                    metrics=distribution(candidate,h)
                    if metrics[0]>before[0]+1e-10 or metrics[2]>before[2]:continue
                    if metrics[1]<before[1]-1e-10 or len(metrics[3]|others[3])<len(occupied):continue
                    valid+=1
                    value=score(metrics)
                    # Conservar el candidato original en empates; no gastar
                    # recorrido o desplazar nacimientos sin ganancia espacial.
                    if value>best_score+1e-8:
                        best_score=value;best=candidate;choice=(delta,twist,scale)
        if best is not None:
            for b in best:index[b['id']].update(b)
        traces.append({'id':identity,'valid_candidates':valid,'accepted':best is not None,
                       'attachment_delta':choice[0],'twist_rad':choice[1],'length_scale':choice[2],
                       'score_before':score(before),'score_after':best_score})
    return {'version':'oak-periphery-0.1.0','tested_candidates':tested,'maximum_candidates_per_secondary':27,
            'horizontal_limit_m':limit,'accepted_subtrees':sum(t['accepted'] for t in traces),'subtrees':traces}
