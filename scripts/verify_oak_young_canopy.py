#!/usr/bin/env python3
"""J2: auditoría del lote joven completo y galería Godot reproducible."""
import argparse
import copy
import html
import math
import os
from pathlib import Path
import shutil
import sys
from collections import Counter
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'src'),str(ROOT/'scripts')]
from treegen.language import load_plan
from treegen.blueprints import canonical_hash
from treegen.branch_tree_audit import raw_channels
from treegen.evaluation import validate_result
from review_pine_painted import read,write,run,sha,camera
from verify_foliage_unit import GODOT
from foliage_evidence import sheet


def audit(out):
    _,_,rows=load_plan(out/'plan')
    assert read(out/'trees/batch.json')['status']=='completed' and read(out/'repeat/batch.json')['status']=='completed'
    accepted=read(ROOT/'docs/evidence/roble-joven/j1/user-acceptance.json')
    checks={};cases={}
    for row in rows:
        name=row['id'];directory=out/'trees'/name
        m=read(directory/'manifest.json');rm=read(out/'repeat'/name/'manifest.json')
        for folder,manifest in ((directory,m),(out/'repeat'/name,rm)):
            assert sha(folder/'tree.glb')==manifest['glb_sha256']
            assert all(sha(folder/file)==h for file,h in manifest['files_sha256'].items())
            assert all(manifest['export_validation']['checks'].values())
        checks[name+'-repeat']=m['export_validation']==rm['export_validation']
        checks[name+'-same-inputs']=m['resolved_blueprint']['instance_request']==rm['resolved_blueprint']['instance_request']==row['instance']
        checks[name+'-same-sources']=m['sources_sha256']==rm['sources_sha256']
        checks[name+'-export']=all(m['export_validation']['checks'].values())
        checks[name+'-budget']=m['metrics']['triangles']<=6279 and len(m['metrics']['triangles_by_material'])==2
        wood=ROOT/'artifacts/roble-joven/j1-madera-01'/name/'bare/tree.glb'
        checks[name+'-approved-wood']=sha(wood)==accepted['approved_wood_glbs_sha256'][name] and raw_channels(directory/'tree.glb')['Painted_Bark']==raw_channels(wood)['Painted_Bark']
        p=read(directory/'prepared-canopy.json')
        cases[name]={'seeds':row['instance']['seeds'],'triangles':m['metrics']['triangles'],'materials':m['metrics']['triangles_by_material'],
            'glb_sha256':m['glb_sha256'],'geometry_sha256':m['export_validation']['geometry_sha256'],
            'maximum_contact_error_m':m['export_validation']['maximum_contact_error_m'],'duration_seconds':m['duration_seconds'],
            'initial_primary_quotas':p['ledger']['initial_primary_quotas'],'primary_quotas':p['ledger']['primary_quotas'],
            'redistributed_groups':p['ledger']['redistributed_groups']}
    p=read(out/'trees/joven-3100/prepared-canopy.json')
    selected=[g for g in p['groups'] if g['parent_branch_id'].split('/')[0]=='p:0']
    checks['approved-pilot-groups-exact']=canonical_hash(selected)==accepted['approved_branch_groups_sha256']
    # Comparar también caras, UV y normales float32 reales de la muestra con el GLB completo.
    full=raw_channels(out/'trees/joven-3100/tree.glb');branch=raw_channels(ROOT/'artifacts/roble-joven/j1-rama-01/painted/tree.glb')
    checks['approved-branch-wood-subset']=not(Counter(branch['Painted_Bark'])-Counter(full['Painted_Bark']))
    checks['approved-branch-foliage-subset']=not(Counter(branch['Painted_Foliage'])-Counter(full['Painted_Foliage']))
    checks['four-distinct-geometries']=len({r['geometry_sha256'] for r in cases.values()})==4
    checks['mature-300-regression']=read(out/'mature-regression/manifest.json')['glb_sha256']==read(ROOT/'docs/evidence/oak-foliage/of11/user-acceptance.json')['approved_glb_sha256']
    checks['pilot-cli-identical']=read(ROOT/'artifacts/roble-joven/j2-piloto-01/manifest.json')['glb_sha256']==cases['joven-3100']['glb_sha256']
    result={'date':'2026-11-04','version':'oak-young-canopy-verification-1.0','passed':all(checks.values()),'checks':checks,'cases':cases,
            'artistic_acceptance':'pending-user','visual_review':'pending','recipe_sha256':sha(ROOT/'blueprints/roble_copa_ancha/3.1.0.json'),
            'plan_sha256':sha(out/'plan/plan.json'),'generation_sources_sha256':m['sources_sha256'],
            'no_performance_tests':True}
    if (out/'verification.json').is_file():
        previous=read(out/'verification.json')
        for key in ('godot_reports','captures_sha256','review_protocol_sha256','visual_captures_generated'):
            if key in previous:result[key]=previous[key]
    write(out/'verification.json',result);assert result['passed'],checks
    print('J2 auditado:',len(checks),'checks; cuatro GLB repetidos y madera/muestra exactas.',flush=True)

def review(out):
    if (out/'verification.json').exists():
        result = read(out/'verification.json')
    else:
        batch = read(out/'trees/batch.json')
        assert batch['status'] == 'completed' and len(batch['cases']) == 4
        result = {'version': 'oak-central-family-1.0', 'passed': False,
                  'technical_audit': 'pending', 'visual_review': 'pending',
                  'artistic_acceptance': 'pending-user',
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
    (out/'index.html').write_text('<!doctype html><meta charset="utf-8"><title>Roble3.1.0 · cuatro jóvenes</title>'
        '<style>body{font:18px sans-serif;background:#eee9df;margin:24px}img{max-width:100%}a{color:#174a35}</style>'
        '<h1>Roble3.1.0 · cuatro jóvenes</h1><p>Semillas3100–3103 · distribución17 · pintura2718. '
        'Mismas cámaras, luz y perfil. Perspectiva provisional; no es la cámara final del juego. '
        'Aprobación artística del árbol completo pendiente; madera y rama p:0 previamente aprobadas.</p>'
        '<p><a href="verification.json">Auditoría</a> · <a href="review-protocol.json">Cámaras y protocolo</a></p>'
        + ''.join('<h2>'+html.escape(label)+'</h2><a href="'+name+'.jpg"><img src="'+name+'.jpg"></a>' for name,label in sections))



def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True);p.add_argument('--stage',choices=('audit','review'),required=True);a=p.parse_args()
    (audit if a.stage=='audit' else review)(a.output.resolve())

if __name__=='__main__':main()
