"""Build the #0870 Falinks portrait pack from the existing SpriteCollab portrait.

Method: the published Falinks portrait is the only art source. Its background is
byte-identical to cell 0 of the canonical template, so the character layer can be
extracted exactly. Missing emotions are then authored by repainting the eyes and
adding small effects inside the portrait's own 12-colour palette, and composited
on the canonical backgrounds of portrait/0186/template.png.
"""
from pathlib import Path
import shutil

from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
REF = ROOT / "source" / "portraits_falinks" / "reference"
CANONICAL = ROOT / "portrait" / "0186" / "template.png"
OUT = ROOT / "portrait" / "0870"
OUT.mkdir(parents=True, exist_ok=True)

# The complete palette of the published Falinks portrait. No colour is invented.
K = (52, 50, 56)        # darkest outline / face plate shadow
G = (71, 71, 80)        # dark grey plate
g = (87, 87, 95)        # face plate mid grey
c = (196, 195, 176)     # pale grey highlight
R = (154, 34, 35)       # crest red
r = (203, 61, 63)       # crest light red
Y = (245, 209, 83)      # helmet light yellow
y = (213, 167, 51)      # helmet mid yellow
o = (143, 112, 32)      # helmet shadow
b = (58, 155, 202)      # eye blue outline
W = (255, 255, 255)     # eye white / glint
t = (150, 226, 227)     # eye pale cyan
BODY = {K, G, g, c, R, r, Y, y, o, b, W, t}
CHARS = {"K": K, "G": G, "g": g, "c": c, "R": R, "r": r, "Y": Y, "y": y,
         "o": o, "b": b, "W": W, "t": t, ".": None}

EMOTIONS = [
    "Normal", "Happy", "Pain", "Angry", "Worried",
    "Sad", "Crying", "Shouting", "Teary-Eyed", "Determined",
    "Joyous", "Inspired", "Surprised", "Dizzy", "Special0",
    "Special1", "Sigh", "Stunned", "Special2", "Special3",
]
UPSTREAM = {"Normal"}

# Eye boxes measured on the published portrait.
LEFT_BOX = (17, 23, 4, 6)   # x, y, width, height
RIGHT_BOX = (26, 23, 3, 6)

# Left eye, 4x6. Right eye, 3x6. "." keeps the cleared face plate.
LEFT = {
    "open": [".bb.", "btWg", "bWWb", "bWWb", "btWb", ".bb."],
    "wide": ["bbbb", "bWWb", "bWtb", "bWWb", "bWWb", "bbbb"],
    "smile": ["....", "....", ".bb.", "b..b", "....", "...."],
    "wince": ["....", "b..b", ".bb.", ".bb.", "b..b", "...."],
    "angry": ["KKKK", "KbWg", "bWWb", "bWWb", "btWb", ".bb."],
    "stern": [".KKK", "KbWg", "bWWb", "bWWb", "btWb", ".bb."],
    "sad":   ["....", "b...", "btWb", "bWWb", "btWb", ".bb."],
    "droop": ["....", "....", "bbb.", "bWWb", "btWb", ".bb."],
    "sparkle": [".bb.", "bWtg", "bWWb", "bWWb", "bWtb", ".bb."],
    "blank": [".bb.", "bWWg", "bWWb", "bWWb", "bWWb", ".bb."],
    "tiny":  [".bb.", "bttg", "btWb", "bWtb", "bttb", ".bb."],
    "swirl": [".bb.", "bWWg", "bWbb", "bbWb", "bWWb", ".bb."],
    "half":  ["....", "KKKK", "bbbb", "bWtb", "btWb", ".bb."],
    "shut":  ["....", "....", "....", "bbbb", "....", "...."],
    "glare": ["KKKK", "KbWb", "bWWb", "bWWb", "bbbb", ".bb."],
}
RIGHT = {
    "open": [".b.", "bWt", "bWt", "bWt", "btb", ".b."],
    "wide": ["bbb", "bWb", "bWt", "bWW", "bWb", "bbb"],
    "smile": ["...", "...", ".b.", "b.b", "...", "..."],
    "wince": ["...", "b.b", ".b.", ".b.", "b.b", "..."],
    "angry": ["KKK", "gWK", "bWt", "bWt", "btb", ".b."],
    "stern": ["KKK", "gWb", "bWt", "bWt", "btb", ".b."],
    "sad":   ["...", "..b", "bWt", "bWt", "btb", ".b."],
    "droop": ["...", "...", ".bb", "bWt", "btb", ".b."],
    "sparkle": [".b.", "bWt", "bWW", "bWt", "bWb", ".b."],
    "blank": [".b.", "bWW", "bWW", "bWW", "bWb", ".b."],
    "tiny":  [".b.", "btt", "bWt", "btW", "btb", ".b."],
    "swirl": [".b.", "bWW", "bbW", "bWb", "bWW", ".b."],
    "half":  ["...", "KKK", "bbb", "bWt", "btb", ".b."],
    "shut":  ["...", "...", "...", "bbb", "...", "..."],
    "glare": ["KKK", "bWK", "bWt", "bWt", "bbb", ".b."],
}


