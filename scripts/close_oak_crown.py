#!/usr/bin/env python3
"""Cierre O2: parejas reproducibles, equilibrio medido e imágenes seleccionadas."""
import argparse
from collections import Counter
import json
from pathlib import Path
import shutil
import sys
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'src'),str(ROOT/'scripts')]
from treegen.oak_crown_evaluation import crown_metrics
from treegen.branch_tree_audit import raw_channels
from treegen.oak_crossed_evaluation import channels
from review_pine_painted import read,write,sha
from foliage_evidence import sheet


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--study',type=Path,required=True);p.add_argument('--repeat',type=Path,required=True)
    p.add_argument('--tests',type=Path,required=True);p.add_argument('--output',type=Path,default=ROOT/'docs/evidence/oak-growth/o2');a=p.parse_args()
    study=a.study.resolve();out=a.output.resolve();out.mkdir(parents=True,exist_ok=True)
    matrix=read(ROOT/'configs/verification/oak-crown-v2.json');historical=read(ROOT/'docs/evidence/oak-growth/o1/verification.json')
    names=[f'maduro-{seed}' for seed in matrix['seeds']]+['joven-3100','centenario-3100'];checks={};cases={}
    for name in names:
        folder=study/name;before=study/'before'/name;old=read(before/'manifest.json');new=read(folder/'manifest.json');r=read(folder/'review.json')
        checks[name+'-generation']=all(m['status']=='completed' and all(m['checks'].values()) for m in (old,new))
        checks[name+'-sources']=all(sha(ROOT/path)==value for m in (old,new) for path,value in m['source_inventory'].items())
        checks[name+'-same-seed-and-base-controls']=old['seed']==new['seed'] and old['preset']=={**{k:v for k,v in new['preset'].items() if k!='crown_balance'},'version':'oak-growth-0.1.0'}
        checks[name+'-legacy-two-glb-exact']=all(sha(before/mode/'tree.glb')==value for mode,value in historical['cases'][name]['glb_sha256'].items())
        checks[name+'-godot']=r['passed'] and all(g['passed'] for g in r['godot'])
        raw=raw_channels(folder/'bare/tree.glb')['Painted_Bark'];core=raw_channels(folder/'scaffold/tree.glb')['Painted_Bark']
        checks[name+'-core-exact-subset']=not (Counter(core)-Counter(raw))
        checks[name+'-bark-shared']=channels(folder/'bare/tree.glb')[3]==channels(before/'bare/tree.glb')[3]
        s=read(folder/'structure.json');joins=read(folder/'joins-audit.json')
        checks[name+'-all-joins-embedded']=joins['passed'] and len(joins['joins'])==len(s['branches'])-1 and max(j['max_signed_distance_m'] for j in joins['joins'])<=1e-5
        metrics_before=crown_metrics(read(before/'structure.json'));metrics_after=crown_metrics(s)
        if name.startswith('maduro-'):
            checks[name+'-outlier-reach-reduced']=metrics_after['max_horizontal_reach_over_H']<metrics_before['max_horizontal_reach_over_H']*.85
            checks[name+'-center-offset-reduced']=metrics_after['crown_center_offset_over_H']<metrics_before['crown_center_offset_over_H']
            checks[name+'-angular-openings-retained']=metrics_after['largest_endpoint_angular_gap_deg']>20
        cases[name]={'seed':new['seed'],'stage':new['preset']['stage'],'preset_sha256':new['preset_sha256'],'balance':new['preset']['crown_balance'],
            'before':metrics_before,'after':metrics_after,'triangles_before':old['variants']['bare']['metrics']['triangles'],'triangles_after':new['variants']['bare']['metrics']['triangles'],
            'architecture_before':old['architecture'],'architecture_after':new['architecture'],'duration_seconds':new['duration_seconds'],
            'glb_sha256':{k:v['glb_sha256'] for k,v in new['variants'].items()},'manifest_sha256':sha(folder/'manifest.json'),'review_sha256':sha(folder/'review.json'),
            'captures':len(r['captures_sha256']),'height_m':new['preset']['height_m']}
        for mode in ('bare','scaffold'):shutil.copy2(folder/(mode+'-comparison.jpg'),out/(name+'-'+mode+'.jpg'))
    first=study/'maduro-3100'
    checks['two-new-glb-repeat-exact']=all(sha(first/mode/'tree.glb')==sha(a.repeat/mode/'tree.glb') for mode in ('bare','scaffold'))
    checks['new-structure-repeat-exact']=sha(first/'structure.json')==sha(a.repeat/'structure.json')
    mature=[cases[f'maduro-{s}'] for s in matrix['seeds']];checks['same-mature-preset']=len({c['preset_sha256'] for c in mature})==1
    checks['distinct-five-results']=len({c['glb_sha256']['bare'] for c in mature})==5
    age=read(study/'ages-review.json');checks['normalized-age-captures']=age['passed']
    reaches=[cases[f'{stage}-3100']['after']['max_horizontal_reach_over_H'] for stage in ('joven','maduro','centenario')]
    checks['relative-spread-age-differences']=reaches[0]<reaches[1]<reaches[2]
    tests=a.tests.read_text();checks['257-tests-pass']='Ran 257 tests' in tests and tests.rstrip().endswith('OK')
    for view in ('front','perspective'):
        sheet(study,out/('cinco-'+view+'.jpg'),2,[[(f'{name}/captures/{label}-bare--{view}.png',('Antes O1' if label=='before' else 'Ahora O2')+' | '+name) for label in ('before','after')] for name in names[:5]])
    shutil.copy2(study/'ages.jpg',out/'edades.jpg');shutil.copy2(a.tests,out/'tests.txt')
    report={'version':'oak-crown-verification-0.1.0','passed':all(checks.values()),'checks':checks,'cases':cases,'matrix':matrix,
        'matrix_sha256':sha(ROOT/'configs/verification/oak-crown-v2.json'),'source_inventory':read(first/'manifest.json')['source_inventory'],
        'captures':sum(c['captures'] for c in cases.values())+len(age['captures_sha256']),
        'age_comparison':age,'study':str(study),'visual_review':'pending_agent','artistic_acceptance':'pending_user',
        'images_sha256':{p.name:sha(p) for p in out.glob('*.jpg')}}
    write(out/'verification.json',report);assert report['passed'],[k for k,v in checks.items() if not v]
    html='<!doctype html><meta charset="utf-8"><title>O2: equilibrio de copa</title><style>body{font:18px sans-serif;background:#eee9df;margin:24px}img{max-width:100%}</style><h1>Antes O1 / ahora O2, mismas cinco semillas</h1><p>Sin hojas, mismas cámaras/luz y escala1; huecos e irregularidad conservados. Madurez comparada por separado a altura normalizada.</p>'
    images=[('cinco-perspective','Cinco semillas en perspectiva'),('cinco-front','Cinco semillas de frente'),('edades','Etapas, altura normalizada')]
    images += [(name+'-bare',name+' | árbol completo') for name in names]
    images += [(name+'-scaffold',name+' | tronco y primarias') for name in names]
    (study/'index.html').write_text(html+''.join('<h2>'+label+'</h2><img src="'+str(out/(name+'.jpg'))+'">' for name,label in images))
    print('Checks',len(checks),'capturas',report['captures'],'passed',report['passed'])

if __name__=='__main__':main()
