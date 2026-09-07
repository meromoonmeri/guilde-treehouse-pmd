"""
dpla.py — animation de palette au format DPLA, celui de Chunsoft.

Comment PMD anime réellement l'eau
----------------------------------
Le format est documenté par l'implémentation de SkyTemple
(`skytemple_files/graphics/dpla/_model.py`, GPLv3). Les points qui comptent :

* Un jeu de tuiles de donjon possède 16 palettes de 16 couleurs. **Seules deux
  d'entre elles sont animées**, aux indices 10 et 11. Tout le reste est fixe.
* Le fichier DPLA contient jusqu'à 32 entrées, une par emplacement de couleur :
  les 16 premières alimentent la palette 10, les 16 suivantes la palette 11.
* Chaque entrée porte **sa propre liste d'images et sa propre durée**. La
  couleur affichée vaut `frames[frame_id % len(frames)]`.
* Rien ne bouge dans les pixels : ce sont les valeurs RVB des emplacements qui
  sont **remplacées** image après image.

La conséquence est essentielle et c'est elle qui donne le rendu si
caractéristique : les emplacements n'ayant ni le même nombre d'images ni la
même durée, ils se désynchronisent. Le miroitement n'est pas un cycle unique
mais la superposition de plusieurs cycles de longueurs différentes, et la
période visible est leur plus petit commun multiple.

Une simple rotation d'indices dans la palette — l'approximation courante —
produit un défilement régulier et mécanique. Ce n'est pas ce que fait le jeu.
"""

from __future__ import annotations

import json
from math import gcd

COULEURS_PAR_PALETTE = 16
MAX_COULEURS = 32
PALETTES_ANIMEES = (10, 11)          # indices imposés par le format


def _ppcm(valeurs):
    r = 1
    for v in valeurs:
        v = max(1, int(v))
        r = r * v // gcd(r, v)
    return r


