"""Auditoría GLB del roble: textura, planos/UV, madera y ramillas históricas."""
import hashlib
import json
import math
from pathlib import Path
import struct
from .evaluation import validate_glb
from .oak_painted import build
from .pine_painted_sample import canonical_hash
from .foliage_twigs_evaluation import inspect_twigs_glb


def inspect_oak(path,manifest,resolved):
    report=validate_glb(path,resolved['base_spec'],triangle_limit=resolved['limits']['triangles'])
    raw=Path(path).read_bytes();size=struct.unpack_from('<I',raw,12)[0];doc=json.loads(raw[20:20+size]);binary=raw[28+size:]
    def require(ok,message):
        if not ok:raise ValueError(message)
    def read(index,width):
        a=doc['accessors'][index];v=doc['bufferViews'][a['bufferView']]
        require(a['type']=={1:'SCALAR',2:'VEC2',3:'VEC3'}[width] and 'sparse' not in a,'Accessor no soportado')
        fmt={5126:'f',5125:'I',5123:'H',5121:'B'}[a['componentType']];length=struct.calcsize('<'+fmt*width);stride=v.get('byteStride',length)
        start=v.get('byteOffset',0)+a.get('byteOffset',0)
        require(v.get('buffer',0)==0 and stride>=length and a['count']>0 and start+(a['count']-1)*stride+length<=min(len(binary),v.get('byteOffset',0)+v['byteLength']),'Accessor fuera de rango')
        return [struct.unpack_from('<'+fmt*width,binary,start+i*stride) for i in range(a['count'])]
    require(not any('uri' in b for b in doc['buffers']),'Buffer externo')
    require(len(doc['materials'])==3 and len(doc.get('images',[]))==1,'Materiales/textura inesperados')
    image=doc['images'][0];require('uri' not in image and image['mimeType']=='image/png','Imagen externa')
    view=doc['bufferViews'][image['bufferView']];offset=view.get('byteOffset',0)
    digest=hashlib.sha256(binary[offset:offset+view['byteLength']]).hexdigest()
    require(digest==resolved['resources']['foliage']['sha256'],'Atlas exportado distinto')
    geometry={};uvrows={};channels={}
    for p in doc['meshes'][0]['primitives']:
        mat=doc['materials'][p['material']];name=mat['name'];leaf=name=='Oak_Painted_Leaf'
        require(name in ('Oak_Bark','RF2_Twig','Oak_Painted_Leaf'),'Canal desconocido')
        require(mat.get('doubleSided') is True and mat.get('alphaMode','OPAQUE')==('MASK' if leaf else 'OPAQUE'),'Reversos o transparencia incorrectos')
        pbr=mat['pbrMetallicRoughness']
        require(abs(pbr.get('roughnessFactor',1)-resolved['appearance']['leaf' if leaf else 'bark']['roughness'])<1e-6,'Rugosidad alterada')
        require(pbr.get('metallicFactor',1)==0,'Metal inesperado')
        if leaf:
            require(mat.get('alphaCutoff',.5)==.5 and 'baseColorTexture' in pbr,'Recorte o pintura ausente')
            texture=pbr['baseColorTexture'];require(texture.get('texCoord',0)==0 and doc['textures'][texture['index']]['source']==0,'Textura UV inválida')
            require(pbr.get('baseColorFactor',[1,1,1,1])==[1,1,1,1],'Tinte alterado')
        else:require('baseColorTexture' not in pbr,'Textura en madera histórica')
        vertices=read(p['attributes']['POSITION'],3);normals=read(p['attributes']['NORMAL'],3);uv=read(p['attributes']['TEXCOORD_0'],2)
        require(len(vertices)==len(normals)==len(uv),'Atributos incompletos')
        require(all(math.isfinite(x) for pair in uv for x in pair),'UV no finitas')
        require(not leaf or all(0<=x<=1 for pair in uv for x in pair),'UV fuera del atlas')
        require(all(abs(sum(x*x for x in n)-1)<.0001 for n in normals),'Normales no unitarias')
        indices=[r[0] for r in read(p['indices'],1)]
        for i in range(0,len(indices),3):
            ids=indices[i:i+3];a,b,c=[vertices[j] for j in ids]
            u=[b[k]-a[k] for k in range(3)];v=[c[k]-a[k] for k in range(3)]
            normal=[u[1]*v[2]-u[2]*v[1],u[2]*v[0]-u[0]*v[2],u[0]*v[1]-u[1]*v[0]]
            require(all(sum(x*y for x,y in zip(normal,normals[j]))>0 for j in ids),'Normal invertida')
            geometry.setdefault(name,[]).append(sorted(tuple(vertices[j]) for j in ids))
            uvrows.setdefault(name,[]).append(sorted(tuple(vertices[j]+uv[j]) for j in ids))
            channels.setdefault(name,[]).append(sorted(tuple(round(x,6) for x in vertices[j]+normals[j]) for j in ids))
    folder=Path(path).parent
    reference=json.loads((folder/'base-reference.json').read_text())
    old=json.loads((folder/'reference/manifest.json').read_text())
    wood,twigs,cards=build(reference,old['placements'],old['supports'],old['canopy_spec'],resolved['paint_seed'])
    def f32(v):return struct.unpack('<f',struct.pack('<f',v))[0]
    def position(v):return [f32(v[0]),f32(v[2]),f32(-v[1])]
    for name,pieces in [('RF2_Twig',twigs),('Oak_Painted_Leaf',cards)]:
        expected=[sorted(tuple(position(mesh['vertices'][j])) for j in face) for mesh in pieces for face in mesh['polygons']]
        require(sorted(expected)==sorted(geometry[name]),'Geometría exportada distinta de la resuelta')
    expected_uv=[sorted(tuple(position(g['vertices'][j])+[f32(g['uv'][j][0]),f32(1-f32(g['uv'][j][1]))]) for j in face) for g in cards for face in g['polygons']]
    require(sorted(expected_uv)==sorted(uvrows['Oak_Painted_Leaf']),'UV del atlas alteradas')
    historical=inspect_twigs_glb(folder/'reference/tree.glb',old['metrics'],triangle_limit=12500)
    hashes={name:canonical_hash(sorted(rows)) for name,rows in channels.items()}
    from .foliage import digest as old_digest
    for name in ('Oak_Bark','RF2_Twig'):
        require(old_digest(sorted(channels[name]))==historical['channel_sha256'][name],'Madera o normales históricas modificadas')
    require(report['triangles']==manifest['metrics']['triangles'] and report['materials']==manifest['metrics']['triangles_by_material'],'Métricas distintas')
    require(manifest['placements']==old['placements'] and manifest['supports']==old['supports'],'Distribución o anclajes modificados')
    return {**report,'channel_sha256':hashes,'atlas_sha256':digest,'exported_cards_valid':True,
        'exact_wood_and_twig_channels':True,'placements_and_supports_exact':True,'visible_height_m':reference['height_m']}
