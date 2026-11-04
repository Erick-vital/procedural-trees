"""Distribución de ejes leñosos; no mide volumen de follaje ni naturalidad."""
import math
from .branch_structure import add,sub,mul,length


def volume_metrics(structure):
    h=structure['preset']['height_m'];bins=[0.,0.,0.];cells=[set(),set(),set()]
    births=[];inner_births=0;primary_rise=[];habits={}
    for b in structure['branches']:
        if b['order']==1:
            span=sum(length(sub(y,x)) for x,y in zip(b['points'],b['points'][1:]))
            primary_rise.append((b['points'][-1][2]-b['points'][0][2])/span)
            habits[b['id']]=b.get('growth_habit','uniform')
        if b['order']<2:continue
        root=b['points'][0];radius=math.hypot(root[0],root[1])/h
        inner_births+=radius<.30
        if b['order']==2:births.append(radius)
        for a,c in zip(b['points'],b['points'][1:]):
            size=length(sub(c,a))/h
            # Longitud integrada por segmentos, no conteo de vértices.
            for i in range(16):
                q=add(a,mul(sub(c,a),(i+.5)/16));r=math.hypot(q[0],q[1])/h
                region=0 if r<.30 else 1 if r<.50 else 2
                bins[region]+=size/16
                cells[region].add(tuple(math.floor(v/(h*.10)) for v in q))
    total=sum(bins)
    return {'radial_regions_over_H':[0,.30,.50],
        'axis_length_over_H':dict(zip(('core','middle','periphery'),bins)),
        'peripheral_length_fraction':bins[2]/total,
        'occupied_cells_0_10H':dict(zip(('core','middle','periphery'),map(len,cells))),
        'inner_births_order_ge_2':inner_births,
        'secondary_mean_birth_radius_over_H':sum(births)/len(births),
        'primary_rise_over_path':primary_rise,'habits_by_bough':habits}
