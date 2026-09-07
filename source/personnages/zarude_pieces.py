#!/usr/bin/env python3
"""Zarude #0893 — pièces de pixel art dessinées à l'échelle 1:1 pour le sprite PMD.

Chaque pièce est un bitmap ASCII (une lettre = une couleur de la palette, « . » = transparent).
Les cinq orientations dessinées sont Bas (0), Bas-droite (1), Droite (2), Haut-droite (3) et
Haut (4) ; Gauche, Haut-gauche et Bas-gauche sont obtenues par miroir dans le constructeur
(`build_zarude_sprite.py`), comme le font les sprites officiels (dir 6 = miroir de dir 2).

Convention : les pièces sont posées par leur coin haut-gauche, en coordonnées relatives à l'ancre
du sprite (point du sol sous le centre du corps = pixel blanc de la feuille Shadow), x vers la
droite, y vers le bas. Les pièces de face ont une largeur impaire pour être centrées sur la
colonne de l'ancre. Les points nommés (`*_FIST`) donnent la position du poing dans la pièce,
utilisée pour les repères mains de la feuille Offsets.

Palette : 13 couleurs opaques, fixées une fois pour toutes (limite SpriteCollab : 15).
"""
from __future__ import annotations

import numpy as np

PALETTE = {
    "#": (0, 0, 0),         # contour
    "d": (40, 38, 46),      # pelage sombre
    "b": (68, 64, 74),      # pelage
    "h": (98, 94, 106),     # pelage éclairé
    "n": (54, 48, 60),      # crinière
    "g": (142, 142, 150),   # gris : museau, griffes, plastron ombré
    "G": (198, 198, 206),   # gris clair : masque, plastron
    "W": (255, 255, 255),   # crocs, reflets, griffures
    "R": (206, 42, 42),     # œil
    "O": (240, 140, 48),    # iris
    "v": (40, 100, 56),     # liane sombre
    "V": (78, 152, 76),     # liane
    "L": (132, 198, 96),    # liane éclairée
}
DARKER = {"h": "b", "b": "d", "L": "V", "V": "v", "G": "g", "g": "h"}   # membres du côté opposé au spectateur


def bmp(rows: list[str]) -> np.ndarray:
    rows = [r for r in rows if r]
    h, w = len(rows), max(len(r) for r in rows)
    a = np.zeros((h, w, 4), np.uint8)
    for y, r in enumerate(rows):
        for x, ch in enumerate(r):
            if ch not in ". ":
                a[y, x] = (*PALETTE[ch], 255)
    return a


def flip(a: np.ndarray) -> np.ndarray:
    return np.ascontiguousarray(a[:, ::-1])


def darker(a: np.ndarray) -> np.ndarray:
    """Même pièce, teintes rabattues d'un cran (membre éloigné du spectateur)."""
    out = a.copy()
    table = {PALETTE[k]: PALETTE[v] for k, v in DARKER.items()}
    for y, x in np.argwhere(out[:, :, 3] > 0):
        c = tuple(int(v) for v in out[y, x, :3])
        if c in table:
            out[y, x, :3] = table[c]
    return out


def shorten(a: np.ndarray, n: int, keep_top: int = 1) -> np.ndarray:
    """Retire n lignes sous les `keep_top` premières : membre plié, le bas (poing, pied) reste en place."""
    rows = [r for r in range(a.shape[0]) if not (keep_top <= r < keep_top + n)]
    return np.ascontiguousarray(a[rows])


