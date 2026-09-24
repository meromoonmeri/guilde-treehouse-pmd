"""Synthèse guidée par patchs (image quilting + texture transfer, Efros & Freeman 2001).

Chaque pixel produit est COPIÉ d'un pixel de l'exemplaire (la référence canonique) :
pas de mélange, pas de filtrage, pas de couleur nouvelle. La carte `src` (y, x)
garde la provenance de chaque pixel.

Coût d'un candidat (u, v) pour un bloc de cible (y, x) :
    w_ov * Σ_M ||E - T||²              (raccord avec les pixels déjà posés / imposés)
  + w_f  * Σ_B ||F_e - F_t||²          (correspondance du plan : distances aux bords, ton)
Calcul par FFT sur toute la référence ; coupe minimale (programmation dynamique)
dans les zones de recouvrement avec les patchs précédents. Les pixels imposés
(module d'origine) ne sont jamais réécrits.
"""
from __future__ import annotations

import numpy as np
from numpy.fft import irfft2, rfft2


def _min_cut_vertical(err: np.ndarray) -> np.ndarray:
    """err (h, o) → pour chaque ligne, index de colonne de coupe (pixels >= coupe = nouveau)."""
    h, o = err.shape
    cost = err.copy()
    back = np.zeros((h, o), int)
    for i in range(1, h):
        for j in range(o):
            lo, hi = max(0, j - 1), min(o, j + 2)
            k = lo + int(np.argmin(cost[i - 1, lo:hi]))
            back[i, j] = k
            cost[i, j] += cost[i - 1, k]
    cut = np.zeros(h, int)
    cut[-1] = int(np.argmin(cost[-1]))
    for i in range(h - 1, 0, -1):
        cut[i - 1] = back[i, cut[i]]
    return cut


