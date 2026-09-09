"""Effets Dynamax dessinés en pixel art (1:1, agrandis ensuite avec le sprite) : nuages-cyclones animés, aura
ondulante, colonne d'énergie et éclairs de la transformation.

Design d'après les planches du générateur d'images `source/personnages/reference/dynamax/concept_*.png`
(nuages = volutes à cœur clair, aura = anneau plein + anneau tramé, transformation = rayon fin → colonne opaque
enroulée d'éclairs → flash → silhouette → géant). Le générateur ne fournit que le brouillon : tout ici est
redessiné à la main sur la grille, dans quatre couleurs.
"""
from __future__ import annotations

import math

import numpy as np

# Palette des effets (l'aura intégrée aux sprites n'utilise que FX_RED et FX_LIGHT)
FX_DARK = (20, 8, 16)         # contour des nuages
FX_CRIMSON = (138, 12, 48)    # cœur de colonne, corps des éclairs
FX_RED = (232, 40, 72)        # aura, nuages, colonne
FX_LIGHT = (255, 144, 128)    # trame de l'aura, reflets, bord des éclairs
FX_WHITE = (255, 236, 232)    # flash, cœur de la colonne au moment du flash

KEY = {"d": FX_DARK, "c": FX_CRIMSON, "r": FX_RED, "l": FX_LIGHT, "w": FX_WHITE}


def bmp(rows: list[str], dark: tuple[int, int, int] | None = None) -> np.ndarray:
    h, w = len(rows), max(len(r) for r in rows)
    out = np.zeros((h, w, 4), np.uint8)
    key = dict(KEY)
    if dark is not None:
        key["d"] = dark
    for y, row in enumerate(rows):
        for x, ch in enumerate(row):
            if ch in key:
                out[y, x] = (*key[ch], 255)
    return out


# ---------------------------------------------------------------------------
# Nuages-cyclones : trois phases de la volute (le cœur tourne d'un tiers de tour), deux tailles
# ---------------------------------------------------------------------------
CLOUD_LARGE = [[
    "......ddddd......",
    "...dddrllrrdd....",
    "..drllrrrrrrrdd..",
    ".drlrrrdddddrrrd.",
    ".drrrrdrrrrrdrrrd",
    "drrrrdrrdddrdrrrd",
    "drrrrdrrdlddrrrrd",
    ".drrrrdrrrrrrrrd.",
    ".ddrrrddddrrrrdd.",
    "...ddrrrrrrrddd..",
    ".....ddddddd.....",
], [
    "......ddddd......",
    "...dddrllrrdd....",
    "..drlrrrrrrrrdd..",
    ".drrrddddddrrrrd.",
    ".drrdrrrrrrddrrrd",
    "drrdrrdddrrrdrrrd",
    "drrdrrdlddrrdrrrd",
    ".drrdrrrrrrrdrrd.",
    ".ddrrdddddddrrdd.",
    "...ddrrrrrrrddd..",
    ".....ddddddd.....",
], [
    "......ddddd......",
    "...dddrllrrdd....",
    "..drlrrrrrrrrdd..",
    ".drrrrrrrrrrrrrd.",
    ".drrdddddddddrrrd",
    "drrdrrrrrrrrrdrrd",
    "drrdrrdddddrrdrrd",
    ".drrdrrrdlrrrdrd.",
    ".ddrrdrrrrrrddrd.",
    "...ddrrdddddddd..",
    ".....ddddddd.....",
]]
CLOUD_SMALL = [[
    "....ddddd...",
    "..ddrllrrdd.",
    ".drrrdddrrrd",
    "drrrdrrrdrrd",
    "drrrdrldrrrd",
    ".drrrdddrrd.",
    ".ddrrrrrrdd.",
    "...dddddd...",
], [
    "....ddddd...",
    "..ddrllrrdd.",
    ".drrrrrrrrrd",
    "drrddddddrrd",
    "drrdrrrldrrd",
    ".drrddddrrd.",
    ".ddrrrrrrdd.",
    "...dddddd...",
], [
    "....ddddd...",
    "..ddrllrrdd.",
    ".drrdddddrrd",
    "drrdrrrrrdrd",
    "drrdrldddrrd",
    ".drrdrrrrrd.",
    ".ddrddddddd.",
    "...dddddd...",
]]

# Traînée derrière chaque nuage : streak effilé, dessiné pour un nuage qui s'éloigne vers la droite (traînée à sa
# gauche) ; retourner horizontalement pour l'autre sens
TRAIL = bmp(["...rrrr", "rrrr..."])
TRAIL_SMALL = bmp(["..rr", "rr.."])


