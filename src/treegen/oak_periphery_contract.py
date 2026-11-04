"""O5: mismos controles y geometría presupuestada que O4."""
import copy
from .oak_volume_contract import validate_preset as validate_v4,triangle_bound
VERSION='oak-growth-0.5.0'


def validate_preset(p):
    if not isinstance(p,dict) or p.get('version')!=VERSION:
        raise ValueError('Preset O5 inválido')
    validate_v4({**p,'version':'oak-growth-0.4.0'})
    return copy.deepcopy(p)
