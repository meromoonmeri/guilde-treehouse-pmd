"""Plan du Jardin secret v1 (816 × 1152 px, grille 8 px) et caractéristiques de guidage.

Classes : 0 = V (sous-bois sombre), 1 = L (pelouse), 2 = C (tapis d'herbe claire).
Le module d'origine (rayon + souche + prairie + deux arbres) est reposé tel quel
en haut, décalé de DX pixels ; le reste du jardin est dessiné ici puis synthétisé.
"""
from __future__ import annotations

import numpy as np
from scipy import ndimage as ndi

W, H = 816, 1152
DX, DY = 204, 0                     # décalage référence → carte pour le module
MODULE_REF = (40, 0, 372, 200)      # zone de la référence reposée à l'identique (x0,y0,x1,y1)
BEAM_REF = (132, 0, 275, 110)
R_CLIP = 16.0
D_SCALE = 6.0
TONE_SCALE = 60.0


def _spline(points, n=60):
    pts = np.asarray(points, float)
    out = []
    for i in range(len(pts) - 1):
        p0 = pts[max(i - 1, 0)]
        p1, p2 = pts[i], pts[i + 1]
        p3 = pts[min(i + 2, len(pts) - 1)]
        for t in np.linspace(0, 1, n, endpoint=False):
            t2, t3 = t * t, t * t * t
            out.append(0.5 * ((2 * p1) + (-p0 + p2) * t + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t2
                              + (-p0 + 3 * p1 - 3 * p2 + p3) * t3))
    out.append(pts[-1])
    return np.array(out)


# Axe du tapis : (x, y, demi-largeur)
CARPET_AXIS = [
    (400, 150, 70), (400, 200, 73), (403, 235, 92), (404, 285, 118), (402, 340, 124), (392, 405, 108),
    (372, 470, 78), (340, 540, 62), (318, 610, 58), (324, 690, 60), (366, 770, 60),
    (428, 850, 62), (466, 930, 64), (458, 1010, 66), (420, 1090, 70), (404, 1180, 72),
]
# Demi-largeur supplémentaire de pelouse de part et d'autre du tapis
LAWN_AXIS = [
    (400, 150, 120), (400, 200, 121), (402, 235, 140), (404, 285, 172), (402, 340, 186), (392, 405, 170),
    (372, 470, 140), (340, 540, 118), (318, 610, 116), (324, 690, 118), (366, 770, 114),
    (428, 850, 116), (466, 930, 120), (458, 1010, 124), (420, 1090, 128), (404, 1180, 130),
]
# Alcôves de pelouse (cx, cy, rx, ry) — la fermeture sud est masquée par le feuillage d'avant-plan
ALCOVES = [
    (215, 395, 88, 62),     # niche nord-ouest
    (606, 440, 92, 74),     # niche nord-est (grand rocher)
    (178, 650, 118, 96),    # alcôve ouest (rochers, fleurs)
    (238, 720, 90, 70),     #   prolongement vers le tapis
    (648, 892, 112, 104),   # alcôve est (arbre, fleurs)
    (580, 960, 90, 70),     #   prolongement vers le tapis
    (178, 1016, 92, 86),    # sous-bois sud-ouest
    (262, 1000, 84, 58),    #   raccord au tapis
]


def _smooth_noise(n, scale, amp, seed):
    rng = np.random.default_rng(seed)
    k = max(2, int(np.ceil(n / scale)) + 3)
    ctrl = rng.uniform(-1, 1, k)
    xs = np.arange(n) / scale
    i = np.floor(xs).astype(int)
    t = xs - i
    t = t * t * (3 - 2 * t)
    return amp * (ctrl[i] * (1 - t) + ctrl[i + 1] * t)


def _noise2d(h, w, scale, amp, seed):
    rng = np.random.default_rng(seed)
    gh, gw = int(np.ceil(h / scale)) + 2, int(np.ceil(w / scale)) + 2
    g = rng.uniform(-1, 1, (gh, gw))
    z = ndi.zoom(g, scale, order=3)[:h, :w]
    return amp * z / max(1e-6, np.abs(z).max())


