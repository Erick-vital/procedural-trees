#!/usr/bin/env python3
"""OF2: cerrar comparación técnica de masas; aceptación artística separada."""
import argparse
from pathlib import Path
import shutil
import sys
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'src'),str(ROOT/'scripts')]
from review_pine_painted import read,write,sha
from treegen.oak_crossed_evaluation import channels
from treegen.branch_structure import sub,length
from treegen.oak_growth import cross
from oak_foliage_chain_masks import measure
from foliage_evidence import sheet


def plane_area(path):
    _,rows,_,_=channels(path)
    return sum(length(cross(sub(t[1][:3],t[0][:3]),sub(t[2][:3],t[0][:3])))/2 for t in rows['Painted_Foliage'])


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--study',type=Path,required=True);p.add_argument('--repeat',type=Path,required=True);p.add_argument('--tests',type=Path,required=True);p.add_argument('--output',type=Path,default=ROOT/'docs/evidence/oak-foliage/of2');a=p.parse_args()
    study=a.study.resolve();out=a.output.resolve();checks={};cases={};layouts={};areas={}
    reference=read(ROOT/'docs/evidence/oak-foliage/of1/verification.json')['generation']
    for v in 'ABC':
        folder=study/v;m=read(folder/'manifest.json');layout=read(folder/'layout.json');layouts[v]=layout;contacts=read(folder/'contacts-audit.json')
        checks.update({v+'-'+k:value for k,value in m['checks'].items()})
        checks[v+'-generation']=m['status']=='completed'
        checks[v+'-sources']=all(sha(ROOT/p)==h for p,h in m['source_inventory'].items())
        checks[v+'-repeat']=all(sha(folder/name/'tree.glb')==sha(a.repeat/v/name/'tree.glb') for name in m['variants']) and sha(folder/'layout.json')==sha(a.repeat/v/'layout.json')
        checks[v+'-same-o5-wood']=m['variants']['bare']['glb_sha256']==reference['variants']['bare']['glb_sha256']
        checks[v+'-sample-budget']=m['group_count']==64 and m['variants']['painted']['metrics']['triangles']==1030
        checks[v+'-contacts']=contacts['passed'];areas[v]=plane_area(folder/'painted/tree.glb')
        cases[v]={'generation':m,'mass_count':len(layout['masses']),'masses':layout['masses'],'links':layout['mass_links'],
            'diagnostics':layout['diagnostics'],'leaf_plane_area_m2':areas[v],'contacts_maximum_error_m':contacts['maximum_error_m']}
    signature=lambda l:[(g['size_m'],g['template_index']) for g in l['groups']]
    checks['equal-group-size-template-sequence']=signature(layouts['A'])==signature(layouts['B'])==signature(layouts['C'])
    checks['equal-exported-plane-area']=max(areas.values())-min(areas.values())<max(areas.values())*1e-5
    checks['distinct-layouts']=len({sha(study/v/'layout.json') for v in 'ABC'})==3
    review=read(study/'review.json');checks['godot']=review['passed'] and all(r['passed'] for r in review['godot']+review['mask_godot'])
    checks['captures']=len(review['captures_sha256'])==68 and all(sha(study/'captures'/f)==h for f,h in review['captures_sha256'].items())
    checks['masks']=len(review['masks_sha256'])==20 and all(sha(study/'masks'/f)==h for f,h in review['masks_sha256'].items())
    checks['protocol']=sha(ROOT/'scripts/compare_oak_foliage_chains.py')==review['protocol_source_sha256']
    for v in ('OF1','A','B','C'):
        c=read(study/(v+'-review-input.json'));checks[v+'-same-cameras-light']=c['shots']==review['shots']
    tests=a.tests.read_text();checks['287-tests']='Ran 287 tests' in tests and tests.rstrip().endswith('OK')
    metrics=measure(study);out.mkdir(parents=True,exist_ok=True)
    for n in ('comparison.jpg','appearance.jpg','preview.jpg'):shutil.copy2(study/n,out/n)
    for v in 'ABC':shutil.copy2(study/'captures'/f'{v}--perspective.png',out/f'{v}.png')
    sheet(study,out/'masks.jpg',4,[[(f'masks/{v}-foliage--{view}.png',v+' | '+view) for v in ('OF1','A','B','C')] for view in ('front','side','perspective','top')])
    shutil.copy2(a.tests,out/'tests.txt')
    report={'version':'oak-foliage-chain-verification-0.1.0','passed':all(checks.values()),'checks':checks,'cases':cases,
        'study':str(study),'review':review,'mask_metrics':metrics,'scope':'same mature branch only; age controls and full-tree foliage not integrated',
        'visual_review':'pending_agent','artistic_acceptance':'pending_user','analysis_sources':{str(p.relative_to(ROOT)):sha(p) for p in [Path(__file__).resolve(),ROOT/'scripts/oak_foliage_chain_masks.py']},
        'images_sha256':{p.name:sha(p) for p in out.iterdir() if p.suffix in ('.jpg','.png')}}
    write(out/'verification.json',report);assert all(checks.values()),[k for k,v in checks.items() if not v]
    print('OF2:',len(checks),'checks correctos; 68 capturas y 20 máscaras.')
    for view,row in metrics.items():print(view,{k:(v['large_components_8_connected'],round(v['largest_component_fraction'],3),round(v['wood_projection_without_leaf_overlap_fraction'],3)) for k,v in row.items()})

if __name__=='__main__':main()
