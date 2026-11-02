#!/usr/bin/env python3
"""T4: empaquetar dos candidatas de normales locales y originales, rama/piloto."""
import json
from pathlib import Path
import shutil
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'src'),str(ROOT/'scripts')]
from build_season_atlas import sha,write
from treegen.canopy_normals import VERSION,build_fields,digest
from treegen.canopy_normals_glb import replace_normals,rows
from treegen.seasonal_paint import replace_foliage,audit
from treegen.season_transition import validate_profile


def build(output):
    t1=ROOT/'artifacts/estaciones/calendario-t01-03';t2=ROOT/'artifacts/estaciones/atlas-t2-05';t3=ROOT/'artifacts/estaciones/mezcla-t3-04'
    read=lambda p:json.loads(p.read_text())
    previous=read(t3/'verification.json');approval=ROOT/'docs/evidence/estaciones/mezcla-t3/user-acceptance.json'
    if not previous['passed'] or read(approval)['decision']!='approved':raise ValueError('T3 no aprobado/verificado')
    if sha(t3/'godot/pilot.glb')!=previous['manifest']['project_lock']['pilot.glb']:raise ValueError('Piloto T3 alterado')
    profile=validate_profile(read(ROOT/'configs/seasons/roble-mezcla-v1.json'))
    old=read(t1/'verification.json')
    for f in ('binding.json','volumes.json','calendar.json'):
        if sha(t1/'pilot'/f)!=old['artifact_lock']['pilot/'+f]:raise ValueError('Datos T1 alterados')
    binding=read(t1/'pilot/binding.json');groups=read(t1/'pilot/volumes.json');calendar=read(t1/'pilot/calendar.json')
    fields=build_fields(groups,calendar)
    summer=(ROOT/profile['resources']['summer']['path']).read_bytes();autumn=(ROOT/profile['resources']['autumn']['path']).read_bytes()
    branch=replace_foliage((t2/'branch/branch.glb').read_bytes(),summer)
    if branch!=(t2/'branch/summer-padded.glb').read_bytes():raise ValueError('Rama T2 alterada')
    output.mkdir(parents=True,exist_ok=False);project=output/'godot';project.mkdir();expected=output/'expected';expected.mkdir()
    for name in ('verify_oak.gd','review_season_calendar.gd','review_canopy_normals.gd','canopy_normals_viewer.gd','canopy_normals_scene.gd'):
        shutil.copy2(ROOT/'godot'/name,project/name)
    shutil.copy2(ROOT/profile['resources']['summer']['path'],project/'summer.png')
    shutil.copy2(ROOT/profile['resources']['autumn']['path'],project/'autumn.png')
    (project/'project.godot').write_text('''config_version=5
[application]
config/name="Roble · ensayo de normales T4"
run/main_scene="res://viewer.tscn"
[display]
window/size/viewport_width=1000
window/size/viewport_height=900
[rendering]
renderer/rendering_method="gl_compatibility"
''')
    (project/'viewer.tscn').write_text('[gd_scene load_steps=2 format=3]\n[ext_resource type="Script" path="res://canopy_normals_viewer.gd" id="1"]\n[node name="CanopyNormalsReview" type="Node3D"]\nscript=ExtResource("1")\n')
    config={'version':VERSION,'variants':['original','n35','n65'],'scopes':['branch','pilot'],'seasons':['summer','autumn'],
            'strengths':[0,.35,.65],'max_deviation_degrees':[0,21,39],'field_sha256':digest(fields),
            'scope':'T4 only; fixed paint; no seasonal interpolation','cases':[]}
    owners={tuple(r['position'])+tuple(r['uv']):r['group_id'] for r in binding};audits={};blender=[]
    for scope,raw,triangles,group_count in [('branch',branch,696,32),('pilot',(t3/'godot/pilot.glb').read_bytes(),6812,264)]:
        for variant,strength in zip(config['variants'],config['strengths']):
            modified,report=replace_normals(raw,binding,fields,strength)
            if modified!=replace_normals(raw,list(reversed(binding)),fields,strength)[0]:raise ValueError('Repetición no exacta')
            if strength==0 and modified!=raw:raise ValueError('Original modificado')
            identifier=scope+'-'+variant
            normals=[{**row,'group_id':owners[tuple(row['position'])+tuple(row['uv'])]} for row in rows(modified)]
            write(expected/(identifier+'.json'),normals);write(project/(identifier+'-normals.json'),normals)
            audits[identifier]=report
            for season,png in [('summer',summer),('autumn',autumn)]:
                painted=replace_foliage(modified,png)
                audit(modified,painted,png)
                name=identifier+'-'+season
                (project/(name+'.glb')).write_bytes(painted)
                config['cases'].append({'id':name,'scope':scope,'variant':variant,'season':season,'triangles':triangles,'groups':group_count,'expected':identifier+'-normals.json'})
            blender.append({'id':identifier,'glb':str(project/(identifier+'-summer.glb')),'expected':str(expected/(identifier+'.json')),
                            'triangles':triangles,'groups':group_count,'roundtrip':str(project/('roundtrip-'+identifier+'.glb'))})
    write(project/'normal-review-config.json',config);write(output/'fields.json',fields)
    write(output/'blender-input.json',{'cases':blender,'report':str(output/'blender-report.json')})
    sources=[Path(__file__),ROOT/'src/treegen/canopy_normals.py',ROOT/'src/treegen/canopy_normals_glb.py',ROOT/'blender/verify_canopy_normals.py']
    sources += [ROOT/'godot'/n for n in ('verify_oak.gd','review_season_calendar.gd','review_canopy_normals.gd','canopy_normals_viewer.gd','canopy_normals_scene.gd')]
    inputs=[approval,t3/'verification.json',t3/'godot/pilot.glb',t2/'branch/branch.glb',t2/'branch/summer-padded.glb']+[t1/'pilot'/f for f in ('binding.json','volumes.json','calendar.json')]
    inputs += [ROOT/profile['resources'][k]['path'] for k in profile['resources']]+[ROOT/'configs/seasons/roble-mezcla-v1.json']
    manifest={'version':VERSION,'config':config,'audits':audits,'source_lock':{str(p.relative_to(ROOT)):sha(p) for p in sources},
              'input_lock':{str(p.relative_to(ROOT)):sha(p) for p in inputs},
              'files_sha256':{str(p.relative_to(output)):sha(p) for p in sorted(output.rglob('*')) if p.is_file() and p.name!='blender-input.json'},
              'status':'experiment_art_pending','production_normals':'original'}
    write(output/'manifest.json',manifest)
    return manifest
