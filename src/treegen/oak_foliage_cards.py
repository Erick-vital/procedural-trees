"""OF1: atlas histórico sin retocar; láminas que coinciden en la raíz pintada."""
import math
from .branch_structure import add,sub,mul,dot,length
from .oak_growth import cross
from .oak_crossed import panels,PLANES


def template_geometry(template):
    world=[v for c in template['source_cards'] for v in c['vertices']]
    local=[v for row in template['normalized_vertices'] for v in row]
    origin=world[0];norigin=local[0]
    # Dos ejes de una tarjeta y un tercer vértice no coplanario.
    a=sub(world[1],origin);b=sub(world[3],origin)
    index=max(range(len(world)),key=lambda i:abs(dot(a,cross(b,sub(world[i],origin)))))
    c=sub(world[index],origin);det=dot(a,cross(b,c))
    if abs(det)<1e-10:raise ValueError('Plantilla degenerada')
    na=sub(local[1],norigin);nb=sub(local[3],norigin);nc=sub(local[index],norigin)
    def to_local(point):
        q=sub(point,origin);x=dot(q,cross(b,c))/det;y=dot(a,cross(q,c))/det;z=dot(a,cross(b,q))/det
        return add(norigin,add(mul(na,x),add(mul(nb,y),mul(nc,z))))
    error=max(length(sub(to_local(w),n)) for w,n in zip(world,local))
    if error>1e-6:raise ValueError('Correspondencia de plantilla inválida')
    ndet=dot(na,cross(nb,nc))
    def to_world_vector(v):
        x=dot(v,cross(nb,nc))/ndet;y=dot(na,cross(v,nc))/ndet;z=dot(na,cross(nb,v))/ndet
        return add(mul(a,x),add(mul(b,y),mul(c,z)))
    sizes=[length(to_world_vector(v)) for v in ((1,0,0),(0,1,0),(0,0,1))]
    root=to_local(template['source_cards'][0]['origin_m'])
    return {'root_normalized':root,'root_candidates_normalized':[to_local(c['origin_m']) for c in template['source_cards']],'aspect':[v/max(sizes) for v in sizes],'affine_error':error}


def rooted_panels(group,template_index):
    result=panels(group,template_index,3);root=group['root_normalized']
    for panel,(a,b) in zip(result,PLANES):
        depth=({0,1,2}-{a,b}).pop();offset=mul(group['axes'][depth],root[depth]*group['size_m'][depth])
        panel['vertices']=[add(v,offset) for v in panel['vertices']]
        panel['source_branch_id']=group['parent_branch_id']
    return result


def prepare_templates(templates,image):
    """Elegir contacto opaco común a las tres proyecciones sin retocar PNG."""
    from itertools import product
    from .oak_crossed import GRID,USABLE
    result=[]
    def alpha(root,index,plane):
        a,b=PLANES[plane];tile=index*3+plane;col,row=tile%GRID,tile//GRID
        u=(col+.5+root[a]*USABLE)/GRID;v=1-(row+.5+root[b]*USABLE)/GRID
        x=max(0,min(image.width-1,round(u*image.width)));y=max(0,min(image.height-1,round(v*image.height)))
        return image.getpixel((x,y))[3]
    offsets=sorted(product(range(-8,9),repeat=3),key=lambda d:(sum(v*v for v in d),d))
    for index,t in enumerate(templates):
        info=template_geometry(t);found=None
        for root_index,original in enumerate(info['root_candidates_normalized']):
            for delta in offsets:
                root=[v+d*.005 for v,d in zip(original,delta)]
                values=[alpha(root,index,plane) for plane in range(3)]
                if min(values)>=192:found=(root,values,original,root_index);break
            if found is not None:break
        if found is None:raise ValueError('Plantilla sin contacto opaco acotado: '+str(index))
        root,values,original,root_index=found;info.update(root_normalized=root,source_root_normalized=original,
            selected_stem_root=root_index,paint_root_shift_normalized=length(sub(root,original)),root_alpha=values)
        result.append(info)
    return result
