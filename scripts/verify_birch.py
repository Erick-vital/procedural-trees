#!/usr/bin/env python3
"""Generar cuatro abedules, repetir, comprobar regresiones y revisar en Godot."""
import argparse
import os
from pathlib import Path
import shutil
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT/'src'), str(ROOT/'scripts')]
from treegen.runner import execute_blueprint
from treegen.evaluation import validate_result
from review_pine_painted import read, write, run, camera, sha
from verify_foliage_unit import GODOT
from foliage_evidence import sheet


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', required=True, type=Path)
    parser.add_argument('--stage', choices=['all', 'generate', 'review'], default='all')
    args = parser.parse_args()
    out = args.output.resolve()
    matrix = read(ROOT/'configs/verification/birch-v1.json')
    recipe = ROOT/matrix['blueprint']
    if args.stage in ('all', 'generate'):
        out.mkdir(parents=True, exist_ok=False)
        report = {'passed': False, 'matrix': matrix, 'cases': {}, 'checks': {}}
        checks = report['checks']
        for row in matrix['cases']:
            m = execute_blueprint(recipe, ROOT/row['instance'], out/row['id'], render=False)
            report['cases'][row['id']] = {k: m[k] for k in ('glb_sha256', 'metrics', 'duration_seconds', 'budget', 'export_validation')}
            checks[row['id']+'-export'] = validate_result(out/row['id'])['exported_anchors_and_groups_valid']
            checks[row['id']+'-budget'] = m['metrics']['triangles'] <= m['budget']['triangles_max'] < 7000 and len(m['metrics']['triangles_by_material']) == 2
            print(row['id'], m['metrics']['triangles'], 'tris', flush=True)
        repeat = execute_blueprint(recipe, ROOT/matrix['cases'][0]['instance'], out/'pilot-repeat', render=False)
        checks['repeat-identical'] = repeat['glb_sha256'] == report['cases']['pilot']['glb_sha256']
        regressions = [('oak', 'blueprints/roble_copa_ancha/2.2.0.json', 'presets/blueprints/roble-madera/pilot.json', 'docs/evidence/roble-pintado/integracion-madera-01/verification.json'),
                       ('pine', 'blueprints/pino_conico/2.3.0.json', 'presets/blueprints/pino-pintado-laminas/pilot.json', 'docs/evidence/pino-pintado/pp4-laminas/verification.json'),
                       ('columnar', 'blueprints/arbol_copa_columnar/1.0.0.json', 'presets/blueprints/columnar/pilot.json', 'docs/evidence/blueprints/b4/verification.json')]
        for name, bp, instance, evidence in regressions:
            m = execute_blueprint(ROOT/bp, ROOT/instance, out/('regression-'+name), render=False)
            checks[name+'-historical-glb-identical'] = m['glb_sha256'] == read(ROOT/evidence)['cases']['pilot']['glb_sha256']
            print('Regresión', name, checks[name+'-historical-glb-identical'], flush=True)
        files = [Path(__file__), ROOT/'configs/verification/birch-v1.json', recipe,
                 ROOT/'godot/review_birch_sample.gd', ROOT/'godot/birch_sample_viewer.gd', ROOT/'godot/birch_tree_viewer.gd', ROOT/'godot/painted_pine_asset.gd', ROOT/'godot/verify_oak.gd']
        for folder, glob in [('src/treegen', '*.py'), ('blender', '*.py'), ('schemas', '*.json'), ('assets/abedul-pintado/v0.1.0', '*')]:
            files.extend((ROOT/folder).glob(glob))
        report['source_lock'] = {str(p.relative_to(ROOT)): sha(p) for p in files if p.is_file()}
        report['passed'] = all(checks.values())
        write(out/'verification.json', report)
        assert report['passed'], [name for name, ok in checks.items() if not ok]
    if args.stage == 'generate':
        return
    report = read(out/'verification.json')
    assert all(sha(ROOT/p) == digest for p, digest in report['source_lock'].items()), 'Fuentes cambiaron entre generación y revisión'
    project, captures, logs = out/'godot', out/'captures', out/'logs'
    for folder in (project, captures, logs):
        folder.mkdir(exist_ok=False)
    for name in ('verify_oak.gd', 'review_birch_sample.gd', 'painted_pine_asset.gd', 'birch_sample_viewer.gd', 'birch_tree_viewer.gd'):
        shutil.copy2(ROOT/'godot'/name, project/name)
    (project/'project.godot').write_text('config_version=5\n[application]\nconfig/name="Abedul pintado · árbol completo"\nrun/main_scene="res://preview.tscn"\n[display]\nwindow/size/viewport_width=1200\nwindow/size/viewport_height=850\n[rendering]\nrenderer/rendering_method="gl_compatibility"\n')
    (project/'preview.tscn').write_text('[gd_scene load_steps=2 format=3]\n[ext_resource type="Script" path="res://birch_tree_viewer.gd" id="1"]\n[node name="BirchTreeReview" type="Node3D"]\nscript=ExtResource("1")\n')
    entries = []
    for row in matrix['cases']:
        for kind in ('tree', 'wood'):
            name = kind+'-'+row['id']
            shutil.copy2(out/row['id']/(kind+'.glb'), project/(name+'.glb'))
            metrics = report['cases'][row['id']]['metrics'] if kind == 'tree' else read(out/row['id']/'wood-metrics.json')
            (project/(name+'.tscn')).write_text('[gd_scene load_steps=3 format=3]\n[ext_resource type="PackedScene" path="res://'+name+'.glb" id="1"]\n[ext_resource type="Script" path="res://painted_pine_asset.gd" id="2"]\n[node name="PaintedBirch" instance=ExtResource("1")]\nscript=ExtResource("2")\n')
            entries.append({'id': name, 'resource': 'res://'+name+'.tscn', 'metrics': metrics})
    # Alias de presentación del piloto para el visor de la rama, con el mismo GLB.
    for alias, name in [('crossed', 'tree-pilot'), ('wood', 'wood-pilot')]:
        shutil.copy2(project/(name+'.glb'), project/(alias+'.glb'))
        (project/(alias+'.tscn')).write_text((project/(name+'.tscn')).read_text().replace(name+'.glb', alias+'.glb'))
    center, span = [0, 0, 5], 10
    write(project/'preview-config.json', {'center': center, 'span': span, 'triangles': report['cases']['pilot']['metrics']['triangles'],
          'cases': [{'id': row['id'], 'triangles': report['cases'][row['id']]['metrics']['triangles']} for row in matrix['cases']]})
    shots = [{'id': name, 'camera': camera(center, span, direction, scale), 'background': '#EEE9DF', 'light': [-35, -25, 0]}
             for name, direction, scale in [('front', [0, -1, .08], 12.5), ('side', [1, 0, .08], 12.5),
                 ('perspective', [1, -1, .35], 12.5), ('back', [-1, 1, .2], 12.5), ('top', [0, 0, 1], 12.5),
                 ('below', [1, -1, -.6], 12.5), ('near', [1, -1, .35], 20), ('medium', [1, -1, .35], 40), ('far', [1, -1, .35], 100)]]
    shots.append({'id': 'dark', 'camera': camera(center, span, [1, -1, .35], 12.5), 'background': '#252A28', 'light': [-35, -25, 0]})
    write(out/'protocol.json', {'center': center, 'span': span, 'shots': shots, 'resolution': [900, 900], 'sun': .75, 'ambient': .35})
    godot = os.environ.get('GODOT_BIN', GODOT)
    env = dict(os.environ, XDG_DATA_HOME=str(out/'xdg/data'), XDG_CONFIG_HOME=str(out/'xdg/config'), XDG_CACHE_HOME=str(out/'xdg/cache'))
    run([godot, '--headless', '--path', project, '--editor', '--import'], logs/'import.log', env)
    reviews = []
    for index in range(0, len(entries), 2):
        config, result = out/f'review-input-{index}.json', out/f'review-report-{index}.json'
        write(config, {'output': str(captures), 'report': str(result), 'center': center, 'span': span,
                       'original_low': [0, 0, 0], 'assets': entries[index:index+2], 'shots': shots})
        run([godot, '--path', project, '--audio-driver', 'Dummy', '--script', 'res://review_birch_sample.gd', '--', config, '--visual'], logs/f'review-{index}.log', env)
        reviews.append(read(result))
        print('Godot lote', index, 'OK', flush=True)
    report['godot'] = reviews
    report['captures'] = {p.name: sha(p) for p in sorted(captures.glob('*.png'))}
    report['checks']['godot'] = all(r['passed'] for r in reviews)
    report['checks']['80-captures'] = len(report['captures']) == 80
    report['passed'] = all(report['checks'].values())
    write(out/'verification.json', report)
    for kind in ('tree', 'wood'):
        for suffix, views in [('views', ['front', 'side', 'perspective', 'back', 'top', 'below']), ('distances', ['near', 'medium', 'far', 'dark'])]:
            sheet(out, out/f'{kind}-{suffix}.jpg', 4, [[(f'captures/{kind}-{row["id"]}--{view}.png', row['id']+' | '+view) for row in matrix['cases']] for view in views])
    cells = ''.join('<figure><img width="300" src="captures/'+name+'"><figcaption>'+name+'</figcaption></figure>' for name in report['captures'])
    (out/'index.html').write_text('<!doctype html><meta charset="utf-8"><title>Abedul · árbol completo</title><style>body{font:16px sans-serif;background:#eee9df}main{display:flex;flex-wrap:wrap}</style><h1>Abedul pintado · cuatro semillas</h1><p>Capturas reales Godot; aprobación artística del árbol pendiente.</p><main>'+cells+'</main>')
    assert report['passed']
    print('Abedul verificado, 80 capturas:', out, flush=True)


if __name__ == '__main__':
    main()
