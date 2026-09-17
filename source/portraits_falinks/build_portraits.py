"""Build Falinks #0870 PMD portrait expressions from the canonical base.

The existing SpriteCollab Normal portrait is copied byte-for-byte.  Every
other expression is a small, hand-authored pixel correction on that exact
portrait: background, helmet silhouette and palette stay Falinks-native.
Mirrors and the SpriteBot sheet are generated deterministically.
"""
from __future__ import annotations

import shutil
import zipfile
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
REFERENCE = ROOT / "source" / "portraits_falinks" / "reference"
OUT = ROOT / "portrait" / "0870" / "0002"
ZIP_OUT = ROOT / "portrait-0870-0002.zip"
ZIP_ALIAS = ROOT / "portrait-0870.zip"
SIZE = (40, 40)

EMOTIONS = [
    "Normal", "Happy", "Pain", "Angry", "Worried", "Sad", "Crying", "Shouting",
    "Teary-Eyed", "Determined", "Joyous", "Inspired", "Surprised", "Dizzy",
    "Special0", "Special1", "Sigh", "Stunned", "Special2", "Special3",
]

# Exact colors found in portrait/0870/0002/Normal.png.  No new color is
# introduced by an expression; the base background is never repainted.
DARK = (57, 60, 41)
OUTLINE = (33, 41, 41)
WHITE = (246, 250, 246)
LIGHT_BLUE = (135, 199, 207)
BLUE = (58, 155, 202)
RED = (180, 36, 32)
GOLD = (238, 198, 65)
LIGHT = (231, 247, 175)

# The commander visor/eyes in the supplied 40px portrait.  These are kept
# inside the face; the large red crest and PMD background are untouched.
LEFT_EYE = [(16, 21), (17, 20), (18, 20), (19, 20), (20, 21),
            (16, 22), (17, 22), (18, 22), (19, 22), (20, 22),
            (16, 23), (17, 23), (18, 23), (19, 23), (20, 23),
            (17, 24), (18, 24), (19, 24), (20, 24)]
RIGHT_EYE = [(27, 19), (28, 19), (29, 19), (30, 20),
             (27, 20), (28, 20), (29, 20), (30, 21),
             (27, 21), (28, 21), (29, 21), (30, 22),
             (27, 22), (28, 22), (29, 22), (30, 23),
             (28, 24), (29, 24)]


def _paint(image: Image.Image, points: list[tuple[int, int]], color: tuple[int, int, int]) -> None:
    for x, y in points:
        if 0 <= x < 40 and 0 <= y < 40:
            image.putpixel((x, y), color)


def _eye_clear(image: Image.Image) -> None:
    _paint(image, LEFT_EYE + RIGHT_EYE, DARK)


def _eyes_closed(image: Image.Image) -> None:
    _eye_clear(image)
    _paint(image, [(16, 23), (17, 23), (18, 22), (19, 23), (20, 23),
                   (27, 22), (28, 22), (29, 21), (30, 22)], OUTLINE)
    _paint(image, [(17, 22), (18, 22), (19, 22), (28, 21), (29, 21)], LIGHT_BLUE)


def _eyes_wide(image: Image.Image) -> None:
    _eye_clear(image)
    _paint(image, [(17, 20), (18, 20), (19, 20), (18, 21),
                   (28, 19), (29, 19), (29, 20)], WHITE)
    _paint(image, [(18, 22), (19, 22), (29, 21)], BLUE)


def _eyes_narrow(image: Image.Image) -> None:
    _eye_clear(image)
    _paint(image, [(17, 22), (18, 22), (19, 22), (20, 22),
                   (28, 21), (29, 21), (30, 21)], LIGHT_BLUE)
    _paint(image, [(18, 23), (29, 22)], OUTLINE)


def _eyes_angry(image: Image.Image) -> None:
    _eyes_narrow(image)
    _paint(image, [(16, 19), (17, 19), (18, 20), (19, 20),
                   (28, 18), (29, 18), (30, 19)], RED)


def _eyes_sad(image: Image.Image) -> None:
    _eye_clear(image)
    _paint(image, [(16, 20), (17, 20), (18, 21), (19, 21), (20, 22),
                   (27, 19), (28, 19), (29, 20), (30, 21)], LIGHT_BLUE)
    _paint(image, [(18, 22), (29, 21)], BLUE)


def _eyes_dizzy(image: Image.Image) -> None:
    _eye_clear(image)
    _paint(image, [(17, 21), (18, 22), (19, 21), (18, 23),
                   (28, 20), (29, 21), (30, 20), (29, 22)], WHITE)
    _paint(image, [(18, 21), (29, 20)], BLUE)


