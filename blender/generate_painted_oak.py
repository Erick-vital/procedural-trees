"""Adaptador roble pintado: reutiliza resolución RF3 sin alterar su ruta histórica."""
import copy
import json
from pathlib import Path
import shutil
import sys
import time
import bpy
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'src'),str(ROOT/'blender')]
from treegen.oak_painted import build,validate_resources
from treegen.pine_painted_sample import canonical_hash
from generate_blueprint import generate as historical_generate,apply_material
from generate_oak import mesh_report
from pine_painted_sample import create
from foliage_branch_lab import wood_hash
from foliage_canopy_lab import export_tree,projection_clips
from foliage_lab import write,sha,render,configure


def generate(job):
    started=time.monotonic();r=job['resolved_blueprint'];out=Path(job['output'])
    frozen=copy.deepcopy(r);assert frozen.pop('resolved_sha256')==canonical_hash(frozen)
    validate_resources(r['resources'])
    source_job=copy.deepcopy(job);source_job['resolved_blueprint']=r['source_resolved_blueprint'];source_job['render']=False
    historical_generate(source_job)
    old=json.loads((out/'manifest.json').read_text());reference=json.loads((out/'base-reference.json').read_text())
    historical=out/'reference';historical.mkdir()
    for name in ('manifest.json','tree.glb','base-reference.json'):shutil.copy2(out/name,historical/name)
    wood,twigs,cards=build(reference,old['placements'],old['supports'],old['canopy_spec'],r['paint_seed'])
    bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
    for mat in list(bpy.data.materials):bpy.data.materials.remove(mat)
    bark=apply_material('Oak_Bark',r['appearance']['bark']);twig=bark.copy();twig.name='RF2_Twig'
    foliage=apply_material('Oak_Painted_Leaf',r['appearance']['leaf'])
    nodes=foliage.node_tree.nodes;bsdf=nodes.get('Principled BSDF');tex=nodes.new('ShaderNodeTexImage')
    image=bpy.data.images.load(str(ROOT/r['resources']['foliage']['path']));tex.image=image
    foliage.node_tree.links.new(tex.outputs['Color'],bsdf.inputs['Base Color'])
    threshold=nodes.new('ShaderNodeMath');threshold.operation='GREATER_THAN';threshold.inputs[1].default_value=.5
    foliage.node_tree.links.new(tex.outputs['Alpha'],threshold.inputs[0]);foliage.node_tree.links.new(threshold.outputs[0],bsdf.inputs['Alpha'])
    foliage.surface_render_method='DITHERED';foliage.alpha_threshold=.5
    pieces=[(wood,0,[[0,0]]*len(wood['vertices']))]+[(g,1,g['uv']) for g in cards]+[(t,2,[[0,0]]*len(t['vertices'])) for t in twigs]
    obj=create('PaintedOak',pieces,[bark,foliage,twig])
    # create aplica UV; conservar smooth explícito para madera histórica.
    for polygon,smooth in zip(obj.data.polygons,wood['smooth']):polygon.use_smooth=smooth
    assert wood_hash(obj.data)==old['wood_sha256']
    metrics=mesh_report(obj.data,triangle_limit=r['limits']['triangles'])
    assert metrics['triangles']==old['metrics']['triangles']-len(cards)
    assert metrics['triangles']<=r['budget_upper_bound']['triangles_max']
    write(out/'placements.json',cards)
    configure()
    if job['render']:render(obj,out,reference['cameras'])
    image.pack();export_tree(obj,out)
    sources={Path(m.__file__).resolve() for m in list(sys.modules.values()) if getattr(m,'__file__',None) and str(m.__file__).endswith('.py')}
    manifest={**old,'kind':'blueprint','version':'oak-painted-single-0.1.0','adapter_version':'oak-painted-blender-0.1.0',
        'resolved_blueprint':r,'spec':job['spec'],'spec_sha256':job['spec_sha256'],'seeds':job['seeds'],
        'runner_python':job['runner_python'],'jsonschema_version':job['jsonschema_version'],
        'metrics':metrics,'budget':r['budget_upper_bound'],'resources':r['resources'],'paint_seed':r['paint_seed'],
        'reference_glb_sha256':old['glb_sha256'],'reference_metrics':old['metrics'],
        'visible_height_m':reference['height_m'],'transparent_support_bounds_blender':metrics['bounds_blender'],
        'card_placements_sha256':canonical_hash(cards),'source_placements_sha256':old['placements_sha256'],
        'representation_triangle_count':len(cards),'projection_clips':projection_clips(obj.data,reference['cameras']),
        'sources_sha256':{str(p.relative_to(ROOT)):sha(p) for p in sources if p.is_relative_to(ROOT)},
        'glb_sha256':sha(out/'tree.glb'),'glb_bytes':(out/'tree.glb').stat().st_size,
        'generation_before_render_export_s':time.monotonic()-started,
        'files_sha256':{name:sha(out/name) for name in ('tree.glb','tree.blend','placements.json')}}
    write(out/'manifest.json',manifest)

if __name__=='__main__':
    assert bpy.app.version[:3]==(5,2,1)
    generate(json.loads(Path(sys.argv[sys.argv.index('--')+1]).read_text()))
