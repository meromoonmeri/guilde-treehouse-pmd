#!/usr/bin/env python3
"""Zarude #0893 — pièces de pixel art du sprite PMD, échelle 1:1.

Deux origines, clairement séparées ci-dessous :

1. **Pièces relevées sur la planche fournie par l'utilisateur** (`reference/zarude/zarude_overworld_2x.png`,
   « Made with Game Character Hub », 4 directions × 4 images, dessinée au double : ramenée à 1:1 dans
   `zarude_overworld_1x.png`). Chaque pièce est une découpe pixel-exacte d'une case (tête, poitrail, bras,
   jambes, queue), en coordonnées relatives à l'ancre de la case (colonne 16, rang 27 : sol sous le corps).
   La vue « gauche » de la planche est retournée pour donner la Droite (2), comme dans les sprites officiels.
   Six teintes quasi doublons de la planche (53/53/53, 63/65/63, 94/97/94, 78/105/74, 200/200/200,
   232/232/248) sont ramenées à leur voisine : 11 couleurs.
2. **Pièces dessinées pour compléter** : les deux diagonales (Bas-droite 1, Haut-droite 3), les variantes
   de bras des animations (levé, tendu, poing au poitrail, poussée), la pose de sommeil, les effets.
   Elles reprennent la palette et le trait (contour noir, cuffs de lianes v/V/L, masque G/g) de la planche.

Convention : une lettre = une couleur, « . » = transparent ; `X_AT` = coin haut-gauche de la pièce X
relatif à l'ancre (x vers la droite, y vers le bas) dans la pose de repos. Les points `_FIST` / `_SHOULDER`
sont en coordonnées de la pièce.
"""
from __future__ import annotations

import numpy as np

PALETTE = {
    "#": (0, 0, 0),         # contour
    "d": (48, 48, 48),      # pelage sombre
    "b": (72, 72, 72),      # pelage
    "h": (96, 96, 96),      # pelage éclairé
    "g": (144, 144, 160),   # gris bleuté : ombre du masque, poitrail
    "G": (192, 192, 192),   # gris clair : masque, poitrail
    "W": (255, 255, 255),   # crocs, reflet de l'œil, griffures
    "R": (224, 56, 56),     # œil
    "v": (45, 61, 43),      # liane sombre (contour des cuffs)
    "V": (111, 151, 90),    # liane
    "L": (148, 198, 90),    # liane éclairée
}
DARKER = {"h": "b", "b": "d", "L": "V", "V": "v", "G": "g"}   # membres du côté opposé au spectateur


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
    if n <= 0:
        return a
    rows = [r for r in range(a.shape[0]) if not (keep_top <= r < keep_top + n)]
    return np.ascontiguousarray(a[rows])


def shift_rows(rows: list[str], dx: int) -> list[str]:
    return [("." * dx + r) if dx >= 0 else r[-dx:] for r in rows]


# =====================================================================================
# 1. PIÈCES RELEVÉES SUR LA PLANCHE FOURNIE
# =====================================================================================

# ---- Bas (0) : case « bas, pas A » ; le pas B est son miroir exact ----
HEAD_0 = bmp([  # tête, crinière, masque (rangs −19 à −6)
    "##................##",
    "#h##............##h#",
    ".#hh##.######.##hh#.",
    "#dbhhh#bbbbbb#hhhbd#",
    ".#dbhhhddbbddhhhbd#.",
    "..#hhhhhhddhhhhhh#..",
    ".#hhbhhhhhhhhhhbhh#.",
    "..##hGGGhhhhGGGh##..",
    "..#hhGddGhhGddGhh#..",
    "...##GRL#GG#LRG##...",
    "....#hGRVggVRGh#....",
    "...#hbhgghhgghbh#...",
    "....#hGdbGGbdGh#....",
    "....#h##WbbW##h#....",
])
HEAD_0_AT = (-10, -19)
TORSO_0 = bmp([  # poitrail
    ".#dGb##bGd#.",
    "#dgGGbbGGg#.",
    "#dbbGddGbbd#",
])
TORSO_0_AT = (-6, -5)
ARM_L_0 = bmp([  # bras gauche-écran, main au sol
    "......d..",
    "....##h..",
    "....#hdV.",
    ".....dhdL",
    ".....#hh.",
    "....#hh#d",
    "...vLV#..",
    "..vVVLLv.",
    "..vLLVVv.",
    ".vLVVLLv.",
    ".#hbbV#..",
    "#hbhhhb#.",
    ".#hb##h#.",
    ".##h#.#..",
    "...##....",
])
ARM_L_0_AT = (-15, -12)
ARM_R_0 = bmp([  # bras droit-écran, main un pixel plus haut
    "..d......",
    "..h##....",
    ".Vdh#....",
    "Ldhd.....",
    ".hh#.....",
    "d#hh#....",
    "..#VLv...",
    ".vVLVVv..",
    ".vLVLLLv.",
    "..#Vbbh#.",
    ".#bhhhbh#",
    ".#h##hh#.",
    "..#.#h##.",
    "....##...",
])
ARM_R_0_AT = (6, -12)
LEG_0 = bmp([  # jambe posée (droite-écran)
    "#bbbb#",
    ".dbb#.",
    ".#bbb#",
    ".#b#b#",
    ".d#.#b",
])
LEG_0_AT = (0, -2)
LEG_UP_0 = bmp([  # jambe levée (gauche-écran, pas A)
    ".#bd##",
    "#bbb#.",
    "db#b#.",
    "d#.#d.",
])
LEG_UP_0_AT = (-6, -2)
HEAD_0_MARK = (10, 9)          # centre du masque (entre les yeux), coordonnées de la pièce
TORSO_0_CENTER = (6, 1)
ARM_L_0_SHOULDER = (6, 0)      # articulation des variantes de bras : (-9, -12)
ARM_L_0_FIST = (3, 12)
ARM_R_0_SHOULDER = (2, 0)
ARM_R_0_FIST = (5, 11)

