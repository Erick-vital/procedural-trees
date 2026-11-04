"""OF2: comparación controlada de tres distribuciones; OF1 intacta."""
import copy
from .oak_foliage_contract import validate_sample as validate_v1
VERSION='oak-foliage-sample-0.2.0'


def validate_sample(p):
    if not isinstance(p,dict) or p.get('version')!=VERSION or p.get('mass_variant') not in ('A','B','C'):
        raise ValueError('Variante OF2 inválida')
    old={k:v for k,v in p.items() if k!='mass_variant'};old['version']='oak-foliage-sample-0.1.0';validate_v1(old)
    return copy.deepcopy(p)
