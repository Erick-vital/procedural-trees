#!/usr/bin/env python3
"""Empaquetar el piloto T3 desde datos T1 y atlas T2, sin regenerar geometría."""
import argparse
import json
from pathlib import Path
import shutil
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'src'),str(ROOT/'scripts')]
from build_season_atlas import sha,write
from treegen.season_transition import VERSION,validate_profile
from treegen.seasonal_paint import replace_foliage,audit
from treegen.season_calendar import validate_calendar


def build(output,calendar_source=ROOT/'artifacts/estaciones/calendario-t01-03'):
    profile_path=ROOT/'configs/seasons/roble-mezcla-v1.json'
    profile=validate_profile(json.loads(profile_path.read_text()))
    previous=json.loads((calendar_source/'verification.json').read_text())
    if not previous['passed']:raise ValueError('T1 sin verificación válida')
    folder=calendar_source/'pilot'
    for name in ('tree.glb','calendar.json','binding.json'):
        if sha(folder/name)!=previous['artifact_lock']['pilot/'+name]:raise ValueError('Piloto T1 alterado')
    calendar=validate_calendar(json.loads((folder/'calendar.json').read_text()))
    if calendar['seed']!=1101 or len(calendar['groups'])!=264:raise ValueError('Calendario piloto distinto')
    raw=(folder/'tree.glb').read_bytes();png=(ROOT/profile['resources']['summer']['path']).read_bytes()
    derived=replace_foliage(raw,png)
    output.mkdir(parents=True,exist_ok=False);project=output/'godot';project.mkdir()
    (project/'pilot.glb').write_bytes(derived)
    # Nombre usado también por la extracción glTF: una sola textura de verano.
    (project/'pilot_foliage.png').write_bytes(png)
    shutil.copy2(ROOT/profile['resources']['autumn']['path'],project/'autumn.png')
    names=['paint_transition.gdshader','paint_transition_tree.gd','paint_transition_viewer.gd',
           'review_paint_transition.gd','review_season_calendar.gd','verify_oak.gd']
    for name in names:shutil.copy2(ROOT/'godot'/name,project/name)
    old=(ROOT/'godot/seasonal_foliage.gdshader').read_text()
    assert 'ROUGHNESS = 0.88;' in old
    (project/'legacy_control.gdshader').write_text(old.replace('ROUGHNESS = 0.88;','ROUGHNESS = 0.95;'))
    shutil.copy2(ROOT/'configs/seasons/roble-otono-v1.json',project/'legacy-profile.json')
    for name in ('binding.json','calendar.json'):shutil.copy2(folder/name,project/name)
    (project/'paint_transition.tres').write_text('''[gd_resource type="ShaderMaterial" load_steps=4 format=3]
[ext_resource type="Shader" path="res://paint_transition.gdshader" id="1"]
[ext_resource type="Texture2D" path="res://pilot_foliage.png" id="2"]
[ext_resource type="Texture2D" path="res://autumn.png" id="3"]
[resource]
resource_name = "Painted_Foliage"
shader = ExtResource("1")
shader_parameter/summer_texture = ExtResource("2")
shader_parameter/autumn_texture = ExtResource("3")
''')
    (project/'pilot.tscn').write_text('''[gd_scene load_steps=3 format=3]
[ext_resource type="PackedScene" path="res://pilot.glb" id="1"]
[ext_resource type="Script" path="res://paint_transition_tree.gd" id="2"]
[node name="PaintTransitionOak" instance=ExtResource("1")]
script = ExtResource("2")
''')
    (project/'viewer.tscn').write_text('''[gd_scene load_steps=2 format=3]
[ext_resource type="Script" path="res://paint_transition_viewer.gd" id="1"]
[node name="PaintTransitionViewer" type="Node3D"]
script = ExtResource("1")
''')
    (project/'project.godot').write_text('''config_version=5
[application]
config/name="Roble · transición pintada T3"
run/main_scene="res://viewer.tscn"
[display]
window/size/viewport_width=1000
window/size/viewport_height=900
[rendering]
renderer/rendering_method="gl_compatibility"
''')
    b=previous['cases']['pilot']['metrics']['bounds_blender']
    center=[(b[0][0]+b[1][0])/2,(b[0][2]+b[1][2])/2,-(b[0][1]+b[1][1])/2]
    config={'version':VERSION,'profile':profile,'bounds_godot':{'center':center,'span':max(z-a for a,z in zip(*b))},
            'seeds':{'base':3009,'canopy':17,'paint':2718,'season':1101},'triangles':6812,'groups':264,
            'calendar_transport':'TEXCOORD_1=(start,duration)','normals':'original',
            'scope':'T3 pilot only; full canopy; artistic acceptance pending'}
    write(project/'transition-config.json',config)
    sources=[Path(__file__),ROOT/'src/treegen/season_transition.py',profile_path,ROOT/profile['atlas_manifest'],
             ROOT/'godot/seasonal_foliage.gdshader',ROOT/'configs/seasons/roble-otono-v1.json']+[ROOT/'godot'/n for n in names]
    sources += [ROOT/p['path'] for p in profile['resources'].values()]
    inputs=[folder/n for n in ('tree.glb','calendar.json','binding.json')]+[calendar_source/'verification.json']
    report={'version':VERSION,'config':config,'audit':audit(raw,derived,png),
            'repeat_glb_exact':derived==replace_foliage(raw,png),
            'source_lock':{str(p.relative_to(ROOT)):sha(p) for p in sources},
            'input_lock':{str(p.relative_to(ROOT)):sha(p) for p in inputs},
            'project_lock':{p.name:sha(p) for p in sorted(project.iterdir())}}
    write(output/'manifest.json',report)
    return report

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',required=True,type=Path)
    a=p.parse_args();build(a.output.resolve());print('Piloto T3 empaquetado.')
