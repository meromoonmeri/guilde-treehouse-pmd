"""Composition canonique par bandes : parois périodiques exactes et chemin par segments.

* Parois : D24P31A est construit sur un bloc vertical de 192 lignes. Pour une ligne s telle que
  B[s] == B[s+192] sur toute la largeur de la paroi, empiler B[s:s+192] reproduit exactement la
  continuation canonique (aucun raccord inventé). Chaque paroi = cette bande, décalée d'un
  décalage horizontal constant et d'une phase verticale.
* Chemin : segments pleine largeur du chemin de D24P11A, posés rigidement (ni étirement ni
  cisaillement) le long de la ligne médiane cible ; raccord horizontal par coupe minimale entre
  segments, raccords verticaux par coupe minimale dans l'herbe côté sol.
Ce module n'écrit aucun fichier à l'import.
"""
from __future__ import annotations

import numpy as np
from scipy import ndimage as ndi

from pmdsynth import _min_cut_vertical

PERIOD = 192
# (colonnes source, ligne de départ s) vérifiées : B[s+k] == B[s+k+192] pour k autour de s
WALL_STRIPS = {"ouest": ((0, 200), 170), "est": ((320, 504), 208)}


def verify_strip(B: np.ndarray, cols, s: int, span: int = 8) -> bool:
    x0, x1 = cols
    a = B[s - span:s + span, x0:x1]
    b = B[s - span + PERIOD:s + span + PERIOD, x0:x1]
    return bool((a == b).all())


def periodic_wall(B: np.ndarray, side: str, H: int, W: int, dx: int, phase: int):
    """Paroi exacte : out[y, x] = B[s + (y + phase) % 192, x - dx] pour les colonnes de la bande."""
    (x0, x1), s = WALL_STRIPS[side]
    assert verify_strip(B, (x0, x1), s), "raccord périodique non exact"
    out = np.zeros((H, W, 3), np.int16)
    prov = np.full((H, W, 3), -1, np.int32)
    ys = s + (np.arange(H) + phase) % PERIOD
    for x in range(W):
        xs = x - dx
        if x0 <= xs < x1:
            out[:, x] = B[ys, xs]
            prov[:, x, 0] = 1
            prov[:, x, 1] = ys
            prov[:, x, 2] = xs
    return out, prov


def _row_profile(mask: np.ndarray):
    h = mask.shape[0]
    c = np.full(h, np.nan)
    r = np.full(h, np.nan)
    for y in range(h):
        xs = np.nonzero(mask[y])[0]
        if len(xs):
            c[y] = (xs.min() + xs.max()) / 2.0
            r[y] = (xs.max() - xs.min() + 1) / 2.0
    return c, r


