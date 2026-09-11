"""Véritable palette cycling : une carte d'indices fixe, des palettes animées.

Aucune translation du plan pour simuler le cycling. Les couleurs des entrées
réservées changent tandis que les indices et la silhouette restent identiques.
"""
from pathlib import Path
from PIL import Image
import numpy as np
import cv2
import json

WATER_RAMP=np.array([(9,112,174),(13,141,196),(31,173,218),(75,208,236),
                     (168,238,251),(239,255,255),(139,230,246),(46,188,223)],dtype=np.uint8)


def create(image, role, directory, prefix):
    directory=Path(directory);directory.mkdir(parents=True,exist_ok=True)
    a=np.array(image.convert('RGBA'));opaque=a[:,:,3]>0;h,w=opaque.shape
    q=Image.fromarray(a[:,:,:3]).quantize(colors=32,dither=Image.Dither.NONE)
    ids=np.array(q).astype('uint8')+1;ids[~opaque]=0
    fixed=np.array(q.getpalette()[:96],np.uint8).reshape(32,3)
    yy,xx=np.indices((h,w))
    if role=='surface':
        median=cv2.medianBlur(a[:,:,:3],5)
        detail=a[:,:,:3].astype(int)-median.astype(int)
        cycle=opaque&(detail.max(2)>5)
        if cycle.sum()<opaque.sum()*.015:
            lum=a[:,:,:3].astype(float)@np.array([.2126,.7152,.0722])
            cycle=opaque&(lum>=np.percentile(lum[opaque],82))
        ids[cycle]=33+((yy[cycle]//3+xx[cycle]//8)%8).astype('uint8')
        base=np.median(a[opaque,:3],axis=0)
        ramp=np.rint(WATER_RAMP*.45+base*.55).clip(0,255).astype('uint8')
        period=24;hold=3
    else:
        light=np.rint(a[:,:,:3].mean(2)/48).astype(int)
        # Bandes fixes le long des rubans. La palette les fait avancer vers le bas.
        ids[opaque]=33+((yy[opaque]//3+light[opaque])%8).astype('uint8')
        cycle=opaque;ramp=WATER_RAMP.copy();period=8;hold=1
    palettes=[]
    for f in range(period):
        table=[[0,0,0,0]]+[list(map(int,rgb))+[255] for rgb in fixed]
        shift=f//hold
        table.extend([list(map(int,ramp[(i-shift)%8]))+[255] for i in range(8)])
        palettes.append(table)
    Image.fromarray(ids).save(directory/(prefix+'_indices.png'),optimize=True)
    data={'kind':'palette_cycle','period':period,'prefix':prefix,'indices':prefix+'_indices.png',
          'palettes':palettes,'cycled_indices':list(range(33,41)),
          'static_indices':list(range(33)),'role':role,'translated_pixels':False}
    (directory/(prefix+'_cycle.json')).write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
    first=np.array(palettes[0],np.uint8)[ids]
    Image.fromarray(first).save(directory/(prefix+'_native.png'),optimize=True)
    assert cycle.any() and len({np.array(p,np.uint8).tobytes() for p in palettes})>=8
    return data


def render(indices, palette):
    return Image.fromarray(np.array(palette,np.uint8)[np.array(indices).astype(int)])
