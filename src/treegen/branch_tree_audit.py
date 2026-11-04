"""Firmas exactas de atributos float32 en GLB ya validado estructuralmente."""
import json
from pathlib import Path
import struct


def raw_channels(path):
    raw=Path(path).read_bytes();size=struct.unpack_from('<I',raw,12)[0]
    doc=json.loads(raw[20:20+size]);binary=raw[28+size:]
    def read(index,width):
        a=doc['accessors'][index];view=doc['bufferViews'][a['bufferView']]
        fmt={5126:'f',5125:'I',5123:'H',5121:'B'}[a['componentType']]
        length=struct.calcsize('<'+fmt*width);stride=view.get('byteStride',length)
        start=view.get('byteOffset',0)+a.get('byteOffset',0)
        return [struct.unpack_from('<'+fmt*width,binary,start+i*stride) for i in range(a['count'])]
    result={}
    for p in doc['meshes'][0]['primitives']:
        name=doc['materials'][p['material']]['name'];attrs=p['attributes']
        positions=read(attrs['POSITION'],3);normals=read(attrs['NORMAL'],3);uv=read(attrs['TEXCOORD_0'],2)
        ids=[i[0] for i in read(p['indices'],1)]
        result.setdefault(name,[])
        for i in range(0,len(ids),3):
            result[name].append(tuple(sorted(positions[j]+normals[j]+uv[j] for j in ids[i:i+3])))
    return {k:sorted(v) for k,v in result.items()}
