"""OF7: continuidad superior mediante marcos fijos, sin cambiar presupuesto."""
import copy
from .oak_foliage_volume_contract import validate_canopy as validate_v6
VERSION='oak-foliage-canopy-0.7.0'


def validate_canopy(spec):
    if not isinstance(spec,dict) or spec.get('version')!=VERSION:raise ValueError('Versión superior inválida')
    validate_v6({**spec,'version':'oak-foliage-canopy-0.6.0'})
    return copy.deepcopy(spec)
