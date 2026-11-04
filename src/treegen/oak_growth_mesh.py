"""Tubos con marcos transportados, UV de corteza y anillos de orden explícito."""
import math
from .oak_growth import unit,cross,frame
from .branch_structure import add,sub,mul,dot,length


def tube(branch):
    points=branch['points'];radii=branch['radii'];sides=branch['sides'];vertices=[];uv=[];faces=[];smooth=[]
    n=None;distance=0.
    for i,point in enumerate(points):
        tangent=unit(sub(points[min(i+1,len(points)-1)],points[max(0,i-1)]))
        if i==0 and branch['order']==0:tangent=(0.,0.,1.)
        if n is None:n=frame(tangent)[0]
        else:
            projected=sub(n,mul(tangent,dot(n,tangent)));n=unit(projected) if length(projected)>1e-8 else frame(tangent)[0]
        b=unit(cross(tangent,n))
        for j in range(sides):
            theta=2*math.pi*j/sides;offset=mul(add(mul(n,math.cos(theta)),mul(b,math.sin(theta))),radii[i])
            vertices.append(add(point,offset));uv.append([j/sides,distance/1.4])
        if i<len(points)-1:distance+=length(sub(points[i+1],point))
    for i in range(len(points)-1):
        for j in range(sides):
            faces.append([i*sides+j,i*sides+(j+1)%sides,(i+1)*sides+(j+1)%sides,(i+1)*sides+j]);smooth.append(True)
    faces.append(list(range((len(points)-1)*sides,len(points)*sides)));smooth.append(False)
    if branch['order']==0:faces.append(list(reversed(range(sides))));smooth.append(False)
    return {'vertices':vertices,'polygons':faces,'uv':uv,'smooth':smooth}


def meshes(structure):
    return [{'id':b['id'],'parent_id':b['parent_id'],'order':b['order'],'mesh':tube(b)} for b in structure['branches']]