def _band(axis, noise_amp, seed):
    """Bande paramétrée en y : |x - cx(y)| <= hw(y) (+ bruit indépendant à gauche et à droite)."""
    pts = _spline([(y, x, r) for x, y, r in axis], n=80)
    ys = np.arange(H)
    cx = np.interp(ys, pts[:, 0], pts[:, 1])
    hw = np.interp(ys, pts[:, 0], pts[:, 2])
    nl = _smooth_noise(H, 70, noise_amp, seed)
    nr = _smooth_noise(H, 70, noise_amp, seed + 1)
    xx = np.arange(W)[None, :]
    left = (cx - hw + nl)[:, None]
    right = (cx + hw + nr)[:, None]
    return (xx >= left) & (xx <= right)


def _blob(cx, cy, rx, ry, seed):
    yy, xx = np.mgrid[0:H, 0:W]
    d = np.sqrt(((xx - cx) / rx) ** 2 + ((yy - cy) / ry) ** 2)
    n = _noise2d(H, W, 48, 0.22, seed)
    return d + n <= 1.0


def target_classes(ref_cls: np.ndarray) -> np.ndarray:
    carpet = _band(CARPET_AXIS, 7, 11)
    lawn = _band(LAWN_AXIS, 12, 21)
    for i, (cx, cy, rx, ry) in enumerate(ALCOVES):
        lawn |= _blob(cx, cy, rx, ry, 100 + i)
    lawn |= carpet
    cls = np.zeros((H, W), np.int8)
    cls[lawn] = 1
    cls[carpet] = 2
    x0, y0, x1, y1 = MODULE_REF
    cls[y0 + DY:y1 + DY, :] = 0
    cls[y0 + DY:y1 + DY, x0 + DX:x1 + DX] = ref_cls[y0:y1, x0:x1]
    # sous la colonne du rayon : sous-bois (le faisceau recouvre tout)
    bx0, by0, bx1, by1 = BEAM_REF
    cls[by0 + DY:min(by1, 92) + DY, bx0 + DX:bx1 + DX] = 0
    return cls


BAND_STARTS = (0, 17, 36)   # début des bandes 1, 2, 3 après la ligne de transition


def target_tone() -> np.ndarray:
    """Ton du tapis en escalier (4 bandes comme la référence), ligne de départ ondulée,
    même lissage (7 px) que la mesure faite sur la référence."""
    wob = _smooth_noise(W, 60, 6, 5)
    ty = 486 + wob
    y = np.arange(H, dtype=float)[:, None] - ty[None, :]
    lvl = np.zeros((H, W))
    for i, s0 in enumerate(BAND_STARTS):
        lvl[y >= s0] = i + 1
    return ndi.uniform_filter(lvl / 3.0, 7)


UP_CLIP = 24.0
UP_SCALE = 4.0


def _dist_from_top(mask: np.ndarray) -> np.ndarray:
    """Pour chaque pixel de `mask`, nombre de pixels depuis le dernier bord rencontré en
    descendant la colonne (ombrages propres aux bords nord)."""
    h, w = mask.shape
    out = np.zeros((h, w), np.float32)
    run = np.zeros(w, np.float32)
    for y in range(h):
        run = np.where(mask[y], run + 1, 0)
        out[y] = run
    return out


def features(cls: np.ndarray, tone: np.ndarray) -> np.ndarray:
    open_ = cls >= 1
    carpet = cls == 2
    dV = ndi.distance_transform_edt(open_) - ndi.distance_transform_edt(~open_)
    dC = ndi.distance_transform_edt(carpet) - ndi.distance_transform_edt(~carpet)
    f = np.stack([
        np.clip(dV, -R_CLIP, R_CLIP) * D_SCALE,
        np.clip(dC, -R_CLIP, R_CLIP) * D_SCALE,
        tone * carpet * TONE_SCALE,
        np.clip(_dist_from_top(open_), 0, UP_CLIP) * UP_SCALE,
        np.clip(_dist_from_top(carpet), 0, UP_CLIP) * UP_SCALE,
    ], -1)
    return f.astype(np.float32)
