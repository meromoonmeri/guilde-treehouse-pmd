"""Verifie : layer unique == blocs natifs miroir, nuit exacte."""
from pathlib import Path
import sys, json
import numpy as np
from PIL import Image
R = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(R / 'source/cote_v4_abyss'))
from night import night
O = R / 'renders/paroi_prairie_sky_v1'
M = json.loads((O / 'manifest.json').read_text())
checks = {}
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
clean[need] = np.median(clean[gmask & ~union][:, :3], axis=0).astype('uint8')
F = clean[328:504, 0:504]
expect = np.concatenate([F, F[:, ::-1]], axis=1)
got = np.array(Image.open(O / 'paroi_prairie_1008x176_jour.png').convert('RGB'))
assert got.shape == (176, 1008, 3) and got.shape[1] % 8 == 0 and got.shape[0] % 8 == 0
assert np.array_equal(got, expect)
checks['layer_unique_natif_exact'] = True
# joints miroir : colonnes dupliquees
for x in (504,):
    assert np.array_equal(got[:, x - 1], got[:, x]), x
checks['joints_continus'] = True
assert night(Image.open(O / 'paroi_prairie_1008x176_jour.png').convert('RGBA')).convert('RGB').tobytes() == Image.open(O / 'paroi_prairie_1008x176_nuit.png').convert('RGB').tobytes()
checks['nuit_abyss_exacte'] = True
rep = {'verifications': checks, 'resultat': 'PASS — 0 difference', 'limites': M['limites']}
(O / 'verification.json').write_text(json.dumps(rep, ensure_ascii=False, indent=2))
print('VERIFY PASS:', json.dumps(checks, ensure_ascii=False))
