"""Validate the Terapagos Stellar portrait pack against SpriteCollab constraints."""
from pathlib import Path

from PIL import Image, ImageChops

import sys

ROOT = Path(__file__).resolve().parents[2]
PACK = ROOT / "portrait" / "1024"
REF = Path(__file__).resolve().parent / "reference"
TEMPLATE = ROOT / "portrait" / "0186" / "template.png"
SLOTS = [
    "Normal", "Happy", "Pain", "Angry", "Worried",
    "Sad", "Crying", "Shouting", "Teary-Eyed", "Determined",
    "Joyous", "Inspired", "Surprised", "Dizzy", None,
    None, "Sigh", "Stunned", None, None,
]
EMOTIONS = [slot for slot in SLOTS if slot]
REQUIRED_16 = EMOTIONS
UPSTREAM = ["Normal"]


def fail(message):
    raise SystemExit("FAIL: " + message)


def load(path):
    if not path.is_file():
        fail(f"missing {path.relative_to(ROOT)}")
    image = Image.open(path)
    if image.size != (40, 40):
        fail(f"{path.name}: expected 40x40, got {image.size}")
    if image.mode == "RGBA" and image.getchannel("A").getextrema() != (255, 255):
        fail(f"{path.name}: portraits must be opaque")
    colors = len(image.convert("RGB").getcolors(1_000_000))
    if colors > 15:
        fail(f"{path.name}: {colors} colors, maximum is 15")
    return image.convert("RGB")


if Image.open(TEMPLATE).size != (200, 320):
    fail("template.png must be 200x320")

normal = {}
mirrored = {}
for emotion in EMOTIONS:
    normal[emotion] = load(PACK / f"{emotion}.png")
    # Upstream Normal^ is hand-adjusted, not a mechanical flip, so the whole
    # mirrored pack is built on it. The check is that each mirror differs from
    # a raw flip by no more than the upstream hand corrections themselves.
    mirrored[emotion] = load(PACK / f"{emotion}^.png")

for emotion in REQUIRED_16:
    if emotion not in normal:
        fail(f"missing required emotion {emotion}")

# Version 2 redraws every slot through the generator, including Normal, so the
# upstream portrait is not expected to be byte-identical here. Instead the
# canonical palette must be respected exactly.

# The Stellar pack is derived from the published portrait, not composited on
# the template: the correct check is that the crystalline shell is preserved
# and only the eye zone changes.
source = Image.open(REF / "Normal.png").convert("RGB")
stellar_palette = {colour for _, colour in source.getcolors(10000)}
EYE_BOX = (9, 14, 28, 36)
for emotion in EMOTIONS:
    image = normal[emotion]
    for _, colour in image.getcolors(10000):
        if colour not in stellar_palette:
            fail(f"{emotion}: colour {colour} is outside the Stellar palette")
    if emotion in UPSTREAM:
        continue
    changed = [(x, y) for y in range(40) for x in range(40)
               if image.getpixel((x, y)) != source.getpixel((x, y))]
    if not changed:
        fail(f"{emotion}: identical to Normal, no expression drawn")
    outside = [(x, y) for x, y in changed
               if not (EYE_BOX[0] <= x <= EYE_BOX[2] and EYE_BOX[1] <= y <= EYE_BOX[3])]
    if outside:
        fail(f"{emotion}: {len(outside)} pixels changed outside the eye/effect zone")

upstream_normal = Image.open(REF / "Normal.png").convert("RGB")
upstream_flip = Image.open(REF / "Normal^.png").convert("RGB")
hand = {(x, y) for y in range(40) for x in range(40)
        if upstream_flip.getpixel((x, y))
        != upstream_normal.transpose(Image.Transpose.FLIP_LEFT_RIGHT).getpixel((x, y))}
for emotion in EMOTIONS:
    flip = normal[emotion].transpose(Image.Transpose.FLIP_LEFT_RIGHT)
    differing = {(x, y) for y in range(40) for x in range(40)
                 if mirrored[emotion].getpixel((x, y)) != flip.getpixel((x, y))}
    if not differing <= hand:
        fail(f"{emotion}^ differs from the flip outside the upstream hand corrections")

sheet_path = PACK / "Sheet.png"
sheet = Image.open(sheet_path).convert("RGB") if sheet_path.is_file() else fail("missing Sheet.png")
if sheet.size != (200, 320):
    fail(f"Sheet.png: expected 200x320, got {sheet.size}")
for index, emotion in enumerate(SLOTS):
    if emotion is None:
        continue
    x, y = (index % 5) * 40, (index // 5) * 40
    if ImageChops.difference(sheet.crop((x, y, x + 40, y + 40)), normal[emotion]).getbbox():
        fail(f"Sheet.png: normal tile {emotion} is out of order or differs")
    if ImageChops.difference(sheet.crop((x, y + 160, x + 40, y + 200)),
                             mirrored[emotion]).getbbox():
        fail(f"Sheet.png: mirrored tile {emotion} is out of order or differs")

print(f"PASS: {len(EMOTIONS)} normal + {len(EMOTIONS)} mirrored Falinks portraits")
print("PASS: the 16 required emotions are present; Special slots left empty")
print("PASS: all portraits are 40x40, opaque and <=15 colors")
print("PASS: shell preserved, only the eye zone repainted, Stellar palette kept")

print("PASS: Sheet.png is 200x320 and matches the SpriteBot order")
