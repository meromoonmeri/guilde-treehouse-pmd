"""Secret Garden V5: bare versions, rocks tilesheets, animated vegetation.

Per room (no new generations, existing pixels only):
- composition_nue.png / .gif : sol + chemin + fleurs (anim 4x200ms) + acces.
  No arbres/buissons/rochers/bordure.
- rochers_tilesheet.png + manifest : individual rock sprites (connected
  components), uniform cells, cols=8.
- vegetation/ : veg_f0..f3.png (arbres+buissons merged, sway dx 0/+1/0/-1,
  brightness 1/1.03/1/0.97, 200ms), vegetation_frames.png strip,
  buissons_spritesheet.png (rows=sprites, cols=4 frames) + manifest.
- composition_full_animee.gif : fleurs + vegetation moving, 4x200ms.
Plus global combined rocks + vegetation sheets at render root.
"""
from pathlib import Path
import json
import numpy as np
from PIL import Image
from scipy import ndimage

R = Path(__file__).resolve().parents[2]
O = R / 'renders/secretgarden_reseau_v1'
SIZE = (512, 512)
COLS = 8


def load(p):
    return Image.open(p).convert('RGBA')


def save(im, p):
    p.parent.mkdir(parents=True, exist_ok=True)
    im.save(p)


def mask(im):
    return np.array(im)[:, :, 3] > 0


def components(im, min_area=1):
    m = mask(im)
    lab, n = ndimage.label(m)
    out = []
    for i in range(1, n + 1):
        comp = lab == i
        area = int(comp.sum())
        if area < min_area:
            continue
        ys, xs = np.where(comp)
        out.append({'id': i, 'area': area,
                    'bbox': [int(xs.min()), int(ys.min()), int(xs.max()) + 1, int(ys.max()) + 1]})
    out.sort(key=lambda c: -c['area'])
    return out, lab


