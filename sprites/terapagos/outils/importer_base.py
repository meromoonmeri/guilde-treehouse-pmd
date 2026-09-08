# -*- coding: utf-8 -*-
"""Importe les poses générées depuis l'artwork officiel et les convertit en
sprites PMD propres : recadrage, réduction sur grille 48x48, quantification
sur palette limitée, suppression de l'anti-aliasing, contour dur 1 px.

Sortie : bases/<DIR>.png — une pose nette par direction, ancrée au sol.
"""
import os
import sys
from PIL import Image

sys.path.insert(0, os.path.dirname(__file__))

R = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
SRC = os.path.join(R, "references", "pmd_depuis_officiel.png")
L = H = 48
ANCRE_X, ANCRE_Y = 24, 40
CONTOUR = (24, 30, 52, 255)
NB_COULEURS = 15  # PMD : 15 couleurs + transparence


def cellules(im, n=4):
    """Découpe la planche source en n poses, par colonnes non vides."""
    g = im.convert("RGBA")
    px = g.load()
    w, h = g.size
    # colonne vide = quasi blanche sur toute la hauteur
    plein = []
    for x in range(w):
        occupe = False
        for y in range(h):
            r, v, b, a = px[x, y]
            if a > 30 and not (r > 235 and v > 235 and b > 235):
                occupe = True
                break
        plein.append(occupe)
    seg = []
    x = 0
    while x < w:
        if plein[x]:
            x0 = x
            while x < w and plein[x]:
                x += 1
            if x - x0 > w // 40:
                seg.append((x0, x))
        else:
            x += 1
    # fusionne les segments trop proches (mèches détachées)
    fus = []
    for s in seg:
        if fus and s[0] - fus[-1][1] < w // 60:
            fus[-1] = (fus[-1][0], s[1])
        else:
            fus.append(list(s))
            fus[-1] = tuple(fus[-1])
            fus[-1] = (s[0], s[1])
    return fus[:n] if len(fus) >= n else seg[:n]


def detourer(im):
    """Rend le fond blanc transparent, sans toucher aux pixels clairs internes."""
    im = im.convert("RGBA")
    px = im.load()
    w, h = im.size
    # remplissage depuis les bords (4-connexe) sur les pixels quasi blancs
    pile = []
    for x in range(w):
        pile += [(x, 0), (x, h - 1)]
    for y in range(h):
        pile += [(0, y), (w - 1, y)]
    vus = set()
    while pile:
        x, y = pile.pop()
        if (x, y) in vus or not (0 <= x < w and 0 <= y < h):
            continue
        r, v, b, a = px[x, y]
        if a < 30 or (r > 225 and v > 225 and b > 225):
            vus.add((x, y))
            px[x, y] = (0, 0, 0, 0)
            pile += [(x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)]
    return im


