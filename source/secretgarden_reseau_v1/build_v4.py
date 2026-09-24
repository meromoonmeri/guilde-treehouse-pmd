"""Secret Garden network V4: separate generated layouts for sol/chemin/fleurs/rochers.

Salvage rules (scripted, documented, same for every room they apply to):
- FLEURS_PARTITION rooms (generator copied grass+flowers): V3 petal color rule
  + neighbouring dark foliage (V4-bouquet), so 06 matches ns/carrefour bouquets.
- ROCHERS_PARTITION rooms (generator copied grass+rocks): neutral-gray cores
  + adjacent dark outlines, holes filled, components with >60 gray px kept.
- CHEMIN_SHIFT: rigid 8px-grid translations of chemin layouts to ports
  (same class as V1 cover/gravity repositioning), then clipped to sol.

Progressive upgrade, same layer names as V3. V4 rooms this run: couloir_ns,
salle_carrefour. Other rooms keep their V3 partition layers untouched.
Assembly rules (scripted, documented):
- chemin &= sol (track strictly on ground)
- old V3 vegetation (03/04) clipped to outside the new ground
- rochers/fleurs &= (new ground | clipped vegetation): nothing floats in the void
- stack order: sol < chemin < arbres < buissons < rochers < fleurs < bordure < acces
- border 07 + ports 08 reused byte-identical from V3; flowers re-animated (4x200ms)
"""
from pathlib import Path
import json, shutil, zipfile
import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage

R = Path(__file__).resolve().parents[2]
O = R / 'renders/secretgarden_reseau_v1'
SIZE = (512, 512)
V4_ROOMS = ['couloir_ns', 'salle_carrefour', 'couloir_ew', 'couloir_t',
            'salle_traversee', 'salle_laterale', 'carrefour_clairiere']
FLEURS_PARTITION = ['couloir_ew', 'couloir_t']
ROCHERS_PARTITION = ['salle_traversee', 'salle_laterale', 'carrefour_clairiere']
CHEMIN_SHIFT = {'salle_laterale': (-40, 0)}  # 512px space, 8px grid
ROCK_RULES = ['couloir_ew', 'couloir_t', 'salle_traversee', 'salle_laterale',
              'carrefour_clairiere']  # ns/carrefour = precedent approuve, fige
TRANSPLANT = {'couloir_t': {'src': 'couloir_ns', 'layer': '04_buissons', 'count': 6,
    'maxside': 64, 'minarea': 150,
    'anchors': [(8, 8), (64, 8), (8, 64), (448, 8), (392, 8), (448, 64),
                (144, 8), (312, 8), (8, 448), (64, 448), (8, 392),
                (448, 448), (384, 448), (448, 392)]}}


def load(p):
    return Image.open(p).convert('RGBA')


def save(im, p):
    p.parent.mkdir(parents=True, exist_ok=True)
    im.save(p)


def cut(im):
    a = np.array(im)
    f = a[:, :, :3].astype(float)
    m = (f[:, :, 0] > f[:, :, 1] * 1.4) & (f[:, :, 2] > f[:, :, 1] * 1.4) & (f[:, :, 2] > 35)
    a[m] = 0
    return Image.fromarray(a)


