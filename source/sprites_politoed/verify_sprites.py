"""Validate the Politoed sprite pack against PMD SpriteCollab rules."""
from __future__ import annotations

import zipfile
import xml.etree.ElementTree as ET
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
PACK = ROOT / "sprite" / "0186"
ZIP_PATH = ROOT / "sprite-0186.zip"
REQUIRED_STARTER = [
    "EventSleep", "Wake", "Eat", "Tumble", "Pose", "Pull", "Pain", "Float",
    "DeepBreath", "Nod", "Sit", "LookUp", "Sink", "Trip", "Laying", "LeapForth",
    "Head", "Cringe", "LostBalance", "TumbleBack", "Faint", "HitGround",
]
EXPECTED_BASE = [
    "Walk", "Attack", "Strike", "Shoot", "RearUp", "Sleep", "Hurt", "Idle",
    "Swing", "Double", "Hop", "Charge", "Rotate",
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
    alpha = im.getchannel("A")
    if alpha.getextrema()[0] not in (0, 255) or alpha.getextrema()[1] != 255:
        fail(f"{label}: alpha must be transparent or fully opaque")


def main() -> None:
    if not PACK.is_dir():
        fail("missing sprite/0186")
    tree = ET.parse(PACK / "AnimData.xml")
    root = tree.getroot()
    if root.findtext("ShadowSize") != "1":
        fail("ShadowSize must remain the canonical medium shadow")
    nodes = root.find("Anims")
    if nodes is None:
        fail("AnimData.xml has no Anims element")

    records = []
    indices = set()
    names = set()
    art_colors = set()
    for anim in nodes.findall("Anim"):
        name = anim.findtext("Name")
        index_text = anim.findtext("Index")
        if not name or index_text is None:
            fail("every Anim needs Name and Index")
        index = int(index_text)
        if name in names:
            fail(f"duplicate animation name: {name}")
        if index in indices:
            fail(f"duplicate animation index: {index}")
        names.add(name)
        indices.add(index)
        copy_of = anim.findtext("CopyOf")
        if copy_of:
            if copy_of not in names:
                fail(f"{name}: CopyOf target must precede the copy")
            records.append((name, index, None, None, 0, copy_of))
            continue
        try:
            fw = int(anim.findtext("FrameWidth", "0"))
            fh = int(anim.findtext("FrameHeight", "0"))
        except ValueError:
            fail(f"{name}: invalid frame dimensions")
        if fw <= 0 or fh <= 0 or fw % 2 or fh % 2:
            fail(f"{name}: frame dimensions must be positive and even")
        durations = anim.findall("./Durations/Duration")
        if not durations:
            fail(f"{name}: missing durations")
        count = len(durations)
        anim_path = PACK / f"{name}-Anim.png"
        offsets_path = PACK / f"{name}-Offsets.png"
        shadow_path = PACK / f"{name}-Shadow.png"
        art = image(anim_path)
        offsets = image(offsets_path)
        shadow = image(shadow_path)
        if art.size != offsets.size or art.size != shadow.size:
            fail(f"{name}: Anim, Offsets and Shadow sizes differ")
        if art.width != fw * count:
            fail(f"{name}: width {art.width} != frame width x durations ({fw * count})")
        if art.height not in (fh, fh * 8):
            fail(f"{name}: height must contain one or eight direction rows")
        if art.height != fh * (1 if art.height == fh else 8):
            fail(f"{name}: invalid row height")
        for label, aux in (("Anim", art), ("Offsets", offsets), ("Shadow", shadow)):
            check_binary_alpha(aux, f"{name}-{label}.png")
        frame_count = art.width // fw
        row_count = art.height // fh
        for row in range(row_count):
            for col in range(frame_count):
                box = (col * fw, row * fh, (col + 1) * fw, (row + 1) * fh)
                offset_frame = offsets.crop(box)
                shadow_frame = shadow.crop(box)
                off = {c[:3] for c in offset_frame.getdata() if c[3]}
                sh = {c[:3] for c in shadow_frame.getdata() if c[3]}
                if not OFFSET_COLORS.issuperset(off):
                    fail(f"{name} frame {row},{col}: unknown offset color")
                if not SHADOW_COLORS.issuperset(sh):
                    fail(f"{name} frame {row},{col}: unknown shadow color")
                if not {(0, 0, 0), (0, 255, 0)}.issubset(off):
                    fail(f"{name} frame {row},{col}: missing head/body offset markers")
                if not SHADOW_COLORS.issubset(sh):
                    fail(f"{name} frame {row},{col}: incomplete PMD shadow")
        art_colors.update(c[:3] for c in art.getdata() if c[3])
        records.append((name, index, fw, fh, count, None))

    expected = set(EXPECTED_BASE + REQUIRED_STARTER)
    if not expected.issubset(names):
        fail("missing animations: " + ", ".join(sorted(expected - names)))
    if not set(range(35)).issubset(indices):
        fail("indices 0-34 must all be present")
    if len(art_colors) > 15:
        fail(f"sprite art uses {len(art_colors)} colors; maximum is 15")

    # SpriteBot accepts only files represented by AnimData.xml (plus credits).
    allowed = {"AnimData.xml", "credits.txt"}
    for name, _index, _fw, _fh, _count, copy_of in records:
        if copy_of is None:
            allowed.update({f"{name}-{part}.png" for part in ("Anim", "Offsets", "Shadow")})
    actual = {p.name for p in PACK.iterdir() if p.is_file()}
    if actual != allowed:
        fail("unexpected or missing files: " + ", ".join(sorted(actual ^ allowed)))

    if not ZIP_PATH.is_file():
        fail("missing sprite-0186.zip")
    with zipfile.ZipFile(ZIP_PATH) as archive:
        zipped = set(archive.namelist())
        if zipped != actual:
            fail("sprite-0186.zip does not exactly match sprite/0186")

    print(f"PASS: {len(records)} AnimData entries, indices 0-34 present")
    print(f"PASS: {len(names)} animation names, <=15 shared sprite colors, binary alpha")
    print("PASS: every non-copy animation has aligned Anim/Offsets/Shadow sheets")
    print("PASS: PMD offset markers and 3-size shadows are valid for every frame")
    print("PASS: sprite-0186.zip exactly matches the SpriteCollab multi-sheet folder")


if __name__ == "__main__":
    main()