# =====================================================================================
# BAS (0) — de face
# =====================================================================================
HEAD_0 = bmp([
    "#.......................#",
    "##.....................##",
    "#d#...................#d#",
    "#dd#.................#dd#",
    "#ddb#......###......#bdd#",
    "#ddbb####bbbbbbb####bbdd#",
    ".#dbbbbbbbbbbbbbbbbbbbd#.",
    ".#bbGGGGbbbbbbbbbGGGGbb#.",
    "..#GGRRRGGbbbbbGGRRRGG#..",
    "..#GGRO#RGbbbbbGR#ORGG#..",
    "..#bGGGGGGGbbbGGGGGGGb#..",
    "...#bbGGGGGGGGGGGGGbb#...",
    "...#bbbbGGggggggGGbbb#...",
    "....##bbGgW#g#WgGbb##....",
    "......##ggg#g#ggg##......",
    "........#ggggggg#........",
    ".........#######.........",
])
HEAD_0_MARK = (12, 11)
MANE_0 = bmp([
    "#......#...........#......#",
    "#n#...#n#.........#n#...#n#",
    "#nn#.#nn#.........#nn#.#nn#",
    ".#nn##nnn#.......#nnn##nn#.",
    "..#Vnnnnnn#######nnnnnnV#..",
    "...#VnnnnnnnnnnnnnnnnnV#...",
    "....##nnnnnnnnnnnnnnn##....",
    "......##nnnnnnnnnnn##......",
    "........###########........",
])
TORSO_0 = bmp([
    "..#########..",
    ".#hhbbbbbbb#.",
    "#hhbGGGGGbbb#",
    "#hbGGgGgGGbb#",
    "#hbGGGGGGGbb#",
    "#bbGgGgGgGbb#",
    "#bbGGGGGGGbb#",
    "#bbbGgGgGbbb#",
    "#bbbbGGGbbbd#",
    "#dbbbbbbbbdd#",
    ".#dbbbbbbdd#.",
    ".#ddbbbbddd#.",
    "..#dddddd#...",
])
TORSO_0_CENTER = (6, 7)
# bras gauche (côté gauche de l'écran) : épaule en haut à droite, poing au sol en bas à gauche
ARM_0 = bmp([
    ".....####.",
    "....#hbbd#",
    "....#hbbd#",
    "...#hhbbd#",
    "...#hbbd#.",
    "...#hbbd#.",
    "..#hhbbd#.",
    "..#hbbd#..",
    "..#hbbd#..",
    ".#hhbbd#..",
    ".#hbbd#...",
    ".#LVVv#...",
    ".#VvVL#...",
    ".#LVVv#...",
    ".#vVvV#...",
    "#hbbbd#...",
    "#hbbbbd#..",
    "#bbbbbd#..",
    ".#g#g#g#..",
])
ARM_0_FIST = (3, 16)
ARM_0_SHOULDER = (7, 0)
# bras levé au-dessus de la tête (charge de l'attaque, hurlement) : épaule en bas à droite
ARM_UP_0 = bmp([
    ".#g#g#g#..",
    "#bbbbbd#..",
    "#hbbbbd#..",
    "#hbbbd#...",
    ".#vVvV#...",
    ".#LVVv#...",
    ".#VvVL#...",
    ".#LVVv#...",
    ".#hbbd#...",
    ".#hhbbd#..",
    "..#hbbd#..",
    "..#hbbd#..",
    "..#hhbbd#.",
    "...#hbbd#.",
    "...#hbbd#.",
    "...#hhbbd#",
    "....#hbbd#",
    "....#hbbd#",
    ".....####.",
])
ARM_UP_0_FIST = (3, 2)
ARM_UP_0_SHOULDER = (7, 18)
# bras tendu sur le côté (coup reçu) : épaule à droite, poing à gauche
ARM_OUT_0 = bmp([
    "..#####......",
    ".#bbbbd#####.",
    "#g#bbbLVLbbbd#",
    "#g#bbbVvVbbbd#",
    "#g#bbbLVLbbbd#",
    ".#bbbdvVvbbdd#",
    "..#####.#####",
])
ARM_OUT_0_FIST = (2, 3)
ARM_OUT_0_SHOULDER = (12, 3)
# bras plié, poing ramené sur le poitrail (Zarude se frappe la poitrine) : épaule en haut à droite
ARM_BEAT_0 = bmp([
    ".....####......",
    "....#hbbd#.....",
    "....#hbbd#..##.",
    "...#hhbbd#.#gg#",
    "...#hbbd##bbbg#",
    "...#hbbLVLbbg#.",
    "..#hhbbVvVbb#..",
    "..#hbbbLVL##...",
    "..#bbbbvVv#....",
    "...#######.....",
])
ARM_BEAT_0_FIST = (12, 3)
ARM_BEAT_0_SHOULDER = (7, 0)
# bras tendu vers le spectateur (Shoot) : raccourci par la perspective, gros poing griffes en avant
ARM_PUSH_0 = bmp([
    ".....####.",
    "....#hbbd#",
    "...#hbbbd#",
    "..#hbbbd#.",
    ".#LVVVd#..",
    ".#VvVLd#..",
    "#hbbbbd#..",
    "#gGgGgd#..",
    "#GgGgGd#..",
    ".#g#g#g#..",
])
ARM_PUSH_0_FIST = (3, 8)
ARM_PUSH_0_SHOULDER = (7, 0)
LEG_0 = bmp([
    "#hbbd#",
    "#hbbd#",
    "#hbbd#",
    "#hbd#.",
    "#hbd#.",
    "#LVv#.",
    "#VvV#.",
    "#hbd#.",
    "#hbd#.",
    "#bbbd#",
    "#GgGd#",
    ".##.#.",
])
TAIL_0 = bmp([
    "....###.",
    "...#ddd#",
    "..#dd#d#",
    "..#d#.##",
    ".#dd#...",
    ".#d#....",
    "#dd#....",
    "#d#.....",
    "##......",
])

