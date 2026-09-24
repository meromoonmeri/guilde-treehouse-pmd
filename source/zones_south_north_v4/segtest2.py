from pathlib import Path
import numpy as np
from PIL import Image
from scipy import ndimage as ndi
R = Path(__file__).resolve().parents[2]
OUT = R / 'source/zones_south_north_v4/analysis'
a = np.array(Image.open(R / 'entrancearidedungeonpmdsky.png').convert('RGBA')).astype(int)
r,g,b = a[...,0],a[...,1],a[...,2]
lum = a[...,:3].mean(2)
desat = (r-b < 25) & (lum>35) & (lum<215)
print('desat: %.2f%%' % (100*desat.mean(),))
lab,n = ndi.label(desat)
print('composantes:', n)
sizes = sorted(((lab==i).sum(),i) for i in range(1,n+1) if (lab==i).sum()>15)
print('grosses (>15px):', [(s,i) for s,i in sizes])
for s,i in sizes:
    ys,xs = np.nonzero(lab==i)
    print(f'  comp{i}: n={s} bbox x[{xs.min()},{xs.max()}] y[{ys.min()},{ys.max()}]')
vis = np.array(Image.open(R/'entrancearidedungeonpmdsky.png').convert('RGBA'))
vis[desat] = (255,0,255,255)
Image.fromarray(vis).save(OUT/'arid_desat_mask.png')
# bouche : pixels sombres
sombre = lum < 40
lab2,n2 = ndi.label(sombre)
for i in range(1,n2+1):
    s=(lab2==i).sum()
    if s>50:
        ys,xs=np.nonzero(lab2==i)
        print(f'sombre{i}: n={s} bbox x[{xs.min()},{xs.max()}] y[{ys.min()},{ys.max()}]')
# violet : bouche = pixels tres sombres ; rochers clairs sur sol
v = np.array(Image.open(R/'roadundergound.png').convert('RGBA')).astype(int)
lumv = v[...,:3].mean(2)
sombre = lumv < 45
lab3,n3 = ndi.label(sombre)
print('violet composantes sombres:')
for i in range(1,n3+1):
    s=(lab3==i).sum()
    if s>100:
        ys,xs=np.nonzero(lab3==i)
        print(f'  sombre{i}: n={s} bbox x[{xs.min()},{xs.max()}] y[{ys.min()},{ys.max()}]')
