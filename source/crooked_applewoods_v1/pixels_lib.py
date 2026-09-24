"""Calque généré (faux pixels, éventuellement pas fractionnaire) -> vrais pixels 1:1 en palette canonique.

1. Clé magenta explicite (teinte + frange contaminée), jamais la couleur du pixel (0,0).
2. Chaque couleur du brut est ramenée à la palette EXACTE fournie (plus proche voisin Lab),
   ou, en option, par rampe de luminance sur des couleurs exactes de la palette.
3. Grille : pas P et phase estimés par axe (P peut être fractionnaire, ex. 2,86 quand le
   générateur a agrandi une petite image au plus proche voisin). Chaque cellule de la vraie
   grille prend la couleur MAJORITAIRE de ses pixels : inversion de l'agrandissement,
   jamais LANCZOS/BILINEAR/NEAREST.
4. Alpha binaire : cellule opaque si >= 60 % de ses pixels ne sont pas du fond.
"""
from pathlib import Path

import numpy as np
from PIL import Image
from scipy import ndimage as nd


def lab(rgb):
    c = np.asarray(rgb, np.float64) / 255.0
    c = np.where(c > 0.04045, ((c + 0.055) / 1.055) ** 2.4, c / 12.92)
    M = np.array([[0.4124, 0.3576, 0.1805], [0.2126, 0.7152, 0.0722], [0.0193, 0.1192, 0.9505]])
    xyz = c @ M.T / np.array([0.9505, 1.0, 1.089])
    f = np.where(xyz > 0.008856, np.cbrt(xyz), 7.787 * xyz + 16 / 116)
    return np.stack([116 * f[..., 1] - 16, 500 * (f[..., 0] - f[..., 1]), 200 * (f[..., 1] - f[..., 2])], -1)


def palette_of(*paths, filt=None):
    cols = []
    for p in paths:
        a = np.asarray(Image.open(p).convert("RGBA"))
        c = a[a[..., 3] == 255][:, :3]
        if filt is not None:
            c = c[filt(c.astype(int))]
        cols.append(c)
    return np.unique(np.concatenate(cols), axis=0)


def magenta_mask(rgb):
    r, g, b = [rgb[..., i].astype(np.float64) for i in range(3)]
    bg = (r > 70) & (b > 70) & (r > g * 1.45) & (b > g * 1.45) & (g < 100)  # g<100 : épargne les pétales roses
    fringe = nd.binary_dilation(bg, iterations=2) & (r > g + 25) & (b > g + 25) & (g < 130)
    return bg | fringe


def _axis_grid(prof, p0):
    """Pas et phase qui placent les fortes variations sur les bords de cellule."""
    n = len(prof)
    x = np.arange(n) + 1.0  # prof[i] = variation entre i et i+1 -> frontière à i+1
    best = None
    for P in np.arange(p0 - 0.06, p0 + 0.061, 0.002):
        for ph in np.arange(0, P, 0.05):
            t = (x - ph) / P
            frac = np.abs(t - np.round(t))
            cost = prof[frac * P > 0.5].sum()  # variation à l'intérieur des cellules
            if best is None or cost < best[0]:
                best = (cost, float(P), float(ph))
    return best[1], best[2]


def _cost(prof, P, ph):
    t = (np.arange(len(prof)) + 1.0 - ph) / P
    return prof[np.abs(t - np.round(t)) * P > 0.5].sum()


def estimate_grid(rgb, bg):
    g = rgb.astype(np.float64).sum(-1)
    fg = ~bg
    dx = np.abs(np.diff(g, axis=1)) * (fg[:, 1:] & fg[:, :-1])
    dy = np.abs(np.diff(g, axis=0)) * (fg[1:] & fg[:-1])
    out = []
    for prof in (dx.mean(0), dy.mean(1)):
        q = prof - prof.mean()
        F = np.abs(np.fft.rfft(q))
        fr = np.fft.rfftfreq(len(q))
        m = (fr > 1 / 8.5) & (fr < 1 / 1.7)
        p0 = 1 / fr[m][F[m].argmax()]
        P, ph = _axis_grid(prof, p0)
        if abs(P - round(P)) < 0.03:  # pas entier : on fige P et on recale la phase
            P0 = float(round(P))
            ph = min(np.arange(0, P0, 0.25), key=lambda f: _cost(prof, P0, f))
            P = P0
        out.append((P, float(ph)))
    (px, phx), (py, phy) = out
    return px, phx, py, phy


