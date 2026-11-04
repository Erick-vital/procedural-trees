"""OF8: cobertura lateral complementaria dentro del techo global 6999."""
import copy
from .oak_foliage_top_contract import validate_canopy as validate_v7
VERSION='oak-foliage-canopy-0.8.0'


def validate_canopy(spec):
    if not isinstance(spec,dict) or spec.get('version')!=VERSION:raise ValueError('Versión de equilibrio inválida')
    validate_v7({**spec,'version':'oak-foliage-canopy-0.7.0'})
    return copy.deepcopy(spec)