# =====================================================================================
# DROITE (2) — profil, le personnage regarde vers la droite
# =====================================================================================
HEAD_2 = bmp([
    "..#.....#...........",
    ".#d#...#d#..........",
    ".#dd#..#dd#.........",
    ".#ddb#.#ddb#........",
    "#dddb#.#ddbb#.......",
    "#ddbbb##bbbbb###....",
    "#dbbbbbbbbbbbbbb##..",
    "#bbbbbbbbbbbGGGGGb#.",
    ".#bbbbbbbbbGGRRRGG#.",
    ".#bbbbbbbbbGRO#RGGg#",
    ".#bbbbbbbbbbGGGGGgg#",
    "..#bbbbbbbbbbGGgggW#",
    "..#dbbbbbbbbbbGggg#.",
    "...#dbbbbbbbbbbb##..",
    "....##ddbbbbbbb#....",
    "......#########.....",
])
HEAD_2_MARK = (13, 8)
MANE_2 = bmp([
    "...#........",
    "#..##...#...",
    "##.#n#.#n#..",
    "#n##nn##nn#.",
    "#nnnnnnnnnn#",
    ".#nnnnnnnnnn",
    "#nnnnnnnnnnn",
    "##nnnnnnnnnn",
    ".##nnnnnnnnn",
    "...#nnnnnnnn",
    "....##nnnnnn",
    "......######",
])
VINES_2 = bmp([
    "..#VL#",
    ".#VLV#",
    ".#vVL#",
    "#VvVL#",
    "#vVvV#",
    "#VvVv#",
    "#vVvV#",
    ".#vVv#",
    ".#VvV#",
    ".#vVv#",
    "..#Vv#",
    "..#v#.",
    "..#v#.",
    "...#..",
])
TORSO_2 = bmp([
    ".....#######...",
    "...##bbbbbbb#..",
    "..#bbbbbbbbbG#.",
    ".#dbbbbbbbbbGg#",
    ".#dbbbbbbbbbGg#",
    "#ddbbbbbbbbbGg#",
    "#ddbbbbbbbbbg#.",
    "#dddbbbbbbbb#..",
    "#dddbbbbbbb#...",
    "#ddddbbbbb#....",
    ".#dddbbbb#.....",
    ".#ddddbb#......",
    "..######.......",
])
TORSO_2_CENTER = (8, 6)
# bras proche : épaule en haut à gauche, poing au sol devant
ARM_2 = bmp([
    ".#####........",
    "#hbbbd#.......",
    "#hbbbd#.......",
    "#hbbbbd#......",
    ".#hbbbd#......",
    ".#hbbbbd#.....",
    "..#hbbbd#.....",
    "..#hbbbbd#....",
    "...#hbbbd#....",
    "...#hbbbbd#...",
    "....#hbbbd#...",
    "....#LVVVv#...",
    "....#VvVvL#...",
    ".....#LVVv#...",
    ".....#vVvV#...",
    ".....#hbbbd#..",
    "......#hbbd#..",
    "......#hbbbd#.",
    "......#hbbbbd#",
    ".....#hbbbbbd#",
    ".....#bbbbbbd#",
    "......#g#g#g#.",
    ".......#.#.#..",
])
ARM_2_FIST = (9, 20)
ARM_2_SHOULDER = (3, 0)
# bras levé devant, au-dessus de la tête : épaule en bas à gauche
ARM_UP_2 = bmp([
    "........#g#g#g#",
    ".......#bbbbbd#",
    ".......#hbbbbd#",
    "......#hbbbd#..",
    "......#vVvV#...",
    ".....#LVVv#....",
    ".....#VvVL#....",
    ".....#LVVv#....",
    "....#hbbd#.....",
    "....#hbbd#.....",
    "...#hbbd#......",
    "...#hbbd#......",
    "..#hbbd#.......",
    "..#hbbd#.......",
    ".#hbbd#........",
    ".#hbbd#........",
    "#hbbbd#........",
    "#hbbbd#........",
    ".#####.........",
])
ARM_UP_2_FIST = (11, 1)
ARM_UP_2_SHOULDER = (3, 18)
# bras tendu devant : épaule à gauche, poing à droite
ARM_OUT_2 = bmp([
    ".......#####....",
    "#####dbbbLVLbbd#",
    "#hbbbbbbbVvVbbd#g",
    "#hbbbbbbbLVLbbd#g",
    ".#####dbbvVvbbd#g",
    ".......#####.###",
])
ARM_OUT_2_FIST = (14, 2)
ARM_OUT_2_SHOULDER = (2, 2)
ARM_PUSH_2, ARM_PUSH_2_FIST, ARM_PUSH_2_SHOULDER = ARM_OUT_2, ARM_OUT_2_FIST, ARM_OUT_2_SHOULDER
# bras plié, poing ramené sur le poitrail
ARM_BEAT_2 = bmp([
    ".#####...",
    "#hbbbd#..",
    "#hbbbd#..",
    "#hbbbd##.",
    ".#hbbbbg#",
    ".#LVLbbg#",
    ".#VvVbb#.",
    ".#LVL##..",
    "..###....",
])
ARM_BEAT_2_FIST = (7, 4)
ARM_BEAT_2_SHOULDER = (3, 0)
LEG_2 = bmp([
    "#hbbd#.",
    "#hbbd#.",
    "#hbbd#.",
    "#hbbd#.",
    "#hbbd#.",
    "#hbbd#.",
    "#hbbd#.",
    "#hbd#..",
    "#LVv#..",
    "#VvV#..",
    "#hbd#..",
    "#hbbd#.",
    "#bbbbd#",
    "#GgGgd#",
    ".##.##.",
])
TAIL_2 = bmp([
    "....###...",
    "...#ddd#..",
    "..#dd#dd#.",
    "..#d#.#d#.",
    "..#d#..##.",
    "..#d#.....",
    "..#dd#....",
    "...#dd#...",
    "....#dd#..",
    ".....#dd#.",
    "......#dd#",
    "......#dd#",
    ".......#d#",
    ".......#d#",
    "........##",
])

