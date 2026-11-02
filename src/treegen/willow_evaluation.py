"""Auditoría del GLB de sauce: geometría, UV, imágenes y procedencia."""
import struct

from .evaluation import validate_glb
from .oak_crossed_evaluation import channels, validate_wood_faces
from .blueprints import canonical_hash
from .willow import build


def inspect_willow(path, manifest, resolved):
    report = validate_glb(path, resolved['base_spec'], triangle_limit=resolved['limits']['triangles'], height_materials={'Painted_Bark'})
    doc, rows, normals, images = channels(path)

    def require(ok, message):
        if not ok:
            raise ValueError(message)

    require(set(rows) == {'Painted_Bark', 'Painted_Foliage'} and len(doc['materials']) == 2, 'Materiales de sauce inválidos')
    require(set(images) == {resolved['resources'][role]['sha256'] for role in ('bark', 'foliage')} and len(images) == 2, 'Pintura embebida alterada')
    for mat in doc['materials']:
        leaf = mat['name'] == 'Painted_Foliage'
        pbr = mat['pbrMetallicRoughness']
        require(mat.get('doubleSided') is True and mat.get('alphaMode', 'OPAQUE') == ('MASK' if leaf else 'OPAQUE'), 'Transparencia o reversos inválidos')
        require(not leaf or mat.get('alphaCutoff', .5) == .5, 'Umbral alfa incorrecto')
        require(abs(pbr.get('roughnessFactor', 1)-.95) < 1e-6 and pbr.get('metallicFactor', 1) == 0, 'Material alterado')
        require(pbr.get('baseColorFactor', [1, 1, 1, 1]) == [1, 1, 1, 1], 'Tinte alterado')
        texture = pbr['baseColorTexture']
        image = doc['textures'][texture['index']]['source']
        require(texture.get('texCoord', 0) == 0 and images[image] == resolved['resources']['foliage' if leaf else 'bark']['sha256'], 'Imagen asignada a canal incorrecto')
    branches, wood, groups = build(resolved)
    validate_wood_faces(rows['Painted_Bark'], [(b['mesh'], 0, b['uv']) for b in wood])

    def f32(value):
        return struct.unpack('<f', struct.pack('<f', value))[0]

    expected = []
    for group in groups:
        for face in group['polygons']:
            expected.append(tuple(sorted((f32(group['vertices'][i][0]), f32(group['vertices'][i][2]), f32(-group['vertices'][i][1]),
                                         f32(group['uv'][i][0]), f32(1-f32(group['uv'][i][1]))) for i in face)))
    require(sorted(expected) == sorted(rows['Painted_Foliage']), 'Cruzadas o UV distintas de los anclajes planificados')
    require(manifest['placements_sha256'] == canonical_hash(groups), 'Distribución registrada alterada')
    require(manifest['wood_sha256'] == canonical_hash([b['mesh'] for b in wood]), 'Madera registrada alterada')
    require(report['triangles'] == manifest['metrics']['triangles'] <= resolved['budget_upper_bound']['triangles_max'] < 7000, 'Conteo o presupuesto inválido')
    wood_y = [vertex[1] for face in rows['Painted_Bark'] for vertex in face]
    wood_height = max(wood_y)-min(wood_y)
    require(abs(wood_height-resolved['parameters']['base']['height_m']) < .0001, 'Altura de sauce alterada')
    return {**report, 'exported_anchors_and_groups_valid': True, 'wood_faces_and_uv_valid': True,
            'groups': len(groups), 'planes': len(groups)*3, 'normals_unit': True, 'wood_height_m': wood_height,
            'channel_sha256': {name: canonical_hash(sorted(value)) for name, value in normals.items()},
            'embedded_images_sha256': images}
