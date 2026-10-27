"""Exportar el canal de madera para revisión; no modifica el GLB de producción."""
import json
from pathlib import Path
import sys
import bpy
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'src'),str(ROOT/'blender')]
from treegen.oak_crossed_production import build
from oak_painted_sample import painted,save
from pine_painted_sample import create
from foliage_lab import write


def main(folder):
    ref=json.loads((folder/'base-reference.json').read_text())
    old=json.loads((folder/'reference/manifest.json').read_text())
    resolved=json.loads((folder/'manifest.json').read_text())['resolved_blueprint']
    wood,_,_,_,_=build(ref,old,resolved)
    bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
    for mat in list(bpy.data.materials):bpy.data.materials.remove(mat)
    obj=create('PaintedOakWood',wood,[painted('Painted_Bark','bark.png')])
    flags=[f for mesh,_,_ in wood for f in mesh.get('smooth',[False]*len(mesh['polygons']))]
    for polygon,flag in zip(obj.data.polygons,flags):polygon.use_smooth=flag
    result=save(obj,folder/'wood');write(folder/'wood/metrics.json',result['metrics'])


if __name__=='__main__':
    for folder in sys.argv[sys.argv.index('--')+1:]:main(Path(folder))
