"""Composition du nouveau layout « Plage — Beach Cave, grande » (lot plage_beach_cave_v1).

Tout est exprimé en cellules de 24 px de la carte EoSO `beach` (33 x 16).
La nouvelle carte (45 x 20) est un ré-assemblage cellule par cellule :
chaque cellule copie la séquence d'images (1 ou 17 frames) d'une cellule
source, octet pour octet. Aucune image n'est redessinée, recolorée ou
redimensionnée. Voir SPEC.md pour la composition et ANALYSE.md pour les
mesures de raccord qui justifient les blocs choisis.
"""
from __future__ import annotations

ORIG_W, ORIG_H = 33, 16

# ---- largeur : 33 -> 45 colonnes ------------------------------------------
# Le bloc de colonnes [11, 23) (12 colonnes de mer/sable purs, sans rocher
# côtier) est inséré une fois après la colonne 22. Raccord mesuré 22 -> 11 :
# 203.7 (MSE 17 frames), inférieur au raccord médian des colonnes d'origine
# (318). Le module de rochers du bas coupé à la colonne 22 se termine par la
# colonne 11 (« 0,4,2 | 3 »), qui est sa suite naturelle.
INSERT_A, INSERT_B = 11, 23
COLMAP = list(range(0, INSERT_B)) + list(range(INSERT_A, INSERT_B)) + list(range(INSERT_B, ORIG_W))
NEW_W = len(COLMAP)  # 45

# ---- hauteur : 16 -> 20 rangées --------------------------------------------
# Quatre rangées de sable sont insérées entre les rangées 9 et 10 d'origine.
# Calque Back (sable) : séquence 8, 9, 9, 9, 9, 9 pour toutes les colonnes
# (raccords 12 / 92 x4 / 23, tous sous le raccord 7 -> 8 d'origine = 107 ;
# les alternances 8,9,8,9 coûtent 186 et créent des marches visibles sur la
# bande claire du chemin de droite).
BACK_ROWS = list(range(0, 8)) + [8, 9, 9, 9, 9, 9] + list(range(10, ORIG_H))
# Calques Front ET Back des colonnes latérales : la cellule répétée est celle
# dont le bord (alpha compris) se raccorde le mieux à elle-même.
# Gauche (mur + rampe de gravier) : rangée 8 répétée, rangée 9 (rétrécissement)
# en dernier — raccord 8/8 de la colonne 3 : 1231 contre 10994 pour 9/9.
LEFT_ROWS = list(range(0, 8)) + [8, 8, 8, 8, 8, 9] + list(range(10, ORIG_H))
# Droite (chemin de sortie) : rangée 9 répétée — raccord 9/9 de la colonne 30 :
# 16762 contre 30818 pour 8/8 ; même séquence que le sable, donc aucune paire
# nouvelle entre le chemin et le sable clair (colonnes 26-29).
RIGHT_ROWS = BACK_ROWS
SIDE_FRONT_ROWS = LEFT_ROWS  # compatibilité
# Calque Front, colonnes de sable : rangées 8 et 9 d'origine puis cellules
# vides ; les détails (cailloux, buisson) sont replacés explicitement (PROPS).
MID_FRONT_ROWS = list(range(0, 8)) + [8, 9, None, None, None, None] + list(range(10, ORIG_H))
NEW_H = len(BACK_ROWS)  # 20
assert len(LEFT_ROWS) == len(RIGHT_ROWS) == len(MID_FRONT_ROWS) == NEW_H

LEFT_SIDE_COLS = set(range(0, 6))      # colonnes source 0-5 : mur, grotte, rampe
RIGHT_SIDE_COLS = set(range(30, 33))   # colonnes source 30-32 : chemin de sortie


def is_side(source_col: int) -> bool:
    return source_col in LEFT_SIDE_COLS or source_col in RIGHT_SIDE_COLS


def side_rows(source_col: int) -> list[int]:
    return LEFT_ROWS if source_col in LEFT_SIDE_COLS else RIGHT_ROWS


def front_rows(source_col: int) -> list[int | None]:
    return side_rows(source_col) if is_side(source_col) else MID_FRONT_ROWS


