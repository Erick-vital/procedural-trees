"""Cobertura proyectada de hojas frente a Q3, leyendo el GLB final."""
import json
from pathlib import Path
import struct

from PIL import Image, ImageChops, ImageDraw


def foliage_masks(path, cameras, resolution=256):
    if not 32 <= resolution <= 900 or len(cameras) > 16:
        raise ValueError('Raster de evaluación excesivo')
    raw = Path(path).read_bytes()
    size = struct.unpack_from('<I', raw, 12)[0]
    doc, binary = json.loads(raw[20:20+size]), raw[28+size:]
    def read(index, width):
        accessor = doc['accessors'][index]
        view = doc['bufferViews'][accessor['bufferView']]
        fmt = {5126: 'f', 5125: 'I', 5123: 'H', 5121: 'B'}[accessor['componentType']]
        stride = view.get('byteStride', struct.calcsize('<'+fmt*width))
        start = view.get('byteOffset', 0)+accessor.get('byteOffset', 0)
        return [struct.unpack_from('<'+fmt*width, binary, start+i*stride) for i in range(accessor['count'])]
    triangles = []
    for primitive in doc['meshes'][0]['primitives']:
        if doc['materials'][primitive['material']]['name'] not in ('Oak_Leaves', 'RF1_Leaf'):
            continue
        points = [(x, -z, y) for x, y, z in read(primitive['attributes']['POSITION'], 3)]
        indices = [row[0] for row in read(primitive['indices'], 1)]
        triangles.extend([[points[i] for i in indices[k:k+3]] for k in range(0, len(indices), 3)])
    result = {}
    for name, camera in cameras.items():
        mask = Image.new('1', (resolution, resolution))
        draw = ImageDraw.Draw(mask)
        axes = camera['basis_columns']
        def pixel(point):
            local = [x-y for x, y in zip(point, camera['location'])]
            x = sum(a*b for a, b in zip(local, axes[0]))/camera['ortho_scale']+.5
            y = .5-sum(a*b for a, b in zip(local, axes[1]))/camera['ortho_scale']
            return x*resolution, y*resolution
        for triangle in triangles:
            draw.polygon([pixel(p) for p in triangle], fill=1)
        result[name] = mask
    return result


def compare_masks(reference, candidate):
    def count(mask):
        return mask.width*mask.height-mask.convert('L').histogram()[0]
    result = {}
    for view, target in reference.items():
        actual = candidate[view]
        target_count = count(target)
        actual_count = count(actual)
        intersection = count(ImageChops.logical_and(target, actual))
        union = count(ImageChops.logical_or(target, actual))
        result[view] = {'reference_pixels': target_count, 'candidate_pixels': actual_count,
            'q3_coverage': intersection/max(1, target_count), 'outside_q3_pixels': actual_count-intersection,
            'iou': intersection/max(1, union)}
    return result
