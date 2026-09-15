"""Mega Evolution effect animation for a PMD sprite, drawn from scratch.

WHY THIS IS A REWRITE
---------------------
The previous attempt generated large images and downscaled them to ~60px.
Downscaled pixel art is not pixel art: it turns to mush, the edges go soft and
the colour count explodes. It also stacked five loud elements at once and used
a saturated rainbow that belongs to no PMD palette, so the effect fought the
Pokemon instead of serving it.

This version fixes that at the root:

  * every pixel is placed by hand at NATIVE resolution, 80x96. Nothing is ever
    resized, so edges stay hard by construction;
  * the palette is TAKEN FROM THE SUBJECT SPRITE ITSELF, so the effect looks
    like it belongs to this Pokemon rather than sitting on top of it;
  * the staging is restrained: at most two ideas on screen at a time, and the
    Pokemon stays readable except during the single deliberate whiteout;
  * the energy reads as RINGS and MOTES converging, which is the classic PMD
    power-up vocabulary, instead of vertical bars that curtained the frame.

Output is a PMD-style sheet: one row per direction, one column per frame.
"""
from pathlib import Path
import math

from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "effects" / "mega"

SPRITE_SHEET = ROOT / "sprite" / "1024" / "Idle-Anim.png"
SUBJECT_W, SUBJECT_H = 40, 48

DIRECTIONS = ["down", "down-right", "right", "up-right",
              "up", "up-left", "left", "down-left"]

WIDTH, HEIGHT = 80, 96
CX, CY = WIDTH // 2, HEIGHT // 2 - 2
FEET_Y = CY + 20
FRAMES = 24

CLEAR = (0, 0, 0, 0)

# Palette lifted from the Terapagos Stellar sprite, plus one warm accent for
# the flash. Keeping the effect inside the subject's own colours is what makes
# it read as PMD rather than as a sticker.
DEEP = (47, 0, 127)
DUSK = (68, 76, 157)
BLUE = (86, 106, 192)
STEEL = (119, 167, 223)
SKY = (100, 199, 238)
AQUA = (49, 165, 206)
MINT = (143, 215, 151)
LEAF = (191, 231, 159)
ICE = (207, 223, 255)
FROST = (223, 247, 255)
WHITE = (255, 255, 255)
ROSE = (221, 78, 151)
LILAC = (154, 86, 213)
GOLD = (255, 231, 175)

PALETTE = [DEEP, DUSK, BLUE, STEEL, SKY, AQUA, MINT, LEAF, ICE, FROST,
           WHITE, ROSE, LILAC, GOLD]


def snap(colour):
    return min(PALETTE, key=lambda c: sum((a - b) ** 2 for a, b in zip(colour, c)))


class Canvas:
    """A tiny native-resolution pixel canvas. No scaling, ever."""

    def __init__(self):
        self.image = Image.new("RGBA", (WIDTH, HEIGHT), CLEAR)
        self.px = self.image.load()

    def set(self, x, y, colour):
        if 0 <= x < WIDTH and 0 <= y < HEIGHT and colour is not None:
            self.px[int(x), int(y)] = (*colour, 255)

    def blit(self, art, ox, oy):
        layer = Image.new("RGBA", (WIDTH, HEIGHT), CLEAR)
        layer.paste(art, (int(ox), int(oy)))
        self.image = Image.alpha_composite(self.image, layer)
        self.px = self.image.load()


