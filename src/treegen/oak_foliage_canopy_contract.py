"""OF3: piloto maduro de copa completa, separado de muestras históricas."""
import copy
from .oak_foliage_contract import validate_sample
VERSION='oak-foliage-canopy-0.3.0'


def validate_canopy(spec):
    if not isinstance(spec,dict) or spec.get('version')!=VERSION:
        raise ValueError('Versión de copa inválida')
    old={**spec,'version':'oak-foliage-sample-0.1.0','branch_id':'p:0'}
    # No aceptar branch_id en un contrato de árbol completo.
    if 'branch_id' in spec:raise ValueError('La copa no selecciona una rama')
    validate_sample(old)
    if spec['preset']!='presets/oak-growth/0.5.0/maduro.json':
        raise ValueError('OF3 solo admite el perfil maduro ensayado')
    return copy.deepcopy(spec)