def square(im):
    w, h = im.size
    if w == h:
        return im
    s = max(w, h)
    sq = Image.new('RGBA', (s, s), (255, 0, 255, 255))
    sq.alpha_composite(im, ((s - w) // 2, (s - h) // 2))
    return sq


def layout(room, el):
    return cut(square(load(O / 'layouts' / room / f'{el}.png')).resize(SIZE, Image.Resampling.NEAREST))


def shift(im, dx, dy):
    a = np.array(im)
    a = np.roll(a, (dy, dx), axis=(0, 1))
    if dy > 0:
        a[:dy] = 0
    elif dy < 0:
        a[dy:] = 0
    if dx > 0:
        a[:, :dx] = 0
    elif dx < 0:
        a[:, dx:] = 0
    return Image.fromarray(a)


def partition_flowers(im):
    a = np.array(im.convert('RGBA'))
    R_, G_, B_ = a[:, :, 0].astype(int), a[:, :, 1].astype(int), a[:, :, 2].astype(int)
    opaque = a[:, :, 3] > 0
    petals = opaque & (((R_ > 200) & (G_ > 180) & (B_ > 150)) |
                      ((R_ > 200) & (G_ > 170) & (B_ < 140)) |
                      ((R_ > 190) & (G_ < 175) & (B_ > 130)))
    darkgreen = opaque & (G_ < 150) & (G_ > R_ + 10) & (G_ > B_ + 10) & (G_ > 40)
    leaves = darkgreen & ndimage.binary_dilation(petals, iterations=8)
    out = np.zeros_like(a)
    keep = petals | leaves
    out[keep] = a[keep]
    return Image.fromarray(out)


def filter_rocks(mask, chemin_mask):
    """R1: composantes 60..15000 px (ni poussiere ni sols/murs).
    R2: jamais sur le chemin fauche (dilate 4px) : pistes lisibles."""
    lab, n = ndimage.label(mask)
    if n:
        sizes = ndimage.sum(mask, lab, range(1, n + 1))
        for i, s in enumerate(sizes, 1):
            if s < 60 or s > 15000:
                mask &= lab != i
    mask &= ~ndimage.binary_dilation(chemin_mask, iterations=4)
    lab, n = ndimage.label(mask)
    if n:
        sizes = ndimage.sum(mask, lab, range(1, n + 1))
        for i, s in enumerate(sizes, 1):
            if s < 60:
                mask &= lab != i
    return mask


def transplant(slug, ground, veg_img):
    """V4 couloir_t: new ground covers all V3 vegetation (veg=0). Transplant the
    COUNT largest bush sprites from src 04 into fixed 8px-grid corner anchors
    (same generator pixels, scripted placement). Keeps veg-outside-ground."""
    spec = TRANSPLANT[slug]
    src = np.array(load(O / spec['src'] / (spec['layer'] + '.png')).convert('RGBA'))
    lab, n = ndimage.label(src[:, :, 3] > 0)
    sizes = ndimage.sum(src[:, :, 3] > 0, lab, range(1, n + 1))
    cand = []
    for i in range(1, n + 1):
        ys, xs = np.where(lab == i)
        w, h = xs.max() - xs.min() + 1, ys.max() - ys.min() + 1
        if max(w, h) <= spec['maxside'] and sizes[i - 1] >= spec['minarea']:
            cand.append(i)
    order = sorted(cand, key=lambda i: -sizes[i - 1])[:spec['count']]
    assert len(order) == spec['count'], (slug, len(order))
    dst = np.array(veg_img)
    placed = 0
    for i in order:
        ys, xs = np.where(lab == i)
        h, w = ys.max() - ys.min() + 1, xs.max() - xs.min() + 1
        spr = src[ys.min():ys.max() + 1, xs.min():xs.max() + 1].copy()
        spr[lab[ys.min():ys.max() + 1, xs.min():xs.max() + 1] != i] = 0
        for ax, ay in spec['anchors']:
            if ax + w > 512 or ay + h > 512:
                continue
            if ground[ay:ay + h, ax:ax + w][spr[:, :, 3] > 0].any():
                continue
            if dst[ay:ay + h, ax:ax + w, 3][spr[:, :, 3] > 0].any():
                continue
            dst[ay:ay + h, ax:ax + w][spr[:, :, 3] > 0] = spr[spr[:, :, 3] > 0]
            placed += 1
            break
    assert placed >= 4, (slug, placed)
    return Image.fromarray(dst)


def partition_rocks(im):
    a = np.array(im.convert('RGBA'))
    mx = a[:, :, :3].max(axis=2).astype(int)
    mn = a[:, :, :3].min(axis=2).astype(int)
    opaque = a[:, :, 3] > 0
    gray = opaque & (mx - mn < 28) & (mx >= 90) & (mx <= 215)
    dark = opaque & (mx - mn < 22) & (mx < 90)
    core = gray | (dark & ndimage.binary_dilation(gray, iterations=3))
    closed = ndimage.binary_closing(core, iterations=2)
    lab, n = ndimage.label(closed)
    keep = np.zeros_like(opaque)
    for i in range(1, n + 1):
        comp = lab == i
        if (gray & comp).sum() > 60:
            keep |= ndimage.binary_fill_holes(comp)
    out = np.zeros_like(a)
    out[keep] = a[keep]
    return Image.fromarray(out)


def mask(im):
    return np.array(im)[:, :, 3] > 0


def apply_mask(im, m):
    a = np.array(im)
    a[~m] = 0
    return Image.fromarray(a)


def flower_frames(f0):
    a = np.array(f0)
    out = []
    for dx, br in [(0, 1.0), (1, 1.06), (0, 1.0), (-1, 0.94)]:
        f = a.copy()
        if dx > 0:
            f[:, dx:] = a[:, :-dx]
            f[:, :dx] = 0
        elif dx < 0:
            f[:, :dx] = a[:, -dx:]
            f[:, dx:] = 0
        rgb = np.clip(f[:, :, :3].astype(float) * br, 0, 255).astype('uint8')
        f[:, :, :3] = rgb
        out.append(Image.fromarray(f))
    return out


m = json.loads((O / 'manifest.json').read_text())
m['version'] = 4
m['v4_note'] = 'separate generated layouts sol/chemin/fleurs/rochers; vegetation clipped outside new ground; nothing floats in void'
for e in m['rooms']:
    slug = e['id']
    d = O / slug
    if slug not in V4_ROOMS:
        e['source'] = 'v3_partition'
        continue
    e['source'] = 'v4_layouts'
    # new layouts
    sol = layout(slug, 'sol')
    ch_raw = layout(slug, 'chemin')
    dx, dy = CHEMIN_SHIFT.get(slug, (0, 0))
    if (dx, dy) != (0, 0):
        assert dx % 8 == 0 and dy % 8 == 0
        ch_raw = shift(ch_raw, dx, dy)
    chemin = apply_mask(ch_raw, mask(sol))
    ground = mask(sol) | mask(chemin)
    # old vegetation clipped outside new ground
    old_arb = load(d / '03_arbres.png')
    old_bui = load(d / '04_buissons.png')
    arbres = apply_mask(old_arb, ~ground)
    buissons = apply_mask(old_bui, ~ground)
    if slug in TRANSPLANT:
        buissons = transplant(slug, ground, buissons)
    veg = mask(arbres) | mask(buissons)
    ro_raw = layout(slug, 'rochers')
    if slug in ROCHERS_PARTITION:
        ro_raw = partition_rocks(ro_raw)
    rochers = apply_mask(ro_raw, ground | veg)
    if slug in ROCK_RULES:
        rm = mask(rochers)
        rochers = apply_mask(rochers, filter_rocks(rm, mask(chemin)))
    fl_raw = layout(slug, 'fleurs')
    if slug in FLEURS_PARTITION:
        fl_raw = partition_flowers(fl_raw)
    fleurs = apply_mask(fl_raw, ground | veg)
    # keep border/ports/schema from V3
    keep = {n: load(d / (n + '.png')) for n in e['layers'] if n.startswith('07_') or n.startswith('08_acces')}
    schema = load(d / 'schema.png')
    detoure_v3 = load(d / 'terrain_detoure.png')
    shutil.rmtree(d)
    d.mkdir()
    layers = {'01_sol': apply_mask(sol, ~mask(chemin)), '02_chemin': chemin,
              '03_arbres': arbres, '04_buissons': buissons,
              '05_rochers': rochers, '06_fleurs': fleurs, **keep}
    order = ['01_sol', '02_chemin', '03_arbres', '04_buissons', '05_rochers', '06_fleurs'] + sorted(keep)
    e['layers'] = order
    for n, im in layers.items():
        save(im, d / (n + '.png'))
    frames = flower_frames(fleurs)
    fdir = d / 'fleurs'
    for i, f in enumerate(frames):
        save(f, fdir / f'06_fleurs_f{i}.png')
    comp = Image.new('RGBA', SIZE)
    for n in order:
        comp.alpha_composite(layers[n])
    save(comp, d / 'composition.png')
    new_terrain = Image.new('RGBA', SIZE)
    for n in order[:6]:
        new_terrain.alpha_composite(layers[n])
    save(new_terrain, d / 'terrain_detoure.png')
    save(schema, d / 'schema.png')
    # animated GIF (flowers only move)
    still = Image.new('RGBA', SIZE)
    for n in order[:5]:
        still.alpha_composite(layers[n])
    for n in order[6:]:
        still.alpha_composite(layers[n])
    gif_frames = []
    for f in frames:
        c = still.copy()
        c.alpha_composite(f)
        gif_frames.append(c.convert('P', palette=Image.Palette.ADAPTIVE, colors=256))
    gif_frames[0].save(d / 'composition_animee.gif', save_all=True, append_images=gif_frames[1:],
                       duration=200, loop=0)
    with zipfile.ZipFile(d / (slug + '.ora'), 'w', zipfile.ZIP_DEFLATED) as z:
        z.writestr('mimetype', 'image/openraster')
        stack = ''.join(f'<layer name="{n}" src="data/{n}.png" x="0" y="0"/>' for n in order)
        z.writestr('stack.xml', f'<?xml version="1.0"?><image w="512" h="512"><stack name="root">{stack}</stack></image>')
        for n in order:
            z.write(d / (n + '.png'), f'data/{n}.png')
        z.write(d / 'composition.png', 'merged.png')
    # zone-constraint checks
    assert mask(chemin).sum() and (mask(chemin) & ~mask(sol)).sum() == 0, (slug, 'chemin')
    assert ((mask(arbres) | mask(buissons)) & ground).sum() == 0, (slug, 'veg')
    assert (mask(rochers) & ~(ground | veg)).sum() == 0, (slug, 'rochers')
    assert (mask(fleurs) & ~(ground | veg)).sum() == 0, (slug, 'fleurs')
    arr = np.array(comp)
    for p in e['ports']:
        dd = p['direction']
        band = arr[0:24, 224:288] if dd == 'N' else arr[-24:, 224:288] if dd == 'S' else arr[224:288, 0:24] if dd == 'W' else arr[224:288, -24:]
        assert np.all(band[:, :, 3] == 255), (slug, dd)
    e['flower_px'] = int(mask(fleurs).sum())
    e['checks'] = {'zone_constraints': True, 'ports_opaque_band': True}

(O / 'manifest.json').write_text(json.dumps(m, ensure_ascii=False, indent=2))
board = Image.new('RGB', (1400, 840), '#1d3320')
dr = ImageDraw.Draw(board)
for i, e in enumerate(m['rooms']):
    im = load(O / e['id'] / 'composition.png').resize((336, 336), Image.Resampling.NEAREST)
    x, y = (i % 4) * 350, (i // 4) * 420
    tag = 'V4' if e.get('source') == 'v4_layouts' else 'V3'
    board.paste(im, (x, y + 24), im)
    dr.text((x + 8, y + 5), f"[{tag}] {e['title']}", fill='white')
save(board, O / 'PLANCHE.png')
print('V4: 7 rooms rebuilt from separate layouts (shifts/partitions documented)')