# ---- Droite (2) : case « gauche » de la planche, retournée ; pas A et pas B ----
HEAD_2 = bmp([  # tête, crinière, lianes de la nuque, haut des épaules (rangs −19 à −7)
    "......##...........",
    "......#d###........",
    "...###.#bbd##......",
    "...#hh###hhhd#.....",
    "..vv#hhhdddhhd#....",
    "..vVV#dhhhhddb#....",
    ".vvv#hhhhhhhhhb#...",
    ".vLLvdddhhGGghh#...",
    ".#vVLdhhhhGddGhg##.",
    ".dddLVdddhgRL#gdGg#",
    "#dhhvLdhhhhGRRdGhg#",
    "#gdbhVLddhbhGghbWd#",
    "#bhhhhVVhdhhhhhdd#.",
])
HEAD_2_AT = (-9, -19)
TORSO_2 = bmp([  # épaules, poitrail, hanche (rangs −6 à −4)
    "..#dgdhbdhGg",
    "#bd....#gGGd",
    ".#bv........",
])
TORSO_2_AT = (-12, -6)
TORSO_2B = bmp([  # épaules, poitrail, hanche, pas B (le bras avancé recouvre l'épaule)
    "..#dgdhbdhGg",
    "#bd....L#GGd",
    ".#bb........",
])
TORSO_2B_AT = (-12, -6)
HAND_F_2 = bmp([  # main du bras éloigné, tendue devant le poitrail
    "#h#hdhb#",
    "###h#h##",
    "..##.d#.",
    ".....##.",
])
HAND_F_2_AT = (0, -6)
ARM_2A = bmp([  # bras proche pendant, main au sol (pas A)
    ".hvLV.",
    ".vVVLV",
    "vVLLVL",
    "vLVVV#",
    "#Vdhhd",
    "#dh##h",
    ".#h#b.",
    "..###.",
])
ARM_2A_AT = (-10, -5)
ARM_2B = bmp([  # bras proche balancé vers l'avant (pas B)
    "hGvVL....",
    ".#VLVV...",
    "#VLVLLV..",
    "#VVLVVL#.",
    ".#VVdhhd#",
    "...#h#dh#",
    "....###h#",
    "...###.#.",
])
ARM_2B_AT = (-9, -5)
LEG_2A = bmp([  # jambe sous le corps (pas A)
    ".#gd.",
    ".#h#.",
    "#hb#.",
    ".##..",
    ".#b#.",
    "#bbd#",
    ".####",
])
LEG_2A_AT = (-5, -4)
LEG_2B = bmp([  # jambe tendue en arrière (pas B)
    "Vv....",
    "#Vd...",
    ".#bbb.",
    "..#b#b",
    "...#..",
])
LEG_2B_AT = (-11, -2)
TAIL_2A = bmp([  # queue relevée derrière (pas A)
    "..##..",
    ".##b##",
    "#bbbb#",
    "##bb#.",
    ".##b#.",
    "..#b#.",
    "...#b#",
    "...#bd",
])
TAIL_2A_AT = (-16, -13)
TAIL_2B = bmp([  # queue relevée, un pixel plus près du corps (pas B)
    "..##..",
    ".##b##",
    "#bbbb#",
    "##bb#.",
    ".##b#.",
    "..#b#.",
    "..#b#.",
    "...#d.",
])
TAIL_2B_AT = (-15, -13)
HEAD_2_MARK = (13, 10)
TORSO_2_CENTER = (8, 1)
ARM_2A_SHOULDER = (3, -1)      # épaule sous la nuque : (-7, -6)
ARM_2A_FIST = (2, 6)
ARM_2B_SHOULDER = (2, -3)
ARM_2B_FIST = (6, 6)
HAND_F_2_FIST = (4, 1)
HAND_F_2_SHOULDER = (-2, -1)   # épaule du bras éloigné, derrière le cou : (-2, -7)

