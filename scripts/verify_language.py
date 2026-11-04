#!/usr/bin/env python3
"""F4: seis interpretaciones del chat, exportación, repetición y parejas Godot."""
import argparse
import copy
import json
import os
from pathlib import Path
import shutil
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / 'src'), str(ROOT / 'scripts')]
from treegen.language import prepare_plan, execute_plan, load_plan
from treegen.blueprints import resolve_blueprint
from treegen.runner import execute_blueprint
from treegen.evaluation import compare
from review_pine_painted import read, write, run, sha, camera
from verify_foliage_unit import GODOT
from foliage_evidence import sheet


def value(parameters, path):
    for part in path.split('.'):
        parameters = parameters[part]
    return parameters


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--output', type=Path, required=True)
    p.add_argument('--stage', choices=['all', 'generate', 'review'], default='all')
    a = p.parse_args()
    out = a.output.resolve()
    matrix = read(ROOT / 'configs/verification/f4-v1.json')
    if a.stage in ('all', 'generate'):
        out.mkdir(parents=True, exist_ok=False)
        (out / 'logs').mkdir()
        report = {'passed': False, 'matrix': matrix, 'checks': {}, 'cases': {},
                  'interpretation_origin': 'codex-current-chat', 'independent_model_call': False,
                  'visual_review': 'pending'}
        prepare_plan(ROOT / matrix['blueprint'], ROOT / 'configs/language/f4-responses-v1.json', out / 'plan')
        execute_plan(out / 'plan', out / 'trees')
        blueprint, document, resolved_rows = load_plan(out / 'plan')
        assert [r['id'] for r in document['cases']] == [r['id'] for r in matrix['cases']]
        for row, resolved_row in zip(matrix['cases'], resolved_rows):
            n = row['id']
            request = resolved_row['instance']
            assert request['seeds'] == row['seeds']
            base_request = {**request, 'profile': matrix['baseline_profile'], 'overrides': {}}
            baseline = execute_blueprint(blueprint, base_request, out / 'bases' / n, render=False)
            candidate = read(out / 'trees' / n / 'manifest.json')
            base_params = resolve_blueprint(blueprint, base_request)['parameters']
            params = resolve_blueprint(blueprint, request)['parameters']
            direction = {path: (value(params, path) > value(base_params, path) if sign == 'increase'
                                else value(params, path) < value(base_params, path))
                         for path, sign in row['expect'].items()}
            report['checks'][n + '-direction'] = all(direction.values())
            report['checks'][n + '-budget'] = all(m['metrics']['triangles'] < 7000 and
                len(m['metrics']['triangles_by_material']) <= 2 for m in (baseline, candidate))
            comparison = compare(out / 'bases' / n, out / 'trees' / n, out / 'comparisons' / n)
            report['checks'][n + '-sources-and-environment'] = comparison['same_sources'] and comparison['same_environment']
            report['checks'][n + '-geometry-changed'] = not comparison['same_geometry']
            if n in ('densa', 'abierta'):
                # El GLB de referencia puede incluir metadatos de ejecución. La
                # estructura/malla base real y su simplificación son el invariante;
                # los conectores de los grupos añadidos sí cambian con su cantidad.
                base_reference = read(out / 'bases' / n / 'base-reference.json')
                candidate_reference = read(out / 'trees' / n / 'base-reference.json')
                report['checks'][n + '-base-wood-identical'] = all(
                    base_reference[k] == candidate_reference[k]
                    for k in ('wood_mesh', 'branches', 'wood_sha256', 'normalization')) and (
                    baseline['wood_optimization'] == candidate['wood_optimization'])
            report['cases'][n] = {'instance': request, 'baseline': base_request, 'direction': direction,
                'triangles': candidate['metrics']['triangles'], 'baseline_triangles': baseline['metrics']['triangles'],
                'glb_sha256': candidate['glb_sha256'], 'baseline_glb_sha256': baseline['glb_sha256'],
                'comparison': comparison}
            print(f'{n}: {baseline["metrics"]["triangles"]} → {candidate["metrics"]["triangles"]} tris', flush=True)
        saved = copy.deepcopy(document)
        saved['origin'] = 'saved-response'
        prepare_plan(blueprint, saved, out / 'replay-plan')
        report['checks']['replay-resolution-identical'] = load_plan(out / 'replay-plan')[2] == resolved_rows
        repeat = execute_blueprint(blueprint, resolved_rows[3]['instance'], out / 'repeat', render=False)
        report['checks']['repeat-glb-identical'] = repeat['glb_sha256'] == report['cases']['densa']['glb_sha256']
        report['source_lock'] = {str(path.relative_to(ROOT)): sha(path) for path in
            [Path(__file__), ROOT / 'configs/verification/f4-v1.json', ROOT / 'configs/language/f4-responses-v1.json',
             *sorted((ROOT / 'src/treegen').glob('*.py'))]}
        report['passed'] = all(report['checks'].values())
        write(out / 'verification.json', report)
        assert report['passed'], report['checks']
    if a.stage == 'generate':
        return
    report = read(out / 'verification.json')
    assert report['source_lock'] == {name: sha(ROOT / name) for name in report['source_lock']}, 'Fuentes cambiadas entre etapas'
    project, captures = out / 'godot', out / 'captures'
    project.mkdir()
    captures.mkdir()
    for name in ('project.godot', 'verify_oak.gd', 'review_painted_pine.gd', 'review_painted_oak_pilot.gd'):
        shutil.copy2(ROOT / 'godot' / name, project / name)
    script = project / 'review_painted_pine.gd'
    script.write_text(script.read_text().replace('im.get_width()==1254 and im.get_height()==1254',
        '(im.get_width()==1254 and im.get_height()==1254) or (im.get_width()==2000 and im.get_height()==2000)'))
    for row in matrix['cases']:
        n = row['id']
        for label, directory in [('base', 'bases'), ('candidate', 'trees')]:
            shutil.copy2(out / directory / n / 'tree.glb', project / f'{label}-{n}.glb')
    env = dict(os.environ, XDG_DATA_HOME=str(out / 'xdg/data'),
               XDG_CONFIG_HOME=str(out / 'xdg/config'), XDG_CACHE_HOME=str(out / 'xdg/cache'))
    godot = os.environ.get('GODOT_BIN', GODOT)
    run([godot, '--headless', '--path', project, '--editor', '--import'], out / 'logs/import.log', env)
    report['godot'] = []
    for row in matrix['cases']:
        n = row['id']
        entries, lows, highs = [], [], []
        for label, directory in [('base', 'bases'), ('candidate', 'trees')]:
            metrics = read(out / directory / n / 'manifest.json')['metrics']
            low, high = metrics['bounds_blender']
            lows.append(low)
            highs.append(high)
            entries.append({'id': f'{label}-{n}', 'resource': f'res://{label}-{n}.glb', 'metrics': metrics})
        low = [min(v[i] for v in lows) for i in range(3)]
        high = [max(v[i] for v in highs) for i in range(3)]
        center = [(a + b) / 2 for a, b in zip(low, high)]
        span = max(b - a for a, b in zip(low, high))
        shots = [{'id': name, 'camera': camera(center, span, direction, span * 1.15),
                  'background': '#EEE9DF', 'light': [-35, -25, 0]}
                 for name, direction in [('front', [0, -1, .1]), ('side', [1, 0, .1]),
                                         ('perspective', [1, -1, .45]), ('top', [0, 0, 1])]]
        config, result = out / f'{n}-input.json', out / f'{n}-report.json'
        write(config, {'output': str(captures), 'report': str(result), 'center': center,
                       'span': span, 'original_low': [0, 0, 0], 'assets': entries, 'shots': shots})
        run([godot, '--path', project, '--audio-driver', 'Dummy', '--script',
             'res://review_painted_oak_pilot.gd', '--', config, '--visual'], out / f'logs/{n}.log', env)
        result_data = read(result)
        assert result_data['passed']
        report['godot'].append(result_data)
        sheet(out, out / f'{n}.jpg', 2,
              [[(f'captures/{label}-{n}--{v}.png', label + ' ' + n + ' | ' + v)
                for label in ('base', 'candidate')] for v in ('front', 'side', 'perspective', 'top')])
        print(n + ': ocho capturas Godot', flush=True)
    report['capture_sha256'] = {p.name: sha(p) for p in captures.glob('*.png')}
    assert len(report['capture_sha256']) == 48
    report['visual_captures_generated'] = True
    write(out / 'verification.json', report)
    (out / 'index.html').write_text('<!doctype html><meta charset="utf-8"><title>F4: variaciones con Codex</title>'
        '<style>body{font:18px sans-serif;background:#eee9df;margin:24px}img{max-width:100%}</style>'
        '<h1>F4: interpretación en el chat de Codex</h1><p>Base izquierda; propuesta derecha. '
        'Mismas semillas y cámaras por pareja. La aceptación artística sigue pendiente.</p>' + ''.join(
            '<h2>' + row['id'] + '</h2><p>' + row['request'] + '</p><img src="' + row['id'] + '.jpg">'
            for row in matrix['cases']))


if __name__ == '__main__':
    main()