# =====================================================================================
# HAUT (4) — de dos
# =====================================================================================
HEAD_4 = bmp([
    "#.......................#",
    "##.....................##",
    "#d#...................#d#",
    "#dd#.................#dd#",
    "#ddb#......###......#bdd#",
    "#ddbb####bbbbbbb####bbdd#",
    ".#dbbbbbbbbbbbbbbbbbbbd#.",
    ".#bbbbbbbbbbbbbbbbbbbbb#.",
    "..#bbbbbbbbbbbbbbbbbbb#..",
    "..#bbbbbbbbbbbbbbbbbbb#..",
    "..#dbbbbbbbbbbbbbbbbbd#..",
    "...#dbbbbbbbbbbbbbbbd#...",
    "...#ddbbbbbbbbbbbbbdd#...",
    "....##dbbbbbbbbbbbd##....",
    "......##ddddddddd##......",
    "........#ddddddd#........",
    ".........#######.........",
])
HEAD_4_MARK = (12, 11)
VINES_4 = bmp([
    "..#VLVLV#..",
    ".#VLVLVLV#.",
    ".#vVLVLVv#.",
    "#VvVLVLVvV#",
    "#vVvVvVvVv#",
    "#VvVvVvVvV#",
    ".#vVvVvVv#.",
    ".#VvVvVvV#.",
    "..#vVvVv#..",
    "..#Vv#Vv#..",
    "...#v#.#v#.",
    "....#...#..",
])
MANE_4 = MANE_0
TORSO_4 = bmp([
    "..#########..",
    ".#hhbbbbbbb#.",
    "#hhbbbbbbbbb#",
    "#hbbbbbbbbbb#",
    "#hbbbbbbbbbb#",
    "#bbbbbbbbbbb#",
    "#bbbbbbbbbbb#",
    "#bbbbbbbbbbb#",
    "#bbbbbbbbbbd#",
    "#dbbbbbbbbdd#",
    ".#dbbbbbbdd#.",
    ".#ddbbbbddd#.",
    "..#dddddd#...",
])
TORSO_4_CENTER = (6, 7)
ARM_4 = bmp([
    ".....####.",
    "....#hbbd#",
    "....#hbbd#",
    "...#hhbbd#",
    "...#hbbd#.",
    "...#hbbd#.",
    "..#hhbbd#.",
    "..#hbbd#..",
    "..#hbbd#..",
    ".#hhbbd#..",
    ".#hbbd#...",
    ".#LVVv#...",
    ".#VvVL#...",
    ".#LVVv#...",
    ".#vVvV#...",
    "#hbbbd#...",
    "#hbbbbd#..",
    "#bbbbbd#..",
    ".#dddd#...",
    "..####....",
])
ARM_4_FIST = (3, 17)
ARM_4_SHOULDER = (7, 0)
ARM_UP_4 = bmp([
    "..####....",
    ".#dddd#...",
    "#bbbbbd#..",
    "#hbbbbd#..",
    "#hbbbd#...",
    ".#vVvV#...",
    ".#LVVv#...",
    ".#VvVL#...",
    ".#LVVv#...",
    ".#hbbd#...",
    ".#hhbbd#..",
    "..#hbbd#..",
    "..#hbbd#..",
    "..#hhbbd#.",
    "...#hbbd#.",
    "...#hbbd#.",
    "...#hhbbd#",
    "....#hbbd#",
    "....#hbbd#",
    ".....####.",
])
ARM_UP_4_FIST = (3, 3)
ARM_UP_4_SHOULDER = (7, 19)
ARM_OUT_4 = bmp([
    "..#####......",
    ".#bbbbd#####.",
    "#dbbbbbLVLbbd#",
    "#dbbbbbVvVbbd#",
    "#dbbbbbLVLbbd#",
    ".#bbbbdvVvbdd#",
    "..#####.#####",
])
ARM_OUT_4_FIST = (2, 3)
ARM_OUT_4_SHOULDER = (12, 3)
# de dos, le bras plié disparaît devant le corps : on ne voit que le haut du bras rentrer derrière le torse
ARM_BEAT_4 = bmp([
    ".....####.",
    "....#hbbd#",
    "....#hbbd#",
    "...#hhbbd#",
    "...#hbbd#.",
    "..#hhbbd#.",
    "..#hbbdd#.",
    "..#bbbdd#.",
    "...#####..",
])
ARM_BEAT_4_FIST = (6, 7)
ARM_BEAT_4_SHOULDER = (7, 0)
# bras tendu loin du spectateur (Shoot de dos) : on voit le haut du bras partir en avant, le poing disparaît
ARM_PUSH_4 = bmp([
    "..#####.",
    ".#hbbbd#",
    "#hbbbbd#",
    "#LVVVd#.",
    "#VvVLd#.",
    "#hbbbd#.",
    ".#ddd#..",
    "..###...",
])
ARM_PUSH_4_FIST = (2, 6)
ARM_PUSH_4_SHOULDER = (6, 0)
LEG_4 = bmp([
    "#hbbd#",
    "#hbbd#",
    "#hbbd#",
    "#hbd#.",
    "#hbd#.",
    "#LVv#.",
    "#VvV#.",
    "#hbd#.",
    "#hbd#.",
    "#bbbd#",
    "#dddd#",
    ".####.",
])
TAIL_4 = bmp([
    "..#dd#..",
    "..#dd#..",
    "..#dd#..",
    "...#dd#.",
    "...#dd#.",
    "....#dd#",
    "....#dd#",
    "...#ddd#",
    "..#dd##.",
    ".#dd#...",
    ".#d#....",
    ".##.....",
])

