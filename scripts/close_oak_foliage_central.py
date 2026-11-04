#!/usr/bin/env python3
"""OF11: auditoría reproducible de presupuesto, referencias, giro y máscaras."""
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
    p.add_argument('--output',type=Path,default=ROOT/'docs/evidence/oak-foliage/of11')
    a=p.parse_args();study=a.study.resolve();out=a.output.resolve()
    m=read(study/'manifest.json');r=read(study/'review.json');layout=read(study/'layout.json');mask=read(study/'mask-review.json')
    checks=dict(m['checks'])
    checks['generation']=m['status']=='completed'
    checks['sources']=all(sha(ROOT/p)==h for p,h in m['source_inventory'].items())
    checks['repeat-exports']=all(sha(study/n/'tree.glb')==sha(a.repeat/n/'tree.glb') for n in m['variants'])
    checks['repeat-inputs-layout']=all(sha(study/n)==sha(a.repeat/n) for n in ('layout.json','o5-structure.json','baseline-groups.json'))
    checks['o5-reference-exact']=m['variants']['reference']['glb_sha256']==read(ROOT/'docs/evidence/oak-growth/o5/verification.json')['cases']['maduro-3100']['glb_sha256']['bare']
    checks['of10-baseline-exact']=m['variants']['baseline']['glb_sha256']==read(ROOT/'docs/evidence/oak-foliage/of10/verification.json')['generation']['variants']['painted']['glb_sha256']
    checks['godot']=r['passed'] and all(x['passed'] for x in r['godot'])
    checks['captures']=len(r['captures_sha256'])==135 and all(sha(study/'captures'/p)==h for p,h in r['captures_sha256'].items())
    checks['protocol-source']=sha(ROOT/'scripts/prepare_oak_foliage_central.py')==r['protocol_source_sha256']
    checks['camera-pairs']=read(study/'baseline-review-input.json')['shots']==read(study/'painted-review-input.json')['shots']==r['protocols']['tree']
    checks['complete-orbit']=len([s for s in r['protocols']['tree'] if s['id'].startswith('orbit-')])==24
    checks['masks']=mask['passed'] and all(x['passed'] for x in mask['godot'])
    checks['mask-integrity']=len(mask['captures_sha256'])==8 and all(sha(study/'masks'/p)==h for p,h in mask['captures_sha256'].items())
    checks['mask-sources']=all(sha(ROOT/p)==h for p,h in mask['sources_sha256'].items())
    checks['mask-camera-pairs']=all(read(study/(n+'-mask-input.json'))['shots']==mask['shots'] for n in ('baseline','painted'))
    tests=a.tests.read_text();match=re.search(r'Ran (\d+) tests',tests)
    checks['tests']=bool(match and int(match[1])>=6 and tests.rstrip().endswith('OK'))
    old={g['id']:g for g in read(study/'baseline-groups.json')}
    checks['paint-scale-identities']=set(old)=={g['id'] for g in layout['groups']} and all(all(g[k]==old[g['id']][k] for k in ('size_m','template_index','root_normalized')) for g in layout['groups'])
    checks['24-relocated-192-exact']=sum(g!=old[g['id']] for g in layout['groups'])==24 and len(layout['central_changes'])==24
    checks['bounded-triangles']=m['variants']['painted']['metrics']['triangles']==5270+layout['central_extension']['added_wood_triangles']<=6999
    checks['unchanged-of10-reference']=m['variants']['baseline']['metrics']['triangles']==5270
    from treegen.branch_tree_audit import raw_channels
    checks['o5-wood-exact-subset']=not(Counter(raw_channels(study/'reference/tree.glb')['Painted_Bark'])-Counter(raw_channels(study/'painted/tree.glb')['Painted_Bark']))
    checks['three-vertical-axes']=layout['central_extension']['structural_axes']==3
    checks['new-wood-budget']=layout['central_extension']['added_wood_triangles']<=600
    checks['region-counts']=sum(x['group_count'] for x in layout['regions'])==216
    checks['bounded-work']=layout['region_attempts']<=216*9*12 and layout['central_attempts']<=24*12
    checks['lateral-complements']=len(layout['lateral_complements'])==63
    areas={n:plane_area(study/n/'tree.glb') for n in ('baseline','painted')}
    checks['same-foliage-area']=abs(areas['painted']-areas['baseline'])/areas['baseline']<1e-6
    from PIL import Image
    from treegen.oak_foliage_gap_evaluation import audit_fans
    fan_audit=audit_fans(study/'painted/tree.glb',layout['gap_fans'],Image.open(ROOT/'assets/roble-pintado/v0.3.0/foliage.png').convert('RGBA'))
    write(study/'fan-contacts-audit.json',fan_audit);checks['fan-export-and-opaque-roots']=fan_audit['passed']
    out.mkdir(parents=True,exist_ok=True)
    for name in ('comparison','appearance','branch','preview','masks','upper','orbit'):
        shutil.copy2(study/(name+'.jpg'),out/(name+'.jpg'))
    for name in ('front','side','top','perspective'):
        shutil.copy2(study/'captures'/('painted--'+name+'.png'),out/(name+'.png'))
    sheet(study,study/'before-after.jpg',2,[[(f'captures/{n}--{v}.png',label+' | '+v) for n,label in [('baseline','OF10 anterior'),('painted','OF11 regiones')]] for v in ('top','front','side','perspective')])
    sheet(study,study/'top-comparison.jpg',2,[[(f'captures/{n}--top.png',label+' | arriba') for n,label in [('baseline','OF10 anterior'),('painted','OF11 regiones')]]])
    shutil.copy2(study/'top-comparison.jpg',out/'top-comparison.jpg')
    sheet(study,study/'wood-comparison.jpg',2,[[(f'captures/{n}--{v}.png',label+' | '+v) for n,label in [('reference','O5 anterior'),('bare','Tres ejes ascendentes nuevos')]] for v in ('front','perspective')])
    shutil.copy2(study/'wood-comparison.jpg',out/'wood-comparison.jpg')
    shutil.copy2(study/'before-after.jpg',out/'before-after.jpg');shutil.copy2(a.tests,out/'tests.txt')
    html=study/'index.html'
    if 'id="orbit-slider"' not in html.read_text():
        html.write_text(html.read_text()+'''<h2>Giro comparado OF10 / OF11</h2>
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
    if 'wood-comparison.jpg' not in html.read_text():html.write_text(html.read_text()+'<h2>Madera anterior / nuevos ejes ascendentes</h2><img src="wood-comparison.jpg">')
    report={'version':'oak-foliage-canopy-verification-0.11.0','passed':all(checks.values()),'checks':checks,'generation':m,
            'study':str(study),'repeat':str(a.repeat.resolve()),'review':r,'mask_review':mask,
            'leaf_plane_area_m2':areas,'regions':layout['regions'],'region_changes':layout['region_changes'],
            'contacts':read(study/'contacts-audit.json'),'visual_review':read(study/'agent-review.json') if (study/'agent-review.json').exists() else 'pending_agent','artistic_acceptance':'pending_user',
            'controls_scope':'3101-3103 and layout18: unit geometry only; no Godot or artistic acceptance',
            'tests_sha256':sha(a.tests),'test_source_sha256':sha(ROOT/'tests/test_oak_foliage_central.py'),'fan_contacts':fan_audit,'central_changes':layout['central_changes'],'central_extension':layout['central_extension'],'central_protection':layout['central_protection'],
            'gap_summary':{'gaps':layout['gaps'],'fans':len(layout['gap_fans']),'attempts':layout['gap_attempts']},
            'fan_evaluation_source_sha256':sha(ROOT/'src/treegen/oak_foliage_gap_evaluation.py'),
            'analysis_source_sha256':sha(Path(__file__)),
            'images_sha256':{p.name:sha(p) for p in out.iterdir() if p.suffix in ('.jpg','.png')}}
    write(out/'verification.json',report)
    assert all(checks.values()),[k for k,v in checks.items() if not v]
    print('OF11:',len(checks),'checks;',match[1],'pruebas; 135 capturas y 8 máscaras de follaje; siete GLB repetidos exactos')

if __name__=='__main__':main()
