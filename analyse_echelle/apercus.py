# -*- coding: utf-8 -*-
"""
Planches de comparaison d'echelle : sprites Pokemon poses a 1:1 sur nos salles
et sur les salles de guilde de Halcyon, plus les gabarits recommandes.

Sorties : analyse_echelle/img/*.png
"""
import os, sys, glob, json, io
import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from rsread import load_ground, render_ground  # noqa: E402

REPO = os.path.dirname(HERE)
HALCYON = os.environ.get('HALCYON_DIR', '/home/user/halcyon')
IMG = os.path.join(HERE, 'img')
RENDERS = os.path.join(HERE, 'rendus_halcyon')
os.makedirs(IMG, exist_ok=True)
os.makedirs(RENDERS, exist_ok=True)

TILE = 24            # case PMD
BLOCK = 8            # bloc de collision ground map
VIEW = (320, 240)    # viewport logique de RogueEssence (cf. Content/UI/Title.png)
VOID = (26, 22, 33, 255)


# --------------------------------------------------------------- sprites

def sprite_from_chara(path):
    """Premiere frame utile d'un .chara (sprite Pokemon), rognee au contenu."""
    d = open(path, 'rb').read()
    o = d.find(b'\x89PNG\r\n\x1a\n')
    im = Image.open(io.BytesIO(d[o:])).convert('RGBA')
    im.load()
    a = np.array(im)[:, :, 3]

    def runs(v):
        out, s = [], None
        for i, x in enumerate(v > 0):
            if x and s is None:
                s = i
            elif not x and s is not None:
                out.append((s, i)); s = None
        if s is not None:
            out.append((s, len(v)))
        return out
    cr = runs(a.sum(axis=0))
    rr = runs(a.sum(axis=1))
    x0, x1 = cr[0]
    y0, y1 = rr[0]
    return im.crop((x0, y0, x1, y1))


def load_sprites():
    out = []
    for f in ('4.chara', '252.chara', '1.chara', '155.chara'):
        p = os.path.join(HALCYON, 'Content', 'Chara', f)
        if os.path.exists(p):
            out.append(sprite_from_chara(p))
    return out


