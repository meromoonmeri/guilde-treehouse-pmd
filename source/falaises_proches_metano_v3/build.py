"""Falaises proches Metano V3 : falaises REGENEREES au generateur (texture
Metano guidee par les references natives), integres comme V1 : detourage
magenta, nuit Abyss exacte, mer + nuages + ciels reutilises de la V2.
Scene 768x512.
"""
from pathlib import Path
import json
import hashlib
import shutil
import sys

import numpy as np
from PIL import Image

R = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(R / 'source'))
from cote_v4_abyss.night import night  # noqa: E402  (module pur)

O = R / 'renders/falaises_proches_metano_v3'
L = O / 'layouts'
V2 = R / 'renders/falaises_proches_metano_v2'
SCENE = (768, 512)
SEA_Y = 300
CLOUD_Y = 8
CLOUD_OFF = 1289
CLOUD_PERIOD = 2200
CLOUD_SPEED = 12


def load(p):
    return Image.open(p).convert('RGBA')


def save(im, p):
    p.parent.mkdir(parents=True, exist_ok=True)
    im.save(p)


def cover(im, size, gravity='center'):
    w, h = im.size
    s = max(size[0] / w, size[1] / h)
    im = im.resize((round(w * s), round(h * s)), Image.Resampling.NEAREST)
    x = {'left': 0, 'center': (im.width - size[0]) // 2, 'right': im.width - size[0]}[gravity]
    return im.crop((x, 0, x + size[0], size[1]))


def cut(im):
    a = np.array(im)
    f = a[:, :, :3].astype(float)
    m = (f[:, :, 0] > f[:, :, 1] * 1.4) & (f[:, :, 2] > f[:, :, 1] * 1.4) & (f[:, :, 2] > 35)
    a[m] = 0
    return Image.fromarray(a)


def tile_clouds(base, strip, off=0):
    x = -off
    while x < SCENE[0]:
        base.alpha_composite(strip, (round(x), CLOUD_Y))
        x += strip.width
    return base


variants = {
    'cap_gauche': {'raw': 'falaise_cap_gauche.png', 'title': 'Cap gauche', 'gravity': 'left'},
    'terrasse_droite': {'raw': 'falaise_terrasse_droite.png', 'title': 'Terrasse droite', 'gravity': 'right'},
}
shas = {n: hashlib.sha256((L / (n + '.png')).read_bytes()).hexdigest()
        for n in ['falaise_cap_gauche', 'falaise_terrasse_droite']}

# --- commun : copies V2 a l'octet (mer phase00, nuages, ciels, ocean 128ph) ---
(O / 'commun/ocean').mkdir(parents=True, exist_ok=True)
for n in ['01_ciel_jour', '02_ciel_nuit', '03_mer_jour', '04_mer_nuit',
          '05_nuages_wrap_jour', '06_nuages_wrap_nuit']:
    shutil.copyfile(V2 / 'commun' / (n + '.png'), O / 'commun' / (n + '.png'))
for p in (V2 / 'commun/ocean').glob('*.png'):
    shutil.copyfile(p, O / 'commun/ocean' / p.name)
shutil.copyfile(V2 / 'commun/ocean/palettes.json', O / 'commun/ocean/palettes.json')
sky_day = load(O / 'commun/01_ciel_jour.png')
sky_night = load(O / 'commun/02_ciel_nuit.png')
sea_canvas = load(O / 'commun/03_mer_jour.png')
sea_canvas_n = load(O / 'commun/04_mer_nuit.png')
cloud_day = load(O / 'commun/05_nuages_wrap_jour.png')
cloud_night = load(O / 'commun/06_nuages_wrap_nuit.png')

# --- audit texture : distance a la palette native (ref canon + V2) ---
ref = np.unique(np.array(Image.open(R / 'source/falaises_generees/reference_canonique.png')
                        .convert('RGB')).reshape(-1, 3), axis=0).astype(float)


def audit(im):
    a = np.array(im.convert('RGBA'))
    op = a[:, :, 3] > 0
    px = a[op][:, :3].astype(float)
    sample = px[np.random.RandomState(0).choice(len(px), 20000, replace=False)]
    d = np.sqrt(((sample[:, None, :] - ref[None, :, :]) ** 2).sum(-1)).min(1)
    exact = (d == 0).mean()
    return {'pct_le30': round(float((d <= 30).mean() * 100), 1), 'pct_exact': round(float(exact * 100), 2)}


manifest = {'scene': list(SCENE), 'sea_y': SEA_Y, 'cloud_period': CLOUD_PERIOD,
            'cloud_y': CLOUD_Y, 'cloud_offset_compo': CLOUD_OFF,
            'cloud_speed_px_s': CLOUD_SPEED,
            'commun_source': 'falaises_proches_metano_v2/commun (copies octet)',
            'layout_sha256': shas,
            'night': 'Abyss exact filter (cote_v4_abyss/night.py), single pass',
            'runtime_validated': False, 'variants': []}
for slug, v in variants.items():
    terrain = cut(cover(load(L / v['raw']), SCENE, v['gravity']))
    out = O / slug
    save(terrain, out / '07_falaise.png')
    save(night(terrain), out / '08_falaise_nuit.png')
    comp = tile_clouds(sky_day.copy(), cloud_day, CLOUD_OFF)
    comp.alpha_composite(sea_canvas, (0, 0))
    comp.alpha_composite(terrain, (0, 0))
    save(comp, out / 'composition_jour.png')
    compn = tile_clouds(sky_night.copy(), cloud_night, CLOUD_OFF)
    compn.alpha_composite(sea_canvas_n, (0, 0))
    compn.alpha_composite(load(out / '08_falaise_nuit.png'), (0, 0))
    save(compn, out / 'composition_nuit.png')
    manifest['variants'].append({'id': slug, 'title': v['title'], 'raw': v['raw'],
                                 'gravity': v['gravity'], 'audit_texture': audit(terrain)})
    print('PASS', slug, manifest['variants'][-1]['audit_texture'], flush=True)
(O / 'manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2))
board = Image.new('RGB', (1200, 560), '#101820')
for i, vv in enumerate(manifest['variants']):
    for j, suf in enumerate(['composition_jour.png', 'composition_nuit.png']):
        im = load(O / vv['id'] / suf).resize((384, 256), Image.Resampling.NEAREST)
        board.paste(im.convert('RGB'), (i * 600, j * 272 + 8))
save(board, O / 'PLANCHE.png')
print('V3 OK : 2 falaises generees texture Metano, commun V2 reutilise')
