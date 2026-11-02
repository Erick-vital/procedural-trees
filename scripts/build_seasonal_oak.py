#!/usr/bin/env python3
"""Empaqueta variantes Godot otoñales sin modificar recetas ni GLB históricos."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'src'))
from treegen.seasons import VERSION, validate_profile, validate_source


def read(path):
    return json.loads(path.read_text())


def write(path, value):
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False)+'\n')


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def build(source, output, profile_path):
    profile = validate_profile(read(profile_path))
    cases = []
    for name in ('pilot', 'joven-07', 'adulto-00', 'viejo-00'):
        manifest = read(source/name/'manifest.json')
        metrics = validate_source(manifest, profile, (source/name/'tree.glb').read_bytes())
        cases.append({'id': name, 'metrics': metrics, 'seeds': manifest['seeds'],
                      'profile': manifest['resolved_blueprint']['profile'],
                      'base_glb_sha256': manifest['glb_sha256']})
    output.mkdir(parents=True, exist_ok=False)
    project = output/'godot'
    project.mkdir()
    for name in ('seasonal_tree.gd', 'seasonal_foliage.gdshader', 'seasonal_tree_viewer.gd',
                 'review_seasonal_tree.gd', 'verify_oak.gd'):
        shutil.copy2(ROOT/'godot'/name, project/name)
    write(project/'season-profile.json', profile)
    write(project/'preview-config.json', {'cases': cases})
    (project/'project.godot').write_text('config_version=5\n[application]\nconfig/name="Roble de otoño"\nrun/main_scene="res://viewer.tscn"\n[display]\nwindow/size/viewport_width=1100\nwindow/size/viewport_height=900\n[rendering]\nrenderer/rendering_method="gl_compatibility"\n')
    (project/'viewer.tscn').write_text('[gd_scene load_steps=2 format=3]\n[ext_resource type="Script" path="res://seasonal_tree_viewer.gd" id="1"]\n[node name="RobleOtono" type="Node3D"]\nscript=ExtResource("1")\n')
    for item in cases:
        name = item['id']
        shutil.copy2(source/name/'tree.glb', project/(name+'.glb'))
        (project/(name+'.tscn')).write_text('[gd_scene load_steps=3 format=3]\n[ext_resource type="PackedScene" path="res://'+name+'.glb" id="1"]\n[ext_resource type="Script" path="res://seasonal_tree.gd" id="2"]\n[node name="AutumnOak" instance=ExtResource("1")]\nscript=ExtResource("2")\n')
    sources = [ROOT/'src/treegen/seasons.py', Path(__file__), profile_path] + [ROOT/'godot'/n for n in (
        'seasonal_tree.gd', 'seasonal_foliage.gdshader', 'seasonal_tree_viewer.gd', 'review_seasonal_tree.gd')]
    result = {'version': VERSION, 'season_profile': profile, 'cases': cases,
              'source_directory': str(source), 'artistic_acceptance': 'pending',
              'format': 'Godot scene + original GLB + seasonal shader',
              'sources_sha256': {str(p.relative_to(ROOT)): sha(p) for p in sources},
              'files_sha256': {str(p.relative_to(project)): sha(p) for p in sorted(project.iterdir())}}
    write(output/'manifest.json', result)
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, default=ROOT/'artifacts/roble-pintado/integracion-madera-01')
    parser.add_argument('--profile', type=Path, default=ROOT/'configs/seasons/roble-otono-v1.json')
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    build(args.source.resolve(), args.output.resolve(), args.profile.resolve())
    print(args.output/'godot/pilot.tscn')
