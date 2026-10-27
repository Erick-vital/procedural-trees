"""Auditoría independiente del GLB de tres láminas y su procedencia."""
from collections import Counter
import json
import math
from pathlib import Path
import struct
import hashlib
from itertools import combinations
from .evaluation import validate_glb
from .oak_crossed_production import build,optimized_wood,wood_model
from .pine_painted_sample import canonical_hash


def channels(path):
    raw=Path(path).read_bytes();size=struct.unpack_from('<I',raw,12)[0];doc=json.loads(raw[20:20+size]);binary=raw[28+size:]
    def read(index,width):
        a=doc['accessors'][index];view=doc['bufferViews'][a['bufferView']]
        if a['type']!={1:'SCALAR',2:'VEC2',3:'VEC3'}[width] or 'sparse' in a:raise ValueError('Accessor no soportado')
        fmt={5126:'f',5125:'I',5123:'H',5121:'B'}[a['componentType']];length=struct.calcsize('<'+fmt*width);stride=view.get('byteStride',length)
        start=view.get('byteOffset',0)+a.get('byteOffset',0)
        if a['count']<1 or stride<length or start+(a['count']-1)*stride+length>min(len(binary),view.get('byteOffset',0)+view['byteLength']):raise ValueError('Accessor fuera de rango')
        return [struct.unpack_from('<'+fmt*width,binary,start+i*stride) for i in range(a['count'])]
    rows={};normals={};images=[]
    if any('uri' in b for b in doc['buffers']):raise ValueError('Buffer externo')
    for image in doc.get('images',[]):
        if 'uri' in image or image['mimeType']!='image/png':raise ValueError('Imagen externa o tipo inválido')
        view=doc['bufferViews'][image['bufferView']];start=view.get('byteOffset',0)
        images.append(hashlib.sha256(binary[start:start+view['byteLength']]).hexdigest())
    for p in doc['meshes'][0]['primitives']:
        name=doc['materials'][p['material']]['name'];v=read(p['attributes']['POSITION'],3);n=read(p['attributes']['NORMAL'],3)
        uv=read(p['attributes']['TEXCOORD_0'],2) if 'TEXCOORD_0' in p['attributes'] else [(0,0)]*len(v)
        if len(n)!=len(v) or len(uv)!=len(v) or not all(math.isfinite(x) for row in uv for x in row):raise ValueError('UV inválidas')
        if not all(abs(sum(x*x for x in normal)-1)<.0001 for normal in n):raise ValueError('Normales inválidas')
        ids=[i[0] for i in read(p['indices'],1)]
        rows.setdefault(name,[]);normals.setdefault(name,[])
        for i in range(0,len(ids),3):
            tri=ids[i:i+3]
            rows[name].append(tuple(sorted(tuple(v[j]+uv[j]) for j in tri)))
            normals[name].append(tuple(sorted(tuple(round(x,6) for x in v[j]+n[j]) for j in tri)))
    return doc,rows,normals,images


def validate_wood_faces(rows,wood):
    """Contrastar caras/UV permitiendo las diagonales que elija Blender al triangular."""
    def f32(x):return struct.unpack('<f',struct.pack('<f',x))[0]
    remaining=Counter(rows)
    for mesh,_,uv in wood:
        for face in mesh['polygons']:
            seam=max(uv[j][0] for j in face)-min(uv[j][0] for j in face)>.5
            corners=[]
            for j in face:
                v=mesh['vertices'][j];u=1 if seam and uv[j][0]==0 else uv[j][0]
                corners.append((f32(v[0]),f32(v[2]),f32(-v[1]),f32(u),f32(1-f32(uv[j][1]))))
            triangles=[tuple(sorted(t)) for t in combinations(corners,3) if remaining[tuple(sorted(t))]]
            if len(triangles)!=len(face)-2 or any(remaining[t]!=1 for t in triangles):
                raise ValueError('Caras o UV de madera selectiva distintas')
            edges=Counter(tuple(sorted(edge)) for t in triangles for edge in combinations(t,2))
            boundary=Counter(tuple(sorted((corners[i],corners[(i+1)%len(corners)]))) for i in range(len(corners)))
            if Counter({e:1 for e,n in edges.items() if n==1})!=boundary or any(n>2 for n in edges.values()):
                raise ValueError('Triangulación de madera inválida')
            remaining.subtract(triangles)
    if +remaining:raise ValueError('Triángulos de madera adicionales')


