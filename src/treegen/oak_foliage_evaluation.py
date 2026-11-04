"""OF1: comprobar contactos sobre posiciones y UV del GLB, con alfa real."""
import math
from .branch_structure import length,sub
from .surface_evaluation import point_triangle_distance
from .oak_crossed import PLANES,GRID,USABLE
from .oak_crossed_evaluation import channels


def barycentric_uv(point,triangle):
    a,b,c=[v[3:5] for v in triangle];x,y=point
    det=(b[1]-c[1])*(a[0]-c[0])+(c[0]-b[0])*(a[1]-c[1])
    if abs(det)<1e-12:return None
    u=((b[1]-c[1])*(x-c[0])+(c[0]-b[0])*(y-c[1]))/det
    v=((c[1]-a[1])*(x-c[0])+(a[0]-c[0])*(y-c[1]))/det
    return (u,v,1-u-v) if min(u,v,1-u-v)>=-1e-6 else None


def audit_contacts(path,groups,image):
    doc,rows,_,_=channels(path);wood=rows['Painted_Bark'];leaf=rows['Painted_Foliage'];by_tile={}
    for triangle in leaf:
        u=sum(v[3] for v in triangle)/3;v=1-sum(v[4] for v in triangle)/3
        tile=math.floor(v*GRID)*GRID+math.floor(u*GRID)
        by_tile.setdefault(tile,[]).append(triangle)
    records=[]
    for g in groups:
        root=g['root_normalized'];anchor=(g['anchor_m'][0],g['anchor_m'][2],-g['anchor_m'][1]);errors=[];alphas=[]
        for plane,(a,b) in enumerate(PLANES):
            tile=g['template_index']*3+plane;col,row=tile%GRID,tile//GRID
            uv=((col+.5+root[a]*USABLE)/GRID,1-(row+.5+root[b]*USABLE)/GRID)
            candidates=[]
            for triangle in by_tile.get(tile,[]):
                weights=barycentric_uv(uv,triangle)
                if weights is not None:
                    q=tuple(sum(w*v[k] for w,v in zip(weights,triangle)) for k in range(3));candidates.append(math.dist(q,anchor))
            if not candidates:raise ValueError('UV de contacto no cubierta por el GLB')
            errors.append(min(candidates));x=round(uv[0]*image.width);y=round(uv[1]*image.height)
            alphas.append(image.getpixel((x,y))[3])
        wood_error=min(point_triangle_distance(anchor,*(v[:3] for v in tri)) for tri in wood)
        records.append({'id':g['id'],'wood_error_m':wood_error,'panel_errors_m':errors,'paint_alpha':alphas})
    worst=max(max(r['panel_errors_m']+[r['wood_error_m']]) for r in records)
    return {'passed':worst<1e-5 and min(min(r['paint_alpha']) for r in records)>=192,
            'maximum_error_m':worst,'groups':records,'scope':'GLB float32 positions + interpolated UV at opaque painted attachment, not all painted leaf connections'}