def shadow(draw, cx, cy, w=14, h=5):
    draw.ellipse([cx - w // 2, cy - h // 2, cx + w // 2, cy + h // 2],
                 fill=(0, 0, 0, 70))


def put_sprite(canvas, spr, fx, fy):
    """Pose un sprite les pieds en (fx, fy)."""
    ov = Image.new('RGBA', canvas.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(ov)
    shadow(d, fx, fy, max(10, spr.width - 4), 5)
    canvas.alpha_composite(ov)
    canvas.alpha_composite(spr, (int(fx - spr.width / 2), int(fy - spr.height)))


# --------------------------------------------------------- masques de sol

def projet_floor(folder):
    p = os.path.join(REPO, 'calques', folder, 'jour', '01_sol.png')
    a = np.array(Image.open(p).convert('RGBA'))[:, :, 3] > 8
    lbl, n = ndimage.label(a)
    if n > 1:
        sizes = ndimage.sum(a, lbl, range(1, n + 1))
        a = lbl == (int(np.argmax(sizes)) + 1)
    return a


def halcyon_floor(name):
    g = load_ground(os.path.join(HALCYON, 'Data', 'Ground', name + '.rsground'))
    cache = os.path.join(RENDERS, name + '.png')
    render = Image.open(cache).convert('RGBA') if os.path.exists(cache) \
        else render_ground(g, HALCYON)
    if not os.path.exists(cache):
        render.save(cache)
    ob = g['obstacles']
    W, H = len(ob), len(ob[0])
    walk = np.zeros((H * BLOCK, W * BLOCK), dtype=bool)
    for x in range(W):
        for y in range(H):
            if ob[x][y]['Tags'] == 0:
                walk[y * BLOCK:(y + 1) * BLOCK, x * BLOCK:(x + 1) * BLOCK] = True
    fl = [L for L in g['Layers'] if 'Floor' in L['Name']] or g['Layers'][:1]
    floor = np.zeros((H, W), dtype=bool)
    for L in fl:
        T = L['Tiles']
        for x in range(W):
            for y in range(H):
                for sub in T[x][y]['Layers']:
                    if sub['Frames'][0]['Sheet']:
                        floor[y, x] = True
    walk &= np.kron(floor, np.ones((BLOCK, BLOCK), dtype=bool))
    rgba = np.array(render)
    body = rgba[:, :, 3] > 0
    border = np.concatenate([rgba[0, :, :3], rgba[-1, :, :3],
                             rgba[:, 0, :3], rgba[:, -1, :3]])
    cols, cnt = np.unique(border, axis=0, return_counts=True)
    dom = cols[int(np.argmax(cnt))]
    if cnt.max() > 0.5 * len(border):
        void = np.all(rgba[:, :, :3] == dom[None, None, :], axis=2) & (rgba[:, :, 3] > 0)
        if void.mean() > 0.02:
            body &= ~void
    walk &= ndimage.binary_closing(body, np.ones((3, 3), dtype=bool))
    ent = g['Entities'][0]
    seeds, entr = [], []
    for src in (ent['Markers'], ent['MapChars'], ent['GroundObjects'], ent['Spawners']):
        for o in src:
            c = o.get('Collider')
            if not c:
                continue
            pt = (int(c['Y'] + c['Height'] / 2), int(c['X'] + c['Width'] / 2))
            seeds.append(pt)
            if 'ntrance' in o.get('EntName', '') or 'pawn' in o.get('EntName', ''):
                entr.append(pt)
    lbl, n = ndimage.label(walk)
    sizes = ndimage.sum(walk, lbl, range(1, n + 1))

    def comps(pts):
        return {int(lbl[y, x]) for (y, x) in pts
                if 0 <= y < walk.shape[0] and 0 <= x < walk.shape[1] and lbl[y, x]}
    keep = comps(entr) or comps(seeds)
    if keep:
        top = max(sizes[c - 1] for c in keep)
        keep = {c for c in keep if sizes[c - 1] >= 0.15 * top}
    if not keep or max(sizes[c - 1] for c in keep) < 0.25 * sizes.max():
        keep = {int(np.argmax(sizes)) + 1}
    return np.isin(lbl, list(keep)), render


# ------------------------------------------------------------- placement

def spread_points(mask, k):
    """k points bien repartis sur le sol (maxima successifs de distance)."""
    dist = ndimage.distance_transform_edt(mask)
    pts = []
    work = dist.copy()
    for _ in range(k):
        idx = np.unravel_index(int(np.argmax(work)), work.shape)
        if work[idx] <= 0:
            break
        pts.append((int(idx[1]), int(idx[0])))
        yy, xx = np.ogrid[:work.shape[0], :work.shape[1]]
        work[((yy - idx[0]) ** 2 + (xx - idx[1]) ** 2) < 42 ** 2] = 0
    return pts


def annotate(canvas, text, xy=(4, 4), color=(255, 255, 255, 255)):
    d = ImageDraw.Draw(canvas)
    x, y = xy
    for dx, dy in ((-1, 0), (1, 0), (0, -1), (0, 1)):
        d.text((x + dx, y + dy), text, fill=(0, 0, 0, 255))
    d.text((x, y), text, fill=color)


def plate(bg, mask, sprites, label, show_view=True, tint=True):
    """Une vignette : image de la salle + zone jouable + sprites 1:1 + viewport."""
    c = Image.new('RGBA', bg.size, VOID)
    c.alpha_composite(bg)
    if tint:
        ov = np.zeros((bg.size[1], bg.size[0], 4), np.uint8)
        ov[mask] = (80, 255, 140, 46)
        c.alpha_composite(Image.fromarray(ov))
    for i, (px, py) in enumerate(spread_points(mask, len(sprites))):
        put_sprite(c, sprites[i % len(sprites)], px, py)
    d = ImageDraw.Draw(c)
    ys, xs = np.nonzero(mask)
    if len(xs):
        d.rectangle([xs.min(), ys.min(), xs.max(), ys.max()],
                    outline=(255, 220, 90, 200))
    if show_view:
        cx, cy = bg.size[0] // 2, bg.size[1] // 2
        d.rectangle([cx - VIEW[0] // 2, cy - VIEW[1] // 2,
                     cx + VIEW[0] // 2, cy + VIEW[1] // 2],
                    outline=(110, 190, 255, 230), width=2)
    annotate(c, label)
    return c


def contact_sheet(items, cols, path, scale=1, gap=10):
    w = max(i.size[0] for i in items)
    h = max(i.size[1] for i in items)
    rows = (len(items) + cols - 1) // cols
    sheet = Image.new('RGBA', (cols * (w + gap) + gap, rows * (h + gap) + gap),
                      (16, 14, 20, 255))
    for k, im in enumerate(items):
        r, c = divmod(k, cols)
        sheet.alpha_composite(im, (gap + c * (w + gap) + (w - im.size[0]) // 2,
                                   gap + r * (h + gap) + (h - im.size[1]) // 2))
    if scale != 1:
        sheet = sheet.resize((sheet.width * scale, sheet.height * scale), Image.NEAREST)
    sheet.convert('RGB').save(path)
    print('->', path)


# ------------------------------------------------------------- gabarits

def gabarit(cases_w, cases_h, titre, meubles, sprites, mur=1):
    """Dessine un gabarit de salle en cases de 24 px, mur compris."""
    W, H = cases_w * TILE, cases_h * TILE
    c = Image.new('RGBA', (W, H), (58, 40, 28, 255))
    d = ImageDraw.Draw(c)
    d.rectangle([mur * TILE, mur * TILE, W - mur * TILE - 1, H - mur * TILE - 1],
                fill=(150, 106, 62, 255))
    for x in range(0, W, TILE):
        d.line([(x, 0), (x, H)], fill=(0, 0, 0, 40))
    for y in range(0, H, TILE):
        d.line([(0, y), (W, y)], fill=(0, 0, 0, 40))
    for (mx, my, mw, mh, col) in meubles:
        d.rectangle([mx * TILE, my * TILE, (mx + mw) * TILE - 1, (my + mh) * TILE - 1],
                    fill=col, outline=(40, 28, 18, 255))
    for i, (sx, sy) in enumerate(sprites):
        put_sprite(c, SPRITES[i % len(SPRITES)], int(sx * TILE), int(sy * TILE))
    d.rectangle([0, 0, VIEW[0] - 1, VIEW[1] - 1], outline=(110, 190, 255, 230), width=2)
    annotate(c, titre)
    return c


SPRITES = []


def main():
    global SPRITES
    SPRITES = load_sprites()
    if not SPRITES:
        raise SystemExit('sprites introuvables : definir HALCYON_DIR')
    for i, s in enumerate(SPRITES):
        print('sprite', i, s.size)

    mes = json.load(io.open(os.path.join(HERE, 'mesures.json'), encoding='utf-8'))
    by_name = {m['nom']: m for m in mes['halcyon']}

    # --- planche Halcyon
    items = []
    for name in sorted(by_name):
        if not name.startswith('guild'):
            continue
        mask, render = halcyon_floor(name)
        m = by_name[name]
        lab = '%s\n%s x %s cases  %s cases2' % (
            name.replace('guild_', ''), m['bbox_sol_cases24'][0],
            m['bbox_sol_cases24'][1], m['aire_sol_cases24'])
        items.append(plate(render, mask, SPRITES, lab))
    contact_sheet(items, 4, os.path.join(IMG, 'halcyon_salles_1a1.png'))

    # --- planche projet
    kit = json.load(io.open(os.path.join(REPO, 'kit.json'), encoding='utf-8'))
    by_id = {m['id']: m for m in mes['projet']}
    items = []
    for s in kit['salles']:
        bg = Image.open(os.path.join(REPO, s['fichiers']['jour']['png'])).convert('RGBA')
        mask = projet_floor(s['dossier'])
        m = by_id[s['id']]
        lab = '%s %s\n%s x %s cases  %s cases2' % (
            s['id'], s['nom'], m['bbox_sol_cases24'][0],
            m['bbox_sol_cases24'][1], m['aire_sol_cases24'])
        items.append(plate(bg, mask, SPRITES, lab))
    contact_sheet(items, 3, os.path.join(IMG, 'projet_salles_1a1.png'))

    # --- comparaison directe, meme echelle pixel
    duo = []
    bg = Image.open(os.path.join(REPO, 'salles', '03_salle_commune',
                                 'salle_jour.png')).convert('RGBA')
    duo.append(plate(bg, projet_floor('03_salle_commune'), SPRITES,
                     'NOUS - Grande salle commune  648 x 432 px'))
    for name, lab in (('guild_second_floor', 'HALCYON - Second Floor (piece commune)'),
                      ('guild_top_left_bedroom', 'HALCYON - Chambre'),
                      ('guild_dining_room', 'HALCYON - Refectoire')):
        mask, render = halcyon_floor(name)
        duo.append(plate(render, mask, SPRITES, lab + '  %d x %d px' % render.size))
    contact_sheet(duo, 2, os.path.join(IMG, 'comparaison_1a1.png'))

    # --- simulation de reduction d'echelle
    sims = []
    for room, png, titre in (
            ('03_salle_commune', 'salles/03_salle_commune/salle_jour.png', 'Grande salle commune'),
            ('02_hall_missions', 'salles/02_hall_missions/salle_jour.png', 'Hall des missions')):
        bg0 = Image.open(os.path.join(REPO, png)).convert('RGBA')
        mask0 = projet_floor(room)
        for f in (1.0, 0.65, 0.5):
            if f == 1.0:
                bg, mask = bg0, mask0
            else:
                w, h = int(round(bg0.width * f)), int(round(bg0.height * f))
                bg = bg0.resize((w, h), Image.LANCZOS)
                mask = np.array(Image.fromarray(mask0.astype(np.uint8) * 255)
                                .resize((w, h), Image.NEAREST)) > 127
            aire = mask.sum() / float(TILE * TILE)
            lab = '%s  x%.2f  %d x %d px  (%.1f x %.1f cases)  sol %.0f cases2' % (
                titre, f, bg.width, bg.height, bg.width / TILE, bg.height / TILE, aire)
            sims.append(plate(bg, mask, SPRITES, lab))
    contact_sheet(sims, 3, os.path.join(IMG, 'simulation_reduction.png'))

    # --- gabarits recommandes
    bois = (120, 84, 48, 255); vert = (96, 150, 80, 255); tissu = (170, 120, 150, 255)
    g1 = gabarit(11, 9, 'CIBLE chambre 9 x 7 cases utiles', [
        (1, 1, 3, 2, bois), (7, 1, 3, 2, bois), (1, 6, 2, 2, bois),
        (8, 6, 2, 2, vert), (4.5 if False else 4, 4, 3, 2, tissu)],
        [(3, 4.4), (7.5, 6.5)])
    g2 = gabarit(14, 11, 'CIBLE salle commune 12 x 9 cases utiles', [
        (1, 1, 4, 2, bois), (9, 1, 4, 2, bois), (1, 8, 3, 2, vert),
        (10, 8, 3, 2, vert), (5, 4, 4, 3, tissu)],
        [(3.5, 4), (7, 8.5), (11, 4.5), (6, 3)])
    g3 = gabarit(18, 12, 'CIBLE grand hall 16 x 10 cases utiles', [
        (1, 1, 5, 2, bois), (12, 1, 5, 2, bois), (1, 9, 4, 2, vert),
        (13, 9, 4, 2, vert), (7, 5, 4, 3, tissu), (8, 1, 3, 2, bois)],
        [(4, 5), (9, 10), (14, 6), (12, 4)])
    contact_sheet([g1, g2, g3], 3, os.path.join(IMG, 'gabarits_cibles.png'), scale=2)


if __name__ == '__main__':
    main()
