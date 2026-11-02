#!/usr/bin/env python3
"""Conservar dos atlas candidatos tras revisar el ensayo T2, sin adoptar el árbol."""
import argparse
import copy
import json
from pathlib import Path
import shutil
from build_season_atlas import ROOT, sha, write


def publish(trial, output, treatment):
    report=json.loads((trial/'verification.json').read_text())
    if not report['passed']: raise ValueError('Ensayo sin verificación válida')
    manifest=copy.deepcopy(report['atlas'])
    for p,h in {**manifest['inputs'],**manifest['sources'],**report['source_lock'],**report['pilot_inputs']}.items():
        if sha(ROOT/p)!=h: raise ValueError('Fuentes distintas del ensayo: '+p)
    output.mkdir(parents=True,exist_ok=False)
    files={}
    for season in ('summer','autumn'):
        original=season+'-'+treatment+'.png'
        source=trial/'atlas'/original
        if sha(source)!=manifest['files'][original]['sha256']: raise ValueError('Atlas alterado')
        target=output/(season+'.png');shutil.copy2(source,target)
        files[target.name]={**manifest['files'][original],'trial_name':original}
    manifest['files']=files
    manifest['padding']['selection']=treatment
    manifest['review']={'verification':str((trial/'verification.json').relative_to(ROOT)),
                        'verification_sha256':sha(trial/'verification.json'),
                        'artistic_acceptance':'pending', 'full_tree_adopted':False}
    manifest['sources']['scripts/publish_season_atlas.py']=sha(Path(__file__))
    write(output/'manifest.json',manifest)
    return manifest

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--trial',required=True,type=Path)
    p.add_argument('--output',required=True,type=Path)
    p.add_argument('--treatment',choices=('common','padded'),required=True)
    a=p.parse_args();publish(a.trial.resolve(),a.output.resolve(),a.treatment)
    print('Dos atlas candidatos conservados; aceptación artística pendiente.')
