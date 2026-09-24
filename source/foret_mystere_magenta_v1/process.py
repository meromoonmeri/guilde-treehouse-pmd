"""Post-traitement des calques générés sur magenta -> vrais pixels 1:1, palette canonique.

1. Clé magenta explicite (teinte magenta + frange contaminée), jamais la couleur du pixel (0,0).
2. Couleurs ramenées à la palette EXACTE de la référence Mystifying Forest (plus proche voisin
   en espace Lab) : aucune couleur inventée.
3. Retour à la grille : le générateur dessine des faux pixels de 2 px ; réduction par VOTE
   MAJORITAIRE dans chaque bloc 2x2 (phase de grille détectée), jamais LANCZOS/BILINEAR.
4. Alpha binaire : bloc opaque si au moins 3 pixels sur 4 ne sont pas du fond.
"""
from pathlib import Path

import numpy as np
from PIL import Image
from scipy import ndimage as nd

HERE = Path(__file__).resolve().parent
REF = HERE / "refs" / "reference_mystifying_forest.png"
FACTOR = 2


def _lab(rgb):
    c = rgb.astype(np.float64) / 255.0
    c = np.where(c > 0.04045, ((c + 0.055) / 1.055) ** 2.4, c / 12.92)
    M = np.array([[0.4124, 0.3576, 0.1805], [0.2126, 0.7152, 0.0722], [0.0193, 0.1192, 0.9505]])
    xyz = c @ M.T / np.array([0.9505, 1.0, 1.089])
    f = np.where(xyz > 0.008856, np.cbrt(xyz), 7.787 * xyz + 16 / 116)
    return np.stack([116 * f[..., 1] - 16, 500 * (f[..., 0] - f[..., 1]), 200 * (f[..., 1] - f[..., 2])], -1)


def canonical_palette():
    a = np.asarray(Image.open(REF).convert("RGB")).reshape(-1, 3)
    return np.unique(a, axis=0)


def magenta_mask(rgb):
    r, g, b = [rgb[..., i].astype(np.float64) for i in range(3)]
    bg = (r > 70) & (b > 70) & (r > g * 1.45) & (b > g * 1.45)
    # frange : pixels teintés de magenta collés au fond (anticrénelage du générateur)
    fringe = nd.binary_dilation(bg, iterations=2) & (r > g + 25) & (b > g + 25)
    return bg | fringe


def grid_phase(rgb):
    best = None
    a = rgb.astype(np.int32)
    for py in range(FACTOR):
        for px in range(FACTOR):
            h = (a.shape[0] - py) // FACTOR * FACTOR
            w = (a.shape[1] - px) // FACTOR * FACTOR
            blk = a[py:py + h, px:px + w].reshape(h // FACTOR, FACTOR, w // FACTOR, FACTOR, 3)
            var = blk.std(axis=(1, 3)).mean()
            if best is None or var < best[0]:
                best = (var, px, py)
    return best[1], best[2]


def to_pixels(path, keyed=True, ramp=None, cuts=(0.12, 0.30, 0.50, 0.70, 0.88)):
    """Retourne (rgba 1:1 en palette canonique, statistiques).

    ramp : liste ordonnée (sombre -> clair) de couleurs EXACTES de la palette canonique.
    Si fournie, les couleurs du brut sont classées par luminance et chaque quantile reçoit
    un cran de la rampe (garde le modelé généré quand ses teintes n'existent pas dans la
    palette, ex. herbes sarcelle écrasées sur une seule couleur par le plus proche voisin)."""
    rgb = np.asarray(Image.open(path).convert("RGB"))
    pal = canonical_palette()
    pal_lab = _lab(pal)
    bg = magenta_mask(rgb) if keyed else np.zeros(rgb.shape[:2], bool)
    # indices de palette (plus proche voisin Lab), calculés par couleur unique
    uniq, inv = np.unique(rgb.reshape(-1, 3), axis=0, return_inverse=True)
    ul = _lab(uniq)
    idx_u = np.empty(len(uniq), np.int32)
    for s in range(0, len(uniq), 4096):
        d = ((ul[s:s + 4096, None, :] - pal_lab[None]) ** 2).sum(-1)
        idx_u[s:s + 4096] = d.argmin(1)
    if ramp is not None:
        ramp = np.asarray(ramp, np.uint8)
        ridx = np.array([int(np.flatnonzero((pal == c).all(1))[0]) for c in ramp])
        lum = uniq.astype(float) @ [0.299, 0.587, 0.114]
        fg = ~bg.ravel()
        cnt = np.bincount(inv.ravel()[fg], minlength=len(uniq))
        order = np.argsort(lum)
        cum = np.cumsum(cnt[order]) / max(1, cnt.sum())
        q = np.searchsorted(np.asarray(cuts), cum, side="right")
        idx_u[order] = ridx[np.minimum(q, len(ramp) - 1)]
    idx = idx_u[inv.ravel()].reshape(rgb.shape[:2])
    px, py = grid_phase(rgb)
    h = (rgb.shape[0] - py) // FACTOR * FACTOR
    w = (rgb.shape[1] - px) // FACTOR * FACTOR
    idx = idx[py:py + h, px:px + w]
    bgc = bg[py:py + h, px:px + w]
    H, W = h // FACTOR, w // FACTOR
    blk_idx = idx.reshape(H, FACTOR, W, FACTOR).transpose(0, 2, 1, 3).reshape(H, W, -1)
    blk_bg = bgc.reshape(H, FACTOR, W, FACTOR).transpose(0, 2, 1, 3).reshape(H, W, -1)
    opaque = (~blk_bg).sum(-1) >= 3
    out_idx = np.zeros((H, W), np.int32)
    n = len(pal)
    for y in range(H):
        row_i, row_b = blk_idx[y], blk_bg[y]
        for x in range(W):
            if not opaque[y, x]:
                continue
            v = row_i[x][~row_b[x]]
            out_idx[y, x] = np.bincount(v, minlength=n).argmax()
    rgba = np.zeros((H, W, 4), np.uint8)
    rgba[..., :3] = pal[out_idx]
    rgba[..., 3] = np.where(opaque, 255, 0)
    rgba[~opaque] = 0
    if keyed:
        # retirer les poussières isolées (< 4 px) laissées par la clé
        lab, k = nd.label(opaque)
        if k:
            sizes = nd.sum(opaque, lab, range(1, k + 1))
            small = np.isin(lab, np.flatnonzero(sizes < 4) + 1)
            rgba[small] = 0
    return rgba, dict(source=path.name, grid_phase=[int(px), int(py)], factor=FACTOR,
                      size_1x=[int(W), int(H)], palette_colors=int(len(pal)),
                      mapping="rampe de luminance" if ramp is not None else "plus proche voisin Lab")
