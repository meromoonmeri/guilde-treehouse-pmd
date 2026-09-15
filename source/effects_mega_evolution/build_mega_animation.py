"""Build a MULTIDIRECTIONAL Mega Evolution effect animation for a PMD sprite.

Reference studied: the Deeshura/Mega_Stones PMDO mod preview GIF. Its beat is
sound but minimal: a plain white orb swells, pops into a red/white starburst,
then a few yellow columns fall. No emblem, no colour identity, one direction.

This build keeps the beat and goes far past it, in six staged acts over 24
frames, rendered for ALL 8 PMD DIRECTIONS:

  act 1  charge    a light pool opens under the Pokemon, shards fly inward
  act 2  implosion the shards slam home, the pool flares
  act 3  engulf    an OPAQUE rainbow sphere swells and swallows the sprite
  act 4  sigil     the Mega Evolution DNA emblem burns in front, pulsing
  act 5  burst     a starburst shockwave detonates, lightning columns strike
  act 6  settle    everything recedes, the Pokemon returns lit by the pool

Art pipeline: every element is drawn BIG by the image generator onto a magenta
key (plates archived in gen/), then de-keyed, trimmed, scaled NEAREST only, and
snapped to one authored effect palette. Hard pixels throughout.
"""
from pathlib import Path
import random

from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
GEN = HERE / "gen"
OUT = ROOT / "effects" / "mega_evolution"

SPRITE_SHEET = ROOT / "sprite" / "1024" / "Idle-Anim.png"
SUBJECT_W, SUBJECT_H = 40, 48

DIRECTIONS = ["down", "down-right", "right", "up-right",
              "up", "up-left", "left", "down-left"]

WIDTH, HEIGHT = 80, 96
CX, CY = WIDTH // 2, HEIGHT // 2
# Feet line: the ground pool sits here, not on the sprite's centre.
FEET_Y = CY + SUBJECT_H // 2 - 6
FRAMES = 24

CLEAR = (0, 0, 0, 0)
OUTLINE = (47, 0, 127)
WHITE = (255, 255, 255)
PALE = (223, 247, 255)
RED = (255, 60, 80)
ORANGE = (255, 140, 40)
YELLOW = (255, 225, 60)
GREEN = (120, 230, 110)
TEAL = (60, 215, 200)
CYAN = (80, 190, 255)
BLUE = (70, 110, 240)
VIOLET = (160, 80, 230)
MAGENTA = (235, 80, 180)
PALETTE = [OUTLINE, WHITE, PALE, RED, ORANGE, YELLOW, GREEN, TEAL, CYAN,
           BLUE, VIOLET, MAGENTA]

# ---------------------------------------------------------------- timelines
# One entry per frame. 0 or -1 means "absent this frame".

# Ground pool: opens early, flares at the implosion, lingers to the end.
POOL_STAGE = [0, 0, 1, 1, 2, 2, 2, 2, 2, 2, 2, 2,
              2, 2, 2, 2, 2, 2, 2, 2, 1, 1, 0, 0]
POOL_WIDTH = [16, 24, 34, 44, 52, 58, 62, 62, 62, 62, 62, 62,
              62, 62, 62, 66, 72, 68, 62, 54, 44, 34, 24, 14]

# Converging shards: fly inward, then gone once the sphere takes over.
SHARD_STAGE = [0, 0, 1, 1, 2, 3, 3, -1, -1, -1, -1, -1,
               -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1]
SHARD_SIZE = [74, 68, 60, 52, 44, 34, 24, 0, 0, 0, 0, 0,
              0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]

# Opaque rainbow sphere: swells, holds through the sigil, collapses at burst.
SPHERE_STAGE = [-1, -1, -1, -1, -1, 0, 1, 2, 3, 4, 5, 5,
                5, 5, 5, 5, 4, -1, -1, -1, -1, -1, -1, -1]