def _mouth(image: Image.Image, kind: str) -> None:
    if kind == "open":
        _paint(image, [(21, 27), (22, 27), (23, 27), (24, 27), (25, 27)], OUTLINE)
        _paint(image, [(22, 28), (23, 28), (24, 28)], RED)
        _paint(image, [(23, 29)], GOLD)
    elif kind == "smile":
        _paint(image, [(21, 27), (22, 28), (23, 28), (24, 28), (25, 27)], RED)
        _paint(image, [(22, 27), (23, 27), (24, 27)], GOLD)
    elif kind == "frown":
        _paint(image, [(21, 29), (22, 28), (23, 28), (24, 28), (25, 29)], OUTLINE)
    elif kind == "small":
        _paint(image, [(23, 28)], RED)
    else:
        _paint(image, [(22, 28), (23, 28), (24, 28)], DARK)


def _tears(image: Image.Image, both: bool = False) -> None:
    _paint(image, [(16, 25), (16, 26), (17, 27)], LIGHT_BLUE)
    if both:
        _paint(image, [(29, 24), (30, 25), (30, 26)], LIGHT_BLUE)


def create(emotion: str, base: Image.Image) -> Image.Image:
    if emotion == "Normal":
        return base.copy()
    image = base.copy()
    if emotion in {"Happy", "Joyous"}:
        _eyes_closed(image)
        _mouth(image, "smile")
    elif emotion in {"Angry", "Determined"}:
        _eyes_angry(image)
        _mouth(image, "flat")
    elif emotion in {"Worried", "Sad"}:
        _eyes_sad(image)
        _mouth(image, "frown")
        _tears(image, both=False)
    elif emotion in {"Crying", "Teary-Eyed"}:
        _eyes_sad(image)
        _mouth(image, "open" if emotion == "Crying" else "frown")
        _tears(image, both=emotion == "Crying")
    elif emotion in {"Pain", "Shouting", "Stunned", "Special2"}:
        _eyes_wide(image)
        _mouth(image, "open")
    elif emotion in {"Surprised", "Dizzy", "Special1"}:
        _eyes_wide(image) if emotion != "Dizzy" else _eyes_dizzy(image)
        _mouth(image, "small" if emotion == "Special1" else "open")
    elif emotion in {"Inspired", "Special0"}:
        _eyes_wide(image)
        _mouth(image, "smile")
        _paint(image, [(17, 19), (29, 18)], LIGHT)
    elif emotion == "Sigh":
        _eyes_closed(image)
        _mouth(image, "frown")
        _paint(image, [(26, 27), (27, 26), (28, 27)], LIGHT_BLUE)
    elif emotion == "Special3":
        _eyes_angry(image)
        _mouth(image, "smile")
    else:
        _eye_clear(image)
        _mouth(image, "flat")
    return image


def build() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    base_path = REFERENCE / "Normal.png"
    base = Image.open(base_path).convert("RGB")
    if base.size != SIZE:
        raise ValueError(f"Falinks Normal portrait must be {SIZE}")
    # Preserve the canonical upstream Normal file byte-for-byte.
    shutil.copyfile(base_path, OUT / "Normal.png")
    for emotion in EMOTIONS[1:]:
        create(emotion, base).save(OUT / f"{emotion}.png", optimize=True)
    for emotion in EMOTIONS:
        Image.open(OUT / f"{emotion}.png").transpose(Image.Transpose.FLIP_LEFT_RIGHT).save(
            OUT / f"{emotion}^.png", optimize=True
        )

    sheet = Image.new("RGB", (200, 320))
    for index, emotion in enumerate(EMOTIONS):
        normal = Image.open(OUT / f"{emotion}.png").convert("RGB")
        x, y = (index % 5) * 40, (index // 5) * 40
        sheet.paste(normal, (x, y))
        sheet.paste(normal.transpose(Image.Transpose.FLIP_LEFT_RIGHT), (x, y + 160))
    sheet.save(OUT / "Sheet.png", optimize=True)

    credits = (REFERENCE / "credits.txt").read_text(encoding="utf-8").rstrip() + "\n"
    credits += "2026-09-17\tmeromoonmeri / Arena.ai Agent\tNEW\t" + ", ".join(EMOTIONS[1:]) + "\n"
    (OUT / "credits.txt").write_text(credits, encoding="utf-8")

    with zipfile.ZipFile(ZIP_OUT, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for path in sorted(OUT.iterdir()):
            if not path.is_file():
                continue
            info = zipfile.ZipInfo(path.name, date_time=(2020, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o644 << 16
            archive.writestr(info, path.read_bytes())
    shutil.copyfile(ZIP_OUT, ZIP_ALIAS)
    print(f"Wrote {len(EMOTIONS)} Falinks portraits and exact mirrors to {OUT}")
    print(f"Wrote {ZIP_OUT}")


if __name__ == "__main__":
    build()
