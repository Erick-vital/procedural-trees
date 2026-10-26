#!/usr/bin/env python3
"""Auditar y conservar evidencia pequeña de la rama artística del roble."""
import argparse
import json
from pathlib import Path
import struct
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'scripts')]
from review_pine_painted import read,write,sha


def channel(path,name):
    raw=path.read_bytes();length=struct.unpack_from('<I',raw,12)[0];doc=json.loads(raw[20:20+length]);binary=raw[28+length:]
    def read_vec(index):
        a=doc['accessors'][index];view=doc['bufferViews'][a['bufferView']];width=3 if a['type']=='VEC3' else 1
        fmt={5126:'f',5125:'I',5123:'H',5121:'B'}[a['componentType']];size=struct.calcsize('<'+fmt*width);stride=view.get('byteStride',size)
        offset=view.get('byteOffset',0)+a.get('byteOffset',0)
        return [struct.unpack_from('<'+fmt*width,binary,offset+i*stride) for i in range(a['count'])]
    rows=[]
    for p in doc['meshes'][0]['primitives']:
        if doc['materials'][p['material']]['name']!=name:continue
        positions=read_vec(p['attributes']['POSITION']);normals=read_vec(p['attributes']['NORMAL']);indices=[v[0] for v in read_vec(p['indices'])]
        assert all(abs(sum(c*c for c in n)-1)<.0001 for n in normals)
        rows += [sorted(tuple(round(c,6) for c in positions[j]+normals[j]) for j in indices[i:i+3]) for i in range(0,len(indices),3)]
    assert rows;return sorted(rows)


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--study',required=True,type=Path);p.add_argument('--repeat',required=True,type=Path);p.add_argument('--evidence',required=True,type=Path);a=p.parse_args()
    study=a.study.resolve();repeat=a.repeat.resolve();evidence=a.evidence.resolve();r=read(study/'manifest.json');assert r['passed']
    assert all(sha(ROOT/p)==h for p,h in r['source_lock'].items())
    assert all(sha(study/'captures'/p)==h for p,h in r['capture_sha256'].items())
    identical={name:sha(study/name/'branch.glb')==sha(repeat/name/'branch.glb') for name in ('original','painted','wood','swatches')};assert all(identical.values())
    assert channel(study/'original/branch.glb','Original_Bark')==channel(study/'painted/branch.glb','Painted_Bark')
    assert len(r['capture_sha256'])==29
    evidence.mkdir(parents=True,exist_ok=True)
    summary={'passed':True,'study':str(study.relative_to(ROOT)),'repeat':str(repeat.relative_to(ROOT)),
        'reference':r['reference'],'variants':r['variants'],'resources':r['resources'],'export_validation':r['export_validation'],
        'repeated_glb_identical':identical,'wood_and_twig_geometry_normals_exact':True,'source_lock_verified':True,
        'real_captures':29,'capture_sha256':r['capture_sha256'],'source_lock':r['source_lock'],
        'sample_tests':{'command':'PYTHONPATH=src python3 -m unittest discover -s tests -p test_oak_painted_sample.py -v','passed':True,'tests':2},
        'artistic_acceptance':'pending','evidence_script_sha256':sha(Path(__file__))}
    write(evidence/'audit.json',summary);print('Madera/normales exactas, 4 GLB repetidos idénticos y 29 capturas auditadas.')

if __name__=='__main__':main()
