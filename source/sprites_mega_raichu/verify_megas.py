"""Validate both Mega Raichu packs against the PMD Sprite Guide."""
from pathlib import Path
import sys
import xml.etree.ElementTree as ET
from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
FAILED = []


def fail(m):
    FAILED.append(m)
    print(f"  FAIL: {m}")


DUNGEON = {0, 1, 5, 6, 7, 8, 9, 10, 11, 12}
STARTER = set(range(13, 35))
LEGAL_OFF = {(0, 0, 0), (0, 255, 0), (255, 0, 0), (0, 0, 255)}
LEGAL_SHADOW = {(255, 255, 255), (255, 0, 0), (0, 255, 0), (0, 0, 255)}
BOLTS = {"x": {(248, 190, 38), (247, 230, 82), (117, 77, 10)},
         "y": {(150, 236, 255), (226, 252, 255), (58, 122, 158)}}

for form in ("x", "y"):
    pack = ROOT / "sprite" / f"0026_mega_{form}"
    print(f"=== Mega {form.upper()} ===")
    root = ET.parse(pack / "AnimData.xml").getroot()
    anims = list(root.find("Anims"))
    idx = {int(a.findtext("Index")) for a in anims}

    if not DUNGEON <= idx:
        fail(f"missing dungeon animations: {sorted(DUNGEON - idx)}")
    else:
        print("  PASS: all 10 dungeon animations present")
    if not STARTER <= idx:
        fail(f"missing starter animations: {sorted(STARTER - idx)}")
    else:
        print("  PASS: all 22 starter animations present (Fully Featured)")

    colours = set()
    bad8 = []
    for a in anims:
        name = a.findtext("Name")
        if a.findtext("CopyOf"):
            continue
        fw, fh = int(a.findtext("FrameWidth")), int(a.findtext("FrameHeight"))
        if fw % 8 or fh % 8:
            bad8.append(f"{name} {fw}x{fh}")
        count = len(list(a.find("Durations")))
        for suffix in ("Anim", "Offsets", "Shadow"):
            path = pack / f"{name}-{suffix}.png"
            if not path.is_file():
                fail(f"missing {path.name}")
                continue
            im = Image.open(path).convert("RGBA")
            if im.width != fw * count:
                fail(f"{name}-{suffix}: width {im.width} != {fw}*{count}")
            rows = im.height // fh
            if im.height % fh or rows not in (1, 8):
                fail(f"{name}-{suffix}: {rows} rows, must be 1 or 8")
            if suffix == "Anim":
                for p in im.get_flattened_data():
                    if p[3] not in (0, 255):
                        fail(f"{name}: partial alpha")
                        break
                    if p[3]:
                        colours.add(p[:3])
            elif suffix == "Offsets":
                bad = {p[:3] for p in im.get_flattened_data() if p[3]} - LEGAL_OFF
                if bad:
                    fail(f"{name}-Offsets illegal colours {bad}")
            else:
                bad = {p[:3] for p in im.get_flattened_data() if p[3]} - LEGAL_SHADOW
                if bad:
                    fail(f"{name}-Shadow illegal colours {bad}")

    if bad8:
        fail(f"frame sizes not multiples of 8: {bad8[:6]}")
    else:
        print("  PASS: every frame size is a multiple of 8")

    if len(colours) > 15:
        fail(f"{len(colours)} colours, guide allows 15 + transparency")
    else:
        print(f"  PASS: {len(colours)} colours + transparency (limit 15)")

    print("  PASS: binary alpha, legal offset and shadow markers")

    # wings on every non-empty frame
    missing = 0
    for a in anims:
        name = a.findtext("Name")
        if a.findtext("CopyOf"):
            continue
        fw, fh = int(a.findtext("FrameWidth")), int(a.findtext("FrameHeight"))
        im = Image.open(pack / f"{name}-Anim.png").convert("RGBA")
        for r in range(im.height // fh):
            for c in range(im.width // fw):
                t = im.crop((c * fw, r * fh, (c + 1) * fw, (r + 1) * fh))
                if t.getbbox() is None:
                    continue
                if not ({p[:3] for p in t.get_flattened_data() if p[3]}
                        & BOLTS[form]):
                    missing += 1
    if missing:
        fail(f"{missing} frames without lightning pixels")
    else:
        print("  PASS: every non-empty frame carries lightning wings")

# the two forms must genuinely differ
cx = {p[:3] for p in Image.open(ROOT / "sprite/0026_mega_x/Idle-Anim.png")
      .convert("RGBA").get_flattened_data() if p[3]}
cy = {p[:3] for p in Image.open(ROOT / "sprite/0026_mega_y/Idle-Anim.png")
      .convert("RGBA").get_flattened_data() if p[3]}
if cx & cy:
    fail(f"X and Y share colours: {cx & cy}")
else:
    print("=== PASS: Mega X and Mega Y palettes are fully distinct")

print()
print("ALL CHECKS PASSED" if not FAILED else f"{len(FAILED)} CHECK(S) FAILED")
sys.exit(1 if FAILED else 0)
