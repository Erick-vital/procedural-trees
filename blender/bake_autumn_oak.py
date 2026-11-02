"""Proyectar la nueva pintura en las plantillas históricas, sin reajustar UV."""
import json
from pathlib import Path
import sys
import bpy

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT/'src'), str(ROOT/'blender')]
import oak_crossed_trial

if __name__ == '__main__':
    source, target = map(Path, sys.argv[sys.argv.index('--')+1:])
    assert bpy.app.version[:3] == (5, 2, 1)
    # Solo cambia el directorio de textura de esta ejecución aislada.
    oak_crossed_trial.ASSETS = source
    templates = json.loads((ROOT/'assets/roble-pintado/v0.3.0/templates.json').read_text())['templates']
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete(use_global=False)
    oak_crossed_trial.bake(templates, target)
