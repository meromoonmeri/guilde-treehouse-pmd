"""Mega Evolution effect: 10 frames, continuous motion, 2D/3D orbiting energy.

DESIGN
------
Ten frames is short, so nothing may be wasted and nothing may jump. Two rules
drive this build:

  FLUID  — every element is a CONTINUOUS function of a normalised time t in
           [0,1). No hand-tuned per-frame tables, no popping. Angles advance by
           a constant step, radii follow smooth eased curves, so the motion
           reads the same at any playback speed and the loop is seamless.

  3D     — the energy orbits on TILTED RINGS rendered in perspective. Each
           orbiting mote carries a depth value z = sin(angle). Motes with z < 0
           are drawn BEHIND the sprite, motes with z > 0 are drawn IN FRONT,
           and their size and brightness track depth. That single trick is what
           sells volume on a flat sprite: the ring visibly wraps around the
           Pokemon instead of sitting on top of it.

Everything is placed pixel by pixel at native 80x96. No image is ever resized,
so edges stay hard. The palette is taken from the subject sprite itself.
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
FRAMES = 10

CLEAR = (0, 0, 0, 0)

# Palette lifted from the Terapagos Stellar sprite.
DEEP = (47, 0, 127)
DUSK = (68, 76, 157)
BLUE = (86, 106, 192)
STEEL = (119, 167, 223)
SKY = (100, 199, 238)
AQUA = (49, 165, 206)
MINT = (143, 215, 151)
ICE = (207, 223, 255)
FROST = (223, 247, 255)
WHITE = (255, 255, 255)
ROSE = (221, 78, 151)
LILAC = (154, 86, 213)

PALETTE = [DEEP, DUSK, BLUE, STEEL, SKY, AQUA, MINT, ICE, FROST, WHITE,
           ROSE, LILAC]

# Depth ramps: far motes are dim and small, near motes bright and fat.
# Far motes still have to be VISIBLE against a dark dungeon floor, so the ramp
# starts at STEEL rather than at the near-black DUSK, which vanished entirely.
DEPTH_RAMP = [STEEL, BLUE, AQUA, SKY, ICE, FROST, WHITE]

# Two counter-rotating rings, each with its own tilt, radius and mote count.
RINGS = [
    {"count": 7, "tilt": 0.46, "spin": +1.0, "phase": 0.0, "rx": 31},
    {"count": 5, "tilt": 0.78, "spin": -1.4, "phase": 1.7, "rx": 24},
]


def snap(colour):
    return min(PALETTE, key=lambda c: sum((a - b) ** 2 for a, b in zip(colour, c)))


def ease_in_out(t):
    """Smooth acceleration and deceleration, so nothing starts or stops hard."""
    return t * t * (3.0 - 2.0 * t)


class Canvas:
    def __init__(self):
        self.image = Image.new("RGBA", (WIDTH, HEIGHT), CLEAR)
        self.px = self.image.load()

    def set(self, x, y, colour):
        if colour is None:
            return
        x, y = int(x), int(y)
        if 0 <= x < WIDTH and 0 <= y < HEIGHT:
            self.px[x, y] = (*colour, 255)

    def blit(self, art, ox, oy):
        layer = Image.new("RGBA", (WIDTH, HEIGHT), CLEAR)
        layer.paste(art, (int(ox), int(oy)))
        self.image = Image.alpha_composite(self.image, layer)
        self.px = self.image.load()


def disc(canvas, cx, cy, radius, colour, squash=1.0):
    for y in range(int(cy - radius * squash) - 1, int(cy + radius * squash) + 2):
        for x in range(int(cx - radius) - 1, int(cx + radius) + 2):
            dx = (x - cx) / max(0.001, radius)
            dy = (y - cy) / max(0.001, radius * squash)
            if dx * dx + dy * dy <= 1.0:
                canvas.set(x, y, colour)


def ring_outline(canvas, cx, cy, radius, colour, squash=1.0):
    steps = max(10, int(radius * 9))
    for step in range(steps):
        angle = 2 * math.pi * step / steps
        canvas.set(round(cx + math.cos(angle) * radius),
                   round(cy + math.sin(angle) * radius * squash), colour)


def orbit_motes(t):
    """Every orbiting mote for time t, as (z, x, y, radius, colour).

    z is the depth: negative is behind the subject, positive is in front.
    The orbit radius contracts with an eased curve, so the energy visibly
    spirals in rather than sliding at constant distance.
    """
    pull = ease_in_out(min(1.0, t / 0.75))
    motes = []
    for ring in RINGS:
        rx = ring["rx"] * (1.0 - 0.34 * pull)
        for k in range(ring["count"]):
            angle = (2 * math.pi * k / ring["count"]
                     + ring["phase"]
                     + 2 * math.pi * ring["spin"] * t)
            # Perspective projection of a tilted circular orbit.
            z = math.sin(angle)
            x = CX + math.cos(angle) * rx
            y = CY + z * rx * ring["tilt"]
            # Near motes render bigger and brighter.
            depth = (z + 1.0) * 0.5
            shade = DEPTH_RAMP[min(len(DEPTH_RAMP) - 1,
                                   int(depth * len(DEPTH_RAMP)))]
            vx = -math.sin(angle) * ring["spin"]
            motes.append((z, x, y, 1 + (depth > 0.55) + (depth > 0.85),
                          shade, vx))
    return motes


def orbit_path(canvas, t, front):
    """Faint dashed ellipse tracing each orbit, split into far/near halves.

    Without the path the motes read as loose sparkles. With it, the eye sees a
    ring in perspective wrapping the sprite, which is what creates the volume.
    """
    pull = ease_in_out(min(1.0, t / 0.75))
    for ring in RINGS:
        rx = ring["rx"] * (1.0 - 0.34 * pull)
        steps = max(24, int(rx * 7))
        for step in range(steps):
            angle = 2 * math.pi * step / steps
            z = math.sin(angle)
            if (z >= 0) != front:
                continue
            # A CONTINUOUS path. Dashes were tried and rejected: at this
            # scale they broke the ellipse into disconnected arcs that looked
            # like rendering errors. Depth is conveyed by colour instead: the
            # far half is dim, the near half bright.
            canvas.set(round(CX + math.cos(angle) * rx),
                       round(CY + z * rx * ring["tilt"]),
                       STEEL if front else DUSK)


def draw_mote(canvas, x, y, size, colour, vx=0.0):
    """A mote plus a short trail opposite its travel, which sells speed."""
    if abs(vx) > 0.15:
        step = -1 if vx > 0 else 1
        canvas.set(x + step, y, colour)
        if size >= 3:
            canvas.set(x + 2 * step, y, DUSK if colour is WHITE else colour)
    canvas.set(x, y, WHITE if size >= 3 else colour)
    if size >= 2:
        for dx, dy in ((-1, 0), (1, 0), (0, -1), (0, 1)):
            canvas.set(x + dx, y + dy, colour)
    if size >= 3:
        for dx, dy in ((0, -1), (0, 1)):
            canvas.set(x + dx, y + dy, WHITE)


def build_frame(index, subject):
    t = index / FRAMES
    canvas = Canvas()

    # --- ground light, breathing with the same eased curve as the orbit
    pull = ease_in_out(min(1.0, t / 0.75))
    pool = 10 + 20 * pull
    flash = 0.70 <= t < 0.90
    disc(canvas, CX, FEET_Y, pool, DUSK, squash=0.34)
    disc(canvas, CX, FEET_Y, pool * 0.70, STEEL if flash else BLUE, squash=0.34)
    disc(canvas, CX, FEET_Y, pool * 0.38, FROST if flash else STEEL, squash=0.34)

    motes = orbit_motes(t)

    # --- BEHIND the subject: the far half of every orbit
    orbit_path(canvas, t, front=False)
    for z, x, y, size, colour, vx in sorted(motes, key=lambda m: m[0]):
        if z < 0:
            draw_mote(canvas, x, y, size, colour, vx)

    # --- the subject, hidden only at the peak of the flash
    if not flash:
        canvas.blit(subject, CX - SUBJECT_W // 2, CY - SUBJECT_H // 2)
    else:
        burst = 14 + 10 * ease_in_out((t - 0.70) / 0.20)
        disc(canvas, CX, CY, burst, WHITE)
        ring_outline(canvas, CX, CY, burst + 1, FROST)
        ring_outline(canvas, CX, CY, burst + 2, LILAC)

    # --- IN FRONT of the subject: the near half, painter's order
    if not flash:
        orbit_path(canvas, t, front=True)
    for z, x, y, size, colour, vx in sorted(motes, key=lambda m: m[0]):
        if z >= 0:
            draw_mote(canvas, x, y, size, colour, vx)

    # --- release wave, only after the flash, capped inside the frame
    if t >= 0.90:
        wave = 20 + 14 * ease_in_out((t - 0.90) / 0.10)
        ring_outline(canvas, CX, CY, wave, ICE, squash=0.8)
        ring_outline(canvas, CX, CY, wave - 2, LILAC, squash=0.8)

    px = canvas.image.load()
    for y in range(HEIGHT):
        for x in range(WIDTH):
            r, g, b, a = px[x, y]
            px[x, y] = CLEAR if a == 0 else (*snap((r, g, b)), 255)
    return canvas.image


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    for stale in OUT.glob("*"):
        stale.unlink()

    src = Image.open(SPRITE_SHEET).convert("RGBA")
    subjects = [src.crop((0, r * SUBJECT_H, SUBJECT_W, (r + 1) * SUBJECT_H))
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
                       append_images=frames[1:], duration=90, loop=0,
                       disposal=2)

    colours = {p[:3] for p in sheet.get_flattened_data() if p[3]}
    print(f"sheet {sheet.size}: {FRAMES} frames x {len(DIRECTIONS)} directions")
    print(f"colours used: {len(colours)}")


if __name__ == "__main__":
    main()
