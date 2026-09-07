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

def table_depuis_rampe(rampe, longueurs=(3, 4, 6, 4), duree=6, amplitude=1,
                       ondes=2, depuis=0):
    """
    Construit une table DPLA pour une nappe de liquide.

    Trois propriétés du format sont reproduites, et ce sont elles qui font le
    rendu du jeu :

    1. **la variation est locale.** Chaque emplacement oscille autour de sa
       propre couleur, de plus ou moins `amplitude` crans dans la rampe. Un
       premier essai faisait parcourir la rampe entière à chaque emplacement :
       les pixels sombres devenaient clairs et inversement, et la nappe
       clignotait au lieu de miroiter.
    2. **chaque emplacement a son propre nombre d'images** — le champ
       NbColors, qui est bien par entrée et non global. Les cycles n'ont donc
       pas la même longueur et se déphasent en permanence.
    3. les emplacements voisins sont décalés en phase, ce qui fait **voyager**
       les reflets le long du dégradé au lieu de les faire battre ensemble.

    Les longueurs par défaut (3, 4, 6, 4) ont un PPCM de 12 : la nappe ne se
    répète qu'au bout de douze pas alors qu'aucun emplacement ne compte plus
    de six images.

    `amplitude` et `ondes` ont été réglés en mesurant la luminance moyenne de
    la nappe image par image : à amplitude 1 et deux ondes le long de la rampe,
    l'écart-type tombe à 9 contre 16 pour une amplitude de 2. Autrement dit la
    nappe miroite sans battre globalement du clair au sombre.
    """
    import math
    n = len(rampe)
    if n < 2:
        return Dpla()
    emplacements = []
    for i in range(COULEURS_PAR_PALETTE):
        # `depuis` laisse fixes les premiers crans de la rampe. C'est ce qui
        # permet d'animer la seule lueur d'un brasier ou d'un cristal : la
        # pierre qui le porte appartient à une palette non animée, comme dans
        # les jeux d'origine.
        if i >= n or i < depuis:
            emplacements.append({"images": [], "duree": 1})
            continue
        lg = longueurs[i % len(longueurs)]
        phase = ondes * i / max(n - 1, 1)
        images = []
        for k in range(lg):
            d = amplitude * math.sin(2 * math.pi * (k / lg + phase))
            j = min(n - 1, max(0, i + int(round(d))))
            images.append(tuple(rampe[j]))
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
