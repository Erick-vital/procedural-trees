#!/usr/bin/env python3
"""T0/T1: congelar cuatro referencias, generar calendarios y verificar UV2."""
import argparse
import copy
import json
import os
from pathlib import Path
import shutil
import sys
import time
from PIL import Image, ImageChops, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT/'src'), str(ROOT/'scripts')]
from build_seasonal_oak import read, write, sha
from review_pine_painted import run
from verify_foliage_unit import GODOT
from treegen.runner import BLENDER
from treegen.evaluation import validate_result, validate_glb
from treegen.oak_crossed_production import build as build_oak
from treegen.pine_painted_sample import canonical_hash
from treegen.seasonal_paint import replace_foliage
from treegen.season_calendar import build_calendar, validate_profile, weight, digest
from treegen.season_calendar_glb import attach_calendar, audit_transport

PROFILE = ROOT/'configs/seasons/roble-calendario-v1.json'


def binding_rows(binding):
    result = {}
    for row in binding:
        key = ','.join(str(round(v*10000)) for v in row['position']+row['uv'])
        value = {'key': key, 'position': row['position'], 'uv': row['uv'],
                 'group_id': row['group_id'], 'calendar': row['calendar']}
        if key in result and result[key] != value:
            raise ValueError('Clave importada ambigua; no redondear grupos distintos')
        result[key] = value
    return [result[k] for k in sorted(result)]


