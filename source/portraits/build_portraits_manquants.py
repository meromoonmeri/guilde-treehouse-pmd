#!/usr/bin/env python3
"""Portraits d'émotions manquants pour quatre Pokémon de la guilde, au format PMDCollab.

Même démarche que `build_portraits_falinks.py` : le portrait **Normal** publié sur PMDCollab
sert de base et n'est jamais redessiné. Une émotion = trois retouches contrôlées :

1. **le fond** est repeint aux couleurs Chunsoft de l'émotion (deux teintes, dégradé haut/bas,
   rayons pour Shouting, zigzag pour Surprised). Le fond est repéré par propagation depuis le
   bord de l'image, en n'acceptant que les couleurs présentes sur ce bord : le personnage n'est
   jamais touché ;
2. **les yeux** sont modifiés par des opérations sur les pixels d'origine — fermer en arche,
   plisser, écarquiller, abaisser la paupière, éteindre la lumière, mettre une étoile ou une
   spirale — en n'employant que les couleurs déjà présentes dans l'œil et la peau qui l'entoure.
   Chaque Pokémon donne les boîtes de ses yeux (relevées sur sa base) et rien d'autre ;
3. **les effets** (goutte, larmes, marque de colère, croix, étincelles) sont posés soit sur le
   fond, soit par-dessus, dans les couleurs de la palette Chunsoft déjà utilisées par le kit.

Aucun pixel n'est peint par un générateur d'images, la palette reste ≤ 15 couleurs, et les
émotions déjà publiées sur SpriteCollab sont recopiées telles quelles pour que la planche soit
complète et importable.

Pokémon traités : Politoed #0186, Hariyama #0297, Ambipom #0424, Pawmot #0923.
Sorties dans `portraits/<nom>/`.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont
from scipy import ndimage

ROOT = Path(__file__).resolve().parents[2]
REF = ROOT / "source" / "portraits" / "reference"
SIZE = 40
MAX_COLOURS = 15

# Gabarit officiel : 5 colonnes × 4 rangées, moitié basse = versions retournées « ^ ».
EMOTIONS = ["Normal", "Happy", "Pain", "Angry", "Worried",
            "Sad", "Crying", "Shouting", "Teary-Eyed", "Determined",
            "Joyous", "Inspired", "Surprised", "Dizzy", "Special0",
            "Special1", "Sigh", "Stunned", "Special2", "Special3"]
PRODUCED = [e for e in EMOTIONS if not e.startswith("Special")]

# Fonds Chunsoft (haut, bas), relevés sur les portraits officiels — mêmes valeurs que Falinks.
# ---------------------------------------------------------------------------
# FONDS CANONIQUES
#
# Les fonds de portrait de PMDCollab ne sont ni libres ni dégradés : ce sont des **paires de
# couleurs fixes par émotion**, identiques d'un Pokémon à l'autre. Relevées ici sur les huit
# jeux de référence du dépôt (ligne 0 pour le ciel, coins bas pour le sol), en prenant la
# valeur majoritaire — les variantes à ±2 par canal viennent de retouches d'auteurs.
#
# La STRUCTURE est tout aussi canonique, et c'est là que la version précédente se trompait :
#
#   • le ciel occupe le haut sur toute la largeur, en **bandes horizontales** ;
#   • le sol occupe le bas, également en bandes horizontales ;
#   • la transition se fait par un **damier** de quelques lignes (`1.1.1.1.`), jamais par un
#     dégradé continu ni par la silhouette du ciel d'origine ;
#   • l'horizon est vers **y = 8**, donc haut dans l'image (le personnage le masque en grande
#     partie ; il n'est visible que sur les bords gauche et droit).
#
# Vérifié sur `0674/Crying`, `0674/Normal`, `0674/Sad` : les lignes 0-7 sont pleines de ciel,
# les lignes 8-12 alternent, le bas est plein de sol. L'ancienne version peignait un dégradé
# épousant le ciel d'origine, ce qui ne ressemblait à aucun portrait officiel.
# ---------------------------------------------------------------------------
HORIZON = 8          # dernière ligne de ciel plein
DAMIER = 4           # hauteur de la bande en damier sous l'horizon

BACKGROUNDS = {
    "Normal": None,                                        # base d'origine, fond non repeint
    "Happy": ((255, 255, 175), (255, 231, 119)),
    "Pain": ((119, 135, 183), (143, 207, 191)),
    "Angry": ((247, 103, 135), (223, 127, 175)),
    "Worried": ((119, 151, 191), (159, 215, 239)),
    "Sad": ((119, 151, 191), (167, 207, 223)),
    "Crying": ((111, 127, 183), (159, 215, 239)),
    "Teary-Eyed": ((247, 191, 199), (237, 132, 177)),
    "Determined": ((239, 159, 191), (247, 103, 133)),
    "Joyous": ((255, 255, 199), (255, 231, 119)),
    "Inspired": ((255, 255, 175), (255, 231, 127)),
    "Sigh": ((254, 241, 164), (255, 207, 79)),
    "Stunned": ((120, 135, 177), (163, 199, 219)),
    "Dizzy": ((151, 207, 207), (183, 215, 191)),
    "Surprised": ((223, 231, 239), (167, 207, 223)),
    "Shouting": ((135, 199, 255), (191, 247, 199)),
}
ZIGZAG = (119, 135, 175)
SALMON = (255, 143, 135)
WHITE = (255, 255, 255)


@dataclass
class Eye:
    """Boîte d'un œil sur la base, relevée à la main sur le portrait Normal."""
    x: int
    y: int
    w: int
    h: int
    side: str = "left"        # « left » = œil le plus proche, « right » = le plus éloigné


