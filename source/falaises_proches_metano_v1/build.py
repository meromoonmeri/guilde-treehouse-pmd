"""Falaises proches Métano V1: 2 variantes, mer, ciel jour/nuit, nuages en wrap.

Layouts générés séparément (falaise / mer / ciel jour / ciel nuit / nuages),
normalisation uniforme cover-crop (jamais anisotrope), nuit par filtre Abyss
exact (source/cote_v4_abyss/night.py), nuages rendus périodiques par fondu.
Scène 768x512 (96x64 cellules 8px).
"""
from pathlib import Path
import json, hashlib, sys
import numpy as np
from PIL import Image

R = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(R / 'source'))
from cote_v4_abyss.night import night  # noqa: E402  (pure module, no side effects)
O = R / 'renders/falaises_proches_metano_v1'
L = O / 'layouts'
SCENE = (768, 512)
SEA_Y = 300
CLOUD_H = 300
BLEND = 120


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
    w = strip.width
    x = -off
    while x < SCENE[0]:
        base.alpha_composite(strip, (round(x), 0))
        x += w
    return base


def seamless(im, blend=BLEND):
    a = im.convert('RGBA')
    w, h = a.size
    n = np.array(a).astype(float)
    for x in range(blend):
        t = x / blend
        n[:, x] = n[:, x] * t + n[:, w - blend + x] * (1 - t)
    return Image.fromarray(n[:, :w - blend].astype('uint8'))


variants = {
    'cap_gauche': {'raw': 'falaise_cap_gauche.png', 'title': 'Cap gauche', 'gravity': 'left'},
    'terrasse_droite': {'raw': 'falaise_terrasse_droite.png', 'title': 'Terrasse droite', 'gravity': 'right'},
}
shas = {n: hashlib.sha256((L / (n + '.png')).read_bytes()).hexdigest()
        for n in ['falaise_cap_gauche', 'falaise_terrasse_droite', 'mer', 'ciel_jour', 'ciel_nuit', 'nuages_wrap']}
ref = R / 'source/falaises_generees/reference_canonique.png'
ref_sha = hashlib.sha256(ref.read_bytes()).hexdigest()

sky_day = cover(load(L / 'ciel_jour.png'), SCENE)
sky_night = cover(load(L / 'ciel_nuit.png'), SCENE)
sea_full = cover(load(L / 'mer.png'), SCENE)
sea_day = sea_full.crop((0, SEA_Y, SCENE[0], SCENE[1]))
sea_night = night(sea_day)
cloud_raw = load(L / 'nuages_wrap.png')
cw, ch = cloud_raw.size
cloud_s = cloud_raw.resize((round(cw * CLOUD_H / ch), CLOUD_H), Image.Resampling.NEAREST)
cloud_s = cut(cloud_s)
cloud_day = seamless(cloud_s)
cloud_night = night(cloud_day)
period = cloud_day.width

shared = {'01_ciel_jour': sky_day, '02_ciel_nuit': sky_night}
for n, im in shared.items():
    save(im, O / 'commun' / (n + '.png'))
sea_canvas = Image.new('RGBA', SCENE, (0, 0, 0, 0))
sea_canvas.alpha_composite(sea_day, (0, SEA_Y))
save(sea_canvas, O / 'commun' / '03_mer_jour.png')
sea_canvas_n = Image.new('RGBA', SCENE, (0, 0, 0, 0))
sea_canvas_n.alpha_composite(sea_night, (0, SEA_Y))
save(sea_canvas_n, O / 'commun' / '04_mer_nuit.png')
save(cloud_day, O / 'commun' / '05_nuages_wrap_jour.png')
save(cloud_night, O / 'commun' / '06_nuages_wrap_nuit.png')

manifest = {'scene': list(SCENE), 'sea_y': SEA_Y, 'cloud_period': period,
            'cloud_speed_px_s': 30, 'reference_sha256': ref_sha, 'layout_sha256': shas,
            'night': 'Abyss exact filter (cote_v4_abyss/night.py), single pass',
            'runtime_validated': False, 'variants': []}
for slug, v in variants.items():
    terrain = cut(cover(load(L / v['raw']), SCENE, v['gravity']))
    terrain_n = night(terrain)
    out = O / slug
    save(terrain, out / '07_falaise.png')
    save(terrain_n, out / '08_falaise_nuit.png')
    comp = tile_clouds(sky_day.copy(), cloud_day)
    comp.alpha_composite(sea_canvas, (0, 0))
    comp.alpha_composite(terrain, (0, 0))
    save(comp, out / 'composition_jour.png')
    compn = tile_clouds(sky_night.copy(), cloud_night)
    compn.alpha_composite(sea_canvas_n, (0, 0))
    compn.alpha_composite(terrain_n, (0, 0))
    save(compn, out / 'composition_nuit.png')
    manifest['variants'].append({'id': slug, 'title': v['title'], 'raw': v['raw'],
                                 'gravity': v['gravity']})
(O / 'manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2))
board = Image.new('RGB', (1200, 560), '#101820')
for i, v in enumerate(manifest['variants']):
    for j, suf in enumerate(['composition_jour.png', 'composition_nuit.png']):
        im = load(O / v['id'] / suf).resize((384, 256), Image.Resampling.NEAREST)
        board.paste(im.convert('RGB'), (i * 600, j * 272 + 8))
save(board, O / 'PLANCHE.png')
print(f'2 variantes 768x512; wrap period {period}px @30px/s; nuit Abyss exacte')
