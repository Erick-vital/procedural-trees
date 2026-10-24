#!/usr/bin/env python3
"""B2: generación aislada, repetición y comparación RF3 en Godot."""
import argparse
import json
import os
from pathlib import Path
import shutil
import signal
import subprocess
import sys
import time

from PIL import Image, ImageChops, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / 'src'), str(ROOT / 'scripts')]
from treegen.evaluation import validate_result
from verify_blueprint_reference import read, write, sha, snapshot
from verify_foliage_unit import GODOT

BLUEPRINT = 'blueprints/roble_copa_ancha/1.0.0.json'
INSTANCE = 'presets/blueprints/roble-copa-ancha-viejo-09.json'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--visual', action='store_true')
    args = parser.parse_args()
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=False)
    (output / 'logs').mkdir()
    report = {'phase': 'B2', 'passed': False, 'visual_requested': args.visual}
    env = dict(os.environ, PYTHONPATH=str(ROOT / 'src'),
               XDG_DATA_HOME=str(output / 'xdg/data'), XDG_CONFIG_HOME=str(output / 'xdg/config'),
               XDG_CACHE_HOME=str(output / 'xdg/cache'))

    def run(name, command, *, cwd=ROOT, environment=None, timeout=180):
        start = time.monotonic()
        with (output / 'logs' / (name + '.log')).open('w') as log:
            process = subprocess.Popen(list(map(str, command)), cwd=cwd, env=environment or env,
                                       stdout=log, stderr=subprocess.STDOUT, start_new_session=True)
            try:
                code = process.wait(timeout=timeout)
            except subprocess.TimeoutExpired:
                os.killpg(process.pid, signal.SIGKILL)
                process.wait()
                raise TimeoutError(f'{name}: excedió {timeout} s')
        content = (output / 'logs' / (name + '.log')).read_text()
        if code or 'SCRIPT ERROR:' in content or '\nERROR:' in content:
            raise RuntimeError(f'{name}: {code}; ' + content[-1800:])
        report.setdefault('duration_seconds', {})[name] = round(time.monotonic() - start, 3)
        print(name + ': OK', flush=True)
        return content.strip()

    try:
        lock = read(ROOT / 'docs/evidence/blueprints/b0/reference-lock.json')
        approved = ROOT / lock['pilot_directory']
        # Integridad del resultado aprobado, sin exigir que el ejecutor nuevo
        # tenga el hash del ejecutor histórico que esta fase amplía.
        for name in ('tree.glb', 'tree.blend', 'manifest.json', 'cameras.json'):
            relative = str((approved / name).relative_to(ROOT))
            if sha(approved / name) != lock['files_sha256'][relative]:
                raise ValueError('Referencia aprobada alterada: ' + relative)
        if snapshot(approved) != lock['snapshot']:
            raise ValueError('Referencia aprobada distinta del lock B0')
        run('tests', [sys.executable, '-m', 'unittest', 'discover', '-s', 'tests', '-v'])
        isolated = output / 'isolated-source'
        isolated.mkdir()
        for folder in ('src', 'blender', 'schemas', 'configs', 'blueprints', 'presets/blueprints'):
            shutil.copytree(ROOT / folder, isolated / folder,
                            ignore=shutil.ignore_patterns('__pycache__', '*.pyc', '*.blend', '*.glb'))
        assert not (isolated / 'artifacts').exists() and not (isolated / 'docs').exists()
        report['isolated_source_has_no_artifacts_or_evidence'] = True
        isolated_env = dict(env, PYTHONPATH=str(isolated / 'src'))
        for name, render in [('pilot', True), ('repeat', False)]:
            command = [sys.executable, '-m', 'treegen', 'generate-blueprint', BLUEPRINT,
                       '--instance', INSTANCE, '--output', output / name]
            if not render:
                command.append('--no-render')
            run(name, command, cwd=isolated, environment=isolated_env, timeout=150)
            validate_result(output / name)
            manifest = read(output / name / 'manifest.json')
            actual = snapshot(output / name)
            actual['manifest_invariants']['spec'] = manifest['canopy_spec']
            differences = [key for key in actual if actual[key] != lock['snapshot'][key]]
            report[name] = {'matches_b0': not differences, 'differences': differences,
                            'metrics': manifest['metrics'], 'glb_sha256': manifest['glb_sha256'],
                            'resolved_sha256': manifest['resolved_blueprint']['resolved_sha256'],
                            'sources_sha256': manifest['sources_sha256']}
            if differences:
                raise ValueError(name + ': diferencias de migración: ' + ', '.join(differences))
        report['repeat_matches'] = report['pilot']['resolved_sha256'] == report['repeat']['resolved_sha256']
        assert report['repeat_matches']

        # Proyecto Godot propio para importar únicamente la pareja a comparar.
        project = output / 'godot'
        project.mkdir()
        for name in ('project.godot', 'verify_oak.gd', 'verify_foliage_molds.gd'):
            shutil.copy2(ROOT / 'godot' / name, project / name)
        reference = output / 'approved-reference'
        reference.mkdir()
        for name in ('tree.glb', 'manifest.json', 'cameras.json'):
            shutil.copy2(approved / name, reference / name)
        entries = []
        for name, folder in [('approved', reference), ('blueprint', output / 'pilot')]:
            shutil.copy2(folder / 'tree.glb', project / (name + '.glb'))
            entries.append({'id': name, 'folder': str(folder), 'capture': args.visual,
                            'resource': 'res://' + name + '.glb'})
        write(output / 'godot-input.json', entries)
        godot = os.environ.get('GODOT_BIN', GODOT)
        assert run('godot-version', [godot, '--version']) == '4.7.2.stable.official.ed1daf0bf'
        run('godot-import', [godot, '--headless', '--path', project, '--editor', '--import'])
        command = [godot, '--path', project, '--script', 'res://verify_foliage_molds.gd', '--',
                   '--input=' + str(output / 'godot-input.json'),
                   '--report=' + str(output / 'godot-report.json')]
        run('godot-check', command[:1] + ['--headless'] + command[1:])
        report['godot'] = read(output / 'godot-report.json')
        assert report['godot']['passed'] and len(report['godot']['assets']) == 2
        if args.visual:
            run('godot-visual', command + ['--visual'])
            report['godot_visual'] = read(output / 'godot-report.json')
            assert report['godot_visual']['passed']
            differences = {}
            cameras = read(output / 'pilot/cameras.json')
            for view in cameras:
                with Image.open(reference / ('godot-' + view + '.png')) as a, \
                        Image.open(output / 'pilot' / ('godot-' + view + '.png')) as b:
                    delta = ImageChops.difference(a.convert('RGB'), b.convert('RGB'))
                    differences[view] = {'same_pixels': delta.getbbox() is None,
                                         'max_channel_delta': max(high for low, high in delta.getextrema())}
            report['visual_comparison'] = differences
            if not all(row['same_pixels'] for row in differences.values()):
                raise ValueError('Diferencias en las capturas Godot de la pareja')
            sheet = Image.new('RGB', (720, 4 * 390), '#e9edf1')
            draw = ImageDraw.Draw(sheet)
            for row, view in enumerate(('front', 'below', 'near', 'detail-perspective')):
                for col, (name, folder) in enumerate((('RF3 aprobado', reference), ('Blueprint', output / 'pilot'))):
                    with Image.open(folder / ('godot-' + view + '.png')) as pic:
                        pic = pic.convert('RGB')
                        pic.thumbnail((354, 354))
                        sheet.paste(pic, (col * 360, row * 390 + 30))
                    draw.text((col * 360 + 6, row * 390 + 8), name + ' | ' + view, fill='black')
            sheet.save(output / 'comparison.jpg', quality=92)
        report['passed'] = True
    except Exception as exc:
        report['error'] = str(exc)
        raise
    finally:
        write(output / 'verification.json', report)
    print('B2 verificada: ' + str(output), flush=True)


if __name__ == '__main__':
    main()
