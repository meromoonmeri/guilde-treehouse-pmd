from __future__ import annotations

"""Pose les meubles du tilesheet dans notre salle, au format PMDO.

Les meubles viennent de `interieur/meubles/meubles_cafe_tilesheet.png`, lui-meme
extrait des vrais tilesets du jeu (`SpindaCafe2.tile` d'ExplorersOfSkyOrigins et
les calques d'objets de Metano dans Halcyon). Ils ne sont donc ni redessines ni
repasses au generateur : on les **deplace**, ce qui preserve exactement leur
qualite d'asset.

Deux fichiers sont produits pour chaque moment de la journee :

  * `interieur_deco_seule_<moment>.png` — les meubles seuls sur fond
    transparent, dans le cadre 576 x 400 et au meme offset que la salle, donc
    superposable au pixel pres ;
  * `interieur_avec_deco_<moment>.png` — la salle vide avec ce calque pose
    dessus.

Chaque objet recoit une **ombre portee** elliptique posee au sol, comme dans le
calque `SpindaCafe1.tile` du jeu, ou les ombres vivent avec le decor.

Les positions sont donnees en pixels dans le cadre 576 x 400, celui de la salle
agrandie a l'echelle du Spinda Cafe officiel (voir `agrandir_salle.py`).

Usage :
    python3 poser_meubles.py
"""

from pathlib import Path
import json
import sys

import numpy as np
from PIL import Image

RACINE = Path(__file__).resolve().parent.parent / "interieur"
SHEET = RACINE / "meubles" / "meubles_cafe_tilesheet.png"
MANIFESTE = RACINE / "meubles" / "meubles_cafe_tilesheet.json"

# (nom de l'objet, x du centre, y du BAS de l'objet) dans le cadre 576 x 400.
# Le placement suit le layout : les deux stands contre le mur du fond, les
# tables au centre, les plantes et caisses contre les bords, l'escalier degage.
PLAN = [
    # --- fond : les deux stands Spinda, de part et d'autre de l'axe ---
    ("spinda_stand_gauche", 188, 190),
    ("spinda_stand_droit", 391, 190),
    # --- guirlandes le long du mur du fond ---
    ("spinda_guirlande_gauche", 153, 120),
    ("spinda_guirlande_droite", 425, 120),
    # --- tables et tabourets, au centre, en laissant l'allee centrale ---
    ("metano_07", 138, 272),      # table-souche
    ("spinda_09", 188, 268),      # tabouret
    ("metano_08", 248, 308),      # table-souche
    ("spinda_10", 298, 302),      # tabouret
    ("metano_10", 378, 272),      # table-souche
    ("spinda_11", 331, 268),      # tabouret
    ("metano_12", 438, 305),      # table-souche
    # --- bord gauche : panneau, plantes, buisson ---
    ("metano_11", 81, 248),       # panneau menu
    ("decor_16", 145, 300),        # plante haute
    ("decor_21", 205, 330),       # petite plante fleurie
    # --- bord droit : caisses, plantes ---
    ("metano_03", 493, 292),      # pile de caisses
    ("decor_13", 400, 318),       # plante en pot
    # --- accents sur les murs lateraux ---
    ("spinda_panneaux_mur", 288, 130),
]

# Ombre portee : petite ellipse posee au pied de l'objet. Elle est peinte en
# assombrissant le SOL directement, pas en superposant un voile translucide :
# l'alpha du calque reste binaire, comme l'exige un tileset PMDO.
OMBRE_FACTEUR = 0.72      # le sol garde 72 % de sa luminosite sous l'ombre
OMBRE_LARGEUR = 0.34      # part de la largeur de l'objet
OMBRE_HAUTEUR = 0.26      # aplatissement de l'ellipse

# Les elements adosses au mur ou suspendus ne posent pas d'ombre au sol : leur
# large boite englobante donnerait une flaque sombre en plein milieu de la piece.
SANS_OMBRE = {
    "spinda_stand_gauche", "spinda_stand_droit",
    "spinda_guirlande_gauche", "spinda_guirlande_droite",
    "spinda_panneaux_mur",
}


