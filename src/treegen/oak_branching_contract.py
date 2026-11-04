"""O3: contrato O2 conservado; cupo extra subordinado al árbol completo."""
import copy
from .oak_crown_contract import validate_preset as validate_v2
VERSION='oak-growth-0.3.0'
EXTRA_TRIANGLES=700
WOOD_LIMIT=6999-1584


def validate_preset(p):
    if not isinstance(p,dict) or p.get('version')!=VERSION:raise ValueError('Preset O3 inválido')
    validate_v2({**p,'version':'oak-growth-0.2.0'})
    return copy.deepcopy(p)


def triangle_bound(p):
    from .oak_growth_contract import triangle_bound as base_bound
    return min(WOOD_LIMIT,base_bound(p)+EXTRA_TRIANGLES)
