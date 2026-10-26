"""Referencia de seis hojas pintadas con la misma madera de la receta cruzada."""
import json
from pathlib import Path
import sys
import bpy
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'src'),str(ROOT/'blender')]
from treegen.oak_painted_tree import build
from oak_painted_sample import painted,save,ASSETS
from pine_painted_sample import create
from foliage_lab import write

if __name__=='__main__':
    folder=Path(sys.argv[sys.argv.index('--')+1]);ref=json.loads((folder/'base-reference.json').read_text());old=json.loads((folder/'reference/manifest.json').read_text())
    atlas=json.loads((ASSETS/'manifest.json').read_text());parts,_,_=build(ref,old,atlas,2718)
    bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
    for mat in list(bpy.data.materials):bpy.data.materials.remove(mat)
    obj=create('PaintedOakTreePilot',parts['painted'],[painted('Painted_Bark','bark.png'),painted('Painted_Foliage','foliage.png',True)])
    for polygon,flag in zip(obj.data.polygons,[f for b in ref['branches'] for f in b['mesh']['smooth']]):polygon.use_smooth=flag
    result=save(obj,folder/'baseline');write(folder/'baseline/metrics.json',result['metrics'])
