from __future__ import annotations

"""Prepare un calque d'interieur pour l'import « Load PNG to Tileset » de PMDO.

DIAGNOSTIC
----------
L'editeur PMDO decoupe le PNG en tuiles de 8 x 8, puis **deduplique** : deux
tuiles identiques ne sont stockees qu'une fois. Deux defauts font s'effondrer
ce mecanisme et donnent l'impression d'une perte de nettete.

1. LE DEGRADE. Nos calques sortent du generateur avec ~60 000 couleurs, dont
   **76 % n'apparaissent qu'une seule fois** : du bruit de degrade, invisible a
   l'oeil. L'intérieur officiel de Metano, lui, tient en **396 couleurs**. Quand
   l'editeur indexe la palette, 65 % de nos pixels sont alteres (contre 0,2 %
   pour Halcyon) : c'est la « bouillie » constatee a l'import.

2. LA GRILLE. Notre salle commence a x=20 et fait 415 px de large. Ni 20 ni 415
   ne sont multiples de 8 : chaque tuile decoupee tombe **a cheval** sur deux
   motifs, donc aucune ne se repete et le tileset explose (1602 tuiles uniques
   contre 1118 pour Halcyon, pour la meme surface).

CORRECTION
----------
  1. On **cale la salle sur la grille** : offset et largeur ramenes a des
     multiples de 8, sans deplacer le dessin par rapport a lui-meme.
  2. On **assainit la palette** par regroupement des teintes voisines. Chaque
     couleur rare est remplacee par la couleur frequente la plus proche, dans
     la limite d'un ecart imperceptible. Aucun pixel n'est moyenne, aucune
     couleur nouvelle n'est inventee : on ne fait que **supprimer les doublons
     quasi identiques**, exactement ce que fait un tileset ripe du jeu.

L'alpha reste strictement binaire (0 ou 255), les bords restent nets.

Usage :
    python3 assainir_pour_pmdo.py <fichier.png> [...]
"""

from pathlib import Path
import sys

import numpy as np
from PIL import Image

TILE = 8

# Deux teintes distantes de moins de cela sont perceptivement identiques : on
# les fusionne. Au-dela on preserve la nuance, pour ne perdre aucun detail.
SEUIL = 16

# Une couleur est jugee « porteuse » du dessin au-dela de ce nombre de pixels.
MIN_PIXELS = 12


def caler_grille(im: Image.Image) -> Image.Image:
    """Ramene le contenu a un offset et une taille multiples de 8."""
    box = im.getbbox()
    if box is None:
        return im
    x0, y0, x1, y1 = box
    a = np.array(im)

    # largeur/hauteur portees au multiple de 8 superieur en dupliquant la
    # derniere ligne/colonne : aucun pixel existant n'est modifie
    manque_x = (-(x1 - x0)) % TILE
    for i in range(manque_x):
        if x1 + i < a.shape[1]:
            col = a[:, x1 - 1]
            a[:, x1 + i] = np.where(col[:, 3:4] > 128, col, a[:, x1 + i])
    manque_y = (-(y1 - y0)) % TILE
    for i in range(manque_y):
        if y1 + i < a.shape[0]:
            lig = a[y1 - 1, :]
            a[y1 + i, :] = np.where(lig[:, 3:4] > 128, lig, a[y1 + i, :])

    im = Image.fromarray(a, "RGBA")

    # offset ramene au multiple de 8 le plus proche
    dx = -(x0 % TILE) if x0 % TILE <= TILE // 2 else TILE - (x0 % TILE)
    dy = -(y0 % TILE) if y0 % TILE <= TILE // 2 else TILE - (y0 % TILE)
    if dx or dy:
        cadre = Image.new("RGBA", im.size, (0, 0, 0, 0))
        cadre.paste(im, (dx, dy), im)
        im = cadre
    return im


def assainir_palette(im: Image.Image) -> tuple[Image.Image, int, int]:
    """Fusionne les teintes quasi identiques, sans en inventer aucune."""
    a = np.array(im)
    op = a[:, :, 3] > 128
    px = a[:, :, :3][op]
    avant = len(np.unique(px, axis=0))

    coul, cnt = np.unique(px, axis=0, return_counts=True)
    fortes = coul[cnt >= MIN_PIXELS].astype(int)
    if len(fortes) == 0:
        return im, avant, avant

    # chaque couleur -> la couleur « forte » la plus proche si elle est assez
    # voisine, sinon elle est conservee telle quelle
    table = {}
    for c in coul:
        ci = c.astype(int)
        d = np.abs(fortes - ci).max(axis=1)
        j = int(d.argmin())
        table[tuple(c)] = tuple(fortes[j]) if d[j] <= SEUIL else tuple(ci)

    plat = a[:, :, :3].reshape(-1, 3)
    masque = op.reshape(-1)
    sortie = plat.copy()
    for i in np.nonzero(masque)[0]:
        sortie[i] = table[tuple(plat[i])]
    a[:, :, :3] = sortie.reshape(a.shape[0], a.shape[1], 3)

    a[:, :, 3] = np.where(a[:, :, 3] > 128, 255, 0)
    res = Image.fromarray(a, "RGBA")
    apres = len(np.unique(a[:, :, :3][a[:, :, 3] > 128], axis=0))
    return res, avant, apres


def compter_tuiles(im: Image.Image) -> tuple[int, int]:
    a = np.array(im)
    h, w, _ = a.shape
    ts = [
        a[y:y + TILE, x:x + TILE].tobytes()
        for y in range(0, h - TILE + 1, TILE)
        for x in range(0, w - TILE + 1, TILE)
    ]
    return len(ts), len(set(ts))


def traiter(path: Path) -> None:
    im = Image.open(path).convert("RGBA")
    n0, u0 = compter_tuiles(im)

    im = caler_grille(im)
    im, c0, c1 = assainir_palette(im)

    n1, u1 = compter_tuiles(im)
    box = im.getbbox()
    im.save(path)

    al = np.array(im)[:, :, 3]
    semi = int(((al > 0) & (al < 255)).sum())
    print(f"{path.name:38s} couleurs {c0:6d} -> {c1:5d}"
          f"   tuiles uniques {u0:5d} -> {u1:5d}"
          f"   bbox x={box[0]} l={box[2] - box[0]}"
          f"   semi={semi}")


def main() -> int:
    args = sys.argv[1:]
    if not args:
        print(__doc__)
        return 1
    print("Assainissement pour l'import PMDO (tuiles 8x8, palette groupee)\n")
    for a in args:
        traiter(Path(a))
    return 0


if __name__ == "__main__":
    sys.exit(main())