def charger_objets() -> dict[str, Image.Image]:
    sheet = Image.open(SHEET).convert("RGBA")
    manif = json.loads(MANIFESTE.read_text())
    out = {}
    for o in manif["objets"]:
        out[o["nom"]] = sheet.crop((o["px_x"], o["px_y"],
                                    o["px_x"] + o["px_w"],
                                    o["px_y"] + o["px_h"]))
    return out


def poser_ombre(sol: np.ndarray, cx: int, bas: int, larg: int) -> None:
    """Assombrit le sol sous l'objet, en place, sans toucher a l'alpha."""
    rw = max(4, int(larg * OMBRE_LARGEUR))
    rh = max(2, int(rw * OMBRE_HAUTEUR))
    for y in range(max(0, bas - rh), min(sol.shape[0], bas + rh + 1)):
        dy = (y - bas) / rh
        if abs(dy) > 1:
            continue
        demi = int(rw * (1 - dy * dy) ** 0.5)
        for x in range(max(0, cx - demi), min(sol.shape[1], cx + demi)):
            if sol[y, x, 3] > 128:
                sol[y, x, :3] = (sol[y, x, :3].astype(int)
                                 * OMBRE_FACTEUR).astype(np.uint8)


def composer(moment: str, objets: dict[str, Image.Image]) -> None:
    salle_p = RACINE / f"interieur_sans_deco_{moment}.png"
    salle = Image.open(salle_p).convert("RGBA")

    # 1) les ombres sont peintes sur une copie du sol : le calque de deco garde
    #    un alpha strictement binaire
    ombre = np.array(salle).copy()
    for nom, cx, bas in PLAN:
        im = objets.get(nom)
        if im is None:
            print(f"  absent du sheet : {nom}", file=sys.stderr)
            continue
        if nom in SANS_OMBRE:
            continue
        poser_ombre(ombre, cx, bas, im.size[0])
    fond = Image.fromarray(ombre, "RGBA")

    # 2) les meubles, du plus haut place au plus bas : ceux de devant
    #    recouvrent ceux du fond
    calque = Image.new("RGBA", salle.size, (0, 0, 0, 0))
    for nom, cx, bas in sorted(PLAN, key=lambda t: t[2]):
        im = objets.get(nom)
        if im is None:
            continue
        calque.alpha_composite(im, (cx - im.size[0] // 2, bas - im.size[1]))

    # le calque seul porte les meubles ET l'ombre la ou elle est visible
    diff = np.array(fond)
    base = np.array(salle)
    bouge = (np.abs(diff[:, :, :3].astype(int)
                    - base[:, :, :3].astype(int)).max(axis=2) > 4)
    seul = np.array(calque)
    pose = seul[:, :, 3] > 128
    seul[bouge & ~pose] = diff[bouge & ~pose]
    seul[:, :, 3] = np.where(pose | bouge, 255, 0)
    Image.fromarray(seul, "RGBA").save(
        RACINE / f"interieur_deco_seule_{moment}.png")

    plein = fond.copy()
    plein.alpha_composite(calque)
    plein.save(RACINE / f"interieur_avec_deco_{moment}.png")
    plein.save(RACINE / f"interieur_avec_deco_{moment}_grille8.png")

    a = np.array(plein)
    al = a[:, :, 3]
    op = al > 200
    print(f"  {moment:5s} -> {len(PLAN)} objets  "
          f"couleurs {len(np.unique(a[:, :, :3][op], axis=0))}  "
          f"semi {int(((al > 0) & (al < 255)).sum())}  "
          f"bbox {plein.getbbox()}")


def main() -> int:
    objets = charger_objets()
    print(f"{len(objets)} objets dans le tilesheet\n")
    for moment in ("jour", "nuit"):
        composer(moment, objets)
    return 0


if __name__ == "__main__":
    sys.exit(main())
