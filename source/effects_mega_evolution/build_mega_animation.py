"""Build a MULTIDIRECTIONAL Mega Evolution effect animation for a PMD sprite.

Pipeline, following the PMD sprite guide:

  1. draw BIG with the image generator: three magenta-keyed pixel-art plates
     live in gen/ (rainbow sphere growth stages, Mega DNA emblem, thick
     lightning columns). They are the only art source for the effect;
  2. turn each plate into a sprite: magenta key removed exactly, snapped back
     to its own pixel grid, then scaled by integer-friendly steps to the sizes
     the animation needs;
  3. composite over the subject sprite for ALL 8 PMD DIRECTIONS, row by row,
     so the sheet covers every angle like a real PMD animation;
  4. snap every pixel to one authored effect palette.

The subject keeps its own per-direction artwork, so the Pokemon faces the right
way in every row while the effect engulfs it.
"""
from pathlib import Path
import math
import random

from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
GEN = HERE / "gen"
OUT = ROOT / "effects" / "mega_evolution"

# Subject: Terapagos Stellar. Its Idle sheet is 13 columns x 8 direction rows.
SPRITE_SHEET = ROOT / "sprite" / "1024" / "Idle-Anim.png"
SUBJECT_W, SUBJECT_H = 40, 48

# PMD direction order, one sheet row each.
DIRECTIONS = ["down", "down-right", "right", "up-right",
              "up", "up-left", "left", "down-left"]

WIDTH, HEIGHT = 80, 96
CX, CY = WIDTH // 2, HEIGHT // 2
FRAMES = 16

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

# Per frame: which generated sphere stage, its diameter, emblem size, bolts.
# Stage -1 means no sphere. The sphere must fully hide the 40x48 subject at
# its peak, so the peak diameter is comfortably larger than the subject.
SPHERE_STAGE = [-1, -1, 0, 1, 2, 3, 4, 5, 5, 5, 5, 4, 3, 2, 1, 0]
SPHERE_SIZE = [0, 0, 10, 22, 38, 54, 64, 68, 68, 68, 68, 66, 58, 44, 26, 12]
EMBLEM_SIZE = [0, 0, 0, 0, 0, 0, 20, 34, 40, 40, 40, 38, 32, 18, 0, 0]
BOLT_COUNT = [2, 3, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 3, 2, 2]


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


def fit(image, size):
    """Scale a de-keyed plate to a target box, keeping hard pixel edges."""
    if size <= 0:
        return None
    source = trim(image)
    scale = min(size / source.width, size / source.height)
    width = max(1, round(source.width * scale))
    height = max(1, round(source.height * scale))
    art = source.resize((width, height), Image.Resampling.NEAREST)
    # Re-harden the alpha: NEAREST keeps it binary, this is a safety net.
    alpha = art.getchannel("A").point(lambda v: 255 if v > 127 else 0)
    art.putalpha(alpha)
    return art


def load_plates():
    sphere = dekey(Image.open(GEN / "sphere_stages.png"))
    stages = []
    step = sphere.width // 6
    for index in range(6):
        stages.append(trim(sphere.crop((index * step, 0,
                                        (index + 1) * step, sphere.height))))

    bolts_plate = dekey(Image.open(GEN / "lightning_columns.png"))
    bolts = []
    step = bolts_plate.width // 4
    for index in range(4):
        bolts.append(trim(bolts_plate.crop((index * step, 0,
                                            (index + 1) * step,
                                            bolts_plate.height))))

    emblem = trim(dekey(Image.open(GEN / "mega_emblem.png")))
    return stages, bolts, emblem


def subject_frame(direction_row):
    """The subject's own artwork for this direction."""
    sheet = Image.open(SPRITE_SHEET).convert("RGBA")
    y = direction_row * SUBJECT_H
    return sheet.crop((0, y, SUBJECT_W, y + SUBJECT_H))


def paste_centre(canvas, art, offset=(0, 0)):
    if art is None:
        return canvas
    layer = Image.new("RGBA", (WIDTH, HEIGHT), CLEAR)
    layer.paste(art, (CX - art.width // 2 + offset[0],
                      CY - art.height // 2 + offset[1]))
    return Image.alpha_composite(canvas, layer)


def build_frame(index, direction_row, plates):
    stages, bolts, emblem = plates
    frame = Image.new("RGBA", (WIDTH, HEIGHT), CLEAR)

    # 1. lightning columns behind, in lanes that frame the subject.
    rng = random.Random(index * 31 + direction_row * 7)
    # Lanes hug the left and right edges: the centre stays clear so the
    # subject and the sphere are never hidden by the columns.
    lanes = [5, 15, 65, 75, 25, 55]
    for bolt in range(BOLT_COUNT[index]):
        plate = bolts[rng.randrange(len(bolts))]
        # Keep each column narrow enough to read as a pillar, not a curtain.
        column = plate.resize((10 if bolt % 2 == 0 else 8, HEIGHT),
                              Image.Resampling.NEAREST)
        alpha = column.getchannel("A").point(lambda v: 255 if v > 127 else 0)
        column.putalpha(alpha)
        layer = Image.new("RGBA", (WIDTH, HEIGHT), CLEAR)
        layer.paste(column, (lanes[bolt % len(lanes)] - column.width // 2, 0))
        frame = Image.alpha_composite(frame, layer)

    # 2. the subject, in ITS OWN direction artwork.
    frame = paste_centre(frame, subject_frame(direction_row))

    # 3. the opaque rainbow sphere swallows it.
    stage = SPHERE_STAGE[index]
    if stage >= 0:
        frame = paste_centre(frame, fit(stages[stage], SPHERE_SIZE[index]))

    # 4. the Mega emblem burns in front.
    frame = paste_centre(frame, fit(emblem, EMBLEM_SIZE[index]))

    pixels = frame.load()
    for y in range(HEIGHT):
        for x in range(WIDTH):
            r, g, b, a = pixels[x, y]
            pixels[x, y] = CLEAR if a == 0 else (*snap((r, g, b)), 255)
    return frame


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    plates = load_plates()

    # One row per direction, one column per frame: a real PMD-style sheet.
    sheet = Image.new("RGBA", (WIDTH * FRAMES, HEIGHT * len(DIRECTIONS)), CLEAR)
    for row in range(len(DIRECTIONS)):
        for index in range(FRAMES):
            frame = build_frame(index, row, plates)
            sheet.paste(frame, (index * WIDTH, row * HEIGHT))
    sheet.save(OUT / "MegaEvolution-Anim.png")

    # A GIF per direction, for review.
    backdrop = Image.new("RGBA", (WIDTH, HEIGHT), (24, 24, 32, 255))
    for row, name in enumerate(DIRECTIONS):
        frames = []
        for index in range(FRAMES):
            tile = sheet.crop((index * WIDTH, row * HEIGHT,
                               (index + 1) * WIDTH, (row + 1) * HEIGHT))
            frames.append(Image.alpha_composite(backdrop, tile)
                          .convert("P", palette=Image.ADAPTIVE))
        frames[0].save(OUT / f"MegaEvolution-{name}.gif", save_all=True,
                       append_images=frames[1:], duration=90, loop=0, disposal=2)

    colours = {p[:3] for p in sheet.get_flattened_data() if p[3]}
    print(f"sheet {sheet.size}: {FRAMES} frames x {len(DIRECTIONS)} directions")
    print(f"palette actually used: {len(colours)} colours")


if __name__ == "__main__":
    main()
