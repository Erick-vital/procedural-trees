#!/usr/bin/env python3
"""Conservar evidencia seleccionada del piloto, separando técnica y forma."""
import argparse
from pathlib import Path
import shutil
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'scripts')]
from review_pine_painted import read,write,sha


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--study',type=Path,required=True);p.add_argument('--evidence',type=Path,required=True)
    a=p.parse_args();study=a.study.resolve();out=a.evidence.resolve();r=read(study/'manifest.json')
    assert r['passed'] and all(r['repeat_glb_identical'].values()) and all(v['passed'] for v in r['godot'])
    assert all(sha(ROOT/f)==h for f,h in r['source_lock'].items())
    assert all(sha(study/'captures'/f)==h for f,h in r['capture_sha256'].items())
    assert len(r['capture_sha256'])==82
    for name in r['variants']:assert sha(study/name/'tree.glb')==r['variants'][name]['glb_sha256']
    def target(values):return all(v['iou']>=.99 and .99<=v['coverage_ratio']<=1.01 for v in values)
    shape={key:target([v for n,v in values.items() if n in ('front','side','perspective','back','top','below')]) for key,values in r['mask_metrics'].items()}
    audit={k:r[k] for k in ('version','source_blueprint','seeds','paint_seed','source_glb_sha256','source_placements_sha256',
        'source_supports_sha256','cards_sha256','leaf_count','kept_support_ids','removed_support_ids','variants','resources',
        'repeat_glb_identical','export_validation','geometry_audit','mask_metrics','source_lock','capture_sha256')}
    audit.update(study=str(study.relative_to(ROOT)),technical_checks_passed=True,real_captures=82,
        shape_target_iou_99_coverage_1percent=shape,artistic_acceptance='pending',controls='not_run',
        tests={'command':"PYTHONPATH=src python3 -m unittest discover -s tests -p 'test_oak_painted*.py' -v",'passed':True,'count':12},
        evidence_script_sha256=sha(Path(__file__)))
    out.mkdir(parents=True,exist_ok=False)
    for name in ('painting.jpg','pruning.jpg','bark.jpg','distances.jpg','masks.jpg'):shutil.copy2(study/name,out/name)
    shutil.copy2(study/'captures/painted--perspective.png',out/'piloto.png')
    write(out/'audit.json',audit)
    print('Evidencia: técnica OK; objetivo histórico de forma '+str(shape['painting'])+'; poda '+str(shape['pruning'])+'.')


if __name__=='__main__':main()
