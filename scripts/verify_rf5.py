#!/usr/bin/env python3
"""RF5: treinta blueprints Q3/RF3, regresión exportada y revisión en Godot."""
import argparse
from collections import Counter
import copy
import html
import math
import os
from pathlib import Path
import shutil
import signal
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / 'src'), str(ROOT / 'scripts')]
from treegen.blueprints import canonical_hash, load_blueprint, resolve_blueprint
from treegen.evaluation import validate_result
from treegen.foliage_twigs_evaluation import inspect_twigs_glb
from treegen.runner import BLENDER, execute_blueprint
from verify_blueprint_reference import read, write, sha
from verify_foliage_unit import GODOT
from foliage_evidence import sheet


def validate_matrix(matrix, blueprint, base_cases):
    """Impide subconjuntos favorables, ajustes individuales y cambios de base."""
    rows = matrix['cases']
    original = {c['id']: c['spec'] for c in base_cases}
    if len(rows) != 30 or len(original) != 30 or {c['id'] for c in rows} != set(original):
        raise ValueError('RF5 requiere exactamente los treinta casos Q3')
    if Counter(c['instance']['profile'] for c in rows) != {'joven': 10, 'adulto': 10, 'viejo': 10}:
        raise ValueError('RF5 requiere diez casos por edad')
    for row in rows:
        instance = row['instance']
        if 'overrides' in instance or instance['profile'] != row['id'].split('-')[0]:
            raise ValueError('No se permiten retoques por ejemplar')
        resolved = resolve_blueprint(blueprint, instance)
        if resolved['base_spec'] != original[row['id']]:
            raise ValueError('Base distinta de Q3: ' + row['id'])
        if instance['seeds']['canopy'] != matrix['canopy_seed']:
            raise ValueError('Semilla de copa distinta de la común')
    if len(matrix['repeat_cases']) != 3 or len(set(matrix['repeat_cases'])) != 3 or any(
            name not in original for name in matrix['repeat_cases']):
        raise ValueError('Se requieren tres repeticiones distintas y explícitas')


