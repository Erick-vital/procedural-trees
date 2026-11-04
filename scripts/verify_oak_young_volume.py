#!/usr/bin/env python3
"""J3: cobertura y volumen, identidad de madera y comparación Godot con J2."""
import argparse
from pathlib import Path
import shutil
import os
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'src'),str(ROOT/'scripts')]
from review_pine_painted import read,write,sha,run
from verify_oak_young_canopy import review as review_trees
from treegen.language import load_plan
from treegen.branch_tree_audit import raw_channels
from foliage_evidence import sheet
from verify_foliage_unit import GODOT


def audit(out,baseline):
    _,_,rows=load_plan(out/'plan');assert read(out/'trees/batch.json')['status']=='completed'
    assert read(out/'repeat/batch.json')['status']=='completed'
    checks={};cases={}
    for row in rows:
        name=row['id'];m=read(out/'trees'/name/'manifest.json');r=read(out/'repeat'/name/'manifest.json')
        b=read(baseline/'trees'/name/'manifest.json');data=read(out/'trees'/name/'prepared-canopy.json')
        for folder,manifest in [(out/'trees'/name,m),(out/'repeat'/name,r),(baseline/'trees'/name,b)]:
            assert all(sha(folder/p)==h for p,h in manifest['files_sha256'].items())
            assert all(manifest['export_validation']['checks'].values())
        checks[name+'-repeat']=m['export_validation']==r['export_validation']
        checks[name+'-same-inputs']=m['resolved_blueprint']['instance_request']==r['resolved_blueprint']['instance_request']==row['instance']
        checks[name+'-same-sources']=m['sources_sha256']==r['sources_sha256']
        checks[name+'-same-wood']=raw_channels(out/'trees'/name/'tree.glb')['Painted_Bark']==raw_channels(baseline/'trees'/name/'tree.glb')['Painted_Bark']
        coverage=data['diagnostics']['axis_coverage'];axis_ids={x['id'] for x in data['structure']['branches']}
        checks[name+'-all-axes-covered']=set(coverage)==axis_ids and all(c['group_count']>=1 and c['distal_t']>.88 for c in coverage.values())
        checks[name+'-leader-covered']=any(g['role']=='leader' and g['parent_t']>.88 for g in data['groups'])
        checks[name+'-budget']=m['metrics']['triangles']<=6999 and len(m['metrics']['triangles_by_material'])==2 and len(data['groups'])==264
        checks[name+'-added-foliage']=m['metrics']['triangles']==b['metrics']['triangles']+720
        cases[name]={'seeds':row['instance']['seeds'],'triangles':m['metrics']['triangles'],'materials':m['metrics']['triangles_by_material'],
                     'glb_sha256':m['glb_sha256'],'geometry_sha256':m['export_validation']['geometry_sha256'],
                     'maximum_contact_error_m':m['export_validation']['maximum_contact_error_m'],'groups':264,'covered_axes':len(coverage),
                     'baseline_covered_axes':len({g['parent_branch_id'] for g in read(baseline/'trees'/name/'prepared-canopy.json')['groups']}),
                     'baseline_triangles':b['metrics']['triangles'],'duration_seconds':m['duration_seconds']}
    checks['four-distinct-geometries']=len({c['geometry_sha256'] for c in cases.values()})==4
    for version,path in [('310',baseline/'trees/joven-3100/manifest.json'),('300',ROOT/'artifacts/roble-joven/j2-completo-01/mature-regression/manifest.json')]:
        g=read(out/('regression-'+version)/'manifest.json');checks['regression-'+version]=g['glb_sha256']==read(path)['glb_sha256']
    result={'version':'oak-young-volume-verification-1.0','date':'2026-11-04','passed':all(checks.values()),'checks':checks,'cases':cases,
            'artistic_acceptance':'pending-user','visual_review':'pending','no_performance_tests':True,
            'generation_sources_sha256':m['sources_sha256'],'baseline':str(baseline.relative_to(ROOT)),
            'recipe_sha256':sha(ROOT/'blueprints/roble_copa_ancha/3.2.0.json')}
    if (out/'verification.json').is_file():
        previous=read(out/'verification.json')
        for key in ('godot_reports','captures_sha256','review_protocol_sha256','visual_captures_generated','comparison_reports','comparison_protocol_sha256'):
            if key in previous:result[key]=previous[key]
    write(out/'verification.json',result);assert result['passed'],checks
    print('J3 auditado:',len(checks),'checks; cobertura completa y repeticiones correctas.',flush=True)


