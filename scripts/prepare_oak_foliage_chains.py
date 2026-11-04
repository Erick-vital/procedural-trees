#!/usr/bin/env python3
"""OF2: rama O5, nueva distribución y pintura actual; muestra antes de integrar."""
import argparse
from collections import Counter
import json
import os
from pathlib import Path
import shutil
import sys
import time
from PIL import Image
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'src'),str(ROOT/'scripts')]
from treegen.oak_crown_contract import load_growth_preset
from treegen.oak_growth_v5 import generate
from treegen.oak_growth_mesh import tube
from treegen.oak_foliage_chain_contract import validate_sample
from treegen.oak_foliage_chains import build
from treegen.oak_foliage_cards import prepare_templates
from treegen.oak_foliage_evaluation import audit_contacts
from treegen.oak_crossed_production import validate_resources,PATHS
from treegen.oak_crossed_evaluation import channels
from treegen.branch_tree_audit import raw_channels
from treegen.evaluation import validate_glb
from treegen.runner import BLENDER
from treegen.pine_painted_sample import canonical_hash
from review_pine_painted import read,write,sha,camera
from verify_branch_space import run
from verify_foliage_unit import GODOT
from foliage_evidence import sheet


def generate_sample(config,out):
    started=time.monotonic();spec=validate_sample(read(config));out.mkdir(parents=True);(out/'logs').mkdir()
    resources=read(ROOT/'blueprints/roble_copa_ancha/2.2.0.json')['resources'];frozen=validate_resources(resources)
    image=Image.open(ROOT/PATHS['foliage']).convert('RGBA');prepared=prepare_templates(frozen['templates'],image)
    s=generate(load_growth_preset(ROOT/spec['preset']),spec['seed']);result=build(s,spec,frozen['templates'],prepared=prepared)
    wood=[tube(b) for b in result['wood']];full=[tube(b) for b in s['branches']]
    job={'output':str(out),'branches':[{**b,'mesh':m} for b,m in zip(result['wood'],wood)],'variants':{
        'reference':{'wood':full,'foliage':[]},'bare':{'wood':wood,'foliage':[]},
        'painted':{'wood':wood,'foliage':result['foliage']},'foliage':{'wood':[],'foliage':result['foliage']}}}
    source_files=[*sorted((ROOT/'src/treegen').glob('*.py')),*sorted((ROOT/'blender').glob('*.py')),Path(__file__).resolve(),ROOT/spec['preset'],config,*[ROOT/'godot'/n for n in ('project.godot','verify_oak.gd','review_painted_pine.gd','review_painted_oak_pilot.gd')]]
    manifest={'version':spec['version'],'scope':'O5 branch sample; full-tree foliage not integrated','status':'running','spec':spec,
        'source_inventory':{str(p.relative_to(ROOT)):sha(p) for p in source_files},'resources':resources,'ledger':result['ledger'],
        'template_contacts':prepared,'artist_acceptance':'pending_user'}
    write(out/'manifest.json',manifest);write(out/'o5-structure.json',s);write(out/'input.json',job)
    write(out/'layout.json',{k:v for k,v in result.items() if k not in ('wood','foliage')})
    env=dict(os.environ,XDG_DATA_HOME=str(out/'xdg/data'),XDG_CONFIG_HOME=str(out/'xdg/config'),XDG_CACHE_HOME=str(out/'xdg/cache'))
    run([os.environ.get('BLENDER_BIN',BLENDER),'--background','--factory-startup','--threads','1','--python-exit-code','1','--python',ROOT/'blender/export_oak_foliage_sample.py','--',out/'input.json'],out/'logs/export.log',env,timeout=max(1,120-(time.monotonic()-started)))
    exports=read(out/'exports.json');checks={};reports={}
    for name,item in exports['variants'].items():
        path=out/name/'tree.glb';report=validate_glb(path,{'parameters':{'height_m':item['metrics']['height_m']}},triangle_limit=6999);reports[name]=report
        doc,_,_,images=channels(path)
        expected={resources[k]['sha256'] for k in (['foliage'] if name=='foliage' else ['bark','foliage'] if name=='painted' else ['bark'])}
        checks[name+'-textures']=set(images)==expected
        checks[name+'-triangles']=report['triangles']==item['metrics']['triangles']
        checks[name+'-materials']=len(doc['materials'])==(2 if name=='painted' else 1) and all(m.get('doubleSided') for m in doc['materials'])
        for mat in doc['materials']:
            if mat['name']=='Painted_Foliage':checks[name+'-alpha']=mat.get('alphaMode')=='MASK' and mat.get('alphaCutoff',.5)==.5
    raw=raw_channels(out/'painted/tree.glb');bare=raw_channels(out/'bare/tree.glb')['Painted_Bark'];ref=raw_channels(out/'reference/tree.glb')['Painted_Bark']
    checks['wood-unchanged-with-foliage']=raw['Painted_Bark']==bare
    checks['wood-exact-o5-subset']=not(Counter(bare)-Counter(ref))
    history=read(ROOT/'docs/evidence/oak-growth/o5/verification.json')['cases']
    case=spec['preset'].split('/')[-1].replace('.json','')+'-'+str(spec['seed'])
    checks['o5-historical-regression']=exports['variants']['reference']['glb_sha256']==history[case]['glb_sha256']['bare'] if case in history else True
    count=len(result['groups']);checks['sample-ledger']=count==result['ledger']['primary_quotas'][spec['branch_id']]
    checks['six-tris-per-group']=reports['painted']['triangles']-reports['bare']['triangles']==6*count
    checks['whole-tree-reservation']=sum(result['ledger']['primary_quotas'].values())*6<=1584 and result['ledger']['tree_projected_triangles']<=6999
    checks['family-upper-bound']=5415+6*spec['tree_groups']<=6999
    contacts=audit_contacts(out/'painted/tree.glb',result['groups'],image);write(out/'contacts-audit.json',contacts);checks['opaque-contacts-glb']=contacts['passed']
    checks['wood-joins']=read(out/'wood-joins.json')['passed']
    manifest.update(status='completed' if all(checks.values()) else 'failed',checks=checks,variants=exports['variants'],
        duration_seconds=time.monotonic()-started,source_structure_sha256=canonical_hash(s),group_count=count,
        wood_ids=[b['id'] for b in result['wood']],export_validation=reports)
    write(out/'manifest.json',manifest)
    if not all(checks.values()):raise ValueError('Comprobaciones fallidas: '+str([k for k,v in checks.items() if not v]))
    print('Generación:',count,'grupos;',reports['painted']['triangles'],'tris;',result['ledger']['tree_projected_triangles'],'proyectados con copa completa.',flush=True)


