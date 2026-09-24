"""Trouver les coupes verticales parois/sol (violet) : variance locale elevee = sol a granules."""
from pathlib import Path
import numpy as np
from PIL import Image
from scipy import ndimage as ndi
R = Path(__file__).resolve().parents[2]
OUT = R / 'source/zones_south_north_v4/analysis'
v = np.array(Image.open(R / 'roadundergound.png').convert('RGBA')).astype(float)
lum = v[...,:3].mean(2)
locstd = ndi.generic_filter(lum, np.std, size=7)
floorish = locstd > 12  # sol granuleux / eboulis
H, W = lum.shape
print('y : left_edge right_edge (colonnes /8)')
for y in range(152, 408, 8):
    row = floorish[y]
    xs = np.flatnonzero(row)
    inside = xs[(xs > 60) & (xs < 444)]
    if len(inside):
        print(f'{y:3d} : {inside.min():3d} ({inside.min()/8:4.1f})  {inside.max():3d} ({inside.max()/8:4.1f})')
vis = np.array(Image.open(R/'roadundergound.png').convert('RGBA'))
vis[floorish] = (vis[floorish]*0.4 + np.array([255,0,255,255])*0.6).astype(np.uint8)
for x in (120, 384):
    vis[:, x-1:x+1] = (255,255,0,255)
Image.fromarray(vis).save(OUT/'violet_floorish_cuts.png')
print('OK')
