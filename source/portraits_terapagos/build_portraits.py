"""Build the Terapagos #1024 Stellar form portrait pack.

Upstream state, checked on SpriteCollab:
  portrait/1024/0002 (Stellar) has ONLY Normal.png and Normal^.png.
  portrait/1024/0001 (Terastal) has a few more emotions by the same artist.

So the Stellar Normal portrait is the single art source. Every missing emotion
is derived from it: the crystalline body is preserved pixel for pixel and only
the eye is repainted, following the vocabulary the Terastal artist actually
uses (the eye is the sole expressive feature; the shell never deforms).

No AI generated pixel enters this pack.
"""
from pathlib import Path
import shutil

from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
REF = Path(__file__).resolve().parent / "reference"
CANONICAL = ROOT / "portrait" / "0186" / "template.png"
OUT = ROOT / "portrait" / "1024"

# Stellar palette, read from the published portrait. Nothing else is allowed.
K = (47, 0, 127)        # deep violet outline
d = (68, 76, 157)       # shell mid violet
b = (86, 106, 192)      # shell blue
c = (49, 165, 206)      # cyan
C = (100, 199, 238)     # light cyan
p = (154, 86, 213)      # purple facet
W = (255, 255, 255)     # white / sclera
w = (207, 223, 255)     # pale blue white
v = (223, 247, 255)     # palest highlight
g = (143, 215, 151)      # green facet
B = (119, 167, 223)     # blue grey
G = (191, 231, 159)     # light green
y = (255, 231, 175)     # warm cream
L = (215, 255, 190)     # pale green
M = (221, 78, 151)      # magenta accent, used on the eye rim

SLOTS = [
    "Normal", "Happy", "Pain", "Angry", "Worried",
    "Sad", "Crying", "Shouting", "Teary-Eyed", "Determined",
    "Joyous", "Inspired", "Surprised", "Dizzy", None,
    None, "Sigh", "Stunned", None, None,
]
EMOTIONS = [slot for slot in SLOTS if slot]
UPSTREAM = {"Normal"}

# The eye of the Stellar portrait, read off the published pixels.
# Rows 24..30, columns 12..17. The magenta rim at column 11 and the violet
# outline around the socket belong to the shell and are never touched.
#
# Published eye (x12..x17):
#   y24  bCcKbd     y25  CGbbKb     y26  GbCwKB     y27  GcCWpK
#   y28  CcWWCK     y29  cWCWcd     y30  KpCwpM
#
# Every pattern below keeps that 6x7 footprint and the same colour language:
# cyan body, white highlight, violet lid. "." keeps the published pixel.
EYE_X, EYE_Y = 12, 24
CHARS = {"K": K, "d": d, "b": b, "c": c, "C": C, "p": p, "W": W, "w": w,
         "v": v, "g": g, "B": B, "G": G, "y": y, "L": L, "M": M, ".": None}

EYES = {
    # The published open eye, used verbatim for Normal.
    "normal": ["bCcKbd", "CGbbKb", "GbCwKB", "GcCWpK",
               "CcWWCK", "cWCWcd", "KpCwpM"],
    # Lid closed into a gentle arc: the cyan body is replaced by shell violet,
    # a thin violet lash line keeps the eye readable.
    "smile":  ["dddKbd", "KKdbKb", "dKKwKB", "ddKKpK",
               "CcKKCK", "cWCWcd", "KpCwpM"],
    # Squeezed shut, lash line pinched upward.
    "squint": ["dddKbd", "KKKbKb", "dKdwKB", "KddKpK",
               "cKKKCK", "cWCWcd", "KpCwpM"],
    # Lid lowered from the top: upper third becomes shell, pupil stays.
    "narrow": ["dddKbd", "KKdbKb", "GbCwKB", "GcCWpK",
               "CcWWCK", "cWCWcd", "KpCwpM"],
    # Opened wider: the highlight grows and the lower lid drops.
    "wide":   ["bCCKbd", "CWCbKb", "CWWwKB", "CWWWpK",
               "CWWWCK", "cWCWcd", "KpCwpM"],
    # Half closed and sagging.
    "droop":  ["dddKbd", "KKdbKb", "dKCwKB", "GcCWpK",
               "CcWWCK", "cWCWcd", "KpCwpM"],
    # Fully shut, a single dark lid line.
    "shut":   ["dddKbd", "dddbKb", "KKKwKB", "dddKpK",
               "ddddCK", "cWCWcd", "KpCwpM"],
    # Weary, lid at mid height.
    "half":   ["dddKbd", "KKdbKb", "dCCwKB", "GcCWpK",
               "CcWWCK", "cWCWcd", "KpCwpM"],
    # Dazed: the highlight is broken into a small swirl.
    "spiral": ["bCcKbd", "CWCbKb", "GWcwKB", "GcWWpK",
               "CWcWCK", "cWCWcd", "KpCwpM"],
    # Vacant: the iris detail is flattened to plain white.
    "blank":  ["bWWKbd", "WWWbKb", "WWWwKB", "WWWWpK",
               "WWWWCK", "cWWWcd", "KpCwpM"],
    # Welling up: extra pale highlight, iris pushed down.
    "glossy": ["bCvKbd", "CvWbKb", "vWCwKB", "GWvWpK",
               "CvWWCK", "cWvWcd", "KpCwpM"],
    # Lit from within, a bright star glint.
    "shine":  ["bCcKbd", "CWWbKb", "GWvwKB", "GWWWpK",
               "CcWWCK", "cWCWcd", "KpCwpM"],
}

