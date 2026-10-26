#!/usr/bin/env python3
"""Auditar GLB PP2: UV, alfa, imágenes embebidas y repetición opcional."""
import argparse
import hashlib
import io
import json
from pathlib import Path
import struct
from PIL import Image


def inspect(path):
    data=path.read_bytes()
    assert struct.unpack_from('<4sII',data)==(b'glTF',2,len(data))
    n=struct.unpack_from('<I',data,12)[0];doc=json.loads(data[20:20+n]);binary=data[28+n:]
    assert not any('uri' in b for b in doc['buffers'])
    mats={m['name']:m for m in doc['materials']}
    for mesh in doc['meshes']:
        for p in mesh['primitives']:
            a=doc['accessors'][p['attributes']['TEXCOORD_0']]
            view=doc['bufferViews'][a['bufferView']]
            assert a['componentType']==5126 and a['type']=='VEC2'
            start=view.get('byteOffset',0)+a.get('byteOffset',0);stride=view.get('byteStride',8)
            uv=[struct.unpack_from('<2f',binary,start+i*stride) for i in range(a['count'])]
            import math
            assert all(math.isfinite(v) for pair in uv for v in pair)
            if 'Painted_Foliage' in mats and doc['materials'][p['material']]['name']=='Painted_Foliage':
                assert all(0<=v<=1 for pair in uv for v in pair)
    images=[]
    for im in doc.get('images',[]):
        assert 'uri' not in im
        view=doc['bufferViews'][im['bufferView']];start=view.get('byteOffset',0)
        png=binary[start:start+view['byteLength']];image=Image.open(io.BytesIO(png))
        assert max(image.size)<=2048
        if im['name'].startswith('foliage'):assert image.mode=='RGBA' and image.getchannel('A').getextrema()==(0,255)
        images.append({'name':im['name'],'dimensions':image.size,'bytes':len(png),'mode':image.mode})
    if 'Painted_Foliage' in mats:
        assert mats['Painted_Foliage']['alphaMode']=='MASK'
        assert mats['Painted_Foliage'].get('alphaCutoff',.5)==.5
        assert all(m['doubleSided'] for m in mats.values())
        assert len(images)==2 and len(mats)==2
    return {'materials':list(mats),'images':images,'glb_sha256':hashlib.sha256(data).hexdigest()}

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('folder',type=Path);parser.add_argument('--repeat',type=Path)
    args=parser.parse_args();report={'passed':False,'variants':{}}
    for mode in ('original','folded','crossed'):
        row=inspect(args.folder/mode/'branch.glb')
        if args.repeat:
            other=inspect(args.repeat/mode/'branch.glb')
            assert row['glb_sha256']==other['glb_sha256'],mode+' no es idéntica'
            row['repeat_identical']=True
        report['variants'][mode]=row
    report['passed']=True;(args.folder/'export-verification.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2))
