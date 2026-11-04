"""OF4: revisión independiente, mismo contrato físico y límites de OF3."""
import copy
from .oak_foliage_canopy_contract import validate_canopy as validate_v3
VERSION='oak-foliage-canopy-0.4.0'


def validate_canopy(spec):
    if not isinstance(spec,dict) or spec.get('version')!=VERSION:
        raise ValueError('Versión periférica inválida')
    validate_v3({**spec,'version':'oak-foliage-canopy-0.3.0'})
    return copy.deepcopy(spec)
