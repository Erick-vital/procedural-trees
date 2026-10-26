"""Validación PP4 del GLB autocontenido; la ruta histórica sigue siendo opaca."""
import hashlib
import io
import json
import math
from pathlib import Path
import struct
from PIL import Image
from .evaluation import validate_glb
from .blueprints import canonical_hash
from .pine_painted import build


def inspect_painted_glb(path, metrics, resolved):
    report=validate_glb(path,resolved['base_spec'],triangle_limit=resolved['limits']['triangles'])
    raw=Path(path).read_bytes();size=struct.unpack_from('<I',raw,12)[0]
    doc=json.loads(raw[20:20+size]);binary=raw[28+size:]
    def require(condition,message):
        if not condition:raise ValueError(message)
    def read(index,width):
        a=doc['accessors'][index];view=doc['bufferViews'][a['bufferView']]
        require(a['componentType'] in (5126,5125,5123,5121) and 'sparse' not in a,'Accessor inválido')
        require(a['type']=={1:'SCALAR',2:'VEC2',3:'VEC3'}[width],'Tipo de accessor inválido')
        fmt={5126:'f',5125:'I',5123:'H',5121:'B'}[a['componentType']]
        length=struct.calcsize('<'+fmt*width);stride=view.get('byteStride',length)
        start=view.get('byteOffset',0)+a.get('byteOffset',0)
        require(view.get('buffer',0)==0 and stride>=length and start+(a['count']-1)*stride+length<=min(len(binary),view.get('byteOffset',0)+view['byteLength']),'Accessor fuera de rango')
        return [struct.unpack_from('<'+fmt*width,binary,start+i*stride) for i in range(a['count'])]
    require(not any('uri' in b for b in doc['buffers']),'Buffer externo')
    require(len(doc.get('materials',[]))==2 and len(doc.get('images',[]))==2,'Recursos incompletos')
    images=[]
    for image in doc['images']:
        require('uri' not in image and image.get('mimeType')=='image/png','Imagen externa o no PNG')
        view=doc['bufferViews'][image['bufferView']];start=view.get('byteOffset',0)
        png=binary[start:start+view['byteLength']]
        im=Image.open(io.BytesIO(png));require(im.size==(1254,1254),'Resolución inesperada')
        images.append(hashlib.sha256(png).hexdigest())
    channels={};geometry={};uv_channels={}
    for p in doc['meshes'][0]['primitives']:
        m=doc['materials'][p['material']];name=m['name'];foliage=name=='Painted_Foliage'
        require(name in ('Painted_Bark','Painted_Foliage'),'Material desconocido')
        require(m.get('doubleSided') is True,'Reversos descartados')
        require(m.get('alphaMode','OPAQUE')==('MASK' if foliage else 'OPAQUE'),'Modo alfa incorrecto')
        require(not foliage or m.get('alphaCutoff',.5)==.5,'Umbral alterado')
        pbr=m['pbrMetallicRoughness'];require(abs(pbr.get('roughnessFactor',1)-.95)<1e-6 and pbr.get('metallicFactor',1)==0,'Rugosidad/metalicidad alterada')
        require(pbr.get('baseColorFactor',[1,1,1,1])==[1,1,1,1],'Tinte inesperado')
        texture=pbr['baseColorTexture'];require(texture.get('texCoord',0)==0,'Canal UV inesperado')
        image_index=doc['textures'][texture['index']]['source']
        require(images[image_index]==resolved['resources']['foliage' if foliage else 'bark']['sha256'],'Pintura embebida distinta de receta')
        positions=read(p['attributes']['POSITION'],3);normals=read(p['attributes']['NORMAL'],3);uv=read(p['attributes']['TEXCOORD_0'],2)
        require(len(positions)==len(normals)==len(uv),'Atributos incompletos')
        require(all(math.isfinite(v) for pair in uv for v in pair),'UV no finitas')
        require(not foliage or all(0<=v<=1 for pair in uv for v in pair),'UV de atlas fuera de rango')
        require(all(all(math.isfinite(v) for v in n) and abs(sum(v*v for v in n)-1)<.0001 for n in normals),'Normales inválidas')
        indices=[x[0] for x in read(p['indices'],1)]
        uv_rows=uv_channels.setdefault(name,[])
        rows=channels.setdefault(name,[]);geo=geometry.setdefault(name,[])
        for i in range(0,len(indices),3):
            ids=indices[i:i+3]
            uv_rows.append(sorted(tuple(positions[j]+uv[j]) for j in ids))
            a,b,c=[positions[j] for j in ids]
            u=[b[k]-a[k] for k in range(3)];v=[c[k]-a[k] for k in range(3)]
            face=[u[1]*v[2]-u[2]*v[1],u[2]*v[0]-u[0]*v[2],u[0]*v[1]-u[1]*v[0]]
            require(all(sum(x*y for x,y in zip(face,normals[j]))>0 for j in ids),'Normal invertida')
            rows.append(sorted(tuple(round(v,6) for v in positions[j]+normals[j]) for j in ids))
            geo.append(sorted(tuple(v for v in positions[j]) for j in ids))
    # Los triángulos exportados han de ser exactamente los grupos anclados y la madera retenida.
    branches,wood,groups=build(resolved)
    def f32(v):return struct.unpack('<f',struct.pack('<f',v))[0]
    expected={}
    for name,pieces in [('Painted_Bark',[b['mesh'] for b in wood]),('Painted_Foliage',groups)]:
        expected[name]=[sorted(tuple(f32(v) for v in (mesh['vertices'][j][0],mesh['vertices'][j][2],-mesh['vertices'][j][1])) for j in face) for mesh in pieces for face in mesh['polygons']]
        require(sorted(expected[name])==sorted(geometry.get(name,[])),'Geometría exportada distinta de recorridos/anclajes')
    expected_uv=[sorted(tuple([f32(g['vertices'][j][0]),f32(g['vertices'][j][2]),f32(-g['vertices'][j][1]),f32(g['uv'][j][0]),f32(1-f32(g['uv'][j][1]))]) for j in face) for g in groups for face in g['polygons']]
    require(sorted(expected_uv)==sorted(uv_channels['Painted_Foliage']),'UV exportadas distintas del atlas planificado')
    require(report['triangles']==metrics['triangles'] and report['materials']==metrics['triangles_by_material'],'Conteos alterados')
    require(abs(report['dimensions_m'][1]-12)<.0001 and report['triangles']<11924,'Altura o reducción PP4 inválida')
    return {**report,'channel_sha256':{n:canonical_hash(sorted(rows)) for n,rows in channels.items()},
            'uv_sha256':{n:canonical_hash(sorted(rows)) for n,rows in uv_channels.items()},
            'embedded_images_sha256':images,'normals_valid':True,'uv_valid':True,
            'exported_anchors_and_groups_valid':True,'group_count':len(groups)}
