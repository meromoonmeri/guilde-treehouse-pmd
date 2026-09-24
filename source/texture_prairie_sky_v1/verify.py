"""Verification : chaque pixel de fond vient d'une tuile GIF, details natifs."""
from pathlib import Path
import sys, json, io
import numpy as np
from PIL import Image
R = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(R / 'source/cote_v4_abyss'))
from night import night
O = R / 'renders/texture_prairie_sky_v1'
M = json.loads((O / 'manifest.json').read_text())
checks = {}
ref = np.array(Image.open(R / 'source/sky_peak_v1/gif_0.png').convert('RGB'))
r, g, b = (ref[:, :, i] for i in range(3))
petal = (r.astype(int) > 190) & (r.astype(int) > g.astype(int) * 1.04) & (r.astype(int) > b.astype(int) * 1.08)
grass = (g.astype(int) > r.astype(int) * 1.05) & (g.astype(int) > b.astype(int) * 1.05)
pool = set()
for cy in range(15, 63):
    for cx in range(63):
        if grass[cy * 8:(cy + 1) * 8, cx * 8:(cx + 1) * 8].all() and not petal[cy * 8:(cy + 1) * 8, cx * 8:(cx + 1) * 8].any():
            pool.add(ref[cy * 8:(cy + 1) * 8, cx * 8:(cx + 1) * 8].tobytes())
assert len(pool) == M['vocabulaire_tuiles'], (len(pool), M['vocabulaire_tuiles'])
checks['vocabulaire'] = len(pool)
fond = np.array(Image.open(O / 'prairie_fond_512.png').convert('RGB'))
assert fond.shape == (512, 512, 3)
bad = sum(1 for y in range(64) for x in range(64)
          if fond[y * 8:(y + 1) * 8, x * 8:(x + 1) * 8].tobytes() not in pool)
assert bad == 0, bad
checks['fond_4096_cellules_natives'] = True
# details : sprites == GIF, placements == surface
def sprite(name, bbox):
    x0, y0, x1, y1 = bbox
    return ref[y0:y1, x0:x1]
n = 0
for i, bb in enumerate(M['touffes']):
    a = np.array(Image.open(O / 'details' / f'touffe_{i:02}.png').convert('RGBA'))
    x0, y0, x1, y1 = bb
    assert np.array_equal(a[:, :, :3], ref[y0:y1, x0:x1]), i
    n += 1
for i, bb in enumerate(M['galets']):
    a = np.array(Image.open(O / 'details' / f'galet_{i:02}.png').convert('RGBA'))
    x0, y0, x1, y1 = bb
    assert np.array_equal(a[:, :, :3], ref[y0:y1, x0:x1]), i
    n += 1
checks['details_natifs'] = n
recomp = Image.fromarray(fond, 'RGB').convert('RGBA')
for pl in M['placements']:
    recomp.alpha_composite(Image.open(O / 'details' / f"{pl['sprite']}.png").convert('RGBA'), tuple(pl['pos']))
assert recomp.tobytes() == Image.open(O / 'prairie_sky_512_jour.png').convert('RGBA').tobytes()
checks['surface_recomposee'] = True
assert night(Image.open(O / 'prairie_sky_512_jour.png').convert('RGBA')).tobytes() == Image.open(O / 'prairie_sky_512_nuit.png').convert('RGBA').tobytes()
checks['nuit_abyss_exacte'] = True
rep = {'verifications': checks, 'resultat': 'PASS — 0 difference avec le GIF', 'limites': M['limites']}
(O / 'verification.json').write_text(json.dumps(rep, ensure_ascii=False, indent=2))
print('VERIFY PASS:', json.dumps(checks, ensure_ascii=False))
