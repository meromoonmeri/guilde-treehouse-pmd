"""Verification independante V2 : masques, pixels natifs, rejeu, nuit, mer, wrap."""
from pathlib import Path
import io
import json
import struct
import sys

import numpy as np
from PIL import Image

R = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(R / 'source'))
from cote_v4_abyss.night import night  # noqa: E402

HERE = Path(__file__).resolve().parent
O = R / 'renders/falaises_proches_metano_v2'
V1 = R / 'renders/falaises_proches_metano_v1'
OCEAN = R / 'renders/caps_terrasses_v3/ocean'
CLOUDS = R / 'sprites/cote_v2/COTEV2_NUAGES_WRAP.png'
NAMES = ['00_HERBE_NATIVE.png', '01_FACES_NATIVE.png', '02_RETOURS_NATIVE.png',
         '03_COURONNES_NATIVE.png', '04_PIEDS_NATIVE.png']
report = {'checks': []}


def check(name, ok, detail=''):
    report['checks'].append({'name': name, 'ok': bool(ok), 'detail': str(detail)})
    print(('PASS' if ok else 'FAIL'), name, detail, flush=True)
    if not ok:
        raise SystemExit(f'ECHEC: {name}')


def decode(path):
    raw = path.read_bytes()
    size, n = struct.unpack_from('<ii', raw)
    assert size == 8
    recs = [struct.unpack_from('<iiq', raw, 8 + i * 16) for i in range(n)]
    w = (max(x for x, y, a in recs) + 1) * 8
    h = (max(y for x, y, a in recs) + 1) * 8
    out = Image.new('RGBA', (w, h))
    cache = {}
    for x, y, a in recs:
        if a not in cache:
            (k,) = struct.unpack_from('<q', raw, a)
            cache[a] = Image.open(io.BytesIO(raw[a + 8:a + 8 + k])).convert('RGBA')
        out.paste(cache[a], (x * 8, y * 8))
    return np.array(out)


sheets = {n: decode(HERE / 'natifs_halcyon' / f'Metano_Town_{n}.tile')
          for n in ['Base', 'Cliffs']}
native = {n: {bytes(sheets[n][y:y + 8, x:x + 8].tobytes())
              for y in range(0, sheets[n].shape[0] - 7, 8)
              for x in range(0, sheets[n].shape[1] - 7, 8)} for n in sheets}
manifest = json.loads((O / 'manifest.json').read_text())
MODS = {k: (v['bank'], tuple(v['rect'])) for k, v in manifest['modules'].items()}

# 1. Mer : 128 phases, indices figes, = crop ocean, palettes conservees.
idx0 = np.array(Image.open(O / 'commun/ocean/jour_00.png'))
same_idx = True
same_src = True
for m in ['jour', 'nuit']:
    for i in range(64):
        ours = Image.open(O / 'commun/ocean' / f'{m}_{i:02d}.png')
        src = Image.open(OCEAN / f'{m}_{i:02d}.png').crop(tuple(manifest['sea_crop']))
        same_idx &= np.array_equal(np.array(ours), idx0)
        same_src &= (np.array_equal(np.array(ours), np.array(src))
                     and ours.getpalette() == src.getpalette()
                     and ours.info.get('transparency') == src.info.get('transparency'))
check('mer 128 phases indices figes', same_idx)
check('mer = crop ocean V2 exact (indices+palette+alpha)', same_src)
# nuit ocean == filtre 1 passe ? (heritage exactitude)
jn = Image.open(O / 'commun/ocean/jour_00.png').convert('RGBA')
nn = Image.open(O / 'commun/ocean/nuit_00.png').convert('RGBA')
check('mer nuit == night(mer jour)', np.array_equal(np.array(night(jn)), np.array(nn)))

# 2. Nuages : bytes sources, wrap, nuit exacte.
check('nuages jour == COTEV2 source',
      (O / 'commun/05_nuages_wrap_jour.png').read_bytes() == CLOUDS.read_bytes())
cl = np.array(Image.open(O / 'commun/05_nuages_wrap_jour.png').convert('RGBA'))
check('nuages wrap L==R 8px', np.array_equal(cl[:, :8], cl[:, -8:]),
      f'{cl.shape[1]}px @12px/s y=8')
check('nuages nuit == night(jour)',
      np.array_equal(np.array(Image.open(O / 'commun/06_nuages_wrap_nuit.png').convert('RGBA')),
                     np.array(night(Image.open(O / 'commun/05_nuages_wrap_jour.png')))))

# 3. Ciels = copies V1.
check('ciels == V1', all(
    (O / f'commun/0{i}_ciel_{m}.png').read_bytes() == (V1 / f'commun/0{i}_ciel_{m}.png').read_bytes()
    for i, m in [(1, 'jour'), (2, 'nuit')]))