SPHERE_SIZE = [0, 0, 0, 0, 0, 12, 26, 42, 56, 66, 70, 70,
               70, 70, 70, 68, 58, 0, 0, 0, 0, 0, 0, 0]

# The emblem: fades in over the sphere, pulses, flashes out with the burst.
EMBLEM_SIZE = [0, 0, 0, 0, 0, 0, 0, 0, 16, 28, 38, 42,
               40, 44, 42, 46, 52, 64, 72, 0, 0, 0, 0, 0]

# Starburst shockwave: detonates as the sphere breaks.
BURST_STAGE = [-1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1,
               -1, -1, -1, -1, 0, 1, 2, 2, 3, 3, -1, -1]
BURST_SIZE = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
              0, 0, 0, 0, 40, 62, 84, 96, 108, 120, 0, 0]

# Lightning columns: a first warning strike, then the real barrage at the pop.
BOLT_COUNT = [0, 1, 2, 2, 3, 3, 2, 2, 2, 2, 3, 3,
              3, 4, 4, 5, 6, 6, 5, 4, 3, 2, 1, 0]

# Subject visibility: hidden only while the opaque sphere covers it.
SUBJECT_HIDDEN = {10, 11, 12, 13, 14, 15}


def snap(colour):
    return min(PALETTE, key=lambda c: sum((a - b) ** 2 for a, b in zip(colour, c)))


def dekey(image):
    """Remove the pure magenta key the generator was told to draw on."""
    image = image.convert("RGBA")
    pixels = image.load()
    for y in range(image.height):
        for x in range(image.width):
            r, g, b, a = pixels[x, y]
            keyed = r > 140 and b > 140 and g < 110 and abs(r - b) < 90
            pixels[x, y] = CLEAR if keyed else (r, g, b, 255)
    return image


def trim(image):
    box = image.getbbox()
    return image.crop(box) if box else image


def slice_plate(path, count):
    plate = dekey(Image.open(path))
    step = plate.width // count
    return [trim(plate.crop((i * step, 0, (i + 1) * step, plate.height)))
            for i in range(count)]


def harden(image):
    alpha = image.getchannel("A").point(lambda v: 255 if v > 127 else 0)
    image.putalpha(alpha)
    return image


def fit(source, size, ratio=None):
    """Scale a plate to a target box, keeping hard pixel edges."""
    if source is None or size <= 0:
        return None
    if ratio is None:
        scale = min(size / source.width, size / source.height)
        width = max(1, round(source.width * scale))
        height = max(1, round(source.height * scale))
    else:
        width = max(1, size)
        height = max(1, round(size * ratio))
    return harden(source.resize((width, height), Image.Resampling.NEAREST))


def load_plates():
    return {
        "sphere": slice_plate(GEN / "sphere_stages.png", 6),
        "bolts": slice_plate(GEN / "lightning_columns.png", 4),
        "emblem": trim(dekey(Image.open(GEN / "mega_emblem.png"))),
        "burst": slice_plate(GEN / "starburst.png", 4),
        "shards": slice_plate(GEN / "shards.png", 4),
        "pool": slice_plate(GEN / "ground_pool.png", 3),
    }


def load_subject_rows():
    sheet = Image.open(SPRITE_SHEET).convert("RGBA")
    return [sheet.crop((0, row * SUBJECT_H, SUBJECT_W, (row + 1) * SUBJECT_H))
            for row in range(len(DIRECTIONS))]


