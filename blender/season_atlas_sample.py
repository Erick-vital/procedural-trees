"""Extraer rama primaria 100 del piloto 2.2.0, con sus cruzadas intactas."""
import json
from pathlib import Path
import sys
import bpy
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'src'),str(ROOT/'blender')]
from treegen.oak_crossed_production import build, wood_model
from treegen.oak_painted_sample import select
from treegen.pine_painted_sample import canonical_hash
from pine_painted_sample import create
from oak_painted_sample import painted, save

source, output = map(Path,sys.argv[sys.argv.index('--')+1:])
read=lambda p:json.loads(p.read_text())
ref=read(source/'base-reference.json'); old=read(source/'reference/manifest.json'); m=read(source/'manifest.json')
wood,cards,groups,_,kept=build(ref,old,m['resolved_blueprint'])
assert canonical_hash(cards)==m['card_placements_sha256']
branches,supports,_=select(ref,old)
branch_ids={b['id'] for b in branches};support_ids={s['id'] for s in supports}
parts=[p for b,p in zip(ref['branches'],wood[:len(ref['branches'])]) if b['id'] in branch_ids]
parts += [p for s,p in zip(kept,wood[len(ref['branches']):]) if s['id'] in support_ids]
selected=[c for c in cards if c['source_support_id'] in support_ids]
parts += [(c,1,c['uv']) for c in selected]
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
bark=painted('Painted_Bark','bark.png')
leaf=painted('Painted_Foliage','foliage.png',True)
tex=next(n for n in leaf.node_tree.nodes if n.type=='TEX_IMAGE')
tex.image=bpy.data.images.load(str(ROOT/'assets/roble-pintado/v0.3.0/foliage.png'))
obj=create('PilotBranch100',parts,[bark,leaf])
_,optimized=wood_model(ref,wood,m['resolved_blueprint'])
flags=[f for b in optimized if b['id'] in branch_ids for f in b['mesh']['smooth']]
for poly,flag in zip(obj.data.polygons,flags):poly.use_smooth=flag
report=save(obj,output/'branch')
report.update(branch_id='q3:primary:100',groups=len(selected)//3,parts_sha256=canonical_hash(parts),
              cards_exact_subset=True,wood_exact_subset=True,blender=bpy.app.version_string)
(output/'branch-report.json').write_text(json.dumps(report,indent=2)+'\n')
