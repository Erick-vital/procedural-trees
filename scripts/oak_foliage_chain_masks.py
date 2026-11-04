"""Indicadores 2D de máscaras alfa, sin atribuir volumen físico o naturalidad."""
from collections import deque
from pathlib import Path
from PIL import Image


def pixels(path):
    im=Image.open(path).convert('L')
    return im.size,bytearray(im.point(lambda v:255 if v<128 else 0).tobytes())


def describe(mask,size):
    width,height=size;remaining=bytearray(mask);areas=[]
    for seed,value in enumerate(remaining):
        if not value:continue
        remaining[seed]=0;queue=deque([seed]);area=0
        while queue:
            pos=queue.popleft();area+=1;x=pos%width;y=pos//width
            for yy in range(max(0,y-1),min(height,y+2)):
                for xx in range(max(0,x-1),min(width,x+2)):
                    nxt=yy*width+xx
                    if remaining[nxt]:remaining[nxt]=0;queue.append(nxt)
        areas.append(area)
    total=sum(bool(v) for v in mask);assert sum(areas)==total
    threshold=max(32,total*.01)
    return {'foreground_pixels':total,'large_components_8_connected':sum(v>=threshold for v in areas),
        'large_component_threshold_pixels':threshold,'largest_component_fraction':max(areas,default=0)/max(1,total),
        'scope':'raw mask, no dilation; significant component >=1% foreground and >=32 pixels'}


def measure(study):
    result={}
    for view in ('front','side','perspective','top'):
        size,wood=pixels(study/'masks'/f'bare--{view}.png');total=sum(bool(v) for v in wood);row={}
        for name in ('OF1','A','B','C'):
            dims,leaf=pixels(study/'masks'/f'{name}-foliage--{view}.png');assert dims==size
            r=describe(leaf,size);r['wood_projection_without_leaf_overlap_fraction']=sum(bool(w) and not l for w,l in zip(wood,leaf))/max(1,total)
            r['overlap_note']='Projection proxy: foliage behind wood also counts as overlap; not true visible wood.';row[name]=r
        result[view]=row
    return result
