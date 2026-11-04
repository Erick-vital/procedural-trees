"""Contrato independiente de arquitectura; no cambia TreeSpec ni blueprints históricos."""
import copy
import json
import math
from pathlib import Path

VERSION='oak-growth-0.1.0'
ORDER_LIMITS=[(1,8,6,9),(2,3,5,6),(3,2,4,5),(4,2,3,3)]


def load_preset(path):
    def unique(pairs):
        d={}
        for k,v in pairs:
            if k in d:raise ValueError('Campo duplicado: '+k)
            d[k]=v
        return d
    return validate_preset(json.loads(Path(path).read_text(),object_pairs_hook=unique,
        parse_constant=lambda x:(_ for _ in ()).throw(ValueError(x))))


def number(value,low,high):
    return type(value) in (int,float) and math.isfinite(value) and low<=value<=high


def validate_preset(p):
    fields={'version','stage','height_m','maturity','vigor','crown_spread','curvature','light_tropism','gravity','competition','pipe_exponent','basal_flare','orders'}
    if not isinstance(p,dict) or set(p)!=fields or p['version']!=VERSION or p['stage'] not in ('joven','maduro','centenario'):
        raise ValueError('Preset oak-growth inválido')
    ranges={'height_m':(3,20),'maturity':(0,1),'vigor':(.65,1.2),'crown_spread':(.8,1.4),'curvature':(.08,.4),
            'light_tropism':(0,.4),'gravity':(0,.25),'competition':(0,1),'pipe_exponent':(2,3),'basal_flare':(1,1.7)}
    if any(not number(p[k],*bounds) for k,bounds in ranges.items()):raise ValueError('Parámetro fuera de rango')
    if not isinstance(p['orders'],list) or len(p['orders'])!=4:raise ValueError('Se requieren cuatro órdenes')
    for row,(order,cap,sides,points) in zip(p['orders'],ORDER_LIMITS):
        if not isinstance(row,dict) or set(row)!={'order','max_children','length_ratio','fork_angle_deg','curvature_scale','sides','points','branching_probability','demand_weight','attachment_min'}:
            raise ValueError('Contrato de orden inválido')
        if any(type(row[k]) is not int for k in ('order','max_children','sides','points')) or (row['order'],row['sides'],row['points'])!=(order,sides,points) or not 1<=row['max_children']<=cap:
            raise ValueError('Resolución o frecuencia fuera del presupuesto')
        if not number(row['length_ratio'],.25,.85) or not number(row['fork_angle_deg'],10,80) or not number(row['curvature_scale'],.2,1.5):raise ValueError('Regla de orden inválida')
        if not number(row['branching_probability'],.3,1) or not number(row['demand_weight'],.00005,.2) or not number(row['attachment_min'],.2,.5):raise ValueError('Frecuencia, carga o nacimiento inválidos')
    if triangle_bound(p)+1584>6999:raise ValueError('Presupuesto total excedido')
    return copy.deepcopy(p)


def triangle_bound(p):
    total=204;count=1
    for r in p['orders']:
        count*=r['max_children'];total+=count*((r['points']-1)*2*r['sides']+r['sides']-2)
    return total


def validate_seed(seed):
    if type(seed) is not int or not 0<=seed<2147483647:raise ValueError('Semilla entera fuera de rango')
    return seed
