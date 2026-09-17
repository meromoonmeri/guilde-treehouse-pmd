"""Build complete SpriteCollab portrait packs for Terapagos / Terrapagos #1024.

Each SpriteCollab form is kept in its own variant directory.  Existing
upstream portrait files are copied byte-for-byte; missing expressions are
constructed as deterministic nearest-neighbour pixel edits on that form's
canonical Normal portrait.  No form is mixed with another form.
"""
from __future__ import annotations

import shutil
import zipfile
from dataclasses import dataclass
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
REFERENCE = ROOT / "source" / "portraits_terapagos" / "reference"
OUT_ROOT = ROOT / "portrait" / "1024"
AGGREGATE_ZIP = ROOT / "portrait-1024.zip"
SIZE = (40, 40)
DATE = "2026-09-17"

EMOTIONS = [
    "Normal", "Happy", "Pain", "Angry", "Worried", "Sad", "Crying", "Shouting",
    "Teary-Eyed", "Determined", "Joyous", "Inspired", "Surprised", "Dizzy",
    "Special0", "Special1", "Sigh", "Stunned", "Special2", "Special3",
]


@dataclass(frozen=True)
class Form:
    key: str
    label: str
    canonical_path: str
    face_fill: tuple[int, int]
    eye_points: tuple[tuple[int, int], ...]
    mouth_points: tuple[tuple[int, int], ...]


# The eye masks are hand-placed against each native 40x40 portrait.  They are
# deliberately small: shell, crystal crown, background and silhouette remain
# untouched.  Coordinates are native pixels, not resized artwork.
FORMS = (
    Form(
        "0000/0001", "Normal Form", "0000/0001",
        (24, 25),
        ((16, 15), (17, 15), (18, 15), (19, 15), (20, 16), (16, 16),
         (17, 16), (18, 16), (19, 16), (20, 17), (16, 17), (17, 17),
         (18, 17), (19, 17), (20, 18), (16, 18), (17, 18), (18, 18),
         (19, 18), (20, 19), (17, 19), (18, 19), (19, 19), (18, 20),
         (19, 20), (18, 21), (19, 21), (18, 22), (19, 22), (18, 23),
         (19, 23)),
        ((22, 26), (23, 26), (24, 26), (25, 26), (26, 26),
         (22, 27), (23, 27), (24, 27), (25, 27), (26, 27),
         (23, 28), (24, 28), (25, 28)),
    ),
    Form(
        "0001", "Terastal Form", "0001",
        (22, 25),
        ((13, 21), (14, 21), (15, 21), (16, 21), (17, 22), (13, 22),
         (14, 22), (15, 22), (16, 22), (17, 23), (13, 23), (14, 23),
         (15, 23), (16, 23), (17, 24), (13, 24), (14, 24), (15, 24),
         (16, 24), (17, 25), (13, 25), (14, 25), (15, 25), (16, 25),
         (14, 26), (15, 26), (16, 26), (15, 27)),
        ((20, 28), (21, 28), (22, 28), (23, 28), (24, 28),
         (20, 29), (21, 29), (22, 29), (23, 29), (24, 29),
         (21, 30), (22, 30), (23, 30)),
    ),
    Form(
        "0002", "Stellar Form", "0002",
        (22, 25),
        ((13, 20), (14, 20), (15, 20), (16, 20), (17, 21), (13, 21),
         (14, 21), (15, 21), (16, 21), (17, 22), (13, 22), (14, 22),
         (15, 22), (16, 22), (17, 23), (13, 23), (14, 23), (15, 23),
         (16, 23), (17, 24), (13, 24), (14, 24), (15, 24), (16, 24),
         (14, 25), (15, 25), (16, 25), (15, 26)),
        ((20, 27), (21, 27), (22, 27), (23, 27), (24, 27),
         (20, 28), (21, 28), (22, 28), (23, 28), (24, 28),
         (21, 29), (22, 29), (23, 29)),
    ),
)


