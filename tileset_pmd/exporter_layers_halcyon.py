from __future__ import annotations

"""Reexporte nos salles selon la nomenclature de layers de Halcyon.

Voir `AUDIT_METHODE_LAYERS_HALCYON.md`. Les regles reprises :

  * un layer = une fonction visuelle, pas un objet ;
  * un layer = un tileset dedie qui porte son nom, `<Zone>_<Layer>` ;
  * le champ `Layer` vaut 0 (rendu sous le joueur) ou 4 (au-dessus) ;
  * pour un interieur, le socle est eclate en `Floor` + `Walls`, jamais `Base`.

Nos calques historiques (`sans_deco`, `deco_seule`) sont donc re-decoupes :

    interieur_sans_deco   ->  Floor   (le sol)      Layer 0
                              Walls   (parois)      Layer 0
    (ombres portees)      ->  Shadows                Layer 0
    interieur_deco_seule  ->  Objects (mobilier)     Layer 0
                              Objects_Over (suspendu) Layer 0
    (avant-plan)          ->  Fringe                 Layer 4

Le decoupage Floor/Walls se fait geometriquement : pour chaque colonne, les
pixels du socle situes SOUS la ligne d'horizon du sol sont du sol, ceux
au-dessus sont de la paroi. L'horizon est detecte par la teinte : le sol du
cafe est dore et clair, les parois sont brunes et sombres.

Usage :
    python3 exporter_layers_halcyon.py
"""

from pathlib import Path
import json

import numpy as np
from PIL import Image

RACINE = Path(__file__).resolve().parent.parent
TILE = 8

# nom du layer -> valeur du champ `Layer` de RogueEssence
PROFONDEUR = {
    "Floor": 0,
    "Walls": 0,
    "Shadows": 0,
    "Objects_Under": 0,
    "Objects": 0,
    "Objects_Over": 0,
    "Fringe": 4,
    "Supports": 4,
}

ZONES = [
    {
        "zone": "Cafe_Interior",
        "dossier": "interieur",
        "socle": "interieur_sans_deco_{m}.png",
        "deco": "interieur_deco_seule_{m}.png",
        "sortie": "layers",
        # au-dessus de cette ligne, un objet est suspendu (guirlandes, bandeau)
        "y_suspendu": 150,
    },
    {
        "zone": "Cafe_Basement",
        "dossier": "sous_sol",
        "socle": "sous_sol_sans_deco_{m}.png",
        "deco": "sous_sol_deco_seule_{m}.png",
        "sortie": "layers",
        "y_suspendu": 140,
    },
]


