#!/usr/bin/env python3
"""Auditar repetición/contactos R1 y seleccionar capturas sin alterar los assets."""
import argparse
import copy
import math
from pathlib import Path
import shutil
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'src'),str(ROOT/'scripts')]
from treegen.oak_crossed_evaluation import channels
from treegen.pine_painted_sample import canonical_hash
from review_pine_painted import read,write,sha
from foliage_evidence import sheet
from PIL import Image


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--study',required=True,type=Path)
    p.add_argument('--output',required=True,type=Path);a=p.parse_args();study=a.study.resolve();out=a.output.resolve()
    out.mkdir(parents=True,exist_ok=True)
    r=read(study/'verification.json');checks=r['checks'];assert r['passed'] and len(r['captures_sha256'])==48
    repeat=read(study/'repeat/exports.json')
    for name,item in r['variants'].items():
        checks['repeat-'+name+'-exact']=item['glb_sha256']==repeat['variants'][name]['glb_sha256']
    before=channels(study/'baseline/tree.glb');after=channels(study/'candidate/tree.glb')
    checks['foliage_normals_exact']=sorted(before[2]['Painted_Foliage'])==sorted(after[2]['Painted_Foliage'])
    points={tuple(v[:3]) for tri in after[1]['Painted_Bark'] for v in tri}
    network=read(study/'network.json');errors=[]
    for item in network['connections'].values():
        x,y,z=item['point'];target=(x,z,-y)
        errors.append(min(math.dist(target,p) for p in points))
    checks['terminal_tips_exported']=max(errors)<1e-6
    for name in ('front','side','perspective','top','below','back'):
        with Image.open(study/'captures'/('leaves-after--'+name+'.png')) as im:
            checks['mask-'+name+'-nonempty']=sum(im.convert('L').histogram()[:10])>1000
    assert all(checks.values()),checks
    for name in ('wood.jpg','tree.jpg'):shutil.copy2(study/name,out/name)
    # Presentación breve: las mismas capturas, solo etiquetas en español.
    sheet(study,out/'comparacion.jpg',3,[
        [(f'captures/{name}--wood-perspective.png',label+' | sin hojas') for name,label in [('baseline','Anterior F5'),('candidate','Nueva R1'),('nodes','Nodos (referencia)')]],
        [(f'captures/{name}--perspective.png',label+' | con hojas') for name,label in [('baseline','Anterior F5'),('candidate','Nueva R1'),('nodes','Nodos (referencia)')]]])
    sheet(study,out/'mascaras.jpg',2,[[(f'captures/{name}--{view}.png',name+' '+view) for name in ('leaves-before','leaves-after')]
          for view in ('front','side','perspective','top','below','back')])
    log=(study/'logs/tests.log').read_text();assert 'Ran 229 tests' in log and log.rstrip().endswith('OK')
    report={**r,'checks':checks,'passed':True,'tests':{'count':229,'passed':True,'log_sha256':sha(study/'logs/tests.log')},
            'exported_terminal_max_error_m':max(errors),'repeat_manifest_sha256':sha(study/'repeat/exports.json'),
            'sample_foliage_groups':network['targets'],'seed':network['seed'],'network_version':network['version'],
            'source_lock_sha256':sha(study/'frozen-branch.json'),'nodes_presentation':read(study/'nodes-presentation.json'),
            'evidence_script_sha256':sha(__file__),'visual_review':'pending_agent','artistic_acceptance':'pending_user'}
    write(out/'verification.json',report)
    print('Comprobaciones:',len(checks),'correctas; error de terminales:',max(errors))


if __name__=='__main__':main()
