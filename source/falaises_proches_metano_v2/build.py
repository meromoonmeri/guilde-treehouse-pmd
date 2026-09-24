"""Falaises proches Metano V2 : 2 variantes reconstruites en modules natifs Halcyon.

Masques approuves V1 (alpha exacte conservee), deco roses/roche echantillonnees
en rectangles coherents (herbe 128x128, face/retour 64x48, couronne/pied 64x16),
translations sur grille 8px, pixels clips par masque, jamais deformes.
Mer = crop de l'ocean V2 reutilise (64+64 phases P, indices fixes).
Nuages = strip COTEV2 reutilise (2200px, y=8, 12px/s).
Nuit = 1 passe du filtre Abyss exact (prouve == Night.tile, cf prepare.py).
Scene 768x512 (96x64 cellules 8px).
"""
from pathlib import Path
import io
import json
import hashlib
import struct
import sys

import numpy as np
from PIL import Image
from scipy import ndimage

R = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(R / 'source'))
from cote_v4_abyss.night import night  # noqa: E402  (module pur, sans effet)

HERE = Path(__file__).resolve().parent
O = R / 'renders/falaises_proches_metano_v2'
V1 = R / 'renders/falaises_proches_metano_v1'
OCEAN = R / 'renders/caps_terrasses_v3/ocean'
CLOUDS = R / 'sprites/cote_v2/COTEV2_NUAGES_WRAP.png'
SCENE = (768, 512)
SEA_Y = 300
SEA_CROP = (272, 370, 1040, 582)  # candidat A : houle lointaine + calme proche
CLOUD_Y = 8
CLOUD_SPEED = 12
NAMES = ['00_HERBE_NATIVE.png', '01_FACES_NATIVE.png', '02_RETOURS_NATIVE.png',
         '03_COURONNES_NATIVE.png', '04_PIEDS_NATIVE.png']
MODULES = {'herbe': ('Base', (0, 640, 128, 768)),
           'face': ('Cliffs', (912, 464, 976, 512)),
           'retour': ('Cliffs', (680, 464, 744, 512)),
           'couronne': ('Cliffs', (912, 448, 976, 464)),
           'pied': ('Cliffs', (912, 528, 976, 544))}


def decode(path):
    raw = path.read_bytes()
    size, n = struct.unpack_from('<ii', raw)
    assert size == 8
    records = [struct.unpack_from('<iiq', raw, 8 + i * 16) for i in range(n)]
    w = (max(x for x, y, a in records) + 1) * 8
    h = (max(y for x, y, a in records) + 1) * 8
    out = Image.new('RGBA', (w, h))
    cache = {}
    for x, y, a in records:
        if a not in cache:
            (k,) = struct.unpack_from('<q', raw, a)
            cache[a] = Image.open(io.BytesIO(raw[a + 8:a + 8 + k])).convert('RGBA')
        out.paste(cache[a], (x * 8, y * 8))
    return np.array(out)


def runs(row, gap=0):
    ids = np.flatnonzero(row)
    if not len(ids):
        return []
    return [(int(g[0]), int(g[-1]) + 1)
            for g in np.split(ids, np.flatnonzero(np.diff(ids) > gap + 1) + 1)]


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


sheets = {n: decode(HERE / 'natifs_halcyon' / f'Metano_Town_{n}.tile')
          for n in ['Base', 'Cliffs']}

# Preuve nuit : night() == filtre Abyss de reference sur toutes les couleurs source.
sys.path.insert(0, str(R / 'source/cote_v4_abyss'))
import tile_night_reference as reference  # noqa: E402
colors = np.unique(np.concatenate([v.reshape(-1, 4) for v in sheets.values()]), axis=0)
swatch = Image.fromarray(colors.reshape(1, -1, 4))
buf = io.BytesIO()
swatch.save(buf, format='PNG')
expected = Image.open(io.BytesIO(reference.to_night(buf.getvalue()))).convert('RGBA')
assert night(swatch).tobytes() == expected.tobytes(), 'night != reference Abyss'

# --- commun : ciels V1, mer reutilisee, nuages reutilises ---
(O / 'commun').mkdir(parents=True, exist_ok=True)
sky_day = Image.open(V1 / 'commun/01_ciel_jour.png').convert('RGBA')
sky_night = Image.open(V1 / 'commun/02_ciel_nuit.png').convert('RGBA')
assert sky_day.size == SCENE and sky_night.size == SCENE
import shutil
shutil.copyfile(V1 / 'commun/01_ciel_jour.png', O / 'commun/01_ciel_jour.png')
shutil.copyfile(V1 / 'commun/02_ciel_nuit.png', O / 'commun/02_ciel_nuit.png')

(O / 'commun/ocean').mkdir(parents=True, exist_ok=True)
sea_palettes = {}
for mode in ['jour', 'nuit']:
    sea_palettes[mode] = []
    for i in range(64):
        ph = Image.open(OCEAN / f'{mode}_{i:02d}.png')
        assert ph.mode == 'P', (mode, i)
        crop = ph.crop(SEA_CROP)
        assert crop.size == (SCENE[0], SCENE[1] - SEA_Y)
        crop.save(O / 'commun/ocean' / f'{mode}_{i:02d}.png')
        sea_palettes[mode].append(crop.getpalette())
