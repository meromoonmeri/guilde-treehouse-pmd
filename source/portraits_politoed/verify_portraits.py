"""Validate the Politoed portrait pack against SpriteCollab constraints."""
from pathlib import Path
from PIL import Image, ImageChops

ROOT = Path(__file__).resolve().parents[2]
PACK = ROOT / "portrait" / "0186"
REF = ROOT / "source" / "portraits_politoed" / "reference"
EMOTIONS = [
    "Normal", "Happy", "Pain", "Angry", "Worried",
    "Sad", "Crying", "Shouting", "Teary-Eyed", "Determined",
    "Joyous", "Inspired", "Surprised", "Dizzy", "Special0",
    "Special1", "Sigh", "Stunned", "Special2", "Special3",
]
UPSTREAM = ["Normal", "Inspired", "Shouting", "Surprised"]


def fail(message: str) -> None:
    raise SystemExit("FAIL: " + message)


def load(path: Path) -> Image.Image:
    if not path.is_file():
        fail(f"missing {path.relative_to(ROOT)}")
    image = Image.open(path)
    if image.size != (40, 40):
        fail(f"{path.name}: expected 40x40, got {image.size}")
    if image.mode not in ("RGB", "RGBA"):
        fail(f"{path.name}: unexpected mode {image.mode}")
    if image.mode == "RGBA" and image.getchannel("A").getextrema() != (255, 255):
        fail(f"{path.name}: portraits must be opaque")
    colors = len(image.convert("RGB").getcolors(1_000_000))
    if colors > 15:
        fail(f"{path.name}: {colors} colors, maximum is 15")
    return image.convert("RGB")


# The newly supplied canonical resources must remain native 40px cells.  The
# template is read as the 5x8 SpriteBot sheet; only its first 20 cells are
# used as standard backgrounds by the generator.
template = PACK / "template.png"
extra = PACK / "Extra_Backgrounds.png"
ai_guide = REF / "ai_expression_guide.png"
if Image.open(template).size != (200, 320):
    fail("template.png must be 200x320")
if Image.open(extra).size != (280, 240):
    fail("Extra_Backgrounds.png must be 280x240")
if Image.open(ai_guide).size != (1024, 1024):
    fail("ai_expression_guide.png must be 1024x1024")

normal = {}
for emotion in EMOTIONS:
    normal[emotion] = load(PACK / f"{emotion}.png")
    flipped = load(PACK / f"{emotion}^.png")
    expected = normal[emotion].transpose(Image.Transpose.FLIP_LEFT_RIGHT)
    if ImageChops.difference(expected, flipped).getbbox() is not None:
        fail(f"{emotion}^ is not the exact horizontal mirror")

for emotion in UPSTREAM:
    published = Image.open(PACK / f"{emotion}.png").convert("RGB")
    reference = Image.open(REF / f"{emotion}.png").convert("RGB")
    if ImageChops.difference(published, reference).getbbox() is not None:
        fail(f"published upstream portrait changed: {emotion}.png")

sheet_path = PACK / "Sheet.png"
if not sheet_path.is_file():
    fail("missing Sheet.png")
sheet = Image.open(sheet_path).convert("RGB")
if sheet.size != (200, 320):
    fail(f"Sheet.png: expected 200x320, got {sheet.size}")
for i, emotion in enumerate(EMOTIONS):
    x, y = (i % 5) * 40, (i // 5) * 40
    if ImageChops.difference(sheet.crop((x, y, x + 40, y + 40)), normal[emotion]).getbbox() is not None:
        fail(f"Sheet.png: normal tile {emotion} is out of order or differs")
    mirrored = normal[emotion].transpose(Image.Transpose.FLIP_LEFT_RIGHT)
    if ImageChops.difference(sheet.crop((x, y + 160, x + 40, y + 200)), mirrored).getbbox() is not None:
        fail(f"Sheet.png: mirrored tile {emotion} is out of order or differs")

print(f"PASS: {len(EMOTIONS)} normal + {len(EMOTIONS)} mirrored Politoed portraits")
print("PASS: all individual portraits are 40x40, opaque, and <=15 colors")
print("PASS: canonical template, supplemental backgrounds and BIG guide dimensions")
print("PASS: upstream Normal/Inspired/Shouting/Surprised pixels unchanged")
print("PASS: Sheet.png is 200x320 and matches the SpriteBot order")