@dataclass
class Target:
    num: str
    folder: str
    label: str
    label_fr: str
    eyes: list[Eye]
    drop: tuple[int, int]                  # coin haut-gauche de la goutte de sueur (sur le fond)
    mark: tuple[int, int]                  # marque de colère
    tears: list[tuple[int, int]] = field(default_factory=list)   # départ des larmes, sous chaque œil
    sparkles: list[tuple[int, int]] = field(default_factory=list)
    note: str = ""


# Boîtes relevées sur les bases (voir apercu_reperes.png produit par ce script).
TARGETS = [
    Target("0186", "politoed", "Politoed", "Tarpaud",
           [Eye(11, 9, 9, 11, "left")], drop=(30, 1), mark=(28, 2),
           tears=[(13, 20)], sparkles=[(2, 2), (31, 3)],
           note="portrait cadré serré : un seul œil visible, très grand ; le second est hors champ"),
    Target("0297", "hariyama", "Hariyama", "Hariyama",
           [Eye(16, 18, 6, 6, "left"), Eye(7, 14, 7, 8, "right")], drop=(33, 1), mark=(30, 2),
           tears=[(18, 24), (9, 22)], sparkles=[(2, 2), (34, 2)],
           note="visage de trois quarts, œil proche à droite du bandeau"),
    Target("0424", "ambipom", "Ambipom", "Capidextre",
           [Eye(13, 22, 6, 7, "left"), Eye(24, 22, 6, 7, "right")], drop=(33, 1), mark=(30, 2),
           tears=[(14, 29), (26, 29)], sparkles=[(1, 1), (35, 1)],
           note="face franche, deux grands yeux ronds"),
    Target("0923", "pawmot", "Pawmot", "Pawmot",
           [Eye(28, 22, 5, 5, "left"), Eye(18, 22, 5, 5, "right")], drop=(6, 1), mark=(4, 2),
           tears=[(29, 27), (19, 27)], sparkles=[(7, 2), (33, 2)],
           note="portrait très rapproché : yeux petits, au-dessus du museau clair"),
]

# ---------------------------------------------------------------------------
# Opérations sur les yeux : elles n'emploient que les couleurs déjà présentes
# dans la boîte (contour, iris, lumière) et la peau qui l'entoure.
# ---------------------------------------------------------------------------
# nom : (opération, paramètre)
EYE_OPS = {
    "Happy":     ("arch", 0),        # arche « ∩ » : œil fermé, sourire des yeux
    "Joyous":    ("arch", 1),        # même arche, un pixel plus haute
    "Sigh":      ("line", 0),        # trait horizontal : paupières closes, détendues
    "Crying":    ("squeeze", 0),     # yeux serrés « > < »
    "Pain":      ("squeeze", 1),     # serrés et abaissés
    "Sad":       ("lid", 2),         # paupière rabattue de deux pixels
    "Worried":   ("lid", 1),         # paupière à peine rabattue
    "Angry":     ("slant", 1),       # coin intérieur abaissé
    "Determined":("slant", 0),       # même pente, œil resté ouvert et vif
    "Shouting":  ("slant", 2),       # pente marquée, œil grand ouvert
    "Teary-Eyed":("wet", 0),         # lumière élargie vers le bas
    "Surprised": ("shrink", 0),      # pupille réduite dans un œil écarquillé
    "Stunned":   ("blank", 0),       # lumière éteinte
    "Dizzy":     ("spiral", 0),      # spirale
    "Inspired":  ("star", 0),        # étoile
}