# =====================================================================================
# BAS-DROITE (1) — trois quarts face (le côté droit de l'écran est le plus proche)
# =====================================================================================
HEAD_1 = bmp([
    "#....................#..",
    "##..................##..",
    "#d#................#d#..",
    "#dd#..............#dd#..",
    "#ddb#....####....#bdd#..",
    "#ddbb####bbbb####bbdd#..",
    ".#dbbbbbbbbbbbbbbbbbd##.",
    ".#bbbGGGGbbbbbbGGGGbbb#.",
    "..#bbGRRRGbbbbGGRRRGGb#.",
    "..#bbGRO#RGbbbGRO#RGGg#.",
    "..#bbGGGGGGbbbGGGGGGgg#.",
    "...#bbbGGGGGGGGGGGGggg#.",
    "....#bbbbbGGgggggggggW#.",
    ".....##bbbbGggW#gggg##..",
    ".......##bbbGgggggg#....",
    ".........###bbbb###.....",
    "............####........",
])
HEAD_1_MARK = (13, 11)
MANE_1 = MANE_0
TORSO_1 = bmp([
    "..#########..",
    ".#hhbbbbbbb#.",
    "#hhbbGGGGGbb#",
    "#hbbGGgGgGGb#",
    "#hbbGGGGGGGb#",
    "#bbbGgGgGgGb#",
    "#bbbGGGGGGGb#",
    "#bbbbGgGgGbb#",
    "#bbbbbGGGbbd#",
    "#dbbbbbbbbdd#",
    ".#dbbbbbbdd#.",
    ".#ddbbbbddd#.",
    "..#dddddd#...",
])
TORSO_1_CENTER = (7, 7)
TAIL_1 = bmp([
    "...###..",
    "..#ddd#.",
    ".#dd#dd#",
    ".#d#.#d#",
    ".#d#.##.",
    ".#dd#...",
    "..#dd#..",
    "...#dd#.",
    "....#dd#",
    ".....#d#",
    "......##",
])

