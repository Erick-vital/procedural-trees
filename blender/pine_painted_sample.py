"""PP2: rama original y muestras texturizadas; adaptador aislado del ejecutor."""
import sys
import json
import math
from pathlib import Path
import bpy
from mathutils import Vector

ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'src'),str(ROOT/'blender')]
from treegen.pine_painted_sample import canonical_hash
from treegen.pine_painted_sample import select, sample_panels, VERSION
from generate_oak import mesh_report, material
from foliage_lab import rig, sha, write

ASSETS=ROOT/'assets/pino-pintado/v0.1.0'


def painted(name, filename, alpha=False):
    mat=bpy.data.materials.new(name);mat.use_nodes=True
    bsdf=mat.node_tree.nodes.get('Principled BSDF')
    bsdf.inputs['Roughness'].default_value=.95
    image=bpy.data.images.load(str(ASSETS/filename),check_existing=True)
    assert max(image.size)<=2048
    tex=mat.node_tree.nodes.new('ShaderNodeTexImage');tex.image=image
    mat.node_tree.links.new(tex.outputs['Color'],bsdf.inputs['Base Color'])
    if alpha:
        # Se exporta como MASK; umbral explícito independiente de luces.
        threshold=mat.node_tree.nodes.new('ShaderNodeMath');threshold.operation='GREATER_THAN'
        threshold.inputs[1].default_value=.5
        mat.node_tree.links.new(tex.outputs['Alpha'],threshold.inputs[0])
        mat.node_tree.links.new(threshold.outputs[0],bsdf.inputs['Alpha'])
        mat.surface_render_method='DITHERED'
        mat.alpha_threshold=.5
    mat.use_backface_culling=False
    return mat


def create(name, pieces, mats):
    vertices=[];faces=[];uvs=[];indices=[]
    for mesh,channel,uv in pieces:
        offset=len(vertices);vertices.extend(mesh['vertices'])
        faces.extend([[offset+i for i in f] for f in mesh['polygons']])
        uvs.extend(uv);indices.extend([channel]*len(mesh['polygons']))
    mesh=bpy.data.meshes.new(name);mesh.from_pydata(vertices,[],faces);mesh.update()
    for mat in mats:mesh.materials.append(mat)
    layer=mesh.uv_layers.new(name='UVMap')
    for p,channel in zip(mesh.polygons,indices):
        p.material_index=channel
        face_uv=[uvs[mesh.loops[i].vertex_index][:] for i in p.loop_indices]
        if name != 'Original' and channel == 0 and max(uv[0] for uv in face_uv)-min(uv[0] for uv in face_uv) > .5:
            for uv in face_uv:
                if uv[0] == 0: uv[0]=1
        for loop,uv in zip(p.loop_indices,face_uv):layer.data[loop].uv=uv
    obj=bpy.data.objects.new(name,mesh);bpy.context.collection.objects.link(obj)
    return obj


