"""Layout de « Lisière fleurie V1 » (768 x 896 px, grille 8 px).

Composition : arrivée au sud, grande prairie fleurie bordée à l'ouest par une lisière de forêt
ondulante (avancée, anse fleurie profonde, retour), bosquets à l'est, corniche rocheuse native sur
toute la largeur percée d'un passage qui mène, par le couloir natif, à la sortie lumineuse au nord.
Seules les positions sont nouvelles ; tous les pixels sont des modules natifs translatés.

Coordonnées = origine tuile (coin haut-gauche, multiple de 8) de chaque module :
  arbre   -> origine de la canopée ; le tronc natif suit à (+24, +48) ;
  rocher, touffe, galet -> origine du module ; fleur -> origine du bloc 24x24.

Les éléments bas sont DEMANDÉS à une position approximative (intention de composition) puis
RÉSOLUS vers la position valide la plus proche : entièrement visibles (hors canopées), sans
chevauchement de tronc, de corniche ni d'un autre élément (cellules 8x8 disjointes).
"""
from __future__ import annotations

import random

import numpy as np

from checks import cells, footprint
from modules import TREE_TRUNK_OFFSET

W, H = 768, 896
CORRIDOR_X = 256          # colonne de destination du couloir natif (colonnes natives 152..359)
SEED = 7
CLOCKS = (8, 10, 14)


def interp(points, v):
    for (a, ea), (b, eb) in zip(points, points[1:]):
        if a <= v <= b:
            return ea + (eb - ea) * (v - a) / (b - a)
    return points[0][1] if v < points[0][0] else points[-1][1]


# Lisière ouest : la forêt occupe les bases de tronc (x + 64, y + 92) à gauche de cette courbe.
# 300-500 : avancée vers l'est ; 600-800 : anse fleurie profonde ; 820+ : retour vers l'arrivée.
WEST_EDGE = [(300, 150), (360, 200), (430, 250), (500, 262), (556, 226), (600, 150),
             (640, 84), (690, 40), (760, 40), (810, 120), (850, 230), (900, 300), (960, 320)]


def region(bx, by):
    if by <= 208:                                   # bande nord, de part et d'autre du couloir
        return bx <= 236 or bx >= 500
    if by < 322:                                    # pas de tronc sur/contre la corniche
        return False
    if bx <= interp(WEST_EDGE, by):                 # grande lisière ouest
        return True
    if by <= 420 and bx >= 632:                     # bosquet est sous la corniche
        return True
    if by >= 800 and bx >= 604 + (880 - by) * 1.1:  # retour de forêt au sud-est
        return True
    return False


# Arbres isolés posés à la main (origine canopée).
LONE_TREES = [
    (512, 480),   # repère au centre-est de la prairie
    (600, 680),   # avant-poste du retour de forêt sud-est
    (184, 792),   # sentinelle qui ferme l'anse au sud
]
REMOVED = set()


def trees(seed=SEED):
    rng = random.Random(seed)
    out = []
    for r, y in enumerate(range(-48, H - 24, 40)):
        off = 48 if r % 2 else 0
        for x in range(-72 + off, W, 96):
            X = x + rng.choice([-16, -8, 0, 8, 16])
            Y = y + rng.choice([-8, 0, 0, 8])
            X, Y = X // 8 * 8, Y // 8 * 8
            if region(X + 64, Y + 92) and (X, Y) not in REMOVED:
                out.append((X, Y))
    return out + LONE_TREES


# ---- Demandes d'éléments bas (positions approximatives = intention) ----
ROCKS = [
    ('rocher_b', 200, 296),   # pied de corniche, ouest du passage
    ('rocher_a', 456, 296),   # pied de corniche, est du passage
    ('rocher_a', 608, 584),   # au pied du repère centre-est
    ('rocher_b', 336, 800),   # flanc ouest de l'arrivée
    ('rocher_a', 200, 184),   # bande nord, près du couloir
]

# Massifs de fleurs : (centre x, centre y, nombre de touffes, étalement px).
FLOWER_PATCHES = [
    (112, 720, 9, 56),    # anse fleurie (cœur du lieu)
    (200, 664, 4, 32),    # anse, entrée
    (272, 452, 3, 28),    # le long de l'avancée
    (240, 560, 3, 28),    # pointe de l'avancée
    (360, 316, 3, 28),    # bouche du passage
    (236, 120, 2, 24),    # bande nord ouest, contre le couloir
    (472, 150, 2, 24),    # bande nord est, contre le couloir
    (392, 540, 3, 40),    # traînée centrale
    (468, 612, 2, 28),    # traînée centrale sud
    (560, 424, 3, 28),    # lisière du bosquet est
    (672, 548, 2, 28),    # est, sous le repère
    (448, 820, 4, 40),    # accueil de l'arrivée
    (300, 700, 2, 24),    # sortie de l'anse
]