def source_snapshot():
    files = [p for folder in ('src/treegen', 'blender', 'blueprints', 'schemas', 'configs')
             for p in (ROOT / folder).rglob('*') if p.is_file() and p.suffix in ('.py', '.json')]
    files += list((ROOT / 'godot').glob('*.gd')) + [Path(__file__)]
    return {str(p.relative_to(ROOT)): sha(p) for p in sorted(files)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--matrix', type=Path, default=ROOT / 'configs/verification/rf5-v1.json')
    parser.add_argument('--q3-reference', type=Path, default=ROOT / 'artifacts/q3/acceptance/lote')
    parser.add_argument('--visual', action='store_true')
    args = parser.parse_args()
    matrix = read(args.matrix)
    bp = load_blueprint(ROOT / matrix['blueprint'])
    validate_matrix(matrix, bp, read(ROOT / matrix['base_cases']))
    out = args.output.resolve()
    out.mkdir(parents=True, exist_ok=False)
    (out / 'logs').mkdir()
    write(out / 'frozen-matrix.json', matrix)
    before = source_snapshot()
    report = {'phase': 'RF5', 'passed': False, 'matrix_executed': False,
              'matrix_sha256': canonical_hash(matrix), 'blueprint_sha256': canonical_hash(bp),
              'sources_before': before, 'visual_requested': args.visual,
              'user_artistic_acceptance': 'pending_for_this_batch',
              'cases': {}, 'repeats': {}, 'checks': {}, 'q3_comparison': {}, 'godot': []}
    env = dict(os.environ, PYTHONPATH=str(ROOT / 'src'), XDG_DATA_HOME=str(out / 'xdg/data'),
               XDG_CONFIG_HOME=str(out / 'xdg/config'), XDG_CACHE_HOME=str(out / 'xdg/cache'))
    manifests = {}
    started = time.monotonic()

    def save():
        report['elapsed_seconds'] = round(time.monotonic() - started, 3)
        write(out / 'verification.json', report)

    def run(name, command):
        with (out / 'logs' / (name + '.log')).open('w') as log:
            process = subprocess.Popen(list(map(str, command)), cwd=ROOT, env=env, stdout=log,
                                       stderr=subprocess.STDOUT, start_new_session=True)
            try:
                code = process.wait(timeout=180)
            except subprocess.TimeoutExpired:
                os.killpg(process.pid, signal.SIGKILL)
                process.wait()
                raise TimeoutError(name + ': excedió 180 s')
        content = (out / 'logs' / (name + '.log')).read_text()
        if code or 'SCRIPT ERROR:' in content or '\nERROR:' in content:
            raise RuntimeError(name + ': ' + content[-2000:])
        print(name + ': OK', flush=True)

    def blender_run(name, script, *arguments):
        run(name, [os.environ.get('BLENDER_BIN', BLENDER), '--background', '--factory-startup',
                   '--threads', '1', '--python-exit-code', '1', '--python', ROOT / script, '--', *arguments])

    try:
        run('tests', [sys.executable, '-m', 'unittest', 'discover', '-s', 'tests', '-v'])
        blender_run('contact-regression', 'blender/verify_mesh_contacts.py')
        # Validar y fijar las referencias antes de generar; no aportan geometría.
        references = {}
        for row in matrix['cases']:
            name = row['id']
            folder = args.q3_reference.resolve() / name
            old = read(folder / 'manifest.json')
            validate_result(folder)
            references[name] = (old, inspect_twigs_glb(folder / 'tree.glb', old['metrics']))
        for row in matrix['cases']:
            name = row['id']
            try:
                m = execute_blueprint(ROOT / matrix['blueprint'], row['instance'], out / name, render=False)
                exported = validate_result(out / name)
                manifests[name] = m
                old, signature = references[name]
                comparison = {'source': str(args.q3_reference.resolve() / name),
                    'reference_glb_sha256': signature['glb_sha256'],
                    'same_base_spec': old['spec'] == m['base_spec'],
                    'geometry_normals_equal': signature['channel_sha256']['Oak_Bark'] == exported['channel_sha256']['Oak_Bark'],
                    'bark_material_equal': signature['material_properties_sha256']['Oak_Bark'] == exported['material_properties_sha256']['Oak_Bark']}
                report['q3_comparison'][name] = comparison
                report['cases'][name] = {'status': 'generated', 'profile': row['instance']['profile'],
                    **{k: m[k] for k in ('metrics', 'support_count', 'leaf_count', 'glb_sha256',
                        'wood_sha256', 'glb_bytes', 'duration_seconds', 'sampling', 'selection',
                        'surface_projection', 'contacts')}, 'manifest_sha256': sha(out / name / 'manifest.json')}
            except Exception as exc:
                report['cases'][name] = {'status': 'failed', 'error': str(exc)}
            print(name + ': ' + report['cases'][name]['status'], flush=True)
            save()
        checks = report['checks']
        checks['all_thirty_generated'] = len(manifests) == 30
        checks['wood_normals_bark_and_inputs_equal_q3'] = len(report['q3_comparison']) == 30 and all(
            all(c[k] for k in ('same_base_spec', 'geometry_normals_equal', 'bark_material_equal'))
            for c in report['q3_comparison'].values())
        checks['thirty_unique_geometries'] = len({m['metrics']['geometry_sha256'] for m in manifests.values()}) == 30
        checks['no_external_geometry_inputs'] = all(m['external_geometry_inputs'] == [] for m in manifests.values())
        lock = read(ROOT / 'docs/evidence/blueprints/b0/reference-lock.json')
        checks['old09_matches_b0'] = 'viejo-09' in manifests and manifests['viejo-09']['glb_sha256'] == lock['files_sha256'][lock['pilot_directory'] + '/tree.glb']
        for name in matrix['repeat_cases']:
            if name not in manifests:
                checks[name + '-repeat'] = False
                continue
            instance = next(c['instance'] for c in matrix['cases'] if c['id'] == name)
            repeated = execute_blueprint(ROOT / matrix['blueprint'], instance, out / (name + '-repeat'), render=False)
            validate_result(out / (name + '-repeat'))
            equal = all(repeated[k] == manifests[name][k] for k in
                        ('glb_sha256', 'wood_sha256', 'supports_sha256', 'twigs_sha256', 'placements_sha256'))
            checks[name + '-repeat'] = equal
            report['repeats'][name] = {'identical': equal, 'glb_sha256': repeated['glb_sha256'],
                                      'duration_seconds': repeated['duration_seconds']}
            print(name + '-repeat: ' + str(equal), flush=True)
            save()
        # Contactos sobre los GLB reimportados; lotes acotados a diez modelos.
        report['export_contacts'] = {}
        names = list(manifests)
        for offset in range(0, len(names), 10):
            source, result = out / f'contacts-input-{offset}.json', out / f'contacts-{offset}.json'
            write(source, [str(out / n) for n in names[offset:offset + 10]])
            blender_run('export-contacts-' + str(offset), 'blender/verify_export_contacts.py', source, result)
            contacts = read(result)
            checks['export-contacts-' + str(offset)] = contacts['passed']
            report['export_contacts'].update(contacts['assets'])
        checks['thirty_export_contacts'] = len(report['export_contacts']) == 30
        # Madera separada para inspección, sin alterar las salidas de generación.
        for offset in range(0, len(names), 10):
            source = out / f'wood-input-{offset}.json'
            write(source, [{'source': str(out / n), 'output': str(out / 'inspection' / (n + '-wood'))}
                           for n in names[offset:offset + 10]])
            blender_run('wood-' + str(offset), 'blender/inspect_blueprint_controls.py', source)
        low = [min(m['metrics']['bounds_blender'][0][k] for m in manifests.values()) for k in range(3)]
        high = [max(m['metrics']['bounds_blender'][1][k] for m in manifests.values()) for k in range(3)]
        center = [(a + b) / 2 for a, b in zip(low, high)]
        fit = math.dist(low, high) / .88
        cameras = read(ROOT / 'configs/inspection/rf3-v1.json')['cameras']
        general = ('front', 'side', 'top', 'below', 'perspective', 'reverse')
        scales = ('near', 'medium', 'far')
        project = out / 'godot'
        project.mkdir()
        for filename in ('project.godot', 'verify_oak.gd', 'verify_foliage_molds.gd'):
            shutil.copy2(ROOT / 'godot' / filename, project / filename)
        entries = []
        for name in names + [n + '-wood' for n in names]:
            wood = name.endswith('-wood')
            original = name[:-5] if wood else name
            folder = out / 'inspection' / name
            folder.mkdir(parents=True, exist_ok=True)
            if not wood:
                for filename in ('tree.glb', 'manifest.json'):
                    shutil.copy2(out / name / filename, folder / filename)
            rig = {}
            for view in (('front', 'side', 'perspective') if wood else general + scales):
                c = copy.deepcopy(cameras[view])
                target = center
                c['ortho_scale'] = fit
                if view in scales:
                    target = [sum(pair) / 2 for pair in zip(*manifests[original]['metrics']['bounds_blender'])]
                    c['ortho_scale'] = manifests[original]['base_spec']['parameters']['height_m'] / c['target_height_fraction']
                c['location'] = [target[k] + 80 * c['basis_columns'][2][k] for k in range(3)]
                rig[view] = c
            write(folder / 'cameras.json', rig)
            shutil.copy2(folder / 'tree.glb', project / (name + '.glb'))
            entries.append({'id': name, 'folder': str(folder), 'capture': args.visual, 'resource': 'res://' + name + '.glb'})
        report['camera_protocol'] = {'general_shared_ortho_scale': fit, 'global_bounds': [low, high],
            'scale_views': 'Altura 50/25/10%; estas vistas no comparan tamaño físico entre edades.',
            'wood_views': 'Frente/perfil/perspectiva, idénticas a las generales del árbol completo.',
            'lighting': 'RF3/B3: luz [-35,-25,0], energía 1.2, ambiente .5; 900×900.'}
        godot = os.environ.get('GODOT_BIN', GODOT)
        run('godot-version', [godot, '--version'])
        run('godot-import', [godot, '--headless', '--path', project, '--editor', '--import'])
        for offset in range(0, len(entries), 2):
            source, result = out / f'godot-input-{offset}.json', out / f'godot-report-{offset}.json'
            write(source, entries[offset:offset + 2])
            command = [godot, '--path', project, '--script', 'res://verify_foliage_molds.gd', '--',
                       '--input=' + str(source), '--report=' + str(result)]
            run('godot-check-' + str(offset), command[:1] + ['--headless'] + command[1:])
            headless = read(result)
            checks['godot-check-' + str(offset)] = headless['passed'] and len(headless['assets']) == len(entries[offset:offset + 2])
            if args.visual:
                run('godot-visual-' + str(offset), command + ['--visual'])
            captured = read(result)
            checks['godot-result-' + str(offset)] = captured['passed']
            report['godot'].append(captured)
            save()
        if args.visual:
            for age in ('joven', 'adulto', 'viejo'):
                group = [n for n in names if n.startswith(age + '-')]
                for offset in (0, 5):
                    sheet(out, out / f'{age}-{offset:02d}-views.jpg', 4,
                          [[(f'inspection/{n}/godot-{v}.png', n + ' | ' + v)
                            for v in ('near', 'side', 'top', 'below')] for n in group[offset:offset + 5]])
            for view, title in (('near', 'overview'), ('front', 'physical-scale')):
                sheet(out, out / (title + '.jpg'), 5,
                      [[(f'inspection/{n}/godot-{view}.png', n + ' | ' + view) for n in names[i:i + 5]]
                       for i in range(0, len(names), 5)])
            sheet(out, out / 'wood-comparison.jpg', 4,
                  [[(f'inspection/{n}{suffix}/godot-{v}.png', n + suffix + ' | ' + v)
                    for suffix in ('-wood', '') for v in ('front', 'perspective')]
                   for n in ('joven-00', 'adulto-00', 'viejo-09') if n in names])
            report['capture_files_sha256'] = {str(p.relative_to(out)): sha(p) for p in sorted((out / 'inspection').glob('*/godot-*.png'))}
            checks['all_360_captures'] = len(report['capture_files_sha256']) == 360
            rows = []
            for entry in entries:
                n = entry['id']
                rig = read(Path(entry['folder']) / 'cameras.json')
                cells = ''.join(f'<td>{html.escape(v)}<a href="inspection/{n}/godot-{v}.png"><img loading="lazy" src="inspection/{n}/godot-{v}.png"></a></td>' for v in rig)
                rows.append('<tr><th>' + html.escape(n) + '</th>' + cells + '</tr>')
            (out / 'index.html').write_text('<!doctype html><meta charset="utf-8"><title>RF5 · treinta robles</title><style>body{font:16px sans-serif;background:#e9edf1}img{display:block;width:230px}td,th{vertical-align:top}</style><h1>RF5: treinta robles</h1><p>Diez por edad, receta B3 1.2.0 aprobada. Lote completo pendiente de aceptación artística. Vistas generales a escala física común; near/medium/far relativas a la altura.</p><a href="verification.json">Resultados y fallos</a><table>' + ''.join(rows) + '</table>')
        checks['sources_unchanged_during_run'] = source_snapshot() == before
        report['matrix_executed'] = True
        report['passed'] = all(checks.values())
    except Exception as exc:
        report['error'] = str(exc)
        raise
    finally:
        save()
    print('RF5 ejecutada; passed=' + str(report['passed']), flush=True)
    if not report['passed']:
        raise SystemExit(1)


if __name__ == '__main__':
    main()
