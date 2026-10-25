"""Validación independiente del GLB exportado y comparación de trabajos."""
import hashlib
import json
import math
from pathlib import Path
import struct
import html


def validate_glb(path, spec, *, triangle_limit=10000):
    if type(triangle_limit) is not int or not 1 <= triangle_limit <= 12500:
        raise ValueError('Límite de triángulos inválido')
    data = Path(path).read_bytes()
    if len(data) < 20 or struct.unpack_from('<4sII', data) != (b'glTF', 2, len(data)):
        raise ValueError('Cabecera GLB inválida')
    chunks, offset = {}, 12
    while offset < len(data):
        length, kind = struct.unpack_from('<II', data, offset)
        offset += 8
        if offset + length > len(data):
            raise ValueError('Chunk GLB truncado')
        chunks[kind] = data[offset:offset + length]
        offset += length
    doc = json.loads(chunks[0x4e4f534a])
    binary = chunks[0x004e4942]
    if len(doc.get('nodes', [])) != 1 or len(doc.get('meshes', [])) != 1:
        raise ValueError('Se requiere una única malla evaluada')
    node = doc['nodes'][0]
    if any(k in node for k in ('matrix', 'translation', 'rotation', 'scale')):
        raise ValueError('Transformación exportada inesperada; validar coordenadas locales no basta')
    def accessor(index, components, allowed):
        a = doc['accessors'][index]
        if a['type'] != components or a['componentType'] not in allowed or 'sparse' in a:
            raise ValueError('Accessor GLB no soportado')
        view = doc['bufferViews'][a['bufferView']]
        if view.get('buffer', 0) != 0:
            raise ValueError('Buffer externo no admitido')
        fmt = {5126: 'f', 5125: 'I', 5123: 'H', 5121: 'B'}[a['componentType']]
        width = 3 if components == 'VEC3' else 1
        size = struct.calcsize('<' + fmt * width)
        stride = view.get('byteStride', size)
        start = view.get('byteOffset', 0) + a.get('byteOffset', 0)
        end = start + (a['count'] - 1) * stride + size
        if a['count'] < 1 or stride < size or end > view.get('byteOffset', 0) + view['byteLength'] or end > len(binary):
            raise ValueError('Accessor fuera del buffer')
        return [struct.unpack_from('<' + fmt * width, binary, start + i * stride) for i in range(a['count'])]
    points, triangles, by_material = [], [], {}
    for primitive in doc['meshes'][0]['primitives']:
        if primitive.get('mode', 4) != 4:
            raise ValueError('Primitiva distinta de triángulos')
        vertices = accessor(primitive['attributes']['POSITION'], 'VEC3', {5126})
        indices = [i[0] for i in accessor(primitive['indices'], 'SCALAR', {5121, 5123, 5125})]
        if len(indices) % 3 or any(i >= len(vertices) for i in indices):
            raise ValueError('Índices inválidos')
        if not all(math.isfinite(c) for v in vertices for c in v):
            raise ValueError('Coordenadas no finitas')
        material = doc['materials'][primitive['material']]['name']
        by_material[material] = by_material.get(material, 0) + len(indices) // 3
        points.extend(vertices)
        for i in range(0, len(indices), 3):
            a, b, c = [vertices[k] for k in indices[i:i + 3]]
            u, v = [b[k] - a[k] for k in range(3)], [c[k] - a[k] for k in range(3)]
            cross = [u[1]*v[2]-u[2]*v[1], u[2]*v[0]-u[0]*v[2], u[0]*v[1]-u[1]*v[0]]
            if sum(x*x for x in cross) <= 4e-20:
                raise ValueError('Triángulo degenerado en GLB')
            triangles.append((material, sorted(tuple(round(x, 6) for x in p) for p in (a, b, c))))
    if not triangles or len(triangles) > triangle_limit or not 1 <= len(by_material) <= 3:
        raise ValueError('Presupuesto geométrico o materiales inválidos')
    bounds = [[fn(p[k] for p in points) for k in range(3)] for fn in (min, max)]
    dimensions = [bounds[1][k] - bounds[0][k] for k in range(3)]
    if min(dimensions) <= 0 or abs(dimensions[1] / spec['parameters']['height_m'] - 1) > .1:
        raise ValueError('Dimensiones o altura exportada inválidas')
    return {'triangles': len(triangles), 'materials': by_material, 'bounds_gltf': bounds,
            'dimensions_m': dimensions, 'geometry_sha256': hashlib.sha256(
                json.dumps(sorted(triangles), separators=(',', ':')).encode()).hexdigest(),
            'glb_sha256': hashlib.sha256(data).hexdigest()}