SMALL = [
    ('touffe_a', 312, 312), ('galet_a', 424, 344), ('touffe_b', 520, 312), ('galet_b', 280, 368),
    ('touffe_b', 560, 480), ('touffe_a', 648, 456), ('galet_a', 392, 432), ('touffe_a', 312, 488),
    ('galet_b', 472, 560), ('touffe_b', 648, 608), ('galet_a', 544, 640), ('touffe_a', 392, 640),
    ('touffe_b', 208, 600), ('galet_b', 232, 744), ('touffe_a', 312, 736), ('galet_a', 424, 752),
    ('touffe_b', 520, 760), ('touffe_a', 440, 872), ('galet_b', 520, 856), ('touffe_b', 368, 864),
    ('touffe_a', 216, 168), ('galet_a', 496, 184), ('touffe_b', 704, 520), ('galet_b', 696, 640),
    ('touffe_a', 64, 648), ('galet_a', 40, 776), ('touffe_b', 160, 832),
]


class Occupancy:
    """Masques de ce qui est déjà posé : canopées, troncs, corniche, cellules prises."""

    def __init__(self, canopy, trunk, cliff):
        self.canopy, self.trunk, self.cliff = canopy, trunk, cliff
        self.taken = set()
        self.blocking = np.zeros_like(canopy)

    def valid(self, mask, x, y, extra_gap=0):
        h, w = mask.shape
        if x < 0 or y < 0 or x + w > W or y + h > H:
            return False
        region_ = (self.canopy | self.trunk | self.cliff)[y:y + h, x:x + w]
        if (region_ & mask).any():
            return False
        cs = cells(x - extra_gap, y - extra_gap, w + 2 * extra_gap, h + 2 * extra_gap)
        return not (cs & self.taken)

    def take(self, mask, x, y):
        self.taken |= cells(x, y, mask.shape[1], mask.shape[0])


def spiral(cx, cy, radius):
    pts = [(dx, dy) for dx in range(-radius, radius + 1, 8) for dy in range(-radius, radius + 1, 8)]
    return sorted(pts, key=lambda p: (p[0] ** 2 + p[1] ** 2, p[1], p[0]))


def resolve(req, trunk_mask, canopy_mask, cliff_mask, mods, sheets, seed=SEED):
    occ = Occupancy(canopy_mask, trunk_mask, cliff_mask)
    rng = random.Random(seed + 1)
    rocks, flowers, small, log = [], [], [], []

    def place(kind, name, x, y, radius=64, gap=0):
        mask, _ = footprint(mods, sheets, kind, name, 0, 0)
        for dx, dy in spiral(x // 8 * 8, y // 8 * 8, radius):
            X, Y = x // 8 * 8 + dx, y // 8 * 8 + dy
            if occ.valid(mask, X, Y, gap):
                occ.take(mask, X, Y)
                return X, Y
        log.append(f'impossible : {name} près de {(x, y)}')
        return None

    for name, x, y in req['rocks']:
        p = place('rock', name, x, y, gap=8)
        if p:
            rocks.append((name, *p))
    clock_i = 0
    for cx, cy, n, spread in req['flower_patches']:
        got = 0
        for _ in range(n * 30):
            if got == n:
                break
            ang = rng.uniform(0, 6.2832)
            rad = spread * (rng.random() ** 0.7)
            x = int(cx + rad * np.cos(ang)) - 12
            y = int(cy + rad * 0.8 * np.sin(ang)) - 12
            mask, _ = footprint(mods, sheets, 'flower', 'fleur', 0, 0)
            X, Y = x // 8 * 8, y // 8 * 8
            if occ.valid(mask, X, Y):
                occ.take(mask, X, Y)
                flowers.append((X, Y, CLOCKS[clock_i % 3]))
                clock_i += 1
                got += 1
        if got < n:
            log.append(f'massif {(cx, cy)} : {got}/{n} touffes posées')
    for name, x, y in req['small']:
        p = place('small', name, x, y, radius=40)
        if p:
            small.append((name, *p))
    return rocks, flowers, small, log


def make_request(seed=SEED):
    return {
        'size': (W, H),
        'corridor_x': CORRIDOR_X,
        'trees': trees(seed),
        'rocks': ROCKS,
        'flower_patches': FLOWER_PATCHES,
        'small': SMALL,
        'arrival': (456, 864),     # marqueur d'entrée 16x16 (sud, face au nord)
    }


def make_layout(seed=SEED, sheets=None, mods=None):
    """Compose d'abord arbres + corniche, puis résout les éléments bas contre ces masques."""
    from compose import compose
    from modules import build_modules, load_sheets
    sheets = sheets or load_sheets()
    mods = mods or build_modules(sheets)
    req = make_request(seed)
    base = dict(req, rocks=[], small=[], flowers=[])
    out = compose(base, sheets, mods)
    trunk = out['troncs_rochers'].rgba[..., 3] > 0
    canopy = out['canopees'].rgba[..., 3] > 0
    cliff = out['corniche'].rgba[..., 3] > 0
    rocks, flowers, small, log = resolve(req, trunk, canopy, cliff, mods, sheets, seed)
    lay = dict(base, rocks=rocks, flowers=flowers, small=small)
    lay.pop('flower_patches', None)
    lay['resolve_log'] = log
    return lay