# Which eye each emotion uses, plus optional small effects.
SPECS = {
    "Happy": ("smile", []),
    "Pain": ("squint", ["sweat"]),
    "Angry": ("narrow", ["brow"]),
    "Worried": ("droop", ["sweat"]),
    "Sad": ("droop", []),
    "Crying": ("shut", ["tears"]),
    "Shouting": ("narrow", ["brow"]),
    "Teary-Eyed": ("glossy", []),
    "Determined": ("narrow", []),
    "Joyous": ("smile", ["sparkle"]),
    "Inspired": ("shine", ["sparkle"]),
    "Surprised": ("wide", []),
    "Dizzy": ("spiral", []),
    "Sigh": ("half", []),
    "Stunned": ("blank", []),
}


def _distance(a, b_):
    return sum((x - y) * (x - y) for x, y in zip(a, b_))


EFFECTS = {
    "sweat": [(24, 20, W), (23, 21, v), (25, 21, v),
              (23, 22, v), (24, 22, W), (25, 22, v), (24, 23, v)],
    "tears": [(12, 32, v), (12, 33, v), (12, 34, v), (13, 35, v),
              (11, 32, C), (11, 34, C)],
    "brow":  [(11, 21, K), (12, 21, K), (13, 22, K), (14, 22, K), (15, 23, K)],
    "sparkle": [(26, 16, W), (25, 17, W), (26, 17, W), (27, 17, W), (26, 18, W),
                (25, 16, v), (27, 18, v)],
}


def draw_effect(pixels, name, mirrored=False):
    """Small PMD effect marks, drawn only in the Stellar palette."""
    for x, y, colour in EFFECTS[name]:
        if mirrored:
            x = 39 - x
        if 0 <= x < 40 and 0 <= y < 40:
            pixels[x, y] = colour


def create(emotion, mirrored=False):
    """Repaint only the eye of the published Stellar portrait.

    The upstream Normal^ is NOT a mechanical flip of Normal: the artist
    hand-adjusted 54 pixels. So the mirrored pack is built on top of the
    published Normal^, with the eye pattern mirrored in place, which keeps
    those hand corrections instead of discarding them.
    """
    base = "Normal^.png" if mirrored else "Normal.png"
    portrait = Image.open(REF / base).convert("RGB")
    if emotion in UPSTREAM:
        return portrait
    eye, effects = SPECS[emotion]
    image = portrait.copy()
    pixels = image.load()
    for row, line in enumerate(EYES[eye]):
        for col, char in enumerate(line):
            colour = CHARS[char]
            if colour is None:
                continue
            x, y = EYE_X + col, EYE_Y + row
            if mirrored:
                x = 39 - x
            if 0 <= x < 40 and 0 <= y < 40:
                pixels[x, y] = colour
    for effect in effects:
        draw_effect(pixels, effect, mirrored)
    return image


def reduce_colors(image, max_colors=15):
    """Deterministic, dither-free reduction onto the most used colours."""
    colors = sorted(image.getcolors(100000), reverse=True)
    if len(colors) <= max_colors:
        return image
    kept = [colour for _, colour in colors[:max_colors]]
    result = image.copy()
    pixels = result.load()
    for y in range(40):
        for x in range(40):
            colour = pixels[x, y]
            if colour not in kept:
                pixels[x, y] = min(kept, key=lambda option: _distance(colour, option))
    return result


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    for emotion in EMOTIONS:
        if emotion in UPSTREAM:
            shutil.copyfile(REF / "Normal.png", OUT / "Normal.png")
            shutil.copyfile(REF / "Normal^.png", OUT / "Normal^.png")
            continue
        reduce_colors(create(emotion)).save(OUT / f"{emotion}.png")
        reduce_colors(create(emotion, mirrored=True)).save(OUT / f"{emotion}^.png")

    sheet = Image.new("RGB", (200, 320), (0, 0, 0))
    for index, emotion in enumerate(SLOTS):
        if emotion is None:
            continue
        image = Image.open(OUT / f"{emotion}.png").convert("RGB")
        flipped = Image.open(OUT / f"{emotion}^.png").convert("RGB")
        x, y = (index % 5) * 40, (index // 5) * 40
        sheet.paste(image, (x, y))
        sheet.paste(flipped, (x, y + 160))
    sheet.save(OUT / "Sheet.png")

    (OUT / "credits.txt").write_text(
        "2024-03-30 00:51:22.215838\t<@!350050109741858829>\tCUR\tCC_BY-NC_4\tNormal,Normal^\n"
        "2026-09-15\tArena.ai Agent for meromoonmeri\tNEW\tUnspecified\t"
        + ",".join(e for e in EMOTIONS if e not in UPSTREAM)
        + " and mirrored portraits\n"
    )
    print(f"built {len(EMOTIONS)} Stellar portraits + mirrors in {OUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