def build(source, output):
    profile = validate_profile(read(PROFILE))
    matrix = read(ROOT/'configs/verification/oak-wood-v1.json')
    output.mkdir(parents=True, exist_ok=False)
    project = output/'godot'
    for folder in (project, output/'logs', output/'captures', output/'frozen', output/'inputs'):
        folder.mkdir()
    paths = []
    for name in ('verify_oak.gd', 'review_season_calendar.gd', 'seasonal_tree.gd', 'seasonal_foliage.gdshader'):
        original = ROOT/'godot'/name
        shutil.copy2(original, project/name)
        paths.append(original)
    shader = project/'seasonal_foliage.gdshader'
    # Control derivado, explícito: no tocar el shader histórico .88.
    assert 'ROUGHNESS = 0.88;' in shader.read_text()
    shader.write_text(shader.read_text().replace('ROUGHNESS = 0.88;', 'ROUGHNESS = 0.95;'))
    shutil.copy2(ROOT/'configs/seasons/roble-otono-v1.json', project/'season-profile.json')
    (project/'project.godot').write_text('config_version=5\n[application]\nconfig/name="Roble · T0 T1"\n[display]\nwindow/size/viewport_width=900\nwindow/size/viewport_height=900\n[rendering]\nrenderer/rendering_method="gl_compatibility"\n')
    for name, resource in profile['resources'].items():
        shutil.copy2(ROOT/resource['path'], output/'frozen'/(name+'.png'))
        paths.append(ROOT/resource['path'])
    write(output/'frozen/profile.json', profile)
    protocol = {'phase': profile['phase'], 'phase_range': [0, 1], 'scope': 'T0 T1 only; no paint interpolation',
                'roughness': .95, 'cutoff': .5, 'msaa': 4, 'resolution': [900, 900],
                'background': '#EEE9DF', 'sun_rotation': [-35, -25, 0], 'sun_energy': 1.2,
                'ambient': .5, 'exposure': 1, 'tonemap': 'linear', 'normal_mode': 'original',
                'filter': 'linear mipmaps anisotropic', 'shader_control_adjustment': '.88 to .95 in derived copy',
                'views': ['front', 'side', 'perspective', 'back', 'far'],
                'alpha_note': 'Original masks retained; common-mask preparation belongs to T2.',
                'artistic_acceptance': 'pending'}
    write(output/'protocol.json', protocol)
    report = {'passed': False, 'checks': {}, 'cases': {}, 'profile': profile, 'protocol': protocol}
    for item, expected_triangles in zip(matrix['cases'], (6812, 3132, 5820, 6900)):
        started = time.monotonic()
        name = item['id']
        folder = source/name
        m = read(folder/'manifest.json')
        source_files = [folder/'manifest.json', folder/'tree.glb', folder/'placements.json',
                        folder/'base-reference.json', folder/'reference/manifest.json']
        validate_result(folder)
        if m['resolved_blueprint']['instance_request'] != item['instance'] or m['metrics']['triangles'] != expected_triangles:
            raise ValueError('Referencia distinta de la matriz congelada')
        if m['blueprint_file_sha256'] != sha(ROOT/matrix['blueprint']):
            raise ValueError('Receta histórica distinta')
        if sha(folder/'tree.glb') != m['glb_sha256']:
            raise ValueError('Hash de GLB fuente distinto')
        for resource in ('summer', 'bark'):
            old_name = 'foliage' if resource == 'summer' else resource
            if profile['resources'][resource] != m['resources'][old_name]:
                raise ValueError('Recursos base distintos del perfil')
        _, cards, items, _, _ = build_oak(read(folder/'base-reference.json'), read(folder/'reference/manifest.json'), m['resolved_blueprint'])
        checks = report['checks']
        checks[name+'-placements-exact'] = cards == read(folder/'placements.json') and canonical_hash(cards) == m['card_placements_sha256']
        checks[name+'-groups-exact'] = canonical_hash([{k: v for k, v in g.items() if k not in ('source_cards', 'descriptor')} for g in items]) == m['groups_sha256']
        groups = [{k: g[k] for k in ('id', 'center_m', 'size_m', 'axes')} for g in items]
        data = build_calendar(groups, profile)
        checks[name+'-repeat-calendar'] = data == build_calendar(list(reversed(groups)), profile)
        alternate = copy.deepcopy(profile)
        alternate['seed'] += 8191
        alt = build_calendar(groups, alternate)
        checks[name+'-seed-independent'] = data['groups'] != alt['groups'] and [g['exposure'] for g in data['groups']] == [g['exposure'] for g in alt['groups']]
        checks[name+'-curves'] = all(
            (values := [weight(p/120, r['start'], r['duration']) for p in range(121)])[0] == 0
            and values[-1] == 1 and values == sorted(values) for r in data['groups'])
        raw = (folder/'tree.glb').read_bytes()
        derived = attach_calendar(raw, cards, data)
        checks[name+'-repeat-glb'] = derived == attach_calendar(raw, list(reversed(cards)), data)
        audit = audit_transport(raw, derived, cards, data)
        binding = binding_rows(audit.pop('binding'))
        target = output/name
        target.mkdir()
        write(target/'calendar.json', data)
        write(target/'volumes.json', groups)
        write(target/'binding.json', binding)
        (target/'tree.glb').write_bytes(derived)
        validate_glb(target/'tree.glb', m['resolved_blueprint']['base_spec'], triangle_limit=6999, height_materials={'Painted_Bark'})
        for style, content in [('original', raw), ('painted', replace_foliage(raw, (ROOT/profile['resources']['autumn']['path']).read_bytes())), ('calendar', derived)]:
            (project/(style+'-'+name+'.glb')).write_bytes(content)
        (project/('shader-'+name+'.tscn')).write_text('[gd_scene load_steps=3 format=3]\n[ext_resource type="PackedScene" path="res://original-'+name+'.glb" id="1"]\n[ext_resource type="Script" path="res://seasonal_tree.gd" id="2"]\n[node name="ShaderControl" instance=ExtResource("1")]\nscript=ExtResource("2")\n')
        blender_input = {'glb': str(target/'tree.glb'), 'binding': binding, 'group_count': len(groups),
                         'triangles': expected_triangles, 'roundtrip': str(project/('roundtrip-'+name+'.glb')),
                         'report': str(target/'blender-report.json')}
        write(output/'inputs'/(name+'-blender.json'), blender_input)
        run([os.environ.get('BLENDER_BIN', BLENDER), '--background', '--factory-startup', '--threads', '2', '--python-exit-code', '1',
             '--python', ROOT/'blender/verify_season_calendar.py', '--', output/'inputs'/(name+'-blender.json')], output/'logs'/(name+'-blender.log'), os.environ)
        blender_report = read(target/'blender-report.json')
        checks[name+'-blender'] = blender_report['passed']
        config = {'id': name, 'binding': binding, 'triangles': expected_triangles, 'group_count': len(groups),
                  'output': str(output/'captures'), 'report': str(target/'godot-report.json'),
                  'assets': [{'id': style, 'resource': 'res://'+style+'-'+name+'.glb', 'calendar': style == 'calendar'} for style in ('original', 'painted', 'calendar')] +
                            [{'id': 'shader', 'resource': 'res://shader-'+name+'.tscn'},
                             {'id': 'roundtrip', 'resource': 'res://roundtrip-'+name+'.glb', 'calendar': True, 'roundtrip': True}]}
        write(output/'inputs'/(name+'-godot.json'), config)
        report['cases'][name] = {'seeds': m['seeds'], 'base_glb_sha256': m['glb_sha256'],
            'derived_glb_sha256': sha(target/'tree.glb'), 'calendar_sha256': digest(data),
            'metrics': m['metrics'], 'attribute_audit': audit, 'blender': blender_report,
            'generation_seconds': time.monotonic()-started,
            'source_files_sha256': {str(p.relative_to(ROOT)): sha(p) for p in source_files},
            'start_range': [min(g['start'] for g in data['groups']), max(g['start'] for g in data['groups'])],
            'exposure_range': [min(g['exposure'] for g in data['groups']), max(g['exposure'] for g in data['groups'])]}
        print(name+': calendario y Blender verificados', flush=True)
    paths += [p for folder in ('src/treegen', 'blender') for p in (ROOT/folder).glob('*.py')]
    paths += [PROFILE, ROOT/'configs/seasons/roble-otono-v1.json', ROOT/matrix['blueprint'],
              ROOT/'schemas/tree-season-calendar-profile.schema.json', ROOT/'schemas/tree-season-calendar-data.schema.json',
              ROOT/'configs/verification/oak-wood-v1.json', Path(__file__), ROOT/'scripts/build_seasonal_oak.py', ROOT/'scripts/review_pine_painted.py']
    report['source_lock'] = {str(p.relative_to(ROOT)): sha(p) for p in sorted(set(paths))}
    report['project_lock'] = {p.name: sha(p) for p in sorted(project.iterdir())}
    report['frozen_lock'] = {p.name: sha(p) for p in sorted((output/'frozen').iterdir())}
    locked_outputs = [output/'protocol.json']+list((output/'inputs').glob('*.json'))
    locked_outputs += [output/name/n for name in report['cases'] for n in ('calendar.json', 'volumes.json', 'binding.json', 'blender-report.json', 'tree.glb')]
    report['artifact_lock'] = {str(p.relative_to(output)): sha(p) for p in locked_outputs}
    write(output/'verification.json', report)