# 4. Variantes.
for v in manifest['variants']:
    slug = v['id']
    d = O / slug
    mask = np.array(Image.open(V1 / slug / '07_falaise.png').convert('RGBA'))
    terrain = np.array(Image.open(d / 'TERRAIN.png').convert('RGBA'))
    check(f'{slug} alpha == masque V1', np.array_equal(terrain[:, :, 3], mask[:, :, 3]))
    check(f'{slug} nuit == night(jour)',
          np.array_equal(np.array(Image.open(d / 'TERRAIN_NUIT.png').convert('RGBA')),
                         np.array(night(Image.open(d / 'TERRAIN.png')))))
    for n in NAMES:
        check(f'{slug} {n} nuit == night(jour)',
              np.array_equal(np.array(Image.open(d / n.replace('.png', '_NUIT.png')).convert('RGBA')),
                             np.array(night(Image.open(d / n).convert('RGBA')))))
    # Rejeu des placements : chaque pixel opaque == pixel module source.
    h, w = terrain.shape[:2]
    rebuilt = [np.zeros((h, w, 4), dtype='uint8') for _ in NAMES]
    placements = json.loads((d / 'placements.json').read_text())
    for p in placements:
        bank, (sx, sy, ex, ey) = MODS[p['module']]
        x, y = p['dest']
        assert x % 8 == 0 and y % 8 == 0
        l, t = max(0, x), max(0, y)
        rr, bb = min(w, x + ex - sx), min(h, y + ey - sy)
        src = sheets[bank][sy + t - y:sy + bb - y, sx + l - x:sx + rr - x]
        layer = np.array(Image.open(d / NAMES[p['layer']]).convert('RGBA'))
        sel = (layer[t:bb, l:rr, 3] == 255) & (src[:, :, 3] == 255)
        if p['module'] == 'couronne':
            c = src.astype('int16')
            sel &= ~((c[:, :, 1] > c[:, :, 0] - 10) & (c[:, :, 1] - c[:, :, 2] > 60))
        if sel.any():
            # Semantique build : les tampons se recouvrent (couronnes/pieds
            # sur grille 32px, modules 64px), le dernier gagne.
            rebuilt[p['layer']][t:bb, l:rr][sel] = src[sel]
    layers_ok = all(np.array_equal(np.array(Image.open(d / n).convert('RGBA')), r)
                    for n, r in zip(NAMES, rebuilt))
    check(f'{slug} calques == rejeu placements ({len(placements)})', layers_ok)
    # Preuve pixel : tout pixel opaque vient d'un tampon (rejeu strict).
    # Les recouvrements (couronnes/pieds sur grille 32px) melangent des
    # sources dans une meme cellule 8x8 : les pixels restent natifs un par
    # un (prouve par le rejeu), la cellule n'est plus mono-source.
    touched = [np.zeros((h, w), bool) for _ in NAMES]
    srcid = [np.full((h, w), -1, dtype='int32') for _ in NAMES]
    for pid, p in enumerate(placements):
        bank, (sx, sy, ex, ey) = MODS[p['module']]
        x, y = p['dest']
        l, t = max(0, x), max(0, y)
        rr, bb = min(w, x + ex - sx), min(h, y + ey - sy)
        src = sheets[bank][sy + t - y:sy + bb - y, sx + l - x:sx + rr - x]
        layer = np.array(Image.open(d / NAMES[p['layer']]).convert('RGBA'))
        sel = (layer[t:bb, l:rr, 3] == 255) & (src[:, :, 3] == 255)
        if p['module'] == 'couronne':
            c = src.astype('int16')
            sel &= ~((c[:, :, 1] > c[:, :, 0] - 10) & (c[:, :, 1] - c[:, :, 2] > 60))
        touched[p['layer']][t:bb, l:rr][sel] = True
        srcid[p['layer']][t:bb, l:rr][sel] = pid
    pix_ok = all(np.array_equal(t, np.array(Image.open(d / n).convert('RGBA'))[:, :, 3] == 255)
                 for t, n in zip(touched, NAMES))
    check(f'{slug} pixels 100% natifs (rejeu strict)', pix_ok)
    mono = tot = 0
    for t, s in zip(touched, srcid):
        for yy in range(0, h, 8):
            for xx in range(0, w, 8):
                if t[yy:yy + 8, xx:xx + 8].all():
                    tot += 1
                    ids = s[yy:yy + 8, xx:xx + 8]
                    mono += (ids == ids[0, 0]).all()
    report['checks'].append({'name': f'{slug} cellules mono-source (info)',
                             'ok': True, 'detail': f'{mono}/{tot}'})
    print('INFO', slug, f'cellules mono-source {mono}/{tot}', flush=True)
    # Couronne sans verts (marche verte exclue).
    cr = np.array(Image.open(d / NAMES[3]).convert('RGBA')).astype('int16')
    op = cr[:, :, 3] > 0
    green = op & (cr[:, :, 1] > cr[:, :, 0] - 10) & (cr[:, :, 1] - cr[:, :, 2] > 60)
    check(f'{slug} couronne 0 vert', not green.any(), f'{int(green.sum())}px')
    # Compositions = ciel + nuages(off) + mer + terrain.
    for mode, sky_f, sea_f, terr_f, cl_f, comp_f in [
            ('jour', '01_ciel_jour', '03_mer_jour', 'TERRAIN', '05_nuages_wrap_jour', 'composition_jour'),
            ('nuit', '02_ciel_nuit', '04_mer_nuit', 'TERRAIN_NUIT', '06_nuages_wrap_nuit', 'composition_nuit')]:
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
print(f"VERIFICATION V2 : PASS ({len(report['checks'])} controles)")