# Le sable sous la rampe (colonne 4, Front couvrant 71 % / 19 %) et sous le
# chemin (colonne 30, 31 % / 78 %) reste visible : dans les colonnes latérales
# le calque Back suit la même séquence que Front, pour que chaque cellule Back
# garde la cellule Front d'origine au-dessus d'elle.
def back_rows(source_col: int) -> list[int]:
    return side_rows(source_col) if is_side(source_col) else BACK_ROWS


ANIM_ROWS = BACK_ROWS  # la mer occupe les rangées 0-6, identiques dans toutes les séquences


# Les obstacles (grille 8 px, 3 x 3 par cellule) suivent le calque Front :
# ce sont les rochers, le mur, la rampe et le chemin qui portent la collision ;
# le sable inséré est libre.
def obstacle_rows(source_col: int) -> list[int | None]:
    return front_rows(source_col)


# ---- détails du sable (coordonnées NOUVELLE carte) --------------------------
# Le calque Back porte les ombres cuites des détails posés dessus (cailloux,
# buisson) : un détail se déplace donc avec ses cellules d'ombre, et une
# cellule d'ombre orpheline est remplacée par la cellule de sable propre de
# même phase (le motif du sable a une période de 8 colonnes ; la cellule
# propre est celle située 8 colonnes plus loin sur la même rangée d'origine,
# sans détail au-dessus dans la carte d'origine).
#
# Caillou isolé : Front (18,9) ; ombre Back (18,9)+(19,9) ; sable propre (10,9)+(11,9).
# Paire de cailloux : Front (12,7)+(13,7) ; ombre Back (12,7)+(13,7) ; propre (20,7)+(21,7).
CLEAN_9 = [(10, 9), (11, 9)]
SHADOW_9 = [(18, 9), (19, 9)]
BACK_OVERRIDES: list[tuple[tuple[int, int], tuple[int, int]]] = []
# 1. rangée 9 répétée (nouvelles rangées 10-13) : pas d'ombre sans caillou,
#    dans la colonne d'origine (X=18-19) et dans sa copie (X=30-31).
for Y in range(10, 14):
    for X0 in (18, 30):
        BACK_OVERRIDES += [(CLEAN_9[0], (X0, Y)), (CLEAN_9[1], (X0 + 1, Y))]
# 2. copies mécaniques du bloc de colonnes : caillou (30,9) et paire (24-25,7)
#    retirés avec leurs ombres.
FRONT_REMOVE = [(24, 7), (25, 7), (30, 9)]
BACK_OVERRIDES += [((20, 7), (24, 7)), ((21, 7), (25, 7)), (CLEAN_9[0], (30, 9)), (CLEAN_9[1], (31, 9))]
# 3. trois cailloux isolés replacés avec leur ombre, sur des cellules de même
#    phase (rangée d'origine 9, colonne d'origine = 18 ou 26 mod 8 = 2).
FRONT_PLACE = [((18, 9), (10, 12)), ((18, 9), (30, 12)), ((18, 9), (38, 10))]
for (_, (X, Y)) in FRONT_PLACE:
    BACK_OVERRIDES += [(SHADOW_9[0], (X, Y)), (SHADOW_9[1], (X + 1, Y))]

# ---- entités (pixels, nouvelle carte) --------------------------------------
COL_SHIFT_RIGHT = (INSERT_B - INSERT_A) * 24   # +288 px pour tout ce qui est à droite du bloc
ENTRANCE_MARKER = {'X': 748 + COL_SHIFT_RIGHT, 'Y': 208, 'Width': 16, 'Height': 16, 'Direction': 2}
# Sortie : bord droit ; le couloir libre d'origine (y 168-240) est prolongé
# par les rangées insérées (8 px : 5 rangées x 3 = +96 px -> y 168-336).
EXIT_OBJECT = {'X': 782 + COL_SHIFT_RIGHT, 'Y': 172, 'Width': 16, 'Height': 78 + 96}
CAVE_OBJECT = {'X': 8, 'Y': 144, 'Width': 64, 'Height': 64}   # inchangé (rangées 6-8)

ASSET = 'plage_bc1_grande_jour'
TITLE = 'Plage — Beach Cave (grande)'
NAMESPACE = 'plage_beach_cave_v1'
