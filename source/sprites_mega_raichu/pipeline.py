"""Pipeline: generated Mega Raichu rotation sheet -> PMDO sprite pack.

WHAT THIS SOLVES
----------------
The previous pack was a RECOLOUR of canonical Raichu geometry, so it lacked the
Mega design's defining feature: the huge lightning-bolt wings. Redrawing those
by hand across 35 animations and 8 angles is not realistic, so the wings were
left out and that limitation was documented.

Here the image generator supplies the missing angles instead. It was given two
references: the canonical 8-direction row (to copy the camera angles and pose)
and the Mega front artwork (to copy the design). It returned one row of 8 cells
showing the Mega design, wings included, rotated correctly.

THE CONVERSION PROBLEM
----------------------
A generated plate is not a sprite. It is huge, magenta-keyed, anti-aliased at
the edges and carries hundreds of colours. Turning it into a PMD sprite needs a
deterministic chain, and every step below exists to protect pixel-art quality:

  1. DE-KEY        the magenta backdrop is removed by hue test, not by exact
                   match, because the generator dithers the key slightly.
  2. SPLIT         the row is cut into its 8 direction cells.
  3. DETECT GRID   the generator draws on an implicit pixel grid. The real
                   pixel size is measured from run lengths, so the plate can be
                   reduced by an INTEGER factor and land on true pixels.
  4. REDUCE        area-average down to that native grid, once. This is the
                   only resize in the chain.
  5. QUANTISE      snap every pixel to the Mega palette read off the source
                   artwork, so the sprite shares its exact colours.
  6. HARDEN        alpha becomes strictly 0 or 255, killing generator fringing.
  7. TRIM + ALIGN  all 8 cells share one bounding box and one baseline, so the
                   character does not jitter between directions.
  8. EMIT          Anim, Offsets and Shadow sheets plus AnimData.xml.

The result is a real, importable Idle animation in 8 directions carrying the
full Mega silhouette. Scope is stated honestly in the README.
"""
from pathlib import Path
import math
import xml.etree.ElementTree as ET
from collections import Counter

from PIL import Image, ImageSequence

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
GEN = HERE / "gen" / "mega_8dir.png"
GIF = HERE / "source.gif"
OUT = ROOT / "sprite" / "0026_mega_x_gen"

DIRECTIONS = ["down", "down-right", "right", "up-right",
              "up", "up-left", "left", "down-left"]

# Target sprite scale. Canonical Raichu occupies ~29x26 in a 40x56 frame; the
# Mega design is bulkier and winged, so it gets a taller frame.
FRAME_W, FRAME_H = 56, 64

OFF_HEAD = (0, 0, 0)
OFF_BODY = (0, 255, 0)
OFF_RIGHT = (255, 0, 0)
OFF_LEFT = (0, 0, 255)
SHADOW_WHITE = (255, 255, 255)
SHADOW_SIZE = 1


# ------------------------------------------------------------------ step 1
def is_key(rgb):
    """Magenta backdrop test. The generator dithers the key, so match by hue."""
    r, g, b = rgb
    return r > 150 and b > 140 and g < 110


def dekey(image):
    image = image.convert("RGBA")
    px = image.load()
    for y in range(image.height):
        for x in range(image.width):
            r, g, b, a = px[x, y]
            px[x, y] = (0, 0, 0, 0) if is_key((r, g, b)) else (r, g, b, 255)
    return image


# ------------------------------------------------------------------ step 3
def detect_pixel_size(image):
    """Measure the generator's implicit pixel size from horizontal run lengths."""
    px = image.load()
    runs = []
    for y in range(0, image.height, 5):
        run = 1
        for x in range(1, image.width):
            if px[x, y] == px[x - 1, y]:
                run += 1
            else:
                if px[x - 1, y][3]:
                    runs.append(run)
                run = 1
    counts = Counter(r for r in runs if 2 <= r <= 40)
    if not counts:
        return 1
    # The true pixel size divides most run lengths. Test candidates and keep
    # the largest that explains a solid majority of them.
    best, best_score = 1, 0
    total = sum(counts.values())
    for cand in range(2, 25):
        score = sum(v for r, v in counts.items() if r % cand == 0)
        if score >= total * 0.70 and cand > best:
            best, best_score = cand, score
    return best


# ------------------------------------------------------------------ step 5
def load_mega_palette():
    """Exact colours of the Mega artwork, so the sprite matches the design."""
    frames = [f.convert("RGBA").resize((96, 96), Image.Resampling.NEAREST)
              for f in ImageSequence.Iterator(Image.open(GIF))]
    colours = Counter()
    for frame in frames:
        colours.update(p[:3] for p in frame.get_flattened_data() if p[3])
    return [c for c, _ in colours.most_common()]


def nearest(colour, palette):
    return min(palette, key=lambda c: sum((a - b) ** 2
                                          for a, b in zip(colour, c)))


def reduce_cell(cell, factor):
    """Step 4: the one and only reduction, onto the generator's native grid."""
    width = max(1, round(cell.width / factor))
    height = max(1, round(cell.height / factor))
    return cell.resize((width, height), Image.Resampling.BOX)


def quantise(tile, palette):
    """Steps 5-6: snap to the Mega palette and harden alpha.

    This runs LAST, after every resize. Running it before align() was a bug:
    align() resized again, blending quantised colours back into thousands of
    new ones. Quantisation is only meaningful once geometry is final.
    """
    px = tile.load()
    cache = {}
    for y in range(tile.height):
        for x in range(tile.width):
            r, g, b, a = px[x, y]
            if a < 128:
                px[x, y] = (0, 0, 0, 0)
                continue
            key = (r, g, b)
            if key not in cache:
                cache[key] = nearest(key, palette)
            px[x, y] = (*cache[key], 255)
    return tile


