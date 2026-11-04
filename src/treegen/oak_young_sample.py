"""J1: contrato y composición de muestra joven, conservando algoritmos históricos."""
import copy
from .oak_foliage_chain_contract import validate_sample as validate_chains
from .oak_foliage_chains import build as build_chains

VERSION = 'oak-young-sample-0.1.0'
FIXED = {'preset': 'presets/oak-growth/0.5.0/joven.json', 'branch_id': 'p:0',
         'tree_groups': 144, 'span_over_height': .10, 'core_radius_over_height': .25, 'mass_variant': 'B'}


def validate_sample(spec):
    if not isinstance(spec, dict) or spec.get('version') != VERSION:
        raise ValueError('Versión de muestra joven inválida')
    validate_chains({**spec, 'version': 'oak-foliage-sample-0.2.0'})
    if any(spec[k] != v for k, v in FIXED.items()):
        raise ValueError('J1 conserva el perfil joven fijo y la rama p:0')
    return copy.deepcopy(spec)


def build(structure, spec, templates, *, prepared=None):
    p = validate_sample(spec)
    if structure.get('version') != 'oak-growth-0.5.0' or structure['preset']['stage'] != 'joven' or structure['preset']['height_m'] != 5:
        raise ValueError('J1 requiere madera O5 joven de5 m')
    if structure['seed'] != p['seed']:
        raise ValueError('Semilla de madera distinta de la muestra')
    result = build_chains(structure, {**p, 'version': 'oak-foliage-sample-0.2.0'}, templates, prepared=prepared)
    result.update(version=VERSION, spec=p, scope='young branch only; full-tree foliage not integrated')
    result['diagnostics']['materialized_scope'] = result['scope']
    result['diagnostics']['reused_distribution'] = 'oak-foliage-sample-0.2.0/B'
    result['ledger']['family_wood_upper_bound'] = 5415
    result['ledger']['family_complete_upper_bound'] = 5415 + 6*p['tree_groups']
    if result['ledger']['family_complete_upper_bound'] > 6999:
        raise ValueError('Presupuesto de familia joven excedido')
    return result
