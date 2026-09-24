"""Synthèse de texture canonique guidée — chaque pixel produit est un pixel source exact.

Méthode (spriter pro, textures canoniques) :
  * quilting par patchs en balayage raster, choix du patch par coût
      recouvrement (SSD sur les pixels déjà posés ou imposés)
    + guidage (écart des cartes de caractéristiques cible/source : distance signée au bord,
      orientation, niveau d'ombre…)
    + pénalité de réutilisation (évite les répétitions en grille) ;
  * coupe minimale (programmation dynamique) dans les bandes de recouvrement gauche/haut,
    pour que les raccords suivent les contours de la matière au lieu de lignes droites ;
  * pixels imposés : jamais réécrits (ex. herbe déjà posée autour d'un chemin) ; le patch
    ne remplit que les pixels libres ;
  * provenance : pour chaque pixel, (id_source, y_source, x_source).

Aucune recoloration, rotation, miroir ni rééchantillonnage : on ne fait que copier des pixels.
Ce module n'écrit aucun fichier à l'import.
"""
from __future__ import annotations

import numpy as np


def _min_cut_vertical(err: np.ndarray) -> np.ndarray:
    """Chemin de coût minimal de haut en bas dans une bande (h, w). Renvoie la colonne par ligne."""
    h, w = err.shape
    cost = err.astype(np.float64).copy()
    back = np.zeros((h, w), np.int8)
    for y in range(1, h):
        prev = cost[y - 1]
        left = np.r_[np.inf, prev[:-1]]
        right = np.r_[prev[1:], np.inf]
        stack = np.stack([left, prev, right])
        k = stack.argmin(0)
        cost[y] += stack[k, np.arange(w)]
        back[y] = k - 1
    path = np.zeros(h, np.int64)
    path[-1] = int(cost[-1].argmin())
    for y in range(h - 1, 0, -1):
        path[y - 1] = np.clip(path[y] + back[y, path[y]], 0, w - 1)
    return path


class Source:
    """Une image source canonique + ses cartes de caractéristiques + positions de patch autorisées."""

    def __init__(self, sid: int, rgb: np.ndarray, feat: np.ndarray | None, allowed: np.ndarray):
        self.sid = sid
        self.rgb = rgb.astype(np.int16)
        h, w = rgb.shape[:2]
        self.feat = np.zeros((h, w, 0), np.float32) if feat is None else feat.astype(np.float32)
        self.allowed = allowed.astype(bool)  # masque des pixels autorisés dans un patch

    def positions(self, p: int) -> np.ndarray:
        """Coins haut-gauche (y, x) dont le patch p×p est entièrement dans le masque autorisé."""
        a = self.allowed.astype(np.int32)
        ii = np.pad(a, ((1, 0), (1, 0))).cumsum(0).cumsum(1)
        h, w = a.shape
        if h < p or w < p:
            return np.zeros((0, 2), np.int64)
        s = ii[p:, p:] - ii[:-p, p:] - ii[p:, :-p] + ii[:-p, :-p]
        ys, xs = np.nonzero(s == p * p)
        return np.stack([ys, xs], 1)


