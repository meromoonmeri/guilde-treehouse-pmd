"""Composition exacte des calques de « Lisière fleurie V1 » à partir des modules natifs.

Chaque pixel écrit est copié depuis une feuille native (translation seule) et sa source
(feuille, x, y) est enregistrée dans un tableau de provenance par calque.
"""
from __future__ import annotations

import numpy as np

from modules import (CLIFF_H, FLOWER_SEQUENCE, SHEET_ID, TREE_TRUNK_OFFSET, build_modules,
                     cliff_columns, load_sheets)

LAYERS = [
    ('01', 'sol', 'Herbe Vast Steppe (motif natif 32 px)'),
    ('02', 'corniche', 'Corniche rocheuse, couloir et sortie lumineuse (Cliifs)'),
    ('03', 'vegetation_basse', 'Touffes et galets praticables (Objects_Under)'),
    ('04', 'fleurs', 'Fleurs animées natives (pose affichée)'),
    ('05', 'troncs_rochers', 'Troncs avec leur ombre d’herbe native, gros rochers (Objects)'),
    ('06', 'canopees', 'Canopées au-dessus du joueur (Fringe, Layer 4)'),
]


class Canvas:
    def __init__(self, w, h):
        self.w, self.h = w, h
        self.rgba = np.zeros((h, w, 4), np.uint8)
        self.sheet = np.full((h, w), -1, np.int16)
        self.sx = np.zeros((h, w), np.int16)
        self.sy = np.zeros((h, w), np.int16)

    def put(self, sheets, sheet, sx0, sy0, mask, dx, dy):
        """Copie les pixels masqués de la feuille (sx0, sy0) vers (dx, dy), ordre du peintre."""
        h, w = mask.shape
        src = sheets[sheet][sy0:sy0 + h, sx0:sx0 + w]
        ys, xs = np.nonzero(mask & (src[..., 3] > 0))
        ty, tx = ys + dy, xs + dx
        ok = (ty >= 0) & (ty < self.h) & (tx >= 0) & (tx < self.w)
        ys, xs, ty, tx = ys[ok], xs[ok], ty[ok], tx[ok]
        self.rgba[ty, tx] = src[ys, xs]
        self.sheet[ty, tx] = SHEET_ID[sheet]
        self.sx[ty, tx] = xs + sx0
        self.sy[ty, tx] = ys + sy0
        return int(ok.sum())


def compose(layout, sheets=None, mods=None):
    sheets = sheets or load_sheets()
    mods = mods or build_modules(sheets)
    W, H = layout['size']
    out = {}

    # 01 sol : motif natif périodique 32x32 (16 tuiles uniques, vérifié), recopié sans rupture de phase.
    sol = Canvas(W, H)
    full = np.ones((32, 32), bool)
    for y in range(0, H, 32):
        for x in range(0, W, 32):
            sol.put(sheets, 'Vast_Steppe_Base', 0, 0, full[:min(32, H - y), :min(32, W - x)], x, y)
    out['sol'] = sol

    # 02 corniche : colonnes natives (bande cyclique, raccord natif x=511|0) translatées.
    cor = Canvas(W, H)
    cols = cliff_columns(W, layout['corridor_x'])
    src = sheets['Vast_Steppe_Cliifs']
    for dx, sx in enumerate(cols):
        col = np.zeros((CLIFF_H, 1), bool)
        col[:, 0] = src[:CLIFF_H, sx, 3] > 0
        cor.put(sheets, 'Vast_Steppe_Cliifs', int(sx), 0, col, dx, layout.get('cliff_y', 0))
    out['corniche'] = cor
    out['_cliff_cols'] = cols

    # 03 végétation basse, 05 troncs/rochers, 06 canopées : modules complets, ordre nord -> sud.
    veg, obj, fri = Canvas(W, H), Canvas(W, H), Canvas(W, H)
    items = []
    for name, x, y in layout['small']:
        items.append((y + mods[name].h, 0, 'veg', name, x, y))
    for name, x, y in layout['rocks']:
        items.append((y + mods[name].h, 1, 'obj', name, x, y))
    for x, y in layout['trees']:
        tx, ty = x + TREE_TRUNK_OFFSET[0], y + TREE_TRUNK_OFFSET[1]
        items.append((ty + mods['tronc'].h, 1, 'obj', 'tronc', tx, ty))
        items.append((ty + mods['tronc'].h, 2, 'fri', 'canopee', x, y))
    target = {'veg': veg, 'obj': obj, 'fri': fri}
    for _, _, lay, name, x, y in sorted(items):
        m = mods[name]
        assert x % 8 == 0 and y % 8 == 0, (name, x, y)
        target[lay].put(sheets, m.sheet, m.sx, m.sy, m.mask, x, y)
    out['vegetation_basse'], out['troncs_rochers'], out['canopees'] = veg, obj, fri

    # 04 fleurs : une toile par pose native (0, 1, 2) ; le composite montre la pose 0.
    poses = []
    fl = sheets['Vast_Steppe_Flower_Animations']
    for pose in range(3):
        c = Canvas(W, H)
        for x, y, clock in layout['flowers']:
            assert x % 8 == 0 and y % 8 == 0
            m = fl[0:24, pose * 24:pose * 24 + 24, 3] > 0
            c.put(sheets, 'Vast_Steppe_Flower_Animations', pose * 24, 0, m, x, y)
        poses.append(c)
    out['fleurs_poses'] = poses
    out['fleurs'] = poses[FLOWER_SEQUENCE[0]]
    return out
