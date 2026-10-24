"""Diagnostica contactos de un trabajo B3 fallido sin mallar ni exportar un éxito."""
import json
from pathlib import Path
import sys
from mathutils import Vector
from mathutils.bvhtree import BVHTree

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / 'src'), str(ROOT / 'blender')]
from treegen.foliage_canopy import profile_molds, sample_exposed, select_canopy
from foliage_molds_lab import callbacks

folder = Path(sys.argv[sys.argv.index('--') + 1]).resolve()
ref = json.loads((folder / 'base-reference.json').read_text())
resolved = json.loads((folder / 'input.json').read_text())['resolved_blueprint']
spec = resolved['canopy_spec']
guides = profile_molds(spec, ref['molds'], ref['profile_center_m'])
exposed, _, surface = callbacks(ref, guides)
pool, _ = sample_exposed(spec, guides, ref['profile_center_m'], exposed)
carriers, _, _ = select_canopy(spec, pool, surface, ref['height_m'],
                              layout_leaf_length_m=resolved['layout_leaf_length_m'])
bvh = BVHTree.FromPolygons(ref['wood_mesh']['vertices'], ref['wood_mesh']['polygons'])
errors, failed = [], []
for carrier in carriers:
    distance = bvh.find_nearest(Vector(carrier['points_m'][0]))[3]
    errors.append(distance)
    if distance >= .0001:
        failed.append({'id': carrier['id'], 'parent': carrier['parent_branch_id'],
                       'distance_m': distance, 'insertion': carrier['points_m'][0]})
(folder / 'contact-diagnostic.json').write_text(json.dumps({
    'carriers': len(carriers), 'failed': failed, 'max_error_m': max(errors),
    'tolerance_m': .0001, 'diagnostic_only': True}, indent=2) + '\n')
print(f'{len(failed)} contactos fuera de tolerancia; máximo {max(errors)} m')