def paste_at(canvas, art, cx, cy):
    if art is None:
        return canvas
    layer = Image.new("RGBA", (WIDTH, HEIGHT), CLEAR)
    layer.paste(art, (cx - art.width // 2, cy - art.height // 2))
    return Image.alpha_composite(canvas, layer)


def build_frame(index, row, plates, subject):
    frame = Image.new("RGBA", (WIDTH, HEIGHT), CLEAR)
    rng = random.Random(index * 31 + row * 7)

    # --- ground pool, flat on the floor, drawn first so it reads as ground
    if POOL_STAGE[index] >= 0 and POOL_WIDTH[index] > 0:
        pool = plates["pool"][POOL_STAGE[index]]
        frame = paste_at(frame, fit(pool, POOL_WIDTH[index], ratio=0.42),
                         CX, FEET_Y)

    # --- lightning columns, in lanes that keep the centre clear
    lanes = [5, 15, 65, 75, 25, 55]
    for bolt in range(BOLT_COUNT[index]):
        plate = plates["bolts"][rng.randrange(4)]
        column = harden(plate.resize((10 if bolt % 2 == 0 else 8, HEIGHT),
                                     Image.Resampling.NEAREST))
        layer = Image.new("RGBA", (WIDTH, HEIGHT), CLEAR)
        layer.paste(column, (lanes[bolt % len(lanes)] - column.width // 2, 0))
        frame = Image.alpha_composite(layer, frame) if False else \
            Image.alpha_composite(frame, layer)

    # --- the subject, in ITS OWN direction artwork
    if index not in SUBJECT_HIDDEN:
        frame = paste_at(frame, subject, CX, CY)

    # --- shards converging inward
    if SHARD_STAGE[index] >= 0 and SHARD_SIZE[index] > 0:
        frame = paste_at(frame, fit(plates["shards"][SHARD_STAGE[index]],
                                    SHARD_SIZE[index]), CX, CY)

    # --- opaque rainbow sphere
    if SPHERE_STAGE[index] >= 0 and SPHERE_SIZE[index] > 0:
        frame = paste_at(frame, fit(plates["sphere"][SPHERE_STAGE[index]],
                                    SPHERE_SIZE[index]), CX, CY)

    # --- starburst shockwave
    if BURST_STAGE[index] >= 0 and BURST_SIZE[index] > 0:
        frame = paste_at(frame, fit(plates["burst"][BURST_STAGE[index]],
                                    BURST_SIZE[index]), CX, CY)

    # --- the Mega emblem, in front of everything
    if EMBLEM_SIZE[index] > 0:
        frame = paste_at(frame, fit(plates["emblem"], EMBLEM_SIZE[index]),
                         CX, CY)

    pixels = frame.load()
    for y in range(HEIGHT):
        for x in range(WIDTH):
            r, g, b, a = pixels[x, y]
            pixels[x, y] = CLEAR if a == 0 else (*snap((r, g, b)), 255)
    return frame


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    for stale in OUT.glob("MegaEvolution-*.gif"):
        stale.unlink()

    plates = load_plates()
    subjects = load_subject_rows()

    sheet = Image.new("RGBA", (WIDTH * FRAMES, HEIGHT * len(DIRECTIONS)), CLEAR)
    for row in range(len(DIRECTIONS)):
        for index in range(FRAMES):
            sheet.paste(build_frame(index, row, plates, subjects[row]),
                        (index * WIDTH, row * HEIGHT))
    sheet.save(OUT / "MegaEvolution-Anim.png")

    backdrop = Image.new("RGBA", (WIDTH, HEIGHT), (24, 24, 32, 255))
    for row, name in enumerate(DIRECTIONS):
        frames = []
        for index in range(FRAMES):
            tile = sheet.crop((index * WIDTH, row * HEIGHT,
                               (index + 1) * WIDTH, (row + 1) * HEIGHT))
            frames.append(Image.alpha_composite(backdrop, tile)
                          .convert("P", palette=Image.ADAPTIVE))
        frames[0].save(OUT / f"MegaEvolution-{name}.gif", save_all=True,
                       append_images=frames[1:], duration=80, loop=0,
                       disposal=2)

    colours = {p[:3] for p in sheet.get_flattened_data() if p[3]}
    print(f"sheet {sheet.size}: {FRAMES} frames x {len(DIRECTIONS)} directions")
    print(f"palette actually used: {len(colours)} colours")


if __name__ == "__main__":
    main()
