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
    """Dessine la tête de Terapagos en gros plan, style portrait PMD."""
    cx, cy = 20.0, 24.0
    rx, ry = 13.0, 11.5

    # --- tête ivoire -----------------------------------------------------
    t.disque(cx, cy, rx, ry, "corp_mid")
    for y in range(T):
        for x in range(T):
            if t.get(x, y) != "corp_mid":
                continue
            u, v = (x - cx) / rx, (y - cy) / ry
            l = -0.55 * u - 0.8 * v
            if l > 0.62:
                t.set(x, y, "corp_hau")
            elif l < -0.5:
                t.set(x, y, "corp_omb")
            elif l < -0.05:
                t.set(x, y, "corp_bas")

    # --- dôme de cristal, débordant du cadre en haut ----------------------
    dcx, dcy, drx, dry = 20.0, 7.0, 15.5, 10.5
    t.disque(dcx, dcy, drx, dry, "cri_mid")
    for y in range(T):
        for x in range(T):
            if t.get(x, y) != "cri_mid":
                continue
            u, v = (x - dcx) / drx, (y - dcy) / dry
            lum = -0.7 * u - 0.85 * v
            bande = math.floor((u * 2.4 + v * 1.3) * 1.1)
            lum += 0.14 * ((bande % 3) - 1)
            if lum > 0.9:
                c = "cri_ecl"
            elif lum > 0.38:
                c = "cri_hau"
            elif lum > -0.05:
                c = "cri_mid"
            elif lum > -0.55:
                c = "cri_bas"
            else:
                c = "cri_omb"
            t.set(x, y, c)
    # arêtes internes
    for a in (-125, -30):
        r = math.radians(a)
        t.ligne(dcx + math.cos(r) * drx * 0.2, dcy + math.sin(r) * dry * 0.2,
                dcx + math.cos(r) * drx * 0.8, dcy + math.sin(r) * dry * 0.8,
                "cont_cri")
    t.set(int(dcx - 6), int(dcy - 2), "cri_ecl")
    t.set(int(dcx - 5), int(dcy - 2), "cri_ecl")
    t.set(int(dcx - 5), int(dcy - 3), "cri_ecl")
    # pointes de cristal
    for u, h in ((-0.82, 3), (-0.45, 4), (0.0, 5), (0.45, 4), (0.82, 3)):
        px = dcx + u * drx * 0.9
        py = dcy - dry * 0.62 + abs(u) * 4
        h = h + 2
        for i in range(h):
            w = max(0, int(round(2 * (1 - i / h))))
            for dx in range(-w, w + 1):
                t.set(px + dx, py - i, "cri_hau" if dx <= 0 else "cri_bas")
    # liseré doré continu à la base du dôme (bandeau, pas de pointillé)
    for x in range(T):
        u = (x - dcx) / drx
        if abs(u) > 0.86:
            continue
        yb = dcy + dry * math.sqrt(max(0.0, 1 - u * u))
        t.set(x, yb, "or_mid")
        t.set(x, yb - 1, "or_hau" if x < dcx else "or_mid")
        t.set(x, yb + 1, "or_omb")

    # --- yeux --------------------------------------------------------------
    ferme = emo in ("Sigh",)
    plisse = emo in ("Happy", "Joyous", "Pain")
    grand = emo in ("Surprised", "Stunned", "Special1")
    larme = emo in ("Crying", "Teary-Eyed")
    oy = 25.5
    for s in (-1, 1):
        ox = cx + s * 6.2
        if ferme:
            t.ligne(ox - 3, oy, ox + 3, oy, "contour")
            continue
        if plisse:
            t.ligne(ox - 3, oy + 1, ox, oy - 1, "contour")
            t.ligne(ox, oy - 1, ox + 3, oy + 1, "contour")
            continue
        hh = 5.0 if grand else 4.0
        t.disque(ox, oy, 3.4, hh, "oeil_bl")
        px_ = ox + (0.8 * s if emo in ("Angry", "Determined", "Shouting") else 0)
        py_ = oy + (1.0 if emo in ("Sad", "Worried", "Crying") else 0)
        t.disque(px_, py_, 2.5, hh * 0.86, "oeil_ir")
        t.disque(px_, py_ + 0.6, 1.5, hh * 0.5, "oeil_pu")
        t.set(int(px_ - 2), int(py_ - 2), "oeil_bl")
        t.set(int(px_ - 1), int(py_ - 2), "oeil_bl")
        if emo == "Dizzy":
            t.disque(px_, py_, 1.4, 1.4, "oeil_bl")
        if larme:
            t.set(int(ox + 3 * s), int(oy + 3), "cri_hau")
            t.set(int(ox + 3 * s), int(oy + 4), "cri_mid")
            if emo == "Crying":
                t.set(int(ox + 3 * s), int(oy + 5), "cri_mid")
        # sourcils
        if emo in ("Angry", "Shouting", "Determined"):
            t.ligne(ox - 4 * s, oy - 6, ox + 3 * s, oy - 4, "contour")
        elif emo in ("Sad", "Worried", "Pain", "Crying", "Teary-Eyed"):
            t.ligne(ox - 4 * s, oy - 4, ox + 3 * s, oy - 6, "contour")

    # --- bouche -------------------------------------------------------------
    bx, by = cx, 32.5
    if emo in ("Happy", "Joyous", "Inspired"):
        t.ligne(bx - 3, by - 1, bx - 1, by + 1, "bouche")
        t.ligne(bx - 1, by + 1, bx + 1, by + 1, "bouche")
        t.ligne(bx + 1, by + 1, bx + 3, by - 1, "bouche")
        if emo == "Joyous":
            t.disque(bx, by, 2.6, 1.8, "bouche")
    elif emo in ("Shouting", "Surprised", "Stunned", "Special1"):
        t.disque(bx, by, 2.4, 2.2, "bouche")
        t.set(int(bx), int(by + 1), "oeil_pu")
    elif emo in ("Sad", "Worried", "Crying", "Teary-Eyed", "Pain"):
        t.ligne(bx - 2, by + 1, bx, by - 1, "bouche")
        t.ligne(bx, by - 1, bx + 2, by + 1, "bouche")
    elif emo == "Angry":
        t.ligne(bx - 3, by, bx + 3, by, "bouche")
        t.set(int(bx - 1), int(by - 1), "bouche")
        t.set(int(bx + 1), int(by - 1), "bouche")
    elif emo == "Sigh":
        t.ligne(bx - 2, by, bx + 2, by, "bouche")
    else:
        t.ligne(bx - 2, by, bx + 2, by, "bouche")

    # joues rosées légères des émotions chaudes (2 px, sans dégradé)
    if emo in ("Happy", "Joyous", "Special0"):
        for s in (-1, 1):
            t.set(int(cx + s * 10), 30, "or_mid")
            t.set(int(cx + s * 10), 31, "or_omb")


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
