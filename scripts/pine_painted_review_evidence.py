#!/usr/bin/env python3
"""Seleccionar evidencia real PP3 y auditar capturas, recursos y comparación alfa."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import sys
from PIL import Image, ImageChops
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
from foliage_evidence import sheet


def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def read(p):return json.loads(Path(p).read_text())
def write(p,v):Path(p).write_text(json.dumps(v,indent=2,ensure_ascii=False,allow_nan=False)+'\n')

def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('study',type=Path);parser.add_argument('--evidence',type=Path,required=True)
    args=parser.parse_args();out=args.study.resolve();e=args.evidence.resolve();e.mkdir(parents=True,exist_ok=True)
    report=read(out/'review-report.json');lock=report['source_lock'];source=Path(lock['source'])
    checks={}
    checks['270_real_captures']=report['visual'] and report['total_captures']==270 and len(list((out/'captures').glob('*.png')))==270
    checks['source_glbs_unchanged']=lock['glbs']=={n:sha(source/n/'branch.glb') for n in lock['glbs']}
    checks['imported_glbs_unchanged']=lock['glbs']=={n:sha(out/'godot'/(n+'.glb')) for n in lock['glbs']}
    checks['sources_unchanged']=lock['sources_sha256']=={n:sha(ROOT/n) for n in lock['sources_sha256']}
    checks['pp2_lock_unchanged']=lock['pp2_reference_sha256']==sha(source/'reference-lock.json') and lock['pp2_manifest_sha256']==sha(source/'manifest.json')
    shots={}
    for stage in ('baseline','full','aa'):
        protocol=read(out/(stage+'-protocol.json'))
        shots.update({s['id']:s for s in protocol['shots']})
    pairs=set();settings_ok=True;dimensions_ok=True
    for c in report['captures']:
        pair=(c['asset'],c['shot']);assert pair not in pairs;pairs.add(pair)
        dimensions_ok &= Image.open(out/'captures'/c['path']).size==(900,900)
        shot=shots[c['shot']]
        if c['asset']!='original':
            fol=next(m for m in c['material_settings'] if m['name']=='Painted_Foliage')
            settings_ok &= fol['alpha_aa']==shot.get('alpha_aa',0)
            settings_ok &= fol['filter']==(1 if shot.get('no_mips',False) else 5)
    expected={(n,s['id']) for s in shots.values() for n in ('original','folded','crossed') if not s.get('only') or s['only']==n}
    checks['capture_coverage']=pairs==expected
    checks['capture_settings']=settings_ok;checks['capture_resolution']=dimensions_ok
    aa=[]
    for bg in ('light','dark'):
        for view in ('three_quarter','side','end_on','near','medium','far'):
            files=[out/'captures'/f'crossed--aa-{m}-{bg}-{view}.png' for m in ('off','coverage','coverage-one')]
            ims=[Image.open(p).convert('RGB') for p in files]
            aa.append({'background':bg,'view':view,'coverage_same_pixels':ImageChops.difference(ims[0],ims[1]).getbbox() is None,
                       'coverage_one_same_pixels':ImageChops.difference(ims[0],ims[2]).getbbox() is None})
    motion={}
    for mode in ('mips','nomips'):
        masks=[]
        for i in range(12):
            im=Image.open(out/'captures'/f'crossed--motion-{mode}-{i:02}.png').convert('RGB')
            channels=ImageChops.difference(im,Image.new('RGB',im.size,im.getpixel((0,0)))).split()
            maximum=ImageChops.lighter(ImageChops.lighter(channels[0],channels[1]),channels[2])
            masks.append(maximum.point(lambda value:255 if value>5 else 0))
        delta=[ImageChops.difference(a,b).histogram()[255] for a,b in zip(masks,masks[1:])]
        motion[mode]={'foreground_pixels':[m.histogram()[255] for m in masks],'changed_pixels':delta,'mean_changed_pixels':sum(delta)/len(delta)}
    detail_report=read(out/'details.json')
    checks['12_real_detail_captures']=detail_report['passed'] and len(detail_report['captures'])==12 and len(list((out/'captures/details').glob('*.png')))==12
    result={'total_real_captures':len(report['captures'])+len(detail_report['captures']),'passed':all(checks.values()),'checks':checks,'alpha_aa_comparison':aa,'motion':motion,
        'motion_method':'Máscara RGB: diferencia máxima >5/255 respecto del fondo. Cámara avanza 0.25 px por captura; sin compensación de movimiento. No es FPS ni métrica perceptual.',
        'source_glbs':lock['glbs'],'capture_png_sha256':{c['path']:sha(out/'captures'/c['path']) for c in report['captures']},
        'evidence_script_sha256':sha(Path(__file__))}
    write(out/'evidence-verification.json',result);assert result['passed']
    sheet(out,e/'comparacion.jpg',3,[[(f'captures/{n}--base-{v}.png',n+' | '+v) for n in ('original','folded','crossed')] for v in ('front','side','three_quarter','top','below','end_on')])
    sheet(out,e/'luces.jpg',3,[[(f'captures/crossed--dark-{light}-{v}.png',light+' | '+v) for light in ('reference','side','back')] for v in ('three_quarter','below','end_on','top')])
    sheet(out,e/'distancias.jpg',3,[[(f'captures/{n}--{bg}-tree-{d}.png',n+' | '+bg+' | '+d) for d in ('near','medium','far')] for bg in ('light','dark') for n in ('original','crossed')])
    sheet(out,e/'sombras.jpg',3,[[(f'captures/{n}--shadow-{light}.png',n+' | '+light) for light in ('reference','side','back')] for n in ('original','folded','crossed')])
    sheet(out,e/'giro.jpg',6,[[(f'captures/crossed--orbit-{i:03}.png',f'{i*5} grados') for i in range(start,start+24,4)] for start in (0,24,48)])
    sheet(out,e/'alfa.jpg',3,[[(f'captures/crossed--aa-{mode}-{bg}-{view}.png',mode+' | '+bg+' | '+view) for mode in ('off','coverage','coverage-one')] for bg,view in [('dark','three_quarter'),('dark','near'),('light','side')]])
    for mode in ('mips','nomips'):
        frames=[]
        for i in range(12):
            im=Image.open(out/'captures'/f'crossed--motion-{mode}-{i:02}.png').convert('RGB')
            frames.append(im)
        frames[0].save(out/(f'motion-{mode}.gif'),save_all=True,append_images=frames[1:],duration=100,loop=0)
    frames=[Image.open(out/'captures'/f'crossed--orbit-{i:03}.png').convert('RGB') for i in range(72)]
    frames[0].save(out/'orbit.gif',save_all=True,append_images=frames[1:],duration=70,loop=0)
    sheet(out,e/'detalles.jpg',4,[[(f'captures/details/crossed--{name}-{i:02}.png',name+' | '+str(i)) for i in group] for name,group in [('bark',range(4)),('bark',range(4,8)),('join',range(4))]])
    shutil.copy2(out/'details.json',e/'details.json')
    shutil.copy2(out/'inputs/details.json',e/'details-protocol.json')
    result['details_script_sha256']=sha(ROOT/'scripts/pine_painted_review_details.py')
    result['detail_png_sha256']={c['path']:sha(out/'captures/details'/c['path']) for c in detail_report['captures']}
    write(out/'evidence-verification.json',result)
    for filename in ('review-report.json','source-lock.json','baseline-protocol.json','full-protocol.json','aa-protocol.json','evidence-verification.json'):
        shutil.copy2(out/filename,e/filename)
    shutil.copy2(out/'captures/crossed--base-three_quarter.png',e/'cruzadas-godot.png')
    print(json.dumps({'passed':result['passed'],'captures':len(report['captures']),'motion':motion,'aa_pairs':len(aa)},indent=2))

if __name__=='__main__':main()
