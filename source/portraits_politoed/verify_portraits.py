"""Validate the Politoed portrait pack against SpriteCollab constraints."""
from pathlib import Path
from PIL import Image, ImageChops

ROOT = Path(__file__).resolve().parents[2]
PACK = ROOT / "portrait" / "0186"
EMOTIONS = [
    "Normal", "Happy", "Pain", "Angry", "Worried",
    "Sad", "Crying", "Shouting", "Teary-Eyed", "Determined",
    "Joyous", "Inspired", "Surprised", "Dizzy", "Special0",
    "Special1", "Sigh", "Stunned", "Special2", "Special3",
]


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


normal = {}
for emotion in EMOTIONS:
    normal[emotion] = load(PACK / f"{emotion}.png")
    flipped = load(PACK / f"{emotion}^.png")
    expected = normal[emotion].transpose(Image.Transpose.FLIP_LEFT_RIGHT)
    if ImageChops.difference(expected, flipped).getbbox() is not None:
        fail(f"{emotion}^ is not the exact horizontal mirror")

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
    if ImageChops.difference(sheet.crop((x, y + 160, x + 40, y + 200)), normal[emotion].transpose(Image.Transpose.FLIP_LEFT_RIGHT)).getbbox() is not None:
        fail(f"Sheet.png: mirrored tile {emotion} is out of order or differs")

print(f"PASS: {len(EMOTIONS)} normal + {len(EMOTIONS)} mirrored Politoed portraits")
print("PASS: all individual portraits are 40x40, opaque, and <=15 colors")
print("PASS: Sheet.png is 200x320 and matches the SpriteBot order")
