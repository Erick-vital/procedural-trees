"""OF10: expansión entre brazos con +700 tris como máximo sobre OF9."""
import copy
from .oak_foliage_regions_contract import validate_canopy as validate_v9
VERSION = 'oak-foliage-canopy-0.10.0'


def validate_canopy(spec):
    if not isinstance(spec, dict) or spec.get('version') != VERSION:
        raise ValueError('Versión de expansión inválida')
    validate_v9({**spec, 'version':'oak-foliage-canopy-0.9.0'})
    return copy.deepcopy(spec)
