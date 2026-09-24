"""Paroi rocheuse + prairie Sky Peak en LAYER UNIQUE 1024x176.

Bande native 504x176 du GIF (fleurs retirees par infill 4 frames),
carrelee en miroir [F][M(F)] : joint unique continu (colonne dupliquee),
100% pixels natifs 1x, jour + nuit Abyss.
"""
from pathlib import Path
import sys, json
import numpy as np
from PIL import Image, ImageDraw
R = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(R / 'source/cote_v4_abyss'))
from night import night
O = R / 'renders/paroi_prairie_sky_v1'
O.mkdir(parents=True, exist_ok=True)

refs = [np.array(Image.open(R / f'source/sky_peak_v1/gif_{i}.png').convert('RGB')) for i in range(4)]
pet = []
for fr in refs:
    r, g, b = (fr[:, :, i].astype(float) for i in range(3))
    pet.append((r > 190) & (r > g * 1.04) & (r > b * 1.08))
union = np.logical_or.reduce(pet)
clean = refs[0].copy(); need = union.copy()
for i, fr in enumerate(refs):
    fill = need & (~pet[i]); clean[fill] = fr[fill]; need &= pet[i]
gr = clean[:, :, 1].astype(float); rr = clean[:, :, 0].astype(float); bb = clean[:, :, 2].astype(float)
gmask = (gr > rr * 1.05) & (gr > bb * 1.05)
med = np.median(clean[gmask & ~union][:, :3], axis=0).astype('uint8')
clean[need] = med
F = clean[328:504, 0:504]
layer = np.concatenate([F, F[:, ::-1]], axis=1)
assert layer.shape == (176, 1008, 3)
Image.fromarray(layer).save(O / 'paroi_prairie_1008x176_jour.png')
night(Image.fromarray(layer).convert('RGBA')).convert('RGB').save(O / 'paroi_prairie_1008x176_nuit.png')
# planche
board = Image.new('RGB', (1064, 560), '#101a14')
d = ImageDraw.Draw(board)
d.text((14, 8), 'PAROI + PRAIRIE SKY — layer unique 1008x176 natif', fill='#e6d493')
d.text((14, 28), 'blocs GIF A[0:256] B[248:504] y328:504 · miroir joints x256/512/768 · nuit Abyss', fill='#9db3a1')
board.paste(Image.open(O / 'paroi_prairie_1008x176_jour.png').resize((1008, 176), Image.NEAREST), (14, 52))
board.paste(Image.open(O / 'paroi_prairie_1008x176_nuit.png').resize((1008, 176), Image.NEAREST), (14, 238))
for i, x in enumerate((504 - 80, 504 - 80, 504 - 80)):
    crop = Image.open(O / 'paroi_prairie_1008x176_jour.png').crop((x, 0, x + 160, 176)).resize((320, 352 // 2), Image.NEAREST)
    board.paste(crop, (14 + i * 330, 424 - 88))
d.text((14, 530), 'joints 2x aux miroirs (presentation)', fill='#9db3a1')
board.save(O / 'PLANCHE_PAROI_NE_PAS_IMPORTER.png')
manifest = {'titre': 'Paroi + prairie Sky 1008x176 layer unique', 'taille': [1008, 176], 'grille_px': 8,
            'source': 'source/sky_peak_v1/gif_0..3.png', 'bloc': [0, 328, 504, 504],
            'miroir': '[F][M(F)], joint unique x=504', 'fleurs_retirees': int(union[328:504].sum()),
            'vert_median': med.tolist(), 'nuit': 'filtre Abyss',
            'limites': ['Texture/scene plate, pas de test PMDO/GPU']}
(O / 'manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2))
print('OK paroi+prairie layer unique')
