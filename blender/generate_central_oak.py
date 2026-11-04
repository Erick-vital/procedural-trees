"""Adaptador1.7: OF11 aprobado, geometría derivada por el ejecutor compartido."""
import json
from pathlib import Path
import sys
import bpy
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'src'),str(ROOT/'blender')]
from treegen.pine_painted_sample import canonical_hash
from treegen.oak_crossed_production import validate_resources
from pine_painted_sample import create,render as render_painted
from oak_painted_sample import painted
from oak_crossed_trial import atlas_material
from foliage_lab import write,sha,rig,configure
from foliage_canopy_lab import export_tree,projection_clips
from generate_oak import mesh_report


def generate(job):
    r=job['resolved_blueprint'];frozen=dict(r)
    assert frozen.pop('resolved_sha256')==canonical_hash(frozen)
    assert job['spec']==r['base_spec'] and job['seeds']==r['base_seeds']
    out=Path(job['output']);data=json.loads((out/'prepared-canopy.json').read_text())
    assert canonical_hash(data)==job['prepared_geometry_sha256'] and data['resolved_sha256']==r['resolved_sha256']
    validate_resources(r['resources'])
    bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
    for mat in list(bpy.data.materials):bpy.data.materials.remove(mat)
    bark=painted('Painted_Bark','bark.png');leaf=atlas_material(ROOT/'assets/roble-pintado/v0.3.0/foliage.png');leaf.name='Painted_Foliage'
    pieces=[(m,0,m['uv']) for m in data['wood']]+[(m,1,m['uv']) for m in data['foliage']]
    obj=create('BranchSample',pieces,[bark,leaf])
    flags=[f for m,_,_ in pieces for f in m.get('smooth',[False]*len(m['polygons']))]
    for poly,flag in zip(obj.data.polygons,flags):poly.use_smooth=flag
    for im in bpy.data.images:
        if im.source=='FILE':im.pack()
    metrics=mesh_report(obj.data,triangle_limit=6999)
    assert metrics['triangles']==data['ledger']['tree_projected_triangles']
    # Exportar igual que el ensayo OF11 antes de configurar cámaras/luces.
    export_tree(obj,out)
    low,high=metrics['bounds_blender'];cameras=rig([(a+b)/2 for a,b in zip(low,high)],max(b-a for a,b in zip(low,high)),12)
    for settings in cameras.values():settings['resolution']=[480,480]
    write(out/'base-reference.json',data['structure']);write(out/'placements.json',data['groups']);write(out/'cameras.json',cameras)
    configure();scene=bpy.context.scene;scene.render.engine='CYCLES';scene.cycles.samples=4
    scene.cycles.device='CPU';scene.cycles.use_denoising=False;scene.render.threads_mode='FIXED';scene.render.threads=1
    scene.render.resolution_x=scene.render.resolution_y=480
    scene.world.use_nodes=True
    scene.world.node_tree.nodes['Background'].inputs[0].default_value=(.35,.35,.35,1)
    scene.world.node_tree.nodes['Background'].inputs[1].default_value=.35
    sun=bpy.data.objects.new('OakReviewSun',bpy.data.lights.new('OakReviewSun','SUN'))
    bpy.context.collection.objects.link(sun);sun.rotation_euler=(.45,-.5,-.5);sun.data.energy=.75
    if job['render']:render_painted(obj,out,cameras)
    sources={Path(m.__file__).resolve() for m in list(sys.modules.values()) if getattr(m,'__file__',None) and str(m.__file__).endswith('.py')}
    sources.update((ROOT/'schemas').glob('*.json'))
    manifest={'status':'completed','kind':'blueprint','adapter_version':'oak-central-blender-1.0.0',
              'spec':job['spec'],'spec_sha256':job['spec_sha256'],'resolved_blueprint':r,'base_seeds':r['base_seeds'],
              'canopy_spec':r['canopy_spec'],'paint_seed':r['paint_seed'],'seeds':job['seeds'],
              'metrics':metrics,'cameras':cameras,'projection_clips':projection_clips(obj.data,cameras),
              'group_count':216,'budget':data['ledger'],'resources':r['resources'],
              'prepared_geometry_sha256':job['prepared_geometry_sha256'],
              'blender':bpy.app.version_string,'blender_build':bpy.app.build_hash.decode(),'blender_python':sys.version,
              'runner_python':job['runner_python'],'jsonschema_version':job['jsonschema_version'],
              'sources_sha256':{str(p.relative_to(ROOT)):sha(p) for p in sorted(sources) if p.is_relative_to(ROOT)},
              'glb_sha256':sha(out/'tree.glb'),'glb_bytes':(out/'tree.glb').stat().st_size,
              'external_geometry_inputs':[],'base_generation':'O5 and OF11 derived from resolved recipe in host Python',
              'files_sha256':{name:sha(out/name) for name in ('tree.glb','tree.blend','placements.json','prepared-canopy.json')}}
    write(out/'manifest.json',manifest)

if __name__=='__main__':generate(json.loads(Path(sys.argv[sys.argv.index('--')+1]).read_text()))
