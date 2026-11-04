#!/usr/bin/env python3
"""Auditar y seleccionar evidencia reproducible de integración R4."""
import argparse
from collections import Counter,defaultdict
import json
from pathlib import Path
import shutil
import struct
import sys
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'src'),str(ROOT/'scripts')]
from treegen.branch_tree_audit import raw_channels
from treegen.oak_painted_sample import wood_uv
from review_pine_painted import read,write,sha
from foliage_evidence import sheet


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--study',required=True,type=Path)
    p.add_argument('--output',type=Path,default=ROOT/'docs/evidence/f5/integracion-r4');a=p.parse_args()
    study=a.study.resolve();out=a.output.resolve();out.mkdir(parents=True,exist_ok=True)
    spec=read(ROOT/'configs/verification/branch-tree-v1.json');cases={};checks={}
    f32=lambda v:struct.unpack('<f',struct.pack('<f',v))[0]
    for case in spec['cases']:
        name=case['id'];folder=study/name;m=read(folder/'manifest.json');review=read(folder/'review.json');plan=read(folder/'tree-plan.json')
        checks[name+'-generation']=m['status']=='completed' and all(m['checks'].values())
        checks[name+'-godot']=review['passed'] and all(review['checks'].values())
        checks[name+'-sources']=all(sha(ROOT/p)==value for p,value in m['sources_sha256'].items())
        reference={b['id']:b for b in read(folder/'source/base-reference.json')['branches']}
        checks[name+'-major-meshes-source-exact']=all(b['mesh']=={**reference[b['id']]['mesh'],'uv':wood_uv(reference[b['id']])} for b in plan['majors'])
        positions={(f32(v[0]),f32(v[2]),f32(-v[1])) for b in plan['majors'] for v in b['mesh']['vertices']}
        before=raw_channels(folder/'source/tree.glb')['Painted_Bark'];expected=[t for t in before if all(v[:3] in positions for v in t)]
        checks[name+'-major-raw-position-normal-uv-exact']=len(expected)==plan['major_triangles'] and all(not (Counter(expected)-Counter(raw_channels(folder/mode/'tree.glb')['Painted_Bark'])) for mode in ('bare','full','simple'))
        networks=[read(p) for p in sorted((folder/'networks').glob('*/network.json'))]
        connected=True;roots_exact=True
        for n in networks:
            original={e['id']:e for e in n['bare']['edges']};current={e['id']:e for e in n['foliated']['edges']}
            roots_exact &= all(e['id'] in current and current[e['id']]['mesh']==e['mesh'] for e in original.values() if e['parent'] is None)
            for mode in ('bare','foliated'):
                edges=n[mode]['edges'];index={e['id']:e for e in edges};degree=defaultdict(int)
                connected &= len(edges)==len(index) and sum(e['parent'] is None for e in edges)==3
                for e in edges:
                    if e['parent'] is not None:
                        connected &= e['parent'] in index and e['points'][0]==index[e['parent']]['points'][-1];degree[e['parent']]+=1
                connected &= max(degree.values(),default=0)<=3
        checks[name+'-connected-networks']=bool(connected);checks[name+'-roots-exact']=bool(roots_exact)
        cases[name]={'profile':case['profile'],'seeds':case['seeds'],'duration_seconds':m['duration_seconds'],'groups':m['groups'],
            'triangles':{k:v['metrics']['triangles'] for k,v in m['variants'].items() if k in ('bare','full','simple')},
            'networks':m['networks'],'checks':m['checks'],'visual_checks':review['checks'],
            'image_comparison':review['image_comparison'],'shadow_comparison':review['shadow_comparison'],
            'visible_wood_comparison':review['visible_wood_comparison'],'captures':len(review['captures_sha256']),
            'glb_sha256':{k:v['glb_sha256'] for k,v in m['variants'].items()},'manifest_sha256':sha(folder/'manifest.json'),
            'review_sha256':sha(folder/'review.json'),'renderer':review['godot']['color']['runs'][0]['renderer'],
            'video_adapter':review['godot']['color']['runs'][0]['video_adapter']}
        for image in ('near','medium','far','bare','visible-wood','shadows'):
            shutil.copy2(folder/(image+'.jpg'),out/(name+'-'+image+'.jpg'))
        orbit=[f'orbit-{i:02}' for i in range(8)]
        sheet(folder,out/(name+'-orbit.jpg'),2,[[(f'captures/color/{mode}--{shot}.png',mode+' '+shot) for mode in ('full','simple')] for shot in orbit])
    repeat=ROOT/'artifacts/f5/integracion-r4-repeat-01';first=study/'joven-03'
    checks['five-exports-repeat-exact']=all(sha(first/name/'tree.glb')==sha(repeat/name/'tree.glb') for name in read(first/'exports.json')['variants'])
    checks['source-repeat-exact']=sha(first/'source/tree.glb')==sha(repeat/'source/tree.glb')
    checks['historical-roble-220-exact']=sha(ROOT/'artifacts/f5/integracion-r4-regresion-01/tree.glb')==sha(ROOT/'artifacts/roble-pintado/integracion-madera-01/pilot/tree.glb')
    checks['approved-r2-sample-exact']=read(first/'networks/01/network.json')['bare']==read(ROOT/'artifacts/f5/rama-r2-03/network-simple.json')
    tests=Path('/tmp/arboles-r4-tests-final.log').read_text();checks['239-tests-pass']='Ran 239 tests' in tests and tests.rstrip().endswith('OK')
    sheet(study,out/'seleccion.jpg',3,[[(name+'/captures/structure/source--medium-perspective.png',name+' | madera anterior'),
        (name+'/captures/structure/bare--medium-perspective.png',name+' | R2 sin hojas'),
        (name+'/captures/color/simple--medium-perspective.png',name+' | R3 con copa')] for name in cases])
    sheet(study,out/'copa.jpg',2,[[(name+'/captures/baseline/source--medium-perspective.png',name+' | copa anterior'),
        (name+'/captures/baseline/simple--medium-perspective.png',name+' | copa conservada')] for name in cases])
    report={'version':'branch-tree-integration-verification-0.1.0','passed':all(checks.values()),'checks':checks,'cases':cases,
        'matrix_sha256':sha(ROOT/'configs/verification/branch-tree-v1.json'),'definition_sha256':sha(ROOT/'configs/branch-tree/0.1.0.json'),
        'source_inventory':read(first/'manifest.json')['sources_sha256'],'artistic_acceptance':'pending_user_complete_trees',
        'visual_review':'pending_agent','study':str(study),'total_captures':sum(c['captures'] for c in cases.values()),
        'evidence_images_sha256':{p.name:sha(p) for p in out.glob('*.jpg')}}
    write(out/'verification.json',report);shutil.copy2('/tmp/arboles-r4-tests-final.log',out/'tests.txt')
    assert report['passed'],[k for k,v in checks.items() if not v]
    html='<!doctype html><meta charset="utf-8"><title>Integración de ramificación R4</title><style>body{font:18px sans-serif;background:#eee9df;margin:24px}img{max-width:100%}a{margin-right:20px}</style><h1>Robles con ramificación integrada</h1><p>Madera anterior / R2 sin hojas / R3 con copa intacta. Revisión artística del árbol completo pendiente.</p><img src="'+str(out/'seleccion.jpg')+'">'
    html+=''.join('<p><a href="'+name+'/index.html">'+name+'</a></p>' for name in cases)
    (study/'index.html').write_text(html)
    print('Checks',len(checks),'capturas',report['total_captures'],'passed',report['passed'])

if __name__=='__main__':main()
