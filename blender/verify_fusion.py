"""Verificación independiente de las mallas guardadas del ensayo de fusión."""
import argparse
import json
from pathlib import Path
import sys

import bpy

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'blender'))
from experiment_fusion import crown, wood_surface_hash, sha
from generate_oak import mesh_report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--study', type=Path, required=True)
    parser.add_argument('--base', type=Path, required=True)
    args = parser.parse_args(sys.argv[sys.argv.index('--')+1:])
    reports = {}
    for case in json.loads((args.study/'summary.json').read_text()):
        folder = args.study/case
        lock = json.loads((folder/'reference-lock.json').read_text())
        original = json.loads((args.base/case/'manifest.json').read_text())
        assert lock['source_files_sha256'] == {n: sha(args.base/case/n) for n in lock['source_files_sha256']}
        bpy.ops.wm.open_mainfile(filepath=str(args.base/case/'tree.blend'), load_ui=False)
        before = bpy.data.objects['Oak'].data
        surface = wood_surface_hash(before)
        # Huella geométrica + atributos de las masas guardadas, independiente de
        # los contadores del informe: demuestra que se conserva la entrada Q3.
        def input_hash(mesh):
            import hashlib
            attributes = {a.name: [list(d.vector) if hasattr(d, 'vector') else d.value for d in a.data]
                          for a in mesh.attributes if a.name.startswith('q3_')}
            payload = {'geometry': mesh_report(mesh)['geometry_sha256'], 'attributes': attributes}
            return hashlib.sha256(json.dumps(payload, sort_keys=True).encode()).hexdigest()
        input_sha = input_hash(before)
        before_name = before.name
        bpy.ops.wm.open_mainfile(filepath=str(folder/'candidate/tree.blend'), load_ui=False)
        after = bpy.data.objects['Oak'].data
        manifest = json.loads((folder/'candidate/manifest.json').read_text())
        assert mesh_report(after) == manifest['metrics']
        assert crown(after, original['spec']['parameters']['height_m']) == manifest['crown_checks']
        assert wood_surface_hash(after) == surface
        assert input_hash(bpy.data.meshes[before_name]) == input_sha, 'La entrada Q3 guardada cambió'
        assert manifest['spec'] == original['spec'] and manifest['seeds'] == original['seeds']
        assert manifest['normalization'] == original['normalization']
        assert manifest['structure_checks'] == original['structure_checks']
        assert manifest['cameras'] == lock['cameras']
        reports[case] = {'saved_mesh_matches_manifest': True, 'wood_surface_unchanged': True,
                         'input_q3_mesh_and_attributes_unchanged': True, 'input_sha256': input_sha,
                         'parameters_seeds_normalization_structure_unchanged': True,
                         'source_files_unchanged': True, 'frozen_cameras_match': True}
    (args.study/'saved-mesh-verification.json').write_text(json.dumps(reports, indent=2)+'\n')
    print('Mallas guardadas: madera, entrada Q3 completa, parámetros y cámaras conservados', flush=True)


if __name__ == '__main__':
    main()
