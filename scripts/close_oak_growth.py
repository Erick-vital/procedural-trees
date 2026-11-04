#!/usr/bin/env python3
"""Seleccionar evidencia y auditar O1 sin confundir métricas con reconocimiento botánico."""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import shutil
import sys
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'src'),str(ROOT/'scripts')]
from treegen.oak_growth import generate
from treegen.oak_growth_runner import architecture_metrics
from treegen.branch_tree_audit import raw_channels
from treegen.oak_crossed_evaluation import channels
from review_pine_painted import read,write,sha
from foliage_evidence import sheet


def digest(data):return hashlib.sha256(json.dumps(data,sort_keys=True,allow_nan=False,separators=(',',':')).encode()).hexdigest()


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--study',required=True,type=Path);p.add_argument('--repeat',required=True,type=Path)
    p.add_argument('--regression',required=True,type=Path);p.add_argument('--tests',required=True,type=Path)
    p.add_argument('--output',type=Path,default=ROOT/'docs/evidence/oak-growth/o1');a=p.parse_args();study=a.study.resolve();out=a.output.resolve();out.mkdir(parents=True,exist_ok=True)
    matrix=read(ROOT/'configs/verification/oak-growth-v1.json');cases={};checks={};reference_checks={};ablation={}
    names=[f'maduro-{seed}' for seed in matrix['seeds']]+['joven-3100','centenario-3100']
    bark=sha(ROOT/'assets/roble-pintado/v0.2.0/bark.png')
    for name in names:
        folder=study/name;m=read(folder/'manifest.json');review=read(folder/'review.json');structure=read(folder/'structure.json')
        checks[name+'-generation']=m['status']=='completed' and all(m['checks'].values())
        checks[name+'-source-inventory']=all(sha(ROOT/path)==value for path,value in m['source_inventory'].items())
        checks[name+'-godot']=review['passed'] and all(g['passed'] for g in review['godot'])
        checks[name+'-shared-bark']=channels(folder/'bare/tree.glb')[3]==[bark]
        raw=raw_channels(folder/'bare/tree.glb')['Painted_Bark'];core=raw_channels(folder/'scaffold/tree.glb')['Painted_Bark']
        checks[name+'-scaffold-attributes-exact-subset']=not (Counter(core)-Counter(raw))
        joins=read(folder/'joins-audit.json');checks[name+'-all-joins-audited']=len(joins['joins'])==len(structure['branches'])-1 and max(j['max_signed_distance_m'] for j in joins['joins'])<=1e-5
        cases[name]={'seed':m['seed'],'preset':m['preset'],'preset_sha256':m['preset_sha256'],'triangles':m['variants']['bare']['metrics']['triangles'],
            'scaffold_triangles':m['variants']['scaffold']['metrics']['triangles'],'architecture':m['architecture'],'duration_seconds':m['duration_seconds'],
            'glb_sha256':{mode:item['glb_sha256'] for mode,item in m['variants'].items()},'manifest_sha256':sha(folder/'manifest.json'),
            'review_sha256':sha(folder/'review.json'),'bounds_blender':m['variants']['bare']['metrics']['bounds_blender'],
            'checks':m['checks'],'captures':len(review['captures_sha256']),'display_scales':review['display_transforms']}
        if name.startswith('maduro-'):
            old=study/'references'/name;before=read(old/'manifest.json')
            reference_checks[name]=before['status']=='completed' and before['request']['seeds']['base']==m['seed']
            cases[name]['reference']={'source':str(old.resolve()),'bare_triangles':before['variants']['bare']['metrics']['triangles'],
                'glb_sha256':sha(old/'bare/tree.glb'),'display_scale':review['display_transforms']['old']}
            baseline=generate(m['preset'],m['seed'],spatial=False)
            ablation[name]={'enabled_architecture':m['architecture'],'disabled_architecture':architecture_metrics(baseline),
                'enabled_branch_sha256':digest(structure['branches']),'disabled_branch_sha256':digest(baseline['branches']),
                'scope':'diagnóstico algorítmico sin capturas ni afirmación de mejora artística/colisiones'}
        shutil.copy2(folder/'comparison.jpg',out/(name+'.jpg'))
    checks['five-references-same-seeds']=all(reference_checks.values()) and len(reference_checks)==5
    checks['same-mature-preset-five-seeds']=len({cases[f'maduro-{seed}']['preset_sha256'] for seed in matrix['seeds']})==1
    checks['five-distinct-architectures']=len({ablation[name]['enabled_branch_sha256'] for name in ablation})==5
    checks['spatial-rule-changes-geometry']=all(v['enabled_branch_sha256']!=v['disabled_branch_sha256'] for v in ablation.values())
    first=study/'maduro-3100';repeat=a.repeat.resolve()
    checks['structure-repeat-exact']=sha(first/'structure.json')==sha(repeat/'structure.json')
    checks['two-glb-repeat-exact']=all(sha(first/mode/'tree.glb')==sha(repeat/mode/'tree.glb') for mode in ('bare','scaffold'))
    expected=read(ROOT/'docs/evidence/f5/integracion-r4/verification.json')['cases']['joven-03']['glb_sha256']
    checks['historical-r4-five-glb-exact']=all(sha(a.regression/mode/'tree.glb')==value for mode,value in expected.items())
    ages=read(study/'ages-review.json');checks['normalized-age-review']=ages['passed']
    tests=a.tests.read_text();checks['249-tests-pass']='Ran 249 tests' in tests and tests.rstrip().endswith('OK')
    shutil.copy2(a.tests,out/'tests.txt');shutil.copy2(study/'ages.jpg',out/'edades-cuatro-vistas.jpg')
    stages=('joven','maduro','centenario')
    sheet(study,out/'edades.jpg',3,[[(f'age-captures/{stage}--front.png',stage+' | misma altura visual') for stage in stages]])
    for filename,mode,label in [('variacion','bare','Cuatro órdenes'),('primarias','scaffold','Solo tronco y primarias')]:
        sheet(study,out/(filename+'.jpg'),2,[[(f'{name}/captures/{mode}--{view}.png',name+' | '+label+' | '+view) for view in ('front','perspective')] for name in names[:5]])
    report={'version':'oak-growth-verification-0.1.0','passed':all(checks.values()),'checks':checks,'cases':cases,'spatial_ablation':ablation,
        'matrix':matrix,'matrix_sha256':sha(ROOT/'configs/verification/oak-growth-v1.json'),
        'source_inventory':read(first/'manifest.json')['source_inventory'],'captures':sum(v['captures'] for v in cases.values())+len(ages['captures_sha256']),
        'artist_acceptance':'pending_user','visual_review':'pending_agent','study':str(study),
        'age_comparison':{'display_scale':ages['display_scale'],'meaning':ages['meaning']},'images_sha256':{p.name:sha(p) for p in out.glob('*.jpg')}}
    write(out/'verification.json',report);assert report['passed'],[k for k,v in checks.items() if not v]
    html='<!doctype html><meta charset="utf-8"><title>Roble O1: arquitectura y madurez</title><style>body{font:18px sans-serif;background:#eee9df;margin:24px}img{max-width:100%}a{display:block}</style><h1>Roble: arquitectura y madurez</h1><p>Sin hojas. R4 anterior / tronco y primarias O1 / cuatro órdenes O1. Valoración artística pendiente.</p>'
    for filename,title in [('edades-cuatro-vistas','Etapas de madurez; altura visual normalizada'),('variacion','Cinco semillas, mismo preset maduro'),('primarias','Arquitectura principal')]+[(name,name) for name in names[:5]]:
        html+='<h2>'+title+'</h2><img src="'+str(out/(filename+'.jpg'))+'">'
    (study/'index.html').write_text(html)
    print('Checks',len(checks),'capturas',report['captures'],'passed',report['passed'])

if __name__=='__main__':main()
