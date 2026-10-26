#!/usr/bin/env python3
"""PP4: cuatro casos, repetición, regresión y galería real de Godot."""
import argparse
import copy
import os
import json
from pathlib import Path
import shutil
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'src'),str(ROOT/'scripts')]
from treegen.runner import execute_blueprint, BLENDER
from treegen.blueprints import canonical_hash
from treegen.evaluation import validate_result
from treegen.pine_painted import build
from review_pine_painted import camera,run,read,write,sha
from verify_foliage_unit import GODOT
from foliage_evidence import sheet


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--stage',choices=['generate','review','all'],default='all')
    parser.add_argument('--visual',action='store_true')
    parser.add_argument('--matrix',type=Path,default=ROOT/'configs/verification/pine-painted-v1.json')
    args=parser.parse_args();out=args.output.resolve()
    matrix=read(args.matrix)
    cards=matrix['blueprint'].endswith('/2.3.0.json')
    optimized=matrix['blueprint'].endswith('/2.2.0.json')
    volume=cards or optimized or matrix['blueprint'].endswith('/2.1.0.json')
    triangles=7520 if volume else 5192
    expected_groups=435 if volume else 241
    if args.stage in ('all','generate'):
        out.mkdir(parents=True,exist_ok=False);(out/'logs').mkdir()
    env=dict(os.environ,PYTHONPATH=str(ROOT/'src'),XDG_DATA_HOME=str(out/'xdg/data'),XDG_CONFIG_HOME=str(out/'xdg/config'),XDG_CACHE_HOME=str(out/'xdg/cache'))
    def command(name,cmd):run(cmd,out/'logs'/(name+'.log'),env);print(name+': OK',flush=True)
    def blender(name,script,*arguments):command(name,[os.environ.get('BLENDER_BIN',BLENDER),'--background','--factory-startup','--threads','1','--python-exit-code','1','--python',ROOT/script,'--',*arguments])
    if args.stage in ('all','generate'):
        report={'passed':False,'matrix':matrix,'cases':{},'checks':{}}
        write(out/'verification.json',report)
        command('tests',[sys.executable,'-m','unittest','discover','-s','tests','-v'])
        cases=copy.deepcopy(matrix['cases'])
        for row in matrix['cases']:
            i=read(ROOT/f'presets/blueprints/{"pino-pintado-madera" if cards else "pino-pintado-volumen" if optimized else "pino-pintado" if volume else "pino-v2"}/{row["id"]}.json')
            cases.append({'id':'before-'+row['id'],'instance':i,'blueprint':'blueprints/pino_conico/'+('2.2.0' if cards else '2.1.0' if optimized else '2.0.0' if volume else '1.1.0')+'.json'})
        cases.append({'id':'pilot-render','instance':copy.deepcopy(matrix['cases'][0]['instance']),'render':True})
        cases.append({'id':'pilot-repeat','instance':copy.deepcopy(matrix['cases'][0]['instance'])})
        i=copy.deepcopy(matrix['cases'][0]['instance']);i['seeds']['paint']+=1
        cases.append({'id':'paint-seed','instance':i})
        cases += [{'id':'oak-reference','blueprint':'blueprints/roble_copa_ancha/1.0.0.json','instance':read(ROOT/'presets/blueprints/roble-copa-ancha-viejo-09.json')},
                  {'id':'columnar-reference','blueprint':'blueprints/arbol_copa_columnar/1.0.0.json','instance':read(ROOT/'configs/verification/b4-v1.json')['cases'][0]['instance']}]
        manifests={}
        for row in cases:
            name=row['id'];m=execute_blueprint(ROOT/row.get('blueprint',matrix['blueprint']),row['instance'],out/name,render=row.get('render',False))
            manifests[name]=m
            report['cases'][name]={k:m[k] for k in ('glb_sha256','metrics','duration_seconds','glb_bytes','wood_sha256')}
            write(out/'verification.json',report);print(name+': generado',flush=True)
        c=report['checks'];pilot=manifests['pilot']
        c['render-preserves-glb']=pilot['glb_sha256']==manifests['pilot-render']['glb_sha256']
        c['repeat-identical']=pilot['glb_sha256']==manifests['pilot-repeat']['glb_sha256']
        c['repeat-placements']=pilot['placements_sha256']==manifests['pilot-repeat']['placements_sha256']
        c['paint-preserves-geometry']=pilot['export_validation']['channel_sha256']==manifests['paint-seed']['export_validation']['channel_sha256']
        c['paint-changes-atlas']=pilot['glb_sha256']!=manifests['paint-seed']['glb_sha256']
        c['four-distinct']=len({manifests[r['id']]['glb_sha256'] for r in matrix['cases']})==4
        historic=read(ROOT/('docs/evidence/pino-pintado/pp4-madera/verification.json' if cards else 'docs/evidence/pino-pintado/pp4-volumen/verification.json' if optimized else 'docs/evidence/pino-pintado/pp4/verification.json' if volume else 'docs/evidence/blueprints/pino-revision/verification.json'))
        reimports=[]
        for row in matrix['cases']:
            n=row['id'];m=manifests[n];old=manifests['before-'+n]
            c[n+'-parameters']=m['resolved_blueprint']['parameters']==pilot['resolved_blueprint']['parameters']
            c[n+'-height-reduction']=m['metrics']['height_m']==12 and (m['metrics']['triangles']<triangles if optimized or cards else m['metrics']['triangles']==triangles) and len(m['metrics']['triangles_by_material'])==2
            c[n+'-reference-exact']=old['glb_sha256']==historic['cases'][n]['glb_sha256']
            new_ref=read(out/n/'base-reference.json');old_ref=read(out/('before-'+n)/'base-reference.json')
            c[n+'-all-paths-exact']=new_ref['branches']==old_ref['branches']
            groups=read(out/n/'placements.json')
            from treegen.pine import point_on
            supports={b['id']:b for b in new_ref['branches']}
            c[n+'-anchors']=all(g['origin_m']==point_on(supports[g['support_id']],g['anchor_t']) for g in groups) and len(groups)==expected_groups and len({g.get('group_id',g['support_id']) for g in groups})==expected_groups
            if volume and not optimized and not cards:
                c[n+'-wood-identical-pp4']=m['export_validation']['channel_sha256']['Painted_Bark']==old['export_validation']['channel_sha256']['Painted_Bark']
                c[n+'-resources-identical-pp4']=m['resources']==old['resources']
            if cards:
                from treegen.pine_painted_cards import optimize
                old_parts=build(old['resolved_blueprint']);new_parts=build(m['resolved_blueprint'])
                c[n+'-wood-exact']=old_parts[1]==new_parts[1] and m['wood_sha256']==old['wood_sha256']
                c[n+'-cards-common-rule']=all(optimize(a)==g for a,g in zip(old_parts[2],new_parts[2]))
                c[n+'-cards-half-triangles']=m['metrics']['triangles_by_material']['Painted_Foliage']==2610
                c[n+'-resources-identical']=m['resources']==old['resources']
            if optimized:
                from treegen.pine_painted_wood import sampled_surface_error
                old_parts=build(old['resolved_blueprint']);new_parts=build(m['resolved_blueprint'])
                errors={a['id']:sampled_surface_error(a,b) for a,b in zip(old_parts[1],new_parts[1])}
                report.setdefault('wood_surface_error_m',{})[n]=errors
                c[n+'-wood-surface-5mm']=max(errors.values())<=.005001
                c[n+'-wood-fewer-triangles']=sum(len(b['mesh']['polygons']) for b in new_parts[1])<2000
                c[n+'-foliage-only-explicit-tuning']=all(g['crown_tuning']['before_tuning_sha256']==canonical_hash(a) for a,g in zip(old_parts[2],new_parts[2]))
                c[n+'-resources-identical']=m['resources']==old['resources']
            c[n+'-export']=validate_result(out/n)['exported_anchors_and_groups_valid']
            for prefix,painted in [('',True),('before-',volume)]:
                name=prefix+n
                reimports.append({'path':str(out/name/'tree.glb'),'triangles':manifests[name]['metrics']['triangles'],'painted':painted})
            reimports.append({'path':str(out/n/'wood.glb'),'triangles':read(out/n/'wood-metrics.json')['triangles'],'painted':True})
            if optimized:reimports.append({'path':str(out/('before-'+n)/'wood.glb'),'triangles':2300,'painted':True})
        lock=read(ROOT/'docs/evidence/blueprints/b0/reference-lock.json')
        c['oak-b0-identical']=manifests['oak-reference']['glb_sha256']==lock['files_sha256'][lock['pilot_directory']+'/tree.glb']
        c['columnar-b4-identical']=manifests['columnar-reference']['glb_sha256']==read(ROOT/'docs/evidence/blueprints/b4/verification.json')['cases']['pilot']['glb_sha256']
        write(out/'reimport-input.json',reimports)
        blender('reimport','blender/verify_painted_pine.py',out/'reimport-input.json',out/'reimport.json')
        c['reimport']=read(out/'reimport.json')['passed']
        report['source_lock']={str(p.relative_to(ROOT)):sha(p) for folder in ('src/treegen','blender','schemas','godot','assets/pino-pintado/v0.1.0') for p in sorted((ROOT/folder).rglob('*')) if p.is_file() and '__pycache__' not in str(p)}
        report['source_lock'].update({str(p.relative_to(ROOT)):sha(p) for p in [Path(__file__),ROOT/'scripts/review_pine_painted.py',ROOT/'scripts/verify_foliage_unit.py',ROOT/matrix['blueprint'],args.matrix.resolve()]})
        report['passed']=all(c.values());write(out/'verification.json',report)
        assert report['passed'],[n for n,v in c.items() if not v]
    if args.stage=='generate':return
    report=read(out/'verification.json')
    assert all(sha(ROOT/p)==v for p,v in report['source_lock'].items()),'Fuentes/recursos alterados entre generación y revisión'
    project=out/'godot';project.mkdir(exist_ok=False);captures=out/'captures';captures.mkdir()
    for f in ('project.godot','verify_oak.gd','review_painted_pine.gd','painted_pine_asset.gd'):shutil.copy2(ROOT/'godot'/f,project/f)
    center=[0,0,6];span=12
    shots=[{'id':name,'camera':camera(center,span,d,scale),'background':'#EEE9DF','light':[-35,-25,0]} for name,d,scale in [
        ('front',[0,-1,.1],15.6),('side',[1,0,.1],15.6),('perspective',[1,-1,.45],15.6),
        ('back',[-1,1,.3],15.6),('top',[0,0,1],15.6),('below',[1,-1,-.7],15.6),
        ('near',[1,-1,.45],24),('medium',[1,-1,.45],48),('far',[1,-1,.45],120)]]
    write(out/'protocol.json',{'center':center,'span':span,'shots':shots,'resolution':[900,900],'material_decision':read(ROOT/'configs/inspection/pine-painted-pp3-v1.json')})
    entries=[]
    for row in matrix['cases']:
        for kind in (('before','new','wood','before-wood') if optimized else ('before','new','wood')):
            n=row['id'];folder=out/(('before-' if kind in ('before','before-wood') else '')+n)
            filename='wood.glb' if kind in ('wood','before-wood') else 'tree.glb';name=kind+'-'+n
            metrics=read(folder/('wood-metrics.json' if kind in ('wood','before-wood') else 'manifest.json'))
            if kind not in ('wood','before-wood'):metrics=metrics['metrics']
            shutil.copy2(folder/filename,project/(name+'.glb'))
            resource='res://'+name+'.glb'
            if kind in ('new','wood','before-wood'):
                scene='[gd_scene load_steps=3 format=3]\n\n[ext_resource type="PackedScene" path="res://'+name+'.glb" id="1"]\n[ext_resource type="Script" path="res://painted_pine_asset.gd" id="2"]\n\n[node name="PaintedPine" instance=ExtResource("1")]\nscript = ExtResource("2")\n'
                (project/(name+'.tscn')).write_text(scene)
                resource='res://'+name+'.tscn'
            entries.append({'id':name,'resource':resource,'metrics':metrics})
    godot=os.environ.get('GODOT_BIN',GODOT)
    command('godot-import',[godot,'--headless','--path',project,'--editor','--import'])
    reports=[]
    for index in range(0,len(entries),2):
        config=out/f'review-input-{index}.json';result=out/f'review-report-{index}.json'
        write(config,{'output':str(captures),'report':str(result),'span':span,'center':center,'original_low':[0,0,0],'assets':entries[index:index+2],'shots':shots})
        cmd=[godot,'--path',project,'--audio-driver','Dummy','--script','res://review_painted_pine.gd','--',config]
        if args.visual:cmd.append('--visual')
        else:cmd.insert(1,'--headless')
        command('godot-'+str(index),cmd);reports.append(read(result))
    report['godot']=reports;report['visual_requested']=args.visual
    report['capture_sha256']={p.name:sha(p) for p in sorted(captures.glob('*.png'))}
    report['real_captures']=len(report['capture_sha256'])
    report['checks']['godot']=all(r['passed'] for r in reports)
    report['checks']['captures']=report['real_captures']==(len(entries)*len(shots) if args.visual else 0)
    report['passed']=all(report['checks'].values());write(out/'verification.json',report)
    if args.visual:
        for filename,kinds,views in [('comparison.jpg',('before','new'),('front','side','perspective')),
                                      ('controls.jpg',('new',),('front','side','perspective','back','top','below')),
                                      ('wood.jpg',('wood',),('front','side','perspective')),
                                      ('distances.jpg',('new',),('near','medium','far'))]:
            rows=[[(f'captures/{kind}-{r["id"]}--{v}.png',kind+' '+r['id']+' | '+v) for r in matrix['cases']] for v in views for kind in kinds]
            sheet(out,out/filename,4,rows)
        if optimized:
            sheet(out,out/'wood-comparison.jpg',4,[[(f'captures/{kind}-{r["id"]}--{view}.png',kind+' '+r['id']+' | '+view) for r in matrix['cases']] for view in ('front','side','perspective') for kind in ('before-wood','wood')])
        cells=''.join('<figure><a href="captures/'+c+'"><img width="250" src="captures/'+c+'"></a><figcaption>'+c+'</figcaption></figure>' for c in report['capture_sha256'])
        (out/'index.html').write_text('<!doctype html><meta charset="utf-8"><title>PP4 · Pino pintado completo</title><style>body{font:16px sans-serif;background:#eee}main{display:flex;flex-wrap:wrap}figure{margin:8px}</style><h1>PP4 · Pino pintado completo</h1><p>Antes/nuevo: versiones explícitas en matriz y manifiestos. Cuatro semillas conocidas, cámaras y luz comunes. Aprobación artística pendiente.</p><p><a href="comparison.jpg">Comparación</a> · <a href="controls.jpg">Controles</a> · <a href="wood.jpg">Madera</a> · <a href="distances.jpg">Distancias</a> · <a href="verification.json">Verificación</a></p><main>'+cells+'</main>')
    assert report['passed']
    print('PP4: passed='+str(report['passed'])+'; capturas='+str(report['real_captures']),flush=True)

if __name__=='__main__':main()
