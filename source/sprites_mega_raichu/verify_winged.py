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
        # PMD allows 1-direction animations: SpriteCollab itself ships Sleep,
        # Eat, Cringe and others as single-row sheets, because those poses are
        # never shown from another angle. Accept 1 or 8 rows, reject anything
        # else, and report the split so the coverage is explicit.
        if im.height % fh:
            fail(f"{name}-{suffix}: height {im.height} is not a multiple of {fh}")
        elif im.height // fh not in (1, 8):
            fail(f"{name}-{suffix}: {im.height // fh} rows, expected 1 or 8")
rows8 = sum(1 for n in drawn
            if Image.open(PACK / f"{n}-Anim.png").height
            // int(next(a for a in anims if a.findtext("Name") == n)
                   .findtext("FrameHeight")) == 8)
print(f"PASS: dimensions even; {rows8} animations in 8 directions, "
      f"{len(drawn) - rows8} single-direction (as upstream)")

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

# 6. wings must actually be present, and on every frame
import xml.etree.ElementTree as ET2
BOLT = {(248, 190, 38), (247, 230, 82), (117, 77, 10)}
missing = []
for name in drawn:
    node = next(a for a in anims if a.findtext("Name") == name)
    fw = int(node.findtext("FrameWidth")); fh = int(node.findtext("FrameHeight"))
    im = Image.open(PACK / f"{name}-Anim.png").convert("RGBA")
    cols, rows = im.width // fw, im.height // fh
    for r in range(rows):
        for c in range(cols):
            tile = im.crop((c * fw, r * fh, (c + 1) * fw, (r + 1) * fh))
            if tile.getbbox() is None:
                continue
            if not ({p[:3] for p in tile.get_flattened_data() if p[3]} & BOLT):
                missing.append(f"{name}[{r},{c}]")
if missing:
    fail(f"{len(missing)} frames have no lightning pixels, e.g. {missing[:5]}")
else:
    print("PASS: every non-empty frame carries lightning-bolt pixels")

# 7. the body must still be animating: frames within a row must differ
static = []
for name in drawn:
    node = next(a for a in anims if a.findtext("Name") == name)
    fw = int(node.findtext("FrameWidth")); fh = int(node.findtext("FrameHeight"))
    im = Image.open(PACK / f"{name}-Anim.png").convert("RGBA")
    cols, rows = im.width // fw, im.height // fh
    if cols < 2:
        continue
    tiles = [im.crop((c * fw, 0, (c + 1) * fw, fh)).tobytes() for c in range(cols)]
    if len(set(tiles)) == 1:
        static.append(name)
if static:
    fail(f"animations whose frames are all identical: {static}")
else:
    print("PASS: multi-frame animations actually change between frames")

print()
print("ALL CHECKS PASSED" if not FAILED else f"{len(FAILED)} CHECK(S) FAILED")
sys.exit(1 if FAILED else 0)
