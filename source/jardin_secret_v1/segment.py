"""Jardin secret v1 — segmentation de la référence canonique `secretgarden.png`.

Produit, à partir des SEULS pixels de la référence :
  * un masque par objet (rayon, souche, arbres, rochers, fleurs) ;
  * une carte de classes du sol (V = sous-bois sombre, L = pelouse, C = tapis)
    et un ton du tapis (clair / ombré) ;
  * les sprites objets (RGBA, pixels exacts, alpha binaire) avec leur origine.

Aucune couleur n'est créée : tous les RGB viennent de la référence.
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
from PIL import Image
from scipy import ndimage as ndi

ROOT = Path(__file__).resolve().parents[2]
REF = ROOT / "secretgarden.png"
OUT = Path(__file__).resolve().parent / "segmentation"

# Boîtes englobantes (coordonnées référence 408×408, x0, y0, x1, y1 exclus).
BOXES = {
    "rayon": (132, 0, 275, 110),
    "rocher_double": (118, 72, 180, 124),
    "arbre_ouest": (44, 116, 142, 214),
    "arbre_est": (266, 68, 364, 164),
    "souche": (148, 100, 252, 184),
    "rocher_s1": (100, 211, 126, 236),
    "rocher_haut": (271, 211, 326, 266),
    "rocher_s2": (251, 256, 279, 279),
    "rocher_paire": (106, 311, 169, 359),
    "rocher_s3": (261, 331, 294, 359),
    "rocher_s4": (271, 354, 299, 382),
}
MEADOW = (110, 90, 326, 202)  # prairie fleurie autour de la souche
# Ombres portées des arbres sur la pelouse (boîtes de recherche, pixels sombres reliés à l'arbre)
SHADOW_BOXES = {"arbre_ouest": (40, 170, 125, 214), "arbre_est": (272, 118, 350, 166)}


def load_ref() -> np.ndarray:
    return np.array(Image.open(REF).convert("RGBA"))


def key(a: np.ndarray) -> np.ndarray:
    a = a.astype(np.int64)
    return (a[..., 0] << 16) | (a[..., 1] << 8) | a[..., 2]


def ground_palette(rgb: np.ndarray) -> set[int]:
    """Couleurs du sol : vues hors de toutes les boîtes ET vertes (g - r >= 24)."""
    h, w, _ = rgb.shape
    m = np.zeros((h, w), bool)
    for x0, y0, x1, y1 in list(BOXES.values()) + [MEADOW]:
        m[y0:y1, x0:x1] = True
    k = key(rgb)
    pal = set()
    for c in np.unique(k[~m]).tolist():
        r, g = c >> 16, (c >> 8) & 255
        if g - r >= 24:
            pal.add(c)
    return pal


def segment():
    OUT.mkdir(parents=True, exist_ok=True)
    ref = load_ref()
    rgb = ref[..., :3]
    h, w, _ = rgb.shape
    k = key(rgb)
    pal = ground_palette(rgb)
    is_ground = np.isin(k, list(pal))
    g_int = rgb[..., 1].astype(int)
    r_int = rgb[..., 0].astype(int)
    b_int = rgb[..., 2].astype(int)

    masks: dict[str, np.ndarray] = {}

    def box_mask(b):
        m = np.zeros((h, w), bool)
        x0, y0, x1, y1 = b
        m[y0:y1, x0:x1] = True
        return m

    beam_box = box_mask(BOXES["rayon"])
    # halo du rayon : verts à b >= 55 non-sol dans la colonne (le feuillage des arbres est à b = 31)
    beam_glow = beam_box & ~is_ground & (b_int >= 55) & (g_int - r_int >= 40)
    # 1) Fleurs : pétales clairs (r >= 180) hors colonne du rayon, dans la prairie
    meadow = box_mask(MEADOW)
    petals = meadow & ~beam_box & ~is_ground & (r_int >= 180)
    flower_px = ndi.binary_dilation(petals, np.ones((3, 3))) & ~is_ground & meadow & ~beam_box
    lab, n = ndi.label(ndi.binary_dilation(flower_px, np.ones((2, 2))))
    fi = 0
    flower_all = np.zeros((h, w), bool)
    for i in range(1, n + 1):
        comp = (lab == i) & flower_px
        if comp.sum() < 6 or comp.sum() > 80:
            continue
        masks[f"fleur_{fi:02d}"] = comp
        flower_all |= comp
        fi += 1
    taken = flower_all | beam_glow

    order = ["rocher_double", "rocher_s1", "rocher_haut", "rocher_s2", "rocher_paire", "rocher_s3",
             "rocher_s4", "souche", "arbre_ouest", "arbre_est"]
    for name in order:
        box = box_mask(BOXES[name])
        x0, y0, x1, y1 = BOXES[name]
        core = box & ~is_ground & ~taken
        core = ndi.binary_fill_holes(ndi.binary_closing(core, np.ones((3, 3))) & box) & ~taken
        lab, n = ndi.label(ndi.binary_dilation(core, np.ones((3, 3))) & box)
        if n > 1:
            sizes = ndi.sum(core, lab, range(1, n + 1))
            core = core & (lab == 1 + int(np.argmax(sizes)))
        ys, xs = np.nonzero(core)
        cy = int(np.percentile(ys, 60))
        below = np.zeros((h, w), bool)
        below[cy:y1, x0:x1] = True
        if name.startswith("rocher"):
            near = ndi.binary_dilation(core, np.ones((5, 5))) & box & below
            core |= near & is_ground & (g_int <= 150) & (g_int >= 60)
        else:
            near = ndi.binary_dilation(core, np.ones((9, 9))) & box & below
            core |= near & is_ground & (g_int <= 79)
        if name in SHADOW_BOXES:
            sb = box_mask(SHADOW_BOXES[name])
            dark = sb & is_ground & (g_int >= 96) & (g_int <= 167) & (b_int >= 55) & ~taken
            lab2, n2 = ndi.label(dark | core)
            ids = np.unique(lab2[core])
            core |= np.isin(lab2, ids[ids > 0]) & dark
        core = ndi.binary_fill_holes(core) & ~taken
        masks[name] = core
        taken |= core

    # 2) Rayon en dernier : tout ce qui n'est pas sol (ou sol éclairé) dans sa colonne
    core = beam_box & (~is_ground | (g_int >= 215)) & ~(taken & ~beam_glow)
    others = taken & ~beam_glow
    core = ndi.binary_fill_holes(ndi.binary_closing(core, np.ones((3, 3))) & beam_box) & ~others
    masks["rayon"] = core
    taken |= core

    obj_any = np.zeros((h, w), bool)
    for m in masks.values():
        obj_any |= m

    # Classes du sol (0 = V sous-bois, 1 = L pelouse, 2 = C tapis)
    cls = np.full((h, w), -1, int)
    cls[(g_int <= 119)] = 0
    lawn = (g_int >= 127) & (b_int >= 63)
    carpet = (g_int >= 143) & (b_int <= 55) | ((g_int >= 119) & (g_int < 143) & (b_int <= 47))
    cls[lawn & (cls < 0)] = 1
    cls[carpet & (cls < 0)] = 2
    cls[(cls < 0)] = 1
    # lissage par vote majoritaire pour absorber les festons dans leur région
    onehot = np.stack([(cls == c).astype(float) for c in range(3)])
    sm = np.stack([ndi.uniform_filter(o, 9) for o in onehot])
    cls_s = sm.argmax(0)
    # sol caché sous les objets : classe du pixel de sol visible le plus proche
    _, (iy, ix) = ndi.distance_transform_edt(obj_any, return_indices=True)
    cls_s = cls_s[iy, ix]
    # le rayon et les objets ne doivent pas influencer : on garde la classe lissée
    # Ton du tapis en 4 bandes (mesuré sur l'axe du couloir) : clair / 143,191,47 / 135,175,47 / 127,167,39
    bands = np.array([[159, 207, 55], [143, 191, 47], [135, 175, 47], [127, 167, 39]])
    extra = {(151, 199, 55): 0, (143, 183, 47): 1, (119, 159, 47): 3}
    lvl = np.full((h, w), -1.0)
    for i, c in enumerate(bands):
        lvl[(rgb == c).all(-1)] = i
    for c, i in extra.items():
        lvl[(rgb == np.array(c)).all(-1)] = i
    known = (lvl >= 0) & (cls_s == 2) & ~obj_any
    num = ndi.uniform_filter(np.where(known, lvl, 0), 9)
    den = ndi.uniform_filter(known.astype(float), 9)
    lvl_s = np.where(den > 0.05, num / np.maximum(den, 1e-6), 0)
    lvl_s = np.round(lvl_s)
    tone = ndi.uniform_filter(lvl_s / 3.0, 7) * (cls_s == 2)

    np.savez_compressed(
        OUT / "segmentation.npz",
        cls=cls_s.astype(np.int8),
        tone=tone.astype(np.float32),
        objects=obj_any,
        **{f"m_{k}": v for k, v in masks.items()},
    )

    # Sprites objets
    sprites = {}
    for name, m in masks.items():
        ys, xs = np.nonzero(m)
        if not len(ys):
            continue
        x0, x1, y0, y1 = xs.min(), xs.max() + 1, ys.min(), ys.max() + 1
        spr = np.zeros((y1 - y0, x1 - x0, 4), np.uint8)
        sub = m[y0:y1, x0:x1]
        spr[sub] = ref[y0:y1, x0:x1][sub]
        Image.fromarray(spr).save(OUT / f"{name}.png")
        sprites[name] = {"origine_ref": [int(x0), int(y0)], "taille": [int(x1 - x0), int(y1 - y0)],
                         "pixels": int(sub.sum())}
    (OUT / "sprites.json").write_text(json.dumps(sprites, indent=1, ensure_ascii=False))

    # Visualisations de contrôle
    viz = ref[..., :3].copy()
    viz[obj_any] = [255, 0, 255]
    Image.fromarray(viz).resize((w * 2, h * 2), Image.NEAREST).save(OUT / "_ctrl_objets.png")
    pal_c = np.array([[30, 30, 90], [120, 220, 120], [230, 220, 60]], np.uint8)
    cv = pal_c[cls_s]
    cv = (cv * (1 - 0.5 * tone[..., None])).astype(np.uint8)
    Image.fromarray(cv).resize((w * 2, h * 2), Image.NEAREST).save(OUT / "_ctrl_classes.png")
    return masks, cls_s, tone


if __name__ == "__main__":
    masks, cls, tone = segment()
    print(len(masks), "masques ;", sum(1 for k in masks if k.startswith("fleur")), "fleurs")
