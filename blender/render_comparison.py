"""Capturas de pares guardados con encuadre común, sin alterar los assets."""
import argparse
import hashlib
import json
from pathlib import Path
import sys
import bpy
import bmesh

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'blender'))
from generate_oak import render_views


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--base', type=Path, required=True)
    parser.add_argument('--candidate', type=Path, required=True)
    parser.add_argument('--reference', type=Path, help='Segunda referencia opcional, con el mismo encuadre')
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--cases', nargs='+', required=True)
    parser.add_argument('--below', action='store_true', help='Añadir vistas inferiores para revisar huecos y madera visible')
    args = parser.parse_args(sys.argv[sys.argv.index('--')+1:])
    args.output.mkdir(parents=True, exist_ok=False)
    for case in args.cases:
        labels = ['base', 'reference', 'candidate'] if args.reference else ['base', 'candidate']
        inputs = ([args.base/case, args.reference/case, args.candidate/case] if args.reference
                  else [args.base/case, args.candidate/case])
        manifests = [json.loads((p/'manifest.json').read_text()) for p in inputs]
        bounds = [m['metrics']['bounds_blender'] for m in manifests]
        low = [min(b[0][k] for b in bounds) for k in range(3)]
        high = [max(b[1][k] for b in bounds) for k in range(3)]
        framing = {'center': [(a+b)/2 for a,b in zip(low, high)],
                   'span': max(b-a for a,b in zip(low, high))}
        cameras = []
        for label, folder in zip(labels, inputs):
            folder = folder.resolve()
            digest = hashlib.sha256((folder/'tree.blend').read_bytes()).hexdigest()
            bpy.ops.wm.open_mainfile(filepath=str(folder/'tree.blend'), load_ui=False)
            obj = bpy.data.objects['Oak']
            for other in bpy.data.objects:
                if other.type == 'MESH':
                    other.hide_render = other != obj
            output = args.output/case/label
            output.mkdir(parents=True)
            rig = render_views(obj, output, framing=framing)
            if args.below:
                rig.update(render_views(obj, output, [('below',(1.3,-1.8,-.65)),
                    ('below-front',(0,-1,-.55))], framing=framing))
            mesh = obj.data.copy()
            bm = bmesh.new()
            bm.from_mesh(mesh)
            bmesh.ops.delete(bm, geom=[f for f in bm.faces if mesh.materials[f.material_index].name == 'Oak_Leaves'], context='FACES')
            bm.to_mesh(mesh)
            bm.free()
            branches = bpy.data.objects.new('ComparisonBranches', mesh)
            bpy.context.collection.objects.link(branches)
            obj.hide_render = True
            rig.update(render_views(branches, output, [('branches',(1.3,-1.8,.65)),
                    ('branches-front',(0,-1,0)), ('branches-side',(1,0,0)), ('branches-top',(0,0,1))], framing=framing))
            if args.below:
                rig.update(render_views(branches, output, [('branches-below',(1.3,-1.8,-.65))], framing=framing))
            cameras.append(rig)
            assert hashlib.sha256((folder/'tree.blend').read_bytes()).hexdigest() == digest
        assert all(rig == cameras[0] for rig in cameras), 'Cámaras diferentes entre referencia y candidato'
        (args.output/case/'cameras.json').write_text(json.dumps({'same_cameras':True, 'framing':framing,
            'cameras':cameras[0], 'inputs':{label:{'folder':str(folder.resolve()),'spec':m['spec'],
            'geometry_sha256':m['metrics']['geometry_sha256']} for label,folder,m in zip(labels,inputs,manifests)}},indent=2)+'\n')


if __name__ == '__main__':
    main()
