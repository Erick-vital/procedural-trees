"""O2: contrato del crecimiento equilibrado; contrato O1 intacto."""
import copy
from .oak_growth_contract import validate_preset as validate_v1,number
from .branch_tree import read_strict
VERSION='oak-growth-0.2.0'
BALANCE_LIMITS={'strength':(0,1),'radius_ratio':(.5,.9),'vertical_ratio':(.38,.6),'path_ratio':(.75,1.25),'irregularity':(.03,.18)}


def validate_preset(p):
    if not isinstance(p,dict) or p.get('version')!=VERSION or 'crown_balance' not in p:raise ValueError('Preset O2 inválido')
    old={k:copy.deepcopy(v) for k,v in p.items() if k!='crown_balance'};old['version']='oak-growth-0.1.0';validate_v1(old)
    b=p['crown_balance']
    if not isinstance(b,dict) or set(b)!=set(BALANCE_LIMITS) or any(not number(b[k],*limits) for k,limits in BALANCE_LIMITS.items()):raise ValueError('Controles de equilibrio inválidos')
    return copy.deepcopy(p)


def load_growth_preset(path):
    p=read_strict(path)
    if p.get('version')=='oak-growth-0.5.0':
        from .oak_periphery_contract import validate_preset as validate_v5
        return validate_v5(p)
    if p.get('version')=='oak-growth-0.4.0':
        from .oak_volume_contract import validate_preset as validate_v4
        return validate_v4(p)
    if p.get('version')=='oak-growth-0.3.0':
        from .oak_branching_contract import validate_preset as validate_v3
        return validate_v3(p)
    return validate_preset(p) if p.get('version')==VERSION else validate_v1(p)
