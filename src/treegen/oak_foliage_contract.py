"""OF1: contrato de muestra, sin cambiar recetas de producción."""
import copy
import math
from .oak_growth_contract import validate_seed
VERSION='oak-foliage-sample-0.1.0'
FIELDS={'version','preset','seed','branch_id','layout_seed','paint_seed','tree_groups','span_over_height','core_radius_over_height'}


def validate_sample(p):
    if not isinstance(p,dict) or set(p)!=FIELDS or p['version']!=VERSION:
        raise ValueError('Contrato de muestra inválido')
    if p['preset'] not in {f'presets/oak-growth/0.5.0/{stage}.json' for stage in ('joven','maduro','centenario')}:
        raise ValueError('Preset O5 fuera del catálogo')
    if p['branch_id'] not in {f'p:{i}' for i in range(8)}:raise ValueError('Primaria inválida')
    for k in ('seed','layout_seed','paint_seed'):validate_seed(p[k])
    if type(p['tree_groups']) is not int or not 24<=p['tree_groups']<=264:raise ValueError('Reserva de follaje excedida')
    for k,lo,hi in [('span_over_height',.06,.16),('core_radius_over_height',.25,.40)]:
        if type(p[k]) not in (int,float) or not math.isfinite(p[k]) or not lo<=p[k]<=hi:raise ValueError('Escala/región inválida')
    return copy.deepcopy(p)
