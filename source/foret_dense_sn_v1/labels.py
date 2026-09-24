"""Étiquettes de matière par pixel des deux références canoniques (D24P11A = A, D24P31A = B).

Chaque pixel reçoit une classe ; les images synthétisées héritent des classes via la provenance
(id_source, y, x), ce qui permet de découper les calques au pixel près sans deviner.

Classes :
  0 HERBE          herbe au soleil
  1 HERBE_SOMBRE   herbe à l'ombre (cercle sombre de B, pénombre)
  2 MUR            canopée + troncs + racines des parois d'arbres
  3 CHEMIN         terre / pavés du chemin (orange) et son liseré
  4 FLEUR          fleurs
  5 ROCHER         rochers gris
  6 BUISSON        petits buissons sombres de B
  7 TUNNEL         passage sombre / pavés gris de A (non utilisé comme source de sol)
  8 CANOPEE_A      canopées et troncs de A (non utilisés comme source de sol)
Ce module n'écrit aucun fichier à l'import.
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
from PIL import Image
from scipy import ndimage as ndi

HERE = Path(__file__).resolve().parent
REFS = {0: HERE / "refs" / "D24P11A.png", 1: HERE / "refs" / "D24P31A.png"}
NAMES = {0: "D24P11A", 1: "D24P31A"}
HERBE, HERBE_SOMBRE, MUR, CHEMIN, FLEUR, ROCHER, BUISSON, TUNNEL, CANOPEE_A = range(9)
CLASS_NAMES = ["herbe", "herbe_sombre", "mur", "chemin", "fleur", "rocher", "buisson", "tunnel", "canopee_A"]


def load_ref(sid: int) -> np.ndarray:
    return np.array(Image.open(REFS[sid]).convert("RGB")).astype(np.int16)


def _key(a: np.ndarray) -> np.ndarray:
    a = a.astype(np.int64)
    return (a[..., 0] << 16) | (a[..., 1] << 8) | a[..., 2]


def _hsv(a: np.ndarray):
    f = a.astype(np.float32) / 255.0
    mx, mn = f.max(-1), f.min(-1)
    r, g, b = f[..., 0], f[..., 1], f[..., 2]
    return mx, mn, r, g, b


def _is_orange(a):
    r, g, b = a[..., 0].astype(int), a[..., 1].astype(int), a[..., 2].astype(int)
    return (r >= 0x8f) & (r > g + 16) & (g > b + 24)


def _is_gray(a):
    r, g, b = a[..., 0].astype(int), a[..., 1].astype(int), a[..., 2].astype(int)
    mx = np.maximum(np.maximum(r, g), b)
    mn = np.minimum(np.minimum(r, g), b)
    return (mx - mn <= 16) & (mx >= 0x40)


def _exclusive_vote(k: np.ndarray, zones: dict[int, np.ndarray], thr: float = 0.95, win: int = 7):
    """Classe chaque couleur exclusive d'une zone, puis vote de voisinage pour les ambiguës."""
    from collections import Counter
    counts = {c: Counter(k[m].tolist()) for c, m in zones.items()}
    colors = set().union(*[set(v) for v in counts.values()])
    lab = np.full(k.shape, -1, np.int16)
    for col in colors:
        tot = sum(counts[c].get(col, 0) for c in zones)
        for c in zones:
            if counts[c].get(col, 0) / tot >= thr:
                lab[k == col] = c
    # vote : pour chaque pixel ambigu, classe majoritaire dans une fenêtre
    classes = list(zones)
    dens = np.stack([ndi.uniform_filter((lab == c).astype(np.float32), win) for c in classes])
    amb = lab < 0
    lab[amb] = np.array(classes)[dens[:, amb].argmax(0)]
    return lab


