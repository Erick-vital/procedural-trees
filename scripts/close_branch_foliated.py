#!/usr/bin/env python3
"""R3: revisar rama desnuda elegida y entregar dos variantes explícitas."""
import argparse
import os
from pathlib import Path
import shutil
import sys
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'scripts')]
from review_pine_painted import read,write,sha
from verify_branch_space import run
from verify_foliage_unit import GODOT
from foliage_evidence import sheet


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--study',required=True,type=Path)
    p.add_argument('--output',type=Path,default=ROOT/'docs/evidence/f5/rama-r3')
    p.add_argument('--stage',choices=('render','evidence'),default='evidence');a=p.parse_args();study=a.study.resolve();out=a.output.resolve()
    report=read(study/'verification.json');assert report['phase']=='R3' and report['passed']
    if a.stage=='render':
        env=dict(os.environ,XDG_DATA_HOME=str(study/'xdg/data'),XDG_CONFIG_HOME=str(study/'xdg/config'),XDG_CACHE_HOME=str(study/'xdg/cache'))
        run([sys.executable,ROOT/'scripts/branch_simplification_shadows.py','--study',study],study/'logs/shadows-runner.log',env)
        folder=study/'captures/bare';folder.mkdir()
        config=read(study/'color-input.json');config.update(output=str(folder),report=str(study/'bare-godot.json'),
            assets=[{'id':'bare','resource':'res://bare.glb','metrics':report['variants']['bare']['metrics']}],
            shots=[s for s in config['shots'] if s['id'].startswith('medium-')])
        path=study/'bare-input.json';write(path,config)
        run([GODOT,'--path',study/'godot','--audio-driver','Dummy','--script','res://review_painted_oak_pilot.gd','--',path,'--visual'],
            study/'logs/bare.log',env)
        assert read(study/'bare-godot.json')['passed'];return
    out.mkdir(parents=True,exist_ok=True)
    shadow=read(study/'shadows-framed-verification.json');bare=read(study/'bare-godot.json')
    tests=(study/'logs/tests.log').read_text();assert 'Ran 233 tests' in tests and tests.rstrip().endswith('OK')
    assert bare['passed'] and all(v['lost_pixels']==0 and v['gained_pixels']==0 and v['reference_pixels']>100 for v in report['visible_wood_comparison'].values())
    for name in ('near','medium','far','visible-wood'):shutil.copy2(study/(name+'.jpg'),out/(name+'.jpg'))
    shutil.copy2(study/'shadows-framed.jpg',out/'shadows.jpg')
    views=('front','side','perspective','top','below','back')
    bare_rows=[[(f'captures/bare/bare--medium-{v}.png','R2 sin follaje | '+v) for v in views[i:i+2]] for i in range(0,6,2)]
    sheet(study,out/'bare.jpg',2,bare_rows)
    preview=[('captures/bare/bare--medium-perspective.png','Sin follaje: R2 | 894 tris'),
             ('captures/color/full--medium-perspective.png','Con follaje: R2 | 1416 tris'),
             ('captures/color/simple--medium-perspective.png','Con follaje: R3 | 1324 tris')]
    sheet(study,out/'seleccion.jpg',3,[preview])
    selected=[]
    for distance in ('near','medium','far'):
        selected += [f'color/{name}--{distance}-{v}.png' for name in ('full','simple') for v in views]
    selected += [f'visible-wood/{name}--medium-{v}.png' for name in ('full','simple') for v in views]
    for group in range(2):
        shots=[f'orbit-{i:02}' for i in range(4*group,4*(group+1))]
        sheet(study,out/f'orbit-{group}.jpg',2,[[(f'captures/color/{name}--{shot}.png',name+' '+shot) for name in ('full','simple')] for shot in shots])
        selected += [f'color/{name}--{shot}.png' for name in ('full','simple') for shot in shots]
    sheet(study,out/'masks.jpg',2,[[(f'captures/mask/{name}--medium-{v}.png',name+' '+v) for name in ('foliage-before','foliage-after')] for v in views])
    selected += [f'mask/{name}--medium-{v}.png' for name in ('foliage-before','foliage-after') for v in views]
    selected += [f'bare/bare--medium-{v}.png' for v in views]
    selected += ['shadows-framed/'+name for name in shadow['captures_sha256']]
    other=ROOT/'artifacts/f5/rama-r3-160-01/verification.json';alternative=read(other)
    registry={'date':'2026-11-03','scope':'branch_sample_only_full_tree_pending','without_foliage':{
        'variant':'R2','path':str((study/'bare/tree.glb').relative_to(ROOT)),'sha256':sha(study/'bare/tree.glb'),
        'triangles':894,'materials':1,'artistic_acceptance':'approved_by_user','decision':'docs/evidence/f5/rama-r2/user-acceptance.json'},
        'with_foliage':{'variant':'R3-alpha128','path':str((study/'simple/tree.glb').relative_to(ROOT)),'sha256':sha(study/'simple/tree.glb'),
        'triangles':1324,'materials':2,'artistic_acceptance':'pending_user','technical_selection':'lowest_cost_candidate_passing_visibility_checks'}}
    write(study/'chosen-variants.json',registry);write(out/'chosen-variants.json',registry)
    evidence={k:v for k,v in report.items() if k not in ('godot','captures_sha256','visual_review')}
    evidence.update(date='2026-11-03',study=str(study.relative_to(ROOT)),registry=registry,
        alternatives={'alpha128':{'triangles':1324,'checks_passed':report['passed'],'visual_checks':True},
                      'alpha160':{'triangles':alternative['variants']['simple']['metrics']['triangles'],'checks_passed':alternative['passed'],'visual_checks':False,'purpose':'more_conservative_fallback_not_needed'}},
        shadows=shadow,bare_godot={'passed':bare['passed'],'captures':len(bare['captures']),'godot':bare['godot'],'renderer':bare['renderer']},
        tests={'passed':233,'log_sha256':sha(study/'logs/tests.log')},
        final_capture_count=146,selected_capture_count=len(set(selected)),
        selected_capture_sha256={name:sha(study/'captures'/name) for name in sorted(set(selected))},
        alpha_profile=read(study/'alpha-profile.json'),source_frozen_sha256=sha(study/'source-frozen.json'),
        qa_sources_sha256={str(p.relative_to(ROOT)):sha(p) for p in [Path(__file__),ROOT/'tests/test_branch_interior.py',ROOT/'scripts/branch_simplification_shadows.py']},
        visual_review='pending_agent',artistic_acceptance='pending_user_for_new_foliated_variant')
    evidence['selected_sheets_sha256']={p.name:sha(p) for p in out.glob('*.jpg')};write(out/'verification.json',evidence)
    for name in ('bare','seleccion','orbit-0','orbit-1','masks'):shutil.copy2(out/(name+'.jpg'),study/(name+'.jpg'))
    sections=[('bare','Elegida sin follaje: R2 (894 tris)'),('near','Con follaje: comparación cercana'),('medium','Con follaje: distancia media'),
              ('far','Con follaje: lejos'),('orbit-0','Giro desde abajo 1'),('orbit-1','Giro desde abajo 2'),
              ('visible-wood','Madera visible en rojo'),('shadows-framed','Sombras')]
    (study/'index.html').write_text('<!doctype html><meta charset="utf-8"><title>R3: dos variantes de rama</title><style>body{font:18px sans-serif;background:#eee9df;margin:24px;max-width:1200px}img{max-width:100%}</style>'
        '<h1>Dos variantes de rama</h1><p>Sin follaje: R2 elegida, 894 tris. Con follaje: nueva R3 de 1324 tris, frente a R2 de 1416. Copa idéntica; la nueva variante queda por valorar.</p><img src="seleccion.jpg">'
        +''.join('<h2>'+title+'</h2><img src="'+name+'.jpg">' for name,title in sections))
    print('Selección:',evidence['selected_capture_count'],'de',evidence['final_capture_count'],'capturas finales.',flush=True)


if __name__=='__main__':main()
