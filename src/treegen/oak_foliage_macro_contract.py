"""OF5: refinamiento acotado de OF4, sin aumentar grupos ni presupuesto."""
import copy
from .oak_foliage_peripheral_contract import validate_canopy as validate_v4
VERSION='oak-foliage-canopy-0.5.0'


def validate_canopy(spec):
    if not isinstance(spec,dict) or spec.get('version')!=VERSION:raise ValueError('Versión de macromasas inválida')
    validate_v4({**spec,'version':'oak-foliage-canopy-0.4.0'})
    return copy.deepcopy(spec)
