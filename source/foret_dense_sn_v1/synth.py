"""Synthèse canonique des matières de FDENSE_V1 : sol, ombre, chemin, parois.

Chaque étape copie des pixels exacts de D24P11A (id 0) / D24P31A (id 1) et tient la provenance.
Ordre : sol clair L → ombre S (contrainte par L) → chemin P (contraint par le sol) → parois.
Ce module n'écrit aucun fichier à l'import.
"""
from __future__ import annotations

import numpy as np
from scipy import ndimage as ndi

import labels as LB
import layout as LY
from pmdsynth import Source, quilt


def _merge_prov(prov_new: np.ndarray, prov_base: np.ndarray) -> np.ndarray:
    out = prov_new.copy()
    m = out[..., 0] == -2
    out[m] = prov_base[m]
    return out


def _norm_conv(values: np.ndarray, mask: np.ndarray, sigma: float) -> np.ndarray:
    num = ndi.gaussian_filter(np.where(mask, values, 0).astype(np.float32), sigma)
    den = ndi.gaussian_filter(mask.astype(np.float32), sigma)
    return num / np.maximum(den, 1e-3)


class Refs:
    def __init__(self):
        self.A = LB.load_ref(0)
        self.B = LB.load_ref(1)
        self.la = LB.labels_A(self.A)
        self.lb = LB.labels_B(self.B)
        self.rgb = {0: self.A, 1: self.B}
        self.lab = {0: self.la, 1: self.lb}

    def label_of(self, prov: np.ndarray) -> np.ndarray:
        """Classe de matière de chaque pixel via sa provenance (-1 si pas de provenance)."""
        out = np.full(prov.shape[:2], -1, np.int16)
        for sid, lab in self.lab.items():
            m = prov[..., 0] == sid
            out[m] = lab[prov[..., 1][m], prov[..., 2][m]]
        return out


def synth_ground(R: Refs, seed: int = 1):
    """Sol clair : herbe au soleil stricte de A, carte entière."""
    src = Source(0, R.A, None, LB.grass_source_mask(R.A, R.la))
    out, prov, _ = quilt((LY.H, LY.W), [src], patch=32, overlap=10, n_cand=2000,
                         reuse_pen=2000.0, reuse_radius=10, top_k=3, seed=seed)
    return out, prov


def shade_feature(R: Refs):
    """Niveau d'ombre local des sources (0 = soleil de A, 1 = cœur du cercle sombre de B)."""
    lumA, lumB = LB.luminance(R.A), LB.luminance(R.B)
    gA = LB.grass_source_mask(R.A, R.la)
    mB = LB.shade_source_mask(R.B, R.lb)
    l_sun = float(lumA[gA].mean())
    core = np.zeros(mB.shape, bool); core[10:80, 205:300] = True
    l_dark = float(lumB[core & mB].mean())
    locA = _norm_conv(lumA, gA, 5.0)
    locB = _norm_conv(lumB, mB, 5.0)
    sA = np.clip((l_sun - locA) / (l_sun - l_dark), 0, 1)
    sB = np.clip((l_sun - locB) / (l_sun - l_dark), 0, 1)
    return sA.astype(np.float32), sB.astype(np.float32), gA, mB


def synth_shade(R: Refs, L: np.ndarray, provL: np.ndarray, lay, seed: int = 2):
    """Herbe ombrée : sources A (soleil) + B (couloir, pénombre, cercle sombre), guidée par la carte d'ombre."""
    sA, sB, gA, mB = shade_feature(R)
    srcs = [Source(0, R.A, sA[..., None] * 4.0, gA), Source(1, R.B, sB[..., None] * 4.0, mB)]
    shade = lay["shade"]
    walls = lay["wall_l"] | lay["wall_r"]
    deep = ndi.distance_transform_edt(walls) > 20
    region = (shade > 0.03) & ~deep
    imposed_mask = ~region
    tf = (shade * 4.0)[..., None].astype(np.float32)
    out, prov, _ = quilt((LY.H, LY.W), srcs, tf, patch=24, overlap=8, region=region, imposed=L,
                         imposed_mask=imposed_mask, w_feat=2500.0, n_cand=2500, reuse_pen=1500.0,
                         reuse_radius=8, top_k=3, seed=seed)
    return out, _merge_prov(prov, provL), region


def dark_mask_B(R: Refs) -> np.ndarray:
    """Cercle sombre de B nettoyé (plus grande composante, trous bouchés)."""
    m = R.lb == LB.HERBE_SOMBRE
    m = ndi.binary_closing(np.pad(m, 8, mode="edge"), np.ones((7, 7)))[8:-8, 8:-8]
    m = ndi.binary_fill_holes(np.pad(m, ((1, 0), (0, 0)), constant_values=1))[1:]
    m = ndi.binary_opening(m, np.ones((5, 5)))
    cc, n = ndi.label(m)
    if n > 1:
        sizes = ndi.sum(m, cc, range(1, n + 1))
        m = cc == (1 + int(np.argmax(sizes)))
    return m


def _shade_features(mask: np.ndarray):
    d = LB.signed_distance(mask)
    dc = np.clip(d, -16, 16) / 4.0
    gy, gx = np.gradient(ndi.gaussian_filter(d, 3.0))
    nrm = np.sqrt(gx * gx + gy * gy) + 1e-6
    near = np.clip(1.0 - np.abs(d) / 20.0, 0, 1)
    return np.stack([dc, gx / nrm * near * 1.5, gy / nrm * near * 1.5], -1).astype(np.float32)