def sheet(cells, cols=COLS, cell=None):
    if cell is None:
        cell = (max(c.width for c in cells), max(c.height for c in cells))
    rows = (len(cells) + cols - 1) // cols
    png = Image.new('RGBA', (cols * cell[0], rows * cell[1]), (0, 0, 0, 0))
    rects = []
    for i, c in enumerate(cells):
        x, y = (i % cols) * cell[0], (i // cols) * cell[1]
        png.alpha_composite(c, (x, y))
        rects.append([x, y, c.width, c.height])
    return png, rects, cell


def shift(im, dx, br):
    a = np.array(im).copy()
    if dx > 0:
        a[:, dx:] = np.array(im)[:, :-dx]
        a[:, :dx] = 0
    elif dx < 0:
        a[:, :dx] = np.array(im)[:, -dx:]
        a[:, dx:] = 0
    a[:, :, :3] = np.clip(a[:, :, :3].astype(float) * br, 0, 255).astype('uint8')
    return Image.fromarray(a)


m = json.loads((O / 'manifest.json').read_text())
m['version'] = 5
m['v5_note'] = 'bare versions (sol+chemin+fleurs+acces), rocks tilesheets, animated vegetation 4x200ms'
all_rocks, all_bushes = [], []
for e in m['rooms']:
    slug = e['id']
    d = O / slug
    L = {n: load(d / (n + '.png')) for n in e['layers']}
    # ---- bare version (no arbres/buissons/rochers/bordure) ----
    acc = [n for n in L if n.startswith('08_acces')]
    ff = [load(d / 'fleurs' / f'06_fleurs_f{i}.png') for i in range(4)]
    fri = []
    for f in ff:
        c = Image.new('RGBA', SIZE)
        c.alpha_composite(L['01_sol'])
        c.alpha_composite(L['02_chemin'])
        c.alpha_composite(f)
        for n in acc:
            c.alpha_composite(L[n])
        fri.append(c)
    save(fri[0], d / 'composition_nue.png')
    fri = [c.convert('P', palette=Image.Palette.ADAPTIVE, colors=256) for c in fri]
    fri[0].save(d / 'composition_nue_animee.gif', save_all=True, append_images=fri[1:],
                duration=200, loop=0)
    # ---- rocks tilesheet ----
    rocks, rock_lab = components(L['05_rochers'], min_area=60)
    rarr = np.array(L['05_rochers'])
    rcells = []
    for c in rocks:
        x0, y0, x1, y1 = c['bbox']
        cell = rarr[y0:y1, x0:x1].copy()
        cell[rock_lab[y0:y1, x0:x1] != c['id']] = 0
        rcells.append(Image.fromarray(cell))
    rp, rrects, rcell = sheet(rcells)
    save(rp, d / 'rochers_tilesheet.png')
    (d / 'rochers_manifest.json').write_text(json.dumps(
        {'cell': list(rcell), 'cols': COLS, 'sprites': [
            {'bbox_src': c['bbox'], 'area': c['area'], 'rect_sheet': r} for c, r in zip(rocks, rrects)]},
        ensure_ascii=False, indent=1))
    # ---- animated vegetation (arbres+buissons merged) ----
    veg_static = Image.new('RGBA', SIZE)
    veg_static.alpha_composite(L['03_arbres'])
    veg_static.alpha_composite(L['04_buissons'])
    vdir = d / 'vegetation'
    vframes = [shift(veg_static, dx, br) for dx, br in [(0, 1.0), (1, 1.03), (0, 1.0), (-1, 0.97)]]
    for i, f in enumerate(vframes):
        save(f, vdir / f'veg_f{i}.png')
    strip = Image.new('RGBA', (512 * 4, 512), (0, 0, 0, 0))
    for i, f in enumerate(vframes):
        strip.alpha_composite(f, (i * 512, 0))
    save(strip, vdir / 'vegetation_frames.png')
    # bush sprites x frames grid
    _bushes, bush_lab = components(L['04_buissons'], min_area=50)
    bushes = [c for c in _bushes
              if max(c['bbox'][2] - c['bbox'][0], c['bbox'][3] - c['bbox'][1]) <= 128]
    for c in bushes:  # +1px margin: sway shifts content
        c['bbox'] = [max(0, c['bbox'][0] - 1), max(0, c['bbox'][1] - 1),
                     min(SIZE[0], c['bbox'][2] + 1), min(SIZE[1], c['bbox'][3] + 1)]
    bcell = [max(c['bbox'][2] - c['bbox'][0] for c in bushes),
             max(c['bbox'][3] - c['bbox'][1] for c in bushes)] if bushes else [8, 8]
    bpng = Image.new('RGBA', (4 * bcell[0], max(1, len(bushes)) * bcell[1]), (0, 0, 0, 0))
    dxs = [0, 1, 0, -1]
    for r, c in enumerate(bushes):
        x0, y0, x1, y1 = c['bbox']
        for i, f in enumerate(vframes):
            cell = np.array(f.crop((x0, y0, x1, y1))).copy()
            mk = (bush_lab == c['id'])[y0:y1, x0:x1].copy()
            dx = dxs[i]
            if dx > 0:
                mk[:, dx:] = mk[:, :-dx]
                mk[:, :dx] = False
            elif dx < 0:
                mk[:, :dx] = mk[:, -dx:]
                mk[:, dx:] = False
            cell[~mk] = 0
            bpng.alpha_composite(Image.fromarray(cell), (i * bcell[0], r * bcell[1]))
    save(bpng, vdir / 'buissons_spritesheet.png')
    (vdir / 'buissons_manifest.json').write_text(json.dumps(
        {'cell': bcell, 'cols_frames': 4, 'sprites': [
            {'bbox_src': c['bbox'], 'area': c['area'], 'row': r} for r, c in enumerate(bushes)]},
        ensure_ascii=False, indent=1))
    # ---- full animated GIF (flowers + vegetation) ----
    still = Image.new('RGBA', SIZE)
    for n in ['01_sol', '02_chemin', '05_rochers']:
        still.alpha_composite(L[n])
    full = []
    for i in range(4):
        c = still.copy()
        c.alpha_composite(vframes[i])
        c.alpha_composite(ff[i])
        c.alpha_composite(L['07_bordure_jungle'])
        for n in acc:
            c.alpha_composite(L[n])
        full.append(c.convert('P', palette=Image.Palette.ADAPTIVE, colors=256))
    full[0].save(d / 'composition_full_animee.gif', save_all=True, append_images=full[1:],
                 duration=200, loop=0)
    e['v5'] = {'nue': True, 'rochers_sprites': len(rocks),
               'rochers_px_kept_pct': round(sum(c['area'] for c in rocks) / max(1, mask(L['05_rochers']).sum()) * 100, 1), 'buissons_sprites': len(bushes),
               'veg_frames': 4, 'veg_cadence_ms': 200}
    all_rocks.append((slug, rarr, rock_lab, rocks))
    all_bushes.append((slug, L['04_buissons'], bushes))

# ---- global combined sheets ----
rcells = []
rman = []
for slug, rarr, rock_lab, rocks in all_rocks:
    for c in rocks:
        x0, y0, x1, y1 = c['bbox']
        cell = rarr[y0:y1, x0:x1].copy()
        cell[rock_lab[y0:y1, x0:x1] != c['id']] = 0
        rcells.append((slug, Image.fromarray(cell), c))
png, rects, cell = sheet([c for _, c, _ in rcells])
save(png, O / 'rochers_TOUTES_ZONES.png')
for (slug, _, c), r in zip(rcells, rects):
    rman.append({'zone': slug, 'bbox_src': c['bbox'], 'area': c['area'], 'rect_sheet': r})
(O / 'rochers_TOUTES_ZONES_manifest.json').write_text(json.dumps(
    {'cell': list(cell), 'cols': COLS, 'sprites': rman}, ensure_ascii=False, indent=1))
(O / 'manifest.json').write_text(json.dumps(m, ensure_ascii=False, indent=2))
nrock = sum(e['v5']['rochers_sprites'] for e in m['rooms'])
nbush = sum(e['v5']['buissons_sprites'] for e in m['rooms'])
print(f'V5: 7 bare versions+GIFs, {nrock} rock sprites, {nbush} bush sprites, veg 4x200ms, 7 full GIFs')
