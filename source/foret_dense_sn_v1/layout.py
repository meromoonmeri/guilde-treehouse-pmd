"""Layout de FDENSE_V1 — entrée de forêt dense, arrivée sud → entrée de donjon au nord.

Carte 512×672 (64×84 cases de 8 px). Toutes les formes sont des masques/champs lisses ; la matière
(pixels) vient ensuite de la synthèse canonique ou des sprites retouchés.
Ce module n'écrit aucun fichier à l'import.
"""
from __future__ import annotations

import numpy as np
from scipy import ndimage as ndi
from scipy.interpolate import PchipInterpolator

W, H = 512, 672

# bords des parois (y, x) — ondulés, plus serrés au nord (entrée), plus ouverts au sud (arrivée)
LEFT_EDGE = [(0, 184), (60, 186), (120, 178), (170, 158), (230, 132), (300, 118), (360, 126),
             (430, 110), (520, 96), (600, 86), (672, 80)]
RIGHT_EDGE = [(0, 328), (60, 326), (120, 334), (170, 354), (230, 380), (300, 394), (360, 386),
              (430, 402), (520, 414), (600, 426), (672, 434)]
# ligne médiane du chemin (y, x) et demi-largeur (y, r)
PATH_CENTER = [(672, 240), (600, 248), (530, 266), (470, 276), (410, 268), (350, 250), (290, 240),
               (240, 246), (200, 254), (150, 256)]
PATH_HALF = [(672, 23), (560, 24), (440, 25), (330, 24), (240, 22), (190, 21), (150, 20)]
# parois périodiques exactes (strips.py) : (décalage horizontal, phase verticale)
WALLS = {"ouest": (-20, 0), "est": (20, 96)}
# entrée du donjon (sprite retouché), bouche du tunnel
ENTRANCE_BOX = (128, 0, 384, 208)  # x0, y0, x1, y1
ENTRANCE_MOUTH = (256, 168)
# arbres géants : (nom, x_centre_tronc, y_base_racines, côté)
FEATURE_TREES = [("arbre_ouest", 104, 468, "ouest"), ("arbre_est", 420, 650, "est")]
# rochers : (nom, x_centre, y_base)
ROCKS = [("rocher_a", 150, 548), ("rocher_b", 372, 292), ("rocher_c", 322, 410)]
# fleurs canoniques : (x_centre, y_centre)
FLOWERS = [(196, 300), (340, 250), (180, 470), (330, 560), (206, 600), (360, 380), (164, 214), (318, 470)]
# petits buissons canoniques de B : (x_centre, y_centre)
BUSHES = [(212, 380), (312, 516), (228, 648)]
# premier plan : canopées qui entrent par le bas (ellipses cx, cy, rx, ry)
FOREGROUND = [(30, 712, 150, 74), (500, 716, 130, 66)]


def _curve(points, n):
    ys = np.array([p[0] for p in points], float)
    vs = np.array([p[1] for p in points], float)
    o = np.argsort(ys)
    f = PchipInterpolator(ys[o], vs[o])
    return f(np.arange(n))


def smoothstep(e0, e1, x):
    t = np.clip((x - e0) / (e1 - e0), 0, 1)
    return t * t * (3 - 2 * t)


def build_layout():
    yy, xx = np.mgrid[0:H, 0:W]
    xl = _curve(LEFT_EDGE, H)
    xr = _curve(RIGHT_EDGE, H)
    wall_l = xx < xl[:, None]
    wall_r = xx >= xr[:, None]
    fg = np.zeros((H, W), bool)
    for cx, cy, rx, ry in FOREGROUND:
        fg |= ((xx - cx) / rx) ** 2 + ((yy - cy) / ry) ** 2 <= 1.0
    fg &= ~(wall_l | wall_r)
    # chemin : union de disques le long de la ligne médiane
    cxs = _curve(PATH_CENTER, H + 1)
    hr = _curve(PATH_HALF, H + 1)
    path = np.zeros((H, W), bool)
    y_top = min(p[0] for p in PATH_CENTER)
    for y in np.arange(y_top, H + 1, 0.5):
        yi = int(round(y))
        cx, r = cxs[min(yi, H)], hr[min(yi, H)]
        y0, y1 = max(0, int(y - r - 1)), min(H, int(y + r + 2))
        x0, x1 = max(0, int(cx - r - 1)), min(W, int(cx + r + 2))
        sub = (yy[y0:y1, x0:x1] - y) ** 2 + (xx[y0:y1, x0:x1] - cx) ** 2 <= r * r
        path[y0:y1, x0:x1] |= sub
    # ombre : cercle sombre devant l'entrée + pénombre des parois
    ex, ey = ENTRANCE_MOUTH
    ell = np.sqrt(((xx - ex) / 172.0) ** 2 + ((yy - (ey - 18)) / 112.0) ** 2)
    s_entr = 1.0 - smoothstep(0.78, 1.0, ell)
    walls = wall_l | wall_r
    d_wall = ndi.distance_transform_edt(~walls)
    s_wall = 0.0 * d_wall  # pénombre des parois abandonnée (bandes visibles) : liseré canonique des parois suffit
    shade = np.maximum(s_entr, s_wall).astype(np.float32)
    # derrière l'entrée : herbe d'ombre partout (aucun interstice clair entre parois et entrée)
    x0, y0, x1, y1 = ENTRANCE_BOX
    behind = (yy < y1 - 24) & (xx >= x0 - 24) & (xx < x1 + 24)
    shade[behind] = 1.0
    return {
        "wall_l": wall_l, "wall_r": wall_r, "foreground": fg, "path": path, "shade": shade,
        "xl": xl, "xr": xr, "path_cx": cxs, "path_hr": hr,
    }


def debug_image(lay) -> np.ndarray:
    img = np.zeros((H, W, 3), np.uint8)
    img[:] = (70, 150, 50)
    s = lay["shade"][..., None]
    img = (img * (1 - 0.6 * s)).astype(np.uint8)
    img[lay["path"]] = (200, 150, 60)
    img[lay["wall_l"] | lay["wall_r"]] = (30, 70, 30)
    img[lay["foreground"]] = (10, 40, 10)
    x0, y0, x1, y1 = ENTRANCE_BOX
    img[y0:y1, x0:x0 + 2] = img[y0:y1, x1 - 2:x1] = (255, 0, 255)
    img[y1 - 2:y1, x0:x1] = (255, 0, 255)
    for _, x, y, _s in FEATURE_TREES:
        img[max(0, y - 190):y, max(0, x - 90):x + 90][::8, :] = (120, 220, 90)
        img[y - 4:y, x - 30:x + 30] = (140, 90, 40)
    for _, x, y in ROCKS:
        img[y - 14:y, x - 12:x + 12] = (150, 150, 150)
    for x, y in FLOWERS:
        img[y - 4:y + 4, x - 4:x + 4] = (250, 150, 200)
    for x, y in BUSHES:
        img[y - 6:y + 6, x - 7:x + 7] = (10, 60, 70)
    return img
