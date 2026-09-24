"""Retouche des éléments générés en vrai pixel art 1:1 dans la palette exacte des références.

Chaîne (aucun LANCZOS/BILINEAR/BICUBIC) :
  1. détourage magenta explicite (fond g<100, frange g<130 ; jamais le pixel (0,0) comme clé) ;
  2. pas de grille : pas natif détecté (projections de gradients) ou pas imposé par la taille cible ;
  3. par cellule : vote majoritaire des indices de palette des pixels centraux de la cellule, chaque
     pixel source étant projeté (Lab) dans la sous-palette de sa matière (feuillage, bois, pierre,
     fleur, sombre) — toutes couleurs issues de D24P11A/D24P31A ;
  4. alpha binaire (couverture ≥ 50 %), suppression des îlots et trous < 6 px, dé-mouchetage.
Ce module n'écrit aucun fichier à l'import.
"""
from __future__ import annotations

import numpy as np
from scipy import ndimage as ndi

import labels as LB


# ---------------------------------------------------------------- couleur

def srgb_to_lab(rgb: np.ndarray) -> np.ndarray:
    c = rgb.astype(np.float64) / 255.0
    c = np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)
    M = np.array([[0.4124, 0.3576, 0.1805], [0.2126, 0.7152, 0.0722], [0.0193, 0.1192, 0.9505]])
    xyz = c @ M.T / np.array([0.95047, 1.0, 1.08883])
    f = np.where(xyz > 0.008856, np.cbrt(xyz), 7.787 * xyz + 16 / 116)
    L = 116 * f[..., 1] - 16
    a = 500 * (f[..., 0] - f[..., 1])
    b = 200 * (f[..., 1] - f[..., 2])
    return np.stack([L, a, b], -1)


def _hsv(rgb):
    f = rgb.astype(np.float32) / 255.0
    mx, mn = f.max(-1), f.min(-1)
    d = mx - mn + 1e-6
    r, g, b = f[..., 0], f[..., 1], f[..., 2]
    h = np.where(mx == r, ((g - b) / d) % 6, np.where(mx == g, (b - r) / d + 2, (r - g) / d + 4)) * 60
    s = np.where(mx > 0, (mx - mn) / (mx + 1e-6), 0)
    return h, s, mx


MATS = ["feuillage", "bois", "pierre", "fleur", "sombre"]


def material_of(rgb: np.ndarray) -> np.ndarray:
    """Matière par pixel : 0 feuillage, 1 bois, 2 pierre, 3 fleur, 4 sombre."""
    h, s, v = _hsv(rgb)
    mat = np.full(rgb.shape[:2], 2, np.int8)
    green = (h >= 65) & (h < 170) & (s > 0.25)
    brown = (h >= 15) & (h < 65) & (s > 0.28) & (v < 0.80)
    flower = ((h < 15) | (h >= 290)) & (s > 0.25) & (v > 0.45)
    flower |= (h >= 40) & (h < 65) & (s > 0.35) & (v >= 0.80)  # jaunes vifs
    flower |= (s < 0.25) & (v > 0.88)  # blancs
    dark = v < 0.22
    mat[green] = 0
    mat[brown] = 1
    mat[flower] = 3
    mat[dark] = 4
    return mat


def ref_subpalettes():
    """Sous-palettes de matière (couleurs exactes des deux références), définies par les étiquettes."""
    A, B = LB.load_ref(0), LB.load_ref(1)
    la, lb = LB.labels_A(A), LB.labels_B(B)
    pix = np.concatenate([A.reshape(-1, 3), B.reshape(-1, 3)])
    lab = np.concatenate([la.ravel(), lb.ravel()])
    cols, inv, cnt = np.unique(pix, axis=0, return_inverse=True, return_counts=True)
    inv = inv.ravel()
    n = len(cols)
    h, s_, v = _hsv(cols[None].astype(np.uint8))
    h, s_, v = h[0], s_[0], v[0]

    def frac(labels):
        c = np.bincount(inv[np.isin(lab, labels)], minlength=n)
        return c / np.maximum(cnt, 1)

    green = (h >= 65) & (h < 170) & (s_ > 0.2)
    trees = frac([LB.CANOPEE_A, LB.MUR, LB.HERBE])
    feuillage = green & (trees > 0.5) & (cnt >= 3)
    brownish = (h >= 15) & (h < 65) & (s_ > 0.25)
    path_f = frac([LB.CHEMIN])
    bois = brownish & (frac([LB.CANOPEE_A, LB.MUR]) > 0.5) & (path_f < 0.3) & (cnt >= 3)
    pierre = (frac([LB.ROCHER, LB.TUNNEL]) > 0.5) & ~green & (cnt >= 2)
    fleur = (frac([LB.FLEUR]) > 0.5) & ~((h >= 65) & (h < 170) & (s_ > 0.45)) & (cnt >= 2)
    lum = 0.299 * cols[:, 0] + 0.587 * cols[:, 1] + 0.114 * cols[:, 2]
    sombre = np.zeros(n, bool)
    greenish = (cols[:, 1] >= cols[:, 0]) & (cols[:, 1] > cols[:, 2])
    order = [i for i in np.argsort(lum) if greenish[i]]
    sombre[order[:8]] = True
    sub = {"feuillage": cols[feuillage], "bois": cols[bois], "pierre": cols[pierre],
           "fleur": cols[fleur], "sombre": cols[sombre]}
    return {k: v.astype(np.int16) for k, v in sub.items()}, cols.astype(np.int16)