def bark_uv(branch):
    # Misma conectividad/radios originales. U por perímetro; V por longitud.
    mesh=branch['mesh'];points=branch['points_m'];sides=len(mesh['vertices'])//len(points)
    lengths=[0]
    for a,b in zip(points,points[1:]):lengths.append(lengths[-1]+math.dist(a,b))
    return [[(i%sides)/sides,lengths[i//sides]/.8] for i in range(len(mesh['vertices']))]


def render(obj,folder,cameras):
    scene=bpy.context.scene
    for ob in scene.objects:
        if ob.type=='MESH':ob.hide_render=ob!=obj
    camera=bpy.data.objects.new('ReviewCamera',bpy.data.cameras.new('ReviewCamera'))
    bpy.context.collection.objects.link(camera);scene.camera=camera;camera.data.type='ORTHO'
    for name,c in cameras.items():
        camera.location=c['location'];camera.rotation_euler=c['rotation_euler'];camera.data.ortho_scale=c['ortho_scale']
        scene.render.filepath=str(folder/(name+'.png'));bpy.ops.render.render(write_still=True)
    bpy.data.objects.remove(camera,do_unlink=True)


def main(out, resolved, no_render=False):
    out.mkdir(parents=True,exist_ok=False)
    bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
    branches,needles,lock=select(resolved)
    # Escribir el contrato antes de construir las alternativas.
    lo,hi=lock['original_bounds_m'];center=Vector([(a+b)/2 for a,b in zip(lo,hi)]);span=max(b-a for a,b in zip(lo,hi))
    protocol=json.loads((ROOT/'docs/evidence/pino-pintado/pp1/review-config.json').read_text())
    cameras=rig(center,span)
    directions=protocol['branch']['views_direction_from_target']
    directions['end_on']=lock['end_on_direction']
    cameras={}
    for name,d in directions.items():
        position=center+Vector(d).normalized()*span*3
        rotation=(center-position).to_track_quat('-Z','Y').to_euler()
        cameras[name]={'location':list(position),'rotation_euler':list(rotation),'ortho_scale':span*1.3,
                       'basis_columns':[list(c) for c in rotation.to_matrix().col]}
    cameras['scale_check']={**cameras['three_quarter'],'ortho_scale':span*2.6}
    lock['cameras']=cameras;write(out/'reference-lock.json',lock)
    bark=painted('Painted_Bark','bark.png');leaf=painted('Painted_Foliage','foliage.png',True)
    old_bark=material('Original_Bark',resolved['appearance']['bark']['color_rgba'][:3])
    old_leaf=material('Original_Needles',resolved['appearance']['leaf']['color_rgba'][:3])
    original=[(b['mesh'],0,[[0,0]]*len(b['mesh']['vertices'])) for b in branches]
    original += [({'vertices':n['vertices'],'polygons':n['triangles']},1,[[0,0]]*len(n['vertices'])) for n in needles]
    objects={'original':create('Original',original,[old_bark,old_leaf])}
    placements={}
    for mode in ('folded','crossed'):
        groups=sample_panels(branches,mode);placements[mode]=groups
        pieces=[(branches[0]['mesh'],0,bark_uv(branches[0]))]+[(g,1,g['uv']) for g in groups]
        objects[mode]=create(mode,pieces,[bark,leaf])
    scene=bpy.context.scene;scene.render.engine='CYCLES';scene.cycles.samples=16
    scene.cycles.device='CPU';scene.render.threads_mode='FIXED';scene.render.threads=4
    scene.render.resolution_x=scene.render.resolution_y=900;scene.render.resolution_percentage=100
    scene.render.image_settings.file_format='PNG'
    scene.view_settings.view_transform='Standard';scene.view_settings.look='None';scene.view_settings.exposure=0
    world=bpy.data.worlds.new('ReviewWorld');scene.world=world;world.use_nodes=True
    world.node_tree.nodes['Background'].inputs[0].default_value=(.35,.35,.35,1)
    world.node_tree.nodes['Background'].inputs[1].default_value=.7
    light=bpy.data.objects.new('ReviewSun',bpy.data.lights.new('ReviewSun','SUN'))
    bpy.context.collection.objects.link(light);light.rotation_euler=(.45,-.5,-.5);light.data.energy=2
    report={'version':VERSION,'source_lock_sha256':canonical_hash(lock),'variants':{},'textures':{},
            'blender':bpy.app.version_string,'blender_build':bpy.app.build_hash.decode(),
            'review':'Blender Cycles; no es validación Godot PP3',
            'lighting':{'sun_rotation_rad':list(light.rotation_euler),'sun_energy':2,'ambient_strength':.7,'samples':16}}
    for filename in ('foliage.png','bark.png'):
        im=bpy.data.images.load(str(ASSETS/filename),check_existing=True)
        report['textures'][filename]={'sha256':sha(ASSETS/filename),'dimensions':list(im.size),'channels':im.channels,'bytes':(ASSETS/filename).stat().st_size}
    for name,obj in objects.items():
        folder=out/name;folder.mkdir()
        metrics=mesh_report(obj.data)
        if name!='original':assert metrics['triangles']==104
        if not no_render: render(obj,folder,cameras)
        bpy.ops.object.select_all(action='DESELECT');obj.hide_set(False);obj.select_set(True);bpy.context.view_layer.objects.active=obj
        bpy.ops.export_scene.gltf(filepath=str(folder/'branch.glb'),export_format='GLB',use_selection=True,export_yup=True)
        for im in bpy.data.images:
            if im.source=='FILE':im.pack()
        bpy.ops.wm.save_as_mainfile(filepath=str(folder/'branch.blend'))
        report['variants'][name]={'metrics':metrics,'glb_sha256':sha(folder/'branch.glb'),'glb_bytes':(folder/'branch.glb').stat().st_size,
                                'placements':placements.get(name,[])}
    # Validar recursos y UV del GLB reimportado, sin tocar verificadores históricos.
    for name in objects:
        bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
        bpy.ops.import_scene.gltf(filepath=str(out/name/'branch.glb'))
        imported=[o for o in bpy.context.selected_objects if o.type=='MESH']
        count=sum(len(o.data.polygons) for o in imported)
        assert count==report['variants'][name]['metrics']['triangles']
        assert all(o.data.uv_layers for o in imported)
        report['variants'][name]['reimport_triangles']=count
    report['sources_sha256']={p:sha(ROOT/p) for p in ('src/treegen/pine_painted_sample.py','blender/pine_painted_sample.py','scripts/pine_painted_sample.py','scripts/verify_pine_painted_sample.py')}
    report['generation_resources_sha256']={p.name:sha(p) for p in ASSETS.glob('*.png')}
    report['captures']=sum(len(list((out/n).glob('*.png'))) for n in objects)
    report['passed']=True;write(out/'manifest.json',report)

if __name__=='__main__':
    args=sys.argv[sys.argv.index('--')+1:]
    main(Path(args[0]).resolve(), json.loads(Path(args[1]).read_text()), '--no-render' in args)
