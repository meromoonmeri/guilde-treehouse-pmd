"""Verification du lot entree_crooked_finale (decomposition de FINALE_map.png)."""
import hashlib
import json
import sys
from pathlib import Path

R = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(R / 'source/cote_v4_abyss'))
import numpy as np
from PIL import Image
from scipy import ndimage as ndi
from night import night

OUT = R / 'renders/entree_crooked_finale'
SRC = R / 'source/entree_crooked_finale'
PFX = 'EntreeCrookedFinale'
res = []


def check(name, ok, detail=''):
    res.append((name, bool(ok), str(detail)))
    print(('PASS ' if ok else 'FAIL ') + name, detail)


lay = {}
for n in ['01_sol_herbe', '02_chemin_sable', '03_paroi', '04_bouche',
           '05_rochers', '06_fleurs', '07_troncs', '08_canopees']:
    a = np.array(Image.open(OUT / f'{PFX}_{n}_jour.png'))
    lay[n] = a
H, W = lay['01_sol_herbe'].shape[:2]
masks = {n: a[..., 3] > 0 for n, a in lay.items()}

# 1. partition exacte
acc = np.zeros((H, W), int)
for m in masks.values():
    acc += m
check('partition-exacte', (acc == 1).all(), f'min={acc.min()} max={acc.max()}')

# 2. composite == brut pixel-exact
brut = np.array(Image.open(SRC / 'bruts/FINALE_map.png').convert('RGBA'))
comp = np.array(Image.open(OUT / 'composite_jour.png'))
check('composite==brut', (comp[..., :3] == brut[..., :3]).all(),
      f'diff={(comp[..., :3].astype(int) - brut[..., :3].astype(int)).max()}')

# 3. nuit Abyss exacte
compn = np.array(Image.open(OUT / 'composite_nuit.png'))
ref = np.array(night(Image.fromarray(brut)))
check('nuit-Abyss', (compn[..., :3] == ref[..., :3]).all())

# 4. bouche : 1 composante, bbox manifeste
man = json.loads((OUT / 'manifest.json').read_text())
lab, n = ndi.label(masks['04_bouche'])
ys, xs = np.nonzero(masks['04_bouche'])
check('bouche-1comp', n == 1, f'n={n}')
check('bouche-bbox', [int(xs.min()), int(ys.min()), int(xs.max() + 1), int(ys.max() + 1)] == man['bouche_bbox'])

# 5. arbres : 4 troncs + 4 canopees
_, nt = ndi.label(masks['07_troncs'])
_, nc = ndi.label(masks['08_canopees'])
check('troncs-4', nt == 4, f'n={nt}')
check('canopees-4', nc == 4, f'n={nc}')
check('arbres-manifest', len(man['arbres']) == 4)

# 6. fleurs : 65, tailles, y>=620
labf, nfl = ndi.label(masks['06_fleurs'])
sizes = sorted((labf == i).sum() for i in range(1, nfl + 1))
check('fleurs-65', nfl == 65, f'n={nfl}')
check('fleurs-tailles', all(6 < s < 600 for s in sizes), f'min={min(sizes)} max={max(sizes)}')
yf, _ = np.nonzero(masks['06_fleurs'])
check('fleurs-y', yf.min() >= 620, f'min={yf.min()}')

# 7. rochers : au voisinage de la bouche
labr, nrk = ndi.label(masks['05_rochers'])
ok = True
for i in range(1, nrk + 1):
    yy, xx = np.nonzero(labr == i)
    if not (abs(xx.mean() - 424) < 260 and yy.mean() < man['bouche_bbox'][3] + 120):
        ok = False
check('rochers-voisinage', ok, f'n={nrk}')

# 8. sol complet : opaque, == sol ou echantillon
sc = np.array(Image.open(OUT / f'{PFX}_00_sol_complet_jour.png'))
exp = masks['01_sol_herbe'] | masks['08_canopees'] | masks['07_troncs'] | masks['06_fleurs']
check('sol-complet-opaque', ((sc[..., 3] > 0) == exp).all())
same = (sc[..., :3][masks['01_sol_herbe']] == lay['01_sol_herbe'][..., :3][masks['01_sol_herbe']]).all()
check('sol-complet==sol', same)

# 9. manifest : sha256 + cles
sha = hashlib.sha256((SRC / 'bruts/FINALE_map.png').read_bytes()).hexdigest()
check('manifest-sha', man['sha256'] == sha)
check('manifest-cles', all(k in man for k in ('canevas', 'bouche_bbox', 'arbres', 'nb_fleurs', 'ordre', 'nuit')))

# 10. fichiers nuit presents
nfiles = [OUT / f'{PFX}_{n}_nuit.png' for n in masks] + [OUT / f'{PFX}_00_sol_complet_nuit.png']
check('fichiers-nuit', all(f.exists() for f in nfiles), f'{len(nfiles)} fichiers')

(OUT / 'verification.json').write_text(json.dumps(
    [{'nom': n, 'ok': o, 'detail': d} for n, o, d in res], indent=1, ensure_ascii=False))
fails = [n for n, o, _ in res if not o]
print(f'{len(res) - len(fails)}/{len(res)} PASS')
sys.exit(1 if fails else 0)