# ---------------------------------------------------------------- détourage et grille

def magenta_alpha(rgb: np.ndarray) -> np.ndarray:
    r, g, b = rgb[..., 0].astype(int), rgb[..., 1].astype(int), rgb[..., 2].astype(int)
    bg = (r > 150) & (b > 150) & (g < 100)
    fringe = (r > 150) & (b > 150) & (g < 130) & (np.abs(r - b) < 90)
    return ~(bg | fringe)


def detect_pitch(rgb: np.ndarray, lo: float = 3.0, hi: float = 16.0) -> float:
    """Pas de grille natif (px générés par pixel d'art) via autocorrélation des gradients."""
    f = rgb.astype(np.float32).sum(-1)
    gx = np.abs(np.diff(f, axis=1)).sum(0)
    gy = np.abs(np.diff(f, axis=0)).sum(1)
    best = []
    for sig in (gx, gy):
        s = sig - sig.mean()
        ac = np.correlate(s, s, "full")[len(s) - 1:]
        ac /= ac[0] + 1e-6
        lags = np.arange(len(ac))
        m = (lags >= lo) & (lags <= hi * 3)
        # le premier pic significatif
        cand = [l for l in range(int(lo), int(hi) + 1) if ac[l] > ac[l - 1] and ac[l] >= ac[l + 1]]
        if cand:
            l = max(cand, key=lambda k: ac[k])
            best.append(l)
    return float(np.mean(best)) if best else 0.0


def pixelize(rgb: np.ndarray, alpha: np.ndarray, pitch: float, subpal: dict, *, core: float = 0.6,
             cov: float = 0.5, phase=(0.0, 0.0), fringe_px: int = 3, majority: int = 0):
    """Réduit en vrai pixel art : renvoie (rgb int16 (h,w,3), alpha bool (h,w))."""
    H, W = alpha.shape
    oh = int(np.floor((H - phase[0]) / pitch))
    ow = int(np.floor((W - phase[1]) / pitch))
    mat = material_of(rgb)
    # projection Lab par matière (sur les couleurs uniques pour la vitesse)
    flat = rgb.reshape(-1, 3)
    uc, uinv = np.unique(flat, axis=0, return_inverse=True)
    uinv = uinv.ravel()
    umat = material_of(uc[None].astype(np.uint8))[0]
    ulab = srgb_to_lab(uc)
    allpal = np.concatenate([subpal[n] for n in MATS])
    offs = np.cumsum([0] + [len(subpal[n]) for n in MATS])
    idx_u = np.zeros(len(uc), np.int32)
    for mi, n in enumerate(MATS):
        m = umat == mi
        if not m.any():
            continue
        pl = srgb_to_lab(subpal[n])
        d = ((ulab[m][:, None, :] - pl[None]) ** 2).sum(-1)
        idx_u[m] = offs[mi] + d.argmin(1)
    idx = idx_u[uinv].reshape(H, W)
    # frange : pixels proches du fond magenta, mélangés — exclus des votes de couleur
    inner = ndi.binary_erosion(alpha, iterations=fringe_px) if fringe_px else alpha
    out_idx = np.full((oh, ow), -1, np.int32)
    out_a = np.zeros((oh, ow), bool)
    k = len(allpal)
    for j in range(oh):
        y0 = phase[0] + j * pitch
        ya, yb = int(round(y0)), int(round(y0 + pitch))
        c0, c1 = int(round(y0 + pitch * (1 - core) / 2)), int(round(y0 + pitch * (1 + core) / 2))
        for i in range(ow):
            x0 = phase[1] + i * pitch
            xa, xb = int(round(x0)), int(round(x0 + pitch))
            if alpha[ya:yb, xa:xb].mean() < cov:
                continue
            d0, d1 = int(round(x0 + pitch * (1 - core) / 2)), int(round(x0 + pitch * (1 + core) / 2))
            cell_i = idx[c0:max(c1, c0 + 1), d0:max(d1, d0 + 1)]
            cell_a = inner[c0:max(c1, c0 + 1), d0:max(d1, d0 + 1)]
            v = cell_i[cell_a]
            if len(v) == 0:
                v = idx[ya:yb, xa:xb][inner[ya:yb, xa:xb]]
            if len(v) == 0:
                # cellule de bord : pixels de frange, sans les teintes « fleur » dues au magenta
                vv = idx[ya:yb, xa:xb][alpha[ya:yb, xa:xb]]
                fl0, fl1 = offs[3], offs[4]
                v = vv[(vv < fl0) | (vv >= fl1)]
            if len(v) == 0:
                continue
            out_idx[j, i] = np.bincount(v, minlength=k).argmax()
            out_a[j, i] = True
    out_a = clean_alpha(out_a)
    out_idx = despeckle(out_idx, out_a)
    for _ in range(majority):
        out_idx = majority_filter(out_idx, out_a)
    rgb_out = np.zeros((oh, ow, 3), np.int16)
    ok = out_a & (out_idx >= 0)
    rgb_out[ok] = allpal[out_idx[ok]]
    return rgb_out, ok


