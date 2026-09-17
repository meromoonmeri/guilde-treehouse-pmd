"""Validate Falinks #0870 portraits against SpriteCollab portrait rules."""
from __future__ import annotations

import zipfile
from pathlib import Path

from PIL import Image, ImageChops

ROOT = Path(__file__).resolve().parents[2]
PACK = ROOT / "portrait" / "0870" / "0002"
REFERENCE = ROOT / "source" / "portraits_falinks" / "reference"
ZIP_PATH = ROOT / "portrait-0870-0002.zip"
ZIP_ALIAS = ROOT / "portrait-0870.zip"
EMOTIONS = [
    "Normal", "Happy", "Pain", "Angry", "Worried", "Sad", "Crying", "Shouting",
    "Teary-Eyed", "Determined", "Joyous", "Inspired", "Surprised", "Dizzy",
    "Special0", "Special1", "Sigh", "Stunned", "Special2", "Special3",
]


def fail(message: str) -> None:
    raise SystemExit("FAIL: " + message)


def load(path: Path) -> Image.Image:
    if not path.is_file():
        fail(f"missing {path.relative_to(ROOT)}")
    image = Image.open(path).convert("RGB")
    if image.size != (40, 40):
        fail(f"{path.name}: expected 40x40, got {image.size}")
    if len(image.getcolors(1_000_000)) > 15:
        fail(f"{path.name}: more than 15 colors")
    return image


def main() -> None:
    if not PACK.is_dir():
        fail("missing portrait/0870/0002")
    normal: dict[str, Image.Image] = {}
    for emotion in EMOTIONS:
        normal[emotion] = load(PACK / f"{emotion}.png")
        mirrored = load(PACK / f"{emotion}^.png")
        expected = normal[emotion].transpose(Image.Transpose.FLIP_LEFT_RIGHT)
        if ImageChops.difference(expected, mirrored).getbbox() is not None:
            fail(f"{emotion}^ is not the exact horizontal mirror")

    if (PACK / "Normal.png").read_bytes() != (REFERENCE / "Normal.png").read_bytes():
        fail("canonical Falinks Normal.png changed")

    sheet = Image.open(PACK / "Sheet.png").convert("RGB")
    if sheet.size != (200, 320):
        fail("Sheet.png must be 200x320")
    for index, emotion in enumerate(EMOTIONS):
        x, y = (index % 5) * 40, (index // 5) * 40
        if ImageChops.difference(sheet.crop((x, y, x + 40, y + 40)), normal[emotion]).getbbox() is not None:
            fail(f"Sheet normal tile out of order: {emotion}")
        mirrored = normal[emotion].transpose(Image.Transpose.FLIP_LEFT_RIGHT)
        if ImageChops.difference(sheet.crop((x, y + 160, x + 40, y + 200)), mirrored).getbbox() is not None:
            fail(f"Sheet mirrored tile out of order: {emotion}")

    actual = {path.name for path in PACK.iterdir() if path.is_file()}
    expected = {"Sheet.png", "credits.txt"}
    for emotion in EMOTIONS:
        expected.update({f"{emotion}.png", f"{emotion}^.png"})
    if actual != expected:
        fail("unexpected portrait files: " + ", ".join(sorted(actual ^ expected)))

    if not ZIP_PATH.is_file():
        fail("missing portrait-0870-0002.zip")
    with zipfile.ZipFile(ZIP_PATH) as archive:
        if set(archive.namelist()) != actual:
            fail("portrait-0870-0002.zip does not match the portrait folder")
    if not ZIP_ALIAS.is_file() or ZIP_ALIAS.read_bytes() != ZIP_PATH.read_bytes():
        fail("portrait-0870.zip is not a byte-for-byte archive alias")

    print("PASS: 20 Falinks normal + 20 exact mirrored portraits")
    print("PASS: all portraits are 40x40 and <=15 colors")
    print("PASS: canonical Normal.png unchanged")
    print("PASS: Sheet.png is 200x320 and follows SpriteBot order")
    print("PASS: portrait-0870-0002.zip exactly matches the portrait folder")
    print("PASS: portrait-0870.zip is a byte-for-byte compatibility alias")


if __name__ == "__main__":
    main()
