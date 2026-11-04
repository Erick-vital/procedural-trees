"""Indicadores de alcance y desequilibrio; no sustituyen revisión artística."""
import math
from .branch_structure import sub,length


def crown_metrics(structure):
    h=structure['preset']['height_m'];points=[];weighted=[];ends=[];sector=[0.]*8
    for b in structure['branches'][1:]:
        ends.append(math.atan2(b['points'][-1][1],b['points'][-1][0])%(2*math.pi))
        points.extend(b['points'])
        for a,c in zip(b['points'],b['points'][1:]):
            w=length(sub(c,a));mid=[(a[k]+c[k])/2 for k in range(3)];weighted.append((mid,w))
    for point in points:
        angle=math.atan2(point[1],point[0])%(2*math.pi);sector[min(7,int(angle/(math.pi/4)))]=max(sector[min(7,int(angle/(math.pi/4)))],math.hypot(*point[:2])/h)
    weight=sum(w for _,w in weighted);center=[sum(p[k]*w for p,w in weighted)/weight/h for k in range(3)]
    avg=sum(sector)/len(sector);cv=math.sqrt(sum((r-avg)**2 for r in sector)/len(sector))/avg
    angles=sorted(ends);gaps=[b-a for a,b in zip(angles,angles[1:]+[angles[0]+2*math.pi])]
    return {'max_horizontal_reach_over_H':max(math.hypot(*p[:2]) for p in points)/h,
        'crown_center_offset_over_H':math.hypot(*center[:2]),'length_weighted_crown_center_over_H':center,
        'sector_reach_over_H':sector,'sector_reach_cv':cv,'largest_endpoint_angular_gap_deg':math.degrees(max(gaps)),
        'endpoint_gap_range_deg':[math.degrees(min(gaps)),math.degrees(max(gaps))]}
