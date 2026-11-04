#!/usr/bin/env python3
"""OF9: auditoría reproducible de presupuesto, referencias, giro y máscaras."""
import argparse
from collections import Counter
from pathlib import Path
import re
import shutil
import sys
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'src'),str(ROOT/'scripts')]
from review_pine_painted import read, write, sha
from close_oak_foliage_chains import plane_area
from foliage_evidence import sheet


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--study',type=Path,required=True);p.add_argument('--repeat',type=Path,required=True)
    p.add_argument('--tests',type=Path,required=True)
    p.add_argument('--region-tests',type=Path);p.add_argument('--api-tests',type=Path)
    p.add_argument('--output',type=Path,default=ROOT/'docs/evidence/oak-foliage/of9')
    a=p.parse_args();study=a.study.resolve();out=a.output.resolve()
    m=read(study/'manifest.json');r=read(study/'review.json');layout=read(study/'layout.json');mask=read(study/'mask-review.json')
    checks=dict(m['checks'])
    checks['generation']=m['status']=='completed'
    checks['sources']=all(sha(ROOT/p)==h for p,h in m['source_inventory'].items())
    checks['repeat-exports']=all(sha(study/n/'tree.glb')==sha(a.repeat/n/'tree.glb') for n in m['variants'])
    checks['repeat-inputs-layout']=all(sha(study/n)==sha(a.repeat/n) for n in ('layout.json','o5-structure.json','baseline-groups.json'))
    checks['of6-reference-exact']=m['variants']['reference']['glb_sha256']==read(ROOT/'docs/evidence/oak-foliage/of6/verification.json')['generation']['variants']['painted']['glb_sha256']
    checks['of8-baseline-exact']=m['variants']['baseline']['glb_sha256']==read(ROOT/'docs/evidence/oak-foliage/of8/verification.json')['generation']['variants']['painted']['glb_sha256']
    checks['godot']=r['passed'] and all(x['passed'] for x in r['godot'])
    checks['captures']=len(r['captures_sha256'])==135 and all(sha(study/'captures'/p)==h for p,h in r['captures_sha256'].items())
    checks['protocol-source']=sha(ROOT/'scripts/prepare_oak_foliage_regions.py')==r['protocol_source_sha256']
    checks['camera-pairs']=read(study/'baseline-review-input.json')['shots']==read(study/'painted-review-input.json')['shots']==r['protocols']['tree']
    checks['complete-orbit']=len([s for s in r['protocols']['tree'] if s['id'].startswith('orbit-')])==24
    checks['masks']=mask['passed'] and all(x['passed'] for x in mask['godot'])
    checks['mask-integrity']=len(mask['captures_sha256'])==12 and all(sha(study/'masks'/p)==h for p,h in mask['captures_sha256'].items())
    checks['mask-sources']=all(sha(ROOT/p)==h for p,h in mask['sources_sha256'].items())
    checks['mask-camera-pairs']=all(read(study/(n+'-mask-input.json'))['shots']==mask['shots'] for n in ('reference','baseline','painted'))
    tests=a.tests.read_text();match=re.search(r'Ran (\d+) tests',tests)
    full_success=bool(match and int(match[1])>=328 and tests.rstrip().endswith('OK'))
    segmented=False; test_runs={'suite':{'sha256':sha(a.tests),'text':tests}}
    if a.region_tests and a.api_tests:
        regional=a.region_tests.read_text();api=a.api_tests.read_text()
        # La suite completa terminó con una sola restricción ambiental. Repetir
        # HTTP fuera y los seis tests OF9 sobre las fuentes finales, sin ocultar
        # el fallo original ni presentar una segunda suite interrumpida como OK.
        segmented=bool(match and int(match[1])==328 and tests.count('ERROR: ')==1
                       and 'ERROR: test_api_async_and_invalid_input' in tests
                       and 'PermissionError: [Errno 1]' in tests and tests.rstrip().endswith('FAILED (errors=1)')
                       and 'Ran 6 tests' in regional and regional.rstrip().endswith('OK')
                       and 'Ran 1 test' in api and api.rstrip().endswith('OK'))
        test_runs.update(region_final={'sha256':sha(a.region_tests),'text':regional},api_external={'sha256':sha(a.api_tests),'text':api})
    checks['tests']=full_success or segmented
    old={g['id']:g for g in read(study/'baseline-groups.json')}
    checks['paint-scale-identities']=set(old)=={g['id'] for g in layout['groups']} and all(all(g[k]==old[g['id']][k] for k in ('size_m','template_index','root_normalized')) for g in layout['groups'])
    checks['biological-arm-quotas']=all(g['parent_branch_id'].split('/')[0]==old[g['id']]['parent_branch_id'].split('/')[0] for g in layout['groups'])
    checks['exact-triangles']=m['variants']['painted']['metrics']['triangles']==m['variants']['baseline']['metrics']['triangles']==5136
    checks['region-counts']=sum(x['group_count'] for x in layout['regions'])==216
    checks['bounded-work']=layout['region_attempts']<=216*9*12
    checks['lateral-complements']=len(layout['lateral_complements'])==63
    areas={n:plane_area(study/n/'tree.glb') for n in ('baseline','painted')}
    checks['unchanged-plane-area']=abs(areas['baseline']-areas['painted'])/areas['baseline']<1e-6
    out.mkdir(parents=True,exist_ok=True)
    for name in ('comparison','appearance','branch','preview','masks','upper','orbit'):
        shutil.copy2(study/(name+'.jpg'),out/(name+'.jpg'))
    for name in ('front','side','top','perspective'):
        shutil.copy2(study/'captures'/('painted--'+name+'.png'),out/(name+'.png'))
    sheet(study,study/'before-after.jpg',2,[[(f'captures/{n}--{v}.png',label+' | '+v) for n,label in [('baseline','OF8 provisional'),('painted','OF9 regiones')]] for v in ('top','front','side','perspective')])
    sheet(study,study/'top-comparison.jpg',2,[[(f'captures/{n}--top.png',label+' | arriba') for n,label in [('baseline','OF8 provisional'),('painted','OF9 regiones')]]])
    shutil.copy2(study/'top-comparison.jpg',out/'top-comparison.jpg')
    shutil.copy2(study/'before-after.jpg',out/'before-after.jpg');shutil.copy2(a.tests,out/'tests.txt')
    if a.region_tests:shutil.copy2(a.region_tests,out/'tests-regions-final.txt')
    if a.api_tests:shutil.copy2(a.api_tests,out/'tests-api-external.txt')
    html=study/'index.html'
    if 'id="orbit-slider"' not in html.read_text():
        html.write_text(html.read_text()+'''<h2>Giro comparado OF8 / OF9</h2>
<p>24 posiciones a 15 grados; distancia media de prueba. <button id="orbit-play">Girar / parar</button>
<input id="orbit-slider" type="range" min="0" max="23" value="0"><span id="orbit-angle">0°</span></p>
<div style="display:flex"><img id="orbit-old" style="width:50%"><img id="orbit-new" style="width:50%"></div>
<script>
const slider=document.getElementById('orbit-slider');
function frame(){const n=String(slider.value).padStart(2,'0');
document.getElementById('orbit-old').src='captures/baseline--orbit-'+n+'.png';
document.getElementById('orbit-new').src='captures/painted--orbit-'+n+'.png';
document.getElementById('orbit-angle').textContent=(15*Number(slider.value))+'°';}
slider.oninput=frame;let timer=null;
document.getElementById('orbit-play').onclick=()=>{if(timer){clearInterval(timer);timer=null;}
else timer=setInterval(()=>{slider.value=(Number(slider.value)+1)%24;frame();},250);};frame();
</script>''')
    report={'version':'oak-foliage-canopy-verification-0.9.0','passed':all(checks.values()),'checks':checks,'generation':m,
            'study':str(study),'repeat':str(a.repeat.resolve()),'review':r,'mask_review':mask,
            'leaf_plane_area_m2':areas,'regions':layout['regions'],'region_changes':layout['region_changes'],
            'contacts':read(study/'contacts-audit.json'),'visual_review':read(study/'agent-review.json') if (study/'agent-review.json').exists() else 'pending_agent','artistic_acceptance':'pending_user',
            'controls_scope':'3101-3103 and layout18: unit geometry only; no Godot or artistic acceptance',
            'test_runs':test_runs,'test_verification_mode':'suite plus final OF9 and external HTTP reruns' if segmented else 'full suite',
            'final_region_test_source_sha256':sha(ROOT/'tests/test_oak_foliage_regions.py'),
            'analysis_source_sha256':sha(Path(__file__)),
            'images_sha256':{p.name:sha(p) for p in out.iterdir() if p.suffix in ('.jpg','.png')}}
    write(out/'verification.json',report)
    assert all(checks.values()),[k for k,v in checks.items() if not v]
    print('OF9:',len(checks),'checks;',match[1],'pruebas; 135 capturas y 12 máscaras; siete GLB repetidos exactos')

if __name__=='__main__':main()
