#!/usr/bin/env python3
"""Familia3.0.0: auditoría de cinco maduros y revisión Godot reproducible."""
import argparse
import copy
import html
import math
import os
from pathlib import Path
import shutil
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / 'src'), str(ROOT / 'scripts')]
from treegen.language import load_plan
from treegen.evaluation import validate_result
from review_pine_painted import read, write, run, sha, camera
from verify_foliage_unit import GODOT
from foliage_evidence import sheet


def audit(out):
    _, _, rows = load_plan(out / 'plan')
    assert read(out / 'trees/batch.json')['status'] == 'completed'
    assert read(out / 'repeat/batch.json')['status'] == 'completed'
    checks, cases = {}, {}
    accepted = read(ROOT / 'docs/evidence/oak-foliage/of11/user-acceptance.json')
    for row in rows:
        name = row['id']
        first, repeat = [validate_result(out / directory / name) for directory in ('trees', 'repeat')]
        manifest = read(out / 'trees' / name / 'manifest.json')
        checks[name + '-repeat'] = first == repeat
        checks[name + '-budget'] = first['triangles'] <= 6999 and len(first['materials']) == 2
        checks[name + '-export'] = all(first['checks'].values())
        repeated_manifest = read(out / 'repeat' / name / 'manifest.json')
        checks[name + '-same-sources'] = manifest['sources_sha256'] == repeated_manifest['sources_sha256']
        checks[name + '-same-request'] = all(m['resolved_blueprint']['instance_request'] == row['instance'] for m in (manifest, repeated_manifest))
        env_keys = ('blender', 'blender_build', 'blender_python', 'runner_python', 'jsonschema_version')
        checks[name + '-same-environment'] = all(manifest[k] == repeated_manifest[k] for k in env_keys)
        checks[name + '-time'] = max(manifest['duration_seconds'], repeated_manifest['duration_seconds']) <= 120
        cases[name] = {'seeds': row['instance']['seeds'], 'triangles': first['triangles'],
                       'materials': first['materials'], 'glb_sha256': first['glb_sha256'],
                       'geometry_sha256': first['geometry_sha256'],
                       'maximum_contact_error_m': first['maximum_contact_error_m'],
                       'lower_core_radius_m': first['lower_core_radius_m'],
                       'duration_seconds': manifest['duration_seconds'],
                       'repeat_duration_seconds': repeated_manifest['duration_seconds'],
                       'sources_sha256': manifest['sources_sha256']}
    checks['distinct-geometries'] = len({v['geometry_sha256'] for v in cases.values()}) == len(rows)
    checks['approved-pilot-identical'] = cases['maduro-3100']['glb_sha256'] == accepted['approved_glb_sha256']
    checks['same-generation-sources'] = all(v['sources_sha256'] == next(iter(cases.values()))['sources_sha256'] for v in cases.values())
    for v in cases.values():
        del v['sources_sha256']
    result = {'version': 'oak-central-family-1.0', 'date': '2026-11-03',
              'checks': checks, 'passed': all(checks.values()), 'cases': cases,
              'interpretation_origin': 'codex-session', 'independent_model_call': False,
              'visual_review': 'pending', 'artistic_acceptance': 'pending-except-pilot',
              'plan_sha256': sha(out / 'plan/plan.json'),
              'recipe_sha256': sha(ROOT / 'blueprints/roble_copa_ancha/3.0.0.json'),
              'environment': {k: manifest[k] for k in env_keys},
              'failed_attempt': read(out/'trees-sandbox-failed-01/batch.json') if (out/'trees-sandbox-failed-01/batch.json').exists() else None}
    if (out/'verification.json').exists():
        previous = read(out/'verification.json')
        for key in ('godot_reports', 'captures_sha256', 'review_protocol_sha256', 'visual_captures_generated'):
            if key in previous:
                result[key] = previous[key]
    write(out / 'verification.json', result)
    assert result['passed'], checks
    print('Auditoría: cinco exportaciones y cinco repeticiones correctas', flush=True)