def tear(x, y0, length=4):
    """A pale tear streak in the portrait's own cyan/white swatches."""
    points = [(x, y0, t), (x, y0 + 1, W)]
    for i in range(2, length):
        points.append((x, y0 + i, W if i % 2 else t))
    points.append((x, y0 + length, t))
    return points


def sweat(x, y0):
    return [(x, y0, W), (x - 1, y0 + 1, t), (x + 1, y0 + 1, t),
            (x - 1, y0 + 2, t), (x, y0 + 2, W), (x + 1, y0 + 2, t),
            (x, y0 + 3, t)]


def sparkle(x, y0):
    return [(x, y0 - 1, W), (x - 1, y0, W), (x, y0, W), (x + 1, y0, W),
            (x, y0 + 1, W), (x - 1, y0 - 1, t), (x + 1, y0 + 1, t)]


def vein(x, y0):
    return [(x, y0, R), (x + 2, y0, R), (x + 1, y0 + 1, R),
            (x, y0 + 2, R), (x + 2, y0 + 2, R), (x + 1, y0, r), (x + 1, y0 + 2, r)]


def mouth(kind):
    """Falinks' plate has no drawn mouth; these are small plate marks only."""
    if kind == "open":
        return [(21, 31, K), (22, 31, K), (23, 31, K), (24, 31, K),
                (21, 32, K), (22, 32, K), (23, 32, K), (24, 32, K),
                (22, 33, K), (23, 33, K)]
    if kind == "small":
        return [(22, 31, K), (23, 31, K), (22, 32, K), (23, 32, K)]
    if kind == "flat":
        return [(21, 31, K), (22, 31, K), (23, 31, K), (24, 31, K)]
    if kind == "frown":
        return [(21, 32, K), (22, 31, K), (23, 31, K), (24, 32, K)]
    return []


# Per emotion: left eye, right eye, extra pixels.
SPECS = {
    "Happy": ("smile", "smile", lambda: mouth("small")),
    "Pain": ("wince", "wince", lambda: mouth("open") + tear(16, 29, 3) + sweat(31, 18)),
    "Angry": ("angry", "angry", lambda: mouth("open") + vein(11, 15)),
    "Worried": ("droop", "droop", lambda: mouth("frown") + sweat(32, 19)),
    "Sad": ("sad", "sad", lambda: mouth("frown")),
    "Crying": ("wince", "wince", lambda: mouth("open") + tear(16, 29, 5) + tear(30, 29, 5)),
    "Shouting": ("angry", "angry", lambda: mouth("open")),
    "Teary-Eyed": ("tiny", "tiny", lambda: mouth("small") + tear(30, 29, 3)),
    "Determined": ("stern", "stern", lambda: mouth("flat")),
    "Joyous": ("smile", "smile", lambda: mouth("open") + sparkle(11, 16) + sparkle(34, 17)),
    "Inspired": ("sparkle", "sparkle", lambda: mouth("small") + sparkle(33, 15)),
    "Surprised": ("wide", "wide", lambda: mouth("open")),
    "Dizzy": ("swirl", "swirl", lambda: mouth("small") + sweat(31, 18)),
    "Sigh": ("half", "half", lambda: mouth("flat") + sweat(33, 20)),
    "Stunned": ("blank", "blank", lambda: mouth("small") + sweat(31, 17)),
    # Specials: Falinks is a drilled formation Pokemon, so the four free slots
    # are a salute, a confident wink, sleep, and a full battle cry.
    "Special0": ("stern", "stern", lambda: mouth("flat") + sparkle(33, 16)),
    "Special1": ("smile", "open", lambda: mouth("small") + sparkle(11, 17)),
    "Special2": ("shut", "shut", lambda: mouth("small")),
    "Special3": ("glare", "glare", lambda: mouth("open") + vein(11, 15) + vein(31, 15)),
}


def _distance(a, b_):
    return sum((p - q) * (p - q) for p, q in zip(a, b_))


def base_art():
    """Extract the published Falinks character layer, background removed."""
    portrait = Image.open(REF / "Normal.png").convert("RGB")
    background = Image.open(CANONICAL).convert("RGB").crop((0, 0, 40, 40))
    art = Image.new("RGBA", (40, 40), (0, 0, 0, 0))
    pixels = art.load()
    for yy in range(40):
        for xx in range(40):
            colour = portrait.getpixel((xx, yy))
            if colour != background.getpixel((xx, yy)):
                pixels[xx, yy] = (*colour, 255)
    return art


