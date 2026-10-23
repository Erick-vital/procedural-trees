"""Comparación numérica de madera/copa Q1b→Q2 guardadas, sin regenerar assets."""
import argparse
import hashlib
import json
import math
from pathlib import Path
import sys
import bpy

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'blender'))
sys.path.insert(0, str(ROOT/'src'))
from generate_oak import evaluated_output
from treegen.crown import measure_crown


def read(folder):
    manifest = json.loads((folder/'manifest.json').read_text())
    bpy.ops.wm.open_mainfile(filepath=str(folder/'tree.blend'), load_ui=False)
    mesh = bpy.data.objects['Oak'].data
    mesh.calc_loop_triangles()
    crown = measure_crown([tuple(v.co) for v in mesh.vertices],
        [(mesh.materials[t.material_index].name, tuple(t.vertices)) for t in mesh.loop_triangles],
        manifest['spec']['parameters']['height_m'])
    return manifest, crown


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--base', type=Path, required=True)
    parser.add_argument('--candidate', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--cases', nargs='+', required=True)
    args = parser.parse_args(sys.argv[sys.argv.index('--')+1:])
    args.output.mkdir(parents=True, exist_ok=False)
    reports = {}
    for name in args.cases:
        base, before = read(args.base/name)
        candidate, after = read(args.candidate/name)
        assert candidate['crown_checks'] == after
        assert base['seeds'] == candidate['seeds']
        assert base['structure_checks'] == candidate['structure_checks']
        assert before['wood_xy_sha256'] == after['wood_xy_sha256'], 'Cambió madera en X/Y'
        height = candidate['spec']['parameters']['height_m']
        assert abs(after['wood_bounds_blender'][1][2] - after['wood_bounds_blender'][0][2] - height) < 1e-4
        leaf_bounds = after['leaf_bounds_blender']
        if leaf_bounds:
            assert leaf_bounds[0][2] >= -1e-5 and leaf_bounds[1][2] <= height+1e-5
        generator = next(g for g in bpy.data.node_groups if g.name.startswith('Oak_Generator_v'))
        # Graph wrapper mínimo para el helper de evaluación: usa el grupo guardado.
        class Wrapper:
            tree = generator
            sockets = {s.name:s.identifier for s in generator.interface.items_tree if s.item_type == 'SOCKET' and s.in_out == 'INPUT'}
        coords = {}
        for channel in ('Anchors', 'Centers'):
            mesh = evaluated_output(Wrapper(), candidate['socket_values'], channel)
            coords[channel] = [tuple(v.co) for v in mesh.vertices]
            bpy.data.meshes.remove(mesh)
        assert len(coords['Anchors']) == len(coords['Centers']) == after['leaf_mass_count']
        offsets = [math.dist(a,c) for a,c in zip(coords['Anchors'],coords['Centers'])]
        scale = min(candidate['spec']['parameters']['foliage_scale_m'], .24*height)
        assert max(offsets, default=0) <= scale+1e-4
        reports[name] = {'same_native_structure':True, 'same_wood_xy':True, 'base':before, 'candidate':after,
            'base_wood_height_m':before['wood_bounds_blender'][1][2]-before['wood_bounds_blender'][0][2],
            'max_anchor_center_distance_m':max(offsets, default=0),
            'effective_foliage_scale_m':scale,
            'base_manifest_sha256':hashlib.sha256((args.base/name/'manifest.json').read_bytes()).hexdigest(),
            'candidate_manifest_sha256':hashlib.sha256((args.candidate/name/'manifest.json').read_bytes()).hexdigest()}
        print(name+': madera X/Y idéntica y follaje dentro de altura', flush=True)
    (args.output/'report.json').write_text(json.dumps({'cases':reports, 'blender':bpy.app.version_string}, indent=2)+'\n')


if __name__ == '__main__':
    main()