def clouds(small: bool, dark: tuple[int, int, int] | None = None) -> list[np.ndarray]:
    return [bmp(rows, dark) for rows in (CLOUD_SMALL if small else CLOUD_LARGE)]


def cloud_ring(t: int, total: int, direction: int, n_clouds: int = 3) -> list[tuple[float, int]]:
    """Positions angulaires des nuages à l'instant t d'une animation de durée `total` (ticks).

    Retourne (angle, phase) par nuage. Les nuages avancent d'un tiers de tour par cycle — la boucle est continue
    (chaque nuage prend la place du suivant) — et la volute change de phase toutes les 1/9 de tour, ce qui fait
    tourner la spirale sur elle-même trois fois par cycle. Décalage d'un douzième de tour par direction pour que
    les huit lignes de la feuille diffèrent.
    """
    frac = (t / total) if total else 0.0
    base = -math.pi / 2 + direction * math.pi / 12 + (2 * math.pi / 3) * frac
    out = []
    for k in range(n_clouds):
        ang = base + k * 2 * math.pi / n_clouds
        phase = (int(frac * 9) + k) % 3
        out.append((ang, phase))
    return out


# ---------------------------------------------------------------------------
# Aura ondulante : quatre phases d'un motif de trame qui « monte » le long de la silhouette
# ---------------------------------------------------------------------------
def aura_rings(mask: np.ndarray, dilate) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    d1 = dilate(mask)
    d2 = dilate(d1)
    d3 = dilate(d2)
    return d1 & ~mask, d2 & ~d1, d3 & ~d2


def aura(mask: np.ndarray, phase: int, dilate) -> np.ndarray:
    """Anneau plein (rouge) + anneau tramé (clair) + langues extérieures clairsemées qui remontent.

    `phase` 0..3 : le motif de la trame est décalé d'un pixel vers le haut à chaque phase, ce qui donne un
    flux ascendant continu sur quatre images ; les langues (troisième anneau, un pixel sur quatre) ondulent
    en opposition de phase.
    """
    ring1, ring2, ring3 = aura_rings(mask, dilate)
    yy, xx = np.indices(mask.shape)
    out = np.zeros((*mask.shape, 4), np.uint8)
    out[ring1] = (*FX_RED, 255)
    flow = ((xx + yy + phase) % 2) == 0
    out[ring2 & flow] = (*FX_LIGHT, 255)
    out[ring2 & ~flow & (((yy + phase) % 4) == 0)] = (*FX_RED, 255)      # points rouges dans les creux de la trame
    tongues = ((xx * 3 + yy + 2 * phase) % 7) == 0
    out[ring3 & tongues] = (*FX_RED, 255)
    return out