class Dpla:
    """
    Table d'animation de palette.

    emplacements : liste de 0 à 32 entrées, chacune étant
        {"images": [(r, g, b), …], "duree": int}
    Une entrée vide signifie « emplacement non animé ».
    """

    def __init__(self, emplacements=None):
        self.emplacements = list(emplacements or [])
        if len(self.emplacements) > MAX_COULEURS:
            self.emplacements = self.emplacements[:MAX_COULEURS]

    # -- lecture ------------------------------------------------------------

    def anime(self, idx_palette: int) -> bool:
        d = idx_palette * COULEURS_PAR_PALETTE
        return (len(self.emplacements) > d
                and bool(self.emplacements[d].get("images")))

    def palette_a_l_image(self, idx_palette: int, tic: int):
        """
        Les 16 couleurs de cette palette au tic donné, exprimé en images de
        jeu. Chaque emplacement avance à son propre rythme : il change de
        couleur tous les `duree` tics et boucle sur sa propre longueur.
        """
        d = idx_palette * COULEURS_PAR_PALETTE
        bloc = self.emplacements[d:d + COULEURS_PAR_PALETTE]
        sortie = []
        for e in bloc:
            im = e.get("images") or [(0, 0, 0)]
            duree = max(1, int(e.get("duree", 1)))
            sortie.append(im[(tic // duree) % len(im)])
        while len(sortie) < COULEURS_PAR_PALETTE:
            sortie.append((0, 0, 0))
        return sortie

    def periode(self, idx_palette: int) -> int:
        """
        Nombre d'images avant que la palette ne se répète : plus petit commun
        multiple des longueurs de cycle, pondéré par les durées.
        """
        d = idx_palette * COULEURS_PAR_PALETTE
        bloc = self.emplacements[d:d + COULEURS_PAR_PALETTE]
        longueurs = [len(e["images"]) * max(1, e.get("duree", 1))
                     for e in bloc if e.get("images")]
        return _ppcm(longueurs) if longueurs else 1

    def appliquer(self, palettes, image: int):
        """Copie de `palettes` avec les deux palettes animées substituées."""
        neuf = [list(p) for p in palettes]
        for i, cible in enumerate(PALETTES_ANIMEES):
            if self.anime(i) and cible < len(neuf):
                neuf[cible] = self.palette_a_l_image(i, image)
        return neuf

    # -- écriture -----------------------------------------------------------

    def vers_dict(self):
        return {
            "format": "DPLA — animation de palette de donjon PMD",
            "reference": "SkyTemple, skytemple_files/graphics/dpla",
            "palettes_animees": list(PALETTES_ANIMEES),
            "couleurs_par_palette": COULEURS_PAR_PALETTE,
            "principe": ("chaque emplacement de couleur possède sa propre "
                         "liste d'images et sa propre durée ; la couleur "
                         "affichée vaut images[n % len(images)]"),
            "emplacements": [
                {"images": ["#%02X%02X%02X" % tuple(c) for c in e.get("images", [])],
                 "duree": e.get("duree", 1)}
                for e in self.emplacements],
        }

    def ecrire_json(self, chemin):
        json.dump(self.vers_dict(), open(chemin, "w"), indent=1, ensure_ascii=False)


# --------------------------------------------------------------------------
# Fabrication d'une table à partir d'une rampe de couleurs réelle
# --------------------------------------------------------------------------

def table_depuis_rampe(rampe, longueurs=(3, 4, 6, 4), duree=6, sens=1):
    """
    Construit une table DPLA pour une nappe de liquide.

    `rampe` est la suite des couleurs du liquide, du plus sombre au plus clair,
    relevée sur les tuiles du jeu.

    Deux propriétés du format sont reproduites, et ce sont elles qui font le
    rendu :

    1. l'emplacement *i* parcourt la rampe **en partant de sa propre
       position**, si bien que les teintes voyagent le long du dégradé au lieu
       de clignoter sur place ;
    2. chaque emplacement reçoit **son propre nombre d'images** — le champ
       NbColors du format, qui est bien par entrée et non global. Les cycles
       n'ont donc pas la même longueur et se déphasent continuellement.

    Les longueurs par défaut (3, 4, 6, 4) ont un PPCM de 12 : le miroitement
    ne se répète qu'au bout de douze pas, alors qu'aucun emplacement ne compte
    plus de six images.
    """
    n = len(rampe)
    if n < 2:
        return Dpla()
    emplacements = []
    for i in range(COULEURS_PAR_PALETTE):
        if i >= n:
            emplacements.append({"images": [], "duree": 1})
            continue
        lg = longueurs[i % len(longueurs)]
        images = [tuple(rampe[(i + sens * round(k * n / lg)) % n])
                  for k in range(lg)]
        emplacements.append({"images": images, "duree": int(duree)})
    return Dpla(emplacements)


def rampe_depuis_tuiles(tuiles, n_couleurs=12):
    """Relève la rampe de couleurs d'un lot de tuiles, triée par luminance."""
    from PIL import Image
    import numpy as np
    if not tuiles:
        return []
    larg = sum(t.size[0] for t in tuiles)
    haut = max(t.size[1] for t in tuiles)
    planche = Image.new("RGB", (larg, haut))
    x = 0
    for t in tuiles:
        planche.paste(t.convert("RGB"), (x, 0))
        x += t.size[0]
    q = planche.quantize(colors=n_couleurs, method=Image.Quantize.MAXCOVERAGE,
                         dither=Image.Dither.NONE)
    pal = q.getpalette()[: n_couleurs * 3]
    couleurs = [tuple(pal[i * 3:i * 3 + 3]) for i in range(n_couleurs)]
    utilisees = {i for i in q.getdata()}
    couleurs = [c for i, c in enumerate(couleurs) if i in utilisees]
    couleurs.sort(key=lambda c: 0.2126 * c[0] + 0.7152 * c[1] + 0.0722 * c[2])
    return couleurs