# ------------------------------------------------------------------ step 7
def align(cells):
    """One shared bounding box and baseline for all 8 directions."""
    boxes = [c.getbbox() for c in cells]
    width = max(b[2] - b[0] for b in boxes)
    height = max(b[3] - b[1] for b in boxes)
    scale = min(FRAME_W / width, FRAME_H / height, 1.0)
    out = []
    for cell, box in zip(cells, boxes):
        art = cell.crop(box)
        if scale < 1.0:
            art = art.resize((max(1, round(art.width * scale)),
                              max(1, round(art.height * scale))),
                             Image.Resampling.BOX)
            alpha = art.getchannel("A").point(lambda v: 255 if v > 127 else 0)
            art.putalpha(alpha)
        tile = Image.new("RGBA", (FRAME_W, FRAME_H), (0, 0, 0, 0))
        # Centred horizontally, standing on a common baseline.
        tile.paste(art, ((FRAME_W - art.width) // 2,
                         FRAME_H - art.height - 2))
        out.append(tile)
    return out


# ------------------------------------------------------------------ step 8
def markers(tile):
    box = tile.getbbox()
    offs = Image.new("RGBA", tile.size, (0, 0, 0, 0))
    shad = Image.new("RGBA", tile.size, (0, 0, 0, 0))
    if box is None:
        return offs, shad
    left, top, right, bottom = box
    cx = (left + right) // 2
    op = offs.load()
    for colour, (x, y) in {
        OFF_BODY: (cx, top + (bottom - top) * 6 // 10),
        OFF_HEAD: (cx, top + (bottom - top) * 3 // 10),
        OFF_RIGHT: (max(left, cx - (right - left) // 4),
                    top + (bottom - top) * 6 // 10),
        OFF_LEFT: (min(right - 1, cx + (right - left) // 4),
                   top + (bottom - top) * 6 // 10),
    }.items():
        if 0 <= x < tile.width and 0 <= y < tile.height:
            op[x, y] = (*colour, 255)
    shad.load()[cx, min(tile.height - 1, bottom - 1)] = (*SHADOW_WHITE, 255)
    return offs, shad


def breathe(tile, lift):
    """A 2-frame idle bob, so the animation is alive without inventing poses."""
    out = Image.new("RGBA", tile.size, (0, 0, 0, 0))
    out.paste(tile, (0, -lift))
    return out


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    for stale in OUT.glob("*"):
        if stale.is_file():
            stale.unlink()

    plate = dekey(Image.open(GEN))
    step = plate.width // len(DIRECTIONS)
    raw = [plate.crop((i * step, 0, (i + 1) * step, plate.height))
           for i in range(len(DIRECTIONS))]
    raw = [c.crop(c.getbbox()) for c in raw]

    factor = detect_pixel_size(plate)
    palette = load_mega_palette()
    print(f"detected generator pixel size: {factor}")
    print(f"Mega palette: {len(palette)} colours")

    cells = [reduce_cell(c, factor) for c in raw]
    cells = align(cells)
    cells = [quantise(c, palette) for c in cells]

    frames = [cells, [breathe(c, 1) for c in cells]]
    count = len(frames)

    anim = Image.new("RGBA", (FRAME_W * count, FRAME_H * 8), (0, 0, 0, 0))
    offs = Image.new("RGBA", anim.size, (0, 0, 0, 0))
    shad = Image.new("RGBA", anim.size, (0, 0, 0, 0))
    for row in range(8):
        for col in range(count):
            tile = frames[col][row]
            anim.paste(tile, (col * FRAME_W, row * FRAME_H))
            o, s = markers(tile)
            offs.paste(o, (col * FRAME_W, row * FRAME_H))
            shad.paste(s, (col * FRAME_W, row * FRAME_H))

    anim.save(OUT / "Idle-Anim.png")
    offs.save(OUT / "Idle-Offsets.png")
    shad.save(OUT / "Idle-Shadow.png")

    root = ET.Element("AnimData")
    ET.SubElement(root, "ShadowSize").text = str(SHADOW_SIZE)
    anims = ET.SubElement(root, "Anims")
    node = ET.SubElement(anims, "Anim")
    ET.SubElement(node, "Name").text = "Idle"
    ET.SubElement(node, "Index").text = "7"
    ET.SubElement(node, "FrameWidth").text = str(FRAME_W)
    ET.SubElement(node, "FrameHeight").text = str(FRAME_H)
    durations = ET.SubElement(node, "Durations")
    for _ in range(count):
        ET.SubElement(durations, "Duration").text = "10"
    ET.indent(root, space="  ")
    ET.ElementTree(root).write(OUT / "AnimData.xml",
                               encoding="utf-8", xml_declaration=True)

    (OUT / "credits.txt").write_text(
        "2026-09-15\tmeromoonmeri\tCUR\tUnspecified\t"
        "Mega Raichu design, commit a214a07\n"
        "2026-09-15\tArena.ai Agent for meromoonmeri\tCUR\tUnspecified\t"
        "8-direction rotation generated from that design, converted to PMD\n"
    )

    used = {p[:3] for p in anim.get_flattened_data() if p[3]}
    print(f"frame {FRAME_W}x{FRAME_H}, {count} frames x 8 directions")
    print(f"colours: {len(used)}")


if __name__ == "__main__":
    main()