def review(output):
    report = read(output/'verification.json')
    for path, expected in report['source_lock'].items():
        if sha(ROOT/path) != expected:
            raise ValueError('Fuente modificada antes de revisar: '+path)
    project = output/'godot'
    for name, expected in report['project_lock'].items():
        if sha(project/name) != expected:
            raise ValueError('Paquete modificado antes de revisar: '+name)
    for name, expected in report['frozen_lock'].items():
        if sha(output/'frozen'/name) != expected:
            raise ValueError('Recurso congelado modificado: '+name)
    for name, expected in report['artifact_lock'].items():
        if sha(output/name) != expected:
            raise ValueError('Datos de revisión modificados: '+name)
    godot = os.environ.get('GODOT_BIN', GODOT)
    run([godot, '--headless', '--path', project, '--editor', '--import'], output/'logs/import.log', os.environ)
    for name, case in report['cases'].items():
        run([godot, '--path', project, '--audio-driver', 'Dummy', '--script', 'res://review_season_calendar.gd', '--',
             output/'inputs'/(name+'-godot.json')], output/'logs'/(name+'-godot.log'), os.environ)
        case['godot'] = read(output/name/'godot-report.json')
        report['checks'][name+'-godot'] = case['godot']['passed']
        report['checks'][name+'-no-visible-change'] = all(ImageChops.difference(
            Image.open(output/'captures'/f'{name}-original-{view}.png').convert('RGB'),
            Image.open(output/'captures'/f'{name}-calendar-{view}.png').convert('RGB')).getbbox() is None
            for view in report['protocol']['views'])
        print(name+': Godot verificado', flush=True)
    captures = sorted((output/'captures').glob('*.png'))
    report['checks']['80-real-captures'] = len(captures) == 80
    report['capture_sha256'] = {p.name: sha(p) for p in captures}
    report['passed'] = all(report['checks'].values())
    write(output/'verification.json', report)
    for title, views, styles in [('references', ['perspective', 'back'], ['original', 'shader', 'painted']),
                                  ('transport', ['perspective', 'far'], ['original', 'calendar'])]:
        names = list(report['cases'])
        sheet = Image.new('RGB', (450*len(styles), 480*len(names)*len(views)), '#EEE9DF')
        draw = ImageDraw.Draw(sheet)
        for row, (name, view) in enumerate((n, v) for n in names for v in views):
            for col, style in enumerate(styles):
                im = Image.open(output/'captures'/f'{name}-{style}-{view}.png').convert('RGB')
                im.thumbnail((450, 450))
                sheet.paste(im, (450*col, 480*row+30))
                draw.text((450*col+8, 480*row+8), name+' | '+style+' | '+view, fill='#29221B')
        sheet.save(output/(title+'.jpg'), quality=93)
    assert report['passed'], [k for k, v in report['checks'].items() if not v]
    print(str(len(report['checks']))+' checks; passed=True', flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--source', type=Path, default=ROOT/'artifacts/roble-pintado/integracion-madera-01')
    parser.add_argument('--stage', choices=('all', 'build', 'review'), default='all')
    args = parser.parse_args()
    if args.stage in ('all', 'build'): build(args.source.resolve(), args.output.resolve())
    if args.stage in ('all', 'review'): review(args.output.resolve())
