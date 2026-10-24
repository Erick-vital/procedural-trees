#!/usr/bin/env python3
"""B3/RF4: matriz congelada, controles, fallos, repetición e inspección Godot."""
import argparse
import copy
import html
import json
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
from treegen.blueprints import load_blueprint, resolve_blueprint, canonical_hash
from treegen.runner import execute_blueprint, BLENDER
from treegen.foliage_twigs_evaluation import inspect_twigs_glb
from verify_blueprint_reference import read, write, sha
from verify_foliage_unit import GODOT
from foliage_evidence import sheet


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', required=True, type=Path)
    parser.add_argument('--visual', action='store_true')
    parser.add_argument('--matrix', type=Path, default=ROOT / 'configs/verification/b3-v1.json')
    args = parser.parse_args()
    out = args.output.resolve()
    out.mkdir(parents=True, exist_ok=False)
    (out / 'logs').mkdir()
    matrix = read(args.matrix)
    bp = load_blueprint(ROOT / matrix['blueprint'])
    write(out / 'frozen-matrix.json', matrix)
    report = {'phase': 'B3', 'matrix_sha256': canonical_hash(matrix), 'blueprint_sha256': canonical_hash(bp),
              'verifier_sha256': sha(Path(__file__)), 'cases': {}, 'checks': {}, 'visual_requested': args.visual, 'passed': False}
    env = dict(os.environ, PYTHONPATH=str(ROOT / 'src'), XDG_DATA_HOME=str(out / 'xdg/data'),
               XDG_CONFIG_HOME=str(out / 'xdg/config'), XDG_CACHE_HOME=str(out / 'xdg/cache'))

    def run(name, command, timeout=180):
        with (out / 'logs' / (name + '.log')).open('w') as log:
            process = subprocess.Popen(list(map(str, command)), cwd=ROOT, env=env,
                                       stdout=log, stderr=subprocess.STDOUT, start_new_session=True)
            try:
                code = process.wait(timeout=timeout)
            except subprocess.TimeoutExpired:
                os.killpg(process.pid, signal.SIGKILL)
                process.wait()
                raise TimeoutError(name)
        log = (out / 'logs' / (name + '.log')).read_text()
        if code or 'SCRIPT ERROR:' in log or '\nERROR:' in log:
            raise RuntimeError(name + ': ' + log[-2000:])
        print(name + ': OK', flush=True)

    manifests, signatures = {}, {}
    try:
        run('tests', [sys.executable, '-m', 'unittest', 'discover', '-s', 'tests', '-v'])
        run('contact-regression', [os.environ.get('BLENDER_BIN', BLENDER), '--background', '--factory-startup',
            '--threads', '1', '--python-exit-code', '1', '--python', ROOT / 'blender/verify_mesh_contacts.py'])
        for case in matrix['cases']:
            name = case['id']
            start = time.monotonic()
            try:
                # execute_blueprint registra también el rechazo antes de abrir Blender.
                m = execute_blueprint(ROOT / matrix['blueprint'], case['instance'], out / name, render=False)
                if case['expect'] == 'reject':
                    raise AssertionError('Se generó una entrada que debía rechazarse')
                manifests[name] = m
                signatures[name] = inspect_twigs_glb(out / name / 'tree.glb', m['metrics'], triangle_limit=12500)
                report['cases'][name] = {'status': 'generated', 'kind': case['kind'],
                    'metrics': m['metrics'], 'supports': m['support_count'], 'leaves': m['leaf_count'],
                    'selection': m['selection'], 'sampling': m['sampling'], 'glb_sha256': m['glb_sha256'],
                    'wood_sha256': m['wood_sha256'], 'export_channels': signatures[name]['channel_sha256'],
                    'duration_seconds': round(time.monotonic()-start, 3)}
            except Exception as exc:
                status = 'rejected' if case['expect'] == 'reject' and isinstance(exc, ValueError) else 'failed'
                report['cases'][name] = {'status': status, 'kind': case['kind'], 'error': str(exc)}
            print(name + ': ' + report['cases'][name]['status'], flush=True)
            write(out / 'verification.json', report)
        pilot = manifests['pilot']
        checks = report['checks']
        lock = read(ROOT / 'docs/evidence/blueprints/b0/reference-lock.json')
        checks['pilot_glb_matches_b0'] = pilot['glb_sha256'] == lock['files_sha256'][lock['pilot_directory'] + '/tree.glb']
        for age in ('viejo', 'adulto', 'joven'):
            a, b = age+'-00', age+'-00-repeat'
            if a in manifests and b in manifests:
                checks[a+'-repeat'] = manifests[a]['glb_sha256'] == manifests[b]['glb_sha256']
        for name in ('leaf-min', 'groups-min', 'groups-max', 'profile-min', 'profile-max', 'east-zero', 'canopy-seed'):
            if name in manifests:
                checks[name+'-base-unchanged'] = all(signatures[name][key]['Oak_Bark'] == signatures['pilot'][key]['Oak_Bark']
                    for key in ('channel_sha256', 'material_properties_sha256')) and manifests[name]['wood_sha256'] == pilot['wood_sha256']
        if 'leaf-min' in manifests:
            small = manifests['leaf-min']
            checks['leaf-only-supports-and-twigs'] = all(small[k] == pilot[k] for k in ('supports_sha256', 'twigs_sha256', 'leaf_count'))
            checks['leaf-only-roots-axes'] = [{k:v for k,v in p.items() if k != 'length_m'} for p in small['placements']] == [{k:v for k,v in p.items() if k != 'length_m'} for p in pilot['placements']]
        if 'canopy-seed' in manifests:
            checks['canopy-seed-changes-layout'] = manifests['canopy-seed']['placements_sha256'] != pilot['placements_sha256']
        if 'east-zero' in manifests:
            east = manifests['east-zero']
            checks['east-zero-keeps-other-supports'] = east['supports'] == [c for c in pilot['supports'] if c['region'] != 'east']
        # Edad cambia solo por perfil común; semilla estructural conserva parámetros.
        for name in ('viejo-00', 'viejo-03', 'viejo-07'):
            if name in manifests:
                checks[name+'-same-parameters'] = manifests[name]['base_spec']['parameters'] == pilot['base_spec']['parameters']
                checks[name+'-different-wood'] = manifests[name]['wood_sha256'] != pilot['wood_sha256']
        if matrix.get('comparison_study'):
            previous = ROOT / matrix['comparison_study']
            report['previous_study'] = matrix['comparison_study']
            for name, m in manifests.items():
                old_path = previous / name / 'manifest.json'
                if not old_path.is_file():
                    continue
                old = read(old_path)
                if old['status'] != 'completed':
                    continue  # El extremo fallido se compara con sus datos intermedios más abajo.
                if m['resolved_blueprint']['profile'] != 'joven':
                    checks[name+'-previous-wood-identical'] = m['wood_sha256'] == old['wood_sha256']
                    changed = m['surface_projection']['corrected_queries'] > 0
                    checks[name+'-previous-glb-or-explicit-projection'] = m['glb_sha256'] == old['glb_sha256'] or changed
                    checks[name+'-same-counts'] = all(m[k] == old[k] for k in ('support_count', 'leaf_count'))
                else:
                    checks[name+'-young-only-size'] = all(m[k] == old[k] for k in
                        ('wood_sha256', 'supports_sha256', 'twigs_sha256', 'support_count', 'leaf_count'))
                    strip = lambda rows: [{k:v for k,v in row.items() if k != 'length_m'} for row in rows]
                    checks[name+'-young-roots-axes'] = strip(m['placements']) == strip(old['placements'])
                    checks[name+'-young-size-factor'] = all(abs(p['length_m'] - q['length_m']*.45) < 1e-12
                        for p,q in zip(m['placements'], old['placements']))
            extreme = 'height-high-scale-low'
            if extreme in manifests:
                checks['extreme-repeat'] = manifests[extreme]['glb_sha256'] == manifests[extreme+'-repeat']['glb_sha256']
                checks['extreme-reference-unchanged'] = read(out / extreme / 'base-reference.json') == read(previous / extreme / 'base-reference.json')
                checks['extreme-keeps-previous-failed-insertion'] = all(
                    any(c['id'] == row['id'] and c['points_m'][0] == row['insertion'] for c in manifests[extreme]['supports'])
                    for row in read(previous / extreme / 'contact-diagnostic.json')['failed'])
            if 'base-seed' in manifests:
                checks['base-seed-changes-wood'] = manifests['base-seed']['wood_sha256'] != pilot['wood_sha256']
                checks['base-seed-keeps-canopy-seed'] = manifests['base-seed']['canopy_spec'] == pilot['canopy_spec']
        # Revisar las inserciones contra la madera del GLB importado, no solo la malla previa.
        write(out / 'export-contact-input.json', [str(out / name) for name in manifests])
        run('export-contacts', [os.environ.get('BLENDER_BIN', BLENDER), '--background', '--factory-startup',
            '--threads', '1', '--python-exit-code', '1', '--python', ROOT / 'blender/verify_export_contacts.py',
            '--', out / 'export-contact-input.json', out / 'export-contacts.json'])
        report['export_contacts'] = read(out / 'export-contacts.json')
        checks['all-export-contacts'] = report['export_contacts']['passed']
        write(out / 'verification.json', report)

        # Inspecciones derivadas: cámaras compartidas en toda la matriz, sin editar manifiestos de generación.
        visible = [c['id'] for c in matrix['cases'] if c['id'] in manifests and c['kind'] != 'repeat']
        wood_names = [n for n in visible if n == 'pilot' or next(c for c in matrix['cases'] if c['id']==n)['kind'] in ('age','reserved','stress')]
        write(out / 'wood-input.json', [{'source': str(out / n), 'output': str(out / 'inspection' / (n+'-wood'))} for n in wood_names])
        run('wood-inspections', [os.environ.get('BLENDER_BIN', BLENDER), '--background', '--factory-startup', '--threads', '1',
            '--python-exit-code', '1', '--python', ROOT / 'blender/inspect_blueprint_controls.py', '--', out / 'wood-input.json'])
        cameras = read(ROOT / 'configs/inspection/rf3-v1.json')['cameras']
        # Caja global y esfera envolvente: encuadre común que incluye extremos de 2/20m.
        low = [min(manifests[n]['metrics']['bounds_blender'][0][k] for n in visible) for k in range(3)]
        high = [max(manifests[n]['metrics']['bounds_blender'][1][k] for n in visible) for k in range(3)]
        center = [(a+b)/2 for a,b in zip(low,high)]
        fit = math.dist(low, high) / .88
        rig = {}
        for view in ('front','side','top','below','perspective','reverse'):
            settings = copy.deepcopy(cameras[view])
            settings['location'] = [center[k] + 80*settings['basis_columns'][2][k] for k in range(3)]
            settings['ortho_scale'] = fit
            rig[view] = settings
        # Escalas por edad, comunes para todas las variantes de 9m; comparaciones de detalle legibles.
        for view, fraction in (('near',.5),('medium',.25),('far',.1)):
            settings = copy.deepcopy(cameras[view]); rig[view] = settings
        project = out / 'godot'; project.mkdir()
        for filename in ('project.godot','verify_oak.gd','verify_foliage_molds.gd'):
            shutil.copy2(ROOT / 'godot' / filename, project / filename)
        entries = []
        for name in visible + [n+'-wood' for n in wood_names]:
            wood = name.endswith('-wood'); source_name = name[:-5] if wood else name
            folder = out / 'inspection' / name; folder.mkdir(parents=True, exist_ok=True)
            if not wood:
                for file in ('tree.glb','manifest.json'): shutil.copy2(out / name / file, folder / file)
            local_rig = copy.deepcopy(rig)
            height = manifests[source_name]['base_spec']['parameters']['height_m']
            bounds = manifests[source_name]['metrics']['bounds_blender']
            target = [(a+b)/2 for a,b in zip(*bounds)]
            for view in ('near','medium','far'):
                camera = local_rig[view]; camera['location'] = [target[k] + 80*camera['basis_columns'][2][k] for k in range(3)]
                camera['ortho_scale'] = height / camera['target_height_fraction']
            write(folder / 'cameras.json', local_rig)
            shutil.copy2(folder / 'tree.glb', project / (name+'.glb'))
            entries.append({'id':name,'folder':str(folder),'capture':args.visual,'resource':'res://'+name+'.glb'})
        run('godot-import', [os.environ.get('GODOT_BIN', GODOT), '--headless', '--path', project, '--editor', '--import'])
        report['godot'] = []
        for start in range(0,len(entries),2):
            batch = entries[start:start+2]; config = out / f'godot-input-{start}.json'; result = out / f'godot-report-{start}.json'
            write(config,batch)
            command = [os.environ.get('GODOT_BIN', GODOT), '--path', project, '--script','res://verify_foliage_molds.gd','--','--input='+str(config),'--report='+str(result)]
            run('godot-check-'+str(start), command[:1]+['--headless']+command[1:])
            if args.visual: run('godot-visual-'+str(start),command+['--visual'])
            r=read(result); assert r['passed']; report['godot'].append(r)
        report['camera_protocol'] = {'general_shared_ortho_scale':fit,'global_bounds':[low,high], 'scale_views':'Altura 50/25/10%; centro del árbol completo compartido con su madera.'}
        if args.visual:
            rows=[]
            for n in wood_names:
                rows.append([(f'inspection/{k}/godot-{v}.png',k+' | '+v) for k in (n+'-wood',n) for v in ('near','perspective')])
            sheet(out,out/'ages.jpg',4,rows)
            controls=[n for n in visible if n not in wood_names]
            sheet(out,out/'controls.jpg',3,[[(f'inspection/{n}/godot-{v}.png', n+' | '+v) for v in ('near','top','below')] for n in ['pilot']+controls])
            rows_html=[]
            for entry in entries:
                n=entry['id']; cells=''.join(f'<td><a href="inspection/{n}/godot-{v}.png"><img src="inspection/{n}/godot-{v}.png"></a></td>' for v in rig)
                rows_html.append('<tr><th>'+html.escape(n)+'</th>'+cells+'</tr>')
            (out/'index.html').write_text('<!doctype html><meta charset="utf-8"><title>B3 / RF4</title><style>body{font:16px sans-serif;background:#e9edf1}img{width:210px}th{min-width:160px}</style><h1>B3 / RF4: controles congelados</h1><p>Regla común; perfiles experimentales. Aceptación artística pendiente. Vistas generales comunes y escalas relativas a la altura; no inferir tamaño entre edades desde near.</p><a href="verification.json">Resultados, fallos y métricas</a><table>'+''.join(rows_html)+'</table>')
        report['passed'] = all(checks.values()) and all(c['status'] != 'failed' for c in report['cases'].values())
        report['matrix_executed'] = True
    finally:
        write(out / 'verification.json', report)
    print('B3 matriz ejecutada; passed='+str(report['passed']), flush=True)


if __name__ == '__main__':
    main()
