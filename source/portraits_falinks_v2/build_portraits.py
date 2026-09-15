"""Build the #0870 Falinks portrait pack, version 2 (image generator route).

Pipeline, following the PMD Portraits for SkyTemple guide:
  1. draw BIG: reference/big_expressions.png is a 1024x1024 pixel-art sheet,
     16 cells of 256x256, generated from the published portrait as reference;
  2. turn the drawing into a sprite: each cell is snapped back to the native
     pixel grid of the generated art, cropped on the character, rescaled so the
     head matches the canonical portrait's bounding box, and reduced to 40x40;
  3. lock the style: every pixel is snapped to the 12 colours of the published
     Falinks portrait, so no colour outside the canonical palette survives;
  4. composite on the canonical backgrounds of portrait/0186/template.png.

Version 1, derived directly from the published portrait, is kept untouched in
portrait/0870_v1_derive/.
"""
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
REF = ROOT / "source" / "portraits_falinks" / "reference" / "Normal.png"
GUIDE = HERE / "reference" / "big_expressions_v4.png"
# The v2 sheet is kept: the user validated four of its portraits.
GUIDE_V2 = HERE / "reference" / "big_expressions.png"
CANONICAL = ROOT / "portrait" / "0186" / "template.png"
OUT = ROOT / "portrait" / "0870"

CELL = 256
GRID = 4
# Native pixel size of the generated art, measured on the sheet.
BLOCK = 5

# SpriteBot slot order. The four Special slots are deliberately left empty:
# the SpriteCollab FAQ requires a Special to be genuinely unique and refuses
# anything describable as "another emotion on a different background".
SLOTS = [
    "Normal", "Happy", "Pain", "Angry", "Worried",
    "Sad", "Crying", "Shouting", "Teary-Eyed", "Determined",
    "Joyous", "Inspired", "Surprised", "Dizzy", None,
    None, "Sigh", "Stunned", None, None,
]
EMOTIONS = [slot for slot in SLOTS if slot]
# Order of the 16 studies on the generated sheet.
GUIDE_ORDER = [
    "Normal", "Happy", "Pain", "Angry",
    "Worried", "Sad", "Crying", "Shouting",
    "Teary-Eyed", "Determined", "Joyous", "Inspired",
    "Surprised", "Dizzy", "Sigh", "Stunned",
]
SPECIAL_SOURCE = {}


def canonical_palette():
    portrait = Image.open(REF).convert("RGB")
    background = Image.open(CANONICAL).convert("RGB").crop((0, 0, 40, 40))
    body, bg = set(), set()
    for y in range(40):
        for x in range(40):
            colour = portrait.getpixel((x, y))
            (bg if colour == background.getpixel((x, y)) else body).add(colour)
    return sorted(body), sorted(bg)


BODY, BACKDROP = canonical_palette()


def _distance(a, b):
    return sum((p - q) * (p - q) for p, q in zip(a, b))


def canonical_bbox():
    """Bounding box of the character in the published portrait."""
    portrait = Image.open(REF).convert("RGB")
    background = Image.open(CANONICAL).convert("RGB").crop((0, 0, 40, 40))
    xs, ys = [], []
    for y in range(40):
        for x in range(40):
            if portrait.getpixel((x, y)) != background.getpixel((x, y)):
                xs.append(x)
                ys.append(y)
    return min(xs), min(ys), max(xs), max(ys)


def snap_to_native_grid(cell):
    """Collapse the generated art onto its own pixel grid, killing the soft
    resampling edges the model leaves behind."""
    size = CELL // BLOCK
    return cell.resize((size, size), Image.Resampling.BOX)


MAGENTA = (255, 0, 255)


def character_mask(image):
    """The studies are drawn on a pure magenta key, so the character is
    isolated exactly and no generated background can leak onto the canonical
    template backdrop."""
    width, height = image.size
    mask = Image.new("L", (width, height), 0)
    pixels = mask.load()
    source = image.load()
    for y in range(height):
        for x in range(width):
            r, g, b = source[x, y]
            # Magenta key plus its resampling halo: high red and blue, low green.
            keyed = r > 140 and b > 140 and g < 110 and abs(r - b) < 90
            if not keyed:
                pixels[x, y] = 255
    return mask


# Portraits the user explicitly validated on the v2 sheet. They are rebuilt
# from that exact sheet so their approved look is preserved untouched.
VALIDATED_V2 = {"Surprised", "Pain", "Inspired", "Joyous"}


