#!/usr/bin/env python3
"""Régénère `zarude_pieces.py` : pièces relevées pixel par pixel sur la planche de marche fournie
(`reference/zarude/zarude_overworld_1x.png`) + pièces dessinées ici en ASCII (diagonales, bras des animations,
sommeil, effets).

Le module généré est commité (il se lit sans cette étape) ; ce script sert quand on retouche une découpe
ou une pièce dessinée : `python3 source/personnages/zarude_pieces_from_sheet.py` puis rebuild.

Tables de découpe : R(y, x0, x1) = pixels x0..x1 du rang y de la case 32 × 32 (ancre en (16, 27)) ;
`flip=True` retourne la pièce (vue « gauche » → Droite) et convertit sa position (x → 15 − x).
"""
from PIL import Image
import numpy as np
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
A = np.array(Image.open(ROOT / 'source/personnages/reference/zarude/zarude_overworld_1x.png'))
MERGE = {(53,53,53):(48,48,48),(63,65,63):(72,72,72),(94,97,94):(96,96,96),(78,105,74):(111,151,90),(200,200,200):(192,192,192),(232,232,248):(255,255,255)}
LET = {(0,0,0):'#',(96,96,96):'h',(72,72,72):'b',(48,48,48):'d',(192,192,192):'G',(144,144,160):'g',(255,255,255):'W',(224,56,56):'R',(45,61,43):'v',(111,151,90):'V',(148,198,90):'L'}
AX, AY = 16, 27
def cell(r, c): return A[r*32:(r+1)*32, c*32:(c+1)*32]
def let(px):
    if px[3] == 0: return '.'
    p = tuple(int(v) for v in px[:3]); return LET[MERGE.get(p, p)]
def R(y, x0, x1=None): return (y, x0, x1 if x1 is not None else x0)
def piece(cl, ranges, flip=False):
    ys = [y for y,_,_ in ranges]; y0, y1 = min(ys), max(ys)
    xs0 = min(x0 for _,x0,_ in ranges); xs1 = max(x1 for _,_,x1 in ranges)
    rows = []
    for y in range(y0, y1+1):
        row = ['.']*(xs1-xs0+1)
        for yy,x0,x1 in ranges:
            if yy != y: continue
            for x in range(x0, x1+1): row[x-xs0] = let(cl[y,x])
        rows.append(''.join(row[::-1]) if flip else ''.join(row))
    rel = (15-xs1, y0-AY) if flip else (xs0-AX, y0-AY)
    return rows, rel

D = cell(0,0); Lc = cell(1,0); Lb = cell(1,2); U = cell(3,0); Ub = cell(3,2)
T = {}
T['HEAD_0'] = (D, [R(8,6,7),R(8,24,25),R(9,6,9),R(9,22,25),R(10,7,11),R(10,13,18),R(10,20,24),R(11,6,25),R(12,7,24),R(13,8,23),R(14,7,24),
          R(15,8,23),R(16,8,23),R(17,9,22),R(18,10,21),R(19,9,22),R(20,10,21),R(21,10,21)], False, "tête, crinière, masque (rangs −19 à −6)")