# ---- Haut (4) : case « haut, pas A » ; le dos du pas B (queue balancée de l'autre côté) vient de la case B ----
HEAD_4 = bmp([  # sommet du crâne et oreilles
    "##..............##",
    "#h##..dddddd..##h#",
    ".#hh##bhhhhb##hh#.",
    "dhhbbdhhhhhhdbbhhd",
    ".dbbbhhVLLVhhbbbd.",
])
HEAD_4_AT = (-9, -18)
BACK_4 = bmp([  # nuque et lianes, dos, queue pendante (pas A)
    ".##bvvVLLLLVvvb##.",
    "##h#LVVVLLVVVL#h##",
    "#hhb#vvV##Vvv#bhh#",
    "#dhhhhb##h#bhhhhd#",
    ".#bhhh#hhhdhhhhb#.",
    "#hhdhh##hhhdhhdhh#",
    "...ghhG##hhdhhg...",
    "...#GGhhhdh#GG#...",
    "...#hhGhgdh#hh#...",
    "....#GhgGdh#g#....",
    "...#dggGbh#ggd#...",
    "...#dbbgd#gbbd#...",
    ".......###........",
])
BACK_4_AT = (-9, -13)
BACK_4B = bmp([  # même dos, queue balancée de l'autre côté (pas B)
    ".##bvvVLLLLVvvb##.",
    "##h#LVVVLLVVVL#h##",
    "#hhb#vvVV##vv#bhh#",
    "#dhhhhbv##h#hhhhd#",
    ".#bhhhh#hhhdhhhb#.",
    "#hhdhhh##hhhdhdhh#",
    "...ghhGh##dhdhg...",
    "...#GGhhhhdh#G#...",
    "...#hhGhgGd#hh#...",
    "....#GhgGdh#g#....",
    "...#dggGbh#ggd#...",
    "...#dbbgd#gbbd#...",
    "........###.......",
])
BACK_4B_AT = (-9, -13)
ARM_L_4 = bmp([  # bras gauche-écran pendant
    "..#hh#",
    ".vLh#.",
    ".vVLLv",
    "vLLVVv",
    "vVLLLV",
    "#bVVVb",
    "#db##d",
    "##b#..",
    "..##..",
])
ARM_L_4_AT = (-12, -7)
ARM_R_4 = bmp([  # bras droit-écran, un peu avancé
    "...v..",
    "#hLLv.",
    "VLVVLv",
    "vVLLVv",
    "#dVVb#",
    "b##bd#",
    "#.#b##",
    "..##..",
])
ARM_R_4_AT = (6, -8)
LEG_4 = bmp([  # jambe posée (droite-écran)
    "ddV#.",
    "#dVb#",
    "#dbb#",
    ".###d",
])
LEG_4_AT = (1, -1)
LEG_UP_4 = bmp([  # jambe levée (gauche-écran, pas A)
    "..#Vd.",
    "##ddd#",
    ".####.",
])
LEG_UP_4_AT = (-7, -1)
HEAD_4_MARK = (9, 2)
BACK_4_CENTER = (9, 6)
ARM_L_4_SHOULDER = (4, -3)     # épaule cachée par le dos : (-8, -10)
ARM_L_4_FIST = (2, 7)
ARM_R_4_SHOULDER = (2, -4)
ARM_R_4_FIST = (3, 6)


# =====================================================================================
# 2. PIÈCES DESSINÉES POUR COMPLÉTER
# =====================================================================================

