"""Test segmentation arbres morts (aride) : gris-bleu vs sable/roc chaud."""
from pathlib import Path
import numpy as np
from PIL import Image
R = Path(__file__).resolve().parents[2]
OUT = R / 'source/zones_south_north_v4/analysis'
a = np.array(Image.open(R / 'entrancearidedungeonpmdsky.png').convert('RGBA')).astype(int)
r, g, b = a[..., 0], a[..., 1], a[..., 2]
# sondes : tronc gauche (~60,185), branche (~45,170), sable (~200,240), roc (~100,60), bouche (~208,70)
for x, y, nom in [(60,185,'troncG'),(45,170,'brancheG'),(30,175,'brancheG2'),(330,180,'troncD'),
                  (150,160,'arbreC'),(200,240,'sable'),(250,220,'sable2'),(100,60,'roc'),
                  (300,80,'roc2'),(208,70,'bouche'),(120,220,'sable3')]:
    print(f'{nom:10s} xy=({x},{y}) RGB={tuple(a[y,x,:3])}')
# echantillons zones : arbres supposes froids (b>=r, faible saturation chaude)
froid = (b >= r) & (b > 60)
print('pixels froids: %.2f%%' % (100*froid.mean(),))
Image.fromarray((froid*255).astype(np.uint8)).save(OUT/'arid_froid_mask.png')
# rochers violets : clairs vs sol
v = np.array(Image.open(R / 'roadundergound.png').convert('RGBA')).astype(int)
lum = v[...,:3].mean(2)
print('violet lum percentiles:', np.percentile(lum,[5,25,50,75,95]).round(1))
for x,y,nom in [(250,250,'sol'),(250,300,'sol2'),(215,220,'rocher?'),(300,330,'rocher?'),(200,120,'paroi'),(90,120,'boucheG')]:
    print(f'{nom:10s} xy=({x},{y}) RGB={tuple(v[y,x,:3])}')
