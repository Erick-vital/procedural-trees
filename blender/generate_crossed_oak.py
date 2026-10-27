"""Ejecutor de roble cruzado registrado; misma base RF3 y recursos aprobados."""
import copy
import json
from pathlib import Path
import shutil
import sys
import time
import bpy
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'src'),str(ROOT/'blender')]
from treegen.oak_crossed_production import build,validate_resources,optimized_wood,wood_model
from treegen.pine_painted_sample import canonical_hash
from generate_blueprint import generate as historical_generate
from oak_painted_sample import painted
from oak_crossed_trial import atlas_material
from pine_painted_sample import create
from generate_oak import mesh_report
from foliage_canopy_lab import export_tree,projection_clips
from foliage_lab import write,sha,configure,render


def generate(job):
    started=time.monotonic();r=job['resolved_blueprint'];out=Path(job['output']);frozen=copy.deepcopy(r)
    assert frozen.pop('resolved_sha256')==canonical_hash(frozen);validate_resources(r['resources'])
    source_job=copy.deepcopy(job);source_job['resolved_blueprint']=r['source_resolved_blueprint'];source_job['render']=False
    historical_generate(source_job)
    old=json.loads((out/'manifest.json').read_text());ref=json.loads((out/'base-reference.json').read_text())
    (out/'reference').mkdir()
    for name in ('manifest.json','tree.glb'):shutil.copy2(out/name,out/'reference'/name)
    wood,crossed,items,assignments,kept=build(ref,old,r)
    bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
    for mat in list(bpy.data.materials):bpy.data.materials.remove(mat)
    bark=painted('Painted_Bark','bark.png');leaf=atlas_material(ROOT/r['resources']['foliage']['path']);leaf.name='Painted_Foliage'
    obj=create('PaintedOakCrossed',wood+[(p,1,p['uv']) for p in crossed],[bark,leaf])
    flags=([f for mesh,_,_ in wood for f in mesh.get('smooth',[False]*len(mesh['polygons']))] if optimized_wood(r)
           else [f for b in ref['branches'] for f in b['mesh']['smooth']])
    for polygon,flag in zip(obj.data.polygons,flags):polygon.use_smooth=flag
    metrics=mesh_report(obj.data,triangle_limit=r['limits']['triangles'])
    assert metrics['triangles']<=r['budget_upper_bound']['triangles_max']
    assert metrics['triangles']==sum(len(f)-2 for mesh,_,_ in wood for f in mesh['polygons'])+6*len(items)
    configure()
    if job['render']:render(obj,out,ref['cameras'])
    for image in bpy.data.images:
        if image.source=='FILE':image.pack()
    export_tree(obj,out);write(out/'placements.json',crossed)
    sources={Path(m.__file__).resolve() for m in list(sys.modules.values()) if getattr(m,'__file__',None) and str(m.__file__).endswith('.py')}
    manifest={**old,'kind':'blueprint','version':'oak-painted-crossed-0.1.0','adapter_version':'oak-crossed-blender-0.1.0',
        'resolved_blueprint':r,'spec':job['spec'],'spec_sha256':job['spec_sha256'],'seeds':job['seeds'],
        'runner_python':job['runner_python'],'jsonschema_version':job['jsonschema_version'],'metrics':metrics,'budget':r['budget_upper_bound'],
        'resources':r['resources'],'paint_seed':r['paint_seed'],'reference_glb_sha256':old['glb_sha256'],'reference_metrics':old['metrics'],
        'assignments':assignments,'kept_support_ids':[s['id'] for s in kept],'removed_support_ids':[s['id'] for s in old['supports'] if s not in kept],
        'groups_sha256':canonical_hash([{k:v for k,v in g.items() if k not in ('source_cards','descriptor')} for g in items]),
        'card_placements_sha256':canonical_hash(crossed),'projection_clips':projection_clips(obj.data,ref['cameras']),
        'sources_sha256':{str(p.relative_to(ROOT)):sha(p) for p in sources if p.is_relative_to(ROOT)},
        'glb_sha256':sha(out/'tree.glb'),'glb_bytes':(out/'tree.glb').stat().st_size,'generation_before_render_export_s':time.monotonic()-started,
        'files_sha256':{name:sha(out/name) for name in ('tree.glb','tree.blend','placements.json')}}
    if optimized_wood(r):
        _,branches=wood_model(ref,wood,r)
        manifest.update(version='oak-painted-crossed-0.2.0',adapter_version='oak-crossed-blender-0.2.0',
                        wood_optimization=[dict(id=b['id'],**b['optimization']) for b in branches])
    write(out/'manifest.json',manifest)


if __name__=='__main__':generate(json.loads(Path(sys.argv[sys.argv.index('--')+1]).read_text()))
