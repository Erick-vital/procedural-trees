#!/usr/bin/env python3
"""Auditoría y evidencia seleccionada PP4; no genera ni acepta pintura."""
import argparse
import copy
import json
from pathlib import Path
import shutil
import struct
import sys
import tempfile
from PIL import Image
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'src'),str(ROOT/'scripts')]
from review_pine_painted import read,write,sha
from treegen.evaluation import validate_result
from treegen.pine_painted_evaluation import inspect_painted_glb
from treegen.foliage_branch_evaluation import inspect_branch_glb


def audit(study,evidence):
    r=read(study/'verification.json');assert r['passed'] and r['visual_requested']
    expected_captures=144 if r['matrix']['blueprint'].endswith('/2.2.0.json') else 108
    assert len(r['capture_sha256'])==expected_captures
    assert all(sha(ROOT/p)==digest for p,digest in r['source_lock'].items())
    for filename,digest in r['capture_sha256'].items():
        p=study/'captures'/filename;assert sha(p)==digest
        im=Image.open(p);assert im.size==(900,900)
        assert len(im.convert('RGB').getcolors(900*900))>100
    for row in r['matrix']['cases']:
        n=row['id'];validate_result(study/n);validate_result(study/('before-'+n))
        for prefix,filename in [('new','tree.glb'),('wood','wood.glb')]:
            assert sha(study/n/filename)==sha(study/'godot'/(prefix+'-'+n+'.glb'))
        assert sha(study/('before-'+n)/'tree.glb')==sha(study/'godot'/('before-'+n+'.glb'))
    mats=[m for report in r['godot'] for n,a in report['assets'].items() if n.startswith(('new-','wood-')) for m in a['materials']]
    assert len(mats)==12
    assert all(m['imported_texture_filter']==5 and m['review_texture_filter']==5 and m['shadow_casting']==2 for m in mats)
    # Inyectar defectos en copias temporales; la evidencia nunca modifica los assets.
    m=read(study/'pilot'/'manifest.json');path=study/'pilot'/'tree.glb';raw=path.read_bytes()
    size=struct.unpack_from('<I',raw,12)[0];doc=json.loads(raw[20:20+size]);binary=raw[28+size:]
    foliage=next(p for p in doc['meshes'][0]['primitives'] if doc['materials'][p['material']]['name']=='Painted_Foliage')
    tests={}
    with tempfile.TemporaryDirectory() as temp:
        target=Path(temp)/'fault.glb'
        for name in ('opaque-foliage','missing-uv','external-image','roughness','shifted-uv','zero-normal'):
            d=copy.deepcopy(doc);b=bytearray(binary)
            p=next(p for p in d['meshes'][0]['primitives'] if d['materials'][p['material']]['name']=='Painted_Foliage')
            if name=='opaque-foliage':d['materials'][p['material']]['alphaMode']='OPAQUE'
            elif name=='missing-uv':p['attributes'].pop('TEXCOORD_0')
            elif name=='external-image':d['images'][0]['uri']='external.png'
            elif name=='roughness':d['materials'][p['material']]['pbrMetallicRoughness']['roughnessFactor']=.3
            else:
                key='NORMAL' if name=='zero-normal' else 'TEXCOORD_0'
                a=d['accessors'][p['attributes'][key]];view=d['bufferViews'][a['bufferView']]
                start=view.get('byteOffset',0)+a.get('byteOffset',0)
                if name=='zero-normal':struct.pack_into('<3f',b,start,0,0,0)
                else:struct.pack_into('<f',b,start,.12345)
            j=json.dumps(d,separators=(',',':')).encode();j+=b' '*((-len(j))%4)
            target.write_bytes(struct.pack('<4sII',b'glTF',2,28+len(j)+len(b))+struct.pack('<II',len(j),0x4e4f534a)+j+struct.pack('<II',len(b),0x004e4942)+b)
            try:inspect_painted_glb(target,m['metrics'],m['resolved_blueprint'])
            except (ValueError,KeyError):tests[name]=True
            else:raise AssertionError('Defecto no rechazado: '+name)
        try:inspect_branch_glb(path,m['metrics'],triangle_limit=12500,wood_material='Painted_Bark',leaf_material='Painted_Foliage')
        except ValueError as exc:
            assert 'transparencia o textura' in str(exc);tests['historical-rejects-texture']=True
        else:raise AssertionError('Ruta histórica permite textura')
    evidence.mkdir(parents=True,exist_ok=True)
    for f in ('comparison.jpg','controls.jpg','wood.jpg','distances.jpg'):
        shutil.copy2(study/f,evidence/f)
    shutil.copy2(study/'captures/new-pilot--perspective.png',evidence/'pilot.png')
    shutil.copy2(study/'verification.json',evidence/'verification.json')
    shutil.copy2(study/'logs/tests.log',evidence/'unit-tests.txt')
    shutil.copy2(study/'reimport.json',evidence/'reimport.json')
    shutil.copy2(study/'protocol.json',evidence/'protocol.json')
    summary={'passed':True,'study':str(study.relative_to(ROOT)),'technical_checks':len(r['checks']),
             'real_captures':expected_captures,'fault_injection_rejections':tests,'godot_adapter_applied':True,
             'source_lock_verified':True,'capture_hashes_verified':True,
             'evidence_generator_sha256':sha(Path(__file__)),'artistic_acceptance':'pending',
             'visual_review':'Revisión del agente documentada en informe.md; no inferida de passed.'}
    write(evidence/'audit.json',summary)
    print(json.dumps(summary,ensure_ascii=False,indent=2))

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--study',type=Path,required=True);p.add_argument('--evidence',type=Path,required=True)
    a=p.parse_args();audit(a.study.resolve(),a.evidence.resolve())