# =====================================================================================
# HAUT-DROITE (3) — trois quarts dos (le côté gauche de l'écran est le plus proche)
# =====================================================================================
HEAD_3 = bmp([
    "..#....................#",
    "..##..................##",
    "..#d#................#d#",
    "..#dd#..............#dd#",
    "..#ddb#....####....#bdd#",
    "..#ddbb####bbbb####bbdd#",
    ".##dbbbbbbbbbbbbbbbbbbd#",
    ".#bbbbbbbbbbbbbbbbbbbbb#",
    ".#bbbbbbbbbbbbbbbbbbbGG#",
    ".#bbbbbbbbbbbbbbbbbbbGG#",
    ".#dbbbbbbbbbbbbbbbbbbbG#",
    "..#dbbbbbbbbbbbbbbbbbbg#",
    "..#ddbbbbbbbbbbbbbbbgg#.",
    "...##dbbbbbbbbbbbbbgg#..",
    ".....##dddddddddddg##...",
    ".......#dddddddddd#.....",
    "........##########......",
])
HEAD_3_MARK = (11, 11)
MANE_3 = MANE_0
VINES_3 = bmp([
    "..#VLVLV#..",
    ".#VLVLVLV#.",
    ".#vVLVLVv#.",
    "#VvVLVLVvV#",
    "#vVvVvVvVv#",
    "#VvVvVvVvV#",
    ".#vVvVvVv#.",
    ".#VvVvVvV#.",
    "..#vVvVv#..",
    "..#Vv#Vv#..",
    "...#v#.#v#.",
    "....#...#..",
])
TORSO_3 = TORSO_4
TORSO_3_CENTER = (6, 7)
TAIL_3 = bmp([
    ".......#dd#",
    "......#dd#.",
    ".....#dd#..",
    "....#dd#...",
    "...#dd#....",
    "..#dd#.....",
    ".#dd#......",
    "#dd#.......",
    "#d#........",
    "##.........",
])

