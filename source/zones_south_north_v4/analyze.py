"""Vues de planification : refs + grille 32px/8px pour definir les modules natifs."""
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw
R = Path(__file__).resolve().parents[2]
OUT = R / 'source/zones_south_north_v4/analysis'
OUT.mkdir(exist_ok=True)
for f in ['entrancearidedungeonpmdsky.png', 'roadundergound.png']:
    im = Image.open(R / f).convert('RGBA')
    W, H = im.size
    print(f, im.size)
    g = im.copy()
    d = ImageDraw.Draw(g)
    for x in range(0, W + 1, 8):
        d.line([(x, 0), (x, H)], fill=(255, 0, 255, 90 if x % 32 else 180), width=1)
    for y in range(0, H + 1, 8):
        d.line([(0, y), (W, y)], fill=(255, 0, 255, 90 if y % 32 else 180), width=1)
    for x in range(0, W, 64):
        d.text((x + 2, 2), str(x), fill=(255, 255, 0, 255))
    for y in range(0, H, 64):
        d.text((2, y + 2), str(y), fill=(255, 255, 0, 255))
    g.save(OUT / f.replace('.png', '_grid.png'))
    # stats par bandeau horizontal : saturation/luminosite medianes (reperer sol vs paroi)
    a = np.array(im).astype(float)
    mx = a[..., :3].max(2); mn = a[..., :3].min(2)
    sat = np.where(mx > 0, (mx - mn) / np.maximum(mx, 1), 0)
    lum = a[..., :3].mean(2)
    print('  y : sat_med lum_med (bandes 16px)')
    for y in range(0, H, 16):
        print(f'  {y:3d}: {np.median(sat[y:y+16]):.2f} {np.median(lum[y:y+16]):5.1f}')
print('OK', OUT)