T['TORSO_0'] = (D, [R(22,11,20),R(23,10,20),R(24,10,21)], False, "poitrail")
T['ARM_L_0'] = (D, [R(15,7),R(16,5,7),R(17,5,8),R(18,6,9),R(19,6,8),R(20,5,9),R(21,4,7),R(22,3,8),R(23,3,8),R(24,2,8),R(25,2,7),R(26,1,8),R(27,2,8),R(28,2,7),R(29,4,5)], False, "bras gauche-écran, main au sol")
T['ARM_R_0'] = (D, [R(15,24),R(16,24,26),R(17,23,26),R(18,22,25),R(19,23,25),R(20,22,26),R(21,24,27),R(22,23,28),R(23,23,29),R(24,24,29),R(25,23,30),R(26,23,29),R(27,24,29),R(28,26,27)], False, "bras droit-écran, main un pixel plus haut")
T['LEG_0'] = (D, [R(25,16,21),R(26,17,20),R(27,17,21),R(28,17,21),R(29,17,21)], False, "jambe posée (droite-écran)")
T['LEG_UP_0'] = (D, [R(25,11,15),R(26,10,14),R(27,10,14),R(28,10,14)], False, "jambe levée (gauche-écran, pas A)")
T['HEAD_2'] = (Lc, [R(8,17,18),R(9,14,18),R(10,12,17),R(10,19,21),R(11,11,21),R(12,10,22),R(13,10,22),R(14,9,23),R(15,9,23),R(16,7,23),R(17,6,23),R(18,6,24),R(19,6,24),R(20,7,24)], True, "tête, crinière, lianes de la nuque, haut des épaules (rangs −19 à −7)")
T['TORSO_2'] = (Lc, [R(21,16,25),R(22,16,20),R(22,25,27),R(23,24,26)], True, "épaules, poitrail, hanche (rangs −6 à −4)")
T['TORSO_2B'] = (Lb, [R(21,16,25),R(22,16,20),R(22,25,27),R(23,24,26)], True, "épaules, poitrail, hanche, pas B (le bras avancé recouvre l'épaule)")
T['HAND_F_2'] = (Lc, [R(21,8,15),R(22,8,15),R(23,9,13),R(24,9,10)], True, "main du bras éloigné, tendue devant le poitrail")
T['ARM_2A'] = (Lc, [R(22,21,24),R(23,20,24),R(24,20,25),R(25,20,25),R(26,20,25),R(27,20,25),R(28,21,24),R(29,21,23)], True, "bras proche pendant, main au sol (pas A)")
T['ARM_2B'] = (Lb, [R(22,20,24),R(23,19,23),R(24,18,24),R(25,17,24),R(26,16,23),R(27,16,21),R(28,16,20),R(29,17),R(29,19,21)], True, "bras proche balancé vers l'avant (pas B)")
T['LEG_2A'] = (Lc, [R(23,17,19),R(24,17,19),R(25,17,20),R(26,18,19),R(27,17,19),R(28,16,20),R(29,16,19)], True, "jambe sous le corps (pas A)")
T['LEG_2B'] = (Lb, [R(25,25,26),R(26,24,26),R(27,22,25),R(28,21,24),R(29,23)], True, "jambe tendue en arrière (pas B)")
T['TAIL_2A'] = (Lc, [R(14,28,29),R(15,26,30),R(16,26,31),R(17,27,31),R(18,27,30),R(19,27,29),R(20,26,28),R(21,26,28)], True, "queue relevée derrière (pas A)")
T['TAIL_2B'] = (Lb, [R(14,27,28),R(15,25,29),R(16,25,30),R(17,26,30),R(18,26,29),R(19,26,28),R(20,26,28),R(21,26,27)], True, "queue relevée, un pixel plus près du corps (pas B)")
T['HEAD_4'] = (U, [R(9,7,8),R(9,23,24),R(10,7,10),R(10,13,18),R(10,21,24),R(11,8,23),R(12,7,24),R(13,8,23)], False, "sommet du crâne et oreilles")
T['BACK_4'] = (U, [R(14,8,23),R(15,7,24),R(16,7,24),R(17,7,24),R(18,8,23),R(19,7,24),R(20,10,21),R(21,10,21),R(22,10,21),R(23,10,21),R(24,10,21),R(25,10,21),R(26,14,16)], False, "nuque et lianes, dos, queue pendante (pas A)")
T['BACK_4B'] = (Ub, [R(14,8,23),R(15,7,24),R(16,7,24),R(17,7,24),R(18,8,23),R(19,7,24),R(20,10,21),R(21,10,21),R(22,10,21),R(23,10,21),R(24,10,21),R(25,10,21),R(26,15,17)], False, "même dos, queue balancée de l'autre côté (pas B)")
T['ARM_L_4'] = (U, [R(20,6,9),R(21,5,8),R(22,5,9),R(23,4,9),R(24,4,9),R(25,4,9),R(26,4,9),R(27,4,7),R(28,6,7)], False, "bras gauche-écran pendant")
T['ARM_R_4'] = (U, [R(19,25),R(20,22,26),R(21,22,27),R(22,22,27),R(23,22,27),R(24,22,27),R(25,22,27),R(26,24,25)], False, "bras droit-écran, un peu avancé")
T['LEG_4'] = (U, [R(26,17,20),R(27,17,21),R(28,17,21),R(29,18,21)], False, "jambe posée (droite-écran)")
T['LEG_UP_4'] = (U, [R(26,11,13),R(27,9,14),R(28,10,13)], False, "jambe levée (gauche-écran, pas A)")

EX = {k: piece(cl, tb, fl) + (cm,) for k, (cl, tb, fl, cm) in T.items()}