def _palette(base: Image.Image) -> dict[str, tuple[int, int, int]]:
    colors = [c for _count, c in base.getcolors(10_000)]
    dark = min(colors, key=lambda c: sum(c))
    white = max(colors, key=lambda c: sum(c))
    pink = max(colors, key=lambda c: (c[0] - c[1] + c[2] // 3, c[0]))
    cool = max(colors, key=lambda c: (c[2] + c[1] - c[0], sum(c)))
    mid = max(colors, key=lambda c: (sum(c), -abs(c[0] - c[2])))
    return {"dark": dark, "white": white, "pink": pink, "cool": cool, "mid": mid}


def _paint(image: Image.Image, points: tuple[tuple[int, int], ...], color: tuple[int, int, int]) -> None:
    for x, y in points:
        if 0 <= x < 40 and 0 <= y < 40:
            image.putpixel((x, y), color)


def _clear_eye(image: Image.Image, form: Form) -> None:
    fill = image.getpixel(form.face_fill)
    _paint(image, form.eye_points, fill)


def _eye_line(form: Form, row: int, slope: int = 0) -> tuple[tuple[int, int], ...]:
    """Return a small native-pixel eyelid centered in the form's eye mask."""
    points = form.eye_points
    xs = [x for x, y in points]
    ys = [y for x, y in points]
    left, right = min(xs), max(xs)
    y = min(ys) + row
    if slope < 0:
        return tuple((x, y + (x - left) // 3) for x in range(left, right + 1))
    if slope > 0:
        return tuple((x, y + (right - x) // 3) for x in range(left, right + 1))
    return tuple((x, y) for x in range(left, right + 1))


def _eyes_closed(image: Image.Image, form: Form, colors: dict[str, tuple[int, int, int]]) -> None:
    _clear_eye(image, form)
    _paint(image, _eye_line(form, 7), colors["dark"])
    _paint(image, _eye_line(form, 8), colors["cool"])


def _eyes_wide(image: Image.Image, form: Form, colors: dict[str, tuple[int, int, int]]) -> None:
    _clear_eye(image, form)
    points = form.eye_points
    # A compact white/cool oval, retaining the form's native eye placement.
    _paint(image, tuple(points[::3]), colors["white"])
    _paint(image, tuple(points[1::4]), colors["cool"])
    if len(points) > 8:
        _paint(image, (points[len(points) // 2],), colors["dark"])


def _eyes_narrow(image: Image.Image, form: Form, colors: dict[str, tuple[int, int, int]], slope: int = -1) -> None:
    _clear_eye(image, form)
    _paint(image, _eye_line(form, 7, slope), colors["dark"])
    _paint(image, _eye_line(form, 8, slope), colors["pink"])


def _eyes_sad(image: Image.Image, form: Form, colors: dict[str, tuple[int, int, int]]) -> None:
    _clear_eye(image, form)
    _paint(image, _eye_line(form, 7, 1), colors["cool"])
    _paint(image, _eye_line(form, 8, 1), colors["dark"])


def _eyes_dizzy(image: Image.Image, form: Form, colors: dict[str, tuple[int, int, int]]) -> None:
    _clear_eye(image, form)
    points = form.eye_points
    _paint(image, tuple(points[::4]), colors["white"])
    _paint(image, tuple(points[1::4]), colors["dark"])


def _mouth(image: Image.Image, form: Form, colors: dict[str, tuple[int, int, int]], kind: str) -> None:
    points = form.mouth_points
    if kind == "open":
        _paint(image, points[:5], colors["dark"])
        _paint(image, points[5:10], colors["pink"])
        _paint(image, points[10:], colors["white"])
    elif kind == "smile":
        _paint(image, points[1:4], colors["pink"])
        _paint(image, points[4:7], colors["white"])
    elif kind == "frown":
        _paint(image, points[0:2] + points[3:5] + points[6:8], colors["dark"])
    elif kind == "small":
        _paint(image, points[len(points) // 2:len(points) // 2 + 2], colors["pink"])
    else:
        _paint(image, points[1:4], colors["dark"])


def _tears(image: Image.Image, form: Form, colors: dict[str, tuple[int, int, int]], both: bool = False) -> None:
    points = form.eye_points
    left = min(x for x, _ in points)
    bottom = max(y for _, y in points)
    _paint(image, ((left, bottom + 1), (left + 1, bottom + 2)), colors["cool"])
    if both:
        right = max(x for x, _ in points)
        _paint(image, ((right, bottom), (right, bottom + 1)), colors["cool"])


def create(emotion: str, base: Image.Image, form: Form) -> Image.Image:
    if emotion == "Normal":
        return base.copy()
    image = base.copy()
    colors = _palette(base)
    if emotion in {"Happy", "Joyous"}:
        _eyes_closed(image, form, colors)
        _mouth(image, form, colors, "smile")
    elif emotion in {"Angry", "Determined", "Special3"}:
        _eyes_narrow(image, form, colors, -1)
        _mouth(image, form, colors, "flat")
    elif emotion in {"Worried", "Sad"}:
        _eyes_sad(image, form, colors)
        _mouth(image, form, colors, "frown")
        _tears(image, form, colors)
    elif emotion in {"Crying", "Teary-Eyed"}:
        _eyes_sad(image, form, colors)
        _mouth(image, form, colors, "open" if emotion == "Crying" else "frown")
        _tears(image, form, colors, both=emotion == "Crying")
    elif emotion in {"Pain", "Shouting", "Stunned", "Special2"}:
        _eyes_wide(image, form, colors)
        _mouth(image, form, colors, "open")
    elif emotion in {"Surprised", "Dizzy", "Special1"}:
        if emotion == "Dizzy":
            _eyes_dizzy(image, form, colors)
        else:
            _eyes_wide(image, form, colors)
        _mouth(image, form, colors, "small" if emotion == "Special1" else "open")
    elif emotion in {"Inspired", "Special0"}:
        _eyes_wide(image, form, colors)
        _mouth(image, form, colors, "smile")
        _paint(image, form.eye_points[::7], colors["pink"])
    elif emotion == "Sigh":
        _eyes_closed(image, form, colors)
        _mouth(image, form, colors, "frown")
        right = max(x for x, _ in form.mouth_points)
        y = min(y for _, y in form.mouth_points)
        _paint(image, ((right + 1, y), (right + 2, y - 1), (right + 3, y)), colors["cool"])
    else:
        _eyes_narrow(image, form, colors)
        _mouth(image, form, colors, "flat")
    return image


def _reference_files(form: Form) -> list[Path]:
    return [path for path in sorted((REFERENCE / form.canonical_path).iterdir()) if path.is_file()]


def _build_variant(form: Form) -> list[Path]:
    reference = REFERENCE / form.canonical_path
    out = OUT_ROOT / form.key
    out.mkdir(parents=True, exist_ok=True)
    base_path = reference / "Normal.png"
    base = Image.open(base_path).convert("RGB")
    if base.size != SIZE:
        raise ValueError(f"{form.key}: Normal portrait must be {SIZE}")

    canonical_names = {path.name for path in _reference_files(form)}
    # Copy every upstream PNG exactly, including published expression variants.
    for path in _reference_files(form):
        if path.suffix.lower() == ".png":
            shutil.copyfile(path, out / path.name)

    for emotion in EMOTIONS:
        normal_path = out / f"{emotion}.png"
        if not normal_path.exists():
            create(emotion, base, form).save(normal_path, optimize=True)
        mirror_path = out / f"{emotion}^.png"
        if not mirror_path.exists():
            Image.open(normal_path).convert("RGB").transpose(Image.Transpose.FLIP_LEFT_RIGHT).save(
                mirror_path, optimize=True
            )

    sheet = Image.new("RGB", (200, 320))
    for index, emotion in enumerate(EMOTIONS):
        normal = Image.open(out / f"{emotion}.png").convert("RGB")
        mirrored = Image.open(out / f"{emotion}^.png").convert("RGB")
        x, y = (index % 5) * 40, (index // 5) * 40
        sheet.paste(normal, (x, y))
        sheet.paste(mirrored, (x, y + 160))
    sheet.save(out / "Sheet.png", optimize=True)

    credits_path = reference / "credits.txt"
    credits = credits_path.read_text(encoding="utf-8").rstrip() + "\n"
    existing = set(canonical_names)
    generated = [name for name in EMOTIONS if f"{name}.png" not in existing]
    generated += [name + "^" for name in EMOTIONS if f"{name}^.png" not in existing]
    credits += f"{DATE}\tmeromoonmeri / Arena.ai Agent\tNEW\t" + ", ".join(generated) + "\n"
    (out / "credits.txt").write_text(credits, encoding="utf-8")

    archive_path = ROOT / f"portrait-1024-{form.key.replace('/', '-')}.zip"
    with zipfile.ZipFile(archive_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for path in sorted(out.iterdir()):
            if not path.is_file():
                continue
            info = zipfile.ZipInfo(path.name, date_time=(2020, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o644 << 16
            archive.writestr(info, path.read_bytes())
    return [path for path in out.iterdir() if path.is_file()]


def _build_aggregate() -> None:
    with zipfile.ZipFile(AGGREGATE_ZIP, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for form in FORMS:
            out = OUT_ROOT / form.key
            prefix = form.key.rstrip("/") + "/"
            for path in sorted(out.iterdir()):
                if not path.is_file():
                    continue
                info = zipfile.ZipInfo(prefix + path.name, date_time=(2020, 1, 1, 0, 0, 0))
                info.compress_type = zipfile.ZIP_DEFLATED
                info.external_attr = 0o644 << 16
                archive.writestr(info, path.read_bytes())


def build() -> None:
    for form in FORMS:
        files = _build_variant(form)
        print(f"Wrote {len(files)} Terapagos portrait files to {OUT_ROOT / form.key}")
    _build_aggregate()
    print(f"Wrote {AGGREGATE_ZIP}")


if __name__ == "__main__":
    build()
