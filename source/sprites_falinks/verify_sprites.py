"""Validate the Falinks #0870 SpriteCollab pack."""
from __future__ import annotations

import zipfile
import xml.etree.ElementTree as ET
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
PACK = ROOT / "sprite" / "0870" / "0002"
CANONICAL = ROOT / "source" / "sprites_falinks" / "canonical"
ZIP_PATH = ROOT / "sprite-0870-0002.zip"
ZIP_ALIAS = ROOT / "sprite-0870.zip"
BASE = [
    "Walk", "Attack", "Strike", "Shoot", "RearUp", "Sleep", "Hurt", "Idle",
    "Swing", "Double", "Hop", "Charge", "Rotate",
]
STARTER = [
    "EventSleep", "Wake", "Eat", "Tumble", "Pose", "Pull", "Pain", "Float",
    "DeepBreath", "Nod", "Sit", "LookUp", "Sink", "Trip", "Laying", "LeapForth",
    "Head", "Cringe", "LostBalance", "TumbleBack", "Faint", "HitGround",
]
OFFSET_COLORS = {(0, 0, 0), (0, 255, 0), (255, 0, 0), (0, 0, 255)}
SHADOW_COLORS = {(255, 255, 255), (0, 255, 0), (255, 0, 0), (0, 0, 255)}


def fail(message: str) -> None:
    raise SystemExit("FAIL: " + message)


def image(path: Path) -> Image.Image:
    if not path.is_file():
        fail(f"missing {path.relative_to(ROOT)}")
    return Image.open(path).convert("RGBA")


def check_binary_alpha(im: Image.Image, label: str) -> None:
    extrema = im.getchannel("A").getextrema()
    if extrema[0] not in (0, 255) or extrema[1] != 255:
        fail(f"{label}: alpha must be transparent or fully opaque")


def main() -> None:
    if not PACK.is_dir():
        fail("missing sprite/0870/0002")
    tree = ET.parse(PACK / "AnimData.xml")
    root = tree.getroot()
    if root.findtext("ShadowSize") != "1":
        fail("ShadowSize must remain 1")
    nodes = root.find("Anims")
    if nodes is None:
        fail("AnimData.xml has no Anims element")

    names: set[str] = set()
    indices: set[int] = set()
    records: list[tuple[str, int, str | None]] = []
    art_colors: set[tuple[int, int, int]] = set()
    for anim in nodes.findall("Anim"):
        name = anim.findtext("Name")
        index_text = anim.findtext("Index")
        if not name or index_text is None:
            fail("every Anim needs Name and Index")
        index = int(index_text)
        if name in names or index in indices:
            fail(f"duplicate animation name/index: {name}/{index}")
        names.add(name)
        indices.add(index)
        copy_of = anim.findtext("CopyOf")
        if copy_of:
            if copy_of not in names:
                fail(f"{name}: CopyOf target must precede the copy")
            records.append((name, index, copy_of))
            continue

        fw = int(anim.findtext("FrameWidth", "0"))
        fh = int(anim.findtext("FrameHeight", "0"))
        if fw <= 0 or fh <= 0 or fw % 2 or fh % 2:
            fail(f"{name}: frame dimensions must be positive and even")
        durations = anim.findall("./Durations/Duration")
        if not durations:
            fail(f"{name}: missing durations")
        art = image(PACK / f"{name}-Anim.png")
        offsets = image(PACK / f"{name}-Offsets.png")
        shadows = image(PACK / f"{name}-Shadow.png")
        if art.size != offsets.size or art.size != shadows.size:
            fail(f"{name}: Anim/Offsets/Shadow sizes differ")
        if art.width != fw * len(durations):
            fail(f"{name}: wrong sheet width")
        if art.height not in (fh, fh * 8):
            fail(f"{name}: height must contain one or eight direction rows")
        for label, sheet in (("Anim", art), ("Offsets", offsets), ("Shadow", shadows)):
            check_binary_alpha(sheet, f"{name}-{label}.png")

        rows = art.height // fh
        for row in range(rows):
            for col in range(len(durations)):
                box = (col * fw, row * fh, (col + 1) * fw, (row + 1) * fh)
                off = {p[:3] for p in offsets.crop(box).getdata() if p[3]}
                shadow = {p[:3] for p in shadows.crop(box).getdata() if p[3]}
                if not OFFSET_COLORS.issuperset(off):
                    fail(f"{name} frame {row},{col}: invalid offset color")
                if not SHADOW_COLORS.issuperset(shadow):
                    fail(f"{name} frame {row},{col}: invalid shadow color")
                if not {(0, 0, 0), (0, 255, 0)}.issubset(off):
                    fail(f"{name} frame {row},{col}: missing head/body offsets")
                if not SHADOW_COLORS.issubset(shadow):
                    fail(f"{name} frame {row},{col}: incomplete shadow")
        art_colors.update(p[:3] for p in art.getdata() if p[3])
        records.append((name, index, None))

    expected = set(BASE + STARTER)
    if expected != names:
        fail("animation name mismatch: " + ", ".join(sorted(expected ^ names)))
    if indices != set(range(35)):
        fail("indices must be exactly 0-34")
    if len(art_colors) > 15:
        fail(f"art uses {len(art_colors)} colors; maximum is 15")

    # Existing official dungeon sheets must be copied byte-for-byte.
    for path in CANONICAL.iterdir():
        if path.name in {"AnimData.xml", "credits.txt"}:
            continue
        if path.read_bytes() != (PACK / path.name).read_bytes():
            fail(f"canonical base changed: {path.name}")

    allowed = {"AnimData.xml", "credits.txt"}
    for name, _index, copy_of in records:
        if copy_of is None:
            allowed.update({f"{name}-{part}.png" for part in ("Anim", "Offsets", "Shadow")})
    actual = {path.name for path in PACK.iterdir() if path.is_file()}
    if actual != allowed:
        fail("unexpected or missing pack files: " + ", ".join(sorted(actual ^ allowed)))

    if not ZIP_PATH.is_file():
        fail("missing sprite-0870-0002.zip")
    with zipfile.ZipFile(ZIP_PATH) as archive:
        if set(archive.namelist()) != actual:
            fail("sprite-0870-0002.zip does not match sprite/0870/0002")
    if not ZIP_ALIAS.is_file() or ZIP_ALIAS.read_bytes() != ZIP_PATH.read_bytes():
        fail("sprite-0870.zip is not a byte-for-byte archive alias")

    print("PASS: 35 Falinks AnimData entries, indices 0-34 present")
    print("PASS: canonical dungeon sheets unchanged byte-for-byte")
    print("PASS: palette <=15 colors, binary alpha, aligned PMD sheets")
    print("PASS: PMD offsets and three-size shadows valid for every frame")
    print("PASS: sprite-0870-0002.zip exactly matches the SpriteCollab folder")
    print("PASS: sprite-0870.zip is a byte-for-byte compatibility alias")


if __name__ == "__main__":
    main()