def load(path: Path) -> np.ndarray:
    im = Image.open(path).convert("RGBA")
    assert im.size == (SIZE, SIZE), f"{path} : {im.size}"
    a = np.array(im)
    assert (a[:, :, 3] == 255).all(), f"{path} : portrait non opaque"
    return a[:, :, :3].astype(np.uint8).copy()


# Couleurs canoniques du fond « Normal » : c'est le décor de toutes les bases officielles
# utilisées ici. Les auteurs les emploient à ±3 par canal près, d'où la tolérance.
FOND_NORMAL = ((119, 199, 215), (231, 247, 183), (215, 255, 191))
TOLERANCE = 6


def background_mask(rgb: np.ndarray) -> np.ndarray:
    """Fond = le décor canonique « Normal » de la base, repéré par ses couleurs officielles.

    Toutes les bases de ce lot sont des portraits `Normal` de PMDCollab : leur décor est donc
    la paire canonique `#77c7d7` / `#e7f7b7` (avec la variante `#d7ffbf`), aux retouches
    d'auteur près. Plutôt que de deviner le fond par propagation depuis le bord — ce qui n'en
    trouvait que 14 à 30 % et laissait des plaques de l'ancien ciel autour du personnage —, on
    part de ces **couleurs connues**, puis on ne garde que ce qui est relié au bord.

    Le rattrapage d'anticrénelage reste nécessaire : la frange entre le décor et la silhouette
    emploie des teintes intermédiaires qui ne sont dans aucune des deux listes.
    """
    # (a) les couleurs canoniques connues du décor Normal
    approx = np.zeros((SIZE, SIZE), bool)
    for colour in FOND_NORMAL:
        approx |= (np.abs(rgb.astype(int) - np.array(colour)).max(axis=2) <= TOLERANCE)

    # (b) toute couleur qui borde l'image sans jamais apparaître au centre : c'est du décor,
    #     même si l'auteur a employé une teinte hors de la paire canonique (cas de Pawmot,
    #     dont le sol est plus jaune que la référence). Les deux critères sont réunis, car
    #     pris séparément ils ne trouvaient que 6 à 30 % du fond.
    ring: set[tuple] = set()
    for line in (rgb[0], rgb[-1], rgb[:, 0], rgb[:, -1]):
        ring |= set(map(tuple, line.tolist()))
    centre = set(map(tuple, rgb[12:32, 12:32].reshape(-1, 3).tolist()))
    for colour in ring - centre:
        approx |= np.all(rgb == colour, axis=2)

    # relier au bord : un pixel de décor enfermé dans le personnage n'est pas du fond
    seen = np.zeros((SIZE, SIZE), bool)
    stack = [(y, x) for y in (0, SIZE - 1) for x in range(SIZE)] + \
            [(y, x) for x in (0, SIZE - 1) for y in range(SIZE)]
    while stack:
        y, x = stack.pop()
        if not (0 <= y < SIZE and 0 <= x < SIZE) or seen[y, x] or not approx[y, x]:
            continue
        seen[y, x] = True
        stack += [(y + 1, x), (y - 1, x), (y, x + 1), (y, x - 1)]

    # Rattrapage de l'anticrénelage : une couleur absente du carré central (donc étrangère au
    # personnage) dont presque tous les pixels touchent déjà le fond en fait partie.
    core = set(map(tuple, rgb[12:32, 12:32].reshape(-1, 3).tolist()))
    for _ in range(4):
        near = ndimage.binary_dilation(seen, np.array([[0, 1, 0], [1, 1, 1], [0, 1, 0]], bool))
        grown = False
        for colour in {tuple(v) for v in rgb.reshape(-1, 3).tolist()} - core:
            mask = np.all(rgb == colour, axis=2)
            if mask.sum() and not (mask & seen).all() and (mask & near).sum() / mask.sum() >= 0.8:
                seen |= mask
                grown = True
        if not grown:
            break
    return seen