# ---- Bas-droite (1) : vue de trois quarts construite sur la vue de face (côté proche = gauche-écran) ----
HEAD_1 = bmp([  # tête de trois quarts : oreille éloignée plus fine, traits du masque décalés d'un pixel vers la droite
    "##..............##",
    "#h##..........##h#",
    ".#hh##.######.#hh#",
    "#dbhhh#bbbbbb#hbd#",
    ".#dbhhhddbbddhbd#.",
    "..#hhhhhhddhhhh#..",
    ".#hhbhhhhhhhhbhh#.",
    "..##hhGGGhhhGGh#..",
    "..#hhhGddGhGdGh#..",
    "...##hGRL#G#LRG#..",
    "....#hhGRVgVRGh#..",
    "...#hbhhgghgghbh#.",
    "....#hhGdbGbdGh#..",
    "....#hh##WbW##h#..",
])
HEAD_1_AT = (-9, -19)
HEAD_1_MARK = (10, 9)
TORSO_1 = bmp([  # poitrail de trois quarts
    ".#ddGb#bGd#.",
    "#ddgGGbGGg#.",
    "#ddbbGdGbd#.",
])
TORSO_1_AT = (-6, -5)
TORSO_1_CENTER = (6, 1)
TAIL_1 = bmp([  # bout de queue qui dépasse derrière l'épaule proche
    "..##.",
    ".#bb#",
    "#bb#.",
    "#b#..",
    "#b#..",
    ".#...",
])
TAIL_1_AT = (-14, -15)

# ---- Haut-droite (3) : vue de trois quarts dos construite sur la vue de dos (côté proche = droite-écran) ----
HEAD_3 = bmp([  # arrière du crâne de trois quarts (oreille éloignée = gauche-écran, plus fine)
    "##............##",
    "#h#.dddddd..##h#",
    "#h##bhhhhb##hh#.",
    "hbbdhhhhhhdbbhhd",
    "dbbhVLLVhhhbbbd.",
])
HEAD_3_AT = (-8, -18)
HEAD_3_MARK = (9, 2)
BACK_3 = bmp([  # dos de trois quarts : lianes et queue décalées d'un pixel vers la gauche, sliver du masque à droite
    ".##vvVLLLLVvvbb##.",
    "##hLVVVLLVVVL#bh##",
    "#hb#vvV##Vvv#bhhG#",
    "#dhhhb##h#bhhhhGG#",
    ".#bhh#hhhdhhhhbG#.",
    "#hdhh##hhhdhhdhhh#",
    "..ghhG##hhdhhg....",
    "..#GGhhhdh#GG#....",
    "..#hhGhgdh#hh#....",
    "...#GhgGdh#g#.....",
    "..#dggGbh#ggd#....",
    "..#dbbgd#gbbd#....",
    "......###.........",
])
BACK_3_AT = (-9, -13)
BACK_3B = bmp([  # dos de trois quarts, queue balancée (pas B)
    ".##vvVLLLLVvvbb##.",
    "##hLVVVLLVVVL#bh##",
    "#hb#vvVV##vv#bhhG#",
    "#dhhhbv##h#hhhhGG#",
    ".#bhhh#hhhdhhhbG#.",
    "#hdhhh##hhhdhdhhh#",
    "..ghhGh##dhdhg....",
    "..#GGhhhhdh#G#....",
    "..#hhGhgGd#hh#....",
    "...#GhgGdh#g#.....",
    "..#dggGbh#ggd#....",
    "..#dbbgd#gbbd#....",
    ".......###........",
])
BACK_3B_AT = (-9, -13)
BACK_3_CENTER = (9, 6)