def review(out):
    if (out/'verification.json').exists():
        result = read(out/'verification.json')
    else:
        batch = read(out/'trees/batch.json')
        assert batch['status'] == 'completed' and len(batch['cases']) == 5
        result = {'version': 'oak-central-family-1.0', 'passed': False,
                  'technical_audit': 'pending', 'visual_review': 'pending',
                  'artistic_acceptance': 'pending-except-pilot',
                  'cases': {c['id']: {'glb_sha256': c['glb_sha256']} for c in batch['cases']}}
    project, captures, inputs, logs = [out / p for p in ('godot', 'captures', 'inputs', 'logs')]
    for p in (project, captures, inputs, logs):
        p.mkdir(exist_ok=False)
    for name in ('project.godot', 'verify_oak.gd', 'review_painted_pine.gd', 'review_painted_oak_pilot.gd'):
        shutil.copy2(ROOT / 'godot' / name, project / name)
    # Adaptador de revisión aislado: no modifica verificadores históricos.
    script = project / 'review_painted_pine.gd'
    source = script.read_text()
    assert source.count('im.get_width()==1254 and im.get_height()==1254') == 1
    source = source.replace('im.get_width()==1254 and im.get_height()==1254',
        '(im.get_width()==1254 and im.get_height()==1254) or (im.get_width()==2000 and im.get_height()==2000)')
    needle = '\t\t\tcamera.size=shot.camera.ortho_scale'
    assert source.count(needle) == 1
    source = source.replace(needle, needle + '\n\t\t\tcamera.projection=Camera3D.PROJECTION_PERSPECTIVE if shot.camera.get("projection", "orthogonal")=="perspective" else Camera3D.PROJECTION_ORTHOGONAL\n\t\t\tcamera.fov=float(shot.camera.get("fov", 50.0))')
    script.write_text(source)
    names = list(result['cases'])
    lows, highs, entries = [], [], []
    for name in names:
        assert sha(out / 'trees' / name / 'tree.glb') == result['cases'][name]['glb_sha256']
        shutil.copy2(out / 'trees' / name / 'tree.glb', project / (name + '.glb'))
        metrics = read(out / 'trees' / name / 'manifest.json')['metrics']
        low, high = metrics['bounds_blender']
        lows.append(low); highs.append(high)
        entries.append({'id': name, 'resource': f'res://{name}.glb', 'metrics': metrics})
    low = [min(v[i] for v in lows) for i in range(3)]
    high = [max(v[i] for v in highs) for i in range(3)]
    center = [(a + b) / 2 for a, b in zip(low, high)]
    span = max(b - a for a, b in zip(low, high))
    shots = []

    def add(name, direction, scale=1.25, distance=None, background='#EEE9DF', light=None, receiver=False):
        cam = camera(center, span, direction, span * scale)
        if distance is not None:
            # FOV vertical50°, esfera envolvente común / fracción de pantalla.
            radius = math.sqrt(sum((b-a)**2 for a, b in zip(low, high))) / 2
            d = radius / math.sin(math.radians(25)) / distance
            norm = math.sqrt(sum(x*x for x in direction))
            cam.update(location=[c + x/norm*d for c, x in zip(center, direction)], projection='perspective', fov=50)
        shots.append({'id': name, 'camera': cam, 'background': background,
                      'light': light or [-35, -25, 0], 'receiver': receiver})

    for name, direction in [('front', [0,-1,.1]), ('side', [1,0,.1]), ('back', [0,1,.1]),
                            ('perspective', [1,-1,.45]), ('top', [0,0,1]), ('upper', [1,-1,1])]:
        add(name, direction)
    for name, fraction in [('near', .85), ('medium', .5), ('far', .25)]:
        add(name, [1,-1,.45], distance=fraction)
    add('dark', [1,-1,.45], distance=.85, background='#1E2A35')
    add('alternate-light', [1,-1,.45], distance=.85, light=[-35,100,0])
    add('shadow', [1,-1,.65], scale=1.9, receiver=True)
    for index in range(8):
        angle = 2*math.pi*index/8
        add(f'orbit-{index:02}', [math.cos(angle), math.sin(angle), .3], distance=.85)
    for name in ('wood-front', 'wood-side', 'wood-perspective'):
        base = next(s for s in shots if s['id'] == name.removeprefix('wood-'))
        shot = copy.deepcopy(base)
        shot.update(id=name, wood_only=True)
        shots.append(shot)
    # Ocultar solo las superficies de follaje en las tomas de madera; no crear
    # otra geometría ni derivar contactos de capturas sin alfa.
    needle = '\t\t\tvar settings_rows := []'
    assert source.count(needle) == 1
    script.write_text(source.replace(needle,
        '\t\t\tfor mat in draw_materials:\n\t\t\t\tif mat.resource_name=="Painted_Foliage":\n\t\t\t\t\tmat.transparency=BaseMaterial3D.TRANSPARENCY_ALPHA_SCISSOR\n\t\t\t\t\tmat.alpha_scissor_threshold=1.0 if shot.get("wood_only", false) else .5\n\t\t\t\t\tmat.albedo_color.a=0.0 if shot.get("wood_only", false) else 1.0\n' + needle))
    protocol = {'version': 'oak-family-review-1.0', 'camera_status': 'perspectiva provisional elegida por usuario',
                'bounds_blender': [low, high], 'center': center, 'span': span, 'shots': shots,
                'resolution': [900,900], 'msaa': '4x', 'renderer': 'gl_compatibility',
                'common_cameras': True, 'near_medium_far': 'fracción objetivo .85/.50/.25 de esfera común; sin cámara final del juego',
                'source_sha256': {str(p.relative_to(ROOT)): sha(p) for p in [Path(__file__),
                    ROOT/'godot/review_painted_pine.gd', ROOT/'godot/review_painted_oak_pilot.gd',
                    ROOT/'godot/verify_oak.gd', ROOT/'godot/project.godot', ROOT/'scripts/review_pine_painted.py']},
                'runtime_adapter_sha256': sha(script)}
    # Protocolo congelado antes de importar y capturar.
    write(out / 'review-protocol.json', protocol)
    env = dict(os.environ, XDG_DATA_HOME=str(out/'xdg/data'), XDG_CONFIG_HOME=str(out/'xdg/config'), XDG_CACHE_HOME=str(out/'xdg/cache'))
    godot = os.environ.get('GODOT_BIN', GODOT)
    run([godot, '--headless', '--path', project, '--editor', '--import'], logs/'import.log', env)
    reports = []
    for entry in entries:
        name = entry['id']
        config, report = inputs/(name+'.json'), out/(name+'-godot.json')
        write(config, {'output': str(captures), 'report': str(report), 'center': center, 'span': span,
                       'original_low': low, 'assets': [entry], 'shots': shots})
        run([godot, '--path', project, '--audio-driver', 'Dummy', '--script',
             'res://review_painted_oak_pilot.gd', '--', config, '--visual'], logs/(name+'.log'), env)
        data = read(report)
        assert data['passed'] and len(data['captures']) == len(shots)
        reports.append(data)
        sheet(out, out/(name+'.jpg'), 4, [[(f'captures/{name}--{s["id"]}.png', name+' | '+s['id'])
              for s in shots[i:i+4]] for i in range(0,len(shots),4)])
        print(name + ': ' + str(len(shots)) + ' capturas Godot', flush=True)
    for label, views in [('overview', ['perspective','top']), ('distance', ['near','medium','far']),
                         ('wood', ['wood-front','wood-side','wood-perspective'])]:
        sheet(out, out/(label+'.jpg'), len(names), [[(f'captures/{name}--{v}.png',name+' | '+v) for name in names] for v in views])
    result.update(godot_reports=reports, captures_sha256={p.name:sha(p) for p in sorted(captures.glob('*.png'))},
                  review_protocol_sha256=sha(out/'review-protocol.json'), visual_captures_generated=True)
    assert len(result['captures_sha256']) == len(shots)*len(names)
    write(out/'verification.json', result)
    sections = [('overview','Comparación de copa'), ('distance','Perspectiva provisional: tres distancias'), ('wood','Madera sola')]
    sections += [(n,n) for n in names]
    (out/'index.html').write_text('<!doctype html><meta charset="utf-8"><title>Roble3.0.0 · cinco maduros</title>'
        '<style>body{font:18px sans-serif;background:#eee9df;margin:24px}img{max-width:100%}a{color:#174a35}</style>'
        '<h1>Roble3.0.0 · cinco maduros</h1><p>Semillas3100–3104 · distribución17 · pintura2718. '
        'Mismas cámaras, luz y perfil. Perspectiva provisional; no es la cámara final del juego. '
        'Aprobación artística del lote pendiente; piloto3100 previamente aprobado.</p>'
        '<p><a href="verification.json">Auditoría</a> · <a href="review-protocol.json">Cámaras y protocolo</a></p>'
        + ''.join('<h2>'+html.escape(label)+'</h2><a href="'+name+'.jpg"><img src="'+name+'.jpg"></a>' for name,label in sections))


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--output', type=Path, required=True)
    p.add_argument('--stage', choices=('audit','review'), required=True)
    args = p.parse_args()
    (audit if args.stage=='audit' else review)(args.output.resolve())


if __name__ == '__main__':
    main()
