#!/usr/bin/env python3
"""Auditoría O5 y galería comparativa; no concede aprobación artística."""
import argparse
from collections import Counter
from pathlib import Path
import shutil
import sys
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'src'),str(ROOT/'scripts')]
from treegen.oak_growth_runner import architecture_metrics
from treegen.branch_structure import sub,length
from treegen.oak_crown_evaluation import crown_metrics
from treegen.branch_tree_audit import raw_channels
from treegen.oak_crossed_evaluation import channels
from review_pine_painted import read,write,sha
from foliage_evidence import sheet
from verify_oak_periphery import CASES
from treegen.oak_volume_evaluation import volume_metrics


def mean_primary_rise(s):
    return sum((b['points'][-1][2]-b['points'][0][2])/sum(length(sub(y,x)) for x,y in zip(b['points'],b['points'][1:])) for b in s['branches'] if b['order']==1)/sum(b['order']==1 for b in s['branches'])


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--study',type=Path,required=True);p.add_argument('--repeat',type=Path,required=True)
    p.add_argument('--tests',type=Path,required=True);p.add_argument('--output',type=Path,default=ROOT/'docs/evidence/oak-growth/o5');a=p.parse_args()
    study=a.study.resolve();out=a.output.resolve();out.mkdir(parents=True,exist_ok=True);checks={};cases={}
    historical=read(ROOT/'docs/evidence/oak-growth/o4/verification.json')
    for stage,seed in CASES:
        name=f'{stage}-{seed}';folder=study/name;oldfolder=study/'before'/name
        old=read(oldfolder/'manifest.json');new=read(folder/'manifest.json');r=read(folder/'review.json')
        bs=read(oldfolder/'structure.json');s=read(folder/'structure.json');budget=s['branching_budget']
        before=old['variants']['bare']['metrics']['triangles'];after=new['variants']['bare']['metrics']['triangles']
        checks[name+'-generation']=all(m['status']=='completed' and all(m['checks'].values()) for m in (old,new))
        checks[name+'-sources']=all(sha(ROOT/path)==value for m in (old,new) for path,value in m['source_inventory'].items())
        checks[name+'-same-inputs']=old['seed']==new['seed'] and old['preset']=={**new['preset'],'version':'oak-growth-0.4.0'}
        checks[name+'-budget']=0<=after-budget['base_triangles']==budget['extra_triangles']<=700 and after==before and after+1584<=6999
        topology=lambda items:[(b['id'],len(b['points']),b['sides']) for b in items]
        checks[name+'-base-topology-preserved']=topology(bs['branches'])==topology(s['branches'])
        checks[name+'-godot']=r['passed'] and all(g['passed'] for g in r['godot'])
        joins=read(folder/'joins-audit.json')
        checks[name+'-joins']=joins['passed'] and len(joins['joins'])==len(s['branches'])-1 and max(j['max_signed_distance_m'] for j in joins['joins'])<=1e-5
        checks[name+'-core-subset']=not(Counter(raw_channels(folder/'scaffold/tree.glb')['Painted_Bark'])-Counter(raw_channels(folder/'bare/tree.glb')['Painted_Bark']))
        checks[name+'-scaffold-identical']=sha(folder/'scaffold/tree.glb')==sha(oldfolder/'scaffold/tree.glb')
        checks[name+'-bark-shared']=channels(folder/'bare/tree.glb')[3]==channels(oldfolder/'bare/tree.glb')[3]
        if name in historical['cases']:
            checks[name+'-o4-historical-exact']=all(sha(oldfolder/mode/'tree.glb')==value for mode,value in historical['cases'][name]['glb_sha256'].items())
        before_volume=volume_metrics(bs);after_volume=volume_metrics(s)
        if stage in ('maduro','centenario'):
            checks[name+'-less-core-axis-length']=after_volume['axis_length_over_H']['core']<=before_volume['axis_length_over_H']['core']+1e-8
            checks[name+'-fewer-inner-births']=after_volume['inner_births_order_ge_2']<=before_volume['inner_births_order_ge_2']
            checks[name+'-secondary-births-farther-out']=after_volume['secondary_mean_birth_radius_over_H']>=before_volume['secondary_mean_birth_radius_over_H']-1e-8
            checks[name+'-peripheral-length-increased']=after_volume['axis_length_over_H']['periphery']>before_volume['axis_length_over_H']['periphery']
            checks[name+'-peripheral-cells-increased']=after_volume['occupied_cells_0_10H']['periphery']>before_volume['occupied_cells_0_10H']['periphery']
            checks[name+'-mixed-bough-habits']=len(set(after_volume['habits_by_bough'].values()))>=3
        am=architecture_metrics(s);bm=architecture_metrics(bs)

        cases[name]={'triangles_before':before,'triangles_after':after,'budget':budget,'architecture_before':bm,'architecture_after':am,
            'mean_primary_rise_before':mean_primary_rise(bs),'mean_primary_rise_after':mean_primary_rise(s),
            'search':s['periphery'],'volume_before':before_volume,'volume_after':after_volume,'crown_before':crown_metrics(bs),'crown_after':crown_metrics(s),'duration_seconds':new['duration_seconds'],
            'glb_sha256':{k:v['glb_sha256'] for k,v in new['variants'].items()},'manifest_sha256':sha(folder/'manifest.json'),
            'review_sha256':sha(folder/'review.json'),'captures':len(r['captures_sha256'])}
    cohort=[c for n,c in cases.items() if not n.startswith('joven-')]
    checks['cohort-peripheral-improvement-at-least-eight']=sum(c['volume_after']['axis_length_over_H']['periphery']>c['volume_before']['axis_length_over_H']['periphery'] for c in cohort)>=8
    first=study/'maduro-3100'
    checks['repeat-cli-exact']=all(sha(first/path)==sha(a.repeat/path) for path in ('structure.json','bare/tree.glb','scaffold/tree.glb'))
    tests=a.tests.read_text();checks['tests-pass']='Ran 275 tests' in tests and tests.rstrip().endswith('OK')
    age=read(study/'ages-review.json');checks['normalized-ages']=age['passed'];shutil.copy2(study/'ages.jpg',out/'edades.jpg');shutil.copy2(a.tests,out/'tests.txt')
    images=[('edades','Etapas O5, altura normalizada')]
    for stage in ('maduro','centenario'):
        for view in ('front','perspective'):
            name=stage+'-'+view
            sheet(study,out/(name+'.jpg'),2,[[(f'{stage}-{seed}/captures/{label}-bare--{view}.png',('Antes O4' if label=='before' else 'Ahora O5')+f' | {stage}-{seed}') for label in ('before','after')] for seed in range(3100,3105)])
            images.append((name,stage+' | '+view+' | cinco semillas'))
    for name in ('maduro-3100','maduro-3103','centenario-3100','centenario-3103'):
        for mode in ('bare','scaffold'):
            shutil.copy2(study/name/(mode+'-comparison.jpg'),out/(name+'-'+mode+'.jpg'));images.append((name+'-'+mode,name+' | '+mode+' | cuatro vistas'))
    sheet(study,out/'comparacion-maduro-3100.jpg',2,[[(f'maduro-3100/captures/{label}-bare--perspective.png',f'{title} | maduro 3100') for label,title in [('before','Antes O4'),('after','Ahora O5')]]])
    held_out={}
    from treegen.oak_growth_v4 import generate as baseline
    from treegen.oak_growth_v5 import generate as candidate
    from treegen.oak_crown_contract import load_growth_preset
    from treegen.oak_growth_mesh import meshes
    for stage in ('maduro','centenario'):
        preset=load_growth_preset(ROOT/f'presets/oak-growth/0.5.0/{stage}.json')
        for seed in range(5000,5005):
            old_s=baseline({**preset,'version':'oak-growth-0.4.0'},seed);new_s=candidate(preset,seed)
            x=volume_metrics(old_s);y=volume_metrics(new_s)
            tris=lambda s:sum(len(f)-2 for b in meshes(s) for f in b['mesh']['polygons'])
            ok=y['axis_length_over_H']['core']<=x['axis_length_over_H']['core']+1e-8 and y['axis_length_over_H']['periphery']>=x['axis_length_over_H']['periphery']-1e-8 and y['occupied_cells_0_10H']['periphery']>=x['occupied_cells_0_10H']['periphery'] and tris(old_s)==tris(new_s) and tris(new_s)+1584<=6999
            checks[f'held-out-{stage}-{seed}']=ok
            held_out[f'{stage}-{seed}']={'before':x,'after':y,'triangles':tris(new_s),'passed':ok,'scope':'pure geometry; no new Godot captures or GLB export'}
    report={'version':'oak-periphery-verification-0.1.0','passed':all(checks.values()),'checks':checks,'cases':cases,
        'held_out':held_out,'study':str(study),'source_inventory':read(first/'manifest.json')['source_inventory'],'captures':sum(c['captures'] for c in cases.values())+len(age['captures_sha256']),
        'visual_review':'pending_agent','artistic_acceptance':'pending_user','images_sha256':{p.name:sha(p) for p in out.glob('*.jpg')}}
    write(out/'verification.json',report)
    assert report['passed'],[k for k,v in checks.items() if not v]
    html='<!doctype html><meta charset="utf-8"><title>Roble O5</title><style>body{font:18px sans-serif;background:#eee9df;margin:24px}img{max-width:100%}</style><h1>Antes O4 / ahora O5</h1><p>Mismas semillas y controles, cámaras y luz comunes. Madera sin hojas. Misma geometría presupuestada de O4; reserva de 1584 conservada. Aceptación artística pendiente.</p>'
    html+=''.join('<h2>'+label+'</h2><img src="'+str(out/(name+'.jpg'))+'">' for name,label in images)
    html+='<h2>Todos los casos, cuatro vistas</h2>'
    html+=''.join(f'<h3>{stage}-{seed}</h3><img src="{stage}-{seed}/bare-comparison.jpg"><img src="{stage}-{seed}/scaffold-comparison.jpg">' for stage,seed in CASES)
    (study/'index.html').write_text(html)
    print('Checks',len(checks),'capturas',report['captures'],'passed',report['passed'])

if __name__=='__main__':main()
