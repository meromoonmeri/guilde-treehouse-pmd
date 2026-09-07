# -*- coding: utf-8 -*-
"""Portraits PMD de Terapagos — 40x40 px, convention SpriteCollab.

Cadrage PMD : tête cadrée large, visage occupant les 2/3 inférieurs, dôme
de cristal débordant en haut, léger décentrage vers le côté regardé.
Une image par émotion + feuille complète Portraits.png (grille 5 x 8).
Les fonds reprennent la grammaire des portraits PMD : aplat de couleur
unie découpé en deux valeurs par une diagonale, sans dégradé ni flou.
"""
import os
import sys
import math
from PIL import Image

sys.path.insert(0, os.path.dirname(__file__))
from moteur import Toile, PAL
from modele import CELL

T = 40  # taille canonique des portraits PMD

# Ordre officiel des émotions SpriteCollab (index de la feuille).
EMOTIONS = [
    "Normal", "Happy", "Pain", "Angry", "Worried",
    "Sad", "Crying", "Shouting", "Teary-Eyed", "Determined",
    "Joyous", "Inspired", "Surprised", "Dizzy", "Special0",
    "Special1", "Sigh", "Stunned", "Special2", "Special3",
]

# Teinte de fond par émotion : logique PMD (fond neutre froid, réchauffé
# pour les émotions positives, assombri pour les négatives).
FONDS = {
    "Normal": (86, 122, 168), "Happy": (208, 168, 96), "Pain": (120, 84, 108),
    "Angry": (162, 78, 72), "Worried": (104, 112, 150), "Sad": (86, 100, 140),
    "Crying": (78, 106, 148), "Shouting": (176, 96, 68),
    "Teary-Eyed": (110, 132, 170), "Determined": (96, 138, 176),
    "Joyous": (224, 186, 110), "Inspired": (144, 176, 200),
    "Surprised": (172, 168, 118), "Dizzy": (128, 110, 156),
    "Special0": (92, 152, 160), "Special1": (150, 132, 178),
    "Sigh": (108, 116, 132), "Stunned": (156, 140, 96),
    "Special2": (96, 146, 190), "Special3": (176, 158, 200),
}


def fond(im, rgb):
    """Fond PMD : deux valeurs séparées par une diagonale nette."""
    px = im.load()
    clair = tuple(min(255, int(c * 1.22)) for c in rgb)
    sombre = tuple(int(c * 0.74) for c in rgb)
    for y in range(T):
        for x in range(T):
            px[x, y] = (clair if (x + y) < T * 0.95 else sombre) + (255,)
    # liseré diagonal, un pixel, valeur intermédiaire (convention PMD)
    for y in range(T):
        x = int(T * 0.95 - y)
        if 0 <= x < T:
            px[x, y] = tuple(int(c * 0.94) for c in clair) + (255,)
    return im


