"""
pixelisation.py — conversion d'une image peinte en pixel art exploitable.

Une image générée n'est pas du pixel art : elle est lissée, dégradée et
comporte des milliers de couleurs. La rendre utilisable demande trois étapes
distinctes, dans cet ordre.
"""

import numpy as np
from PIL import Image, ImageEnhance, ImageFilter


def cadrer(im, larg, haut):
    """Recadre au bon rapport puis réduit, sans déformer."""
    r_cible = larg / haut
    w, h = im.size
    if w / h > r_cible:
        nw = int(h * r_cible)
        im = im.crop(((w - nw) // 2, 0, (w - nw) // 2 + nw, h))
    else:
        nh = int(w / r_cible)
        im = im.crop((0, (h - nh) // 2, w, (h - nh) // 2 + nh))
    return im.resize((larg, haut), Image.LANCZOS)


def posteriser(im, niveaux=6):
    """Écrase les dégradés en paliers francs, avant toute quantification."""
    a = np.asarray(im.convert("RGB"), dtype=np.float32) / 255.0
    a = np.floor(a * niveaux + 0.5) / niveaux
    return Image.fromarray((np.clip(a, 0, 1) * 255).astype(np.uint8), "RGB")


def palette_fixe(im, couleurs):
    """Projette sur une palette imposée, sans tramage."""
    pal = Image.new("P", (1, 1))
    plat = []
    for c in couleurs:
        plat += list(c)
    plat += [0, 0, 0] * (256 - len(couleurs))
    pal.putpalette(plat)
    return im.convert("RGB").quantize(palette=pal, dither=Image.Dither.NONE)


def refroidir(im, force=0.22, assombrir=0.86):
    """
    Ramène la dominante vers l'indigo et baisse la luminosité. Une image
    générée tire facilement au magenta ; sans ce recalage elle jure avec la
    palette bleue de Terapagos et écrase les effets posés par-dessus.
    """
    a = np.asarray(im.convert("RGB"), dtype=np.float32)
    r, g, b = a[..., 0], a[..., 1], a[..., 2]
    a[..., 0] = r * (1 - force)
    a[..., 1] = g * (1 - force * 0.35)
    a[..., 2] = np.minimum(255.0, b * (1 + force * 0.30))
    return Image.fromarray(np.clip(a * assombrir, 0, 255).astype(np.uint8), "RGB")


def convertir(chemin, larg, haut, n_couleurs=28, niveaux=7,
              saturation=0.92, contraste=1.06):
    """
    Chaîne complète : cadrage, renforcement, postérisation, quantification
    adaptative sans tramage. Le tramage est volontairement désactivé — il
    produit un bruit qui ne se lit pas comme du pixel art à cette échelle.
    """
    im = Image.open(chemin).convert("RGB")
    im = cadrer(im, larg, haut)
    im = ImageEnhance.Color(im).enhance(saturation)
    im = ImageEnhance.Contrast(im).enhance(contraste)
    im = refroidir(im)
    im = im.filter(ImageFilter.MedianFilter(3))     # retire le moucheté
    im = posteriser(im, niveaux)
    q = im.quantize(colors=n_couleurs, method=Image.Quantize.MAXCOVERAGE,
                    dither=Image.Dither.NONE)
    return q.convert("RGBA"), extraire_palette(q)


def extraire_palette(q):
    p = q.getpalette()
    n = len({i for i in q.getdata()})
    return [tuple(p[i * 3:i * 3 + 3]) for i in range(n)]


def separer_fond_sol(im, haut_sol):
    """
    Sépare la planche en deux calques : la caverne du fond et l'aire de jeu.
    La coupure suit une ligne d'horizon donnée.
    """
    a = np.array(im)
    fond = a.copy()
    sol = a.copy()
    fond[haut_sol:, 3] = 0
    sol[:haut_sol, 3] = 0
    return (Image.fromarray(fond, "RGBA"), Image.fromarray(sol, "RGBA"))


def decouper_bandes(chemin, larg, haut_max, n_couleurs=20, seuil=42):
    """
    Découpe une planche de références alignées en objets isolés, par
    projection en colonnes : les colonnes sombres séparent les objets.
    """
    im = Image.open(chemin).convert("RGB")
    a = np.asarray(im, dtype=np.float32).sum(axis=2) / 3.0
    col = a.max(axis=0)
    plein = col > seuil
    bandes, debut = [], None
    for x, v in enumerate(plein):
        if v and debut is None:
            debut = x
        elif not v and debut is not None:
            if x - debut > im.size[0] * 0.03:
                bandes.append((debut, x))
            debut = None
    if debut is not None:
        bandes.append((debut, len(plein)))
    objets = []
    for x0, x1 in bandes:
        sub = im.crop((x0, 0, x1, im.size[1]))
        b = np.asarray(sub, dtype=np.float32).sum(axis=2) / 3.0
        lignes = np.nonzero(b.max(axis=1) > seuil)[0]
        if not len(lignes):
            continue
        sub = sub.crop((0, lignes[0], sub.size[0], lignes[-1] + 1))
        k = min(larg / sub.size[0], haut_max / sub.size[1])
        sub = sub.resize((max(1, int(sub.size[0] * k)),
                          max(1, int(sub.size[1] * k))), Image.LANCZOS)
        sub = posteriser(sub, 6).quantize(
            colors=n_couleurs, method=Image.Quantize.MAXCOVERAGE,
            dither=Image.Dither.NONE).convert("RGBA")
        arr = np.array(sub)
        lum = arr[..., :3].astype(np.float32).sum(axis=2) / 3.0
        arr[..., 3] = np.where(lum < seuil * 0.8, 0, 255)
        objets.append(Image.fromarray(arr, "RGBA"))
    return objets


def masque_veines(im, seuil_cyan=0.30):
    """
    Repère les joints lumineux du sol dans une image convertie : pixels dont
    le bleu et le vert dominent nettement le rouge, et qui sont clairs.
    Sert à animer les veines exactement là où l'image les a peintes.
    """
    a = np.asarray(im.convert("RGB"), dtype=np.float32) / 255.0
    r, g, b = a[..., 0], a[..., 1], a[..., 2]
    lum = (r + g + b) / 3.0
    cyan = np.minimum(g, b) - r
    return (cyan > seuil_cyan) & (lum > 0.30)