def clean_alpha(a: np.ndarray, min_island: int = 6) -> np.ndarray:
    cc, n = ndi.label(a)
    if n:
        sizes = ndi.sum(a, cc, range(1, n + 1))
        keep = np.r_[False, sizes >= min_island]
        a = keep[cc]
    holes = ~a
    cc, n = ndi.label(holes)
    if n:
        sizes = ndi.sum(holes, cc, range(1, n + 1))
        border = np.unique(np.r_[cc[0], cc[-1], cc[:, 0], cc[:, -1]])
        small = np.r_[False, sizes < min_island]
        small[border] = False
        a = a | small[cc]
    return a


def majority_filter(idx: np.ndarray, a: np.ndarray, need: int = 5) -> np.ndarray:
    """Amas : si ≥ need des 8 voisins partagent une couleur différente du centre, on l'adopte."""
    h, w = idx.shape
    pad = np.pad(np.where(a, idx, -1), 1, constant_values=-1)
    neigh = np.stack([pad[1 + dy:h + 1 + dy, 1 + dx:w + 1 + dx]
                      for dy in (-1, 0, 1) for dx in (-1, 0, 1) if (dy, dx) != (0, 0)], -1)
    out = idx.copy()
    ys, xs = np.nonzero(a)
    for y, x in zip(ys, xs):
        v = neigh[y, x]
        v = v[v >= 0]
        if len(v) < need:
            continue
        vals, cnt = np.unique(v, return_counts=True)
        j = cnt.argmax()
        if cnt[j] >= need and vals[j] != idx[y, x]:
            out[y, x] = vals[j]
    return out


def despeckle(idx: np.ndarray, a: np.ndarray, passes: int = 2) -> np.ndarray:
    """Remplace un pixel isolé (aucun voisin 8 de même couleur) par la couleur majoritaire voisine."""
    idx = idx.copy()
    h, w = idx.shape
    for _ in range(passes):
        pad = np.pad(np.where(a, idx, -1), 1, constant_values=-1)
        neigh = np.stack([pad[1 + dy:h + 1 + dy, 1 + dx:w + 1 + dx]
                          for dy in (-1, 0, 1) for dx in (-1, 0, 1) if (dy, dx) != (0, 0)], -1)
        same = (neigh == idx[..., None]).sum(-1)
        iso = a & (same == 0)
        ys, xs = np.nonzero(iso)
        for y, x in zip(ys, xs):
            v = neigh[y, x]
            v = v[v >= 0]
            if len(v):
                vals, cnt = np.unique(v, return_counts=True)
                if cnt.max() >= 3:
                    idx[y, x] = vals[cnt.argmax()]
    return idx
