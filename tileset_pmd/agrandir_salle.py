from __future__ import annotations

"""Agrandit la salle (et elle seule) pour retrouver l'echelle du Spinda Cafe.

AUDIT (mesures faites sur `interieur/reference/spinda_cafe_officiel_pmd_sky.png`,
le rip officiel de Explorers of Sky, compare a `interieur_sans_deco_jour.png`) :

  * asset officiel : sol large de 426 px, tables rondes de 43 px, comptoirs de
    120 px. Une table occupe donc 10,1 % de la largeur du sol, un comptoir 28,2 %.
  * notre salle : sol large de 405 px, tables de 46 a 53 px, comptoirs de 150 px.
    Une table occupe 11,7 % de la largeur du sol, un comptoir 37,0 %.

Conclusion : le mobilier n'est pas trop grand dans l'absolu — il est a la bonne
taille d'asset, celle du jeu — c'est **la piece qui est trop petite pour lui**,
d'un facteur 1,16 (tables) a 1,32 (comptoirs), soit 1,235 en moyenne.

On corrige donc la piece, jamais les meubles, avec un facteur exact de
**5/4 = 1,25** : agrandissement entier x5 au plus proche voisin, puis reduction
x4 par couleur dominante de bloc. Aucune interpolation n'intervient, donc aucune
perte de nettete ni couleur inventee, et le facteur reste rationnel simple.

Cadre : 456 x 320 (57 x 40 cellules) -> 576 x 400 (72 x 50 cellules), la salle
agrandie etant centree horizontalement et calee en bas (l'escalier reste sur le
bord inferieur).

Usage :
    python3 agrandir_salle.py
"""

from collections import Counter
from pathlib import Path

import numpy as np
from PIL import Image

RACINE = Path(__file__).resolve().parent.parent / "interieur"

NUM, DEN = 5, 4               # facteur 1,25 exact
CIBLE_W, CIBLE_H = 576, 400   # 72 x 50 cellules de 8 px
TILE = 8

CALQUES = [
    "interieur_sans_deco_jour",
    "interieur_sans_deco_nuit",
    "interieur_fenetres_jour",
    "interieur_fenetres_nuit",
]


def reduire_dominante(img: Image.Image, facteur: int) -> Image.Image:
    """Reduit d'un facteur entier en prenant la couleur dominante de chaque bloc.

    Un filtre classique moyennerait les pixels : les bords deviendraient flous
    et de nouvelles couleurs apparaitraient, ce qui casse la contrainte de
    16 couleurs par tuile. La dominante garde des aplats francs.
    """
    a = np.array(img.convert("RGBA"))
    h, w = a.shape[:2]
    hw, hh = w // facteur, h // facteur
    out = np.zeros((hh, hw, 4), dtype=np.uint8)
    for y in range(hh):
        for x in range(hw):
            bloc = a[y * facteur:(y + 1) * facteur, x * facteur:(x + 1) * facteur]
            pix = [tuple(int(v) for v in p) for p in bloc.reshape(-1, 4)]
            opaques = [p for p in pix if p[3] > 127]
            if len(opaques) * 2 < len(pix):
                continue  # bloc majoritairement vide -> reste transparent
            r, g, b, _ = Counter(opaques).most_common(1)[0][0]
            out[y, x] = (r, g, b, 255)
    return Image.fromarray(out, "RGBA")


def agrandir(img: Image.Image) -> Image.Image:
    w, h = img.size
    gros = img.resize((w * NUM, h * NUM), Image.NEAREST)
    return reduire_dominante(gros, DEN)


def recadrer(img: Image.Image) -> Image.Image:
    """Place la salle agrandie dans le cadre cible : centree en x, calee en bas."""
    cadre = Image.new("RGBA", (CIBLE_W, CIBLE_H), (0, 0, 0, 0))
    ox = (CIBLE_W - img.size[0]) // 2
    oy = CIBLE_H - img.size[1]
    cadre.paste(img, (ox, oy))
    return cadre, ox, oy


def main() -> None:
    offsets = None
    for nom in CALQUES:
        chemin = RACINE / f"{nom}.png"
        if not chemin.exists():
            print(f"  absent : {chemin.name}")
            continue
        src = Image.open(chemin).convert("RGBA")
        grand = agrandir(src)
        cadre, ox, oy = recadrer(grand)
        offsets = (ox, oy)
        cadre.save(chemin)

        a = np.array(cadre)
        alpha = a[..., 3]
        semi = int(((alpha > 0) & (alpha < 255)).sum())
        ys, xs = np.nonzero(alpha > 0)
        couleurs = len({tuple(p) for p in a[alpha > 0][:, :3]})
        print(f"  {nom:28s} {src.size[0]}x{src.size[1]} -> {cadre.size[0]}x{cadre.size[1]}"
              f"  bbox ({xs.min()},{ys.min()},{xs.max()},{ys.max()})"
              f"  couleurs {couleurs}  semi {semi}")
    if offsets:
        print(f"\n  offset de la salle dans le cadre : {offsets}")


if __name__ == "__main__":
    main()
