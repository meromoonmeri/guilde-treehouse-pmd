from __future__ import annotations

"""Ramene un calque au grain d'un vrai tileset PMDO, façon Palikadude/Halcyon.

DIAGNOSTIC
----------
L'interieur du cafe de Metano a ete reconstitue tuile par tuile depuis
`Palikadude/Halcyon` pour servir d'etalon. La comparaison est sans appel :

                                        Palika      nous (avant)
    couleurs de l'image                    396           60 299
    couleurs dans une tuile 8x8 (moyenne)  5,3             59,2
    tuiles tenant en 16 couleurs          99,4 %            0 %
    pixels voisins STRICTEMENT identiques 76,2 %          1,6 %
    longueur moyenne d'une plage unie     4,18 px        1,02 px

Autrement dit : chez Palika, un aplat est un vrai aplat — de longues plages de
pixels rigoureusement identiques. Chez nous, **98,5 % des plages ne font qu'un
seul pixel** : le generateur d'image depose un grain de +-1 a +-12 niveaux sur
chaque pixel. Ce grain est invisible a l'ecran, mais il est fatal a l'import :

  * l'editeur PMDO decoupe en tuiles 8x8 et **deduplique** ; avec 59 couleurs
    par tuile, aucune tuile ne se repete jamais,
  * une tuile DS tient normalement sur 16 couleurs, et l'editeur reindexe la
    palette : les deux tiers des pixels sont alors deplaces vers une teinte
    voisine, d'ou la bouillie constatee en jeu.

CORRECTION
----------
On reconstruit de vrais aplats, **sans toucher au dessin** :

  1. `posteriser` — chaque zone de couleur homogene est ramenee a une teinte
     unique. On travaille par regroupement des teintes voisines vers la plus
     frequente de leur voisinage, pas par quantification uniforme : les aplats
     redeviennent plats, les bords et les details gardent leurs teintes
     propres.
  2. `limiter_par_tuile` — dans chaque tuile de 8x8, les couleurs restantes
     au-dela des 16 plus presentes sont ramenees a la plus proche des 16
     retenues. C'est exactement la contrainte d'un tileset DS.

Aucun pixel n'est moyenne, aucune couleur n'est inventee : chaque pixel recoit
une teinte deja presente a cote de lui. L'alpha reste binaire.

Usage :
    python3 aplatir_comme_palika.py <fichier.png> [...]
"""

from pathlib import Path
import sys

import numpy as np
from PIL import Image

TILE = 8

# Deux teintes plus proches que cela appartiennent au meme aplat. Le grain
# mesure sur nos calques va de 1 a 12 niveaux : 14 l'absorbe entierement.
GRAIN = 14

# Contrainte d'un tileset DS : 16 couleurs par tuile de 8x8.
COUL_PAR_TUILE = 16


def posteriser(a: np.ndarray) -> np.ndarray:
    """Fusionne les teintes separees par moins que le grain."""
    op = a[:, :, 3] > 128
    px = a[:, :, :3][op]
    coul, cnt = np.unique(px, axis=0, return_counts=True)
    ordre = np.argsort(-cnt)
    coul, cnt = coul[ordre].astype(int), cnt[ordre]

    # On parcourt les teintes de la plus frequente a la plus rare : chacune
    # devient soit un nouveau « pilier », soit l'alias du pilier voisin.
    piliers: list[np.ndarray] = []
    table = {}
    for c in coul:
        if piliers:
            P = np.array(piliers)
            d = np.abs(P - c).max(axis=1)
            j = int(d.argmin())
            if d[j] <= GRAIN:
                table[tuple(c)] = tuple(P[j])
                continue
        piliers.append(c)
        table[tuple(c)] = tuple(c)

    plat = a[:, :, :3].reshape(-1, 3)
    masque = op.reshape(-1)
    idx = np.nonzero(masque)[0]
    vals = plat[idx]
    sortie = np.array([table[tuple(v)] for v in vals], dtype=np.uint8)
    plat[idx] = sortie
    a[:, :, :3] = plat.reshape(a.shape[0], a.shape[1], 3)
    return a


def limiter_par_tuile(a: np.ndarray) -> np.ndarray:
    """Ramene chaque tuile 8x8 a 16 couleurs, comme un tileset DS."""
    h, w, _ = a.shape
    for y in range(0, h - TILE + 1, TILE):
        for x in range(0, w - TILE + 1, TILE):
            t = a[y:y + TILE, x:x + TILE]
            m = t[:, :, 3] > 128
            if m.sum() == 0:
                continue
            px = t[:, :, :3][m]
            coul, cnt = np.unique(px, axis=0, return_counts=True)
            if len(coul) <= COUL_PAR_TUILE:
                continue
            garde = coul[np.argsort(-cnt)[:COUL_PAR_TUILE]].astype(int)
            d = np.abs(px[:, None, :].astype(int) - garde[None, :, :]).max(axis=2)
            t[:, :, :3][m] = garde[d.argmin(axis=1)].astype(np.uint8)
    return a


def mesurer(a: np.ndarray) -> tuple[int, float, float]:
    op = a[:, :, 3] > 200
    coul = len(np.unique(a[:, :, :3][op], axis=0))
    parTuile = []
    h, w, _ = a.shape
    for y in range(0, h - TILE + 1, TILE):
        for x in range(0, w - TILE + 1, TILE):
            t = a[y:y + TILE, x:x + TILE]
            m = t[:, :, 3] > 200
            if m.sum() < 32:
                continue
            parTuile.append(len(np.unique(t[:, :, :3][m], axis=0)))
    moy = float(np.mean(parTuile)) if parTuile else 0.0
    d = np.abs(a[:, 1:, :3].astype(int) - a[:, :-1, :3].astype(int)).max(axis=2)
    mm = op[:, 1:] & op[:, :-1]
    ident = float((d[mm] == 0).mean() * 100) if mm.any() else 0.0
    return coul, moy, ident


def traiter(path: Path) -> None:
    im = Image.open(path).convert("RGBA")
    a = np.array(im)
    c0, t0, i0 = mesurer(a)

    a = posteriser(a)
    a = limiter_par_tuile(a)
    a[:, :, 3] = np.where(a[:, :, 3] > 128, 255, 0)

    c1, t1, i1 = mesurer(a)
    Image.fromarray(a, "RGBA").save(path)
    print(f"{path.name:34s} couleurs {c0:6d} -> {c1:5d} | "
          f"par tuile {t0:5.1f} -> {t1:4.1f} | "
          f"voisins identiques {i0:4.1f}% -> {i1:4.1f}%")


def main() -> int:
    args = sys.argv[1:]
    if not args:
        print(__doc__)
        return 1
    print("Aplatissement facon tileset Palika (etalon : 5,3 coul/tuile, 76% "
          "de voisins identiques)\n")
    for p in args:
        traiter(Path(p))
    return 0


if __name__ == "__main__":
    sys.exit(main())
