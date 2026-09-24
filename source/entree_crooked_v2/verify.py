"""Vérification entrée Crooked v2 : couches générées recalées 1:1."""
from pathlib import Path
import importlib.util
import json
import sys
import zipfile

R = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(R / 'source/cote_v4_abyss'))
import numpy as np
from PIL import Image
from scipy import ndimage as ndi
from night import night

spec = importlib.util.spec_from_file_location('b2', R / 'source/entree_crooked_v2/build.py')
b2 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(b2)

OUT = R / 'renders/entree_crooked_v2'
W, H = 848, 1264
PFX = 'EntreeCrookedV2'
ORDER = ['01_sol_herbe', '02_chemin_sable', '05_rochers', '06_fleurs',
         '03_paroi', '04_bouche', '07_troncs', '08_canopees']
res = []


def check(name, ok, detail=''):
    res.append((name, bool(ok), detail))
    print(('PASS' if ok else 'FAIL'), name, detail)


def arr(n, moment='jour'):
    return np.array(Image.open(OUT / f'{PFX}_{n}_{moment}.png').convert('RGBA'))


def mag(a):
    r, g, bl = a[..., 0].astype(int), a[..., 1].astype(int), a[..., 2].astype(int)
    return (r > 150) & (bl > 150) & (g < 100) & (a[..., 3] > 128)


man = json.load(open(OUT / 'manifest.json'))
J = {n: arr(n) for n in ORDER}

# 1. dimensions + présence
for n in ORDER:
    check(f'dim {n}', J[n].shape == (H, W, 4) and
          (OUT / f'{PFX}_{n}_nuit.png').exists())

# 2. sol opaque plein cadre
check('sol opaque', bool((J['01_sol_herbe'][..., 3] > 128).all()))

# 3. zéro magenta-like dans les couches finales
for n in ORDER:
    check(f'magenta=0 {n}', not mag(J[n]).any())

# 4. paroi/bouche : partition du détouré G_paroi
paroi_d, _ = b2.detour('G_paroi.png')
ref = (np.array(paroi_d)[..., 3] > 0)
mp = (J['03_paroi'][..., 3] > 0)
mb = (J['04_bouche'][..., 3] > 0)
check('paroi∩bouche=0', not (mp & mb).any())
check('paroi∪bouche=détouré', bool(((mp | mb) == ref).all()))
bx0, by0, bx1, by1 = man['details']['bouche_ref']['bbox_rectifie']
check('bouche dans bbox', bool(mb[by0:by1, bx0:bx1].sum() == mb.sum() and mb.sum() > 5000),
      f'n={int(mb.sum())}')

# 5. troncs/canopees : partition du détouré G_arbres placé
ar_d, _ = b2.detour('G_arbres.png')
dxa, dya = man['details']['07_troncs']['regle'] and (40, -56)
plc = np.array(b2.place(ar_d, dxa, dya))
refa = plc[..., 3] > 0
mt = (J['07_troncs'][..., 3] > 0)
mc = (J['08_canopees'][..., 3] > 0)
check('troncs∩canopees=0', not (mt & mc).any())
check('troncs∪canopees=détouré placé', bool(((mt | mc) == refa).all()))
check('troncs non vides', mt.sum() > 1000, f'n={int(mt.sum())}')

# 6. fleurs : touffes gardées ≥12px et sur prairie
F = J['06_fleurs']
non_prairie = (J['02_chemin_sable'][..., 3] > 0) | mp | mb
lab, n3 = ndi.label(F[..., 3] > 0)
bad = 0
for i in range(1, n3 + 1):
    m = lab == i
    if m.sum() < 12 or (m & non_prairie).sum() / m.sum() > 0.15:
        bad += 1
check('fleurs propres', bad == 0, f'touffes={n3} mauvaises={bad}')

# 7. translations multiples de 8
ok = True
for n in ORDER:
    for t in ([man['details'][n].get('translation')] if 'translation' in man['details'][n]
              else [p for _, _, p in []]):
        pass
for n, key in [('02_chemin_sable', 'translation'), ('06_fleurs', 'translation')]:
    t = man['details'][n][key]
    ok &= (t[0] % 8 == 0 and t[1] % 8 == 0)
for _, avant, apres in man['details']['05_rochers']['placements']:
    ok &= ((apres[0] - avant[0]) % 8 == 0 and (apres[1] - avant[1]) % 8 == 0)
check('translations ÷8', ok)

# 8. chemin recentré sur la bouche (snap 8)
mcx = man['details']['bouche_ref']['centroid'][0]
dx = man['details']['02_chemin_sable']['translation'][0]
pcx = man['details']['02_chemin_sable']['couloir_x_avant']
check('chemin snap8 bouche', dx == int(round((mcx - pcx) / 8) * 8), f'dx={dx}')

# 9. nuit == Abyss(jour) par calque, exact
for n in ORDER:
    N = np.array(night(Image.fromarray(J[n])))
    check(f'nuit {n}', bool((N == arr(n, 'nuit')).all()))

# 10. composites == empilement ordre
for moment in ('jour', 'nuit'):
    comp = Image.new('RGBA', (W, H))
    for n in ORDER:
        comp.alpha_composite(Image.fromarray(arr(n, moment) if moment == 'jour'
                                             else np.array(night(Image.fromarray(J[n])))))
    refc = np.array(Image.open(OUT / f'composite_{moment}.png').convert('RGBA'))
    check(f'composite {moment}', bool((np.array(comp) == refc).all()))

# 11. ORA valide : 8 calques == couches jour
z = zipfile.ZipFile(OUT / 'entreecrookedv2.ora')
xml = z.read('stack.xml').decode()
import io as _io
ok = all(f'<layer name="{n}"' in xml for n in ORDER)
for n in ORDER:
    o = np.array(Image.open(_io.BytesIO(z.read(f'data/{n}.png'))).convert('RGBA'))
    ok &= bool((o == J[n]).all())
check('ora 8 calques == jour', ok)

# 12. manifest : sha bruts + entrée sur chemin + centroid bouche
import hashlib
ok = all(hashlib.sha256((R / 'source/entree_crooked_v2/bruts' / f).read_bytes()).hexdigest() == s
         for f, s in man['bruts'].items())
check('sha bruts', ok)
ex, ey = man['entree']
check('entrée sur chemin', bool(J['02_chemin_sable'][ey, ex, 3] > 0), f'{man["entree"]}')
cx, cy = man['details']['bouche_ref']['centroid']
check('centroid dans bouche', bool(mb[cy, cx]), f'({cx},{cy})')

# 13. couches non vides
for n in ORDER:
    check(f'remplissage {n}', (J[n][..., 3] > 0).sum() > 1000)

npass = sum(1 for _, ok, _ in res if ok)
print(f'\n{npass}/{len(res)} PASS')
sys.exit(0 if npass == len(res) else 1)
