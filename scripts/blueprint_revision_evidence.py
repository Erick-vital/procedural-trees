#!/usr/bin/env python3
"""B3 revisada: antes/después de jóvenes con cámaras idénticas y evidencia final."""
import argparse
import json
import os
from pathlib import Path
import shutil
import signal
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'scripts'))
from verify_blueprint_reference import read, write, sha
from verify_foliage_unit import GODOT
from foliage_evidence import sheet


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--study', type=Path, required=True)
    parser.add_argument('--previous', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    study, previous, output = args.study.resolve(), args.previous.resolve(), args.output.resolve()
    report = read(study/'verification.json')
    assert report['passed'] and report['export_contacts']['passed']
    output.mkdir(parents=True, exist_ok=True)
    env = dict(os.environ, PYTHONPATH=str(ROOT/'src'))

    def run(name, command):
        with (study/'logs'/(name+'.log')).open('w') as log:
            process = subprocess.Popen(list(map(str,command)), cwd=ROOT, env=env,
                stdout=log, stderr=subprocess.STDOUT, start_new_session=True)
            try:
                code = process.wait(timeout=180)
            except subprocess.TimeoutExpired:
                os.killpg(process.pid,signal.SIGKILL);process.wait();raise
        content=(study/'logs'/(name+'.log')).read_text()
        if code or 'SCRIPT ERROR:' in content or '\nERROR:' in content:
            raise RuntimeError(name+': '+content[-2000:])
        print(name+': OK',flush=True)

    # La comparación antigua usa exactamente las cámaras de la revisión actual.
    project=study/'godot-before-after';project.mkdir(exist_ok=False)
    for filename in ('project.godot','verify_oak.gd','verify_foliage_molds.gd'):
        shutil.copy2(ROOT/'godot'/filename,project/filename)
    entries=[]
    for name in ('joven-00','joven-07'):
        folder=study/'inspection'/(name+'-before');folder.mkdir(exist_ok=False)
        for filename in ('tree.glb','manifest.json'):
            shutil.copy2(previous/name/filename,folder/filename)
        shutil.copy2(study/'inspection'/name/'cameras.json',folder/'cameras.json')
        shutil.copy2(folder/'tree.glb',project/(name+'-before.glb'))
        entries.append({'id':name+'-before','folder':str(folder),'capture':True,'resource':'res://'+name+'-before.glb'})
    write(study/'before-after-input.json',entries)
    godot=os.environ.get('GODOT_BIN',GODOT)
    run('before-after-import',[godot,'--headless','--path',project,'--editor','--import'])
    command=[godot,'--path',project,'--script','res://verify_foliage_molds.gd','--',
        '--input='+str(study/'before-after-input.json'),'--report='+str(study/'before-after-godot.json')]
    run('before-after-check',command[:1]+['--headless']+command[1:])
    run('before-after-visual',command+['--visual'])
    assert read(study/'before-after-godot.json')['passed']
    run('evidence',[sys.executable,ROOT/'scripts/blueprint_controls_evidence.py','--study',study,'--output',output,
                    '--q3-reference',ROOT/'artifacts/q3/acceptance/lote'])
    rows=[]
    for name in ('joven-00','joven-07'):
        for view in ('near','top','below','medium'):
            rows.append([(f'inspection/{n}/godot-{view}.png',n+' | '+view)
                for n in (name+'-before',name)])
    sheet(study,output/'young-before-after.jpg',2,rows)
    sheet(study,output/'young-summary.jpg',4,[[(f'inspection/{n}/godot-{view}.png',n+' | '+view)
        for n in ('joven-00-before','joven-00','joven-07-before','joven-07')] for view in ('near','below')])
    sheet(study,output/'extreme-20m.jpg',3,[[(f'inspection/{n}/godot-{view}.png',n+' | '+view)
        for view in ('near','top','below')] for n in ('height-high-scale-low-wood','height-high-scale-low')])
    for src,dest in (('logs/tests.log','unit-tests.txt'),('logs/contact-regression.log','contact-regression.txt'),
                     ('export-contacts.json','export-contacts.json')):
        shutil.copy2(study/src,output/dest)
    previous_diagnostic=ROOT/'artifacts/blueprints/b3-contact-diagnosis.json'
    if previous_diagnostic.exists():shutil.copy2(previous_diagnostic,output/'initial-surface-diagnostic.json')
    details={}
    for name,c in report['cases'].items():
        if c['status']=='generated':
            m=read(study/name/'manifest.json')
            details[name]={k:m[k] for k in ('surface_projection','contacts','adapter_version','supports_sha256',
                'twigs_sha256','wood_sha256','glb_sha256','duration_seconds','glb_bytes')}
    write(output/'contact-and-provenance.json',details)
    r=read(output/'verification.json')
    r['comparison_cameras_identical']=all(read(study/'inspection'/n/'cameras.json')==read(study/'inspection'/(n+'-before')/'cameras.json') for n in ('joven-00','joven-07'))
    r['selected_images_sha256']={p.name:sha(p) for p in output.glob('*.jpg')}
    r['revision_evidence_script_sha256']=sha(Path(__file__))
    write(output/'verification.json',r)
    print('Revisión B3 y comparación visual preparadas: '+str(output),flush=True)


if __name__=='__main__':
    main()
