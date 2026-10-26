"""Adaptador PP4: usa ejecutor común, geometría cruzada y materiales PP2/PP3."""
import json
import sys
import time
from pathlib import Path
import bpy
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'src'),str(ROOT/'blender')]
from treegen.pine_painted_sample import canonical_hash
from treegen.pine_painted import build, validate_resources, check_parameters
from pine_painted_sample import create, painted, bark_uv, render as render_painted
from foliage_lab import write, sha, rig, configure
from foliage_canopy_lab import export_tree, projection_clips
from generate_oak import mesh_report


def generate(job):
    started=time.monotonic();r=job['resolved_blueprint'];frozen=dict(r)
    assert frozen.pop('resolved_sha256')==canonical_hash(frozen)
    validate_resources(r['resources'])
    assert check_parameters(r['parameters'],r['limits'],representation=r['blueprint_definition']['components']['representation'])==r['budget_upper_bound']
    assert job['spec']==r['base_spec'] and job['seeds']==r['base_seeds']
    assert job['spec_sha256']==canonical_hash(job['spec'])
    out=Path(job['output'])
    bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
    for mat in list(bpy.data.materials):bpy.data.materials.remove(mat)
    branches,wood,groups=build(r)
    bark=painted('Painted_Bark','bark.png');leaf=painted('Painted_Foliage','foliage.png',True)
    pieces=[(b['mesh'],0,b.get('uv') or bark_uv(b)) for b in wood]+[(g,1,g['uv']) for g in groups]
    obj=create('PaintedPine',pieces,[bark,leaf]);mesh=obj.data
    metrics=mesh_report(mesh,triangle_limit=r['limits']['triangles'])
    assert metrics['triangles']<=r['budget_upper_bound']['triangles_max']
    if r['blueprint_definition']['components']['representation'] not in ('pine-painted-crossed@0.3.0','pine-painted-crossed@0.4.0'):
        assert metrics['triangles']==r['budget_upper_bound']['triangles_max']
    assert abs(metrics['height_m']-12)<.0001
    assert metrics['triangles']<11924
    lo,hi=metrics['bounds_blender'];center=[(a+b)/2 for a,b in zip(lo,hi)]
    cameras=rig(center,max(b-a for a,b in zip(lo,hi)),metrics['height_m'])
    for settings in cameras.values():settings['resolution']=[480,480]
    wood_data=[b['mesh'] for b in wood]
    ref={'version':'pine-painted-reference-0.1.0','branches':branches,'retained_ids':[b['id'] for b in wood],
         'retained_wood_sha256':canonical_hash(wood_data),'wood_triangles':sum(len(b['mesh']['polygons']) for b in wood),
         'wood_optimization':{b['id']:b['wood_optimization'] for b in wood if 'wood_optimization' in b},
         'height_m':metrics['height_m'],'cameras':cameras}
    write(out/'base-reference.json',ref);write(out/'cameras.json',cameras)
    write(out/'placements.json',groups)
    configure()
    # Guardar también una escena editable que muestre la pintura real.
    scene=bpy.context.scene;scene.render.engine='CYCLES';scene.cycles.samples=4
    scene.cycles.device='CPU';scene.cycles.use_denoising=False
    scene.render.use_persistent_data=True
    scene.render.resolution_x=scene.render.resolution_y=480
    scene.render.threads_mode='FIXED';scene.render.threads=4
    scene.world.use_nodes=True
    scene.world.node_tree.nodes['Background'].inputs[0].default_value=(.35,.35,.35,1)
    scene.world.node_tree.nodes['Background'].inputs[1].default_value=.7
    sun=bpy.data.objects.new('PaintedReviewSun',bpy.data.lights.new('PaintedReviewSun','SUN'))
    bpy.context.collection.objects.link(sun);sun.rotation_euler=(.45,-.5,-.5);sun.data.energy=2
    if job['render']:render_painted(obj,out,cameras)
    for im in bpy.data.images:
        if im.source=='FILE':im.pack()
    export_tree(obj,out)
    wood_obj=create('PaintedWood',pieces[:len(wood)],[bark])
    write(out/'wood-metrics.json',mesh_report(wood_obj.data))
    bpy.ops.object.select_all(action='DESELECT');wood_obj.select_set(True);bpy.context.view_layer.objects.active=wood_obj
    bpy.ops.export_scene.gltf(filepath=str(out/'wood.glb'),export_format='GLB',use_selection=True,export_yup=True)
    sources={Path(m.__file__).resolve() for m in list(sys.modules.values()) if getattr(m,'__file__',None) and str(m.__file__).endswith('.py')}
    sources.update((ROOT/'schemas').glob('*.json'))
    manifest={'status':'completed','kind':'blueprint','adapter_version':'pine-painted-blender-0.1.0',
        'version':r['blueprint_definition']['components']['representation'].replace('@','-'),'spec':job['spec'],'spec_sha256':job['spec_sha256'],
        'seeds':job['seeds'],'base_seeds':r['base_seeds'],'canopy_spec':r['canopy_spec'],
        'resolved_blueprint':r,'metrics':metrics,'cameras':cameras,'projection_clips':projection_clips(mesh,cameras),
        'wood_sha256':canonical_hash(wood_data),'branch_count':len(wood),'group_count':len(groups),'leaf_count':0,
        'placements_sha256':canonical_hash(groups),'paint_seed':r['paint_seed'],'resources':r['resources'],
        'budget':r['budget_upper_bound'],'external_geometry_inputs':[],'base_generation':'pine_paths_in_memory',
        'runner_python':job['runner_python'],'jsonschema_version':job['jsonschema_version'],
        'blender':bpy.app.version_string,'blender_build':bpy.app.build_hash.decode(),'blender_python':sys.version,
        'sources_sha256':{str(p.relative_to(ROOT)):sha(p) for p in sorted(sources) if p.is_relative_to(ROOT)},
        'glb_sha256':sha(out/'tree.glb'),'glb_bytes':(out/'tree.glb').stat().st_size,
        'generation_before_finalize_s':time.monotonic()-started,
        'files_sha256':{n:sha(out/n) for n in ('tree.glb','tree.blend','placements.json')}}
    write(out/'manifest.json',manifest)

if __name__=='__main__':
    assert bpy.app.version[:3]==(5,2,1)
    generate(json.loads(Path(sys.argv[sys.argv.index('--')+1]).read_text()))