def resample(rows, segs):
    out = []
    for r in rows:
        s = ''
        for s0, s1, dl in segs:
            seg = r[s0:s1]
            s += ''.join(seg[min(int((k + 0.5) * len(seg) / dl), len(seg) - 1)] for k in range(dl))
        out.append(s)
    return out

def block(name, rows, rel, comment):
    lines = [f"{name} = bmp([  # {comment}"]
    lines += [f'    "{r}",' for r in rows]
    lines.append("])")
    lines.append(f"{name}_AT = {rel}")
    return "\n".join(lines)

def hand(name, rows, rel, comment):
    w = max(len(r) for r in rows)
    rows = [r.ljust(w, '.') for r in rows]
    return block(name, rows, rel, comment)

out = []
out.append('''#!/usr/bin/env python3
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
''')

out.append("\n# =====================================================================================\n# 1. PIÈCES RELEVÉES SUR LA PLANCHE FOURNIE\n# =====================================================================================\n")
out.append("# ---- Bas (0) : case « bas, pas A » ; le pas B est son miroir exact ----")
for k in ['HEAD_0', 'TORSO_0', 'ARM_L_0', 'ARM_R_0', 'LEG_0', 'LEG_UP_0']:
    rows, rel, cm = EX[k]; out.append(block(k, rows, rel, cm))
out.append("HEAD_0_MARK = (10, 9)          # centre du masque (entre les yeux), coordonnées de la pièce\nTORSO_0_CENTER = (6, 1)\nARM_L_0_SHOULDER = (6, 0)      # articulation des variantes de bras : (-9, -12)\nARM_L_0_FIST = (3, 12)\nARM_R_0_SHOULDER = (2, 0)\nARM_R_0_FIST = (5, 11)")
out.append("\n# ---- Droite (2) : case « gauche » de la planche, retournée ; pas A et pas B ----")
for k in ['HEAD_2', 'TORSO_2', 'TORSO_2B', 'HAND_F_2', 'ARM_2A', 'ARM_2B', 'LEG_2A', 'LEG_2B', 'TAIL_2A', 'TAIL_2B']:
    rows, rel, cm = EX[k]; out.append(block(k, rows, rel, cm))
out.append("HEAD_2_MARK = (13, 10)\nTORSO_2_CENTER = (8, 1)\nARM_2A_SHOULDER = (3, -1)      # épaule sous la nuque : (-7, -6)\nARM_2A_FIST = (2, 6)\nARM_2B_SHOULDER = (2, -3)\nARM_2B_FIST = (6, 6)\nHAND_F_2_FIST = (4, 1)\nHAND_F_2_SHOULDER = (-2, -1)   # épaule du bras éloigné, derrière le cou : (-2, -7)")
out.append("\n# ---- Haut (4) : case « haut, pas A » ; le dos du pas B (queue balancée de l'autre côté) vient de la case B ----")
for k in ['HEAD_4', 'BACK_4', 'BACK_4B', 'ARM_L_4', 'ARM_R_4', 'LEG_4', 'LEG_UP_4']:
    rows, rel, cm = EX[k]; out.append(block(k, rows, rel, cm))
out.append("HEAD_4_MARK = (9, 2)\nBACK_4_CENTER = (9, 6)\nARM_L_4_SHOULDER = (4, -3)     # épaule cachée par le dos : (-8, -10)\nARM_L_4_FIST = (2, 7)\nARM_R_4_SHOULDER = (2, -4)\nARM_R_4_FIST = (3, 6)")

# ---------------- diagonales ----------------
def interior_shift(rows, dx, fill=None):
    """Décale l'intérieur de chaque ligne de dx (contour gauche/droit conservé) : rotation de 45° approchée
    pour une pièce vue de dos ; la place libérée est remplie avec le pixel intérieur du bord opposé."""
    out = []
    for r in rows:
        op = [i for i, ch in enumerate(r) if ch != '.']
        if len(op) < 4:
            out.append(r); continue
        a, b = op[0], op[-1]
        inner = r[a + 1:b]
        if dx < 0:
            inner = inner[-dx:] + (fill or inner[-1]) * (-dx)
        else:
            inner = (fill or inner[0]) * dx + inner[:-dx]
        out.append(r[:a + 1] + inner + r[b:])
    return out

