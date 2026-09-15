"""Validate the generated Mega Raichu pack (sprite/0026_mega_x_gen)."""
from pathlib import Path
import sys
import xml.etree.ElementTree as ET
from PIL import Image, ImageSequence

ROOT = Path(__file__).resolve().parents[2]
PACK = ROOT / "sprite" / "0026_mega_x_gen"
GIF = Path(__file__).resolve().parent / "source.gif"

FAILED = []
def fail(m):
    FAILED.append(m); print(f"FAIL: {m}")

root = ET.parse(PACK / "AnimData.xml").getroot()
anims = list(root.find("Anims"))
node = anims[0]
fw, fh = int(node.findtext("FrameWidth")), int(node.findtext("FrameHeight"))
count = len(list(node.find("Durations")))

if fw % 2 or fh % 2:
    fail(f"frame {fw}x{fh} not even")
else:
    print(f"PASS: frame {fw}x{fh}, even dimensions")

for suffix in ("Anim", "Offsets", "Shadow"):
    im = Image.open(PACK / f"Idle-{suffix}.png")
    if im.size != (fw * count, fh * 8):
        fail(f"Idle-{suffix}: {im.size} != {(fw*count, fh*8)}")
print(f"PASS: sheets are {count} frames x 8 directions")

anim = Image.open(PACK / "Idle-Anim.png").convert("RGBA")
bad = [p[3] for p in anim.get_flattened_data() if p[3] not in (0, 255)]
if bad:
    fail(f"{len(bad)} pixels with partial alpha")
else:
    print("PASS: binary alpha")

colours = {p[:3] for p in anim.get_flattened_data() if p[3]}
if len(colours) > 15:
    fail(f"{len(colours)} colours, over the limit of 15")
else:
    print(f"PASS: {len(colours)} colours")

src = set()
for f in ImageSequence.Iterator(Image.open(GIF)):
    fr = f.convert("RGBA").resize((96, 96), Image.Resampling.NEAREST)
    src |= {p[:3] for p in fr.get_flattened_data() if p[3]}
stray = colours - src
if stray:
    fail(f"colours not present in the Mega artwork: {stray}")
else:
    print("PASS: every colour comes from the original Mega artwork")

LEGAL = {(0, 0, 0), (0, 255, 0), (255, 0, 0), (0, 0, 255)}
off = Image.open(PACK / "Idle-Offsets.png").convert("RGBA")
bad = {p[:3] for p in off.get_flattened_data() if p[3]} - LEGAL
if bad:
    fail(f"illegal offset colours: {bad}")
sh = Image.open(PACK / "Idle-Shadow.png").convert("RGBA")
bad = {p[:3] for p in sh.get_flattened_data() if p[3]} - {(255, 255, 255)}
if bad:
    fail(f"illegal shadow colours: {bad}")
print("PASS: marker sheets legal")

# every direction must actually contain art, and they must differ from
# each other: that is the whole point of a rotation sheet
tiles = [anim.crop((0, r * fh, fw, (r + 1) * fh)) for r in range(8)]
empty = [i for i, t in enumerate(tiles) if t.getbbox() is None]
if empty:
    fail(f"empty direction rows: {empty}")
same = sum(1 for i in range(8) for j in range(i + 1, 8)
           if tiles[i].tobytes() == tiles[j].tobytes())
if same:
    fail(f"{same} pairs of identical direction rows")
else:
    print("PASS: all 8 directions are distinct, none empty")

print()
print("ALL CHECKS PASSED" if not FAILED else f"{len(FAILED)} CHECK(S) FAILED")
sys.exit(1 if FAILED else 0)
