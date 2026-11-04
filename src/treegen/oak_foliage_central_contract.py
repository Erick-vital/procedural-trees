"""OF11: soporte central y follaje alto; contrato histórico OF10 conservado."""
import copy
from .oak_foliage_gaps_contract import validate_canopy as validate_v10
VERSION='oak-foliage-canopy-0.11.0'


def validate_canopy(spec):
    if not isinstance(spec,dict) or spec.get('version')!=VERSION:
        raise ValueError('Versión de copa central inválida')
    validate_v10({**spec,'version':'oak-foliage-canopy-0.10.0'})
    if spec['tree_groups']!=216:raise ValueError('OF11 conserva exactamente216 grupos')
    return copy.deepcopy(spec)
