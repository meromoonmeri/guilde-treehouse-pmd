"""
liquides.py — tuiles de liquide animées, du dessin à l'export Tiled.

Chaîne complète :

  1. la planche de tuiles peintes est découpée et ramenée à 24 px ;
  2. chaque tuile est indexée sur une palette de 16 couleurs, triée par
     luminance : c'est la palette que le format DPLA anime ;
  3. les images de l'animation sont produites par **substitution de couleurs**
     — les indices des pixels ne changent jamais, exactement comme sur le
     matériel Nintendo ;
  4. le tout est empaqueté en planche de tuiles, en `.tsx` Tiled avec des
     blocs `<animation>`, et en `.aseprite` multi-images avec un tag.

Le point important : générer huit dessins indépendants ne donnerait pas une
animation d'eau PMD mais un scintillement incohérent, puisque les pixels
changeraient d'une image à l'autre. Un seul dessin, animé par sa palette,
donne le rendu du jeu.
"""

from __future__ import annotations

import os
import numpy as np
from PIL import Image

import dpla as DPLA

T = 24


# --------------------------------------------------------------------------
# Découpe et indexation
# --------------------------------------------------------------------------



def _fond(im):
    a = np.asarray(im.convert("RGB"), dtype=np.float32)
    coins = np.array([a[0, 0], a[0, -1], a[-1, 0], a[-1, -1]])
    return np.median(coins, axis=0)


