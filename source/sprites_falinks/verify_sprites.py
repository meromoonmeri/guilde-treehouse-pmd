"""Validate the Falinks #0870 form 0 sprite folder against SpriteCollab rules."""
from pathlib import Path
import xml.etree.ElementTree as ET

from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
PACK = ROOT / "sprite" / "0870"
CANON = Path(__file__).resolve().parent / "canonical"

SHADOW_COLORS = {(0, 0, 0, 0), (255, 255, 255, 255), (255, 0, 0, 255),
                 (0, 255, 0, 255), (0, 0, 255, 255)}
OFFSET_COLORS = {(0, 0, 0, 0), (0, 0, 0, 255), (0, 255, 0, 255),
                 (255, 0, 0, 255), (0, 0, 255, 255)}


def fail(message):
    raise SystemExit("FAIL: " + message)


root = ET.parse(PACK / "AnimData.xml").getroot()
if root.findtext("ShadowSize") is None:
    fail("AnimData.xml has no ShadowSize")

canon_palette = set()
for name in ("brass", "trooper"):
    sheet = Image.open(CANON / name / "Idle-Anim.png").convert("RGBA")
    canon_palette |= {p[:3] for p in sheet.get_flattened_data() if p[3]}

anims = list(root.find("Anims"))
names = [a.findtext("Name") for a in anims]
indices = [int(a.findtext("Index")) for a in anims]
if len(set(indices)) != len(indices):
    fail("duplicate animation indices")
if "Walk" not in names or "Idle" not in names:
    fail("Walk and Idle are mandatory")

palette = set()
for anim in anims:
    name = anim.findtext("Name")
    if anim.findtext("CopyOf"):
        if anim.findtext("CopyOf") not in names:
            fail(f"{name}: CopyOf target missing")
        continue

    width = int(anim.findtext("FrameWidth"))
    height = int(anim.findtext("FrameHeight"))
    if width % 2 or height % 2:
        fail(f"{name}: frame dimensions must be even, got {width}x{height}")

    durations = [d.text for d in anim.find("Durations")]
    if not durations:
        fail(f"{name}: no durations")

    sizes = {}
    for kind in ("Anim", "Offsets", "Shadow"):
        path = PACK / f"{name}-{kind}.png"
        if not path.is_file():
            fail(f"missing {path.relative_to(ROOT)}")
        sheet = Image.open(path).convert("RGBA")
        if sheet.width % width or sheet.height % height:
            fail(f"{name}-{kind}: {sheet.size} is not a whole grid of {width}x{height}")
        sizes[kind] = sheet.size

        cols = sheet.width // width
        if cols < len(durations):
            fail(f"{name}-{kind}: {cols} columns for {len(durations)} durations")

        colors = {p for p in sheet.get_flattened_data()}
        if kind == "Anim":
            for r, g, b, a in colors:
                if a not in (0, 255):
                    fail(f"{name}-Anim: semi-transparent pixel, alpha must be 0 or 255")
                if a:
                    palette.add((r, g, b))
        elif kind == "Shadow":
            if not colors <= SHADOW_COLORS:
                fail(f"{name}-Shadow: unexpected colours {colors - SHADOW_COLORS}")
        else:
            if not colors <= OFFSET_COLORS:
                fail(f"{name}-Offsets: unexpected colours {colors - OFFSET_COLORS}")

    if len(set(sizes.values())) != 1:
        fail(f"{name}: Anim/Offsets/Shadow sheets differ in size {sizes}")

if len(palette) > 15:
    fail(f"shared palette has {len(palette)} colours, maximum is 15")
if not palette <= canon_palette:
    fail(f"colours outside the canonical Falinks palette: {palette - canon_palette}")

print(f"PASS: {len(anims)} animations declared, indices unique")
print("PASS: all frame dimensions even, sheets are whole grids")
print("PASS: Anim/Offsets/Shadow sheets agree in size for every animation")
print("PASS: transparency is binary, shadow and offset colours are legal")
print(f"PASS: shared palette is {len(palette)} colours, all from the canonical "
      "Brass/Trooper sheets")
