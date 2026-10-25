#!/usr/bin/env python3
"""Conserva métricas y láminas seleccionadas del intento experimental de pino."""
import argparse
import json
from pathlib import Path
import shutil

from foliage_evidence import sheet


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--study',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    study=args.study.resolve();out=args.output.resolve()
    report=json.loads((study/'verification.json').read_text())
    assert report['passed'] and report['visual_requested']
    out.mkdir(parents=True,exist_ok=True)
    summary={k:v for k,v in report.items() if k not in ('contacts','godot')}
    summary['study']=str(study)
    summary['contacts']={Path(k).name:v for k,v in report['contacts']['cases'].items()}
    summary['godot']=[{k:v for k,v in r.items() if k!='assets'} for r in report['godot']]
    summary['real_captures']=report.get('real_captures',72)
    summary['artistic_acceptance']='pending_user_review'
    (out/'verification.json').write_text(json.dumps(summary,indent=2,ensure_ascii=False)+'\n')
    for filename in ('controls.jpg','wood.jpg','distances.jpg'):
        shutil.copy2(study/filename,out/filename)
    for filename in ('comparison.jpg','comparison-wood.jpg'):
        if (study/filename).exists():shutil.copy2(study/filename,out/filename)
    shutil.copy2(study/'inspection/pilot/godot-perspective.png',out/'pilot.png')
    shutil.copy2(study/'logs/tests.log',out/'unit-tests.txt')
    sheet(study,out/'pilot-views.jpg',3,[[(f'inspection/pilot/godot-{v}.png',v) for v in views]
          for views in [('front','side','perspective'),('top','below','reverse')]])


if __name__=='__main__':main()