def sky_mask(rgb: np.ndarray, bg: np.ndarray) -> np.ndarray:
    """Partie haute du fond (le « ciel »), qui reçoit la teinte claire du dégradé.

    Les fonds PMD sont ciel en haut, sol en bas, séparés par un tramage. On prend la couleur
    dominante de la première ligne de fond, puis tout le fond situé au-dessus du dernier pixel
    de cette couleur, tramage compris.
    """
    first = next((y for y in range(SIZE) if bg[y].any()), 0)
    row = [tuple(int(v) for v in c) for c in rgb[first][bg[first]]]
    if not row:
        return bg.copy()
    top_colour = max(set(row), key=row.count)
    same = bg & np.all(rgb == top_colour, axis=2)
    ys = np.nonzero(same.any(axis=1))[0]
    limit = int(ys.max()) if len(ys) else first
    return bg & (np.arange(SIZE)[:, None] <= limit)


def paint_background(rgb: np.ndarray, bg: np.ndarray, sky: np.ndarray, name: str,
                     flat: bool = False) -> dict:
    """Repeint le fond selon la **structure canonique** des portraits PMDCollab.

    Ciel plein en haut jusqu'à `HORIZON`, sol plein en bas, et entre les deux une bande de
    `DAMIER` lignes en damier — exactement ce que font les portraits officiels. L'argument
    `sky` (la forme du ciel d'origine) n'est plus utilisé pour la géométrie : c'est ce qui
    rendait les fonds précédents non canoniques, puisqu'ils épousaient la silhouette du décor
    de départ au lieu d'être horizontaux.

    `flat` : n'employer que le ciel. Le SpriteBot refuse au-delà de 15 couleurs ; quand le
    personnage partage déjà des teintes avec son décor, la paire ferait passer la planche à 16.
    On retombe alors sur un aplat, comme le font plusieurs portraits officiels.
    """
    top, bottom = BACKGROUNDS[name]
    if flat:
        bottom = top
    ys, xs = np.nonzero(bg)

    if name == "Shouting" and not flat:
        # Shouting est le seul fond radial officiel : des rayons depuis le visage.
        cx, cy = 20.0, 24.0
        for y, x in zip(ys, xs):
            secteur = int(np.floor((np.arctan2(y - cy, x - cx) + np.pi) / (2 * np.pi / 14)))
            rgb[y, x] = top if secteur % 2 == 0 else bottom
        return {"type": "rayons", "couleurs": [list(top), list(bottom)]}

    for y, x in zip(ys, xs):
        if y < HORIZON:
            rgb[y, x] = top                                   # ciel plein
        elif y < HORIZON + DAMIER:
            rgb[y, x] = top if (x + y) % 2 == 0 else bottom   # damier de transition
        else:
            rgb[y, x] = bottom                                # sol plein
    return {"type": "ciel/sol canonique" if top != bottom else "aplat",
            "couleurs": [list(top), list(bottom)],
            "horizon": HORIZON, "damier": DAMIER}


