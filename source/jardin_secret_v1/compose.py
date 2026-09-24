"""Jardin secret v1 — objets, feuillage immersif d'avant-plan, calques jour/nuit.

Tous les pixels viennent de `secretgarden.png` (translation seule) :
  * sol : synthèse guidée (build_ground.py), provenance pixel par pixel ;
  * objets : sprites détourés (segment.py), posés par translation entière ;
  * feuillage d'avant-plan : synthèse guidée de la frange sombre de la référence,
    silhouette par seuil sur les teintes de feuillage (g <= 151), pixels exacts.
Nuit : filtre Abyss exact (source/cote_v4_abyss/night.py), appliqué une seule fois.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
from PIL import Image
from scipy import ndimage as ndi

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(ROOT / "source" / "cote_v4_abyss"))
import layout as L  # noqa: E402
from build_ground import exemplar  # noqa: E402
from night import night  # noqa: E402
from quilt import Quilter  # noqa: E402

SEG = HERE / "segmentation"
WORK = HERE / "travail"
SPR = json.loads((SEG / "sprites.json").read_text())

# ---------------------------------------------------------------------------
# Placements. Objets du module : position d'origine + (DX, DY).
MODULE_OBJECTS = ["rayon", "souche", "rocher_double", "arbre_ouest", "arbre_est"] + \
    [k for k in SPR if k.startswith("fleur_")]

# Nouveaux placements : (sprite, x_pied, y_pied) = centre bas du sprite
# positions souhaitées ; `snap` les recale sur la pelouse (hors tapis) au plus près
TREES = [
    ("arbre_est", 150, 440), ("arbre_ouest", 680, 520), ("arbre_est", 96, 700),
    ("arbre_ouest", 736, 950), ("arbre_est", 120, 1060), ("arbre_ouest", 520, 640),
    ("arbre_est", 290, 560),
]
ROCKS = [
    ("rocher_haut", 628, 470), ("rocher_s2", 580, 488), ("rocher_s1", 262, 430),
    ("rocher_paire", 190, 718), ("rocher_s3", 262, 690), ("rocher_s4", 128, 640),
    ("rocher_haut", 662, 930), ("rocher_s1", 600, 952), ("rocher_s2", 238, 1040),
    ("rocher_s4", 520, 1128), ("rocher_s3", 300, 860), ("rocher_s1", 512, 780),
    ("rocher_paire", 560, 1000),
]
# Bouquets de fleurs : (cx, cy, rayon, nombre, graine)
FLOWER_BEDS = [
    (200, 380, 46, 9, 1), (170, 640, 60, 14, 2), (236, 600, 34, 6, 3),
    (650, 880, 58, 14, 4), (620, 420, 40, 8, 5), (180, 1000, 44, 9, 6), (700, 960, 30, 5, 7),
]
# Masses de feuillage d'avant-plan (cx, cy, rx, ry)
FOLIAGE = [
    # cadre gauche
    (-10, 300, 60, 110), (10, 470, 70, 80), (-20, 600, 70, 120), (20, 800, 80, 70),
    (-10, 930, 70, 110),
    # cadre droit
    (830, 330, 70, 120), (800, 480, 60, 70), (835, 640, 80, 130), (800, 780, 60, 80),
    (830, 1090, 90, 120),
    # fermetures sud des alcôves (masquent aussi les raccords orientés sud)
    (210, 470, 92, 34), (620, 536, 90, 38), (150, 770, 120, 40), (655, 1022, 110, 44),
    (190, 1112, 110, 46),
    # cadre haut, de part et d'autre de la trouée du rayon
    (-20, 110, 130, 150), (836, 100, 130, 160), (170, -14, 150, 56), (640, -14, 150, 56),
    # feuilles pendantes au-dessus des épaules de la clairière
    (560, 250, 44, 30), (240, 250, 44, 30),
    # entrée sud : tunnel de feuillage
    (150, 1160, 190, 58), (680, 1160, 190, 62), (300, 1180, 70, 40), (530, 1178, 70, 40),
]


def load_sprite(name: str) -> np.ndarray:
    return np.array(Image.open(SEG / f"{name}.png").convert("RGBA"))


def paste(layer: np.ndarray, spr: np.ndarray, x: int, y: int, src_layer=None, ox=0, oy=0):
    h, w = spr.shape[:2]
    H, W = layer.shape[:2]
    x0, y0 = max(0, x), max(0, y)
    x1, y1 = min(W, x + w), min(H, y + h)
    if x0 >= x1 or y0 >= y1:
        return
    s = spr[y0 - y:y1 - y, x0 - x:x1 - x]
    m = s[..., 3] > 0
    layer[y0:y1, x0:x1][m] = s[m]
    if src_layer is not None:
        yy, xx = np.mgrid[y0 - y:y1 - y, x0 - x:x1 - x]
        src_layer[y0:y1, x0:x1][m] = np.stack([yy + oy, xx + ox], -1)[m]


def split_tree(spr: np.ndarray):
    """Cime (au-dessus du joueur) / tronc + ombre (sous le joueur), par teinte."""
    r, g = spr[..., 0].astype(int), spr[..., 1].astype(int)
    a = spr[..., 3] > 0
    canopy = a & (g - r >= 40) & (g >= 100)
    canopy = ndi.binary_opening(canopy, np.ones((2, 2))) & a
    # le bas du feuillage qui touche le tronc reste dans la cime ; l'ombre au sol non
    lo = spr.copy()
    lo[canopy] = 0
    hi = spr.copy()
    hi[~canopy] = 0
    return lo, hi


def foliage_layer(ref, fe, valid, cls_ground, seed=3):
    yy, xx = np.mgrid[0:L.H, 0:L.W]
    m = np.zeros((L.H, L.W), bool)
    for i, (cx, cy, rx, ry) in enumerate(FOLIAGE):
        d = np.sqrt(((xx - cx) / rx) ** 2 + ((yy - cy) / ry) ** 2)
        m |= d + L._noise2d(L.H, L.W, 40, 0.18, 300 + i) <= 1.0
    cls = np.where(m, 0, 1).astype(np.int8)
    ft = L.features(cls, np.zeros((L.H, L.W)))
    q = Quilter(ref, fe, valid, block=24, overlap=8, tol=0.06, seed=seed)
    rgb, src, _ = q.synth(ft, progress=False)
    g = rgb[..., 1].astype(int)
    # au-dessus du sous-bois : seulement les feuilles sombres (g <= 119), sinon frange complète
    over_void = ndi.binary_erosion(cls_ground == 0, np.ones((5, 5)))
    leafy = np.where(over_void, g <= 119, g <= 151)
    alpha = leafy & ndi.binary_dilation(m, np.ones((25, 25)))
    # nettoyage : retirer les poussières, boucher les trous intérieurs
    lab, n = ndi.label(alpha)
    if n:
        sizes = ndi.sum(alpha, lab, range(1, n + 1))
        alpha &= np.isin(lab, 1 + np.nonzero(sizes >= 40)[0])
    alpha = ndi.binary_fill_holes(alpha) & (leafy | m)
    out = np.zeros((L.H, L.W, 4), np.uint8)
    out[..., :3] = rgb
    out[..., 3] = np.where(alpha, 255, 0)
    src = np.where(alpha[..., None], src, -1)
    return out, src, m


def snap(cls_t, fx, fy, half_w, min_carpet=10, max_void=None, search=90):
    """Point le plus proche de (fx, fy) dont l'empreinte au sol est de la pelouse, à au moins
    `min_carpet` px du tapis et (optionnel) à au plus `max_void` px du sous-bois."""
    lawn = cls_t == 1
    d_carpet = ndi.distance_transform_edt(cls_t != 2)
    d_void = ndi.distance_transform_edt(cls_t != 0)
    best = None
    for dy in range(-search, search + 1, 2):
        for dx in range(-search, search + 1, 2):
            x, y = fx + dx, fy + dy
            if not (half_w <= x < L.W - half_w and 8 <= y < L.H - 2):
                continue
            fp = lawn[y - 6:y, x - half_w:x + half_w]
            if not fp.all() or d_carpet[y - 6:y, x - half_w:x + half_w].min() < min_carpet:
                continue
            if max_void is not None and d_void[y - 3, x] > max_void:
                continue
            dd = dx * dx + dy * dy
            if best is None or dd < best[0]:
                best = (dd, x, y)
    return (best[1], best[2]) if best else (fx, fy)


def flower_positions():
    names = [k for k in SPR if k.startswith("fleur_") and SPR[k]["pixels"] >= 38]
    out = []
    for cx, cy, r, n, seed in FLOWER_BEDS:
        rng = np.random.default_rng(seed)
        pts = []
        tries = 0
        while len(pts) < n and tries < 500:
            tries += 1
            a, d = rng.uniform(0, 2 * np.pi), r * np.sqrt(rng.uniform(0, 1))
            x, y = cx + d * np.cos(a), cy + d * np.sin(a) * 0.8
            if all((x - px) ** 2 + (y - py) ** 2 > 14 ** 2 for px, py in pts):
                pts.append((x, y))
        for x, y in pts:
            out.append((names[rng.integers(len(names))], int(x), int(y)))
    return out


def compose():
    ref, rcls, rtone, objects, valid, fe = exemplar()
    refrgba = np.array(Image.open(ROOT / "secretgarden.png").convert("RGBA"))
    sol = np.load(WORK / "sol.npz")
    cls_t = sol["cls"]
    H, W = L.H, L.W
    layers = {k: np.zeros((H, W, 4), np.uint8) for k in
              ["02_fleurs", "03_rochers", "04_souche", "05_arbres_troncs", "06_arbres_cimes",
               "07_rayon", "08_feuillage_avant"]}
    srcs = {k: np.full((H, W, 2), -1, np.int32) for k in layers}
    ground = np.zeros((H, W, 4), np.uint8)
    ground[..., :3] = sol["rgb"]
    ground[..., 3] = 255
    placements = []
    warnings = []

    def on_lawn(x, y, r=3):
        y0, y1 = max(0, y - r), min(H, y + r)
        x0, x1 = max(0, x - r), min(W, x + r)
        return bool((cls_t[y0:y1, x0:x1] >= 1).all())

    # 1) objets du module, position d'origine
    for name in MODULE_OBJECTS:
        spr = load_sprite(name)
        ox, oy = SPR[name]["origine_ref"]
        x, y = ox + L.DX, oy + L.DY
        if name.startswith("fleur_"):
            key = "02_fleurs"
        elif name == "rayon":
            key = "07_rayon"
        elif name == "souche":
            key = "04_souche"
        elif name.startswith("rocher"):
            key = "03_rochers"
        else:
            lo, hi = split_tree(spr)
            paste(layers["05_arbres_troncs"], lo, x, y, srcs["05_arbres_troncs"], ox, oy)
            paste(layers["06_arbres_cimes"], hi, x, y, srcs["06_arbres_cimes"], ox, oy)
            placements.append({"sprite": name, "x": x, "y": y, "module": True})
            continue
        paste(layers[key], spr, x, y, srcs[key], ox, oy)
        placements.append({"sprite": name, "x": x, "y": y, "module": True, "calque": key})

    # 2) nouveaux arbres, rochers, fleurs (tri par y pour l'ordre de profondeur)
    trees = [(n, *snap(cls_t, fx, fy, 12, min_carpet=14, max_void=34)) for n, fx, fy in TREES]
    rocks = [(n, *snap(cls_t, fx, fy, max(4, load_sprite(n).shape[1] // 3), min_carpet=6))
             for n, fx, fy in ROCKS]
    for name, fx, fy in sorted(trees, key=lambda t: t[2]):
        spr = load_sprite(name)
        h, w = spr.shape[:2]
        x, y = fx - w // 2, fy - h
        if not on_lawn(fx, fy - 4, 4):
            warnings.append(f"arbre {name} pied hors pelouse ({fx},{fy})")
        lo, hi = split_tree(spr)
        ox, oy = SPR[name]["origine_ref"]
        paste(layers["05_arbres_troncs"], lo, x, y, srcs["05_arbres_troncs"], ox, oy)
        paste(layers["06_arbres_cimes"], hi, x, y, srcs["06_arbres_cimes"], ox, oy)
        placements.append({"sprite": name, "x": x, "y": y, "pied": [fx, fy]})
    for name, fx, fy in sorted(rocks, key=lambda t: t[2]):
        spr = load_sprite(name)
        h, w = spr.shape[:2]
        x, y = fx - w // 2, fy - h
        if not on_lawn(fx, fy - 3, 3):
            warnings.append(f"rocher {name} hors pelouse ({fx},{fy})")
        ox, oy = SPR[name]["origine_ref"]
        paste(layers["03_rochers"], spr, x, y, srcs["03_rochers"], ox, oy)
        placements.append({"sprite": name, "x": x, "y": y, "pied": [fx, fy]})
    occupied = (layers["03_rochers"][..., 3] > 0) | (layers["05_arbres_troncs"][..., 3] > 0)
    for name, fx, fy in sorted(flower_positions(), key=lambda t: t[2]):
        spr = load_sprite(name)
        h, w = spr.shape[:2]
        x, y = fx - w // 2, fy - h // 2
        if not (0 <= fy < H and 0 <= fx < W) or not on_lawn(fx, fy, 5):
            continue
        if cls_t[fy, fx] != 1 or occupied[max(0, y - 2):y + h + 2, max(0, x - 2):x + w + 2].any():
            continue
        ox, oy = SPR[name]["origine_ref"]
        paste(layers["02_fleurs"], spr, x, y, srcs["02_fleurs"], ox, oy)
        placements.append({"sprite": name, "x": x, "y": y})

    # 3) feuillage immersif
    fol, fsrc, fmask = foliage_layer(ref, fe, valid, cls_t)
    layers["08_feuillage_avant"] = fol
    srcs["08_feuillage_avant"] = fsrc

    all_layers = {"01_sol": ground, **layers}
    all_src = {"01_sol": sol["src"], **srcs}
    return all_layers, all_src, placements, warnings, refrgba


def composite(layers: dict, keys=None) -> np.ndarray:
    keys = keys or sorted(layers)
    out = Image.new("RGBA", (L.W, L.H), (0, 0, 0, 0))
    for k in keys:
        out.alpha_composite(Image.fromarray(layers[k]))
    return np.array(out)


if __name__ == "__main__":
    layers, srcs, placements, warnings, _ = compose()
    WORK.mkdir(exist_ok=True)
    comp = composite(layers)
    Image.fromarray(comp).save(WORK / "composition.png")
    Image.fromarray(np.array(night(Image.fromarray(comp)))).save(WORK / "composition_nuit.png")
    print("\n".join(warnings) or "placements OK")
