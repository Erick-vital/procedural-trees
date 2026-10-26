"""Auditoría independiente del GLB de tres láminas y su procedencia."""
from collections import Counter
import json
import math
from pathlib import Path
import struct
import hashlib
from .evaluation import validate_glb
from .oak_crossed_production import build
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
    require(not (main-actual),'Madera estructural o normales modificadas')
    kept_positions={tuple(sorted(position(t[0]['vertices'][j]) for j in face)) for t in wood[len(ref['branches']):] for face in t[0]['polygons']}
    kept_quantized={tuple(sorted(tuple(round(x,6) for x in p) for p in tri)) for tri in kept_positions}
    historical_kept=[t for t in historical['RF2_Twig'] if tuple(sorted(tuple(p[:3]) for p in t)) in kept_quantized]
    require(actual==main+Counter(historical_kept),'Soportes o normales distintos de los conservados')
    require(report['triangles']==old['metrics']['triangles']-8*(len(old['supports'])-len(kept))-6*len(old['supports']),'Conteo de cruzadas incorrecto')
    require(len(rows['Painted_Foliage'])==6*len(items),'No hay tres láminas por grupo')
    return {**report,'crossed_panels_valid':True,'wood_and_remaining_supports_exact':True,'source_distribution_exact':True,
        'groups':len(items),'panels':len(panels),'kept_supports':len(kept),'resource_sha256':resolved['resources'],
        'channel_sha256':{name:canonical_hash(sorted(value)) for name,value in normals.items()}}