# ---------------------------------------------------------------------------
# Yeux
# ---------------------------------------------------------------------------
def eye_colours(rgb: np.ndarray, e: Eye) -> tuple[tuple, tuple, tuple]:
    """(contour, iris, lumière) : le plus sombre, le médian, le plus clair de la boîte."""
    box = rgb[e.y:e.y + e.h, e.x:e.x + e.w].reshape(-1, 3)
    uniq, counts = np.unique(box, axis=0, return_counts=True)
    lum = uniq.astype(int).sum(1)
    order = np.argsort(lum)
    outline = tuple(int(v) for v in uniq[order[0]])
    light = tuple(int(v) for v in uniq[order[-1]])
    mid = tuple(int(v) for v in uniq[order[len(order) // 2]])
    return outline, mid, light


def skin_colour(rgb: np.ndarray, e: Eye) -> tuple:
    """Couleur de peau : la plus fréquente de l'anneau d'un pixel autour de la boîte."""
    y0, y1 = max(0, e.y - 1), min(SIZE, e.y + e.h + 1)
    x0, x1 = max(0, e.x - 1), min(SIZE, e.x + e.w + 1)
    ring = []
    for y in range(y0, y1):
        for x in range(x0, x1):
            if e.x <= x < e.x + e.w and e.y <= y < e.y + e.h:
                continue
            ring.append(tuple(int(v) for v in rgb[y, x]))
    return max(set(ring), key=ring.count) if ring else (0, 0, 0)


def apply_eye(rgb: np.ndarray, e: Eye, op: str, k: int, touched: np.ndarray) -> None:
    outline, iris, light = eye_colours(rgb, e)
    skin = skin_colour(rgb, e)
    x0, y0, w, h = e.x, e.y, e.w, e.h

    def put(x, y, colour):
        if 0 <= x < SIZE and 0 <= y < SIZE:
            rgb[y, x] = colour
            touched[y, x] = True

    def clear():
        for y in range(y0, y0 + h):
            for x in range(x0, x0 + w):
                put(x, y, skin)

    mid_y = y0 + h // 2
    if op == "arch":                        # œil fermé, arche vers le haut
        clear()
        top = mid_y - 1 - k
        for i in range(w):
            t = abs(i - (w - 1) / 2) / max(1, (w - 1) / 2)
            put(x0 + i, top + int(round(t * (h // 3))), outline)
        put(x0 + w // 2, top + 1, light)
    elif op == "line":                      # paupières closes, trait détendu
        clear()
        for i in range(w):
            put(x0 + i, mid_y, outline)
        put(x0 + w // 2, mid_y + 1, light)
    elif op == "squeeze":                   # yeux serrés « > < »
        clear()
        drop = k
        for i in range(w):
            t = abs(i - (w - 1) / 2) / max(1, (w - 1) / 2)
            y = mid_y + drop - int(round((1 - t) * (h // 3)))
            put(x0 + i, y, outline)
            put(x0 + i, y + 1, outline)
    elif op == "lid":                       # paupière rabattue
        for y in range(y0, min(y0 + k + 1, y0 + h)):
            for x in range(x0, x0 + w):
                put(x, y, skin)
        for x in range(x0, x0 + w):
            put(x, y0 + k, outline)
    elif op == "slant":                     # coin intérieur abaissé (colère, résolution, cri)
        inner = range(w) if e.side == "left" else range(w - 1, -1, -1)
        for j, i in enumerate(inner):
            rows = max(0, k + 1 - (j * (k + 1)) // max(1, w - 1))
            for y in range(y0, min(y0 + rows + 1, y0 + h)):
                put(x0 + i, y, skin)
            put(x0 + i, y0 + rows, outline)
    elif op == "wet":                       # lumière mouillée, élargie vers le bas
        for y in range(y0, y0 + h):
            for x in range(x0, x0 + w):
                if tuple(int(v) for v in rgb[y, x]) == iris and y > mid_y:
                    put(x, y, light)
    elif op == "shrink":                    # pupille réduite : surprise
        for y in range(y0, y0 + h):
            for x in range(x0, x0 + w):
                c = tuple(int(v) for v in rgb[y, x])
                if c == outline and (y0 < y < y0 + h - 1) and (x0 < x < x0 + w - 1):
                    put(x, y, light)
        put(x0 + w // 2, mid_y, outline)
        put(x0 + w // 2, mid_y + 1, outline)
    elif op == "blank":                     # lumière éteinte : hébétude
        for y in range(y0, y0 + h):
            for x in range(x0, x0 + w):
                if tuple(int(v) for v in rgb[y, x]) == light:
                    put(x, y, iris)
    elif op == "spiral":                    # tournis
        clear()
        cx, cy = x0 + w // 2, mid_y
        r = min(w, h) // 2
        for i in range(w):
            for j in range(h):
                x, y = x0 + i, y0 + j
                d = max(abs(x - cx), abs(y - cy))
                if d == r or (d == max(1, r - 2) and x >= cx):
                    put(x, y, outline)
        put(cx, cy, outline)
    elif op == "star":                      # émerveillement
        clear()
        cx, cy = x0 + w // 2, mid_y
        r = min(w, h) // 2
        for d in range(-r, r + 1):
            put(cx + d, cy, light)
            put(cx, cy + d, light)
        for d in (-1, 1):
            put(cx + d, cy + d, light)
            put(cx + d, cy - d, light)
        put(cx, cy, WHITE)
    else:
        raise ValueError(op)


# ---------------------------------------------------------------------------
# Effets
# ---------------------------------------------------------------------------
def motif(text: str) -> list[str]:
    return text.strip("\n").splitlines()


DROP = motif("..o..\n.oLo.\noLLLo\noLLWo\noLWWo\n.ooo.")
ANGER = motif("..W.W..\n..W.W..\nWW...WW\n.......\nWW...WW\n..W.W..\n..W.W..")
CROSS = motif("SS..SS\nSSSSSS\n.SSSS.\n.SSSS.\nSSSSSS\nSS..SS")
SPARK = motif("..W..\n..W..\nWWWWW\n..W..\n..W..")
TEAR = motif("L\nW\nL\nL\nW")


def stamp(rgb, x0, y0, pattern, palette, mask, touched):
    for dy, line in enumerate(pattern):
        for dx, ch in enumerate(line):
            if ch == ".":
                continue
            x, y = x0 + dx, y0 + dy
            if not (0 <= x < SIZE and 0 <= y < SIZE):
                continue
            if mask is not None and not mask[y, x]:
                continue
            rgb[y, x] = palette[ch]
            touched[y, x] = True


def fit_palette(rgb: np.ndarray, base: np.ndarray, info: dict) -> np.ndarray:
    """Dernier recours pour tenir dans les 15 couleurs : les teintes d'effet ajoutées (blanc,
    saumon des croix) sont rabattues sur la couleur la plus proche déjà présente sur la base.
    Le fond et le personnage ne sont jamais touchés par cette étape."""
    allowed = colours_of(base)
    out = rgb.copy()
    current = colours_of(rgb)
    extra = [c for c in current if c not in allowed and tuple(c) not in
             {tuple(x) for pair in [info.get("fond", {}).get("couleurs", [])] for x in pair}]
    rebased = []
    for c in extra:
        if len(colours_of(out)) <= MAX_COLOURS:
            break
        near = min(allowed, key=lambda a: sum((p - q) ** 2 for p, q in zip(a, c)))
        out[np.all(out == c, axis=2)] = near
        rebased.append({"de": "#%02x%02x%02x" % c, "vers": "#%02x%02x%02x" % near})
    if rebased:
        info["couleurs_rabattues"] = rebased
    return out


def build_emotion(name: str, base: np.ndarray, t: Target, bg: np.ndarray, sky: np.ndarray,
                  flat: bool = False) -> tuple[np.ndarray, dict]:
    rgb = base.copy()
    touched = np.zeros((SIZE, SIZE), bool)
    info: dict = {"fond": None, "yeux": [], "effets": []}
    if name == "Normal":
        return rgb, info
    info["fond"] = paint_background(rgb, bg, sky, name, flat)
    if name in EYE_OPS:
        op, k = EYE_OPS[name]
        for e in t.eyes:
            apply_eye(rgb, e, op, k, touched)
            info["yeux"].append({"boite": [e.x, e.y, e.w, e.h], "cote": e.side, "operation": op, "parametre": k})

    outline, iris, light = eye_colours(base, t.eyes[0])
    pal = {"o": outline, "L": light, "W": WHITE, "S": SALMON}
    if name == "Pain":
        stamp(rgb, *t.drop, DROP, pal, None, touched)
        info["effets"].append("goutte de sueur")
    if name == "Sigh":
        stamp(rgb, *t.drop, DROP, pal, None, touched)
        info["effets"].append("soupir : goutte")
    if name == "Stunned":
        stamp(rgb, *t.drop, DROP, pal, None, touched)
        info["effets"].append("hébétude : goutte")
    if name == "Angry":
        stamp(rgb, *t.mark, ANGER, pal, None, touched)
        info["effets"].append("marque de colère")
    if name in ("Crying", "Teary-Eyed"):
        n = len(TEAR) if name == "Crying" else 2
        for x, y in t.tears:
            stamp(rgb, x, y, TEAR[:n], pal, None, touched)
        info["effets"].append("larmes")
    if name == "Joyous":
        for x in (1, 33):
            stamp(rgb, x, 1, CROSS, pal, bg, touched)
        info["effets"].append("croix de joie sur le fond")
    if name == "Inspired":
        for x, y in t.sparkles:
            stamp(rgb, x, y, SPARK, pal, bg, touched)
        info["effets"].append("étincelles sur le fond")
    info["pixels_retouches_hors_fond"] = int(touched.sum())
    return rgb, info


# ---------------------------------------------------------------------------
# Exports
# ---------------------------------------------------------------------------
def font(size: int):
    try:
        return ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", size)
    except OSError:
        return ImageFont.load_default()


def to_image(rgb: np.ndarray) -> Image.Image:
    return Image.fromarray(np.dstack([rgb, np.full((SIZE, SIZE), 255, np.uint8)]).astype(np.uint8), "RGBA")


def colours_of(rgb: np.ndarray) -> list[tuple]:
    return sorted({tuple(int(v) for v in c) for c in rgb.reshape(-1, 3)})


def contact_sheet(images: dict, title: str, subtitle: str, path: Path) -> None:
    zoom, cols = 4, 4
    cw, ch = SIZE * zoom + 24, SIZE * zoom + 40
    rows = -(-len(PRODUCED) // cols)
    out = Image.new("RGBA", (cols * cw + 24, rows * ch + 76), (26, 26, 46, 255))
    d = ImageDraw.Draw(out)
    d.text((24, 18), title, fill=(240, 240, 240, 255), font=font(20))
    d.text((24, 46), subtitle, fill=(170, 170, 200, 255), font=font(13))
    for i, n in enumerate(PRODUCED):
        x, y = 24 + (i % cols) * cw, 76 + (i // cols) * ch
        out.paste(images[n].resize((SIZE * zoom, SIZE * zoom), Image.NEAREST), (x, y))
        cnt = len(colours_of(np.array(images[n])[:, :, :3]))
        d.text((x, y + SIZE * zoom + 6), f"{n}  ·  {cnt} couleurs", fill=(230, 230, 230, 255), font=font(13))
    out.save(path, optimize=True)


def marks_sheet(base: np.ndarray, t: Target, bg: np.ndarray, path: Path) -> None:
    zoom = 8
    img = to_image(base).resize((SIZE * zoom, SIZE * zoom), Image.NEAREST).convert("RGBA")
    d = ImageDraw.Draw(img, "RGBA")
    mask = Image.new("RGBA", img.size, (0, 0, 0, 0))
    md = ImageDraw.Draw(mask)
    for y in range(SIZE):
        for x in range(SIZE):
            if bg[y, x]:
                md.rectangle([x * zoom, y * zoom, (x + 1) * zoom - 1, (y + 1) * zoom - 1], fill=(255, 0, 255, 70))
    img.alpha_composite(mask)
    for e in t.eyes:
        d.rectangle([e.x * zoom, e.y * zoom, (e.x + e.w) * zoom - 1, (e.y + e.h) * zoom - 1],
                    outline=(0, 255, 255, 255), width=2)
    out = Image.new("RGBA", (img.width, img.height + 48), (26, 26, 46, 255))
    out.alpha_composite(img, (0, 48))
    dd = ImageDraw.Draw(out)
    dd.text((8, 8), f"{t.label} #{t.num} — repères de retouche", fill=(240, 240, 240, 255), font=font(15))
    dd.text((8, 28), "cyan : boîtes des yeux · magenta : fond détecté (repeint par émotion)",
            fill=(170, 170, 200, 255), font=font(12))
    out.save(path, optimize=True)


def spritebot_sheet(images: dict, flips: dict) -> Image.Image:
    sheet = Image.new("RGBA", (200, 320), (0, 0, 0, 0))
    for i, name in enumerate(EMOTIONS):
        if name in images:
            sheet.paste(images[name], ((i % 5) * 40, (i // 5) * 40))
            sheet.paste(flips[name], ((i % 5) * 40, 160 + (i // 5) * 40))
    return sheet


def credits(t: Target, out: Path, existing: list[str]) -> None:
    src = (REF / t.num / "credits.txt").read_text(encoding="utf-8").rstrip("\n").splitlines()
    lines = [f"# {t.label} #{t.num} — portraits d'émotions complétés à partir du portrait Normal officiel",
             "# Lignes d'origine du dépôt SpriteCollab, conservées :"] + src + [
        "2026-09-07 00:00:00.000000\tGuilde Treehouse (retouche pixel scriptée, base non redessinée)\tCUR\tCC_BY-NC_4\t"
        + ",".join(n for n in PRODUCED if n not in existing),
        "",
        f"Base : portrait Normal de https://sprites.pmdcollab.org/#/{t.num} — crédits et licence ci-dessus.",
        f"Émotions déjà publiées et reprises telles quelles : {', '.join(existing) if existing else 'aucune'}.",
        "Les émotions ajoutées ne sont ni soumises ni approuvées sur SpriteCollab.",
    ]
    (out / "credits.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")


def build_one(t: Target) -> dict:
    out = ROOT / "portraits" / t.folder
    (out / "emotions").mkdir(parents=True, exist_ok=True)
    base = load(REF / t.num / "Normal.png")
    bg = background_mask(base)
    sky = sky_mask(base, bg)
    existing = sorted(p.stem for p in (REF / t.num).glob("*.png") if "^" not in p.stem and p.stem in PRODUCED)

    images, flips, infos = {}, {}, {}
    for name in PRODUCED:
        official = REF / t.num / f"{name}.png"
        if official.is_file():
            rgb = load(official)
            info = {"origine": "portrait officiel PMDCollab, repris tel quel"}
        else:
            rgb, info = build_emotion(name, base, t, bg, sky)
            if len(colours_of(rgb)) > MAX_COLOURS:      # aplat de repli, voir paint_background
                rgb, info = build_emotion(name, base, t, bg, sky, flat=True)
            if len(colours_of(rgb)) > MAX_COLOURS:      # puis rabattement des couleurs d'effet
                rgb, info = build_emotion(name, base, t, bg, sky, flat=True)
                rgb = fit_palette(rgb, base, info)
            info["origine"] = "retouche de la base Normal"
        pal = colours_of(rgb)
        assert len(pal) <= MAX_COLOURS, f"{t.num} {name} : {len(pal)} couleurs"
        info["couleurs"] = len(pal)
        info["palette"] = ["#%02x%02x%02x" % c for c in pal]
        images[name] = to_image(rgb)
        flips[name] = to_image(rgb[:, ::-1].copy())
        images[name].save(out / "emotions" / f"{name}.png", optimize=True)
        flips[name].save(out / "emotions" / f"{name}^.png", optimize=True)
        infos[name] = info

    sheet = spritebot_sheet(images, flips)
    sheet.save(out / "planche_spritebot.png", optimize=True)
    sheet.crop((0, 0, 200, 160)).save(out / "planche_spritebot_160.png", optimize=True)
    contact_sheet(images, f"{t.label.upper()} #{t.num} — PORTRAITS D'ÉMOTIONS PMD (×4)",
                  f"Base : portrait Normal PMDCollab · {len(PRODUCED)} émotions · 40 × 40 px · 15 couleurs max · {t.note}",
                  out / "apercu.png")
    marks_sheet(base, t, bg, out / "apercu_reperes.png")
    credits(t, out, existing)

    kit = {
        "pokemon": {"numero": t.num, "nom": t.label, "nom_fr": t.label_fr, "forme": "0000",
                    "source": f"https://sprites.pmdcollab.org/#/{t.num}?form=0"},
        "methode": "retouche pixel de la base Normal : fond Chunsoft repeint par propagation depuis le bord, "
                   "yeux transformés par opérations sur leurs propres couleurs, effets de la palette du kit",
        "format": {"portrait": [SIZE, SIZE], "planche": [200, 320], "grille": [5, 8], "ordre": EMOTIONS,
                   "moitie_basse": "versions retournées « ^ » : miroir horizontal exact",
                   "cases_vides": ["Special0", "Special1", "Special2", "Special3"]},
        "yeux": [{"boite": [e.x, e.y, e.w, e.h], "cote": e.side} for e in t.eyes],
        "operations": {k: list(v) for k, v in EYE_OPS.items()},
        "emotions_officielles_reprises": existing,
        "emotions": infos,
        "note": t.note,
    }
    (out / "kit.json").write_text(json.dumps(kit, ensure_ascii=False, indent=1), encoding="utf-8")
    return {"num": t.num, "nom": t.label, "produits": len(images), "reprises": len(existing),
            "dossier": str(out.relative_to(ROOT))}


def main() -> None:
    for t in TARGETS:
        r = build_one(t)
        print(f"#{r['num']} {r['nom']:10s} : {r['produits']} portraits (+ ^), dont {r['reprises']} officiels repris → {r['dossier']}")


if __name__ == "__main__":
    main()