HEAD_1_ROWS = [      # face tournée vers la droite : oreille éloignée (droite-écran) plus fine, traits décalés d'un pixel
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
]
TORSO_1_ROWS = [
    ".#ddGb#bGd#.",
    "#ddgGGbGGg#.",
    "#ddbbGdGbd#.",
]
HEAD_3_ROWS = [      # dos tourné vers la droite : oreille éloignée (gauche-écran) plus fine, lianes de la nuque décalées
    "##............##",
    "#h#.dddddd..##h#",
    "#h##bhhhhb##hh#.",
    "hbbdhhhhhhdbbhhd",
    "dbbhVLLVhhhbbbd.",
]
BACK_3_ROWS = [      # dos tourné vers la droite : lianes et queue décalées d'un pixel vers la gauche (côté éloigné),
    ".##vvVLLLLVvvbb##.",   # sliver du masque (G) sur le bord droit à hauteur des yeux
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
]
BACK_3B_ROWS = [
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
]
back3, back3b = BACK_3_ROWS, BACK_3B_ROWS

out.append("\n\n# =====================================================================================\n# 2. PIÈCES DESSINÉES POUR COMPLÉTER\n# =====================================================================================\n")
out.append("# ---- Bas-droite (1) : vue de trois quarts construite sur la vue de face (côté proche = gauche-écran) ----")
out.append(block("HEAD_1", HEAD_1_ROWS, (-9, -19), "tête de trois quarts : oreille éloignée plus fine, traits du masque décalés d'un pixel vers la droite"))
out.append("HEAD_1_MARK = (10, 9)")
out.append(block("TORSO_1", TORSO_1_ROWS, (-6, -5), "poitrail de trois quarts"))
out.append("TORSO_1_CENTER = (6, 1)")
out.append(hand("TAIL_1", [
    "..##.",
    ".#bb#",
    "#bb#.",
    "#b#..",
    "#b#..",
    ".#...",
], (-14, -15), "bout de queue qui dépasse derrière l'épaule proche"))
out.append("\n# ---- Haut-droite (3) : vue de trois quarts dos construite sur la vue de dos (côté proche = droite-écran) ----")
out.append(block("HEAD_3", HEAD_3_ROWS, (-8, -18), "arrière du crâne de trois quarts (oreille éloignée = gauche-écran, plus fine)"))
out.append("HEAD_3_MARK = (9, 2)")
out.append(block("BACK_3", back3, (-9, -13), "dos de trois quarts : lianes et queue décalées d'un pixel vers la gauche, sliver du masque à droite"))
out.append(block("BACK_3B", back3b, (-9, -13), "dos de trois quarts, queue balancée (pas B)"))
out.append("BACK_3_CENTER = (9, 6)")

# ---------------- variantes de bras ----------------
# Même trait que les bras de la planche : contour noir, avant-bras de 3-4 px, cuff de lianes de 6-7 px, main griffue de 8 px.
out.append("\n# ---- Variantes de bras, famille 0 (face) : dessinées pour le bras gauche-écran, retournées pour l'autre ----")
out.append(hand("ARM_UP_0", [
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
], (-14, -28), "bras levé au-dessus de la tête : main ouverte en haut (celle de la planche, retournée), cuff, avant-bras vers l'épaule"))
out.append("ARM_UP_0_FIST = (4, 2)\nARM_UP_0_SHOULDER = (5, 16)")
out.append(hand("ARM_OUT_0", [
    "...##..vvv.....",
    ".##h#.vLVLv#...",
    "#hbh#vVLVLV#h#.",
    "#hbhhLVLVLVhhh#",
    "#hbh#vVLVLV#hb#",
    ".##h#.vLVLv.##.",
    "...##..vvv.....",
], (-22, -15), "bras tendu sur le côté : main à gauche, cuff, épaule à droite"))
out.append("ARM_OUT_0_FIST = (2, 3)\nARM_OUT_0_SHOULDER = (13, 3)")
out.append(hand("ARM_BEAT_0", [
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
], (-11, -12), "bras plié : haut du bras vertical le long du corps, avant-bras vers le centre, cuff et poing sur le poitrail"))
out.append("ARM_BEAT_0_FIST = (12, 10)\nARM_BEAT_0_SHOULDER = (2, 0)")
out.append(hand("ARM_PUSH_0", [
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
], (-11, -12), "bras poussé vers l'avant : bras oblique vers le centre, cuff vu de face, paume ouverte griffes vers le bas"))
out.append("ARM_PUSH_0_FIST = (4, 10)\nARM_PUSH_0_SHOULDER = (1, 0)")