def synth_shade_shape(R: Refs, L: np.ndarray, provL: np.ndarray, dark_t: np.ndarray, walls: np.ndarray,
                      seed: int = 2):
    """Zone d'ombre à liseré canonique : distance signée au bord du cercle sombre de B → forme cible."""
    dmB = dark_mask_B(R)
    fB = _shade_features(dmB)
    okB = LB.shade_source_mask(R.B, R.lb) & ndi.binary_dilation(dmB, np.ones((41, 41)))
    okB &= ~ndi.binary_dilation(np.isin(R.lb, [LB.FLEUR, LB.MUR, LB.ROCHER, LB.BUISSON, LB.CHEMIN]),
                                np.ones((3, 3)))
    src = Source(1, R.B, fB, okB)
    ft = _shade_features(dark_t)
    deep = ndi.distance_transform_edt(walls) > 24
    region = ndi.binary_dilation(dark_t, np.ones((33, 33))) & ~deep
    out, prov, _ = quilt((LY.H, LY.W), [src], ft, patch=24, overlap=8, region=region, imposed=L,
                         imposed_mask=~region, w_feat=4000.0, n_cand=3000, reuse_pen=1200.0,
                         reuse_radius=8, top_k=3, seed=seed)
    return out, _merge_prov(prov, provL), region


def _edge_features(mask: np.ndarray, clip_in: float, clip_out: float, scale: float):
    """(distance signée écrêtée, composante x de la normale intérieure pondérée près du bord)."""
    d = LB.signed_distance(mask)
    dc = np.clip(d, -clip_out, clip_in)
    gy, gx = np.gradient(ndi.gaussian_filter(d, 2.0))
    nrm = np.sqrt(gx * gx + gy * gy) + 1e-6
    nx = gx / nrm
    near = np.clip(1.0 - np.abs(d) / (clip_in + 4), 0, 1)
    return np.stack([dc * scale, nx * near * 2.0], -1).astype(np.float32)


def synth_path(R: Refs, G: np.ndarray, provG: np.ndarray, lay, seed: int = 3):
    """Chemin de terre de A, guidé par la distance signée au bord et le côté (gauche/droite)."""
    pa = LB.path_mask_A(R.la)
    fa = _edge_features(pa, 12, 10, 0.25)
    # sources : bande du chemin de A (chemin + herbe riveraine), sans tunnel/rochers/fleurs/canopées
    band = ndi.binary_dilation(pa, np.ones((21, 21))) & np.isin(R.la, [LB.HERBE, LB.CHEMIN])
    band &= ~ndi.binary_dilation(np.isin(R.la, [LB.TUNNEL, LB.ROCHER, LB.FLEUR, LB.CANOPEE_A]), np.ones((3, 3)))
    src = Source(0, R.A, fa, band)
    path = lay["path"]
    ft = _edge_features(path, 12, 10, 0.25)
    margin = ndi.binary_dilation(path, np.ones((9, 9))) & (lay["shade"] < 0.3)
    region = path | margin
    out, prov, _ = quilt((LY.H, LY.W), [src], ft, patch=24, overlap=8, region=region, imposed=G,
                         imposed_mask=~region, w_feat=3000.0, n_cand=2500, reuse_pen=1500.0,
                         reuse_radius=8, top_k=3, seed=seed)
    return out, _merge_prov(prov, provG), region


def _wall_source(R: Refs, side: str):
    wall = R.lb == LB.MUR
    h, w = wall.shape
    xx = np.arange(w)[None, :].repeat(h, 0)
    if side == "ouest":
        mine = wall & (xx < w // 2)
    else:
        mine = wall & (xx >= w // 2)
    # masque de paroi du côté voulu = composante touchant le bord correspondant
    cc, _ = ndi.label(mine)
    edge_ids = np.unique(cc[:, 0] if side == "ouest" else cc[:, -1])
    mine = np.isin(cc, edge_ids[edge_ids > 0])
    feat = _edge_features(mine, 28, 14, 1.0 / 6.0)
    allowed = mine | (ndi.binary_dilation(mine, np.ones((29, 29))) &
                      np.isin(R.lb, [LB.HERBE, LB.HERBE_SOMBRE]))
    if side == "ouest":
        allowed &= xx < w // 2 + 40
    else:
        allowed &= xx >= w // 2 - 40
    return feat, allowed


def synth_walls(R: Refs, lay, seed: int = 4):
    """Parois d'arbres : paroi ouest de B → paroi ouest, paroi est de B → paroi est (+ premier plan)."""
    res = {}
    for side, key, sd in (("ouest", "wall_l", seed), ("est", "wall_r", seed + 1)):
        feat, allowed = _wall_source(R, side)
        src = Source(1, R.B, feat, allowed)
        fg = lay["foreground"]
        xx = np.arange(LY.W)[None, :]
        fg_side = fg & ((xx < LY.W // 2) if side == "ouest" else (xx >= LY.W // 2))
        mask = lay[key] | fg_side
        ft = _edge_features(mask, 28, 14, 1.0 / 6.0)
        region = ndi.binary_dilation(mask, np.ones((25, 25)))
        out, prov, _ = quilt((LY.H, LY.W), [src], ft, patch=40, overlap=12, region=region,
                             w_feat=2500.0, n_cand=2500, reuse_pen=1500.0, reuse_radius=10,
                             top_k=3, seed=sd)
        res[side] = (out, prov, mask, region)
    return res
