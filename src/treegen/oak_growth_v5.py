"""O5: ocupar periferia con la geometría O4 y scaffold protegido."""
import copy
from .oak_periphery_contract import VERSION,validate_preset
from .oak_growth_v4 import generate as previous
from .oak_growth import assign_radii
from .oak_growth_joins import fit_root_rings
from .oak_periphery import redistribute


def generate(preset,seed,*,max_order=4,spatial=True):
    p=validate_preset(preset)
    s=previous({**p,'version':'oak-growth-0.4.0'},seed,max_order=max_order,spatial=spatial)
    protected={b['id']:copy.deepcopy(b) for b in s['branches'] if b['order']<=1}
    s['version']=VERSION;s['preset']=p
    if max_order>=2:
        s['periphery']=redistribute(s)
        assign_radii(s['branches'],p)
        for b in s['branches']:
            if b['id'] in protected:
                b['radii']=protected[b['id']]['radii']
                b['join_radius_scale']=protected[b['id']].get('join_radius_scale',1.)
        fit_root_rings(s['branches'])
        for b in s['branches']:
            if b['id'] in protected:
                saved=protected[b['id']]
                b.clear();b.update(saved)
    else:s['periphery']={'tested_candidates':0,'accepted_subtrees':0,'subtrees':[]}
    return s