def visage(t, emo):
    """Gros plan PMD : tête bleu nuit devant, carapace vitrail derrière,
    fourrure menthe débordante — d'après l'artwork officiel."""
    import math as _m

    # --- carapace en vitrail, en arrière-plan haut -------------------------
    dcx, dcy, drx, dry = 20.0, 9.0, 18.0, 10.5
    t.disque(dcx, dcy, drx, dry, "vit_bas")
    for y in range(T):
        for x in range(T):
            if t.get(x, y) != "vit_bas":
                continue
            u, v = (x - dcx) / drx, (y - dcy) / dry
            a = _m.atan2(v, u)
            r = _m.sqrt(u * u + v * v)
            sect = int((a + _m.pi) / (2 * _m.pi) * 8) % 8
            idx = (sect + (0 if r < 0.5 else 5)) % len(CELL)
            c = CELL[idx]
            lum = -0.55 * u - 0.8 * v
            if lum > 0.5 and c in ("vit_omb", "vit_bas"):
                c = "vit_mid"
            elif lum < -0.5 and c in ("vit_mid", "vit_cya", "vit_ver"):
                c = "vit_bas"
            t.set(x, y, c)
    # nervures menthe
    for y in range(T):
        for x in range(T):
            c = t.get(x, y)
            if c is None or not c.startswith("vit"):
                continue
            for dx, dy in ((1, 0), (0, 1)):
                n = t.get(x + dx, y + dy)
                if n is not None and n.startswith("vit") and n != c:
                    t.set(x, y, "nerv_hau" if y < dcy else "nerv_mid")
    for y in range(T):
        for x in range(T):
            c = t.get(x, y)
            if c is None or not c.startswith(("vit", "nerv")):
                continue
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                n = t.get(x + dx, y + dy)
                if n is None or not n.startswith(("vit", "nerv")):
                    t.set(x, y, "nerv_hau" if y < dcy else "nerv_mid")
                    break
    # éclair jaune
    for dx, dy, c in ((0, -2, "or_hau"), (-1, -1, "or_mid"), (0, -1, "or_hau"),
                      (-1, 0, "or_mid"), (0, 0, "or_mid"), (1, 0, "or_hau"),
                      (0, 1, "or_mid"), (1, 1, "or_omb"), (0, 2, "or_omb")):
        t.set(dcx - 4 + dx, dcy - 2 + dy, c)
    t.set(int(dcx - 8), int(dcy - 4), "vit_ecl")
    t.set(int(dcx - 7), int(dcy - 4), "vit_ecl")

    # --- fourrure vaporeuse autour de la carapace --------------------------
    for i in range(22):
        a = _m.pi * (i / 21.0) + _m.pi  # demi-couronne supérieure
        ca, sa = _m.cos(a), _m.sin(a)
        lon = 5.0 + 3.0 * abs(ca)
        x0, y0 = dcx + ca * drx, dcy + sa * dry
        x1, y1 = dcx + ca * (drx + lon), dcy + sa * (dry + lon * 0.8)
        pas = max(1, int(max(abs(x1 - x0), abs(y1 - y0))))
        for k in range(pas + 1):
            u = k / pas
            x, y = x0 + (x1 - x0) * u, y0 + (y1 - y0) * u
            c = "four_cre" if u > 0.65 else ("four_hau" if u > 0.3 else "four_mid")
            w = max(0, int(round(2.0 * (1 - u * 0.6))))
            for dx in range(-w, w + 1):
                for dy in range(-1, 1):
                    if t.get(x + dx, y + dy) is None:
                        t.set(x + dx, y + dy, c)
    for y in range(T):
        for x in range(T):
            u, v = (x - dcx) / (drx + 3.0), (y - dcy) / (dry + 3.0)
            dd = u * u + v * v
            if 0.72 <= dd <= 1.0 and t.get(x, y) is None:
                lum = -0.6 * u - 0.85 * v
                t.set(x, y, "four_hau" if lum > 0.4 else
                      ("four_mid" if lum > -0.1 else "four_bas"))

    # --- tête bleu nuit au premier plan ------------------------------------
    cx, cy = 20.0, 28.0
    rx, ry = 11.5, 9.0
    t.disque(cx, cy, rx, ry, "tet_mid")
    for y in range(T):
        for x in range(T):
            if t.get(x, y) != "tet_mid":
                continue
            u, v = (x - cx) / rx, (y - cy) / ry
            lum = -0.5 * u - 0.85 * v
            if lum > 0.55:
                t.set(x, y, "tet_hau")
            elif lum < -0.35:
                t.set(x, y, "tet_omb")

    # --- yeux : anneau rouge, iris cyan ------------------------------------
    ferme = emo in ("Sigh",)
    plisse = emo in ("Happy", "Joyous", "Pain")
    grand = emo in ("Surprised", "Stunned", "Special1")
    larme = emo in ("Crying", "Teary-Eyed")
    oy = 27.5
    for s in (-1, 1):
        ox = cx + s * 5.6
        if ferme:
            t.ligne(ox - 3, oy, ox + 3, oy, "oeil_rou")
            continue
        if plisse:
            t.ligne(ox - 3, oy + 1, ox, oy - 1, "oeil_rou")
            t.ligne(ox, oy - 1, ox + 3, oy + 1, "oeil_rou")
            continue
        hh = 4.6 if grand else 3.9
        t.disque(ox, oy, 3.5, hh, "oeil_rou")
        px_ = ox + (0.8 * s if emo in ("Angry", "Determined", "Shouting") else 0)
        py_ = oy + (1.0 if emo in ("Sad", "Worried", "Crying") else 0)
        t.disque(px_, py_, 2.3, hh * 0.72, "oeil_cya")
        t.disque(px_, py_ + 0.4, 1.5, hh * 0.52, "oeil_ver")
        t.disque(px_, py_ + 0.5, 1.1, hh * 0.36, "oeil_pu")
        t.set(int(px_ - 2), int(py_ - 2), "oeil_bl")
        t.set(int(px_ - 1), int(py_ - 2), "oeil_bl")
        if emo == "Dizzy":
            t.disque(px_, py_, 1.4, 1.4, "oeil_bl")
        if larme:
            t.set(int(ox + 4 * s), int(oy + 3), "four_hau")
            t.set(int(ox + 4 * s), int(oy + 4), "four_mid")
            if emo == "Crying":
                t.set(int(ox + 4 * s), int(oy + 5), "four_mid")
        if emo in ("Angry", "Shouting", "Determined"):
            t.ligne(ox - 4 * s, oy - 6, ox + 3 * s, oy - 5, "tet_omb")
        elif emo in ("Sad", "Worried", "Pain", "Crying", "Teary-Eyed"):
            t.ligne(ox - 4 * s, oy - 5, ox + 3 * s, oy - 6, "tet_omb")

    # --- bouche en zigzag ---------------------------------------------------
    bx, by = cx, 34.5
    if emo in ("Shouting", "Surprised", "Stunned", "Special1"):
        t.disque(bx, by, 2.6, 2.2, "nerv_hau")
        t.set(int(bx), int(by + 1), "tet_omb")
    elif emo in ("Sad", "Worried", "Crying", "Teary-Eyed", "Pain"):
        for dx, dy in ((-3, 1), (-2, 0), (-1, 0), (0, 0), (1, 0), (2, 0), (3, 1)):
            t.set(bx + dx, by + dy, "nerv_hau")
    elif emo in ("Happy", "Joyous", "Inspired"):
        for dx, dy in ((-4, 0), (-3, 1), (-2, 2), (-1, 2), (0, 2),
                       (1, 2), (2, 2), (3, 1), (4, 0)):
            t.set(bx + dx, by + dy, "nerv_hau")
    elif emo == "Sigh":
        t.ligne(bx - 3, by, bx + 3, by, "nerv_hau")
    else:  # zigzag caractéristique
        for dx, dy in ((-4, 0), (-3, 1), (-2, 0), (-1, 1), (0, 0),
                       (1, 1), (2, 0), (3, 1), (4, 0)):
            t.set(bx + dx, by + dy, "nerv_hau")


def portrait(emo):
    t = Toile(T, T)
    visage(t, emo)
    t.contourner("contour")
    im = Image.new("RGBA", (T, T))
    fond(im, FONDS.get(emo, FONDS["Normal"]))
    im.alpha_composite(t.image())
    return im


def generer(base):
    os.makedirs(base, exist_ok=True)
    feuille = Image.new("RGBA", (T * 5, T * 8), (0, 0, 0, 0))
    for i, e in enumerate(EMOTIONS):
        im = portrait(e)
        im.save(os.path.join(base, "%s.png" % e))
        feuille.paste(im, ((i % 5) * T, (i // 5) * T))
        # variante « ^ » (miroir), convention SpriteCollab pour le côté droit
        mi = im.transpose(Image.FLIP_LEFT_RIGHT)
        mi.save(os.path.join(base, "%s^.png" % e))
        feuille.paste(mi, ((i % 5) * T, (i // 5 + 4) * T))
    feuille.save(os.path.join(base, "Portraits.png"))
    return len(EMOTIONS)


if __name__ == "__main__":
    R = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    for code in ("0000", "0001", "0002"):
        n = generer(os.path.join(R, "portrait", code))
        print(code, n, "émotions")