# ---- Variantes de bras, famille 0 (face) : dessinées pour le bras gauche-écran, retournées pour l'autre ----
ARM_UP_0 = bmp([  # bras levé au-dessus de la tête : main ouverte en haut (celle de la planche, retournée), cuff, avant-bras vers l'épaule
    "...##...",
    ".##h#.#.",
    ".#hb##h#",
    "#hbhhhb#",
    ".#hbbV#.",
    ".vLVVLv.",
    "vLVVLLv.",
    "vLLVVLv.",
    ".vvVLv..",
    "..#hh#..",
    "..#hh#..",
    "..#hb#..",
    "..#hb#..",
    "...#hb#.",
    "...#hb#.",
    "....#h#.",
    "....##..",
])
ARM_UP_0_AT = (-14, -28)
ARM_UP_0_FIST = (4, 2)
ARM_UP_0_SHOULDER = (5, 16)
ARM_OUT_0 = bmp([  # bras tendu sur le côté : main à gauche, cuff, épaule à droite
    "...##..vvv.....",
    ".##h#.vLVLv#...",
    "#hbh#vVLVLV#h#.",
    "#hbhhLVLVLVhhh#",
    "#hbh#vVLVLV#hb#",
    ".##h#.vLVLv.##.",
    "...##..vvv.....",
])
ARM_OUT_0_AT = (-22, -15)
ARM_OUT_0_FIST = (2, 3)
ARM_OUT_0_SHOULDER = (13, 3)
ARM_BEAT_0 = bmp([  # bras plié : haut du bras vertical le long du corps, avant-bras vers le centre, cuff et poing sur le poitrail
    ".#d#...........",
    "#hbd#..........",
    "#hbd#..........",
    "#hbd#..........",
    "#hbd#..........",
    "#hbd#..........",
    "#hbd#..........",
    ".#hbd#...vvv...",
    "..#hbd#.vLVLv#.",
    "...#hbdvVLVLhh#",
    "....#hbLVLVLhb#",
    ".....#vVLVLVbh#",
    "......vvLVLv##.",
    ".......vvv.....",
])
ARM_BEAT_0_AT = (-11, -12)
ARM_BEAT_0_FIST = (12, 10)
ARM_BEAT_0_SHOULDER = (2, 0)
ARM_PUSH_0 = bmp([  # bras poussé vers l'avant : bras oblique vers le centre, cuff vu de face, paume ouverte griffes vers le bas
    "#d#......",
    "#hd#.....",
    "#hbd#....",
    ".#hbd#...",
    ".#hbd#...",
    "..#hbd#..",
    "..vvLVv..",
    ".vLVLVLv.",
    ".vVLVLVv.",
    ".#vvVvv#.",
    "#hbhhhbh#",
    ".#h#h#h#.",
    "..#.#.#..",
])
ARM_PUSH_0_AT = (-11, -12)
ARM_PUSH_0_FIST = (4, 10)
ARM_PUSH_0_SHOULDER = (1, 0)

# ---- Variantes de bras, famille 2 (profil regardant à droite), bras proche ----
ARM_UP_2 = bmp([  # bras levé, vu de profil (doigts repliés)
    "..##..",
    ".#h##.",
    "#hbh#.",
    "#hbbh#",
    ".#bV#.",
    ".vLVLv",
    "vLVVLv",
    "vVLLVv",
    ".vvVv.",
    ".#hh#.",
    ".#hh#.",
    ".#hb#.",
    ".#hb#.",
    ".#hb#.",
    ".#hb#.",
    ".#hb#.",
    ".#bd#.",
    "..##..",
])
ARM_UP_2_AT = (-9, -25)
ARM_UP_2_FIST = (2, 2)
ARM_UP_2_SHOULDER = (2, 17)
ARM_OUT_2 = bmp([  # bras tendu vers l'avant à hauteur d'épaule : épaule à gauche, cuff, main à droite
    "......vvv....##.",
    ".####vLVLv.##h#.",
    "#hhhhLVLVL#hbh#.",
    "#bhhhVLVLVhhbhh#",
    ".####vLVLv#hbh#.",
    "......vvv.##h#..",
    "...........##...",
])
ARM_OUT_2_AT = (-8, -11)
ARM_OUT_2_FIST = (13, 3)
ARM_OUT_2_SHOULDER = (1, 2)
ARM_BEAT_2 = bmp([  # bras plié, poing sur le poitrail (vers l'avant)
    "#d#........",
    "#hd#.......",
    "#hd#.vvv...",
    "#hb#vLVLv#.",
    ".#hbLVLVhh#",
    ".#hbvLVLhb#",
    "..##.vvv##.",
])
ARM_BEAT_2_AT = (-8, -8)
ARM_BEAT_2_FIST = (9, 4)
ARM_BEAT_2_SHOULDER = (1, 0)
ARM_PUSH_2 = ARM_OUT_2
ARM_PUSH_2_FIST = ARM_OUT_2_FIST
ARM_PUSH_2_SHOULDER = ARM_OUT_2_SHOULDER
ARM_PUSH_2_AT = ARM_OUT_2_AT

