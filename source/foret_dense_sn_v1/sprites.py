"""Éléments ponctuels de FDENSE_V1.

* Générés puis retouchés 1:1 (pixelize.py) : arbres géants, entrée, rochers — découpés en
  canopée (au-dessus du joueur) / tronc-racines-corps (au sol).
* Canoniques exacts : fleurs de D24P11A et petits buissons de D24P31A, détourés par couleur
  (pixels hors palette cœur de l'herbe), provenance au pixel.
Ce module n'écrit aucun fichier à l'import.
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
from PIL import Image
from scipy import ndimage as ndi

import labels as LB
import pixelize as PX

HERE = Path(__file__).resolve().parent
BRUTS = HERE / "bruts"

# réglages de retouche : fichier brut → (pas de grille, passes de majorité, limite canopée en fraction de hauteur)
GENERATED = {
    "arbre_ouest": ("gen_arbre_ouest.png", 5.77, 0, 0.66),
    "arbre_est": ("gen_arbre_est.png", 6.3, 0, 0.72),
    "entree": ("gen_entree.png", 4.5, 0, 0.64),
    "rochers": ("gen_rochers.png", 15.0, 2, None),
}


class Sprite:
    def __init__(self, name, rgb, alpha, origin, layer_split=None):
        self.name = name
        self.rgb = rgb.astype(np.int16)
        self.alpha = alpha.astype(bool)
        self.origin = origin  # texte de provenance
        self.split = layer_split  # masque bool « canopée » ou None
        self.prov = None  # (h,w,3) pour les sprites canoniques

    @property
    def shape(self):
        return self.alpha.shape


def _retouch(fname, pitch, maj, subpal):
    rgb = np.array(Image.open(BRUTS / fname).convert("RGB"))
    a = PX.magenta_alpha(rgb)
    ys, xs = np.nonzero(a)
    crop = (slice(max(0, ys.min() - 2), ys.max() + 3), slice(max(0, xs.min() - 2), xs.max() + 3))
    return PX.pixelize(rgb[crop], a[crop], pitch, subpal, majority=maj)


def canopy_split(rgb: np.ndarray, alpha: np.ndarray, limit_frac: float) -> np.ndarray:
    """Canopée = plus grande composante verte (8-connexe) restreinte au-dessus de la limite,
    plus les pixels verts qui y sont rattachés au-dessus de la limite. Le reste (bois, touffes
    d'herbe basses, pierres, fleurs) reste au sol."""
    mat = PX.material_of(rgb.astype(np.uint8))
    green = alpha & (mat == 0)
    h = alpha.shape[0]
    lim = int(round(h * limit_frac))
    upper = green.copy()
    upper[lim:] = False
    cc, n = ndi.label(upper, np.ones((3, 3)))
    if n == 0:
        return np.zeros_like(alpha)
    sizes = ndi.sum(upper, cc, range(1, n + 1))
    keep = np.zeros(n + 1, bool)
    keep[1:] = sizes >= max(40, sizes.max() * 0.02)
    can = keep[cc]
    # pixels sombres/bois entièrement entourés par la canopée (ombres internes) → canopée
    filled = ndi.binary_fill_holes(can) & alpha
    filled[lim:] = can[lim:]
    return filled


def generated_sprites(subpal=None) -> dict[str, Sprite]:
    if subpal is None:
        subpal, _ = PX.ref_subpalettes()
    out = {}
    for name, (fname, pitch, maj, lim) in GENERATED.items():
        rgb, a = _retouch(fname, pitch, maj, subpal)
        origin = f"généré ({fname}) puis retouché 1:1 : pas {pitch}, vote majoritaire, palette D24P11A/D24P31A"
        if name == "rochers":
            cc, n = ndi.label(a, np.ones((3, 3)))
            objs = ndi.find_objects(cc)
            items = sorted([(sl[1].start, i + 1, sl) for i, sl in enumerate(objs)])
            for k, (_, lab_id, sl) in enumerate(items):
                m = cc[sl] == lab_id
                if m.sum() < 60:
                    continue
                matm = PX.material_of(rgb[sl].astype(np.uint8))
                if ((matm == 1) | (matm == 3))[m].mean() > 0.03:
                    continue  # rocher à mousse jaune écarté (hors style des rochers gris de la référence)
                out[f"rocher_{k}"] = Sprite(f"rocher_{k}", np.where(m[..., None], rgb[sl], 0), m, origin)
            continue
        split = canopy_split(rgb, a, lim)
        out[name] = Sprite(name, rgb, a, origin, split)
    return out


def canonical_flowers(A: np.ndarray, la: np.ndarray):
    """Fleurs de D24P11A : pixels des boîtes FLEUR hors palette cœur de l'herbe, composante centrale."""
    k = (A[..., 0].astype(np.int64) << 16) | (A[..., 1].astype(np.int64) << 8) | A[..., 2]
    res = []
    fl = la == LB.FLEUR
    cc, n = ndi.label(fl)
    for i, sl in enumerate(ndi.find_objects(cc)):
        box = cc[sl] == (i + 1)
        sub_k = k[sl]
        mat = PX.material_of(A[sl].astype(np.uint8))
        petal = np.isin(sub_k, [0xc76f47, 0xd79f6f, 0xcfcf57, 0xd7d77f, 0xb7d787])
        m = box & ~np.isin(sub_k, LB.GRASS_CORE) & ((mat != 1) | petal)
        m = ndi.binary_opening(m, np.ones((2, 2))) | (m & ndi.binary_dilation(
            ndi.binary_opening(m, np.ones((2, 2))), np.ones((3, 3))))
        c2, n2 = ndi.label(m, np.ones((3, 3)))
        if n2 == 0:
            continue
        sizes = ndi.sum(m, c2, range(1, n2 + 1))
        m = c2 == (1 + int(np.argmax(sizes)))
        m = ndi.binary_fill_holes(m)
        if m.sum() < 20:
            continue
        ys, xs = np.nonzero(m)
        y0, y1, x0, x1 = ys.min(), ys.max() + 1, xs.min(), xs.max() + 1
        mm = m[y0:y1, x0:x1]
        gy, gx = sl[0].start + y0, sl[1].start + x0
        rgb = A[gy:gy + (y1 - y0), gx:gx + (x1 - x0)].copy()
        s = Sprite(f"fleur_A{i}", rgb, mm, f"canonique D24P11A ({gx},{gy})")
        yy, xx = np.mgrid[0:mm.shape[0], 0:mm.shape[1]]
        s.prov = np.stack([np.zeros_like(yy), yy + gy, xx + gx], -1).astype(np.int32)
        res.append(s)
    return res


def canonical_bushes(B: np.ndarray, lb: np.ndarray):
    """Petits buissons sombres de D24P31A : pixels des boîtes BUISSON hors herbe claire du couloir."""
    res = []
    bu = lb == LB.BUISSON
    cc, n = ndi.label(bu)
    lum = LB.luminance(B)
    for i, sl in enumerate(ndi.find_objects(cc)):
        box = cc[sl] == (i + 1)
        sub = B[sl]
        r, g, b = sub[..., 0].astype(int), sub[..., 1].astype(int), sub[..., 2].astype(int)
        dark = (lum[sl] < 70) | ((b > 0x27) & (g < 0x70))  # buisson sombre bleuté + contour
        m = box & dark
        m = ndi.binary_opening(m, np.ones((2, 2)))
        c2, n2 = ndi.label(m, np.ones((3, 3)))
        if n2 == 0:
            continue
        sizes = ndi.sum(m, c2, range(1, n2 + 1))
        m = c2 == (1 + int(np.argmax(sizes)))
        m = ndi.binary_fill_holes(m)
        ys, xs = np.nonzero(m)
        y0, y1, x0, x1 = ys.min(), ys.max() + 1, xs.min(), xs.max() + 1
        mm = m[y0:y1, x0:x1]
        gy, gx = sl[0].start + y0, sl[1].start + x0
        rgb = B[gy:gy + (y1 - y0), gx:gx + (x1 - x0)].copy()
        s = Sprite(f"buisson_B{i}", rgb, mm, f"canonique D24P31A ({gx},{gy})")
        yy, xx = np.mgrid[0:mm.shape[0], 0:mm.shape[1]]
        s.prov = np.stack([np.ones_like(yy), yy + gy, xx + gx], -1).astype(np.int32)
        res.append(s)
    return res
