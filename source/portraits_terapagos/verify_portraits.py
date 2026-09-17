"""Validate the complete Terapagos #1024 SpriteCollab portrait set."""
from __future__ import annotations

import zipfile
from pathlib import Path

from PIL import Image, ImageChops

ROOT = Path(__file__).resolve().parents[2]
REFERENCE = ROOT / "source" / "portraits_terapagos" / "reference"
OUT_ROOT = ROOT / "portrait" / "1024"
AGGREGATE = ROOT / "portrait-1024.zip"
SIZE = (40, 40)
EMOTIONS = [
    "Normal", "Happy", "Pain", "Angry", "Worried", "Sad", "Crying", "Shouting",
    "Teary-Eyed", "Determined", "Joyous", "Inspired", "Surprised", "Dizzy",
    "Special0", "Special1", "Sigh", "Stunned", "Special2", "Special3",
]
VARIANTS = ("0000/0001", "0001", "0002")


def fail(message: str) -> None:
    raise SystemExit("FAIL: " + message)


def load(path: Path) -> Image.Image:
    if not path.is_file():
        fail(f"missing {path.relative_to(ROOT)}")
    image = Image.open(path).convert("RGB")
    if image.size != SIZE:
        fail(f"{path.relative_to(ROOT)}: expected 40x40, got {image.size}")
    colors = image.getcolors(1_000_000)
    if colors is None or len(colors) > 15:
        fail(f"{path.relative_to(ROOT)}: more than 15 colors")
    return image


def expected_names() -> set[str]:
    names = {"Sheet.png", "credits.txt"}
    for emotion in EMOTIONS:
        names.update({f"{emotion}.png", f"{emotion}^.png"})
    return names


def main() -> None:
    if not OUT_ROOT.is_dir():
        fail("missing portrait/1024")
    aggregate_expected: set[str] = set()
    for variant in VARIANTS:
        out = OUT_ROOT / variant
        ref = REFERENCE / variant
        if not out.is_dir() or not ref.is_dir():
            fail(f"missing variant {variant}")
        normal: dict[str, Image.Image] = {}
        mirror: dict[str, Image.Image] = {}
        canonical_names = {path.name for path in ref.iterdir() if path.is_file()}
        for emotion in EMOTIONS:
            normal[emotion] = load(out / f"{emotion}.png")
            mirror[emotion] = load(out / f"{emotion}^.png")
            canonical = ref / f"{emotion}.png"
            if canonical.is_file() and canonical.read_bytes() != (out / canonical.name).read_bytes():
                fail(f"{variant}/{emotion}.png changed a canonical upstream portrait")
            canonical_mirror = ref / f"{emotion}^.png"
            if canonical_mirror.is_file():
                if canonical_mirror.read_bytes() != (out / canonical_mirror.name).read_bytes():
                    fail(f"{variant}/{emotion}^.png changed a canonical upstream portrait")
            else:
                expected = normal[emotion].transpose(Image.Transpose.FLIP_LEFT_RIGHT)
                if ImageChops.difference(expected, mirror[emotion]).getbbox() is not None:
                    fail(f"{variant}/{emotion}^ is not the exact generated horizontal mirror")

        sheet = Image.open(out / "Sheet.png").convert("RGB")
        if sheet.size != (200, 320):
            fail(f"{variant}/Sheet.png must be 200x320")
        for index, emotion in enumerate(EMOTIONS):
            x, y = (index % 5) * 40, (index // 5) * 40
            if ImageChops.difference(sheet.crop((x, y, x + 40, y + 40)), normal[emotion]).getbbox() is not None:
                fail(f"{variant}: normal tile out of order: {emotion}")
            if ImageChops.difference(sheet.crop((x, y + 160, x + 40, y + 200)), mirror[emotion]).getbbox() is not None:
                fail(f"{variant}: mirrored tile out of order: {emotion}")

        actual = {path.name for path in out.iterdir() if path.is_file()}
        if actual != expected_names():
            fail(f"{variant}: unexpected files: " + ", ".join(sorted(actual ^ expected_names())))
        archive_path = ROOT / f"portrait-1024-{variant.replace('/', '-')}.zip"
        if not archive_path.is_file():
            fail(f"missing {archive_path.name}")
        with zipfile.ZipFile(archive_path) as archive:
            if set(archive.namelist()) != actual:
                fail(f"{archive_path.name} does not match {variant}")
        aggregate_expected.update({variant.rstrip("/") + "/" + name for name in actual})

    if not AGGREGATE.is_file():
        fail("missing portrait-1024.zip")
    with zipfile.ZipFile(AGGREGATE) as archive:
        if set(archive.namelist()) != aggregate_expected:
            fail("portrait-1024.zip does not match all three form folders")

    print("PASS: 3 Terapagos forms, 60 normal + 60 mirrored portraits")
    print("PASS: all tiles are 40x40 and use at most 15 colors")
    print("PASS: every canonical upstream PNG is preserved byte-for-byte")
    print("PASS: generated mirrors and SpriteBot sheets are structurally valid")
    print("PASS: 3 variant archives and portrait-1024.zip match their folders")


if __name__ == "__main__":
    main()
