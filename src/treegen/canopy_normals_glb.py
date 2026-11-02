"""Adaptador T4: sustituir exclusivamente float32 NORMAL de follaje en GLB."""
import math
import struct
from collections import Counter
from .seasonal_paint import unpack
from .season_calendar_glb import _primitives,read_accessor
from .canopy_normals import normal,dot,VERSION


def normal_offsets(doc,primitive):
    index=primitive['attributes']['NORMAL'];a=doc['accessors'][index];view_index=a['bufferView']
    if a['componentType']!=5126 or a['type']!='VEC3':raise ValueError('NORMAL no es float32 VEC3')
    if any(i!=index and b['bufferView']==view_index for i,b in enumerate(doc['accessors'])):
        raise ValueError('NORMAL comparte vista con otro atributo')
    if any(i.get('bufferView')==view_index for i in doc.get('images',[])):
        raise ValueError('NORMAL comparte vista con imagen')
    if sum(p['attributes'].get('NORMAL')==index for _,p in _primitives(doc))!=1:
        raise ValueError('NORMAL compartida entre materiales')
    view=doc['bufferViews'][view_index]
    low=view.get('byteOffset',0);high=low+view['byteLength']
    if any(i!=view_index and other.get('byteOffset',0)<high and other.get('byteOffset',0)+other['byteLength']>low for i,other in enumerate(doc['bufferViews'])):
        raise ValueError('Vista NORMAL solapada con otro recurso')
    start=low+a.get('byteOffset',0)
    # read_accessor valida tamaño, stride y rango antes de escribir.
    return [start+i*view.get('byteStride',12) for i in range(a['count'])]


def rows(raw):
    doc,binary=unpack(raw);result=[]
    for name,p in _primitives(doc):
        if name!='Painted_Foliage':continue
        a=p['attributes'];v=read_accessor(doc,binary,a['POSITION'],3);u=read_accessor(doc,binary,a['TEXCOORD_0'],2);n=read_accessor(doc,binary,a['NORMAL'],3)
        if len(v)!=len(u) or len(v)!=len(n):raise ValueError('Atributos de follaje incompletos')
        result.extend({'position':list(x),'uv':list(y),'normal':list(z)} for x,y,z in zip(v,u,n))
    return result


def replace_normals(raw,binding,fields,strength):
    doc,binary=unpack(raw);updated=bytearray(binary);owners={}
    if not isinstance(binding,list) or not 1<=len(binding)<=10000:raise ValueError('Binding excesivo o vacío')
    for row in binding:
        key=tuple(row['position'])+tuple(row['uv']);owner=row['group_id']
        if owner not in fields or key in owners and owners[key]!=owner:raise ValueError('Binding ambiguo o desconocido')
        owners[key]=owner
    groups=Counter();angles=[];count=0
    for name,p in _primitives(doc):
        if name!='Painted_Foliage':continue
        a=p['attributes'];v=read_accessor(doc,binary,a['POSITION'],3);u=read_accessor(doc,binary,a['TEXCOORD_0'],2);n=read_accessor(doc,binary,a['NORMAL'],3)
        indices=[r[0] for r in read_accessor(doc,binary,p['indices'],1)]
        if len(v)!=len(u) or len(v)!=len(n) or any(i>=len(v) for i in indices) or len(indices)%3:
            raise ValueError('Topología o atributos incorrectos')
        identifiers=[]
        offsets=normal_offsets(doc,p)
        for position,uv,original,offset in zip(v,u,n,offsets):
            identifier=owners.get(tuple(position)+tuple(uv))
            if identifier is None:raise ValueError('Vértice de follaje sin grupo')
            identifiers.append(identifier)
            candidate=normal(position,original,fields[identifier],strength)
            if strength!=0:struct.pack_into('<3f',updated,offset,*candidate)
            angles.append(math.degrees(math.acos(max(-1,min(1,dot(original,candidate)/math.sqrt(dot(original,original)))))))
            count+=1
        for i in range(0,len(indices),3):
            ids={identifiers[j] for j in indices[i:i+3]}
            if len(ids)!=1:raise ValueError('Cara mezcla grupos')
            groups[next(iter(ids))]+=1
    if not groups or any(value!=6 for value in groups.values()):raise ValueError('Grupo sin tres láminas completas')
    result=raw[:-len(binary)]+updated
    report=audit_normals(raw,result)
    report.update(version=VERSION,strength=strength,vertices=count,groups=len(groups),group_ids=sorted(groups),
                  max_angle_deg=max(angles),mean_angle_deg=sum(angles)/len(angles))
    return result,report


def audit_normals(before,after):
    doc,old=unpack(before);new_doc,new=unpack(after)
    if doc!=new_doc or len(before)!=len(after) or before[:-len(old)]!=after[:-len(new)]:
        raise ValueError('Documento/cabecera/longitud GLB modificados')
    restored=bytearray(new);changed=0
    for name,p in _primitives(doc):
        if name!='Painted_Foliage':continue
        a=p['attributes'];normals=read_accessor(new_doc,new,a['NORMAL'],3)
        for n,offset in zip(normals,normal_offsets(doc,p)):
            if abs(dot(n,n)-1)>2e-6:raise ValueError('Normal final no unitaria')
            changed+=old[offset:offset+12]!=new[offset:offset+12]
            restored[offset:offset+12]=old[offset:offset+12]
    if bytes(restored)!=old:raise ValueError('Cambió un byte fuera de normales de follaje')
    return {'only_foliage_normals_changed':True,'positions_uv0_uv2_indices_exact':True,
            'wood_images_materials_scene_exact':True,'changed_normal_vertices':changed,'bytes_added':0}
