"""Surface prairie Sky Peak — 100% tuiles natives du GIF, quilting a raccords.

Imite zones_guidees : vocabulaire natif dedup, selection avec continuite
des bords voisins, jamais de rotation/recoloration. Source = GIF Sky Peak
(504x504, y>=120), pas de feuilles externes.
"""
from pathlib import Path
import sys, json, io
import numpy as np
from scipy import ndimage as nd
from PIL import Image, ImageDraw
R = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(R / 'source/cote_v4_abyss'))
from night import night
O = R / 'renders/texture_prairie_sky_v1'
O.mkdir(parents=True, exist_ok=True)
W = H = 512
GW = GH = 64
rng = np.random.default_rng(11)

ref = np.array(Image.open(R / 'source/sky_peak_v1/gif_0.png').convert('RGB'))
r, g, b = (ref[:, :, i] for i in range(3))
petal = (r.astype(int) > 190) & (r.astype(int) > g.astype(int) * 1.04) & (r.astype(int) > b.astype(int) * 1.08)
grass = (g.astype(int) > r.astype(int) * 1.05) & (g.astype(int) > b.astype(int) * 1.05)

# vocabulaire : cellules 8x8 100% herbe, zero petale, zone prairie y>=120
pool, seen, origins = [], set(), []
for cy in range(15, 63):
    for cx in range(63):
        cell = ref[cy * 8:(cy + 1) * 8, cx * 8:(cx + 1) * 8]
        if grass[cy * 8:(cy + 1) * 8, cx * 8:(cx + 1) * 8].all() and not petal[cy * 8:(cy + 1) * 8, cx * 8:(cx + 1) * 8].any():
            sig = cell.tobytes()
            if sig not in seen:
                seen.add(sig); pool.append(cell); origins.append([cx, cy])
pool = np.stack(pool).astype(float)
print('vocabulaire herbe :', len(pool), 'tuiles distinctes')
# quilting avec continuite des bords (esprit zones_guidees)
choice = np.full((GH, GW), -1)
fond = np.zeros((H, W, 3), 'uint8')
idx = np.arange(len(pool))
for y in range(GH):
    for x in range(GW):
        cand = rng.choice(idx, size=min(24, len(pool)), replace=False)
        score = np.zeros(len(cand))
        if x > 0:
            left = fond[y * 8:(y + 1) * 8, x * 8 - 1]
            score += ((pool[cand, :, 0, :] - left[None, :, :]) ** 2).mean(axis=(1, 2)) / 255 ** 2
        if y > 0:
            up = fond[y * 8 - 1, x * 8:(x + 1) * 8]
            score += ((pool[cand, 0, :, :] - up[None, :, :]) ** 2).mean(axis=(1, 2)) / 255 ** 2
        if x > 0:
            score += (cand == choice[y, x - 1]) * 2.0
        if y > 0:
            score += (cand == choice[y - 1, x]) * 2.0
        best = int(cand[int(np.argmin(score))])
        choice[y, x] = best
        fond[y * 8:(y + 1) * 8, x * 8:(x + 1) * 8] = pool[best].astype('uint8')

# details natifs : touffes sombres + galets (extraits du GIF, poses 1x)
rock_h = (b.astype(int) > r.astype(int) + 8) & (b.astype(int) > g.astype(int) + 8) & (r < 160)
_rlab, _n = nd.label(rock_h, np.ones((3, 3)))
rock_big = np.zeros_like(rock_h)
for _k, _sl in enumerate(nd.find_objects(_rlab), 1):
    if _sl is not None and (_rlab == _k).sum() > 200:
        rock_big |= (_rlab == _k)