def to_pixels(path, palette, keyed=True, ramp=None, cuts=(0.12, 0.30, 0.50, 0.70, 0.88), grid=None):
    path = Path(path)
    rgb = np.asarray(Image.open(path).convert("RGB"))
    bg = magenta_mask(rgb) if keyed else np.zeros(rgb.shape[:2], bool)
    pal = np.asarray(palette, np.uint8)
    uniq, inv = np.unique(rgb.reshape(-1, 3), axis=0, return_inverse=True)
    inv = inv.ravel()
    if ramp is None:
        ul, pl = lab(uniq), lab(pal)
        idx_u = np.empty(len(uniq), np.int32)
        for s in range(0, len(uniq), 2048):
            idx_u[s:s + 2048] = ((ul[s:s + 2048, None] - pl[None]) ** 2).sum(-1).argmin(1)
    else:
        ramp = np.asarray(ramp, np.uint8)
        ridx = np.array([int(np.flatnonzero((pal == c).all(1))[0]) for c in ramp])
        lum = uniq.astype(float) @ [0.299, 0.587, 0.114]
        cnt = np.bincount(inv[~bg.ravel()], minlength=len(uniq))
        order = np.argsort(lum)
        cum = np.cumsum(cnt[order]) / max(1, cnt.sum())
        idx_u = np.empty(len(uniq), np.int32)
        idx_u[order] = ridx[np.minimum(np.searchsorted(np.asarray(cuts), cum, side="right"), len(ramp) - 1)]
    idx = idx_u[inv].reshape(rgb.shape[:2])

    px, phx, py, phy = grid or estimate_grid(rgb, bg)
    H0, W0 = rgb.shape[:2]
    cx = np.floor((np.arange(W0) + 0.5 - phx) / px).astype(int)
    cy = np.floor((np.arange(H0) + 0.5 - phy) / py).astype(int)
    # ne garder que les cellules entières
    okx = (cx >= 0) & (cx < cx.max()) if cx.max() > 0 else cx >= 0
    oky = (cy >= 0) & (cy < cy.max()) if cy.max() > 0 else cy >= 0
    W, H = int(cx[okx].max()) + 1, int(cy[oky].max()) + 1
    cell = (cy[:, None] * W + cx[None, :])
    valid = oky[:, None] & okx[None, :]
    c_all = cell[valid]
    tot = np.bincount(c_all, minlength=H * W)
    fgm = valid & ~bg
    c_fg, i_fg = cell[fgm], idx[fgm]
    nfg = np.bincount(c_fg, minlength=H * W)
    key = c_fg.astype(np.int64) * len(pal) + i_fg
    k, n = np.unique(key, return_counts=True)
    kc, ki = k // len(pal), k % len(pal)
    o = np.lexsort((-n, kc))
    kc, ki = kc[o], ki[o]
    first = np.r_[True, kc[1:] != kc[:-1]]
    maj = np.zeros(H * W, np.int64)
    maj[kc[first]] = ki[first]
    opaque = nfg >= 0.6 * np.maximum(tot, 1)
    out = np.zeros((H * W, 4), np.uint8)
    out[:, :3] = pal[maj]
    out[:, 3] = 255
    out[~opaque] = 0
    out = out.reshape(H, W, 4)
    if keyed:
        op = out[..., 3] > 0
        lb, kk = nd.label(op)
        if kk:
            s = nd.sum(op, lb, range(1, kk + 1))
            out[np.isin(lb, np.flatnonzero(s < 4) + 1)] = 0
    stats = dict(source=path.name, pas_x=round(px, 3), pas_y=round(py, 3), phase=[round(phx, 2), round(phy, 2)],
                 taille_1x=[W, H], couleurs_palette=int(len(pal)),
                 conversion="rampe de luminance" if ramp is not None else "plus proche voisin Lab")
    return out, stats