def labels_B(B: np.ndarray | None = None) -> np.ndarray:
    """Étiquettes de D24P31A : parois gauche/droite, couloir d'herbe, cercle sombre, chemin, liseré…"""
    if B is None:
        B = load_ref(1)
    h, w = B.shape[:2]
    k = _key(B)
    wall = np.zeros((h, w), bool); wall[:, :110] = True; wall[:, 395:] = True
    corr = np.zeros((h, w), bool); corr[140:480, 172:205] = True; corr[140:480, 300:330] = True
    dark = np.zeros((h, w), bool); dark[0:90, 200:300] = True
    lab = _exclusive_vote(k, {MUR: wall, HERBE: corr, HERBE_SOMBRE: dark})
    # chemin + liseré : orange/brun clair dans la bande centrale basse ; bordure verte lisse = chemin
    yy, xx = np.mgrid[0:h, 0:w]
    orange = _is_orange(B) & (yy > 170) & (xx > 195) & (xx < 320)
    path = ndi.binary_closing(orange, np.ones((5, 5)), border_value=1)
    path = ndi.binary_fill_holes(path)
    path = ndi.binary_opening(path, np.ones((5, 5)))
    # la bordure verte lisse de B (entre herbe et pavés) : on l'inclut au chemin de B (non utilisé)
    verge = ndi.binary_dilation(path, np.ones((25, 25))) & (yy > 160) & (xx > 185) & (xx < 330)
    lab[verge & (lab != MUR)] = CHEMIN
    lab[path] = CHEMIN
    # mur : nettoyage morphologique (paroi = composante connexe touchant le bord gauche/droit)
    m = lab == MUR
    m = ndi.binary_opening(m, np.ones((3, 3)))
    m = ndi.binary_closing(np.pad(m, 6, mode="edge"), np.ones((5, 5)))[6:-6, 6:-6]
    cc, n = ndi.label(m)
    keep = np.zeros(n + 1, bool)
    for side in (cc[:, 0], cc[:, -1]):
        keep[np.unique(side)] = True
    keep[0] = False
    m = keep[cc]
    m = ndi.binary_fill_holes(np.pad(m, ((0, 0), (1, 1)), constant_values=1))[:, 1:-1]
    lab[(lab == MUR) & ~m] = HERBE
    lab[m & (lab != CHEMIN)] = MUR
    # rochers gris
    rock = _is_gray(B) & ~m
    rock = ndi.binary_dilation(rock, np.ones((3, 3))) & (lab != CHEMIN)
    lab[rock] = ROCHER
    # buissons sombres et fleurs (boîtes relevées sur la grille ×2)
    for (x0, y0, x1, y1) in [(595 // 2, 300 // 2, 640 // 2, 340 // 2), (565 // 2, 718 // 2, 610 // 2, 752 // 2),
                             (420 // 2, 910 // 2, 462 // 2, 945 // 2)]:
        sub = (slice(y0, y1), slice(x0, x1))
        lab[sub][(lab[sub] != MUR)] = BUISSON
    for (x0, y0, x1, y1) in [(370 // 2, 38 // 2, 404 // 2, 72 // 2), (610 // 2, 100 // 2, 646 // 2, 136 // 2),
                             (626 // 2, 454 // 2, 662 // 2, 488 // 2)]:
        sub = (slice(y0, y1), slice(x0, x1))
        lab[sub][(lab[sub] != MUR)] = FLEUR
    return lab


def labels_A(A: np.ndarray | None = None) -> np.ndarray:
    """Étiquettes de D24P11A : herbe, chemin (avec brins d'herbe qui débordent), canopées, tunnel."""
    if A is None:
        A = load_ref(0)
    h, w = A.shape[:2]
    k = _key(A)
    yy, xx = np.mgrid[0:h, 0:w]
    grass_z = np.zeros((h, w), bool)
    grass_z[244:345, 310:380] = True
    grass_z[250:340, 170:232] = True
    grass_z[345:432, 305:352] = True
    can_z = np.zeros((h, w), bool)
    can_z[0:130, 0:215] = True
    can_z[0:130, 300:504] = True
    lab = _exclusive_vote(k, {HERBE: grass_z, CANOPEE_A: can_z}, win=9)
    # chemin : orange dans la bande ; zone = fermeture + remplissage
    orange = _is_orange(A) & (xx > 195) & (xx < 320) & (yy > 95)
    path = ndi.binary_closing(orange, np.ones((7, 7)), border_value=0)
    path = ndi.binary_fill_holes(path)
    path = ndi.binary_opening(path, np.ones((5, 5)))
    cc, n = ndi.label(path)
    if n:
        sizes = ndi.sum(path, cc, range(1, n + 1))
        path = cc == (1 + int(np.argmax(sizes)))
    lab[path] = CHEMIN
    # tunnel sombre + pavés gris du passage nord
    tun = (yy < 100) & (xx > 225) & (xx < 290)
    lab[tun] = TUNNEL
    # rochers gris hors tunnel
    rock = _is_gray(A) & ~tun & ~path
    rock = ndi.binary_dilation(ndi.binary_opening(rock, np.ones((2, 2))), np.ones((3, 3)))
    lab[rock] = ROCHER
    # fleurs (boîtes relevées sur la grille ×2, en coordonnées 1×)
    for (cx, cy) in [(296, 200), (368, 222), (435, 232), (116, 248), (328, 392), (52, 408)]:
        sub = (slice(cy - 9, cy + 9), slice(cx - 10, cx + 10))
        m = lab[sub]
        m[(m == HERBE) | (m == CANOPEE_A)] = FLEUR
    # troncs/racines/canopées : tout ce qui n'est pas herbe/chemin reste CANOPEE_A
    return lab


GRASS_CORE = [0x3f7737, 0x477f37, 0x4f8f37, 0x478737, 0x5fa737, 0x6fb737, 0x4f8737, 0x77bf37,
              0x87c737, 0x579f37, 0x5faf37, 0x8fcf37, 0x67b737]


def grass_source_mask(img: np.ndarray, lab: np.ndarray) -> np.ndarray:
    """Herbe au soleil stricte : étiquette HERBE et couleur du cœur de l'herbe de A (13 couleurs)."""
    k = _key(img)
    ok = np.isin(k, GRASS_CORE) & (lab == HERBE)
    return ok


def shade_source_mask(img: np.ndarray, lab: np.ndarray) -> np.ndarray:
    """Herbe (soleil → ombre) sans racines/fleurs : étiquette herbe et couleur à dominante verte."""
    r, g, b = img[..., 0].astype(int), img[..., 1].astype(int), img[..., 2].astype(int)
    green = (g > r) & (g > b)
    ok = np.isin(lab, [HERBE, HERBE_SOMBRE]) & green
    ok = ndi.binary_opening(ok, np.ones((2, 2)))
    return ok


def luminance(img: np.ndarray) -> np.ndarray:
    f = img.astype(np.float32)
    return 0.299 * f[..., 0] + 0.587 * f[..., 1] + 0.114 * f[..., 2]


def path_mask_A(lab: np.ndarray) -> np.ndarray:
    return lab == CHEMIN


def signed_distance(mask: np.ndarray) -> np.ndarray:
    """Distance signée euclidienne au bord : > 0 à l'intérieur, < 0 à l'extérieur (en pixels)."""
    inside = ndi.distance_transform_edt(mask)
    outside = ndi.distance_transform_edt(~mask)
    return (inside - outside).astype(np.float32)


def colorize(lab: np.ndarray) -> np.ndarray:
    pal = np.array([[90, 200, 60], [20, 80, 20], [120, 60, 20], [230, 160, 40], [255, 120, 200],
                    [150, 150, 150], [0, 40, 60], [40, 0, 60], [200, 90, 30]], np.uint8)
    return pal[lab]