# =====================================================================================
# SOMMEIL (une seule direction) — couché sur le flanc, tête à gauche, queue enroulée
# =====================================================================================
SLEEP_A = bmp([
    "...#..#.............................",
    "..##.##.......###...................",
    "..#d#d#.....##nnn##.................",
    ".#ddbdd#..##nnnnnnn##...............",
    "#dbbbbbb###nnnnnnnnnnn##............",
    "#bbbbbbbbbbnnnnnnnnbbbbb##..........",
    "#bGGGbbbbbbbbnnnbbbbbbbbbb##........",
    "#GG##Gbbbbbbbbbbbbbbbbbbbbbb#.......",
    "#GGGGGbbbbbbbbbbbbbbbbbbbbbbb#......",
    "#bGgggGbbbbbbbbbbbbbbbbbbbbbbd#.....",
    ".#ggg#gbbbbbbbbbbbbbbbbbbbbbbdd#....",
    ".##ggg#bbbbbbbbbbbbbbbbbbbbbbddd#...",
    "..####hbbbbbbbbbbbbbbbbbbbbbbbddd#..",
    "....#hbbbbbbbbbbbbbbbbbbbbbbbdddd#..",
    "...#hbbbbLVLbbbbbbbbbLVLbbbbbdddd#..",
    "...#hbbbbVvVbbbbbbbbbVvVbbbbdddd#...",
    "...#bbbbbLVLbbbbbbbbbLVLbbbbddd##...",
    "...#g#g#g#bbbbbbbb#g#g#g#bbdd#dd#...",
    "....###########################dd#..",
    "..............................####..",
])
SLEEP_B = bmp([              # respiration : le dos redescend d'une ligne
    "...#..#.............................",
    "..##.##.............................",
    "..#d#d#.......###...................",
    ".#ddbdd#....##nnn##.................",
    "#dbbbbbb###nnnnnnnn##...............",
    "#bbbbbbbbbbnnnnnnnnnnn###...........",
    "#bGGGbbbbbbbbnnnnnbbbbbbb##.........",
    "#GG##Gbbbbbbbbbbbbbbbbbbbbbb#.......",
    "#GGGGGbbbbbbbbbbbbbbbbbbbbbbb#......",
    "#bGgggGbbbbbbbbbbbbbbbbbbbbbbd#.....",
    ".#ggg#gbbbbbbbbbbbbbbbbbbbbbbdd#....",
    ".##ggg#bbbbbbbbbbbbbbbbbbbbbbddd#...",
    "..####hbbbbbbbbbbbbbbbbbbbbbbbddd#..",
    "....#hbbbbbbbbbbbbbbbbbbbbbbbdddd#..",
    "...#hbbbbLVLbbbbbbbbbLVLbbbbbdddd#..",
    "...#hbbbbVvVbbbbbbbbbVvVbbbbdddd#...",
    "...#bbbbbLVLbbbbbbbbbLVLbbbbddd##...",
    "...#g#g#g#bbbbbbbb#g#g#g#bbdd#dd#...",
    "....###########################dd#..",
    "..............................####..",
])
SLEEP_HEAD_MARK = (3, 8)
SLEEP_CENTER = (16, 11)
SLEEP_FISTS = ((6, 17), (21, 17))


# =====================================================================================
# Effets
# =====================================================================================
# Griffures : trois traits parallèles à la direction de frappe, dessinés à la main pour les trois
# familles d'axes (vertical, horizontal, diagonale) ; les autres directions sont des miroirs/transposées.
_SLASH_V = bmp([
    "..G...G...G..",
    "..W...W...W..",
    ".GW..GW..GW..",
    ".GW..GW..GW..",
    ".GW..GW..GW..",
    ".GW..GW..GW..",
    ".GW..GW..GW..",
    "..W...W...W..",
    "..G...G...G..",
])
_SLASH_D = bmp([          # frappe vers le bas-droite : trois traits « \ » décalés en travers
    "......G......",
    "......GW.....",
    ".......GW....",
    "...G....GW...",
    "...GW....GW..",
    "....GW....GW.",
    "G....GW.....G",
    "GW....GW.....",
    ".GW....GW....",
    "..GW....G....",
    "...GW........",
    "....GW.......",
    "......G......",
])


def slash(direction: int) -> np.ndarray:
    if direction in (0, 4):
        return _SLASH_V
    if direction in (2, 6):
        return np.ascontiguousarray(_SLASH_V.transpose(1, 0, 2))
    a = _SLASH_D                       # 1 : bas-droite (axe « \ »)
    if direction == 3:                 # haut-droite : axe « / »
        a = a[::-1]
    elif direction == 5:               # haut-gauche : axe « \ », rotation de 180°
        a = a[::-1, ::-1]
    elif direction == 7:               # bas-gauche : axe « / »
        a = a[:, ::-1]
    return np.ascontiguousarray(a)


HOWL = bmp([
    ".W..",
    "W.W.",
    "...W",
    "W.W.",
    ".W..",
])
