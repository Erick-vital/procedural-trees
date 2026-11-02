#!/usr/bin/env python3
"""T5 0.1.0: cuatro casos, extremos estándar y ejecución Godot autocontenida."""
import argparse
import json
import hashlib
from PIL import Image
from pathlib import Path
import shutil
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'src'),str(ROOT/'scripts')]
from build_season_atlas import sha,write
from treegen.season_bundle import VERSION,validate_profile,validate_portable
from treegen.season_transition import validate_profile as validate_paint
from treegen.season_calendar import build_calendar,digest
from treegen.canopy_normals import build_fields
from treegen.canopy_normals_glb import replace_normals,rows,audit_normals
from treegen.seasonal_paint import replace_foliage,audit
from treegen.evaluation import validate_glb


def build(output):
    read=lambda p:json.loads(p.read_text())
    config_path=ROOT/'configs/seasons/roble-integracion-v1.json';profile=validate_profile(read(config_path))
    paint=validate_paint(read(ROOT/profile['paint_profile']));matrix=read(ROOT/profile['matrix'])
    t1=ROOT/'artifacts/estaciones/calendario-t01-03';previous=read(t1/'verification.json')
    if not previous['passed']:raise ValueError('T1 no verificada')
    output.mkdir(parents=True,exist_ok=False);portable=output/'portable';project=output/'godot'
    for p in (portable,project,portable/'resources',portable/'cases',project/'runtime',project/'static',project/'data',project/'resources',output/'expected'):p.mkdir()
    inputs=[config_path,ROOT/profile['normal_approval'],ROOT/'docs/evidence/estaciones/mezcla-t3/user-acceptance.json',t1/'verification.json',ROOT/profile['matrix'],ROOT/profile['blueprint'],ROOT/profile['calendar_profile'],ROOT/profile['paint_profile'],ROOT/paint['atlas_manifest']]
    for season in ('summer','autumn','bark'):
        src=ROOT/paint['resources'][season]['path'];inputs.append(src)
        for base in (portable,project):shutil.copy2(src,base/'resources'/(season+'.png'))
    names=['season_bundle_tree.gd','season_bundle_viewer.gd','season_bundle_scene.gd','review_season_bundle.gd','review_season_bundle_resources.gd',
           'paint_transition.gdshader','review_season_calendar.gd','verify_oak.gd']
    for name in names:shutil.copy2(ROOT/'godot'/name,project/name)
    # Se conserva el shader histórico como control, igualando solo rugosidad.
    legacy=ROOT/'godot/seasonal_foliage.gdshader'
    (project/'legacy_control.gdshader').write_text(legacy.read_text().replace('ROUGHNESS = 0.88;','ROUGHNESS = 0.95;'))
    shutil.copy2(ROOT/'configs/seasons/roble-otono-v1.json',project/'legacy-profile.json');inputs.extend([legacy,ROOT/'configs/seasons/roble-otono-v1.json'])
    (project/'paint_transition.tres').write_text('''[gd_resource type="ShaderMaterial" load_steps=4 format=3]
[ext_resource type="Shader" path="res://paint_transition.gdshader" id="1"]
[ext_resource type="Texture2D" path="res://resources/summer.png" id="2"]
[ext_resource type="Texture2D" path="res://resources/autumn.png" id="3"]
[resource]
resource_name="Painted_Foliage"
shader=ExtResource("1")
shader_parameter/summer_texture=ExtResource("2")
shader_parameter/autumn_texture=ExtResource("3")
''')
    (project/'bark.tres').write_text('''[gd_resource type="StandardMaterial3D" load_steps=2 format=3]
[ext_resource type="Texture2D" path="res://resources/bark.png" id="1"]
[resource]
resource_name="Painted_Bark"
cull_mode=2
roughness=0.95
texture_filter=3
albedo_texture=ExtResource("1")
''')
    cases=[];audits={};blender=[]
    for item,triangles in zip(matrix['cases'],[6812,3132,5820,6900]):
        name=item['id'];source=t1/name
        for f in ('tree.glb','binding.json','volumes.json','calendar.json'):
            p=source/f
            if sha(p)!=previous['artifact_lock'][name+'/'+f]:raise ValueError('Entrada T1 alterada')
            inputs.append(p)
        binding=read(source/'binding.json');volumes=read(source/'volumes.json');calendar=read(source/'calendar.json')
        if build_calendar(volumes,read(ROOT/profile['calendar_profile']))!=calendar:raise ValueError('Calendario no repetible')
        fields=build_fields(volumes,calendar);raw=(source/'tree.glb').read_bytes()
        owners={tuple(r['position'])+tuple(r['uv']):r['group_id'] for r in binding}
        schedules={tuple(r['position'])+tuple(r['uv']):r['calendar'] for r in binding}
        folder=portable/'cases'/name;folder.mkdir();data=project/'data'/name;data.mkdir()
        for base in (folder,data):
            write(base/'calendar.json',calendar);write(base/'binding.json',binding);write(base/'fields.json',fields)
        original_manifest=ROOT/'artifacts/roble-pintado/integracion-madera-01'/name/'manifest.json';inputs.append(original_manifest)
        original=read(original_manifest);exports={};metrics={};selected_report=None
        for normal_kind,strength in [('original',0.0),('selected',profile['normal_strength'])]:
            normal_raw,normal_report=replace_normals(raw,binding,fields,strength)
            if normal_raw!=replace_normals(raw,list(reversed(binding)),fields,strength)[0]:raise ValueError('Normales no repetibles')
            expected=[{**row,'group_id':owners[tuple(row['position'])+tuple(row['uv'])],'calendar':schedules[tuple(row['position'])+tuple(row['uv'])]} for row in rows(normal_raw)]
            write(data/(normal_kind+'-normals.json'),expected);write(output/'expected'/(name+'-'+normal_kind+'.json'),expected)
            for season in ('summer','autumn'):
                png=(portable/'resources'/(season+'.png')).read_bytes();derived=replace_foliage(normal_raw,png)
                if replace_foliage(normal_raw,png)!=derived:raise ValueError('Extremo no repetible')
                path=folder/(season+'-'+normal_kind+'.glb');path.write_bytes(derived)
                metrics=validate_glb(path,original['resolved_blueprint']['base_spec'],triangle_limit=6999,height_materials={'Painted_Bark'})
                if metrics['triangles']!=triangles or len(metrics['materials'])!=2:raise ValueError('Presupuesto distinto')
                audits[name+'-'+normal_kind+'-'+season]={'normals':normal_report,'paint':audit(normal_raw,derived,png),'validation':metrics}
                key=season+'-'+normal_kind;exports[key]=str(path.relative_to(portable))
                shutil.copy2(path,project/'static'/(name+'-'+key+'.glb'))
                blender.append({'id':name+'-'+key,'glb':str(project/'static'/(name+'-'+key+'.glb')),'expected':str(output/'expected'/(name+'-'+normal_kind+'.json')),
                                'triangles':triangles,'groups':264,'roundtrip':str(project/'static'/('roundtrip-'+name+'-'+key+'.glb'))})
            shutil.copy2(folder/('summer-'+normal_kind+'.glb'),project/'runtime'/(name+'-'+normal_kind+'.glb'))
            (project/(name+'-'+normal_kind+'.tscn')).write_text('[gd_scene load_steps=3 format=3]\n[ext_resource type="PackedScene" path="res://runtime/'+name+'-'+normal_kind+'.glb" id="1"]\n[ext_resource type="Script" path="res://season_bundle_tree.gd" id="2"]\n[node name="SeasonBundleOak" instance=ExtResource("1")]\nscript=ExtResource("2")\n')
            if normal_kind=='selected':selected_report=normal_report
        if name=='pilot':
            approved=ROOT/'artifacts/estaciones/normales-t4-06/godot/pilot-n35-summer.glb';inputs.append(approved)
            if (folder/'summer-selected.glb').read_bytes()!=approved.read_bytes():raise ValueError('Piloto distinto de .35 aprobada')
        bounds=metrics['bounds_gltf'];center=[(a+b)/2 for a,b in zip(*bounds)]
        cases.append({'id':name,'triangles':triangles,'materials':2,'groups':264,'planes':792,'seeds':{**item['instance']['seeds'],'season':calendar['seed']},
                      'bounds':{'center':center,'span':max(b-a for a,b in zip(*bounds))},'exports':exports,
                      'calendar':'cases/'+name+'/calendar.json','fields':'cases/'+name+'/fields.json','binding':'cases/'+name+'/binding.json',
                      'calendar_sha256':digest(calendar),'fields_sha256':digest(fields),'normal_max_angle_deg':selected_report['max_angle_deg']})
    info={'version':VERSION,'profile':profile,'cases':cases,'normal_selection':'.35 selected; originals preserved as controls',
          'phase_portability':'Static endpoints are standard GLB. Animated group mix requires Godot adapter. Intermediate static export is not implemented.',
          'memory_estimate_rgba8_bytes':{'two_foliage_atlases_base':32000000,'two_foliage_atlases_mips':42665712,'all_three_textures_base':38290064,'all_three_textures_mips':51049784},
          'foliage_samples_per_fragment_evaluation':2,'status':'candidate_four_case_review_pending'}
    info['resource_pixels_sha256']={name:hashlib.sha256(Image.open(portable/'resources'/(name+'.png')).convert('RGBA').tobytes()).hexdigest() for name in ('summer','autumn','bark')}
    info['files_sha256']={str(p.relative_to(portable)):sha(p) for p in sorted(portable.rglob('*')) if p.is_file()}
    write(portable/'manifest.json',info);validate_portable(portable)
    write(project/'bundle-config.json',info)
    (portable/'README.txt').write_text('T5 0.1.0: extremos verano/otoño con normales seleccionadas .35 y originales.\nCada GLB lleva dos PNG embebidos y material estándar. UV2 reservado al calendario.\nLa mezcla por grupo necesita el proyecto Godot adjunto; no hay exportación estática de fases intermedias.\nNo se sustituye la receta roble 2.2.0 ni sus alias históricos.\n')
    # Registrar también la guía del paquete portable.
    info['files_sha256']['README.txt']=sha(portable/'README.txt');write(portable/'manifest.json',info);write(project/'bundle-config.json',info)
    (project/'viewer.tscn').write_text('[gd_scene load_steps=2 format=3]\n[ext_resource type="Script" path="res://season_bundle_viewer.gd" id="1"]\n[node name="SeasonBundleViewer" type="Node3D"]\nscript=ExtResource("1")\n')
    (project/'project.godot').write_text('config_version=5\n[application]\nconfig/name="Roble · integración estacional T5"\nrun/main_scene="res://viewer.tscn"\n[display]\nwindow/size/viewport_width=1000\nwindow/size/viewport_height=900\n[rendering]\nrenderer/rendering_method="gl_compatibility"\n')
    write(output/'blender-input.json',{'cases':blender,'report':str(output/'blender-report.json')})
    source_paths=[Path(__file__),ROOT/'src/treegen/season_bundle.py',ROOT/'src/treegen/canopy_normals.py',ROOT/'src/treegen/canopy_normals_glb.py',ROOT/'src/treegen/season_calendar.py',ROOT/'src/treegen/seasonal_paint.py',ROOT/'blender/verify_canopy_normals.py']+[ROOT/'godot'/n for n in names]
    manifest={'version':VERSION,'bundle':info,'audits':audits,'source_lock':{str(p.relative_to(ROOT)):sha(p) for p in source_paths},
              'input_lock':{str(p.relative_to(ROOT)):sha(p) for p in inputs},
              'project_lock':{str(p.relative_to(project)):sha(p) for p in sorted(project.rglob('*')) if p.is_file()},
              'portable_manifest_sha256':sha(portable/'manifest.json')}
    write(output/'manifest.json',manifest)
    return manifest

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',required=True,type=Path);a=p.parse_args();build(a.output.resolve())
