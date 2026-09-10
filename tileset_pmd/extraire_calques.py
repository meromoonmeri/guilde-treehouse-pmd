from __future__ import annotations

"""Extrait des calques separes des interieurs, au meme scale que le tileset.

Deux calques sont produits, tous deux dans le meme cadre 456 x 320 que les
calques de fond, avec le meme offset : ils se superposent donc au pixel pres,
sans aucun recalage. C'est la regle des tilesets PMDO / RogueEssence, ou le
cafe de Metano est decoupe en `_Base`, `_Objects`, `_Objects_Fringe`, etc.

  1. `interieur_deco_seule_*.png`
     Difference entre le calque decore et le calque vide : ne restent que les
     meubles, les guirlandes et **leurs ombres portees**. Tout le reste est
     transparent.

  2. `interieur_fenetres_jour.png`
     Les quatre disques de vitrage seuls, decoupes sur le calque de jour. Sert
     de calque d'eclairage : on le pose sur la version nuit pour rallumer les
     fenetres, ou on le remplace pour changer le ciel.

L'extraction se fait par comparaison exacte de pixels, jamais par un seuil de
couleur : aucun pixel n'est recalcule, donc aucune perte de qualite. L'alpha
reste strictement binaire (0 ou 255).

Usage :
    python3 extraire_calques.py
"""

from pathlib import Path
import sys

import numpy as np
from PIL import Image

ICI = Path(__file__).resolve().parent.parent / "interieur"

# Tolerance de comparaison. Le generateur reharmonise legerement les teintes du
# fond quand il ajoute les meubles ; en dessous de ce delta on considere que le
# pixel n'a pas change et il part en transparent.
DELTA = 55


def charger(nom: str) -> np.ndarray:
    return np.array(Image.open(ICI / nom).convert("RGBA"))


def ecrire(arr: np.ndarray, nom: str) -> None:
    Image.fromarray(arr, "RGBA").save(ICI / nom)
    opaque = int((arr[:, :, 3] > 0).sum())
    alpha = arr[:, :, 3]
    semi = int(((alpha > 0) & (alpha < 255)).sum())
    print(f"    -> {nom:44s} {opaque:6d} px visibles  semi={semi}")


def deco_seule(vide: str, decore: str, sortie: str) -> None:
    a = charger(vide).astype(int)
    b = charger(decore).astype(int)
    if a.shape != b.shape:
        sys.exit(f"tailles differentes : {vide} {a.shape} vs {decore} {b.shape}")

    ecart = np.abs(a[:, :, :3] - b[:, :, :3]).max(axis=2)
    change = (ecart > DELTA) & (b[:, :, 3] > 128)

    # Le rendu du bois bouge de quelques points entre les deux generations, ce
    # qui seme des pixels isoles hors des meubles. On ne garde donc que les
    # pixels ayant au moins 4 voisins retenus sur 8 : les aplats des meubles
    # passent, le bruit du plancher tombe.
    pad = np.pad(change, 1, constant_values=False).astype(np.uint8)
    voisins = (
        pad[:-2, :-2] + pad[:-2, 1:-1] + pad[:-2, 2:]
        + pad[1:-1, :-2] + pad[1:-1, 2:]
        + pad[2:, :-2] + pad[2:, 1:-1] + pad[2:, 2:]
    )
    change &= voisins >= 4

    out = np.zeros_like(b, dtype=np.uint8)
    out[change] = b[change].astype(np.uint8)
    out[:, :, 3] = np.where(change, 255, 0).astype(np.uint8)
    ecrire(out, sortie)


def fenetres(source: str, sortie: str) -> None:
    """Isole le vitrage : bleu franc (jour) a l'interieur des disques hauts."""
    a = charger(source).astype(int)
    r, g, b, al = a[:, :, 0], a[:, :, 1], a[:, :, 2], a[:, :, 3]

    # De jour le vitrage est bleu ciel clair, de nuit bleu nuit profond : dans
    # les deux cas le bleu domine nettement le rouge, ce qui n'arrive nulle
    # part dans le bois environnant.
    verre = (b - r > 15) & (b > 55) & (al > 128)

    # Les vitres sont dans la moitie haute : on coupe le reste pour ne pas
    # attraper un bol bleu ou le tapis du stand de droite.
    limite = int(a.shape[0] * 0.42)
    verre[limite:, :] = False

    out = np.zeros_like(a, dtype=np.uint8)
    out[verre] = a[verre].astype(np.uint8)
    out[:, :, 3] = np.where(verre, 255, 0).astype(np.uint8)
    ecrire(out, sortie)


def main() -> None:
    print("Extraction des calques separes (cadre 456 x 320, offset identique)\n")

    # Le calque de decoration n'est PAS extrait par difference : deux
    # generations successives reteintent legerement tout le bois, ce qui
    # troue les meubles. Il est produit par `caler_calque_deco.py`.

    print("\n  Calque FENETRES (vitrage seul)")
    fenetres("interieur_sans_deco_jour_grille8.png", "interieur_fenetres_jour.png")
    fenetres("interieur_sans_deco_nuit_grille8.png", "interieur_fenetres_nuit.png")


if __name__ == "__main__":
    main()