def path_strips(A: np.ndarray, pathA: np.ndarray, validA: np.ndarray, G: np.ndarray, provG: np.ndarray,
                cx_t: np.ndarray, hr_t: np.ndarray, y_top: int, margin_t: np.ndarray, *, seg_h: int = 40,
                ov: int = 12, side_band: int = 8, reuse_pen: float = 800.0, w_shape: float = 60.0,
                top_k: int = 3, seed: int = 0, src_id: int = 0):
    """Chemin par segments. margin_t[y] = marge d'herbe riveraine (px) gardée de chaque côté à la ligne y."""
    rng = np.random.default_rng(seed)
    H, W = G.shape[:2]
    out = G.copy()
    prov = provG.copy()
    cA, rA = _row_profile(pathA)
    cA_s = ndi.uniform_filter1d(np.nan_to_num(cA, nan=np.nanmean(cA)), 5)
    hA = A.shape[0]
    starts = [ys for ys in range(0, hA - seg_h) if validA[ys:ys + seg_h].all() and not np.isnan(rA[ys:ys + seg_h]).any()]
    if not starts:
        raise ValueError("aucune rangée source valide pour le chemin")
    used = np.zeros(hA, np.float32)
    y0 = y_top
    prev_rows = None  # masque des pixels écrits par le segment précédent
    placed = []
    while y0 < H:
        y1 = min(H, y0 + seg_h)
        n = y1 - y0
        rows_t = np.arange(y0, y1)
        mid = (y0 + y1) // 2
        best = []
        for ys in starts:
            rows_s = np.arange(ys, ys + n)
            dx = int(round(cx_t[mid] - cA_s[ys + (mid - y0)]))
            shape = np.mean((cA_s[rows_s] + dx - cx_t[rows_t]) ** 2 + (rA[rows_s] - hr_t[rows_t]) ** 2)
            cost = w_shape * shape + reuse_pen * used[ys:ys + n].mean()
            best.append((cost, ys, dx))
        best.sort()
        # recouvrement : SSD avec les pixels déjà posés par le segment précédent (sur les meilleurs)
        cand = best[:40]
        scored = []
        for cost, ys, dx in cand:
            ovc = 0.0
            if prev_rows is not None:
                oy1 = min(y0 + ov, y1)
                errs = []
                for yy in range(y0, oy1):
                    xs_t = np.nonzero(prev_rows[yy])[0]
                    xs_s = xs_t - dx
                    ok = (xs_s >= 0) & (xs_s < A.shape[1])
                    if ok.any():
                        d = A[ys + yy - y0, xs_s[ok]].astype(np.float32) - out[yy, xs_t[ok]].astype(np.float32)
                        errs.append((d * d).sum(-1).mean())
                ovc = float(np.mean(errs)) if errs else 0.0
            scored.append((cost + ovc, ys, dx))
        scored.sort()
        pick = scored[int(rng.integers(0, min(top_k, len(scored))))]
        _, ys, dx = pick
        # étendue horizontale du segment par ligne (chemin source + marge), en coordonnées cible
        seg = np.zeros((n, W), bool)
        for i, yy in enumerate(rows_t):
            srow = ys + i
            m = int(margin_t[yy])
            xs = np.nonzero(pathA[srow])[0]
            lo, hi = xs.min() - m + dx, xs.max() + m + dx
            lo, hi = max(0, lo), min(W - 1, hi)
            seg[i, lo:hi + 1] = True
        src_px = np.zeros((n, W, 3), np.int16)
        src_ok = np.zeros((n, W), bool)
        for i in range(n):
            xs_t = np.nonzero(seg[i])[0]
            xs_s = xs_t - dx
            ok = (xs_s >= 0) & (xs_s < A.shape[1])
            src_px[i, xs_t[ok]] = A[ys + i, xs_s[ok]]
            src_ok[i, xs_t[ok]] = True
        seg &= src_ok
        write = seg.copy()
        # coupes verticales gauche/droite dans la marge (transition sol → segment)
        err = ((src_px.astype(np.float32) - out[y0:y1].astype(np.float32)) ** 2).sum(-1)
        lefts = np.array([np.nonzero(seg[i])[0].min() if seg[i].any() else 0 for i in range(n)])
        rights = np.array([np.nonzero(seg[i])[0].max() if seg[i].any() else 0 for i in range(n)])
        for side in ("g", "d"):
            band = np.zeros((n, side_band), np.float32)
            for i in range(n):
                if side == "g":
                    xs = lefts[i] + np.arange(side_band)
                else:
                    xs = rights[i] - side_band + 1 + np.arange(side_band)
                xs = np.clip(xs, 0, W - 1)
                band[i] = err[i, xs]
            cut = _min_cut_vertical(band)
            for i in range(n):
                if side == "g":
                    write[i, lefts[i]:lefts[i] + cut[i]] = False
                else:
                    write[i, rights[i] - side_band + 1 + cut[i] + 1:rights[i] + 1] = False
        # coupe horizontale dans le recouvrement avec le segment précédent
        if prev_rows is not None:
            oy = min(ov, n)
            cols = np.nonzero(seg[:oy].any(0) | prev_rows[y0:y0 + oy].any(0))[0]
            if len(cols):
                c0, c1 = cols.min(), cols.max() + 1
                band = err[:oy, c0:c1].T  # (colonnes, lignes)
                cut = _min_cut_vertical(band)
                for j, x in enumerate(range(c0, c1)):
                    write[:cut[j], x] = False
        # écrire
        sub = out[y0:y1]
        sp = prov[y0:y1]
        sub[write] = src_px[write]
        ii, jj = np.nonzero(write)
        sp[ii, jj, 0] = src_id
        sp[ii, jj, 1] = ys + ii
        sp[ii, jj, 2] = jj - dx
        used[ys:ys + n] += 1.0
        prev_rows = np.zeros((H, W), bool)
        prev_rows[y0:y1] = seg
        placed.append((y0, ys, dx))
        y0 += seg_h - ov
        if y1 == H:
            break
    return out, prov, placed