# ---- Variantes de bras, famille 4 (dos) : mêmes silhouettes que de face, dos de la main (pas de paume) ----
ARM_UP_4 = bmp([  # bras levé vu de dos
    "...##...",
    ".##b#.#.",
    ".#bd##b#",
    "#bdbbbd#",
    ".#bddV#.",
    ".vLVVLv.",
    "vLVVLLv.",
    "vLLVVLv.",
    ".vvVLv..",
    "..#hh#..",
    "..#hh#..",
    "..#hb#..",
    "..#hb#..",
    "...#hb#.",
    "...#hb#.",
    "....#h#.",
    "....##..",
])
ARM_UP_4_AT = (-14, -28)
ARM_UP_4_FIST = (4, 2)
ARM_UP_4_SHOULDER = (5, 16)
ARM_OUT_4 = bmp([  # bras tendu sur le côté, vu de dos
    "...##..vvv.....",
    ".##b#.vLVLv#...",
    "#bdb#vVLVLV#h#.",
    "#bdbbLVLVLVhhh#",
    "#bdb#vVLVLV#hb#",
    ".##b#.vLVLv.##.",
    "...##..vvv.....",
])
ARM_OUT_4_AT = (-22, -15)
ARM_OUT_4_FIST = (2, 3)
ARM_OUT_4_SHOULDER = (13, 3)
ARM_BEAT_4 = bmp([  # bras plié vu de dos : coude sorti, avant-bras et poing cachés par le corps
    "..#d#.",
    ".#hbd#",
    ".#hbd#",
    "#hbd#.",
    "#hbd#.",
    "#hb#vv",
    "#bb#LV",
    ".#d#vv",
    "..##..",
])
ARM_BEAT_4_AT = (-11, -12)
ARM_BEAT_4_FIST = (5, 6)
ARM_BEAT_4_SHOULDER = (3, 0)
ARM_PUSH_4 = bmp([  # bras poussé vers l'avant vu de dos : seul le haut du bras dépasse
    ".#d#.",
    "#hbd#",
    "#hbd#",
    ".#bd#",
    ".#bd#",
    "..##.",
])
ARM_PUSH_4_AT = (-11, -12)
ARM_PUSH_4_FIST = (3, 5)
ARM_PUSH_4_SHOULDER = (2, 0)

# ---- Sommeil (une seule ligne, deux images) : couché sur le flanc, tête à gauche ----
SLEEP_A = bmp([  # sommeil, image 1
    "..##.........###..........",
    ".#hh#......##bbb##........",
    "#hbb##....#bbbbbbb##......",
    "#bhhhh#..#bbbbbbbbbb#.....",
    ".#hhGGh##bbbbbbbbbbbb#....",
    ".#hGGgGhbbbbbbbbbbbbbb#...",
    "#hGGgGGhbbbbbbbbbbbbbbb#..",
    "#GGGgGGhbbbbbbbbbbbbbbbb#.",
    "#gGGgGhbbbbbbbbbbbbbbbbbd#",
    "#hgGGhbbbbvLVvbbbbbvLVvbd#",
    "#hhhhbbbbvLVLVvbbbvLVLVvd#",
    ".#hhbbbbbvVLVVvbbbvVLVVvd#",
    "..#hh#bbb#hbbh#bbb#hbbh#d#",
    "...##..###.##.#####.##.###",
])
SLEEP_A_AT = (-14, -12)
SLEEP_HEAD_MARK = (4, 7)
SLEEP_CENTER = (14, 8)
SLEEP_FISTS = ((11, 12), (20, 12))
SLEEP_B = bmp([  # sommeil, image 2 : le dos redescend d'un rang (respiration)
    "..##......................",
    ".#hh#........###..........",
    "#hbb##.....##bbb##........",
    "#bhhhh#...#bbbbbbb##......",
    ".#hhGGh##.#bbbbbbbbb#.....",
    ".#hGGgGhbbbbbbbbbbbbb#....",
    "#hGGgGGhbbbbbbbbbbbbbb#...",
    "#GGGgGGhbbbbbbbbbbbbbbb#..",
    "#gGGgGhbbbbbbbbbbbbbbbbd#.",
    "#hgGGhbbbbvLVvbbbbbvLVvbd#",
    "#hhhhbbbbvLVLVvbbbvLVLVvd#",
    ".#hhbbbbbvVLVVvbbbvVLVVvd#",
    "..#hh#bbb#hbbh#bbb#hbbh#d#",
    "...##..###.##.#####.##.###",
])
SLEEP_B_AT = (-14, -12)

# ---- Effets ----
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
_SLASH_D = bmp([          # frappe vers le bas-droite : trois traits « \\ » décalés en travers
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
    a = _SLASH_D                       # 1 : bas-droite (axe « \\ »)
    if direction == 3:                 # haut-droite : axe « / »
        a = a[::-1]
    elif direction == 5:               # haut-gauche : axe « \\ », rotation de 180°
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
SPARK = bmp(["W"])