# ---------------------------------------------------------------------------
# Transformation : rayon, colonne d'énergie, éclairs, flash, silhouette
# ---------------------------------------------------------------------------
def beam(width: int, height: int, phase: int) -> np.ndarray:
    """Rayon fin descendant : bande claire avec cœur blanc, bords rouges, stries animées."""
    out = np.zeros((height, width, 4), np.uint8)
    for x in range(width):
        edge = x == 0 or x == width - 1
        for y in range(height):
            if edge:
                out[y, x] = (*FX_RED, 255)
            elif width >= 5 and (x == width // 2) and ((y + phase) % 3 != 0):
                out[y, x] = (*FX_WHITE, 255)
            else:
                out[y, x] = (*FX_LIGHT, 255)
    return out


def column(width: int, height: int, phase: int, white: bool = False) -> np.ndarray:
    """Colonne d'énergie opaque, structure verticale : bord clair (1 px) | bande rouge | cœur cramoisi avec un
    filet sombre au centre | bande rouge | bord clair. Des étincelles claires coulent dans les bandes rouges
    (période 6 px, deux pixels de descente par phase). `white` : colonne surexposée (flash)."""
    out = np.zeros((height, width, 4), np.uint8)
    band = max(2, width // 4)
    core0, core1 = band, width - band
    mid = width // 2
    for y in range(height):
        for x in range(width):
            if x == 0 or x == width - 1:
                col = FX_LIGHT if not white else FX_WHITE
            elif x < core0 or x >= core1:
                flowing = ((y - 2 * phase + 3 * (x % 2)) % 6) == 0
                col = (FX_LIGHT if flowing else FX_RED) if not white else (FX_WHITE if flowing else FX_LIGHT)
            elif x == mid and width >= 9:
                col = FX_DARK if not white else FX_LIGHT
            else:
                col = FX_CRIMSON if not white else FX_LIGHT
            out[y, x] = (*col, 255)
    return out


def bolt(points: list[tuple[int, int]], thick: int, canvas: np.ndarray, dark: tuple[int, int, int] = FX_CRIMSON) -> None:
    """Éclair épais et opaque : polyligne en segments, corps cramoisi, bord clair (1 px de chaque côté)."""
    def plot(x0, y0, x1, y1, colour, t):
        dx, dy = x1 - x0, y1 - y0
        n = max(abs(dx), abs(dy), 1)
        for k in range(n + 1):
            x = x0 + round(dx * k / n)
            y = y0 + round(dy * k / n)
            for ox in range(-(t // 2), t - t // 2):
                for oy in range(-(t // 2), t - t // 2):
                    px, py = x + ox, y + oy
                    if 0 <= px < canvas.shape[1] and 0 <= py < canvas.shape[0]:
                        canvas[py, px] = (*colour, 255)
    for (x0, y0), (x1, y1) in zip(points, points[1:]):
        plot(x0, y0, x1, y1, FX_LIGHT, thick + 2)
    for (x0, y0), (x1, y1) in zip(points, points[1:]):
        plot(x0, y0, x1, y1, dark, thick)


def spiral_bolt(cx: int, top: int, bottom: int, rx: int, ry: int, turns: float, phase: float, n: int = 10,
                jitter: int = 5) -> tuple[list[tuple[int, int]], list[bool]]:
    """Points d'un éclair en zigzag qui s'enroule en hélice autour de la colonne en descendant de `top` à `bottom`.

    Le zigzag alterne de part et d'autre de l'hélice (± jitter px) ; retourne les points et, pour chacun, s'il est
    devant la colonne (sin > 0)."""
    pts, front = [], []
    for k in range(n + 1):
        f = k / n
        ang = phase + f * turns * 2 * math.pi
        side = 0 if k in (0, n) else (1 if k % 2 else -1)
        x = int(round(cx + rx * math.cos(ang))) + side * (jitter if k % 3 else jitter // 2)
        y = int(round(top + (bottom - top) * f + ry * math.sin(ang))) + (side * 2 if 0 < k < n else 0)
        pts.append((x, y))
        front.append(math.sin(ang) > 0)
    return pts, front


def filled_ellipse(canvas: np.ndarray, cx: int, cy: int, rx: int, ry: int, colour: tuple[int, int, int]) -> None:
    yy, xx = np.indices(canvas.shape[:2])
    m = ((xx - cx) / max(rx, 1)) ** 2 + ((yy - cy) / max(ry, 1)) ** 2 <= 1.0
    canvas[m] = (*colour, 255)


def ellipse_ring(canvas: np.ndarray, cx: int, cy: int, rx: int, ry: int, thickness: int, colour: tuple[int, int, int]) -> None:
    yy, xx = np.indices(canvas.shape[:2])
    d = np.sqrt(((xx - cx) / max(rx, 1)) ** 2 + ((yy - cy) / max(ry, 1)) ** 2)
    m = (d <= 1.0) & (d >= 1.0 - thickness / max(rx, 1))
    canvas[m] = (*colour, 255)


def flash_burst(cx: int, cy: int, radius: int, spikes: int, phase: int, canvas: np.ndarray, thickness: int = 2) -> None:
    """Éclat en étoile : rayons alternés blancs / clairs partant du centre, longueur variant avec la phase."""
    for k in range(spikes):
        ang = k * 2 * math.pi / spikes + phase * 0.2
        length = radius if k % 2 == 0 else radius * 2 // 3
        length = max(3, length - (phase % 2) * 2)
        x1 = int(round(cx + length * math.cos(ang)))
        y1 = int(round(cy + length * 0.6 * math.sin(ang)))
        colour = FX_WHITE if k % 2 == 0 else FX_LIGHT
        dx, dy = x1 - cx, y1 - cy
        n = max(abs(dx), abs(dy), 1)
        for s in range(n + 1):
            px = cx + round(dx * s / n)
            py = cy + round(dy * s / n)
            t = thickness if s < n // 2 else max(1, thickness - 1)
            for ox in range(t):
                for oy in range(t):
                    if 0 <= px + ox < canvas.shape[1] and 0 <= py + oy < canvas.shape[0]:
                        canvas[py + oy, px + ox] = (*colour, 255)


def silhouette(mask: np.ndarray, colour: tuple[int, int, int], outline: tuple[int, int, int], dilate) -> np.ndarray:
    out = np.zeros((*mask.shape, 4), np.uint8)
    out[dilate(mask) & ~mask] = (*outline, 255)
    out[mask] = (*colour, 255)
    return out
