"""Adaptador aislado del piloto completo; recetas históricas intactas."""
import json
from pathlib import Path
import sys
import bpy
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'src'),str(ROOT/'blender')]
from treegen.oak_painted_tree import build,VERSION
from treegen.pine_painted_sample import canonical_hash
from oak_painted_sample import painted,save,ASSETS
from pine_painted_sample import create
from foliage_lab import write,sha


def main(out):
    reference=json.loads((out/'source/base-reference.json').read_text());source=json.loads((out/'source/manifest.json').read_text())
    atlas=json.loads((ASSETS/'manifest.json').read_text());seed=2718
    for name,info in atlas['files'].items():assert sha(ASSETS/name)==info['sha256']
    pieces,cards,kept=build(reference,source,atlas,seed)
    bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
    for mat in list(bpy.data.materials):bpy.data.materials.remove(mat)
    bark=painted('Painted_Bark','bark.png');leaf=painted('Painted_Foliage','foliage.png',True)
    variants={}
    for name,parts in pieces.items():
        obj=create('PaintedOakTreePilot',parts,[bark,leaf] if name.startswith('painted') else [bark])
        for polygon,flag in zip(obj.data.polygons,[f for b in reference['branches'] for f in b['mesh']['smooth']]):polygon.use_smooth=flag
        variants[name]=save(obj,out/name)
        (out/name/'branch.glb').rename(out/name/'tree.glb');(out/name/'branch.blend').rename(out/name/'tree.blend')
        bpy.data.objects.remove(obj,do_unlink=True)
    ids={s['id'] for s in kept}
    write(out/'placements.json',cards)
    write(out/'manifest.json',{'passed':True,'version':VERSION,'scope':'Piloto completo para revisión; sin integración en recetas ni controles.',
        'source_blueprint':'roble_copa_ancha@1.2.0','seeds':source['resolved_blueprint']['instance_request']['seeds'],'paint_seed':seed,
        'source_glb_sha256':source['glb_sha256'],'source_placements_sha256':canonical_hash(source['placements']),
        'source_supports_sha256':canonical_hash(source['supports']),'cards_sha256':canonical_hash(cards),'leaf_count':len(cards),
        'kept_support_ids':[s['id'] for s in kept],'removed_support_ids':[s['id'] for s in source['supports'] if s['id'] not in ids],
        'variants':variants,'resources':atlas['files'],'blender':bpy.app.version_string,
        'sources_sha256':{str(p.relative_to(ROOT)):sha(p) for p in [Path(__file__),ROOT/'src/treegen/oak_painted_tree.py',ROOT/'src/treegen/oak_painted_sample.py']}})


if __name__=='__main__':main(Path(sys.argv[sys.argv.index('--')+1]))
