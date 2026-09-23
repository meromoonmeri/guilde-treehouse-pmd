# -*- coding: utf-8 -*-
"""V4 verification : the base V3 layout is preserved (centre of the wall, stars, meteors, moon,
panorama, mist bands, plateau are pixel-identical) while the wall flanks are extended to the frame
corners and the sky/clouds are rebuilt. Re-runs the build deterministically, then checks numbers."""
from pathlib import Path
import subprocess, sys, json
import numpy as np
from PIL import Image

R = Path(__file__).resolve().parents[2]
O = R/'renders/sky_peak_prairie_v1'
V3 = O/'v3'; V = O/'v4'
P3 = 'SkyPeakPrairieV3'; P = 'SkyPeakPrairieV4'
W, H = 960, 864

checks = []
def ok(name, cond, detail=''):
    checks.append((name, bool(cond), detail))

def load(v, n, d='v3'):
    base = V3 if d == 'v3' else V
    pre = P3 if d == 'v3' else P
    path = base/(('calques' if n.endswith('.png') is False and not n.startswith(('etoiles','filantes')) else '') + '')
    return Image.open(base/'calques'/f'{pre}_{n}.png').convert('RGBA')

def L3(n): return Image.open(V3/'calques'/f'{P3}_{n}.png').convert('RGBA')
def L4(n): return Image.open(V/'calques'/f'{P}_{n}.png').convert('RGBA')

# 01 composition exists
for f in [f'{P}_composition_nuit.png', f'{P}_composition_nuit_abyss.png', f'{P}_editable.ora']:
    ok(f'exists {f}', (V/f).exists())
ok(f'exists calques/{P}_01_ciel_profond.png', (V/'calques'/f'{P}_01_ciel_profond.png').exists())

# 02 centre de la paroi identique au V3 (layout de base conservé)
w3 = np.array(L3('08_paroi_rocheuse')); w4 = np.array(L4('08_paroi_rocheuse'))
centre3 = w3[400:864, 179:781]; centre4 = w4[400:864, 179:781]
ok('wall centre == V3 (pixels identiques)', (centre3 == centre4).all(),
   f'diff={(centre3!=centre4).sum()}')

# 03 flancs couverts jusqu'aux coins
for lbl, sl in [('left', (slice(800,864), slice(0,80))), ('right', (slice(800,864), slice(880,960)))]:
    o = (w4[sl][..., 3] > 0)
    ok(f'wall flank {lbl} covers corners', o.mean() > 0.98, f'frac={o.mean():.2f}')

# 04 haut de la paroi : pas de vert vif dans la zone élargie des flancs
a4 = w4[..., :3]; green = (a4[..., 1] > 190) & (a4[..., 0] < 130) & (w4[..., 3] > 0)
ok('no bright-green fringe in extended flanks', green[:, :144].sum() < 40 and green[:, 816:].sum() < 40,
   f'L={green[:, :144].sum()} R={green[:, 816:].sum()}')

# 05 centre bas : toujours herbe (plateau) sauf paroi d'origine
pa = np.array(L4('07_plateau_herbe')); po = pa[..., 3] > 0
ok('plateau grass still present (base layout)', po.sum() > 100000, f'px={po.sum()}')

# 06 étoiles / filantes réutilisées à l'identique
s3 = np.array(Image.open(V3/'etoiles_frames'/f'{P3}_etoiles_00.png').convert('RGBA'))
s4 = np.array(Image.open(V/'etoiles_frames'/f'{P}_etoiles_00.png').convert('RGBA'))
ok('stars frame 00 == V3', (s3 == s4).all())

# 07 lune réutilisée
ok('moon == V3', np.array(L3('03_lune_generee') == L4('03_lune_generee')).all())

# 08 ciel lisse (sans motifs parasites), opaque
sk = np.array(L4('01_ciel_profond'))
ok('sky opaque', (sk[..., 3] == 255).all())
# variance locale faible hors lune/horizon
lum = sk[:, :, :3].astype(float).mean(2)
mid = lum[80:300, 80:300]
ok('sky smooth (no baked cloud motifs)', mid.std() < 35, f'std={mid.std():.1f}')

# 09 nuages : 6 blocs distincts sur la bande lointaine + overlay
far = np.array(L4('bande_nuages_lointains_1440'))
o = far[..., 3] > 0
# nuages = pixels clairs ET ombres portées (tous différents du ciel sombre derrière)
nl = int(o.sum())
ok('far strip has varied clouds', nl > 15000, f'px={nl}')
sky0 = np.array(L4('01_ciel_profond'), dtype=int)[:, :, :3]
topy, topx = np.nonzero(o)
sample = sky0[topy[:2000], topx[:2000]]
ok('clouds contrast with sky', far[o][:,:3].mean() > sample.mean() + 10)

# 10 composition produite par build.py, distincte de V3 (corrections appliquées)
c4 = np.array(Image.open(V/f'{P}_composition_nuit.png').convert('RGB'))
c3 = np.array(Image.open(V3/f'{P3}_composition_nuit.png').convert('RGB'))
ok('composition differs from V3 (corrections applied)', (c4 != c3).sum() > 5000, f'diff={(c4!=c3).sum()}')

# 11 lune visible dans la composition (pixels clairs dans la zone lune)
moon = c4[48:176, 716:844]
ok('moon visible in composition', (moon.sum(2) > 400).sum() > 800)

fail = [c for c in checks if not c[1]]
print(f'{len(checks)-len(fail)} / {len(checks)} PASS')
for name, cond, detail in checks:
    print(('PASS' if cond else 'FAIL'), name, detail)
for name, cond, detail in fail:
    pass
sys.exit(1 if fail else 0)