(O / 'commun/ocean/palettes.json').write_text(json.dumps(sea_palettes))
# indices figes sur les 128 phases (meme crop) :
idx0 = np.array(Image.open(O / 'commun/ocean/jour_00.png'))
assert all(np.array_equal(np.array(Image.open(O / 'commun/ocean' / f'{m}_{i:02d}.png')), idx0)
           for m in ['jour', 'nuit'] for i in range(64)), 'indices ocean non figes'
# aucune transparence dans le crop (mer pleine) :
tr = Image.open(O / 'commun/ocean/jour_00.png').info.get('transparency', b'\xff')
tra = tr if isinstance(tr, bytes) else bytes([tr])
assert all(tra[v] != 0 for v in np.unique(idx0)), 'trou transparent dans la mer'
sea0 = Image.open(O / 'commun/ocean/jour_00.png').convert('RGBA')
sea0n = Image.open(O / 'commun/ocean/nuit_00.png').convert('RGBA')
sea_canvas = Image.new('RGBA', SCENE, (0, 0, 0, 0))
sea_canvas.alpha_composite(sea0, (0, SEA_Y))
sea_canvas.save(O / 'commun/03_mer_jour.png')
sea_canvas_n = Image.new('RGBA', SCENE, (0, 0, 0, 0))
sea_canvas_n.alpha_composite(sea0n, (0, SEA_Y))
sea_canvas_n.save(O / 'commun/04_mer_nuit.png')

cloud_day = Image.open(CLOUDS).convert('RGBA')
assert cloud_day.size == (2200, 344)
a = np.array(cloud_day)
assert np.array_equal(a[:, :8], a[:, -8:]), 'raccord strip nuages'
cloud_night = night(cloud_day)
import shutil
shutil.copyfile(CLOUDS, O / 'commun/05_nuages_wrap_jour.png')  # octet pour octet
cloud_night.save(O / 'commun/06_nuages_wrap_nuit.png')


CLOUD_OFF = 1289  # fenetre 768px la plus chargee (52% de la masse nuageuse)


def tile_clouds(base, strip, off=0):
    x = -off
    while x < SCENE[0]:
        base.alpha_composite(strip, (round(x), CLOUD_Y))
        x += strip.width
    return base


# --- variantes : masques V1 + tampons natifs ---
variants = {'cap_gauche': 'Cap gauche', 'terrasse_droite': 'Terrasse droite'}
manifest = {'scene': list(SCENE), 'sea_y': SEA_Y, 'sea_crop': list(SEA_CROP),
            'sea_source': 'renders/caps_terrasses_v3/ocean (64+64 phases P reutilisees)',
            'cloud_source': 'sprites/cote_v2/COTEV2_NUAGES_WRAP.png',
            'cloud_period': 2200, 'cloud_y': CLOUD_Y,
            'cloud_speed_px_s': CLOUD_SPEED,
            'cloud_offset_compo': CLOUD_OFF,
            'sky_source': 'falaises_proches_metano_v1/commun (01/02 recopies)',
            'mask_source': 'falaises_proches_metano_v1/{variante}/07_falaise.png (alpha exacte)',
            'grass_rule': 'g>=r-8 et g-b>60 ; îlots roche detaches <2000px reclasses herbe',
            'modules': {k: {'bank': b, 'rect': list(r)} for k, (b, r) in MODULES.items()},
            'night': 'Abyss exact filter (cote_v4_abyss/night.py), single pass',
            'runtime_validated': False, 'variants': []}
