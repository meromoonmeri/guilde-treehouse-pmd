"""Verification independante V3 : commun V2, detourage, nuit, re-assemblage, audit."""
from pathlib import Path
import json
import hashlib
import sys

import numpy as np
from PIL import Image

R = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(R / 'source'))
from cote_v4_abyss.night import night  # noqa: E402

O = R / 'renders/falaises_proches_metano_v3'
V2 = R / 'renders/falaises_proches_metano_v2'
report = {'checks': []}


def check(name, ok, detail=''):
    report['checks'].append({'name': name, 'ok': bool(ok), 'detail': str(detail)})
    print(('PASS' if ok else 'FAIL'), name, detail, flush=True)
    if not ok:
        raise SystemExit(f'ECHEC: {name}')


manifest = json.loads((O / 'manifest.json').read_text())

# 1. Commun = copies V2 a l'octet.
for n in ['01_ciel_jour', '02_ciel_nuit', '03_mer_jour', '04_mer_nuit',
          '05_nuages_wrap_jour', '06_nuages_wrap_nuit']:
    check(f'commun {n} == V2', (O / 'commun' / (n + '.png')).read_bytes()
          == (V2 / 'commun' / (n + '.png')).read_bytes())
ocean_ok = all((O / 'commun/ocean' / p.name).read_bytes() == p.read_bytes()
               for p in (V2 / 'commun/ocean').glob('*.png'))
check('commun ocean 128ph == V2', ocean_ok)
check('commun palettes == V2', (O / 'commun/ocean/palettes.json').read_text()
      == (V2 / 'commun/ocean/palettes.json').read_text())

# 2. Layouts presents, shas manifest.
for n, h in manifest['layout_sha256'].items():
    check(f'layout {n}', hashlib.sha256((O / 'layouts' / (n + '.png')).read_bytes()).hexdigest() == h)

# 3. Audit texture reproductible (meme graine).
ref = np.unique(np.array(Image.open(R / 'source/falaises_generees/reference_canonique.png')
                         .convert('RGB')).reshape(-1, 3), axis=0).astype(float)
for v in manifest['variants']:
    slug = v['id']
    d = O / slug
    terrain = Image.open(d / '07_falaise.png').convert('RGBA')
    a = np.array(terrain)
    op = a[:, :, 3] > 0
    px = a[op][:, :3].astype(float)
    sample = px[np.random.RandomState(0).choice(len(px), 20000, replace=False)]
    dist = np.sqrt(((sample[:, None, :] - ref[None, :, :]) ** 2).sum(-1)).min(1)
    got = {'pct_le30': round(float((dist <= 30).mean() * 100), 1),
           'pct_exact': round(float((dist == 0).mean() * 100), 2)}
    check(f'{slug} audit == manifest', got == v['audit_texture'], got)
    # 4. Detourage : 0 magenta residuel, alpha coherente.
    f = a[:, :, :3].astype(float)
    mag = (f[:, :, 0] > f[:, :, 1] * 1.4) & (f[:, :, 2] > f[:, :, 1] * 1.4) & (f[:, :, 2] > 35)
    check(f'{slug} 0 magenta', not (mag & op).any(), f'opaque={op.mean():.3f}')
    # 5. Nuit exacte.
    check(f'{slug} nuit == night(jour)',
          np.array_equal(np.array(Image.open(d / '08_falaise_nuit.png').convert('RGBA')),
                         np.array(night(terrain))))
    # 6. Compositions == re-assemblage.
    for mode, sky_f, sea_f, terr_f, cl_f, comp_f in [
            ('jour', '01_ciel_jour', '03_mer_jour', '07_falaise', '05_nuages_wrap_jour', 'composition_jour'),
            ('nuit', '02_ciel_nuit', '04_mer_nuit', '08_falaise_nuit', '06_nuages_wrap_nuit', 'composition_nuit')]:
        comp = Image.open(O / 'commun' / f'{sky_f}.png').convert('RGBA')
        strip = Image.open(O / 'commun' / f'{cl_f}.png').convert('RGBA')
        x = -manifest['cloud_offset_compo']
        while x < 768:
            comp.alpha_composite(strip, (round(x), manifest['cloud_y']))
            x += strip.width
        comp.alpha_composite(Image.open(O / 'commun' / f'{sea_f}.png').convert('RGBA'), (0, 0))
        comp.alpha_composite(Image.open(d / f'{terr_f}.png').convert('RGBA'), (0, 0))
        check(f'{slug} {comp_f} == re-assemblage',
              np.array_equal(np.array(comp), np.array(Image.open(d / f'{comp_f}.png').convert('RGBA'))))

report['result'] = 'PASS'
(O / 'verification.json').write_text(json.dumps(report, ensure_ascii=False, indent=2))
print(f"VERIFICATION V3 : PASS ({len(report['checks'])} controles)")