rock_big_dil = nd.binary_dilation(rock_big, iterations=3)
dark = grass & (ref.sum(axis=2) < 330)
lab, _ = nd.label(dark, np.ones((3, 3)))
tufts = []
for k, sl in enumerate(nd.find_objects(lab), 1):
    if sl is None: continue
    gy, gx = sl; h, w = gy.stop - gy.start, gx.stop - gx.start
    if not (8 <= w <= 22 and 6 <= h <= 18) or gy.start < 122: continue
    m = lab == k
    halo = nd.binary_dilation(m, iterations=2) & ~m
    if grass[halo].mean() < 0.5: continue
    if (rock_big_dil & nd.binary_dilation(m, iterations=3)).any(): continue
    spr = np.zeros((h, w, 4), 'uint8'); spr[:, :, :3] = ref[gy, gx]
    spr[:, :, 3] = (m[gy, gx] * 255).astype('uint8')
    tufts.append({'bbox': [gx.start, gy.start, gx.stop, gy.stop], 'img': Image.fromarray(spr)})
# Pas de galets isoles dans le GIF (candidats = eclats de falaise) : abandonne.
pebbles = []
tufts = tufts[:8]
print('touffes:', len(tufts), 'galets:', len(pebbles))
assert len(tufts) >= 5, len(tufts)
surf = Image.fromarray(fond, 'RGB').convert('RGBA')
placements = []
for i in range(30):
    t = tufts[i % len(tufts)]
    x, y = int(rng.integers(0, W - t['img'].width)), int(rng.integers(0, H - t['img'].height))
    surf.alpha_composite(t['img'], (x, y))
    placements.append({'sprite': f'touffe_{i % len(tufts):02}', 'pos': [x, y]})
Image.fromarray(fond).save(O / 'prairie_fond_512.png')
surf.save(O / 'prairie_sky_512_jour.png')
night(surf).save(O / 'prairie_sky_512_nuit.png')
(SP := O / 'details').mkdir(exist_ok=True)
for i, t in enumerate(tufts):
    t['img'].save(SP / f'touffe_{i:02}.png')
# planche
board = Image.new('RGB', (1064, 620), '#101a14')
d = ImageDraw.Draw(board)
d.text((14, 8), 'TEXTURE PRAIRIE SKY PEAK — 512x512 natif, tuiles GIF 8x8', fill='#e6d493')
d.text((14, 28), 'vocabulaire %d tuiles · touffes natives · nuit Abyss' % len(pool), fill='#9db3a1')
meadow = Image.open(R / 'source/sky_peak_v1/gif_0.png').convert('RGB').crop((124, 248, 380, 504)).resize((248, 248), Image.NEAREST)
board.paste(meadow, (14, 52))
board.paste(Image.open(O / 'prairie_fond_512.png').resize((248, 248), Image.NEAREST), (274, 52))
board.paste(Image.open(O / 'prairie_sky_512_jour.png').resize((248, 248), Image.NEAREST), (534, 52))
board.paste(Image.open(O / 'prairie_sky_512_nuit.png').resize((248, 248), Image.NEAREST), (794, 52))
for i, lab_ in enumerate(['source GIF (crop)', 'fond quilte', 'surface jour', 'surface nuit']):
    d.text((14 + i * 260, 306), lab_, fill='#a3dae3')
det = Image.open(O / 'prairie_sky_512_jour.png').crop((128, 128, 256, 256)).resize((256, 256), Image.NEAREST)
det2 = Image.open(O / 'prairie_sky_512_nuit.png').crop((320, 256, 448, 384)).resize((256, 256), Image.NEAREST)
board.paste(det, (14, 330)); board.paste(det2, (282, 330))
d.text((14, 592), 'details 2x jour / nuit (presentation)', fill='#9db3a1')
board.save(O / 'PLANCHE_TEXTURE_NE_PAS_IMPORTER.png')
manifest = {'titre': 'Texture prairie Sky Peak 512x512', 'taille': [W, H], 'grille_px': 8,
            'source': 'source/sky_peak_v1/gif_0.png (zone y>=120)', 'vocabulaire_tuiles': len(pool),
            'origines_tuiles': origins, 'choix_cellules': choice.tolist(),
            'touffes': [t['bbox'] for t in tufts], 'galets': [],
            'placements': placements, 'nuit': 'filtre Abyss',
            'limites': ['Surface de texture, pas une scene ; raccords quilting a apprecier a 1x',
                        'Pas de test PMDO/GPU']}
(O / 'manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2))
print('OK texture 512')
