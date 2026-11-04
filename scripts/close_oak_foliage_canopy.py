#!/usr/bin/env python3
"""Cerrar OF3 con exportación repetida, recursos y capturas auditadas."""
import argparse
from pathlib import Path
import shutil
import sys
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'src'),str(ROOT/'scripts')]
from review_pine_painted import read,write,sha
from close_oak_foliage_chains import plane_area


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--study',type=Path,required=True);p.add_argument('--repeat',type=Path,required=True);p.add_argument('--tests',type=Path,required=True);p.add_argument('--output',type=Path,default=ROOT/'docs/evidence/oak-foliage/of3');a=p.parse_args()
    study=a.study.resolve();out=a.output.resolve();m=read(study/'manifest.json');layout=read(study/'layout.json');review=read(study/'review.json');checks=dict(m['checks'])
    checks['generation']=m['status']=='completed'
    checks['sources']=all(sha(ROOT/p)==h for p,h in m['source_inventory'].items())
    checks['repeat-exports']=all(sha(study/n/'tree.glb')==sha(a.repeat/n/'tree.glb') for n in m['variants'])
    checks['repeat-layout-structure']=all(sha(study/n)==sha(a.repeat/n) for n in ('layout.json','o5-structure.json','baseline-groups.json'))
    checks['godot']=review['passed'] and all(r['passed'] for r in review['godot'])
    checks['capture-integrity']=len(review['captures_sha256'])==46 and all(sha(study/'captures'/p)==h for p,h in review['captures_sha256'].items())
    checks['review-protocol']=sha(ROOT/'scripts/prepare_oak_foliage_canopy.py')==review['protocol_source_sha256']
    for name,scope in [('baseline','tree'),('painted','tree'),('sample-old','sample'),('sample-new','sample')]:
        checks[name+'-common-cameras']=read(study/(name+'-review-input.json'))['shots']==review['protocols'][scope]
    tests=a.tests.read_text();checks['293-tests']='Ran 293 tests' in tests and tests.rstrip().endswith('OK')
    out.mkdir(parents=True,exist_ok=True)
    for n in ('comparison.jpg','appearance.jpg','branch.jpg','preview.jpg'):shutil.copy2(study/n,out/n)
    for n in ('perspective','top','front'):shutil.copy2(study/'captures'/f'painted--{n}.png',out/f'{n}.png')
    shutil.copy2(a.tests,out/'tests.txt')
    report={'version':'oak-foliage-canopy-verification-0.3.0','passed':all(checks.values()),'checks':checks,
        'generation':m,'study':str(study),'repeat':str(a.repeat.resolve()),'review':review,
        'layout_summary':{k:layout[k] for k in ('fork_quotas','masses','diagnostics','minimum_card_radius_m')},
        'contacts':read(study/'contacts-audit.json'),
        'leaf_plane_area_m2':{n:plane_area(study/n/'tree.glb') for n in ('baseline','painted')},
        'visual_review':'pending_agent','artistic_acceptance':'pending_user','scope':'mature 3100 pilot only; no other ages or production promotion',
        'analysis_source_sha256':sha(Path(__file__)),
        'images_sha256':{p.name:sha(p) for p in out.iterdir() if p.suffix in ('.png','.jpg')}}
    write(out/'verification.json',report)
    assert all(checks.values()),[k for k,v in checks.items() if not v]
    print('OF3:',len(checks),'checks; 46 capturas verificadas; 6 GLB repetidos exactos.')

if __name__=='__main__':main()
