"""OF6: volúmenes compartidos de copa, sin tocar el contrato histórico."""
import copy
from .oak_foliage_macro_contract import validate_canopy as validate_v5
VERSION='oak-foliage-canopy-0.6.0'


def validate_canopy(spec):
    if not isinstance(spec,dict) or spec.get('version')!=VERSION:raise ValueError('Versión de volumen inválida')
    validate_v5({**spec,'version':'oak-foliage-canopy-0.5.0'})
    return copy.deepcopy(spec)
