"""
dtef_kit.py — fabrication d'un jeu de tuiles au format DTEF, à partir de
textures de base, et pose par autotuilage selon la méthode d'Explorers of Sky.

Le format
---------
Un jeu de tuiles de donjon PMD décrit **trois types de terrain** — mur,
secondaire (eau ou lave), sol — et, pour chacun, la manière dont la tuile se
raccorde à ses huit voisines. Cela fait 256 configurations, que le format
réduit à **47 règles de base** ; les 209 autres s'y ramènent.

La réduction est simple et exacte : un bit diagonal ne compte que si les deux
bits cardinaux qui l'encadrent sont posés. Un coin nord-ouest n'existe que si
le nord *et* l'ouest sont du même type.

La planche `tileset_0.png` empile les trois sections dans l'ordre imposé —
mur, secondaire, sol — chacune sur une grille de 6 × 8 tuiles.

Ce module ne recopie aucun pixel du jeu : il construit les 47 tuiles à partir
de textures de base, en dessinant lui-même bordures, biseaux et coins
rentrants selon la règle.
"""

from __future__ import annotations

import json
import os
import numpy as np
from PIL import Image

T = 24
COLS, LIGNES = 6, 8
TYPES = ("mur", "secondaire", "sol")     # ordre imposé par le format

# bits de voisinage
S, SE, E, NE, N, NW, W, SW = 0x01, 0x02, 0x04, 0x08, 0x10, 0x20, 0x40, 0x80
CARDINAUX = {"n": N, "e": E, "s": S, "o": W}
DIAGONALES = {"no": (NW, N, W), "ne": (NE, N, E),
              "se": (SE, S, E), "so": (SW, S, W)}

ICI = os.path.dirname(os.path.abspath(__file__))
REGLES = json.load(open(os.path.join(ICI, "regles_47.json")))


def reduire(regle: int) -> int:
    """Ramène une des 256 configurations à sa règle de base."""
    r = regle
    for bit, (a, b) in ((NW, (N, W)), (NE, (N, E)), (SE, (S, E)), (SW, (S, W))):
        if r & bit and not (r & a and r & b):
            r &= ~bit
    return r


TABLE = {}
for _i, _r in enumerate(REGLES):
    if _r is not None:
        TABLE[_r] = _i


def index_regle(regle: int) -> int:
    """Position dans la grille 6 x 8 pour une configuration quelconque."""
    return TABLE.get(reduire(regle), TABLE.get(0, 10))


# --------------------------------------------------------------------------
# Construction des 47 tuiles d'un type
# --------------------------------------------------------------------------

def _echantillon(texture, x, y):
    """Motif répété : la texture est lue en boucle, la tuile reste raccordable."""
    w, h = texture.size
    return texture.crop((0, 0, w, h)).resize((T, T), Image.NEAREST) if (w, h) != (T, T) \
        else texture


def _tuile_texture(texture, tx, ty):
    """Découpe de 24 px prise dans la texture, en coordonnées cycliques."""
    a = np.asarray(texture.convert("RGB"))
    h, w = a.shape[:2]
    ys = [(ty * T + i) % h for i in range(T)]
    xs = [(tx * T + i) % w for i in range(T)]
    return Image.fromarray(a[np.ix_(ys, xs)], "RGB")


def construire_type(corps, bordure_claire, bordure_sombre, regles=REGLES,
                    face=None, epaisseur=3, graine=0):
    """
    Fabrique la section 6 x 8 d'un type de terrain.

    Pour chaque règle : le corps est posé, puis chaque côté dont le voisin est
    d'un autre type reçoit un liseré, et chaque coin diagonal manquant reçoit
    une encoche. Si `face` est fourni, le bord sud reçoit en plus une face
    verticale — c'est ce qui donne aux murs leur relief dans les donjons.
    """
    rng = np.random.default_rng(graine)
    planche = Image.new("RGBA", (COLS * T, LIGNES * T), (0, 0, 0, 0))
    for i, regle in enumerate(regles):
        if regle is None:
            continue
        cx, cy = (i % COLS) * T, (i // COLS) * T
        t = np.array(_tuile_texture(corps, int(rng.integers(0, 5)),
                                    int(rng.integers(0, 5))).convert("RGBA"))

        cl = np.array(bordure_claire, dtype=np.float32)
        so = np.array(bordure_sombre, dtype=np.float32)
        e = epaisseur

        # liserés sur les côtés ouverts
        if not regle & N:
            t[:e, :, :3] = (t[:e, :, :3] * 0.35 + cl * 0.65)
        if not regle & S:
            t[-e:, :, :3] = (t[-e:, :, :3] * 0.35 + so * 0.65)
        if not regle & W:
            t[:, :e, :3] = (t[:, :e, :3] * 0.40 + cl * 0.60)
        if not regle & E:
            t[:, -e:, :3] = (t[:, -e:, :3] * 0.40 + so * 0.60)

        # encoches de coin : le voisin diagonal manque alors que les deux
        # cardinaux sont présents
        for nom, (bit, a, b) in DIAGONALES.items():
            if regle & a and regle & b and not regle & bit:
                yy = slice(0, e) if "n" in nom else slice(T - e, T)
                xx = slice(0, e) if "o" in nom else slice(T - e, T)
                coul = cl if "n" in nom else so
                t[yy, xx, :3] = (t[yy, xx, :3] * 0.30 + coul * 0.70)

        # face verticale sous un bord sud ouvert
        if face is not None and not regle & S:
            hf = min(T // 2, 10)
            f = np.array(_tuile_texture(face, int(rng.integers(0, 4)), 0)
                         .convert("RGBA"))[:hf]
            t[T - hf:, :, :3] = f[:, :, :3]
            t[T - hf:T - hf + 1, :, :3] = (t[T - hf:T - hf + 1, :, :3] * 0.2
                                           + np.array(so) * 0.8)

        planche.paste(Image.fromarray(t, "RGBA"), (cx, cy))
    return planche


def assembler(sections):
    """Empile mur, secondaire et sol dans l'ordre imposé par le format."""
    out = Image.new("RGBA", (COLS * T, LIGNES * T * 3), (0, 0, 0, 0))
    for i, nom in enumerate(TYPES):
        out.paste(sections[nom], (0, i * LIGNES * T))
    return out


def tuile_pour(planche, type_idx, regle):
    """Extrait la tuile correspondant à une configuration donnée."""
    i = index_regle(regle)
    x, y = (i % COLS) * T, (i // COLS) * T + type_idx * LIGNES * T
    return planche.crop((x, y, x + T, y + T))


# --------------------------------------------------------------------------
# XML DTEF
# --------------------------------------------------------------------------

def ecrire_xml(chemin, animations=None):
    """
    Fichier `tileset.dtef.xml`. `animations` est une liste de
    (numero_palette, [ [ (r,g,b) x16 ] par image ], [durees x16]).
    """
    L = ['<?xml version="1.0" encoding="UTF-8"?>',
         f'<DungeonTileset dimensions="{T}">']
    for pal, images, durees in (animations or []):
        L.append(f' <Animation palette="{pal}">')
        for k, couleurs in enumerate(images):
            L.append('  <Frame>')
            for j, c in enumerate(couleurs):
                d = f' duration="{durees[j]}"' if k == 0 else ''
                L.append(f'   <Color{d}>%02x%02x%02x</Color>' % tuple(c))
            L.append('  </Frame>')
        L.append(' </Animation>')
    L.append('</DungeonTileset>')
    open(chemin, "w").write("\n".join(L) + "\n")
