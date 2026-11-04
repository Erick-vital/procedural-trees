"""OF9: organización espacial sobre OF8, piloto maduro versionado."""
import copy
from .oak_foliage_balance_contract import validate_canopy as validate_v8
VERSION = 'oak-foliage-canopy-0.9.0'


def validate_canopy(spec):
    if not isinstance(spec, dict) or spec.get('version') != VERSION:
        raise ValueError('Versión de regiones inválida')
    validate_v8({**spec, 'version': 'oak-foliage-canopy-0.8.0'})
    return copy.deepcopy(spec)