def separer_sol_parois(a: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Coupe le socle en Floor / Walls a la plinthe.

    Trier par teinte ne marche pas : les parois sont en bois dore, exactement
    comme le plancher, et de jour la quasi-totalite de la piece partait dans
    `Floor`. Ce qui separe reellement les deux, c'est la **plinthe** : une
    ligne sombre continue (~(151,82,5), nettement plus foncee que ses deux
    voisines) qui court au pied des parois.

    Pour chaque colonne on cherche donc, dans la moitie haute, la derniere
    rupture franche vers le sombre : tout ce qui est en dessous est du sol.
    Les colonnes sans plinthe visible heritent de la frontiere de leur voisine,
    ce qui evite les dents de scie.
    """
    m = a[..., 3] > 0
    h, w = m.shape
    lum = a[..., :3].astype(int).sum(2)

    frontiere = np.full(w, -1, dtype=int)
    for x in range(w):
        col = np.nonzero(m[:, x])[0]
        if len(col) == 0:
            continue
        y0, y1 = col.min(), col.max()
        limite = y0 + int((y1 - y0) * 0.6)
        meilleur, score = -1, 0
        for y in range(y0 + 2, min(limite, h - 3)):
            if not (m[y, x] and m[y - 2, x] and m[y + 2, x]):
                continue
            # creux de luminosite : la plinthe est plus sombre que dessus ET dessous
            creux = min(lum[y - 2, x], lum[y + 2, x]) - lum[y, x]
            if creux > score and creux > 90:
                score, meilleur = creux, y
        frontiere[x] = meilleur

    # lissage : une colonne sans plinthe reprend la derniere connue
    derniere = -1
    for x in range(w):
        if frontiere[x] < 0:
            frontiere[x] = derniere
        else:
            derniere = frontiere[x]
    suivante = -1
    for x in range(w - 1, -1, -1):
        if frontiere[x] < 0:
            frontiere[x] = suivante
        else:
            suivante = frontiere[x]

    # Les veines du bois creent de faux creux : la frontiere brute est en dents
    # de scie. Une mediane glissante la rend continue, comme la vraie plinthe.
    brute = frontiere.copy()
    lisse = frontiere.copy()
    demi = 12
    for x in range(w):
        if brute[x] < 0:
            continue
        fenetre = brute[max(0, x - demi):x + demi + 1]
        fenetre = fenetre[fenetre >= 0]
        if len(fenetre):
            lisse[x] = int(np.median(fenetre))
    frontiere = lisse

    floor = np.zeros((h, w), bool)
    ys = np.arange(h)[:, None]
    valide = frontiere >= 0
    floor[:, valide] = m[:, valide] & (ys > frontiere[None, valide])
    floor[:, ~valide] = m[:, ~valide]
    walls = m & ~floor
    return floor, walls


def extraire(a: np.ndarray, masque: np.ndarray) -> np.ndarray:
    out = np.zeros_like(a)
    out[masque] = a[masque]
    out[..., 3] = np.where(masque, 255, 0)
    return out


def separer_ombres(socle_avant: np.ndarray, socle_apres: np.ndarray) -> np.ndarray:
    """Isole les ombres : pixels du socle assombris par la pose des meubles."""
    d = socle_avant[..., :3].astype(int) - socle_apres[..., :3].astype(int)
    m = (d.sum(2) > 12) & (socle_apres[..., 3] > 0)
    return extraire(socle_apres, m)


def controler(a: np.ndarray) -> dict:
    al = a[..., 3]
    m = al > 0
    h, w = al.shape
    tuiles = []
    for ty in range(0, h, TILE):
        for tx in range(0, w, TILE):
            t = a[ty:ty + TILE, tx:tx + TILE].reshape(-1, 4)
            c = {tuple(int(v) for v in p[:3]) for p in t if p[3] > 0}
            if c:
                tuiles.append(len(c))
    tuiles = np.array(tuiles) if tuiles else np.array([0])
    return {
        "cellules_occupees": int(len(tuiles)),
        "couleurs": int(len(np.unique(a[m][:, :3], axis=0))) if m.any() else 0,
        "moy_par_tuile": round(float(tuiles.mean()), 1),
        "pct_tuiles_conformes": round(float((tuiles <= 16).mean() * 100), 1),
        "semi_transparents": int(((al > 0) & (al < 255)).sum()),
        "occupation_pct": round(float(m.mean() * 100), 2),
    }


def traiter(cfg: dict) -> dict:
    base = RACINE / cfg["dossier"]
    sortie = base / cfg["sortie"]
    sortie.mkdir(parents=True, exist_ok=True)
    manifeste = {"zone": cfg["zone"], "tile_px": TILE, "moments": {}}

    for moment in ("jour", "nuit"):
        socle = np.array(Image.open(base / cfg["socle"].format(m=moment)).convert("RGBA"))
        deco = np.array(Image.open(base / cfg["deco"].format(m=moment)).convert("RGBA"))

        floor_m, walls_m = separer_sol_parois(socle)
        couches: dict[str, np.ndarray] = {
            "Floor": extraire(socle, floor_m),
            "Walls": extraire(socle, walls_m),
        }

        # Le calque de deco contient a la fois les meubles et les ombres qu'on
        # a peintes dans le sol. On les separe : une ombre est un pixel dont la
        # teinte reste celle du sol, mais assombrie.
        dm = deco[..., 3] > 0
        socle_rgb = socle[..., :3].astype(int)
        deco_rgb = deco[..., :3].astype(int)
        ecart = socle_rgb - deco_rgb
        ombre_m = dm & (ecart.sum(2) > 12) & (ecart.min(2) >= -6) & (socle[..., 3] > 0)
        objets_m = dm & ~ombre_m

        couches["Shadows"] = extraire(deco, ombre_m)

        # Les objets suspendus (guirlandes, bandeau de rideaux) partent en
        # Objects_Over ; le mobilier pose au sol reste en Objects.
        ys = np.arange(deco.shape[0])[:, None].repeat(deco.shape[1], 1)
        haut_m = objets_m & (ys < cfg["y_suspendu"])
        couches["Objects_Over"] = extraire(deco, haut_m)
        couches["Objects"] = extraire(deco, objets_m & ~haut_m)

        infos = {}
        for nom, img in couches.items():
            if (img[..., 3] > 0).sum() == 0:
                continue
            fichier = f"{cfg['zone']}_{nom}_{moment}.png"
            Image.fromarray(img, "RGBA").save(sortie / fichier)
            infos[nom] = {"fichier": fichier, "Layer": PROFONDEUR[nom], **controler(img)}
        manifeste["moments"][moment] = infos

        # verification : rempiler les layers doit redonner la salle decoree
        ordre = ["Floor", "Walls", "Shadows", "Objects", "Objects_Over"]
        comp = Image.new("RGBA", (socle.shape[1], socle.shape[0]), (0, 0, 0, 0))
        for nom in ordre:
            if nom in couches:
                comp.alpha_composite(Image.fromarray(couches[nom], "RGBA"))
        ref = Image.open(base / cfg["socle"].replace("sans_deco", "avec_deco").format(m=moment)).convert("RGBA")
        ecart_px = float((np.abs(np.array(comp).astype(int) - np.array(ref).astype(int)).sum(2) > 0).mean() * 100)
        manifeste["moments"][moment]["_recomposition_ecart_pct"] = round(ecart_px, 3)

    (sortie / f"{cfg['zone']}_layers.json").write_text(json.dumps(manifeste, indent=2))
    return manifeste


def main() -> None:
    for cfg in ZONES:
        man = traiter(cfg)
        print(f"\n=== {man['zone']} ===")
        for moment, infos in man["moments"].items():
            print(f"  [{moment}] recomposition : ecart {infos['_recomposition_ecart_pct']}%")
            print(f"    {'layer':<16}{'Layer':>6}{'cellules':>10}{'coul':>7}"
                  f"{'moy/tui':>9}{'<=16':>8}{'semi':>6}{'occup':>8}")
            for nom, d in infos.items():
                if nom.startswith("_"):
                    continue
                print(f"    {nom:<16}{d['Layer']:>6}{d['cellules_occupees']:>10}"
                      f"{d['couleurs']:>7}{d['moy_par_tuile']:>9}"
                      f"{d['pct_tuiles_conformes']:>7}%{d['semi_transparents']:>6}"
                      f"{d['occupation_pct']:>7}%")


if __name__ == "__main__":
    main()
