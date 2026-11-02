"""Reimportar UV2 estacionales en Blender y reexportar una prueba de transporte."""
import json
from pathlib import Path
import sys
import bpy

def key(position, uv):
    return ','.join(str(round(x*10000)) for x in list(position)+list(uv))


def main(config_path):
    config = json.loads(config_path.read_text())
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete(use_global=False)
    bpy.ops.import_scene.gltf(filepath=config['glb'])
    expected = {r['key']: r for r in config['binding']}
    seen, triangles, error, vertices = set(), 0, 0.0, 0
    for obj in bpy.context.scene.objects:
        if obj.type != 'MESH':
            continue
        mesh = obj.data
        mesh.calc_loop_triangles()
        triangles += len(mesh.loop_triangles)
        for face in mesh.polygons:
            material = obj.material_slots[face.material_index].material
            if material.name.split('.')[0] != 'Painted_Foliage':
                continue
            if len(mesh.uv_layers) != 2:
                raise ValueError('Blender perdió el canal UV2')
            owners = set()
            for loop in face.loop_indices:
                v = obj.matrix_world @ mesh.vertices[mesh.loops[loop].vertex_index].co
                uv = mesh.uv_layers[0].data[loop].uv
                row = expected[key([v.x, v.z, -v.y], [uv.x, 1-uv.y])]
                actual = mesh.uv_layers[1].data[loop].uv
                delta = max(abs(actual.x-row['calendar'][0]), abs((1-actual.y)-row['calendar'][1]))
                if delta > .00001:
                    raise ValueError('Blender importó un calendario distinto')
                error = max(error, delta)
                owners.add(row['group_id'])
                seen.add(row['group_id'])
                vertices += 1
            if len(owners) != 1:
                raise ValueError('Blender mezcló grupos por cara')
    if len(seen) != config['group_count'] or triangles != config['triangles'] or triangles >= 7000:
        raise ValueError('Presupuesto/grupos importados distintos')
    bpy.ops.export_scene.gltf(filepath=config['roundtrip'], export_format='GLB',
                              export_texcoords=True, export_normals=True)
    Path(config['report']).write_text(json.dumps({'passed': True, 'blender': bpy.app.version_string,
        'triangles': triangles, 'groups': len(seen), 'checked_corners': vertices,
        'max_calendar_error': error, 'roundtrip': config['roundtrip']}, indent=2)+'\n')


if __name__ == '__main__':
    assert bpy.app.version[:3] == (5, 2, 1)
    main(Path(sys.argv[sys.argv.index('--')+1]))
