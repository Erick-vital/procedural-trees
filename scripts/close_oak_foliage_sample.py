#!/usr/bin/env python3
"""OF1: congelar evidencia de rama, repetición y presupuesto sin integrar copa."""
import argparse
from pathlib import Path
import shutil
import sys
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'src'),str(ROOT/'scripts')]
from review_pine_painted import read,write,sha
from foliage_evidence import sheet


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--study',type=Path,required=True);p.add_argument('--repeat',type=Path,required=True);p.add_argument('--tests',type=Path,required=True);p.add_argument('--output',type=Path,default=ROOT/'docs/evidence/oak-foliage/of1');a=p.parse_args()
    study=a.study.resolve();out=a.output.resolve();m=read(study/'manifest.json');r=read(study/'review.json');checks=dict(m['checks'])
    checks['generation']=m['status']=='completed';checks['sources']=all(sha(ROOT/f)==h for f,h in m['source_inventory'].items())
    checks['resources']=all(sha(ROOT/v['path'])==v['sha256'] for v in m['resources'].values())
    checks['godot']=r['passed'] and all(x['passed'] for x in r['godot'])
    checks['captures']=len(r['captures_sha256'])==36 and all(sha(study/'captures'/f)==h for f,h in r['captures_sha256'].items())
    checks['repeat-glb']=all(sha(study/name/'tree.glb')==sha(a.repeat/name/'tree.glb') for name in m['variants'])
    checks['repeat-layout']=sha(study/'layout.json')==sha(a.repeat/'layout.json') and sha(study/'o5-structure.json')==sha(a.repeat/'o5-structure.json')
    tests=a.tests.read_text();checks['281-tests']='Ran 281 tests' in tests and tests.rstrip().endswith('OK')
    checks['real-shadow-receiver']=any(s.get('receiver') is True for s in r['shots'])
    out.mkdir(parents=True,exist_ok=True)
    for name in ('comparison.jpg','appearance.jpg'):shutil.copy2(study/name,out/name)
    for source,target in [('painted--perspective.png','rama.png'),('painted--contact-close.png','contacto.png'),('painted--shadow_perspective.png','sombras.png')]:shutil.copy2(study/'captures'/source,out/target)
    shutil.copy2(a.tests,out/'tests.txt')
    write(out/'verification.json',{'version':'oak-foliage-sample-verification-0.1.0','passed':all(checks.values()),'checks':checks,
        'study':str(study),'generation':m,'contacts':read(study/'contacts-audit.json'),'review':r,
        'visual_review':'pending_agent','artistic_acceptance':'pending_user','tree_foliage_integration':'not_started',
        'images_sha256':{p.name:sha(p) for p in out.iterdir() if p.suffix in ('.jpg','.png')}})
    assert all(checks.values()),[k for k,v in checks.items() if not v]
    print('OF1:',len(checks),'checks correctos;',len(r['captures_sha256']),'capturas;',m['group_count'],'grupos.')

if __name__=='__main__':main()