def review(out,baseline):
    review_trees(out)
    result=read(out/'verification.json');project=out/'godot';protocol=read(out/'review-protocol.json')
    env=dict(os.environ,XDG_DATA_HOME=str(out/'xdg/data'),XDG_CONFIG_HOME=str(out/'xdg/config'),XDG_CACHE_HOME=str(out/'xdg/cache'))
    assets=[]
    for name in result['cases']:
        m=read(baseline/'trees'/name/'manifest.json');assert sha(baseline/'trees'/name/'tree.glb')==m['glb_sha256']
        shutil.copy2(baseline/'trees'/name/'tree.glb',project/('baseline-'+name+'.glb'))
        assets.append({'id':'baseline-'+name,'resource':'res://baseline-'+name+'.glb','metrics':m['metrics']})
    # Las cámaras de J3 se reutilizan exactamente para los J2, sin reencuadrarlos.
    views=['front','side','perspective','top','near','medium','far']
    shots=[s for s in protocol['shots'] if s['id'] in views]
    write(out/'comparison-protocol.json',{'baseline':str(baseline),'candidate':str(out),'common_shots':shots,
          'comparison_script_sha256':sha(Path(__file__)),'review_script_sha256':sha(ROOT/'scripts/verify_oak_young_canopy.py')})
    run([GODOT,'--headless','--path',project,'--editor','--import'],out/'logs/comparison-import.log',env)
    reports=[]
    for entry in assets:
        name=entry['id'];config=out/'inputs'/(name+'.json');report=out/(name+'-godot.json')
        write(config,{'output':str(out/'captures'),'report':str(report),'center':protocol['center'],'span':protocol['span'],
                      'original_low':protocol['bounds_blender'][0],'shots':shots,'assets':[entry]})
        run([GODOT,'--path',project,'--audio-driver','Dummy','--script','res://review_painted_oak_pilot.gd','--',config,'--visual'],out/'logs'/(name+'.log'),env)
        r=read(report);assert r['passed'] and len(r['captures'])==7;reports.append(r)
    for name in result['cases']:
        sheet(out,out/(name+'-comparison.jpg'),2,[[(f'captures/{prefix}{name}--{v}.png',f'{label} | {name} | {v}') for prefix,label in [('baseline-','J2 anterior'),('','J3 cobertura/volumen')]] for v in views])
    sheet(out,out/'comparison.jpg',4,[[(f'captures/{prefix}{name}--perspective.png',label+' | '+name) for name in result['cases']] for prefix,label in [('baseline-','J2 anterior'),('','J3 cobertura/volumen')]])
    result.update(comparison_reports=reports,comparison_protocol_sha256=sha(out/'comparison-protocol.json'),
                  captures_sha256={p.name:sha(p) for p in sorted((out/'captures').glob('*.png'))})
    assert len(result['captures_sha256'])==120
    write(out/'verification.json',result)
    page=out/'index.html';s=page.read_text().replace('3.1.0','3.2.0')
    s=s.replace('</h1>','</h1><p>J3:264 grupos, cobertura de todos los ejes y más volumen; madera y pintura conservadas.</p><h2>J2 anterior / J3</h2><img src="comparison.jpg">',1)
    s+=''.join('<h2>'+n+' · antes/después</h2><img src="'+n+'-comparison.jpg">' for n in result['cases'])
    page.write_text(s)
    print('J3 Godot:120 capturas; comparación con cámaras idénticas.',flush=True)


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True)
    p.add_argument('--baseline',type=Path,default=ROOT/'artifacts/roble-joven/j2-completo-01')
    p.add_argument('--stage',choices=('audit','review'),required=True);a=p.parse_args()
    (audit if a.stage=='audit' else review)(a.output.resolve(),a.baseline.resolve())

if __name__=='__main__':main()