def clear_eyes(art):
    """Erase only the eye artwork; the plate, helmet and crest are untouched."""
    pixels = art.load()
    for x0, y0, width, height in (LEFT_BOX, RIGHT_BOX):
        for yy in range(y0, y0 + height):
            for xx in range(x0 - 1, x0 + width + 1):
                if pixels[xx, yy][3] and pixels[xx, yy][:3] in {b, W, t}:
                    pixels[xx, yy] = (*g, 255)


def draw(art, rows, box):
    x0, y0, _, _ = box
    pixels = art.load()
    for j, row in enumerate(rows):
        for i, char in enumerate(row):
            colour = CHARS[char]
            if colour is None:
                continue
            x, yy = x0 + i, y0 + j
            if 0 <= x < 40 and 0 <= yy < 40:
                pixels[x, yy] = (*colour, 255)


def create(emotion):
    art = base_art()
    if emotion in UPSTREAM:
        return art
    left, right, extras = SPECS[emotion]
    clear_eyes(art)
    draw(art, LEFT[left], LEFT_BOX)
    draw(art, RIGHT[right], RIGHT_BOX)
    pixels = art.load()
    for x, yy, colour in extras():
        if 0 <= x < 40 and 0 <= yy < 40:
            pixels[x, yy] = (*colour, 255)
    return art


def _template_tile(emotion):
    index = EMOTIONS.index(emotion)
    template = Image.open(CANONICAL).convert("RGB")
    return template.crop(((index % 5) * 40, (index // 5) * 40,
                          (index % 5 + 1) * 40, (index // 5 + 1) * 40))


def reduce_background(tile, max_colors):
    """Deterministic, dither-free reduction: keep the most used colours of the
    canonical cell and snap the rest to the nearest kept colour. Only the two
    very rich Special backgrounds of the template ever need this."""
    colors = sorted(tile.getcolors(100000), reverse=True)
    if len(colors) <= max_colors:
        return tile, [colour for _, colour in colors]
    kept = [colour for _, colour in colors[:max_colors]]
    reduced = tile.copy()
    pixels = reduced.load()
    for yy in range(40):
        for xx in range(40):
            colour = pixels[xx, yy]
            if colour not in kept:
                pixels[xx, yy] = min(kept, key=lambda option: _distance(colour, option))
    return reduced, kept


# Body swatches ordered by how much they carry the design, for the rare
# Special backgrounds that need room under the 15-colour ceiling.
BODY_PRIORITY = [K, R, g, Y, b, W, G, y, o, r, t, c]


def compose(emotion, art):
    tile = _template_tile(emotion)
    used = {art.getpixel((x, y))[:3] for y in range(40) for x in range(40)
            if art.getpixel((x, y))[3]}
    body = [colour for colour in BODY_PRIORITY if colour in used]
    # The canonical background is never requantised: it stays byte-exact and
    # the character palette is trimmed instead, in reverse priority order.
    bg_palette = [colour for _, colour in tile.getcolors(100000)]
    if len(bg_palette) > 15:
        tile, bg_palette = reduce_background(tile, 12)
    background = tile
    if len(bg_palette) + len(body) > 15:
        body = body[:max(1, 15 - len(bg_palette))]
    allowed = bg_palette + body
    result = Image.new("RGB", (40, 40))
    rp, bp = result.load(), background.load()
    ap = art.getchannel("A").load()
    rgb = art.convert("RGB").load()
    for yy in range(40):
        for xx in range(40):
            if ap[xx, yy] == 0:
                rp[xx, yy] = bp[xx, yy]
                continue
            colour = rgb[xx, yy]
            rp[xx, yy] = colour if colour in allowed else min(
                allowed, key=lambda option: _distance(colour, option))
    return result


def main():
    for emotion in EMOTIONS:
        if emotion in UPSTREAM:
            shutil.copyfile(REF / f"{emotion}.png", OUT / f"{emotion}.png")
            image = Image.open(OUT / f"{emotion}.png").convert("RGB")
        else:
            image = compose(emotion, create(emotion))
            image.save(OUT / f"{emotion}.png")
        image.transpose(Image.Transpose.FLIP_LEFT_RIGHT).save(OUT / f"{emotion}^.png")

    sheet = Image.new("RGB", (200, 320), (0, 0, 0))
    for index, emotion in enumerate(EMOTIONS):
        image = Image.open(OUT / f"{emotion}.png").convert("RGB")
        x, y = (index % 5) * 40, (index // 5) * 40
        sheet.paste(image, (x, y))
        sheet.paste(image.transpose(Image.Transpose.FLIP_LEFT_RIGHT), (x, y + 160))
    sheet.save(OUT / "Sheet.png")
    shutil.copyfile(CANONICAL, OUT / "template.png")
    print(f"built {len(EMOTIONS)} portraits + mirrors in {OUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