out.append("\n# ---- Variantes de bras, famille 2 (profil regardant à droite), bras proche ----")
out.append(hand("ARM_UP_2", [
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
], (-9, -25), "bras levé, vu de profil (doigts repliés)"))
out.append("ARM_UP_2_FIST = (2, 2)\nARM_UP_2_SHOULDER = (2, 17)")
out.append(hand("ARM_OUT_2", [
    "......vvv....##.",
    ".####vLVLv.##h#.",
    "#hhhhLVLVL#hbh#.",
    "#bhhhVLVLVhhbhh#",
    ".####vLVLv#hbh#.",
    "......vvv.##h#..",
    "...........##...",
], (-8, -11), "bras tendu vers l'avant à hauteur d'épaule : épaule à gauche, cuff, main à droite"))
out.append("ARM_OUT_2_FIST = (13, 3)\nARM_OUT_2_SHOULDER = (1, 2)")
out.append(hand("ARM_BEAT_2", [
    "#d#........",
    "#hd#.......",
    "#hd#.vvv...",
    "#hb#vLVLv#.",
    ".#hbLVLVhh#",
    ".#hbvLVLhb#",
    "..##.vvv##.",
], (-8, -8), "bras plié, poing sur le poitrail (vers l'avant)"))
out.append("ARM_BEAT_2_FIST = (9, 4)\nARM_BEAT_2_SHOULDER = (1, 0)")
out.append("ARM_PUSH_2 = ARM_OUT_2\nARM_PUSH_2_FIST = ARM_OUT_2_FIST\nARM_PUSH_2_SHOULDER = ARM_OUT_2_SHOULDER\nARM_PUSH_2_AT = ARM_OUT_2_AT")

out.append("\n# ---- Variantes de bras, famille 4 (dos) : mêmes silhouettes que de face, dos de la main (pas de paume) ----")
out.append(hand("ARM_UP_4", [
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
], (-14, -28), "bras levé vu de dos"))
out.append("ARM_UP_4_FIST = (4, 2)\nARM_UP_4_SHOULDER = (5, 16)")
out.append(hand("ARM_OUT_4", [
    "...##..vvv.....",
    ".##b#.vLVLv#...",
    "#bdb#vVLVLV#h#.",
    "#bdbbLVLVLVhhh#",
    "#bdb#vVLVLV#hb#",
    ".##b#.vLVLv.##.",
    "...##..vvv.....",
], (-22, -15), "bras tendu sur le côté, vu de dos"))
out.append("ARM_OUT_4_FIST = (2, 3)\nARM_OUT_4_SHOULDER = (13, 3)")
out.append(hand("ARM_BEAT_4", [
    "..#d#.",
    ".#hbd#",
    ".#hbd#",
    "#hbd#.",
    "#hbd#.",
    "#hb#vv",
    "#bb#LV",
    ".#d#vv",
    "..##..",
], (-11, -12), "bras plié vu de dos : coude sorti, avant-bras et poing cachés par le corps"))
out.append("ARM_BEAT_4_FIST = (5, 6)\nARM_BEAT_4_SHOULDER = (3, 0)")
out.append(hand("ARM_PUSH_4", [
    ".#d#.",
    "#hbd#",
    "#hbd#",
    ".#bd#",
    ".#bd#",
    "..##.",
], (-11, -12), "bras poussé vers l'avant vu de dos : seul le haut du bras dépasse"))
out.append("ARM_PUSH_4_FIST = (3, 5)\nARM_PUSH_4_SHOULDER = (2, 0)")

# ---------------- sommeil, effets ----------------
out.append("\n# ---- Sommeil (une seule ligne, deux images) : couché sur le flanc, tête à gauche ----")
out.append(hand("SLEEP_A", [
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
], (-14, -12), "sommeil, image 1"))
out.append("SLEEP_HEAD_MARK = (4, 7)\nSLEEP_CENTER = (14, 8)\nSLEEP_FISTS = ((11, 12), (20, 12))")
out.append(hand("SLEEP_B", [
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
], (-14, -12), "sommeil, image 2 : le dos redescend d'un rang (respiration)"))

out.append('''
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
_SLASH_D = bmp([          # frappe vers le bas-droite : trois traits « \\\\ » décalés en travers
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
    a = _SLASH_D                       # 1 : bas-droite (axe « \\\\ »)
    if direction == 3:                 # haut-droite : axe « / »
        a = a[::-1]
    elif direction == 5:               # haut-gauche : axe « \\\\ », rotation de 180°
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
''')

(ROOT / 'source/personnages/zarude_pieces.py').write_text("\n".join(out) + "\n", encoding='utf-8')
print('écrit', len("\n".join(out).splitlines()), 'lignes')
