"""Adaptador de ensayo, sin cambiar recetas de producción."""
import json
from pathlib import Path
import sys
import bpy

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT/'src'), str(ROOT/'blender')]
from treegen.oak_crossed_production import build as crossed_build
from treegen.oak_wood import build, VERSION
from treegen.pine_painted_sample import canonical_hash
from oak_painted_sample import painted, save
from oak_crossed_trial import atlas_material
from pine_painted_sample import create
from foliage_lab import write, sha


def main(source, out):
    reference = json.loads((source/'base-reference.json').read_text())
    historical = json.loads((source/'reference/manifest.json').read_text())
    production = json.loads((source/'manifest.json').read_text())
    wood, panels, _, _, _ = crossed_build(reference, historical, production['resolved_blueprint'])
    bpy.ops.object.select_all(action='SELECT'); bpy.ops.object.delete(use_global=False)
    for mat in list(bpy.data.materials): bpy.data.materials.remove(mat)
    bark = painted('Painted_Bark', 'bark.png')
    leaf = atlas_material(ROOT/'assets/roble-pintado/v0.3.0/foliage.png'); leaf.name='Painted_Foliage'
    report = {'version': VERSION, 'source_glb_sha256': sha(source/'tree.glb'),
              'seeds': production['seeds'], 'resources': production['resources'],
              'panels_sha256': canonical_hash(panels), 'variants': {}, 'measurements': {}}
    variants = [('before', wood, reference['branches'])]
    for label, tolerance in [('5mm', .005), ('10mm', .01), ('20mm', .02)]:
        parts, branches = build(wood, reference['branches'], tolerance)
        report['measurements'][label] = [dict(id=b['id'], **b['optimization']) for b in branches]
        if label != '5mm': variants.append((label, parts, branches))
    parts, branches = build(wood, reference['branches'], .02, secondary_only=True)
    report['measurements']['secondary20mm'] = [dict(id=b['id'], **b['optimization']) for b in branches]
    variants.append(('secondary20mm', parts, branches))
    for label, parts, branches in variants:
        for kind in ('tree', 'wood'):
            pieces = parts + ([(p,1,p['uv']) for p in panels] if kind=='tree' else [])
            obj = create('PaintedOakWoodTrial', pieces, [bark,leaf] if kind=='tree' else [bark])
            for polygon, flag in zip(obj.data.polygons, [f for b in branches for f in b['mesh']['smooth']]):
                polygon.use_smooth = flag
            name = label+'-'+kind
            report['variants'][name] = save(obj, out/name)
            bpy.data.objects.remove(obj, do_unlink=True)
    report['blender'] = bpy.app.version_string
    report['sources_sha256'] = {str(p.relative_to(ROOT)): sha(p) for p in (Path(__file__), ROOT/'src/treegen/oak_wood.py')}
    write(out/'manifest.json', report)


if __name__ == '__main__':
    args = sys.argv[sys.argv.index('--')+1:]
    main(Path(args[0]), Path(args[1]))
