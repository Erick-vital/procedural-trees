"""Ensayo aislado de madera: quitar soportes directos de la primaria."""
import json
import sys
from pathlib import Path
import bpy

ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'src'),str(ROOT/'blender')]
from treegen.oak_painted_sample import select,secondary_supports,wood_uv
from treegen.foliage_molds import connection_geometry
from oak_painted_sample import painted,save
from pine_painted_sample import create
from foliage_lab import write,sha


def main(source,out):
    ref=json.loads((source/'source/base-reference.json').read_text())
    manifest=json.loads((source/'source/manifest.json').read_text())
    wood,supports,_=select(ref,manifest)
    kept=secondary_supports(wood,supports)
    kept_ids={s['id'] for s in kept}
    bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
    for mat in list(bpy.data.materials):bpy.data.materials.remove(mat)
    bark=painted('Painted_Bark','bark.png')
    pieces=[(b['mesh'],0,wood_uv(b)) for b in wood]
    for s in kept:
        v,f=connection_geometry(s,manifest['canopy_spec'])
        uv=[[i%3/3,0 if i<3 else s['length_m']/1.4] for i in range(len(v))]
        pieces.append(({'vertices':v,'polygons':f},0,uv))
    obj=create('PaintedOakSample',pieces,[bark])
    for polygon,flag in zip(obj.data.polygons,[flag for b in wood for flag in b['mesh']['smooth']]):polygon.use_smooth=flag
    result=save(obj,out/'wood')
    write(out/'manifest.json',{'passed':True,'profile':'secondary-only-v1','scope':'Solo madera de muestra; no modifica hojas ni árbol completo.',
        'source':str(source.relative_to(ROOT)),'source_sha256':{name:sha(source/name) for name in ('source/base-reference.json','source/manifest.json','wood/branch.glb')},
        'kept_support_ids':[s['id'] for s in kept],'removed_support_ids':[s['id'] for s in supports if s['id'] not in kept_ids],
        'twig_spec':manifest['canopy_spec'],'wood_ids':[b['id'] for b in wood],'variants':{'wood':result},'blender':bpy.app.version_string})


if __name__=='__main__':
    args=sys.argv[sys.argv.index('--')+1:];main(Path(args[0]),Path(args[1]))
