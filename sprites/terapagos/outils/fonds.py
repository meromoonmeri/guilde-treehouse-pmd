# -*- coding: utf-8 -*-
"""Fonds canoniques des portraits PMD, reconstruits en pixel art.

Grammaire observée sur les planches de fonds SpriteCollab :
  - dégradés verticaux à deux teintes, obtenus par TRAMAGE (dither ordonné
    de Bayer) et non par interpolation : aucune couleur intermédiaire ;
  - bandes diagonales régulières, à 45°, en deux valeurs ;
  - éclat radial (rayons partant du centre) pour la surprise ;
  - dents de scie en haut du cadre pour la colère ;
  - croix / éclats épars pour l'étourdissement.

Chaque fond est construit sur la même palette réduite que le portrait et ne
contient jamais de flou, de vignette ni de transparence variable.
"""
from PIL import Image

T = 40

# Matrice de Bayer 4x4 : tramage ordonné, strictement déterministe.
BAYER = [
    [0, 8, 2, 10],
    [12, 4, 14, 6],
    [3, 11, 1, 9],
    [15, 7, 13, 5],
]


def _mix(a, b, t, x, y):
    """Choisit a ou b selon le tramage : jamais de couleur intermédiaire."""
    seuil = (BAYER[y % 4][x % 4] + 0.5) / 16.0
    return b if t > seuil else a


def degrade(haut, bas):
    """Dégradé vertical tramé, deux teintes seulement."""
    im = Image.new("RGBA", (T, T))
    p = im.load()
    for y in range(T):
        t = y / float(T - 1)
        for x in range(T):
            p[x, y] = _mix(haut, bas, t, x, y) + (255,)
    return im


def diagonales(clair, sombre, pas=6):
    """Bandes diagonales à 45°, deux valeurs franches."""
    im = Image.new("RGBA", (T, T))
    p = im.load()
    for y in range(T):
        for x in range(T):
            p[x, y] = (clair if ((x + y) // pas) % 2 == 0 else sombre) + (255,)
    return im


def diagonales_degrade(clair, sombre, fondc, fonds_, pas=7):
    """Bandes diagonales posées sur un dégradé tramé (cas fréquent PMD)."""
    base = degrade(fondc, fonds_)
    p = base.load()
    for y in range(T):
        for x in range(T):
            if ((x + y) // pas) % 2 == 0:
                t = y / float(T - 1)
                p[x, y] = _mix(clair, sombre, t, x, y) + (255,)
    return base


def radial(centre, bord, rayons=16):
    """Éclat radial : rayons alternés partant du centre du cadre."""
    import math
    im = Image.new("RGBA", (T, T))
    p = im.load()
    cx = cy = (T - 1) / 2.0
    for y in range(T):
        for x in range(T):
            a = math.atan2(y - cy, x - cx)
            sect = int((a + math.pi) / (2 * math.pi) * rayons)
            p[x, y] = (centre if sect % 2 == 0 else bord) + (255,)
    return im


def zigzag(haut, bas, dent=4):
    """Dents de scie en haut du cadre (colère), sur fond de dégradé."""
    im = degrade(haut, bas)
    p = im.load()
    blanc = (250, 250, 246)
    for x in range(T):
        # profil triangulaire régulier
        k = x % (dent * 2)
        h = k if k <= dent else (dent * 2 - k)
        for y in range(0, 3 + h):
            p[x, y] = blanc + (255,)
    return im


def etoiles(haut, bas, points):
    """Petites croix éparses (étourdissement), sur dégradé."""
    im = degrade(haut, bas)
    p = im.load()
    blanc = (250, 250, 246)
    for (cx, cy) in points:
        for dx, dy in ((0, 0), (1, 0), (-1, 0), (0, 1), (0, -1)):
            x, y = cx + dx, cy + dy
            if 0 <= x < T and 0 <= y < T:
                p[x, y] = blanc + (255,)
    return im


# --------------------------------------------------------------------------
# Un fond par émotion, suivant la logique de couleur PMD :
# froid au repos, chaud pour le positif, rouge pour la colère, sourd pour le
# négatif. Les noms sont les slots officiels SpriteCollab.
FONDS = {
    "Normal":     lambda: degrade((150, 214, 236), (86, 150, 202)),
    "Happy":      lambda: degrade((252, 240, 168), (244, 198, 92)),
    "Joyous":     lambda: diagonales_degrade((255, 246, 196), (250, 216, 120),
                                             (252, 236, 150), (240, 190, 84)),
    "Sad":        lambda: degrade((156, 176, 210), (92, 112, 158)),
    "Angry":      lambda: zigzag((240, 128, 140), (198, 60, 78)),
    "Shouting":   lambda: zigzag((248, 152, 120), (208, 74, 56)),
    "Surprised":  lambda: radial((226, 248, 252), (128, 214, 238)),
    "Stunned":    lambda: etoiles((236, 226, 168), (196, 176, 96),
                                  [(7, 8), (31, 11), (12, 30), (33, 28)]),
    "Special0":   lambda: degrade((186, 214, 226), (108, 148, 172)),
    "Worried":    lambda: degrade((178, 184, 214), (110, 122, 166)),
    "Dizzy":      lambda: radial((214, 200, 238), (146, 126, 190)),
    "Special1":   lambda: degrade((206, 216, 236), (140, 156, 192)),
    "Determined": lambda: diagonales_degrade((188, 226, 244), (120, 184, 220),
                                             (164, 210, 236), (98, 158, 202)),
    "Inspired":   lambda: radial((252, 246, 206), (238, 206, 120)),
    "Sigh":       lambda: degrade((208, 210, 208), (146, 150, 156)),
    "Special2":   lambda: degrade((178, 200, 232), (114, 140, 186)),
    "Special3":   lambda: diagonales_degrade((252, 208, 220), (240, 164, 190),
                                             (250, 196, 212), (232, 150, 178)),
    "Crying":     lambda: degrade((166, 200, 226), (98, 138, 180)),
    "Pain":       lambda: degrade((206, 168, 190), (144, 100, 138)),
    "Teary-Eyed": lambda: degrade((186, 206, 230), (122, 150, 190)),
}


def fond(nom):
    return FONDS.get(nom, FONDS["Normal"])()