def reduire(im):
    """Réduit la pose détourée dans un cadre 48x48, pieds sur l'ancre."""
    bb = im.getbbox()
    if bb is None:
        return Image.new("RGBA", (L, H), (0, 0, 0, 0))
    c = im.crop(bb)
    # cible : le sprite occupe ~38 px de large et ~30 px de haut au maximum
    maxw, maxh = 46, 36
    r = min(maxw / c.size[0], maxh / c.size[1])
    nw = max(1, int(round(c.size[0] * r)))
    nh = max(1, int(round(c.size[1] * r)))
    # réduction en deux temps : moyenne puis seuil dur (pas d'anti-aliasing)
    c = c.resize((nw * 2, nh * 2), Image.LANCZOS).resize((nw, nh), Image.BOX)
    out = Image.new("RGBA", (L, H), (0, 0, 0, 0))
    out.paste(c, (ANCRE_X - nw // 2, ANCRE_Y - nh), c)
    return out


def durcir_alpha(im, seuil=128):
    px = im.load()
    for y in range(im.size[1]):
        for x in range(im.size[0]):
            r, v, b, a = px[x, y]
            px[x, y] = (r, v, b, 255 if a >= seuil else 0)
    return im


# Palette PMD imposée (15 couleurs + transparence), tirée de l'artwork.
PALETTE = [
    (24, 30, 52),     # contour
    (38, 44, 88),     # vitrail sombre
    (58, 64, 118),    # vitrail moyen
    (96, 78, 142),    # cellule violette
    (168, 96, 132),   # cellule rose
    (72, 132, 112),   # cellule verte
    (64, 126, 166),   # cellule cyan
    (150, 196, 168),  # fourrure ombre
    (186, 220, 186),  # fourrure moyenne
    (226, 240, 202),  # fourrure claire
    (246, 248, 214),  # fourrure crème
    (244, 214, 78),   # éclair jaune
    (206, 62, 74),    # anneau de l'oeil
    (96, 220, 214),   # iris cyan
    (250, 252, 246),  # éclat blanc
]


def quantifier(im, n=NB_COULEURS):
    """Force la palette PMD fixe, plus proche voisin, sans dithering."""
    out = Image.new("RGBA", im.size, (0, 0, 0, 0))
    src = im.load()
    dst = out.load()
    cache = {}
    for y in range(im.size[1]):
        for x in range(im.size[0]):
            r, v, b, a = src[x, y]
            if a == 0:
                continue
            k = (r >> 2, v >> 2, b >> 2)
            c = cache.get(k)
            if c is None:
                c = min(PALETTE, key=lambda p: (p[0] - r) ** 2 +
                        (p[1] - v) ** 2 + (p[2] - b) ** 2)
                cache[k] = c
            dst[x, y] = c + (255,)
    return out


def contourner(im, couleur=CONTOUR):
    px = im.load()
    w, h = im.size
    aj = []
    for y in range(h):
        for x in range(w):
            if px[x, y][3] != 0:
                continue
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                nx, ny = x + dx, y + dy
                if 0 <= nx < w and 0 <= ny < h and px[nx, ny][3] != 0:
                    aj.append((x, y))
                    break
    for x, y in aj:
        px[x, y] = couleur
    return im


def tete_lisible(im, d):
    """Redessine la petite tête bleu nuit + oeil rouge/cyan, pour que le
    visage reste lisible à 48 px après réduction (convention PMD)."""
    if d in ("N", "NE", "NO"):
        return im  # de dos : pas de visage
    px = im.load()
    # position de la tête selon la direction, calée sur le bas du sprite
    pos = {"S": (24, 33), "SE": (30, 32), "E": (34, 31),
           "SO": (18, 32), "O": (14, 31)}
    cx, cy = pos.get(d, (24, 33))
    rx, ry = (5.0, 4.0) if d in ("S", "SO", "SE") else (4.4, 3.8)
    fonce, moyen = (24, 30, 52, 255), (44, 54, 96, 255)
    for y in range(int(cy - ry) - 1, int(cy + ry) + 2):
        for x in range(int(cx - rx) - 1, int(cx + rx) + 2):
            if not (0 <= x < im.size[0] and 0 <= y < im.size[1]):
                continue
            u, v = (x - cx) / rx, (y - cy) / ry
            if u * u + v * v <= 1.0:
                px[x, y] = moyen if (-0.5 * u - 0.8 * v) > 0.1 else fonce
    # yeux : anneau rouge + iris cyan + éclat
    rouge, cyan, blanc = (206, 62, 74, 255), (96, 220, 214, 255), (250, 252, 246, 255)
    if d in ("S",):
        yeux = [(cx - 2, cy - 1), (cx + 2, cy - 1)]
    elif d in ("SE", "E"):
        yeux = [(cx + 2, cy - 1)]
    else:
        yeux = [(cx - 2, cy - 1)]
    for (ox, oy) in yeux:
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                x, y = ox + dx, oy + dy
                if 0 <= x < im.size[0] and 0 <= y < im.size[1]:
                    px[x, y] = rouge
        if 0 <= ox < im.size[0] and 0 <= oy < im.size[1]:
            px[ox, oy] = cyan
            if oy + 1 < im.size[1]:
                px[ox, oy + 1] = cyan
        if 0 <= ox - 1 < im.size[0] and 0 <= oy - 1 < im.size[1]:
            px[ox - 1, oy - 1] = blanc
    return im


def importer():
    src = Image.open(SRC)
    segs = cellules(src, 4)
    noms = ["S", "SE", "E", "N"]
    dst = os.path.join(R, "bases")
    os.makedirs(dst, exist_ok=True)
    faits = {}
    for (x0, x1), nom in zip(segs, noms):
        pose = src.crop((x0, 0, x1, src.size[1]))
        pose = detourer(pose)
        pose = reduire(pose)
        pose = durcir_alpha(pose)
        pose = quantifier(pose)
        pose = tete_lisible(pose, nom)
        pose = contourner(pose)
        pose.save(os.path.join(dst, "%s.png" % nom))
        faits[nom] = pose
    # directions manquantes par miroir horizontal (convention PMD)
    for src_n, dst_n in (("SE", "SO"), ("E", "O"), ("SE", "NE"), ("SO", "NO")):
        if dst_n in faits:
            continue
        base = faits.get(src_n)
        if base is None:
            continue
        m = base.transpose(Image.FLIP_LEFT_RIGHT)
        m.save(os.path.join(dst, "%s.png" % dst_n))
        faits[dst_n] = m
    # NE / NO : dérivés du dos (N) miroité et légèrement décalé
    return faits


if __name__ == "__main__":
    f = importer()
    print("bases importées :", ", ".join(sorted(f)))