for slug, title in variants.items():
    mask_src = V1 / slug / '07_falaise.png'
    original = np.array(Image.open(mask_src).convert('RGBA'))
    h, w = original.shape[:2]
    assert (w, h) == SCENE
    land = original[:, :, 3] > 0
    r, g, b = (original[:, :, i].astype('int16') for i in range(3))
    grass = land & (g >= r - 8) & (g - b > 60)
    rock = land & ~grass
    # Nettoyage : îlots roche détachés (fleurs/debris du guide) -> herbe.
    # Règle : ne survit que la masse principale + tout îlot ≥2000px ou
    # touchant la masse dilatée de 3px (frange organique conservée).
    lab, n = ndimage.label(rock)
    sizes = ndimage.sum(np.ones_like(lab), lab, range(1, n + 1))
    main = int(np.argmax(sizes)) + 1
    near = ndimage.binary_dilation(lab == main, iterations=3)
    for i, s in enumerate(sizes, 1):
        if i != main and (s < 2000 and not (near & (lab == i)).any()):
            grass[lab == i] = True
    rock = land & ~grass
    arrays = [np.zeros((h, w, 4), dtype='uint8') for _ in NAMES]
    placements = []

    def stamp(layer, module, x, y, mask):
        assert x % 8 == 0 and y % 8 == 0
        bank, rect = MODULES[module]
        sx, sy, ex, ey = rect
        mw, mh = ex - sx, ey - sy
        left, top = max(0, x), max(0, y)
        right, bottom = min(w, x + mw), min(h, y + mh)
        if right <= left or bottom <= top:
            return
        source = sheets[bank][sy + top - y:sy + bottom - y, sx + left - x:sx + right - x]
        selected = mask[top:bottom, left:right] & (source[:, :, 3] == 255)
        if module == 'couronne':
            c = source.astype('int16')
            selected &= ~((c[:, :, 1] > c[:, :, 0] - 10) & (c[:, :, 1] - c[:, :, 2] > 60))
        if not selected.any():
            return
        arrays[layer][top:bottom, left:right][selected] = source[selected]
        placements.append({'layer': layer, 'module': module, 'dest': [x, y]})

    for y in range(0, h, 128):
        for x in range(0, w, 128):
            stamp(0, 'herbe', x, y, grass)
    for y in range(0, h, 48):
        for x in range(0, w, 64):
            stamp(1, 'face', x, y, rock)
    for y in range(0, h, 48):
        row = rock[y:min(h, y + 48)].mean(axis=0) > .55
        for left, right in runs(row, gap=8):
            if right - left < 40:
                continue
            xs = [left // 8 * 8]
            if right - left >= 160:
                xs.append((right - 64) // 8 * 8)
            for x in xs:
                stamp(2, 'retour', x, y, rock)
    for x in range(0, w, 32):
        col = rock[:, x:min(w, x + 32)].mean(axis=1) > .4
        for top, bottom in runs(col, gap=8):
            if bottom - top < 24:
                continue
            stamp(3, 'couronne', x, top // 8 * 8, rock)
            if bottom < h:
                stamp(4, 'pied', x, (bottom // 8) * 8 - 16, rock)
    dest = O / slug
    dest.mkdir(parents=True, exist_ok=True)
    scene = Image.new('RGBA', (w, h))
    for name, arr in zip(NAMES, arrays):
        im = Image.fromarray(arr)
        im.save(dest / name, optimize=True)
        night(im).save(dest / name.replace('.png', '_NUIT.png'), optimize=True)
        scene = Image.alpha_composite(scene, im)
    assert np.array_equal(np.array(scene)[:, :, 3], original[:, :, 3]), slug
    scene.save(dest / 'TERRAIN.png', optimize=True)
    night(scene).save(dest / 'TERRAIN_NUIT.png', optimize=True)
    # Reproductibilité : rejouer les placements redonne les calques.
    rebuilt = [np.zeros_like(x) for x in arrays]
    for p in placements:
        bank, (sx, sy, ex, ey) = MODULES[p['module']]
        x, y = p['dest']
        l, t = max(0, x), max(0, y)
        rr, bb = min(w, x + ex - sx), min(h, y + ey - sy)
        src = sheets[bank][sy + t - y:sy + bb - y, sx + l - x:sx + rr - x]
        select = (grass if p['layer'] == 0 else rock)[t:bb, l:rr] & (src[:, :, 3] == 255)
        if p['module'] == 'couronne':
            c = src.astype('int16')
            select &= ~((c[:, :, 1] > c[:, :, 0] - 10) & (c[:, :, 1] - c[:, :, 2] > 60))
        rebuilt[p['layer']][t:bb, l:rr][select] = src[select]
    assert all(np.array_equal(x, y) for x, y in zip(arrays, rebuilt)), slug
    (dest / 'placements.json').write_text(json.dumps(placements, separators=(',', ':')))
    comp = tile_clouds(sky_day.copy(), cloud_day, CLOUD_OFF)
    comp.alpha_composite(sea_canvas, (0, 0))
    comp.alpha_composite(scene, (0, 0))
    comp.save(dest / 'composition_jour.png')
    compn = tile_clouds(sky_night.copy(), cloud_night, CLOUD_OFF)
    compn.alpha_composite(sea_canvas_n, (0, 0))
    compn.alpha_composite(Image.open(dest / 'TERRAIN_NUIT.png'), (0, 0))
    compn.save(dest / 'composition_nuit.png')
    counts = {}
    for p in placements:
        counts[p['module']] = counts.get(p['module'], 0) + 1
    manifest['variants'].append(
        {'id': slug, 'title': title, 'mask_sha256': sha(mask_src), 'placements': counts,
         'terrain_sha256': sha(dest / 'TERRAIN.png')})
    print('PASS', slug, 'native modules', len(placements), counts, flush=True)

(O / 'manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2))
board = Image.new('RGB', (1200, 560), '#101820')
for i, v in enumerate(manifest['variants']):
    for j, suf in enumerate(['composition_jour.png', 'composition_nuit.png']):
        im = Image.open(O / v['id'] / suf).convert('RGBA').resize((384, 256), Image.NEAREST)
        board.paste(im.convert('RGB'), (i * 600, j * 272 + 8))
board.save(O / 'PLANCHE.png')
print('V2 OK : 2 terrains natifs, mer reutilisee 64ph, nuages 2200px @12px/s')