class Quilter:
    def __init__(self, exemplar_rgb: np.ndarray, feats_e: np.ndarray, valid_px: np.ndarray,
                 block: int = 24, overlap: int = 8, w_ov: float = 1.0, w_f: float = 1.0,
                 tol: float = 0.08, seed: int = 0, reuse_penalty: float = 4000.0, reuse_radius: int = 6):
        self.E = exemplar_rgb.astype(np.float64)
        self.Fe = feats_e.astype(np.float64)
        self.B, self.O = block, overlap
        self.S = block - overlap
        self.w_ov, self.w_f, self.tol = w_ov, w_f, tol
        self.rng = np.random.default_rng(seed)
        self.reuse_penalty, self.reuse_radius = reuse_penalty, reuse_radius
        H, W, _ = self.E.shape
        self.H, self.W = H, W
        self.P = (H + block, W + block)
        B = block
        # candidats valides : bloc entier dans des pixels autorisés
        inv = (~valid_px).astype(np.float64)
        ii = np.pad(inv.cumsum(0).cumsum(1), ((1, 0), (1, 0)))
        box = ii[B:, B:] - ii[:-B, B:] - ii[B:, :-B] + ii[:-B, :-B]
        self.valid = box[: H - B + 1, : W - B + 1] < 0.5
        # FFT pré-calculées
        self.fE = [rfft2(self.E[..., c], s=self.P) for c in range(3)]
        self.fE2 = rfft2((self.E ** 2).sum(-1), s=self.P)
        self.fF = [rfft2(self.Fe[..., c], s=self.P) for c in range(self.Fe.shape[-1])]
        f2 = (self.Fe ** 2).sum(-1)
        ii2 = np.pad(f2.cumsum(0).cumsum(1), ((1, 0), (1, 0)))
        self.boxF2 = (ii2[B:, B:] - ii2[:-B, B:] - ii2[B:, :-B] + ii2[:-B, :-B])[: H - B + 1, : W - B + 1]

    def _corr_spec(self, k: np.ndarray) -> np.ndarray:
        return rfft2(k[::-1, ::-1], s=self.P)

    def _extract(self, spec: np.ndarray) -> np.ndarray:
        r = irfft2(spec, s=self.P)
        B = self.B
        return r[B - 1: B - 1 + self.H - B + 1, B - 1: B - 1 + self.W - B + 1]

    def synth(self, feats_t: np.ndarray, fixed_rgb: np.ndarray | None = None,
              fixed_src: np.ndarray | None = None, fixed_mask: np.ndarray | None = None,
              progress: bool = True):
        Ht, Wt, _ = feats_t.shape
        B, O, S = self.B, self.O, self.S
        nby = int(np.ceil((Ht - O) / S))
        nbx = int(np.ceil((Wt - O) / S))
        PH, PW = nby * S + O, nbx * S + O
        T = np.zeros((PH, PW, 3))
        src = np.full((PH, PW, 2), -1, np.int32)
        filled = np.zeros((PH, PW), bool)
        fixed = np.zeros((PH, PW), bool)
        Ft = np.zeros((PH, PW, feats_t.shape[-1]))
        Ft[:Ht, :Wt] = feats_t
        Ft[Ht:, :Wt] = feats_t[-1:, :, :]
        Ft[:, Wt:] = Ft[:, Wt - 1: Wt]
        if fixed_mask is not None:
            fm = np.zeros((PH, PW), bool)
            fm[:Ht, :Wt] = fixed_mask
            T[:Ht, :Wt][fixed_mask] = fixed_rgb[fixed_mask]
            src[:Ht, :Wt][fixed_mask] = fixed_src[fixed_mask]
            filled |= fm
            fixed |= fm
        picks = []
        usage = np.zeros(self.valid.shape, np.float64)
        for by in range(nby):
            for bx in range(nbx):
                y, x = by * S, bx * S
                blk_fixed = fixed[y:y + B, x:x + B]
                if blk_fixed.all():
                    continue
                M = filled[y:y + B, x:x + B].astype(np.float64)
                Tb = T[y:y + B, x:x + B]
                Fb = Ft[y:y + B, x:x + B]
                spec = np.zeros_like(self.fE2)
                # terme recouvrement
                w = self.w_ov
                for c in range(3):
                    spec += -2 * w * self._corr_spec(M * Tb[..., c]) * self.fE[c]
                spec += w * self._corr_spec(M) * self.fE2
                # terme plan
                wf = self.w_f
                for c in range(Fb.shape[-1]):
                    spec += -2 * wf * self._corr_spec(Fb[..., c]) * self.fF[c]
                cost = self._extract(spec) + wf * self.boxF2
                cost += w * (M[..., None] * Tb ** 2).sum() + wf * (Fb ** 2).sum()
                cost = cost + self.reuse_penalty * usage
                cost = np.where(self.valid, cost, np.inf)
                cmin = cost.min()
                cand = np.argwhere(cost <= cmin + abs(cmin) * self.tol + 1e-6)
                u, v = cand[self.rng.integers(len(cand))]
                rr = self.reuse_radius
                usage[max(0, u - rr):u + rr + 1, max(0, v - rr):v + rr + 1] += 1
                patch = self.E[u:u + B, v:v + B]
                # masque d'écriture : coupe minimale sur les recouvrements avec les patchs posés
                write = np.ones((B, B), bool)
                err = ((patch - Tb) ** 2).sum(-1)
                prev = filled[y:y + B, x:x + B] & ~blk_fixed
                if bx > 0 and prev[:, :O].any():
                    cut = _min_cut_vertical(np.where(prev[:, :O], err[:, :O], 0.0))
                    for i in range(B):
                        write[i, :cut[i]] &= ~prev[i, :cut[i]]
                if by > 0 and prev[:O, :].any():
                    cut = _min_cut_vertical(np.where(prev[:O, :], err[:O, :], 0.0).T)
                    for j in range(B):
                        write[:cut[j], j] &= ~prev[:cut[j], j]
                write &= ~blk_fixed
                sl = (slice(y, y + B), slice(x, x + B))
                T[sl][write] = patch[write]
                yy, xx = np.mgrid[0:B, 0:B]
                s2 = np.stack([yy + u, xx + v], -1)
                src[sl][write] = s2[write]
                filled[sl] |= write
                picks.append((int(y), int(x), int(u), int(v)))
            if progress and by % 8 == 0:
                print(f"  rangée {by + 1}/{nby}", flush=True)
        return T[:Ht, :Wt].astype(np.uint8), src[:Ht, :Wt], picks
