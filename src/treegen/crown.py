"""Medidas de madera y masas de copa sobre una malla; sin dependencia de Blender."""
import hashlib
import json
import math


def measure_crown(vertices, triangles, height):
    """Los triángulos son pares (nombre de material, índices de vértices).

    Componentes topológicas de follaje: no confundir masas superpuestas con una
    unión geométrica ni esta ocupación de centros con volumen o silueta cubierta.
    """
    wood = [tuple(ids) for name,ids in triangles if name == 'Oak_Bark']
    leaves = [tuple(ids) for name,ids in triangles if name == 'Oak_Leaves']
    used = sorted({i for ids in wood for i in ids})
    if not used or not math.isfinite(height) or height <= 0:
        raise ValueError('Madera o altura inválida')

    def digest(axes):
        coords = {i:tuple(round(vertices[i][k], 6) for k in axes) for i in used}
        value = [sorted(coords.values()), sorted(sorted(coords[i] for i in ids) for ids in wood)]
        return hashlib.sha256(json.dumps(value).encode()).hexdigest()

    parents = {i:i for ids in leaves for i in ids}

    def find(i):
        while parents[i] != i:
            parents[i] = parents[parents[i]]
            i = parents[i]
        return i

    for ids in leaves:
        for i in ids[1:]:
            parents[find(i)] = find(ids[0])
    components = {}
    for i in parents:
        components.setdefault(find(i), []).append(i)
    centers = [[sum(vertices[i][k] for i in ids)/len(ids) for k in range(3)] for ids in components.values()]
    bounds = [[fn(vertices[i][k] for i in used) for k in range(3)] for fn in (min,max)]
    # Referencia horizontal: centro de la caja de madera, también en troncos curvos.
    center_xy = [(bounds[0][k]+bounds[1][k])/2 for k in (0,1)]
    sectors, bands = [0]*8, [0]*5
    for x,y,z in centers:
        sectors[int((math.atan2(y-center_xy[1], x-center_xy[0]) % (2*math.pi))/(2*math.pi)*8) % 8] += 1
        bands[max(0, min(4, int(z/height*5)))] += 1
    leaf_ids = sorted(parents)
    face_counts = {}
    for ids in leaves:
        root = find(ids[0])
        face_counts[root] = face_counts.get(root,0)+1
    triangle_histogram = {}
    for count in face_counts.values():
        triangle_histogram[str(count)] = triangle_histogram.get(str(count),0)+1
    sizes = [math.sqrt(sum((max(vertices[i][k] for i in ids)-min(vertices[i][k] for i in ids))**2 for k in range(3)))
             for ids in components.values()]
    mean = sum(sizes)/len(sizes) if sizes else 0
    size_stats = {'minimum_m':min(sizes,default=0), 'maximum_m':max(sizes,default=0), 'mean_m':mean,
                  'coefficient_of_variation':math.sqrt(sum((v-mean)**2 for v in sizes)/len(sizes))/mean if mean else 0}
    return {'wood_geometry_sha256':digest((0,1,2)), 'wood_xy_sha256':digest((0,1)),
            'wood_bounds_blender':bounds, 'wood_triangles':len(wood), 'leaf_triangles':len(leaves),
            'leaf_mass_count':len(centers), 'center_height_bins':bands, 'center_azimuth_sectors':sectors,
            'mass_bbox_diagonal':size_stats,
            'mass_triangle_histogram':triangle_histogram,
            'occupied_height_bins':sum(n > 0 for n in bands), 'occupied_azimuth_sectors':sum(n > 0 for n in sectors),
            'leaf_bounds_blender':[[fn(vertices[i][k] for i in leaf_ids) for k in range(3)] for fn in (min,max)] if leaf_ids else None}
