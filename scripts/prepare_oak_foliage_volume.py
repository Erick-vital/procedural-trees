#!/usr/bin/env python3
"""OF6: roble maduro completo, OF5 anterior/OF6 periférica, pintura conservada."""
import argparse
from collections import Counter
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
from treegen.oak_foliage_volume_contract import validate_canopy
from treegen.oak_foliage_volume import build,minimum_radius
from treegen.oak_foliage_macro import build as build_of5
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


def generate_canopy(config,out):
    started=time.monotonic();spec=validate_canopy(read(config));out.mkdir(parents=True);(out/'logs').mkdir()
    resources=read(ROOT/'blueprints/roble_copa_ancha/2.2.0.json')['resources'];frozen=validate_resources(resources)
    image=Image.open(ROOT/PATHS['foliage']).convert('RGBA');prepared=prepare_templates(frozen['templates'],image)
    s=generate(load_growth_preset(ROOT/spec['preset']),spec['seed']);result=build(s,spec,frozen['templates'],prepared=prepared)
    old={**spec,'version':'oak-foliage-canopy-0.5.0'}
    reference=build_of5(s,old,frozen['templates'],prepared=prepared)
    baseline=reference['foliage'];old_groups=reference['groups']
    wood=[tube(b) for b in s['branches']]
    sample=[b for b in s['branches'] if b['id']=='p:0' or b['id'].startswith('p:0/')]
    samplewood=[tube(b) for b in sample]
    ids={b['id'] for b in sample}
    samplecards=lambda cs:[c for c in cs if c['source_branch_id'] in ids]
    variants={'bare':{'wood':wood,'foliage':[]},'baseline':{'wood':wood,'foliage':baseline},
        'painted':{'wood':wood,'foliage':result['foliage']},'foliage':{'wood':[],'foliage':result['foliage']},
        'sample-old':{'wood':samplewood,'foliage':samplecards(baseline)},'sample-new':{'wood':samplewood,'foliage':samplecards(result['foliage'])}}
    job={'output':str(out),'branches':[{**b,'mesh':m} for b,m in zip(s['branches'],wood)],'variants':variants}
    source_files=[*sorted((ROOT/'src/treegen').glob('*.py')),*sorted((ROOT/'blender').glob('*.py')),Path(__file__).resolve(),ROOT/spec['preset'],config,
        *[ROOT/'godot'/n for n in ('project.godot','verify_oak.gd','review_painted_pine.gd','review_painted_oak_pilot.gd')]]
    manifest={'version':spec['version'],'scope':'full mature pilot; no production recipe promotion','status':'running','spec':spec,
        'source_inventory':{str(p.relative_to(ROOT)):sha(p) for p in source_files},'resources':resources,'ledger':result['ledger'],
        'template_contacts':prepared,'artist_acceptance':'pending_user'}
    write(out/'manifest.json',manifest);write(out/'o5-structure.json',s);write(out/'input.json',job)
    write(out/'layout.json',{k:v for k,v in result.items() if k not in ('wood','foliage')});write(out/'baseline-groups.json',old_groups)
    env=dict(os.environ,XDG_DATA_HOME=str(out/'xdg/data'),XDG_CONFIG_HOME=str(out/'xdg/config'),XDG_CACHE_HOME=str(out/'xdg/cache'))
    run([os.environ.get('BLENDER_BIN',BLENDER),'--background','--factory-startup','--threads','1','--python-exit-code','1','--python',ROOT/'blender/export_oak_foliage_sample.py','--',out/'input.json'],out/'logs/export.log',env,timeout=max(1,120-(time.monotonic()-started)))
    exports=read(out/'exports.json');checks={};reports={}
    bare=raw_channels(out/'bare/tree.glb')['Painted_Bark']
    for name,item in exports['variants'].items():
        path=out/name/'tree.glb';report=validate_glb(path,{'parameters':{'height_m':item['metrics']['height_m']}},triangle_limit=6999);reports[name]=report
        doc,_,_,images=channels(path);keys=['foliage'] if name=='foliage' else ['bark'] if name=='bare' else ['bark','foliage']
        checks[name+'-textures']=set(images)=={resources[k]['sha256'] for k in keys}
        checks[name+'-triangles']=report['triangles']==item['metrics']['triangles']
        checks[name+'-materials']=len(doc['materials'])==len(keys) and all(m.get('doubleSided') for m in doc['materials'])
        if 'foliage' in keys:
            mat=next(m for m in doc['materials'] if m['name']=='Painted_Foliage');checks[name+'-alpha']=mat.get('alphaMode')=='MASK' and mat.get('alphaCutoff',.5)==.5
        if name not in ('foliage','bare'):
            raw=raw_channels(path)['Painted_Bark'];checks[name+'-wood']=raw==bare if not name.startswith('sample-') else not(Counter(raw)-Counter(bare))
    history=read(ROOT/'docs/evidence/oak-growth/o5/verification.json')['cases'];case='maduro-'+str(spec['seed'])
    if case in history:checks['historical-o5']=exports['variants']['bare']['glb_sha256']==history[case]['glb_sha256']['bare']
    history=read(ROOT/'docs/evidence/oak-foliage/of5/verification.json')['generation']
    if old==history['spec']:
        checks['historical-of5-branch']=exports['variants']['sample-old']['glb_sha256']==history['variants']['sample-new']['glb_sha256']
        checks['historical-of5-full']=exports['variants']['baseline']['glb_sha256']==history['variants']['painted']['glb_sha256']
    checks['exact-global-budget']=reports['painted']['triangles']==result['ledger']['tree_projected_triangles']==reports['baseline']['triangles']
    checks['216-groups']=len(result['groups'])==spec['tree_groups']==len(old_groups)
    checks['reservation']=len(result['groups'])*6<=1584 and 5415+6*spec['tree_groups']<=6999
    checks['core-clear']=result['minimum_card_radius_m']>=spec['core_radius_over_height']*s['preset']['height_m']
    # Auditoría del cilindro también sobre vértices GLB float32 reimportados.
    _,rows,_,_=channels(out/'painted/tree.glb')
    triangles=[{'vertices':[(v[0],-v[2],v[1]) for v in tri],'polygons':[(0,1,2)]} for tri in rows['Painted_Foliage']]
    glb_radius=minimum_radius(triangles);checks['core-clear-export']=glb_radius>=spec['core_radius_over_height']*s['preset']['height_m']-1e-5
    contacts=audit_contacts(out/'painted/tree.glb',result['groups'],image);write(out/'contacts-audit.json',contacts);checks['contacts']=contacts['passed']
    checks['wood-joins']=read(out/'wood-joins.json')['passed']
    manifest.update(status='completed' if all(checks.values()) else 'failed',checks=checks,variants=exports['variants'],
        duration_seconds=time.monotonic()-started,source_structure_sha256=canonical_hash(s),group_count=len(result['groups']),
        minimum_card_radius_export_m=glb_radius,export_validation=reports)
    write(out/'manifest.json',manifest)
    if not all(checks.values()):raise ValueError('Comprobaciones fallidas: '+str([k for k,v in checks.items() if not v]))
    print('Generación:',len(result['groups']),'grupos;',reports['painted']['triangles'],'tris; núcleo',glb_radius,'m',flush=True)


