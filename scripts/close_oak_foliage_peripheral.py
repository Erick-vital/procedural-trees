#!/usr/bin/env python3
"""Cerrar OF4 con exportación repetida, recursos y capturas auditadas."""
import argparse
from pathlib import Path
import shutil
import sys
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'src'),str(ROOT/'scripts')]
from review_pine_painted import read,write,sha
from close_oak_foliage_chains import plane_area
from foliage_evidence import sheet


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--study',type=Path,required=True);p.add_argument('--repeat',type=Path,required=True);p.add_argument('--tests',type=Path,required=True);p.add_argument('--output',type=Path,default=ROOT/'docs/evidence/oak-foliage/of4');a=p.parse_args()
    study=a.study.resolve();out=a.output.resolve();m=read(study/'manifest.json');layout=read(study/'layout.json');review=read(study/'review.json');checks=dict(m['checks'])
    checks['generation']=m['status']=='completed'
    checks['sources']=all(sha(ROOT/p)==h for p,h in m['source_inventory'].items())
    checks['repeat-exports']=all(sha(study/n/'tree.glb')==sha(a.repeat/n/'tree.glb') for n in m['variants'])
    checks['repeat-layout-structure']=all(sha(study/n)==sha(a.repeat/n) for n in ('layout.json','o5-structure.json','baseline-groups.json'))
    checks['godot']=review['passed'] and all(r['passed'] for r in review['godot'])
    checks['capture-integrity']=len(review['captures_sha256'])==46 and all(sha(study/'captures'/p)==h for p,h in review['captures_sha256'].items())
    checks['review-protocol']=sha(ROOT/'scripts/prepare_oak_foliage_peripheral.py')==review['protocol_source_sha256']
    for name,scope in [('baseline','tree'),('painted','tree'),('sample-old','sample'),('sample-new','sample')]:
        checks[name+'-common-cameras']=read(study/(name+'-review-input.json'))['shots']==review['protocols'][scope]
    tests=a.tests.read_text();checks['299-tests']='Ran 299 tests' in tests and tests.rstrip().endswith('OK')
    mask=read(study/'mask-review.json')
    checks['masks-godot']=mask['passed'] and all(r['passed'] for r in mask['godot'])
    checks['masks-integrity']=len(mask['captures_sha256'])==8 and all(sha(study/'masks'/p)==h for p,h in mask['captures_sha256'].items())
    checks['mask-sources']=all(sha(ROOT/p)==h for p,h in mask['sources_sha256'].items())
    checks['mask-common-cameras']=all(read(study/(n+'-mask-input.json'))['shots']==mask['shots'] for n in ('baseline','painted'))
    checks['projected-coverage-increases-four-views']=all(row['painted']['foreground_pixels']>row['baseline']['foreground_pixels'] for row in mask['metrics'].values())
    checks['fixed-5010-triangles']=m['variants']['painted']['metrics']['triangles']==m['variants']['baseline']['metrics']['triangles']==5010
    out.mkdir(parents=True,exist_ok=True)
    for n in ('comparison.jpg','appearance.jpg','branch.jpg','preview.jpg','masks.jpg'):shutil.copy2(study/n,out/n)
    for n in ('perspective','top','front'):shutil.copy2(study/'captures'/f'painted--{n}.png',out/f'{n}.png')
    shutil.copy2(a.tests,out/'tests.txt')
    sheet(study,study/'before-after.jpg',2,[[(f'captures/{n}--perspective.png',label) for n,label in [('baseline','OF3 anterior'),('painted','OF4 llenado periférico')]]])
    shutil.copy2(study/'before-after.jpg',out/'before-after.jpg')
    html=study/'index.html'
    if 'masks.jpg' not in html.read_text():html.write_text(html.read_text()+'<h2>Follaje visible: OF3 / OF4</h2><img src="masks.jpg">')
    report={'version':'oak-foliage-canopy-verification-0.4.0','passed':all(checks.values()),'checks':checks,
        'generation':m,'study':str(study),'repeat':str(a.repeat.resolve()),'review':review,
        'mask_review':mask,'geometric_control_seeds':[3101,3102,3103],'controls_scope':'unit geometry only; no Godot or art acceptance',
        'layout_summary':{k:layout[k] for k in ('fork_quotas','masses','diagnostics','minimum_card_radius_m')},
        'contacts':read(study/'contacts-audit.json'),
        'leaf_plane_area_m2':{n:plane_area(study/n/'tree.glb') for n in ('baseline','painted')},
        'visual_review':'pending_agent','artistic_acceptance':'pending_user','scope':'mature 3100 pilot only; no other ages or production promotion',
        'analysis_source_sha256':sha(Path(__file__)),
        'images_sha256':{p.name:sha(p) for p in out.iterdir() if p.suffix in ('.png','.jpg')}}
    write(out/'verification.json',report)
    assert all(checks.values()),[k for k,v in checks.items() if not v]
    print('OF4:',len(checks),'checks; 46 capturas y 8 máscaras verificadas; 6 GLB repetidos exactos.')

if __name__=='__main__':main()
