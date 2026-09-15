"""Build the Mega Evolution effect animation that engulfs a PMD sprite.

The effect is a VFX overlay animation, not a character animation:

  1. thick lightning energy columns strike down around the Pokemon;
  2. an OPAQUE rainbow energy sphere grows and swallows the sprite;
  3. the Mega Evolution emblem, the DNA double helix, burns in front of it;
  4. the sphere collapses and the emblem fades.

Everything is drawn procedurally at native resolution with integer maths and
snapped to one authored pixel-art palette. No filtering, no anti-aliasing and
no AI generated pixel is involved.
"""
from pathlib import Path
import math
import random

from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
OUT = ROOT / "effects" / "mega_evolution"

# Default subject: the Terapagos Stellar idle, facing the camera.
SPRITE_SHEET = ROOT / "sprite" / "1024" / "Idle-Anim.png"
SPRITE_FRAME = (40, 48)

WIDTH, HEIGHT = 80, 96
CX, CY = WIDTH // 2, HEIGHT // 2
FRAMES = 16

# Authored effect palette. Pixel art discipline: every pixel is snapped to it.
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
DARK = (90, 40, 150)
MID = (140, 90, 200)

# The rainbow ring order, dark rim first so the sphere reads as a volume.
RAINBOW = [RED, ORANGE, YELLOW, GREEN, TEAL, CYAN, BLUE, VIOLET, MAGENTA]
PALETTE = [OUTLINE, WHITE, PALE, RED, ORANGE, YELLOW, GREEN, TEAL, CYAN,
           BLUE, VIOLET, MAGENTA, DARK, MID]

# Sphere radius per frame: grow, hold, collapse.
RADII = [0, 0, 5, 12, 20, 27, 32, 34, 34, 34, 34, 33, 30, 24, 15, 6]
# Emblem scale per frame, 0 means hidden.
EMBLEM = [0, 0, 0, 0, 0, 0, 1, 2, 2, 2, 2, 2, 2, 1, 0, 0]
# Lightning intensity per frame.
BOLTS = [2, 3, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 3, 2, 2]

# The Mega Evolution emblem: a closed DNA helix, drawn as an S ribbon with
# three rungs. "#" is the ribbon body, "=" a rung, "." is empty.
EMBLEM_ART = [
    "...#########....",
    "..###########...",
    ".####.....####..",
    ".###...==..###..",
    ".###...==.......",
    "..####..........",
    "...#####==......",
    "....######......",
    ".....######.....",
    "......######....",
    "......==#####...",
    "........####....",
    "...........###..",
    ".###.......###..",
    ".###..==..####..",
    ".####.....####..",
    "..###########...",
    "...#########....",
]


def snap(colour):
    return min(PALETTE, key=lambda c: sum((a - b) ** 2 for a, b in zip(colour, c)))


def put(pixels, x, y, colour):
    if 0 <= x < WIDTH and 0 <= y < HEIGHT:
        pixels[x, y] = (*colour, 255)


def load_subject():
    """First frame, facing down, of the subject sprite."""
    sheet = Image.open(SPRITE_SHEET).convert("RGBA")
    fw, fh = SPRITE_FRAME
    return sheet.crop((0, 0, fw, fh))


