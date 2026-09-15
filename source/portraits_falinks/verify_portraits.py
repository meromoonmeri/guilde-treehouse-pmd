"""Validate the Falinks portrait pack against SpriteCollab constraints."""
from pathlib import Path

from PIL import Image, ImageChops

import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
from build_portraits import reduce_background  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
PACK = ROOT / "portrait" / "0870"
REF = ROOT / "source" / "portraits_falinks" / "reference"
TEMPLATE = ROOT / "portrait" / "0186" / "template.png"
EMOTIONS = [
    "Normal", "Happy", "Pain", "Angry", "Worried",
    "Sad", "Crying", "Shouting", "Teary-Eyed", "Determined",
    "Joyous", "Inspired", "Surprised", "Dizzy", "Special0",
    "Special1", "Sigh", "Stunned", "Special2", "Special3",
]
REQUIRED_16 = EMOTIONS[:14] + ["Sigh", "Stunned"]
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
for emotion in EMOTIONS:
    normal[emotion] = load(PACK / f"{emotion}.png")
    flipped = load(PACK / f"{emotion}^.png")
    expected = normal[emotion].transpose(Image.Transpose.FLIP_LEFT_RIGHT)
    if ImageChops.difference(expected, flipped).getbbox() is not None:
        fail(f"{emotion}^ is not the exact horizontal mirror")

for emotion in REQUIRED_16:
    if emotion not in normal:
        fail(f"missing required emotion {emotion}")

for emotion in UPSTREAM:
    published = Image.open(PACK / f"{emotion}.png").convert("RGB")
    reference = Image.open(REF / f"{emotion}.png").convert("RGB")
    if ImageChops.difference(published, reference).getbbox() is not None:
        fail(f"published upstream portrait changed: {emotion}.png")

# Every generated portrait must reuse the canonical background of its template
# cell wherever no character pixel is drawn, and must not invent colours
# outside the published Falinks palette on the character itself.
template = Image.open(TEMPLATE).convert("RGB")
source = Image.open(REF / "Normal.png").convert("RGB")
falinks_palette = {colour for _, colour in source.getcolors(10000)}
for index, emotion in enumerate(EMOTIONS):
    tile = template.crop(((index % 5) * 40, (index // 5) * 40,
                          (index % 5 + 1) * 40, (index // 5 + 1) * 40))
    portrait = normal[emotion]
    matches = sum(1 for y in range(40) for x in range(40)
                  if portrait.getpixel((x, y)) == tile.getpixel((x, y)))
    if matches < 120:
        fail(f"{emotion}: canonical background from template cell {index} not preserved")

for emotion in EMOTIONS:
    if emotion in UPSTREAM:
        continue
    index = EMOTIONS.index(emotion)
    tile = template.crop(((index % 5) * 40, (index // 5) * 40,
                          (index % 5 + 1) * 40, (index // 5 + 1) * 40))
    tile_colors = {colour for _, colour in tile.getcolors(10000)}
    if len(tile_colors) > 15:
        tile_colors = set(reduce_background(tile, 12)[1])
    for _, colour in normal[emotion].getcolors(10000):
        if colour not in falinks_palette and colour not in tile_colors:
            fail(f"{emotion}: colour {colour} is neither Falinks art nor background")

sheet_path = PACK / "Sheet.png"
sheet = Image.open(sheet_path).convert("RGB") if sheet_path.is_file() else fail("missing Sheet.png")
if sheet.size != (200, 320):
    fail(f"Sheet.png: expected 200x320, got {sheet.size}")
for index, emotion in enumerate(EMOTIONS):
    x, y = (index % 5) * 40, (index // 5) * 40
    if ImageChops.difference(sheet.crop((x, y, x + 40, y + 40)), normal[emotion]).getbbox():
        fail(f"Sheet.png: normal tile {emotion} is out of order or differs")
    mirrored = normal[emotion].transpose(Image.Transpose.FLIP_LEFT_RIGHT)
    if ImageChops.difference(sheet.crop((x, y + 160, x + 40, y + 200)), mirrored).getbbox():
        fail(f"Sheet.png: mirrored tile {emotion} is out of order or differs")

print(f"PASS: {len(EMOTIONS)} normal + {len(EMOTIONS)} mirrored Falinks portraits")
print("PASS: the 16 required emotions and the 4 Special slots are present")
print("PASS: all portraits are 40x40, opaque and <=15 colors")
print("PASS: upstream Normal.png pixels unchanged")
print("PASS: canonical template backgrounds preserved, palette limited to Falinks art")
print("PASS: Sheet.png is 200x320 and matches the SpriteBot order")