def review_sample(out):
    m=read(out/'manifest.json');assert m['status']=='completed'
    assert all(sha(ROOT/p)==h for p,h in m['source_inventory'].items())
    project=out/'godot';project.mkdir();captures=out/'captures';captures.mkdir()
    for name in ('project.godot','verify_oak.gd','review_painted_pine.gd','review_painted_oak_pilot.gd'):shutil.copy2(ROOT/'godot'/name,project/name)
    path=project/'review_painted_pine.gd';path.write_text(path.read_text().replace('im.get_width()==1254 and im.get_height()==1254','(im.get_width()==1254 and im.get_height()==1254) or (im.get_width()==2000 and im.get_height()==2000)'))
    entries=[]
    for name in ('bare','painted','foliage'):
        shutil.copy2(out/name/'tree.glb',project/(name+'.glb'));entries.append({'id':name,'resource':'res://'+name+'.glb','metrics':m['variants'][name]['metrics']})
    bounds=[e['metrics']['bounds_blender'] for e in entries];lo=[min(b[0][k] for b in bounds) for k in range(3)];hi=[max(b[1][k] for b in bounds) for k in range(3)]
    center=[(a+b)/2 for a,b in zip(lo,hi)];span=max(b-a for a,b in zip(lo,hi))
    directions=[('front',[0,-1,.12]),('side',[1,0,.12]),('perspective',[1,-1,.4]),('back',[-1,1,.3]),('top',[0,0,1]),('below',[1,-1,-.7])]
    shots=[{'id':name,'camera':camera(center,span,d,span*1.15),'background':'#EEE9DF','light':[-35,-25,0]} for name,d in directions]
    shots.extend([{'id':name,'camera':camera(center,span,[1,-1,.4],span*scale),'background':background,'light':light,'receiver':name.startswith('shadow_')} for name,scale,background,light in [
        ('medium',2.2,'#EEE9DF',[-35,-25,0]),('far',4.,'#EEE9DF',[-35,-25,0]),('dark',1.15,'#252A28',[-35,-25,0]),('alternate-light',1.15,'#EEE9DF',[35,120,0]),('shadow_perspective',1.4,'#EEE9DF',[-75,-25,0])]])
    groups=read(out/'layout.json')['groups'];detail=groups[len(groups)//2]
    close_span=max(detail['size_m'])*1.8
    shots.append({'id':'contact-close','camera':camera(detail['anchor_m'],close_span,[1,-1,.4],close_span),'background':'#EEE9DF','light':[-35,-25,0]})
    env=dict(os.environ,XDG_DATA_HOME=str(out/'xdg/data'),XDG_CONFIG_HOME=str(out/'xdg/config'),XDG_CACHE_HOME=str(out/'xdg/cache'))
    run([GODOT,'--headless','--path',project,'--editor','--import'],out/'logs/godot-import.log',env)
    results=[]
    for e in entries:
        name=e['id'];config=out/(name+'-review-input.json');report=out/(name+'-godot.json')
        write(config,{'output':str(captures),'report':str(report),'center':center,'span':span,'original_low':lo,'shots':shots,'assets':[e]})
        run([GODOT,'--path',project,'--audio-driver','Dummy','--script','res://review_painted_oak_pilot.gd','--',config,'--visual'],out/'logs'/('godot-'+name+'.log'),env)
        r=read(report);assert r['passed'];results.append(r)
    sheet(out,out/'comparison.jpg',2,[[(f'captures/{name}--{view}.png',('O5 madera' if name=='bare' else 'OF2 follaje')+' | '+view) for name in ('bare','painted')] for view in ('front','side','perspective','top','below')])
    sheet(out,out/'appearance.jpg',2,[[(f'captures/painted--{a}.png',a),(f'captures/painted--{b}.png',b)] for a,b in [('perspective','back'),('medium','far'),('dark','alternate-light'),('shadow_perspective','top')]])
    write(out/'review.json',{'passed':True,'godot':results,'shots':shots,'captures_sha256':{p.name:sha(p) for p in captures.glob('*.png')},'visual_review':'pending_agent','artistic_acceptance':'pending_user'})
    html='<!doctype html><meta charset="utf-8"><title>Rama O5 · follaje OF2</title><style>body{font:18px sans-serif;background:#eee9df;margin:24px}img{max-width:100%}</style><h1>Rama O5 con follaje · OF2</h1><p>Maduro3100, p:0. Pintura actual, madera exacta y reserva global; aceptación artística pendiente. Sin integrar árbol completo.</p>'
    html+='<h2>Madera / follaje</h2><img src="comparison.jpg"><h2>Aspecto y distancias</h2><img src="appearance.jpg">'
    html+=''.join('<h2>'+name+'</h2><img src="captures/'+name+'">' for name in sorted(p.name for p in captures.glob('*.png')))
    (out/'index.html').write_text(html);print('Godot:',len(list(captures.glob('*.png'))),'capturas verificadas.',flush=True)


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--config',type=Path,default=ROOT/'configs/oak-foliage/chains-B.json');p.add_argument('--output',type=Path,required=True);p.add_argument('--stage',choices=('all','generate','review'),default='all');a=p.parse_args();out=a.output.resolve()
    if a.stage in ('all','generate'):generate_sample(a.config.resolve(),out)
    if a.stage in ('all','review'):review_sample(out)

if __name__=='__main__':main()
