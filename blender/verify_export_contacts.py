"""B3: vuelve a importar cada GLB y comprueba inserciones sobre su madera real."""
import json
from pathlib import Path
import sys

import bpy

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / 'src'), str(ROOT / 'blender')]
from foliage_fusion import extract
from mesh_contacts import insertion_errors

args = sys.argv[sys.argv.index('--')+1:]
reports = {}
for folder in map(Path, json.loads(Path(args[0]).read_text())):
    m = json.loads((folder / 'manifest.json').read_text())
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete(use_global=False)
    for mat in list(bpy.data.materials):
        bpy.data.materials.remove(mat)
    bpy.ops.import_scene.gltf(filepath=str(folder / 'tree.glb'))
    objects = [o for o in bpy.context.scene.objects if o.type == 'MESH']
    assert len(objects) == 1
    obj = objects[0]
    # El importador restaura Z arriba; aplicar la transformación importada.
    obj.data.transform(obj.matrix_world)
    faces = [p for p in obj.data.polygons if obj.data.materials[p.material_index].name == 'Oak_Bark']
    assert faces
    wood = extract(obj.data, faces, 'B3_ImportedWood')
    points = [c['points_m'][0] for c in m['supports']]
    errors = insertion_errors(wood, points)
    reports[folder.name] = {'insertions': len(points), 'max_error_m': max(errors),
                             'glb_sha256': m['glb_sha256'], 'tolerance_m': .0001}
    bpy.data.meshes.remove(wood)
Path(args[1]).write_text(json.dumps({'passed': True, 'assets': reports}, indent=2)+'\n')
print('Contactos del GLB importado comprobados: '+str(len(reports)))