def study(emotion):
    """One cleaned, canonically framed 40x40 character layer."""
    name = SPECIAL_SOURCE.get(emotion, emotion)
    index = GUIDE_ORDER.index(name)
    source = GUIDE_V2 if name in VALIDATED_V2 else GUIDE
    sheet = Image.open(source).convert("RGB")
    cell = sheet.crop(((index % GRID) * CELL, (index // GRID) * CELL,
                       (index % GRID + 1) * CELL, (index // GRID + 1) * CELL))
    native = snap_to_native_grid(cell)
    mask = character_mask(native)
    box = mask.getbbox()
    if box is None:
        raise SystemExit(f"{emotion}: no character found in the study")

    # Rescale the study so its character matches the canonical portrait's
    # bounding box. The scale is uniform and driven by the head WIDTH, then the
    # art is anchored on the top of the crest, so the head keeps its true
    # proportions and whatever falls below row 39 is simply cropped, exactly
    # like the published portrait which is itself cut off at the bottom.
    x0, y0, x1, y1 = canonical_bbox()
    target_w = x1 - x0 + 1
    bw, bh = box[2] - box[0], box[3] - box[1]
    scale = target_w / bw
    art = native.crop(box).resize((target_w, max(1, round(bh * scale))),
                                  Image.Resampling.LANCZOS)
    alpha = mask.crop(box).resize(art.size, Image.Resampling.LANCZOS)

    layer = Image.new("RGBA", (40, 40), (0, 0, 0, 0))
    rgba = art.convert("RGBA")
    rgba.putalpha(alpha)
    layer.paste(rgba, (x0, y0))

    erase_mouth(layer)

    # Lock the style: snap every character pixel to the published palette.
    pixels = layer.load()
    for y in range(40):
        for x in range(40):
            r, g, b, a = pixels[x, y]
            if a < 128:
                pixels[x, y] = (0, 0, 0, 0)
                continue
            pixels[x, y] = (*min(BODY, key=lambda c: _distance((r, g, b), c)), 255)
    return layer


PLATE = {(87, 87, 95), (71, 71, 80), (52, 50, 56)}
RED = {(154, 34, 35), (203, 61, 63)}


def erase_mouth(layer):
    """Falinks has no mouth. The crest is red and the face plate is grey, so
    any red the generator painted inside the plate is a mouth: it is repainted
    with the surrounding plate colour."""
    pixels = layer.load()
    for y in range(20, 40):
        for x in range(40):
            r, g, b, a = pixels[x, y]
            if a == 0:
                continue
            nearest = min(BODY, key=lambda c: _distance((r, g, b), c))
            if nearest not in RED:
                continue
            # Count plate neighbours in a small ring around the pixel.
            plate = 0
            for dy in range(-3, 4):
                for dx in range(-3, 4):
                    nx, ny = x + dx, y + dy
                    if not (0 <= nx < 40 and 0 <= ny < 40):
                        continue
                    nr, ng, nb, na = pixels[nx, ny]
                    if na and min(BODY, key=lambda c: _distance((nr, ng, nb), c)) in PLATE:
                        plate += 1
            if plate >= 12:
                pixels[x, y] = (*sorted(PLATE, key=lambda c: -c[0])[0], 255)


def reduce_background(tile, max_colors):
    colors = sorted(tile.getcolors(100000), reverse=True)
    if len(colors) <= max_colors:
        return tile, [colour for _, colour in colors]
    kept = [colour for _, colour in colors[:max_colors]]
    reduced = tile.copy()
    pixels = reduced.load()
    for y in range(40):
        for x in range(40):
            colour = pixels[x, y]
            if colour not in kept:
                pixels[x, y] = min(kept, key=lambda option: _distance(colour, option))
    return reduced, kept


BODY_PRIORITY = [
    (52, 50, 56), (154, 34, 35), (87, 87, 95), (245, 209, 83), (58, 155, 202),
    (255, 255, 255), (71, 71, 80), (213, 167, 51), (143, 112, 32),
    (203, 61, 63), (150, 226, 227), (196, 195, 176),
]


def compose(emotion, layer):
    index = SLOTS.index(emotion)
    template = Image.open(CANONICAL).convert("RGB")
    tile = template.crop(((index % 5) * 40, (index // 5) * 40,
                          (index % 5 + 1) * 40, (index // 5 + 1) * 40))
    used = {layer.getpixel((x, y))[:3] for y in range(40) for x in range(40)
            if layer.getpixel((x, y))[3]}
    body = [colour for colour in BODY_PRIORITY if colour in used]
    bg_palette = [colour for _, colour in tile.getcolors(100000)]
    if len(bg_palette) > 15:
        tile, bg_palette = reduce_background(tile, 12)
    if len(bg_palette) + len(body) > 15:
        body = body[:max(1, 15 - len(bg_palette))]
    allowed = bg_palette + body

    result = Image.new("RGB", (40, 40))
    rp, bp = result.load(), tile.load()
    lp = layer.load()
    for y in range(40):
        for x in range(40):
            r, g, b, a = lp[x, y]
            if a == 0:
                rp[x, y] = bp[x, y]
                continue
            rp[x, y] = (r, g, b) if (r, g, b) in allowed else min(
                allowed, key=lambda option: _distance((r, g, b), option))
    return result


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    for emotion in EMOTIONS:
        image = compose(emotion, study(emotion))
        image.save(OUT / f"{emotion}.png")
        image.transpose(Image.Transpose.FLIP_LEFT_RIGHT).save(OUT / f"{emotion}^.png")

    sheet = Image.new("RGB", (200, 320), (0, 0, 0))
    for index, emotion in enumerate(SLOTS):
        if emotion is None:
            continue
        image = Image.open(OUT / f"{emotion}.png").convert("RGB")
        x, y = (index % 5) * 40, (index // 5) * 40
        sheet.paste(image, (x, y))
        sheet.paste(image.transpose(Image.Transpose.FLIP_LEFT_RIGHT), (x, y + 160))
    sheet.save(OUT / "Sheet.png")
    print(f"built v2: {len(EMOTIONS)} portraits + mirrors in {OUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