def review_canopy(out):
    m=read(out/'manifest.json');assert m['status']=='completed'
    assert all(sha(ROOT/p)==h for p,h in m['source_inventory'].items())
    project=out/'godot';project.mkdir();captures=out/'captures';captures.mkdir()
    for name in ('project.godot','verify_oak.gd','review_painted_pine.gd','review_painted_oak_pilot.gd'):shutil.copy2(ROOT/'godot'/name,project/name)
    path=project/'review_painted_pine.gd';path.write_text(path.read_text().replace('im.get_width()==1254 and im.get_height()==1254','(im.get_width()==1254 and im.get_height()==1254) or (im.get_width()==2000 and im.get_height()==2000)'))
    entries=[]
    for name in m['variants']:
        shutil.copy2(out/name/'tree.glb',project/(name+'.glb'));entries.append({'id':name,'resource':'res://'+name+'.glb','metrics':m['variants'][name]['metrics']})
    env=dict(os.environ,XDG_DATA_HOME=str(out/'xdg/data'),XDG_CONFIG_HOME=str(out/'xdg/config'),XDG_CACHE_HOME=str(out/'xdg/cache'))
    run([GODOT,'--headless','--path',project,'--editor','--import'],out/'logs/godot-import.log',env)
    results=[];protocols={}
    for scope in ('tree','sample'):
        selected=[e for e in entries if e['id'].startswith('sample-')==(scope=='sample')]
        bounds=[e['metrics']['bounds_blender'] for e in selected];lo=[min(b[0][k] for b in bounds) for k in range(3)];hi=[max(b[1][k] for b in bounds) for k in range(3)]
        center=[(a+b)/2 for a,b in zip(lo,hi)];span=max(b-a for a,b in zip(lo,hi))
        directions=[('front',[0,-1,.12]),('side',[1,0,.12]),('perspective',[1,-1,.4]),('back',[-1,1,.3]),('top',[0,0,1]),('below',[1,-1,-.7])]
        shots=[{'id':name,'camera':camera(center,span,d,span*1.08),'background':'#EEE9DF','light':[-35,-25,0]} for name,d in directions]
        if scope=='tree':
            shots.extend([{'id':name,'camera':camera(center,span,[1,-1,.4],span*scale),'background':bg,'light':light,'receiver':name=='shadow'} for name,scale,bg,light in [
                ('medium',2.2,'#EEE9DF',[-35,-25,0]),('far',4.,'#EEE9DF',[-35,-25,0]),('dark',1.08,'#252A28',[-35,-25,0]),('alternate-light',1.08,'#EEE9DF',[35,120,0]),('shadow',1.4,'#EEE9DF',[-75,-25,0])]])
        protocols[scope]=shots
        for e in selected:
            name=e['id'];config=out/(name+'-review-input.json');report=out/(name+'-godot.json')
            write(config,{'output':str(captures),'report':str(report),'center':center,'span':span,'original_low':lo,'shots':shots[:6] if name in ('bare','foliage') else shots,'assets':[e]})
            run([GODOT,'--path',project,'--audio-driver','Dummy','--script','res://review_painted_oak_pilot.gd','--',config,'--visual'],out/'logs'/('godot-'+name+'.log'),env)
            r=read(report);assert r['passed'];results.append(r);print(name,len(r['captures']),'capturas',flush=True)
    sheet(out,out/'comparison.jpg',3,[[(f'captures/{name}--{view}.png',label+' | '+view) for name,label in [('bare','O5 madera'),('baseline','OF5 anterior'),('painted','OF6 periférica')]] for view in ('front','side','perspective','back','top','below')])
    sheet(out,out/'appearance.jpg',2,[[(f'captures/{n}--{v}.png',label+' | '+v) for n,label in [('baseline','OF5 anterior'),('painted','OF6 periférica')]] for v in ('medium','far','dark','alternate-light','shadow')])
    sheet(out,out/'branch.jpg',2,[[(f'captures/{n}--{v}.png',label+' | '+v) for n,label in [('sample-old','Rama OF5'),('sample-new','Rama OF6')]] for v in ('front','side','perspective','top')])
    sheet(out,out/'preview.jpg',2,[[(f'captures/painted--{v}.png','Maduro 3100 | '+v) for v in ('perspective','top')]])
    write(out/'review.json',{'passed':True,'godot':results,'protocols':protocols,'captures_sha256':{p.name:sha(p) for p in captures.glob('*.png')},'visual_review':'pending_agent','artistic_acceptance':'pending_user','protocol_source_sha256':sha(Path(__file__))})
    html='<!doctype html><meta charset="utf-8"><title>OF6 · maduro 3100</title><style>body{font:18px sans-serif;background:#eee9df;margin:24px}img{max-width:100%}</style><h1>Maduro 3100 · copa OF6 periférica</h1><p>216 grupos · 5010 tris · dos materiales · pintura y madera conservadas. Arte pendiente de revisión.</p>'
    html+=''.join(f'<h2>{label}</h2><img src="{name}.jpg">' for name,label in [('preview','Copa completa'),('comparison','Madera / OF5 / OF6'),('branch','Cambios en la rama p:0'),('appearance','Distancias, fondos y sombras')])
    html+='<p><a href="painted/tree.glb">GLB revisado</a> · <a href="painted/tree.blend">Fuente Blender</a></p>'
    (out/'index.html').write_text(html)


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--config',type=Path,default=ROOT/'configs/oak-foliage/volume-B.json');p.add_argument('--output',type=Path,required=True);p.add_argument('--stage',choices=('all','generate','review'),default='all');a=p.parse_args();out=a.output.resolve()
    if a.stage in ('all','generate'):generate_canopy(a.config.resolve(),out)
    if a.stage in ('all','review'):review_canopy(out)

if __name__=='__main__':main()
