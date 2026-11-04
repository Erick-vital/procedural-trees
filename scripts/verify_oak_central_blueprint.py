#!/usr/bin/env python3
"""Cerrar la receta3.0.0 con identidad OF11, repetición y suite por archivos."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import sys
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'src')]
from treegen.blueprints import load_blueprint,load_instance,resolve_blueprint,canonical_hash,registered_blueprints


def read(path):return json.loads(Path(path).read_text())
def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--first',type=Path,required=True)
    p.add_argument('--repeat',type=Path,required=True);p.add_argument('--tests',type=Path,required=True)
    p.add_argument('--output',type=Path,default=ROOT/'docs/evidence/oak-foliage/of11/blueprint-release.json')
    a=p.parse_args();first=a.first.resolve();repeat=a.repeat.resolve();one=read(first/'manifest.json');two=read(repeat/'manifest.json')
    b=load_blueprint(ROOT/'blueprints/roble_copa_ancha/3.0.0.json');i=load_instance(ROOT/'presets/blueprints/roble-central/maduro-3100.json')
    resolved=resolve_blueprint(b,i);accepted=read(ROOT/'docs/evidence/oak-foliage/of11/user-acceptance.json')
    tests=read(a.tests);test_count=0;records=[]
    for row in tests['results']:
        log=ROOT/row['log'];text=log.read_text();m=re.search(r'Ran (\d+) tests?',text)
        passed=row['exit_code']==0 and m is not None and text.rstrip().endswith('OK')
        test_count+=int(m[1]) if m else 0
        records.append({**row,'passed':passed,'tests':int(m[1]) if m else None,'log_sha256':sha(log)})
    checks={'registered':any(e['id']==b['id'] and e['version']=='3.0.0' for e in registered_blueprints()),
            'approved':accepted['status']=='accepted','resolved':one['resolved_blueprint']==two['resolved_blueprint']==resolved,
            'completed':one['status']==two['status']=='completed',
            'exact-approved-glb':sha(first/'tree.glb')==sha(repeat/'tree.glb')==accepted['approved_glb_sha256'],
            '5745-triangles':one['export_validation']['triangles']==two['export_validation']['triangles']==5745,
            '216-groups':one['group_count']==two['group_count']==216,
            'two-materials':len(one['export_validation']['materials'])==len(two['export_validation']['materials'])==2,
            'export-audits':all(one['export_validation']['checks'].values()) and all(two['export_validation']['checks'].values()),
            'prepared-repeat':sha(first/'prepared-canopy.json')==sha(repeat/'prepared-canopy.json'),
            'sources':all(sha(ROOT/n)==h for n,h in one['sources_sha256'].items()),
            'bounded-time':one['duration_seconds']<=120 and two['duration_seconds']<=120,
            'all-tests':tests['passed'] and tests['completed']==tests['total_files']==len(records) and all(r['passed'] for r in records),
            'rendered-views':len(one['required_views'])==9 and all((first/(v+'.png')).is_file() for v in one['required_views']),
            'no-clipping':all(v['vertices_outside_frame']==0 for v in one['projection_clips'].values())}
    report={'version':'oak-central-blueprint-release-1.0','date':'2026-11-03','passed':all(checks.values()),'checks':checks,
            'blueprint':{'path':'blueprints/roble_copa_ancha/3.0.0.json','file_sha256':sha(ROOT/'blueprints/roble_copa_ancha/3.0.0.json'),'canonical_sha256':canonical_hash(b)},
            'instance':i,'first':str(first),'repeat':str(repeat),'approved_glb_sha256':accepted['approved_glb_sha256'],
            'first_duration_s':one['duration_seconds'],'repeat_duration_s':two['duration_seconds'],
            'export_validation':one['export_validation'],'tests':{'count':test_count,'files':records},
            'render_review':'Nine Blender diagnostic views generated; perspective inspected. Approved Godot captures retained because the GLB is byte-identical.',
            'scope':'Full-art approval only mature3100/layout17/paint2718; other seeds geometric controls, no new ages or parameter ranges.',
            'analysis_source_sha256':sha(Path(__file__))}
    a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    assert all(checks.values()),[k for k,v in checks.items() if not v]
    print('Blueprint3.0.0:',len(checks),'checks;',test_count,'tests;',len(records),'archivos; GLB idéntico a OF11 aprobado')

if __name__=='__main__':main()