def decouper(chemin, ech=4, aire_min=0.004):
    """Composantes connexes sur fond uni, puis mise au gabarit 24 x 24."""
    from collections import deque
    im = Image.open(chemin).convert("RGB")
    W, H = im.size
    pet = im.resize((W // ech, H // ech), Image.LANCZOS)
    a = np.asarray(pet, dtype=np.float32)
    fond = _fond(pet)
    m = np.linalg.norm(a - fond, axis=2) > 46
    h, w = m.shape
    vus = np.zeros_like(m)
    boites = []
    for y0 in range(h):
        for x0 in range(w):
            if not m[y0, x0] or vus[y0, x0]:
                continue
            q = deque([(y0, x0)])
            vus[y0, x0] = True
            xs0 = xs1 = x0
            ys0 = ys1 = y0
            n = 0
            while q:
                y, x = q.popleft()
                n += 1
                xs0, xs1 = min(xs0, x), max(xs1, x)
                ys0, ys1 = min(ys0, y), max(ys1, y)
                for dy in (-1, 0, 1):
                    for dx in (-1, 0, 1):
                        ny, nx = y + dy, x + dx
                        if 0 <= ny < h and 0 <= nx < w and m[ny, nx] and not vus[ny, nx]:
                            vus[ny, nx] = True
                            q.append((ny, nx))
            if n >= aire_min * h * w:
                boites.append((xs0, ys0, xs1, ys1))
    boites.sort(key=lambda b: (b[1] // max(1, h // 3), b[0]))
    tuiles = []
    for (x0, y0, x1, y1) in boites:
        b = (x0 * ech, y0 * ech, (x1 + 1) * ech, (y1 + 1) * ech)
        sub = im.crop(b)
        c = min(sub.size)
        sub = sub.crop(((sub.size[0] - c) // 2, (sub.size[1] - c) // 2,
                        (sub.size[0] - c) // 2 + c, (sub.size[1] - c) // 2 + c))
        tuiles.append(sub.resize((T, T), Image.LANCZOS))
    return tuiles


def rendre_raccordable(t, marge=3):
    """
    Rend une tuile raccordable par fondu croisé de ses bords opposés.
    Sans ce passage, une nappe pavée laisse voir la grille.
    """
    a = np.asarray(t.convert("RGB"), dtype=np.float32)
    r = np.linspace(0, 1, marge)[:, None, None]
    a[:marge] = a[:marge] * r + a[-marge:][::-1] * (1 - r)
    r2 = np.linspace(0, 1, marge)[None, :, None]
    a[:, :marge] = a[:, :marge] * r2 + a[:, -marge:][:, ::-1] * (1 - r2)
    return Image.fromarray(np.clip(a, 0, 255).astype(np.uint8), "RGB")


def indexer_sur_rampe(tuiles, n_couleurs=12):
    """
    Indexe toutes les tuiles sur une palette commune triée par luminance.
    Renvoie (cartes d'indices, rampe).
    """
    larg = sum(t.size[0] for t in tuiles)
    planche = Image.new("RGB", (larg, T))
    x = 0
    for t in tuiles:
        planche.paste(t, (x, 0))
        x += t.size[0]
    q = planche.quantize(colors=n_couleurs, method=Image.Quantize.MAXCOVERAGE,
                         dither=Image.Dither.NONE)
    pal = q.getpalette()[: n_couleurs * 3]
    couleurs = [tuple(pal[i * 3:i * 3 + 3]) for i in range(n_couleurs)]
    utilisees = sorted({i for i in q.getdata()})
    couleurs = [couleurs[i] for i in utilisees]
    ordre = sorted(range(len(couleurs)),
                   key=lambda i: 0.2126 * couleurs[i][0] + 0.7152 * couleurs[i][1]
                   + 0.0722 * couleurs[i][2])
    rampe = [couleurs[o] for o in ordre]
    r = np.array(rampe, dtype=np.float32)
    cartes = []
    for t in tuiles:
        a = np.asarray(t.convert("RGB"), dtype=np.float32).reshape(-1, 3)
        idx = np.argmin(np.linalg.norm(a[:, None, :] - r[None, :, :], axis=2), axis=1)
        cartes.append(idx.reshape(T, T))
    return cartes, rampe


# --------------------------------------------------------------------------
# Animation DPLA et empaquetage
# --------------------------------------------------------------------------

def images_dpla(cartes, rampe, n_images=12, longueurs=(3, 4, 6, 4), duree=6):
    """
    Produit les images de chaque tuile par substitution de palette.
    Les indices des pixels sont identiques d'une image à l'autre.
    """
    table = DPLA.table_depuis_rampe(rampe, longueurs=longueurs, duree=duree)
    periode = table.periode(0)
    pas = max(1, periode // n_images)
    suites = []
    for carte in cartes:
        images = []
        for k in range(n_images):
            pal = table.palette_a_l_image(0, k * pas)
            tab = np.array([pal[i] if i < len(pal) else (0, 0, 0)
                            for i in range(len(rampe))], dtype=np.uint8)
            images.append(Image.fromarray(tab[np.clip(carte, 0, len(tab) - 1)], "RGB"))
        suites.append(images)
    return suites, table


def planche_animee(suites):
    """
    Planche de tuiles : une colonne par image, une ligne par tuile.
    C'est la disposition attendue par Tiled pour des tuiles animées.
    """
    n_tuiles = len(suites)
    n_img = len(suites[0])
    out = Image.new("RGBA", (n_img * T, n_tuiles * T))
    for i, suite in enumerate(suites):
        for k, im in enumerate(suite):
            out.paste(im.convert("RGBA"), (k * T, i * T))
    return out, n_img, n_tuiles


def ecrire_tsx(chemin, nom, image_rel, n_img, n_tuiles, duree_ms, largeur, hauteur):
    """
    Jeu de tuiles Tiled avec de vraies tuiles animées.

    Chaque tuile source porte un bloc <animation> listant ses images et leur
    durée. Tiled les joue dans l'éditeur, et tout moteur lisant le .tsx
    retrouve l'animation sans code supplémentaire.
    """
    L = ['<?xml version="1.0" encoding="UTF-8"?>',
         f'<tileset version="1.10" tiledversion="1.10.2" name="{nom}" '
         f'tilewidth="{T}" tileheight="{T}" tilecount="{n_img * n_tuiles}" '
         f'columns="{n_img}">',
         f' <image source="{image_rel}" width="{largeur}" height="{hauteur}"/>']
    for i in range(n_tuiles):
        premier = i * n_img
        L.append(f' <tile id="{premier}">')
        L.append('  <animation>')
        for k in range(n_img):
            L.append(f'   <frame tileid="{premier + k}" duration="{duree_ms}"/>')
        L.append('  </animation>')
        L.append(' </tile>')
    L.append('</tileset>')
    open(chemin, "w").write("\n".join(L) + "\n")


def ecrire_aseprite(chemin, suites, duree_ms):
    """Un calque par tuile, une image par pas d'animation, plus un tag."""
    import aseprite
    n_tuiles = len(suites)
    n_img = len(suites[0])
    noms = [f"tuile_{i:02d}" for i in range(n_tuiles)]
    structure = [{"nom": n} for n in noms]
    images = []
    for k in range(n_img):
        jeu = {}
        for i, n in enumerate(noms):
            lame = Image.new("RGBA", (T, T * n_tuiles))
            lame.paste(suites[i][k].convert("RGBA"), (0, i * T))
            jeu[n] = lame
        images.append(jeu)
    aseprite.ecrire_avance(chemin, structure, images, (T, T * n_tuiles),
                           duree_ms=duree_ms,
                           tags=[("liquide", 0, n_img - 1, aseprite.AVANT,
                                  (90, 170, 230))])


def ecrire_tmx_demo(chemin, tsx_rel, nom_tsx, cols=20, lignes=15,
                    n_img=12, n_tuiles=4):
    """
    Petite carte Tiled de démonstration : une mare animée au centre.

    Les identifiants pointent sur la première image de chaque tuile ; c'est le
    bloc <animation> du .tsx qui fait défiler les suivantes. Ouvrir ce fichier
    dans Tiled suffit à voir l'eau bouger.
    """
    import math
    donnees = []
    for y in range(lignes):
        ligne = []
        for x in range(cols):
            d = math.hypot((x - cols / 2) / (cols * 0.30),
                           (y - lignes / 2) / (lignes * 0.30))
            if d < 1.0:
                gid = 1 + ((x + y) % n_tuiles) * n_img      # première image
            else:
                gid = 0
            ligne.append(str(gid))
        donnees.append(",".join(ligne))
    L = ['<?xml version="1.0" encoding="UTF-8"?>',
         f'<map version="1.10" tiledversion="1.10.2" orientation="orthogonal" '
         f'renderorder="right-down" width="{cols}" height="{lignes}" '
         f'tilewidth="{T}" tileheight="{T}" infinite="0" nextlayerid="2" '
         f'nextobjectid="1">',
         f' <tileset firstgid="1" source="{tsx_rel}"/>',
         f' <layer id="1" name="{nom_tsx}" width="{cols}" height="{lignes}">',
         '  <data encoding="csv">',
         ",\n".join(donnees),
         '  </data>', ' </layer>', '</map>']
    open(chemin, "w").write("\n".join(L) + "\n")
