"""Sud -> nord V4 : entree aride + couloir violet, pixels natifs des references.

- Modules complets par translation (parois, bouches), jamais de mosaïque 8 px.
- Sols : quilting de patches natifs (recouvrement, sans fondu) + tampons controles.
- Nuit : filtre Abyss exact, une seule fois. Provenance NPZ par pixel.
"""
from pathlib import Path
import json
import hashlib
import sys
import xml.etree.ElementTree as ET

R = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(R))
sys.path.insert(0, str(R / 'source/cote_v4_abyss'))
import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage as nd
from source.zones_relayout_v1.build import seam
from night import night

OUT = R / 'exports/zones_south_north_v4'
FILES = ['entrancearidedungeonpmdsky.png', 'roadundergound.png']
A = [np.array(Image.open(R / p).convert('RGBA')) for p in FILES]
SHA = {p: hashlib.sha256((R / p).read_bytes()).hexdigest() for p in FILES}
PREFIX = 'SouthNorthV4'


class Map:
    def __init__(self, id, w, h):
        self.id = id
        self.W, self.H = w, h
        self.layers = []
        self.ops = []

    def layer(self, name):
        l = [name, np.zeros((self.H, self.W, 4), np.uint8),
             np.full((self.H, self.W, 3), -1, np.int16)]
        self.layers.append(l)
        return l

    def put(self, l, s, box, pos, punch=()):
        x0, y0, x1, y1 = box
        x, y = pos
        assert (x1 - x0) % 8 == 0 and (y1 - y0) % 8 == 0, (box, 'non 8px')
        assert x % 8 == 0 and y % 8 == 0, (pos, 'non 8px')
        p = A[s][y0:y1, x0:x1]
        hh, ww = p.shape[:2]
        assert x >= 0 and y >= 0 and x + ww <= self.W and y + hh <= self.H, (box, pos)
        mask = p[:, :, 3] > 0
        for (px0, py0, px1, py1) in punch:
            mask[py0 - y0:py1 - y0, px0 - x0:px1 - x0] = False
        sy, sx = np.mgrid[y0:y1, x0:x1]
        q = np.stack([np.full(sx.shape, s), sx, sy], 2)
        l[1][y:y + hh, x:x + ww][mask] = p[mask]
        l[2][y:y + hh, x:x + ww][mask] = q[mask]
        self.ops.append(dict(layer=l[0], source=FILES[s], rect=list(box),
                             position=list(pos), punch=[list(r) for r in punch]))

    def fill(self, l, s, boxes, mask=None, seed=11):
        W, H = self.W, self.H
        rng = np.random.default_rng(seed)
        mask = np.ones((H, W), bool) if mask is None else mask
        hh = boxes[0][3] - boxes[0][1]
        ww = boxes[0][2] - boxes[0][0]
        ov = min(8, hh // 2, ww // 2)
        for y in range(0, H, hh - ov):
            for x in range(0, W, ww - ov):
                h = min(hh, H - y)
                w = min(ww, W - x)
                want = mask[y:y + h, x:x + w]
                if not want.any():
                    continue
                old = l[1][y:y + h, x:x + w]
                occupied = (old[:, :, 3] > 0) & want
                best = None
                for idx in rng.permutation(len(boxes))[:24]:
                    x0, y0, _, _ = boxes[idx]
                    patch = A[s][y0:y0 + h, x0:x0 + w]
                    cost = ((old[:, :, :3].astype(float) - patch[:, :, :3]) ** 2).sum(2)
                    score = cost[occupied].mean() if occupied.any() else rng.random()
                    if best is None or score < best[0]:
                        best = (score, x0, y0, patch, cost)
                _, x0, y0, patch, cost = best
                take = want.copy()
                if x and w >= ov:
                    take[:, :ov] &= np.arange(ov)[None, :] >= seam(cost[:, :ov])[:, None]
                if y and h >= ov:
                    take[:ov, :] &= np.arange(ov)[:, None] >= seam(cost[:ov, :].T)[None, :]
                take |= want & (old[:, :, 3] == 0)
                sy, sx = np.mgrid[y0:y0 + h, x0:x0 + w]
                q = np.stack([np.full(sx.shape, s), sx, sy], 2)
                old[take] = patch[take]
                l[2][y:y + h, x:x + w][take] = q[take]
        self.ops.append(dict(layer=l[0], source=FILES[s], method='native ground patch overlap, no blending',
                             patch_count=len(boxes), patch_size=[ww, hh], seed=seed))

    def stamp(self, l, s, box, pos, ov=8):
        """Tampon controle (decor au sol) : interieur garde, coutures sur 4 bords."""
        x0, y0, x1, y1 = box
        x, y = pos
        p = A[s][y0:y1, x0:x1]
        hh, ww = p.shape[:2]
        assert x >= 0 and y >= 0 and x + ww <= self.W and y + hh <= self.H, (box, pos)
        old = l[1][y:y + hh, x:x + ww]
        cost = ((old[:, :, :3].astype(float) - p[:, :, :3]) ** 2).sum(2)
        take = np.ones((hh, ww), bool)
        if x > 0:
            take[:, :ov] &= np.arange(ov)[None, :] >= seam(cost[:, :ov])[:, None]
        if y > 0:
            take[:ov, :] &= np.arange(ov)[:, None] >= seam(cost[:ov, :].T)[None, :]
        if x + ww < self.W:
            cR = cost[:, ww - ov:][:, ::-1]
            keep = (ov - 1 - np.arange(ov)[None, :]) >= seam(cR)[:, None]
            take[:, ww - ov:] &= keep[:, ::-1]
        if y + hh < self.H:
            cB = cost[hh - ov:, :][::-1, :]
            keep = (ov - 1 - np.arange(ov)[:, None]) >= seam(cB.T)[None, :]
            take[hh - ov:, :] &= keep[::-1, :]
        sy, sx = np.mgrid[y0:y1, x0:x1]
        q = np.stack([np.full(sx.shape, s), sx, sy], 2)
        old[take] = p[take]
        l[2][y:y + hh, x:x + ww][take] = q[take]
        self.ops.append(dict(layer=l[0], source=FILES[s], method='controlled stamp, 4-side seam',
                             rect=list(box), position=list(pos)))

    def save(self, title, entrances, pathmask, notes):
        d = OUT / self.id
        d.mkdir(parents=True, exist_ok=True)
        W, H = self.W, self.H
        comp_j = Image.new('RGBA', (W, H))
        comp_n = Image.new('RGBA', (W, H))
        ls = []
        for name, a, q in self.layers:
            fj = f'{PREFIX}_{self.id}_{name}_jour.png'
            fn = f'{PREFIX}_{self.id}_{name}_nuit.png'
            imj = Image.fromarray(a)
            imn = night(imj)
            imj.save(d / fj)
            imn.save(d / fn)
            comp_j.alpha_composite(imj)
            comp_n.alpha_composite(imn)
            np.savez_compressed(d / (name + '_source.npz'), source_sxy=q)
            for f in (fj, fn):
                root = ET.Element('tileset', version='1.10', name=Path(f).stem,
                                  tilewidth='8', tileheight='8', columns=str(W // 8),
                                  tilecount=str(W // 8 * (H // 8)))
                ET.SubElement(root, 'image', source=f, width=str(W), height=str(H))
                ET.ElementTree(root).write(d / (Path(f).stem + '.tsx'),
                                           encoding='utf-8', xml_declaration=True)
            ls.append(dict(id=name, file_jour=fj, file_nuit=fn,
                           provenance=name + '_source.npz'))
        allowed = {l['file_jour'] for l in ls} | {l['file_nuit'] for l in ls} | \
            {l['provenance'] for l in ls} | \
            {Path(l['file_jour']).stem + '.tsx' for l in ls} | \
            {Path(l['file_nuit']).stem + '.tsx' for l in ls}
        for old in d.iterdir():
            if old.is_file() and old.name.startswith(PREFIX) and old.name not in allowed:
                old.unlink()
        comp_j.save(d / 'composite_jour.png')
        comp_n.save(d / 'composite_nuit.png')
        Image.fromarray(np.uint8(pathmask) * 255).save(d / 'path_connectivity_mask.png')
        review = comp_j.copy()
        dr = ImageDraw.Draw(review)
        for e in entrances:
            dr.ellipse((e[0] - 6, e[1] - 6, e[0] + 6, e[1] + 6),
                       outline=(255, 255, 0, 255), width=2)
        review.save(d / 'access_review_NOT_RUNTIME.png')
        return dict(id=self.id, title=title, size=[W, H], orientation='SOUTH_TO_NORTH',
                    entrances=entrances, layers=ls, operations=self.ops, notes=notes,
                    runtime='NOT TESTED', art_approved=False,
                    night='Abyss exact, applied once per layer',
                    connectivity='Pixel path mask continuity only, not engine collision or warp.')


def clean_boxes(s, x0, x1, y0, y1, w=24, h=16, lmin=0, lmax=255, smax=999, dmax=999,
                step=8, limit=48):
    a = A[s].astype(float)
    lum = a[:, :, :3].mean(2)
    boxes = []
    for yy in range(y0, y1 - h + 1, step):
        for xx in range(x0, x1 - w + 1, step):
            z = lum[yy:yy + h, xx:xx + w]
            if lmin <= z.mean() <= lmax and z.std() <= smax and (z < 150).sum() <= dmax:
                boxes.append((xx, yy, xx + w, yy + h))
    assert len(boxes) >= 8, (s, len(boxes))
    return boxes[:limit]


def arid():
    m = Map('arid_dungeon_entrance', 408, 560)
    sol = m.layer('01_sol')
    boxes = clean_boxes(0, 0, 408, 196, 280, lmin=180, lmax=215, smax=18, dmax=10)
    m.fill(sol, 0, boxes, seed=21)
    # Accents : arbres morts resserres + semis de cailloux, hors du passage.
    m.stamp(sol, 0, (16, 144, 56, 208), (16, 328))
    m.stamp(sol, 0, (344, 152, 376, 208), (336, 400))
    m.stamp(sol, 0, (296, 232, 328, 256), (112, 440))
    m.stamp(sol, 0, (128, 248, 160, 272), (264, 296))
    m.stamp(sol, 0, (184, 224, 216, 248), (240, 512))
    paroi = m.layer('02_paroi_nord')
    mouth = (176, 32, 240, 112)
    m.put(paroi, 0, (0, 0, 408, 208), (0, 0), punch=[mouth])
    bouche = m.layer('03_bouche')
    m.put(bouche, 0, mouth, (176, 32))
    yy, xx = np.mgrid[:560, :408]
    pm = (yy >= 88) & (np.abs(xx - 206) <= 34)
    return m.save('Entree aride — arrivee sud, grotte au nord', [[206, 90]], pm,
                  'Couronne nord 408x208 translatée (arbres hauts aplatis), bouche percée '
                  'sur calque dédié, couloir sable quilté + 5 tampons natifs (2 arbres, '
                  '3 semis de cailloux).')


def violet():
    m = Map('violet_underground_road', 504, 488)
    sol = m.layer('01_sol')
    boxes = clean_boxes(1, 144, 360, 160, 376, lmin=110, lmax=185, smax=30)
    m.fill(sol, 1, boxes, seed=22)
    # Eboulis re-quiltés le long du couloir (tampons de sol rocheux natif).
    m.stamp(sol, 1, (200, 200, 280, 264), (216, 240))
    m.stamp(sol, 1, (232, 296, 312, 360), (200, 400))
    m.stamp(sol, 1, (168, 160, 232, 208), (280, 160))
    paroi = m.layer('02_parois')
    mL, mR = (104, 72, 192, 152), (312, 72, 400, 152)
    m.put(paroi, 1, (0, 0, 504, 152), (0, 0), punch=[mL, mR])
    m.put(paroi, 1, (0, 152, 136, 408), (0, 152))
    m.put(paroi, 1, (368, 152, 504, 408), (368, 152))
    m.put(paroi, 1, (0, 272, 136, 352), (0, 408))
    m.put(paroi, 1, (368, 272, 504, 352), (368, 408))
    bouche = m.layer('03_bouches')
    m.put(bouche, 1, mL, (104, 72))
    m.put(bouche, 1, mR, (312, 72))
    yy, xx = np.mgrid[:488, :504].astype(float)
    pm = (yy >= 200) & (np.abs(xx - 252) <= 100)
    for cx in (148, 355):
        t = np.clip((220 - yy) / 80.0, 0, 1)
        mid = 252 + (cx - 252) * t
        pm |= (yy >= 140) & (yy <= 220) & (np.abs(xx - mid) <= 28)
    return m.save('Couloir violet — arrivee sud, deux bouches au nord (principale gauche)',
                  [[148, 140], [355, 140]], pm,
                  'Couronne + colonnes de parois translatées (coupes x=136/368), bouches '
                  'percées, sol du couloir re-quilté + 3 tampons d\'éboulis. Bouche gauche '
                  '= principale (documenté, pas de warp configuré).')


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    maps = [arid(), violet()]
    (OUT / 'manifest.json').write_text(json.dumps(
        dict(lot='zones_south_north_v4', sources=FILES, sha256=SHA, maps=maps),
        indent=1, ensure_ascii=False))
    for info in maps:
        print(info['id'], info['size'], 'calques:', len(info['layers']),
              'ops:', len(info['operations']))


if __name__ == '__main__':
    main()