def inspect_crossed(path,manifest,resolved):
    path=Path(path);report=validate_glb(path,resolved['base_spec'],triangle_limit=resolved['limits']['triangles'],height_materials={'Painted_Bark'})
    doc,rows,normals,images=channels(path)
    def require(ok,message):
        if not ok:raise ValueError(message)
    require(set(rows)=={'Painted_Bark','Painted_Foliage'} and len(doc['materials'])==2,'Materiales inesperados')
    require(set(images)=={resolved['resources'][k]['sha256'] for k in ('foliage','bark')} and len(images)==2,'Texturas embebidas distintas')
    for mat in doc['materials']:
        leaf=mat['name']=='Painted_Foliage';pbr=mat['pbrMetallicRoughness']
        require(mat.get('doubleSided') is True and mat.get('alphaMode','OPAQUE')==('MASK' if leaf else 'OPAQUE'),'Transparencia o reversos inválidos')
        require(not leaf or mat.get('alphaCutoff',.5)==.5,'Umbral alfa incorrecto')
        require(abs(pbr.get('roughnessFactor',1)-.95)<1e-6 and pbr.get('metallicFactor',1)==0,'Material alterado')
        require(pbr.get('baseColorFactor',[1,1,1,1])==[1,1,1,1] and 'baseColorTexture' in pbr,'Pintura o tinte alterados')
        texture=pbr['baseColorTexture'];image=doc['textures'][texture['index']]['source']
        require(texture.get('texCoord',0)==0 and images[image]==resolved['resources']['foliage' if leaf else 'bark']['sha256'],'Canal de textura incorrecto')
    old=json.loads((path.parent/'reference/manifest.json').read_text());ref=json.loads((path.parent/'base-reference.json').read_text())
    wood,panels,items,assignments,kept=build(ref,old,resolved)
    def f32(x):return struct.unpack('<f',struct.pack('<f',x))[0]
    def position(v):return (f32(v[0]),f32(v[2]),f32(-v[1]))
    expected=[tuple(sorted(position(p['vertices'][j])+(f32(p['uv'][j][0]),f32(1-f32(p['uv'][j][1]))) for j in face)) for p in panels for face in p['polygons']]
    require(sorted(expected)==sorted(rows['Painted_Foliage']),'Posiciones/UV de cruzadas distintas')
    require(manifest['assignments']==assignments and manifest['card_placements_sha256']==canonical_hash(panels),'Asignaciones o tarjetas alteradas')
    require(manifest['placements']==old['placements'] and manifest['supports']==old['supports'],'Distribución histórica alterada')
    require(manifest['kept_support_ids']==[s['id'] for s in kept],'Selección de soportes alterada')
    _,_,historical,_=channels(path.parent/'reference/tree.glb')
    main=Counter(historical['Oak_Bark']);actual=Counter(normals['Painted_Bark'])
    optimized=optimized_wood(resolved)
    if optimized:
        validate_wood_faces(rows['Painted_Bark'],wood)
        parents={b['id']:b['parent_id'] for b in ref['branches']}
        major=[b for b in ref['branches'] if b['parent_id'] is None or parents[b['parent_id']] is None]
        vertices={tuple(round(x,6) for x in position(v)) for b in major for v in b['mesh']['vertices']}
        main=Counter(t for t in historical['Oak_Bark'] if all(tuple(p[:3]) in vertices for p in t))
        require(sum(main.values())==sum(len(f)-2 for b in major for f in b['mesh']['polygons']),'Referencia de tronco/primarias incompleta')
        _,branches=wood_model(ref,wood,resolved)
        require(manifest['wood_optimization']==[dict(id=b['id'],**b['optimization']) for b in branches],'Registro de simplificación distinto')
    require(not (main-actual),'Madera conservada o normales modificadas')
    kept_positions={tuple(sorted(position(t[0]['vertices'][j]) for j in face)) for t in wood[len(ref['branches']):] for face in t[0]['polygons']}
    kept_quantized={tuple(sorted(tuple(round(x,6) for x in p) for p in tri)) for tri in kept_positions}
    historical_kept=[t for t in historical['RF2_Twig'] if tuple(sorted(tuple(p[:3]) for p in t)) in kept_quantized]
    if optimized:
        require(not (Counter(historical_kept)-actual),'Soportes o normales modificados')
    else:require(actual==main+Counter(historical_kept),'Soportes o normales distintos de los conservados')
    require(report['triangles']==sum(len(f)-2 for mesh,_,_ in wood for f in mesh['polygons'])+6*len(items),'Conteo de cruzadas incorrecto')
    require(len(rows['Painted_Foliage'])==6*len(items),'No hay tres láminas por grupo')
    result={**report,'crossed_panels_valid':True,'wood_and_remaining_supports_exact':not optimized,'source_distribution_exact':True,
        'groups':len(items),'panels':len(panels),'kept_supports':len(kept),'resource_sha256':resolved['resources'],
        'channel_sha256':{name:canonical_hash(sorted(value)) for name,value in normals.items()}}
    if optimized:result.update(selective_wood_valid=True,trunk_primary_remaining_supports_exact=True,
        wood_optimization_version='oak-wood-rings-0.1.0',wood_tolerance_m=.02)
    return result