def validate_result(directory):
    directory = Path(directory)
    manifest = json.loads((directory / 'manifest.json').read_text())
    if manifest['status'] != 'completed':
        raise ValueError('Trabajo no completado')
    triangle_limit = 10000
    if manifest.get('kind') == 'blueprint':
        from .blueprints import resolve_blueprint
        stored = manifest['resolved_blueprint']
        resolved = resolve_blueprint(stored['blueprint_definition'], stored['instance_request'])
        if stored != resolved or manifest['spec'] != resolved['base_spec']:
            raise ValueError('Resolución de blueprint alterada o distinta de la especificación')
        if manifest['canopy_spec'] != resolved['canopy_spec'] or manifest['base_seeds'] != resolved['base_seeds']:
            raise ValueError('Entradas de generación distintas del blueprint resuelto')
        triangle_limit = resolved['limits']['triangles']
    report = validate_glb(directory / 'tree.glb', manifest['spec'], triangle_limit=triangle_limit)
    if manifest.get('kind') == 'blueprint':
        from .foliage_twigs_evaluation import inspect_twigs_glb
        roles = ({'wood_material': 'Pine_Bark', 'leaf_material': 'Pine_Needles'}
                 if resolved['base_spec']['algorithm'] == 'pine-whorls' else {})
        detailed = inspect_twigs_glb(directory / 'tree.glb', manifest['metrics'], triangle_limit=triangle_limit, **roles)
        if manifest.get('export_validation') and manifest['export_validation'] != detailed:
            raise ValueError('Firmas exportadas distintas de las registradas')
        report = detailed
    metrics = manifest['metrics']
    if report['triangles'] != metrics['triangles'] or report['materials'] != metrics['triangles_by_material']:
        raise ValueError('GLB distinto de la malla evaluada')
    low, high = metrics['bounds_blender']
    expected = [[low[0], low[2], -high[1]], [high[0], high[2], -low[1]]]
    if any(abs(a-b) > 1e-4 for row, exp in zip(report['bounds_gltf'], expected) for a,b in zip(row, exp)):
        raise ValueError('Escala/orientación distinta en GLB')
    if report['glb_sha256'] != manifest['glb_sha256']:
        raise ValueError('Hash GLB distinto del manifiesto')
    for name, digest in manifest.get('files_sha256', {}).items():
        if Path(name).name != name:
            raise ValueError('Ruta de artefacto inválida')
        p = directory / name
        if not p.is_file() or hashlib.sha256(p.read_bytes()).hexdigest() != digest:
            raise ValueError(f'Artefacto alterado o ausente: {name}')
    for view in manifest.get('required_views', []):
        p = directory / f'{view}.png'
        if not p.is_file() or p.read_bytes()[:8] != b'\x89PNG\r\n\x1a\n':
            raise ValueError(f'Vista ausente o inválida: {view}')
    return report


def compare(left, right, output):
    left, right, output = Path(left).resolve(), Path(right).resolve(), Path(output).resolve()
    a, b = [json.loads((p / 'manifest.json').read_text()) for p in (left, right)]
    va, vb = validate_result(left), validate_result(right)
    report = {'left': str(left), 'right': str(right), 'same_spec': a['spec_sha256'] == b['spec_sha256']
              and a.get('resolved_blueprint') == b.get('resolved_blueprint'),
              'same_environment': all(a.get(k) == b.get(k) for k in
                                      ('blender', 'blender_build', 'blender_python', 'runner_python', 'jsonschema_version')),
              'same_sources': a.get('sources_sha256') == b.get('sources_sha256'),
              'same_cameras': a.get('cameras') == b.get('cameras'),
              'same_geometry': va['geometry_sha256'] == vb['geometry_sha256'],
              'triangle_delta': vb['triangles'] - va['triangles'], 'metrics': [va, vb]}
    output.mkdir(parents=True, exist_ok=True)
    (output / 'comparison.json').write_text(json.dumps(report, indent=2) + '\n')
    import shutil
    rows = []
    for view in ('front', 'side', 'top', 'perspective'):
        cells = []
        for label, directory in (('left', left), ('right', right)):
            source = directory / f'{view}.png'
            if source.exists():
                target = f'{label}-{view}.png'
                shutil.copy2(source, output / target)
                cells.append(f'<td><img width="360" src="{target}" alt="{label} {view}"></td>')
            else:
                cells.append('<td>Vista no generada</td>')
        rows.append(f'<tr><th>{view}</th>{"".join(cells)}</tr>')
    (output / 'index.html').write_text('<!doctype html><meta charset="utf-8"><title>Comparación de robles</title>'
        '<h1>Comparación de robles</h1><pre>' + html.escape(json.dumps(report, indent=2)) + '</pre>'
        '<table><tr><th>Vista</th><th>Referencia</th><th>Candidato</th></tr>' + ''.join(rows) + '</table>')
    return report