def draw_bolt(pixels, seed, x0, thickness, reach):
    """One heavy column of lightning: a few long straight angular segments,
    each drawn as a wide bar with a white core, a pale mantle and a violet
    rim. Thin per-row jitter was tried first and rejected: it read as scratchy
    noise instead of a thick energy column."""
    rng = random.Random(seed)
    # Build 3 or 4 long segments, so the bolt stays angular and readable.
    points = [(x0, 0)]
    segments = rng.choice((3, 4))
    for step in range(1, segments + 1):
        y = round(reach * step / segments)
        drift = rng.choice((-5, -4, -3, 3, 4, 5)) if step < segments else 0
        points.append((points[-1][0] + drift, y))

    half = max(2, thickness // 2)
    for (ax, ay), (bx, by) in zip(points, points[1:]):
        span = max(1, by - ay)
        for step in range(span + 1):
            y = ay + step
            x = ax + round((bx - ax) * step / span)
            # Taper the column slightly towards the ground.
            local = max(2, half - (1 if y > reach * 3 // 4 else 0))
            for offset in range(-local - 2, local + 3):
                distance = abs(offset)
                if distance <= local - 2:
                    colour = WHITE
                elif distance <= local:
                    colour = PALE
                elif distance <= local + 1:
                    colour = CYAN
                else:
                    colour = VIOLET
                put(pixels, x + offset, y, colour)


def draw_sphere(pixels, radius, phase):
    """Opaque rainbow energy sphere: concentric bands, no transparency."""
    if radius <= 0:
        return
    for y in range(CY - radius - 1, CY + radius + 2):
        for x in range(CX - radius - 1, CX + radius + 2):
            dx, dy = x - CX, y - CY
            dist = int(math.isqrt(dx * dx + dy * dy))
            if dist > radius:
                continue
            if dist >= radius - 1:
                put(pixels, x, y, WHITE)
                continue
            band = (dist + phase) // 3
            colour = RAINBOW[band % len(RAINBOW)]
            # A brighter core sells the energy without breaking opacity.
            if dist < radius // 4:
                colour = WHITE if (band + phase) % 2 else PALE
            put(pixels, x, y, colour)


def draw_emblem(pixels, scale, bright):
    """The Mega Evolution DNA emblem, integer scaled, drawn in front."""
    if scale <= 0:
        return
    art_h = len(EMBLEM_ART)
    art_w = len(EMBLEM_ART[0])
    ox = CX - (art_w * scale) // 2
    oy = CY - (art_h * scale) // 2
    for row, line in enumerate(EMBLEM_ART):
        for col, char in enumerate(line):
            if char == ".":
                continue
            colour = WHITE if char == "#" else (PALE if bright else CYAN)
            for sy in range(scale):
                for sx in range(scale):
                    put(pixels, ox + col * scale + sx, oy + row * scale + sy, colour)
    # Dark contour so the emblem stays readable over the bright sphere.
    for row, line in enumerate(EMBLEM_ART):
        for col, char in enumerate(line):
            if char == ".":
                continue
            for dx, dy in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                nc, nr = col + dx, row + dy
                inside = (0 <= nr < art_h and 0 <= nc < art_w
                          and EMBLEM_ART[nr][nc] != ".")
                if inside:
                    continue
                for step in range(scale):
                    px = ox + col * scale + (dx * scale if dx > 0 else (
                        -1 if dx < 0 else step))
                    py = oy + row * scale + (dy * scale if dy > 0 else (
                        -1 if dy < 0 else step))
                    if dx:
                        py = oy + row * scale + step
                    if dy:
                        px = ox + col * scale + step
                    put(pixels, px, py, OUTLINE)


def build_frame(index, subject):
    frame = Image.new("RGBA", (WIDTH, HEIGHT), CLEAR)
    pixels = frame.load()

    # 1. lightning columns, behind everything
    count = BOLTS[index]
    # Columns stand around the subject, never straight through its centre.
    lanes = [8, 20, 60, 72, 30, 50]
    for bolt in range(count):
        draw_bolt(pixels, seed=index * 100 + bolt, x0=lanes[bolt % len(lanes)],
                  thickness=7 if bolt % 2 == 0 else 5, reach=HEIGHT)

    # 2. the subject sprite
    layer = Image.new("RGBA", (WIDTH, HEIGHT), CLEAR)
    layer.paste(subject, ((WIDTH - subject.width) // 2,
                          (HEIGHT - subject.height) // 2))
    frame = Image.alpha_composite(frame, layer)
    pixels = frame.load()

    # 3. the opaque rainbow sphere, which swallows the sprite
    draw_sphere(pixels, RADII[index], phase=index)

    # 4. the emblem, in front of the sphere
    draw_emblem(pixels, EMBLEM[index], bright=index % 2 == 0)

    # Snap everything to the authored palette.
    for y in range(HEIGHT):
        for x in range(WIDTH):
            r, g, b, a = pixels[x, y]
            if a == 0:
                pixels[x, y] = CLEAR
            else:
                pixels[x, y] = (*snap((r, g, b)), 255)
    return frame


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    subject = load_subject()
    frames = [build_frame(i, subject) for i in range(FRAMES)]

    sheet = Image.new("RGBA", (WIDTH * FRAMES, HEIGHT), CLEAR)
    for i, frame in enumerate(frames):
        sheet.paste(frame, (i * WIDTH, 0))
        frame.save(OUT / f"frame_{i:02d}.png")
    sheet.save(OUT / "MegaEvolution-Anim.png")

    backdrop = Image.new("RGBA", (WIDTH, HEIGHT), (24, 24, 32, 255))
    gif = [Image.alpha_composite(backdrop, f).convert("P", palette=Image.ADAPTIVE)
           for f in frames]
    gif[0].save(OUT / "MegaEvolution.gif", save_all=True, append_images=gif[1:],
                duration=90, loop=0, disposal=2)

    colours = set()
    for frame in frames:
        colours |= {p[:3] for p in frame.get_flattened_data() if p[3]}
    print(f"{FRAMES} frames of {WIDTH}x{HEIGHT} in {OUT.relative_to(ROOT)}")
    print(f"palette actually used: {len(colours)} colours")


if __name__ == "__main__":
    main()