def quilt(shape, sources: list[Source], tgt_feat: np.ndarray | None = None, *, patch: int = 24,
          overlap: int = 8, region: np.ndarray | None = None, imposed: np.ndarray | None = None,
          imposed_mask: np.ndarray | None = None, w_feat: float = 1.0, n_cand: int = 3000,
          reuse_radius: int = 12, reuse_pen: float = 0.0, top_k: int = 4, seed: int = 0,
          feat_weights: np.ndarray | None = None, progress: bool = False):
    """Synthétise une image (h, w, 3) dans `region` (tout si None).

    Retourne (rgb int16 (h,w,3), prov int32 (h,w,3) = (sid, sy, sx) ou -1, filled bool (h,w)).
    """
    rng = np.random.default_rng(seed)
    h, w = shape
    p, o = patch, overlap
    step = p - o
    out = np.zeros((h, w, 3), np.int16)
    prov = np.full((h, w, 3), -1, np.int32)
    filled = np.zeros((h, w), bool)
    if imposed_mask is not None:
        out[imposed_mask] = imposed[imposed_mask]
        filled |= imposed_mask
        prov[imposed_mask] = -2  # -2 : pixel imposé (provenance tenue par l'appelant)
    if region is None:
        region = np.ones((h, w), bool)
    todo = region & ~filled
    F = 0 if tgt_feat is None else tgt_feat.shape[2]
    if feat_weights is None:
        feat_weights = np.ones(F, np.float32)
    feat_weights = np.asarray(feat_weights, np.float32)

    # positions candidates par source
    pos = [s.positions(p) for s in sources]
    cand_sid = np.concatenate([np.full(len(q), i) for i, q in enumerate(pos)]) if pos else np.zeros(0, int)
    cand_yx = np.concatenate(pos) if pos else np.zeros((0, 2), int)
    if len(cand_yx) == 0:
        raise ValueError("aucune position de patch valide dans les sources")
    used = [np.zeros(s.rgb.shape[:2], np.float32) for s in sources]

    ys = list(range(0, max(h - p, 0) + 1, step))
    if ys[-1] != h - p:
        ys.append(h - p)
    xs = list(range(0, max(w - p, 0) + 1, step))
    if xs[-1] != w - p:
        xs.append(w - p)
    dy, dx = np.mgrid[0:p, 0:p]
    n_done = 0
    for y0 in ys:
        for x0 in xs:
            need = todo[y0:y0 + p, x0:x0 + p]
            if not need.any():
                continue
            known = filled[y0:y0 + p, x0:x0 + p]
            tpatch = out[y0:y0 + p, x0:x0 + p].astype(np.float32)
            # candidats
            n = min(n_cand, len(cand_yx))
            idx = rng.choice(len(cand_yx), n, replace=False) if n < len(cand_yx) else np.arange(len(cand_yx))
            cs, cyx = cand_sid[idx], cand_yx[idx]
            cost = np.zeros(n, np.float32)
            # recouvrement
            kn = known & (region[y0:y0 + p, x0:x0 + p] | known)
            nk = int(kn.sum())
            gathered = np.empty((n, p, p, 3), np.float32)
            for si in np.unique(cs):
                m = cs == si
                S = sources[si].rgb
                gathered[m] = S[cyx[m, 0, None, None] + dy, cyx[m, 1, None, None] + dx]
            if nk:
                d = gathered[:, kn] - tpatch[kn][None]
                cost += (d * d).sum((1, 2)) / nk
            if F:
                tf = tgt_feat[y0:y0 + p, x0:x0 + p]
                gf = np.empty((n, p, p, F), np.float32)
                for si in np.unique(cs):
                    m = cs == si
                    gf[m] = sources[si].feat[cyx[m, 0, None, None] + dy, cyx[m, 1, None, None] + dx]
                d = (gf - tf[None]) * feat_weights
                cost += w_feat * (d * d).mean((1, 2, 3))
            if reuse_pen:
                pen = np.array([used[s][y, x] for s, (y, x) in zip(cs, cyx)], np.float32)
                cost += reuse_pen * pen
            order = np.argsort(cost)
            best = order[: max(1, top_k)]
            thr = cost[order[0]] * 1.08 + 1e-6
            best = best[cost[best] <= thr]
            pick = int(rng.choice(best))
            si, (sy, sx) = int(cs[pick]), cyx[pick]
            src = gathered[pick]
            # masque d'écriture : pixels libres + côté « nouveau » de la coupe minimale
            write = need.copy()
            imp = imposed_mask[y0:y0 + p, x0:x0 + p] if imposed_mask is not None else np.zeros((p, p), bool)
            prev_only = known & ~imp
            if prev_only.any():
                err = ((src - tpatch) ** 2).sum(-1)
                wr = np.zeros((p, p), bool)
                # bande gauche
                if x0 > 0 and prev_only[:, :o].any():
                    band = np.where(prev_only[:, :o], err[:, :o], 0)
                    cut = _min_cut_vertical(band)
                    for yy in range(p):
                        wr[yy, cut[yy]:o] = True
                    wr[:, o:] = True
                else:
                    wr[:, :] = True
                wr2 = np.zeros((p, p), bool)
                if y0 > 0 and prev_only[:o, :].any():
                    band = np.where(prev_only[:o, :], err[:o, :], 0).T
                    cut = _min_cut_vertical(band)
                    for xx in range(p):
                        wr2[cut[xx]:o, xx] = True
                    wr2[o:, :] = True
                else:
                    wr2[:, :] = True
                write |= prev_only & wr & wr2 & region[y0:y0 + p, x0:x0 + p]
            write &= region[y0:y0 + p, x0:x0 + p] | need
            sub_out = out[y0:y0 + p, x0:x0 + p]
            sub_prov = prov[y0:y0 + p, x0:x0 + p]
            sub_out[write] = src[write].astype(np.int16)
            sub_prov[write, 0] = sources[si].sid
            sub_prov[write, 1] = (sy + dy)[write]
            sub_prov[write, 2] = (sx + dx)[write]
            filled[y0:y0 + p, x0:x0 + p] |= write
            if reuse_pen:
                u = used[si]
                r = reuse_radius
                u[max(0, sy - r):sy + r + 1, max(0, sx - r):sx + r + 1] += 1.0
            n_done += 1
            if progress and n_done % 200 == 0:
                print(f"  … {n_done} patchs")
    return out, prov, filled


def check_provenance(out: np.ndarray, prov: np.ndarray, sources_rgb: dict[int, np.ndarray]) -> int:
    """Nombre de pixels dont la valeur ne correspond pas à leur pixel source déclaré (doit être 0)."""
    bad = 0
    m = prov[..., 0] >= 0
    for sid, S in sources_rgb.items():
        mm = m & (prov[..., 0] == sid)
        if mm.any():
            sv = S[prov[..., 1][mm], prov[..., 2][mm]]
            bad += int((sv != out[mm]).any(-1).sum())
    return bad