def ring(canvas, cx, cy, radius, colour, squash=1.0, gaps=0):
    """A 1px ring drawn with midpoint stepping, optionally dashed."""
    if radius < 1:
        return
    steps = max(8, int(radius * 8))
    for step in range(steps):
        if gaps and (step * gaps // steps) % 2:
            continue
        angle = 2 * math.pi * step / steps
        x = round(cx + math.cos(angle) * radius)
        y = round(cy + math.sin(angle) * radius * squash)
        canvas.set(x, y, colour)


def disc(canvas, cx, cy, radius, colour, squash=1.0):
    for y in range(int(cy - radius * squash) - 1, int(cy + radius * squash) + 2):
        for x in range(int(cx - radius) - 1, int(cx + radius) + 2):
            dx = (x - cx) / max(0.001, radius)
            dy = (y - cy) / max(0.001, radius * squash)
            if dx * dx + dy * dy <= 1.0:
                canvas.set(x, y, colour)


def mote(canvas, x, y, colour, big=False):
    """A converging energy mote: a plus sign, with a core when big."""
    canvas.set(x, y, WHITE if big else colour)
    for dx, dy in ((-1, 0), (1, 0), (0, -1), (0, 1)):
        canvas.set(x + dx, y + dy, colour)
    if big:
        for dx, dy in ((-1, -1), (1, -1), (-1, 1), (1, 1)):
            canvas.set(x + dx, y + dy, colour)


def spark(canvas, cx, cy, angle, inner, outer, colour, tip=WHITE):
    """A radial energy spike, drawn as a line of pixels."""
    length = outer - inner
    if length <= 0:
        return
    for step in range(length + 1):
        t = inner + step
        x = round(cx + math.cos(angle) * t)
        y = round(cy + math.sin(angle) * t)
        canvas.set(x, y, tip if step >= length - 1 else colour)


def ground_pool(canvas, radius, bright):
    """Flat light pooling on the floor, anchored at the feet."""
    if radius < 2:
        return
    disc(canvas, CX, FEET_Y, radius, DUSK, squash=0.34)
    disc(canvas, CX, FEET_Y, radius * 0.72, BLUE if not bright else STEEL,
         squash=0.34)
    disc(canvas, CX, FEET_Y, radius * 0.40, STEEL if not bright else FROST,
         squash=0.34)
    ring(canvas, CX, FEET_Y, radius, LILAC, squash=0.34)


def halo(canvas, radius, colour, squash=1.0, gaps=0):
    ring(canvas, CX, CY, radius, colour, squash=squash, gaps=gaps)


# ------------------------------------------------------------------ timeline
# Restraint is the point: each phase owns the frame, they overlap only briefly.
#   0-5   gather : motes spiral inward, pool opens
#   6-10  bind   : rings tighten around the Pokemon
#   11-13 flash  : single clean whiteout, the only moment the sprite is hidden
#   14-18 emerge : shockwave rings expand, sparks radiate
#   19-23 settle : pool dims, last motes drift off


def draw_motes(canvas, index):
    """Motes spiralling inward during the gather, outward on release."""
    if index <= 10:
        t = index / 10.0
        distance = 40 - 28 * t
        count = 8
        spin = index * 0.38
        colours = [SKY, MINT, ROSE, ICE]
        for k in range(count):
            angle = 2 * math.pi * k / count + spin
            x = round(CX + math.cos(angle) * distance)
            y = round(CY + math.sin(angle) * distance * 0.8)
            mote(canvas, x, y, colours[k % len(colours)], big=index > 6)
    elif index >= 19:
        t = (index - 19) / 4.0
        distance = 14 + 26 * t
        for k in range(6):
            angle = 2 * math.pi * k / 6 + index * 0.2
            x = round(CX + math.cos(angle) * distance)
            y = round(CY + math.sin(angle) * distance * 0.8)
            mote(canvas, x, y, ICE)


def build_frame(index, subject):
    canvas = Canvas()

    # --- floor light, present through most of the sequence
    pool = 0
    if index < 6:
        pool = 6 + index * 3
    elif index < 14:
        pool = 24 + (index - 6)
    elif index < 19:
        pool = 34 - (index - 14) * 2
    else:
        pool = max(0, 24 - (index - 19) * 6)
    ground_pool(canvas, pool, bright=11 <= index <= 14)

    # --- the Pokemon, in its own direction artwork
    if not (11 <= index <= 13):
        canvas.blit(subject, CX - SUBJECT_W // 2, CY - SUBJECT_H // 2)

    # --- gather: motes converge
    draw_motes(canvas, index)

    # --- bind: rings tighten
    if 6 <= index <= 12:
        t = (index - 6) / 6.0
        radius = 30 - 20 * t
        halo(canvas, radius, FROST, squash=0.85)
        halo(canvas, radius - 3, SKY, squash=0.85, gaps=6)

    # --- flash: one clean whiteout, no clutter competing with it
    if 11 <= index <= 13:
        stage = index - 11
        radius = (16, 26, 20)[stage]
        disc(canvas, CX, CY, radius, WHITE)
        ring(canvas, CX, CY, radius + 1, FROST)
        ring(canvas, CX, CY, radius + 2, LILAC)
        if stage == 1:
            for k in range(12):
                spark(canvas, CX, CY, 2 * math.pi * k / 12, radius + 2,
                      radius + 9, FROST, tip=WHITE)

    # --- emerge: shockwave rings and sparks.
    # The ring must DIE before it reaches the frame edge. An expanding circle
    # that runs off the canvas gets sliced into broken arcs, which reads as a
    # bug rather than as energy, so the wave is capped and thins out instead.
    if 14 <= index <= 18:
        t = index - 14
        outer = 16 + t * 5          # peaks at 36, inside the 40px half-width
        colour = (FROST, FROST, ICE, STEEL, DUSK)[t]
        halo(canvas, outer, colour, squash=0.8)
        if t <= 2:
            halo(canvas, outer - 2, LILAC, squash=0.8, gaps=8)
        if t <= 2:
            for k in range(8):
                angle = 2 * math.pi * k / 8 + 0.2 * t
                spark(canvas, CX, CY, angle, outer - 6, outer + 1, SKY,
                      tip=WHITE)

    # --- palette lock
    px = canvas.image.load()
    for y in range(HEIGHT):
        for x in range(WIDTH):
            r, g, b, a = px[x, y]
            px[x, y] = CLEAR if a == 0 else (*snap((r, g, b)), 255)
    return canvas.image


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    sheet_src = Image.open(SPRITE_SHEET).convert("RGBA")
    subjects = [sheet_src.crop((0, r * SUBJECT_H, SUBJECT_W, (r + 1) * SUBJECT_H))
                for r in range(len(DIRECTIONS))]

    sheet = Image.new("RGBA", (WIDTH * FRAMES, HEIGHT * len(DIRECTIONS)), CLEAR)
    for row in range(len(DIRECTIONS)):
        for index in range(FRAMES):
            sheet.paste(build_frame(index, subjects[row]),
                        (index * WIDTH, row * HEIGHT))
    sheet.save(OUT / "Mega-Anim.png")

    backdrop = Image.new("RGBA", (WIDTH, HEIGHT), (28, 26, 38, 255))
    for row, name in enumerate(DIRECTIONS):
        frames = []
        for index in range(FRAMES):
            tile = sheet.crop((index * WIDTH, row * HEIGHT,
                               (index + 1) * WIDTH, (row + 1) * HEIGHT))
            frames.append(Image.alpha_composite(backdrop, tile)
                          .convert("P", palette=Image.ADAPTIVE))
        frames[0].save(OUT / f"Mega-{name}.gif", save_all=True,
                       append_images=frames[1:], duration=80, loop=0,
                       disposal=2)

    colours = {p[:3] for p in sheet.get_flattened_data() if p[3]}
    print(f"sheet {sheet.size}: {FRAMES} frames x {len(DIRECTIONS)} directions")
    print(f"colours used: {len(colours)}")


if __name__ == "__main__":
    main()
