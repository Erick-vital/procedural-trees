"""B3: exporta solo la madera congelada para inspección, sin alterar resultados."""
import json
from pathlib import Path
import sys
import bpy

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / 'src'), str(ROOT / 'blender')]
from foliage_branch_lab import mesh_from
from generate_blueprint import apply_material
from generate_oak import mesh_report
from foliage_canopy_lab import export_tree
from foliage_lab import write

for item in json.loads(Path(sys.argv[sys.argv.index('--') + 1]).read_text()):
    source, output = Path(item['source']), Path(item['output'])
    output.mkdir(parents=True, exist_ok=False)
    ref = json.loads((source / 'base-reference.json').read_text())
    manifest = json.loads((source / 'manifest.json').read_text())
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete(use_global=False)
    for mat in list(bpy.data.materials):
        bpy.data.materials.remove(mat)
    mesh = mesh_from(ref['wood_mesh'], 'B3_WoodInspection')
    mesh.materials.append(apply_material('Oak_Bark', manifest['resolved_blueprint']['appearance']['bark']))
    obj = bpy.data.objects.new('B3_WoodInspection', mesh)
    bpy.context.collection.objects.link(obj)
    export_tree(obj, output)
    write(output / 'manifest.json', {'metrics': mesh_report(mesh), 'inspection_only': True,
          'source': str(source), 'wood_sha256': ref['wood_sha256']})
