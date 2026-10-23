"""Capturas con cámaras fijadas desde alturas Q3 y exportación común por edad."""
import argparse
import json
from pathlib import Path
import sys

import bpy
import bmesh

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT/'src'), str(ROOT/'blender')]
from foliage_lab import configure, render, rig, sha, write
from generate_oak import mesh_report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--models', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args(sys.argv[sys.argv.index('--')+1:])
    args.output = args.output.resolve()
    args.output.mkdir(parents=True, exist_ok=False)
    configs = json.loads(args.models.read_text())
    all_cameras = {}
    for age, height in [('adulto', 10), ('viejo', 9)]:
        cameras = rig([0, 0, height/2], 2*height/1.3)
        # Se establecen antes de leer ningún candidato, a partir de la altura
        # de referencia y origen común. No se adapta la caja a cada árbol.
        all_cameras[age] = cameras
    for item in configs:
        source = Path(item['folder'])
        original_files = {name: sha(source/name) for name in ('tree.blend', 'manifest.json')}
        m = json.loads((source/'manifest.json').read_text())
        bpy.ops.wm.open_mainfile(filepath=str(source/'tree.blend'), load_ui=False)
        obj = bpy.data.objects['Oak' if item['engine'] == 'q3' else 'ComparisonTree']
        obj.data = obj.data.copy()
        # La copia de presentación Q3 recibe el mismo facetado que los addons;
        # los archivos y el sombreado de la referencia original no se escriben.
        changed_shading = sum(p.use_smooth for p in obj.data.polygons)
        for face in obj.data.polygons:
            face.use_smooth = False
        obj.hide_set(False)
        for other in bpy.data.objects:
            if other != obj and other.type in ('CURVE', 'MESH'):
                other.hide_render = True
                other.hide_set(True)
        folder = args.output/item['id']
        folder.mkdir()
        cameras = all_cameras[item['age']]
        projected_heights = render(obj, folder, cameras)
        # Vista solo madera para distinguir distribución de follaje y estructura.
        mesh = obj.data.copy()
        bm = bmesh.new()
        bm.from_mesh(mesh)
        bmesh.ops.delete(bm, geom=[f for f in bm.faces if mesh.materials[f.material_index].name == 'Oak_Leaves'], context='FACES')
        bm.to_mesh(mesh)
        bm.free()
        wood = bpy.data.objects.new('ComparisonWoodOnly', mesh)
        bpy.context.collection.objects.link(wood)
        render(wood, folder/'wood-only', {'perspective': cameras['perspective']})
        bpy.data.objects.remove(wood, do_unlink=True)
        obj.hide_render = False
        configure()
        bpy.ops.object.select_all(action='DESELECT')
        obj.select_set(True)
        bpy.context.view_layer.objects.active = obj
        bpy.ops.export_scene.gltf(filepath=str(folder/'tree.glb'), export_format='GLB', use_selection=True, export_yup=True)
        bpy.ops.wm.save_as_mainfile(filepath=str(folder/'tree.blend'))
        metrics = mesh_report(obj.data) if m['metrics']['triangles'] <= 10000 else m['metrics']
        report = {'id': item['id'], 'engine': item['engine'], 'age': item['age'],
            'metrics': metrics, 'source_folder': str(source.resolve()), 'source_files_sha256': original_files,
            'presentation_smooth_faces_flattened': changed_shading,
            'projected_height_fractions': projected_heights,
            'cameras': cameras, 'original_manifest': m,
            'files_sha256': {n: sha(folder/n) for n in ('tree.blend', 'tree.glb')}}
        write(folder/'manifest.json', report)
        write(folder/'cameras.json', cameras)
        assert original_files == {name: sha(source/name) for name in original_files}
        print(item['id']+': capturado y exportado con cámaras compartidas', flush=True)
    write(args.output/'cameras.json', all_cameras)


if __name__ == '__main__':
    main()
