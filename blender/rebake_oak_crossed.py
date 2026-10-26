"""Rehornear el atlas desde plantillas congeladas, sin resultados anteriores."""
import json
from pathlib import Path
import sys
import bpy
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'src'),str(ROOT/'blender')]
from oak_crossed_trial import bake
from foliage_lab import sha

if __name__=='__main__':
    target=Path(sys.argv[sys.argv.index('--')+1])
    templates=json.loads((ROOT/'assets/roble-pintado/v0.3.0/templates.json').read_text())['templates']
    bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
    bake(templates,target)
    # Blender escribe fecha/tiempo de render en PNG; la auditoría compara RGBA.
    print('Atlas rehorneado: '+sha(target))
