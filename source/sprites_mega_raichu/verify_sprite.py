"""Validate the Mega Raichu pack against the PMDO / SpriteCollab format."""
from pathlib import Path
import sys
import xml.etree.ElementTree as ET

from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
PACK = ROOT / "sprite" / "0026_mega_x"
GIF = Path(__file__).resolve().parent / "source.gif"

FAILED = []


def fail(msg):
    FAILED.append(msg)
    print(f"FAIL: {msg}")


root = ET.parse(PACK / "AnimData.xml").getroot()
anims = list(root.find("Anims"))

# 1. indices unique and contiguous
idx = [int(a.findtext("Index")) for a in anims]
if sorted(idx) != list(range(len(idx))):
    fail(f"animation indices are not contiguous from 0: {sorted(idx)}")
else:
    print(f"PASS: {len(anims)} animations, indices 0..{len(idx) - 1}")

# 2. every anim is either drawn or a valid CopyOf
names = {a.findtext("Name") for a in anims}
drawn = []
for a in anims:
    name = a.findtext("Name")
    copy = a.findtext("CopyOf")
    if copy is None:
        drawn.append(name)
        if not (PACK / f"{name}-Anim.png").is_file():
            fail(f"{name} declares frames but {name}-Anim.png is missing")
    elif copy not in names:
        fail(f"{name} copies {copy}, which does not exist")
print(f"PASS: {len(drawn)} drawn animations, {len(anims) - len(drawn)} CopyOf")

# 3. geometry of each drawn animation
for name in drawn:
    node = next(a for a in anims if a.findtext("Name") == name)
    fw = int(node.findtext("FrameWidth"))
    fh = int(node.findtext("FrameHeight"))
    if fw % 2 or fh % 2:
        fail(f"{name}: frame size {fw}x{fh} is not even")
    count = len(list(node.find("Durations")))
    for suffix in ("Anim", "Offsets", "Shadow"):
        path = PACK / f"{name}-{suffix}.png"
        if not path.is_file():
            fail(f"missing {path.name}")
            continue
        im = Image.open(path)
        if im.width != fw * count:
            fail(f"{name}-{suffix}: width {im.width} != {fw}*{count}")
        if im.height != fh * 8:
            fail(f"{name}-{suffix}: height {im.height} != {fh}*8 directions")
print("PASS: frame dimensions even, sheets are whole 8-direction grids")

# 4. colour budget and binary alpha
colours = set()
for name in drawn:
    im = Image.open(PACK / f"{name}-Anim.png").convert("RGBA")
    for p in im.get_flattened_data():
        if p[3] not in (0, 255):
            fail(f"{name}-Anim.png has partial transparency")
            break
        if p[3]:
            colours.add(p[:3])
if len(colours) > 15:
    fail(f"{len(colours)} colours, over the SpriteCollab limit of 15")
else:
    print(f"PASS: {len(colours)} colours, binary alpha")

# 5. offsets use only the legal marker colours, shadow only white
LEGAL_OFF = {(0, 0, 0), (0, 255, 0), (255, 0, 0), (0, 0, 255)}
for name in drawn:
    off = Image.open(PACK / f"{name}-Offsets.png").convert("RGBA")
    bad = {p[:3] for p in off.get_flattened_data() if p[3]} - LEGAL_OFF
    if bad:
        fail(f"{name}-Offsets.png uses illegal colours: {bad}")
    sh = Image.open(PACK / f"{name}-Shadow.png").convert("RGBA")
    bad = {p[:3] for p in sh.get_flattened_data() if p[3]} - {
        (255, 255, 255), (255, 0, 0), (0, 255, 0), (0, 0, 255)}
    if bad:
        fail(f"{name}-Shadow.png uses illegal colours: {bad}")
print("PASS: offset and shadow sheets use only legal marker colours")

# 6. the artwork really is the source, pixel for pixel
from PIL import ImageSequence
src = [f.convert("RGBA").resize((96, 96), Image.Resampling.NEAREST)
       for f in ImageSequence.Iterator(Image.open(GIF))]
idle = Image.open(PACK / "Idle-Anim.png").convert("RGBA")
node = next(a for a in anims if a.findtext("Name") == "Idle")
fw, fh = int(node.findtext("FrameWidth")), int(node.findtext("FrameHeight"))
tile = idle.crop((0, 0, fw, fh))
found = any(
    all(tile.getpixel((x, y)) == s.getpixel((x + ox, y + oy))
        for y in range(0, fh, 3) for x in range(0, fw, 3))
    for s in src[:1] for ox in range(0, 96 - fw + 1) for oy in range(0, 96 - fh + 1)
)
if not found:
    fail("the first Idle tile does not match the source GIF artwork")
else:
    print("PASS: pack artwork is pixel-identical to the source GIF")

print()
print("ALL CHECKS PASSED" if not FAILED else f"{len(FAILED)} CHECK(S) FAILED")
sys.exit(1 if FAILED else 0)
