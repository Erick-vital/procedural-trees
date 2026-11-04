"""Auditoría de cada lámina añadida OF10 sobre posiciones/UV exportadas."""
import math
from .oak_crossed_evaluation import channels
from .oak_crossed import GRID,USABLE,PLANES
from .oak_foliage_cards import rooted_panels
from .oak_foliage_evaluation import barycentric_uv


def audit_fans(path,fans,image):
    _,rows,_,_=channels(path);leaf=rows['Painted_Foliage'];by_tile={}
    for tri in leaf:
        u=sum(v[3] for v in tri)/3;v=1-sum(v[4] for v in tri)/3
        by_tile.setdefault(math.floor(v*GRID)*GRID+math.floor(u*GRID),[]).append(tri)
    records=[]
    for fan in fans:
        g=fan['group'];plane=fan['plane'];tile=g['template_index']*3+plane
        card=rooted_panels(g,g['template_index'])[plane];matched=[];geometry_errors=[]
        for face in card['polygons']:
            expected=[(card['vertices'][i][0],card['vertices'][i][2],-card['vertices'][i][1],card['uv'][i][0],1-card['uv'][i][1]) for i in face]
            def error(tri):return max(min(math.dist(v[:3],w[:3])+math.dist(v[3:5],w[3:5]) for w in tri) for v in expected)
            tri=min(by_tile[tile],key=error);err=error(tri);geometry_errors.append(err);matched.append(tri)
        a,b=PLANES[plane];col,row=tile%GRID,tile//GRID;root=g['root_normalized']
        uv=((col+.5+root[a]*USABLE)/GRID,1-(row+.5+root[b]*USABLE)/GRID)
        anchor=(g['anchor_m'][0],g['anchor_m'][2],-g['anchor_m'][1]);errors=[]
        for tri in matched:
            weights=barycentric_uv(uv,tri)
            if weights is not None:
                q=tuple(sum(w*v[k] for w,v in zip(weights,tri)) for k in range(3));errors.append(math.dist(q,anchor))
        alpha=image.getpixel((round(uv[0]*image.width),round(uv[1]*image.height)))[3]
        records.append({'group_id':fan['group_id'],'gap_id':fan['gap_id'],'plane':plane,
                        'geometry_error_m_uv':max(geometry_errors),'root_error_m':min(errors,default=1e9),'paint_alpha':alpha})
    return {'passed':bool(records) and all(r['geometry_error_m_uv']<1e-5 and r['root_error_m']<1e-5 and r['paint_alpha']>=192 for r in records),
            'maximum_geometry_error_m_uv':max((r['geometry_error_m_uv'] for r in records),default=0),
            'maximum_root_error_m':max((r['root_error_m'] for r in records),default=0), 'planes':records,
            'scope':'every expected new triangle matched in GLB positions and UV before interpolating its opaque root; branch contact certified by unchanged OF9 anchor audit'}
