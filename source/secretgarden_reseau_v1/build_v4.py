"""Secret Garden network V4: separate generated layouts for sol/chemin/fleurs/rochers.

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

R = Path(__file__).resolve().parents[2]
O = R / 'renders/secretgarden_reseau_v1'
SIZE = (512, 512)
V4_ROOMS = ['couloir_ns', 'salle_carrefour']


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
    chemin = apply_mask(layout(slug, 'chemin'), mask(sol))
    ground = mask(sol) | mask(chemin)
    # old vegetation clipped outside new ground
    old_arb = load(d / '03_arbres.png')
    old_bui = load(d / '04_buissons.png')
    arbres = apply_mask(old_arb, ~ground)
    buissons = apply_mask(old_bui, ~ground)
    veg = mask(arbres) | mask(buissons)
    rochers = apply_mask(layout(slug, 'rochers'), ground | veg)
    fleurs = apply_mask(layout(slug, 'fleurs'), ground | veg)
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
print('V4: 2 rooms rebuilt from separate layouts; 5 rooms V3 untouched')
