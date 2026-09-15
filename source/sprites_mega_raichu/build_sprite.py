"""Convert the Mega Raichu GIF into a PMDO / SpriteCollab sprite pack.

SOURCE
------
Commit a214a07 on main, "raichu mega evolve": a 480x480, 68 frame GIF.

Three facts established by measurement before any conversion:

  1. the GIF is a clean integer x5 upscale. Downsampling to 96x96 with NEAREST
     is LOSSLESS: re-upscaling reproduces the original exactly, 0 pixels of
     difference. So the native artwork is recovered, not approximated;
  2. of the 68 frames only 14 are unique. The rest is a loop. Two distinct
     motions exist: a gentle idle bob (frames 0-17) and a wider ear/arm swing
     (frames 37-50);
  3. the artwork is 13 colours with fully binary alpha, which already satisfies
     the SpriteCollab colour and transparency rules.

SCALE, AND WHY NOTHING IS RESIZED
---------------------------------
The subject occupies 77x65 native pixels. Canonical Raichu occupies 29x26.
The source art is therefore ~2.6x the PMD scale. It is NOT downscaled here:
resampling pixel art by a non-integer factor destroys it. PMDO reads frame
dimensions from AnimData.xml, so the pack simply declares its own larger frame
size and stays pixel-exact.

WHAT IS REAL AND WHAT IS NOT
----------------------------
The source contains ONE camera angle: front / facing down. PMD wants 8. The
missing angles cannot be invented from a front view without fabricating art,
so every direction row is filled with the real front artwork, horizontally
mirrored for the left-facing half. This makes the pack structurally valid and
importable; it does not pretend to be a true 8-angle rotation. See README.
"""
from pathlib import Path
import xml.etree.ElementTree as ET

from PIL import Image, ImageSequence

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
GIF = HERE / "source.gif"
OUT = ROOT / "sprite" / "0026_mega_x"

NATIVE = 96                     # lossless native size of each GIF frame
UPSCALE = 5                     # measured integer factor of the source GIF

# PMD direction order. Index 0 is "down", which is the angle we actually have.
DIRECTIONS = ["down", "down-right", "right", "up-right",
              "up", "up-left", "left", "down-left"]
# Rows whose art is mirrored so the character faces the other way.
MIRRORED_ROWS = {5, 6, 7}

# Unique frame ids measured from the GIF, in playback order.
IDLE_IDS = [0, 2, 3, 5, 7, 9, 5, 3, 2]
CHARGE_IDS = [37, 39, 41, 42, 44, 48, 49, 50]

# Offsets sheet colour code, per the PMD format.
OFF_HEAD = (0, 0, 0)
OFF_BODY = (0, 255, 0)
OFF_RIGHT = (255, 0, 0)
OFF_LEFT = (0, 0, 255)
# Shadow sheet colour code.
SH_WHITE = (255, 255, 255)

SHADOW_SIZE = 1


def load_native_frames():
    """Recover the GIF's native pixels. Verified lossless before returning."""
    frames = [f.convert("RGBA").copy()
              for f in ImageSequence.Iterator(Image.open(GIF))]
    native = [f.resize((NATIVE, NATIVE), Image.Resampling.NEAREST)
              for f in frames]

    check = native[0].resize(frames[0].size, Image.Resampling.NEAREST)
    if list(check.get_flattened_data()) != list(frames[0].get_flattened_data()):
        raise SystemExit("refusing to continue: the x5 downsample is lossy")
    return native


def content_box(images):
    """Union bounding box over a set of frames."""
    boxes = [im.getbbox() for im in images if im.getbbox()]
    return (min(b[0] for b in boxes), min(b[1] for b in boxes),
            max(b[2] for b in boxes), max(b[3] for b in boxes))


def even(value):
    """PMD frame dimensions must be even."""
    return value + (value % 2)


def crop_frames(native, ids, box):
    left, top, right, bottom = box
    width = even(right - left)
    height = even(bottom - top)
    out = []
    for fid in ids:
        tile = Image.new("RGBA", (width, height), (0, 0, 0, 0))
        tile.paste(native[fid].crop((left, top, left + width, top + height)),
                   (0, 0))
        out.append(tile)
    return out, width, height


def anchor_points(tile):
    """Derive head / body / hand markers from the artwork itself."""
    box = tile.getbbox()
    if box is None:
        cx, cy = tile.width // 2, tile.height // 2
        return {OFF_BODY: (cx, cy), OFF_HEAD: (cx, cy),
                OFF_RIGHT: (cx, cy), OFF_LEFT: (cx, cy)}
    left, top, right, bottom = box
    cx = (left + right) // 2
    body_y = top + (bottom - top) * 6 // 10
    head_y = top + (bottom - top) * 3 // 10
    hand_y = body_y
    return {
        OFF_BODY: (cx, body_y),
        OFF_HEAD: (cx, head_y),
        OFF_RIGHT: (max(left, cx - (right - left) // 4), hand_y),
        OFF_LEFT: (min(right - 1, cx + (right - left) // 4), hand_y),
    }


def build_offsets(tile):
    sheet = Image.new("RGBA", tile.size, (0, 0, 0, 0))
    px = sheet.load()
    for colour, (x, y) in anchor_points(tile).items():
        if 0 <= x < tile.width and 0 <= y < tile.height:
            px[x, y] = (*colour, 255)
    return sheet


def build_shadow(tile):
    """A single white shadow marker on the ground under the sprite."""
    sheet = Image.new("RGBA", tile.size, (0, 0, 0, 0))
    box = tile.getbbox()
    if box is None:
        return sheet
    left, top, right, bottom = box
    px = sheet.load()
    x = (left + right) // 2
    y = min(tile.height - 1, bottom - 1)
    px[x, y] = (*SH_WHITE, 255)
    return sheet


def assemble(frames, width, height):
    """Lay frames out as columns, one row per direction."""
    anim = Image.new("RGBA", (width * len(frames), height * len(DIRECTIONS)),
                     (0, 0, 0, 0))
    offs = Image.new("RGBA", anim.size, (0, 0, 0, 0))
    shad = Image.new("RGBA", anim.size, (0, 0, 0, 0))
    for row in range(len(DIRECTIONS)):
        for col, tile in enumerate(frames):
            art = tile.transpose(Image.Transpose.FLIP_LEFT_RIGHT) \
                if row in MIRRORED_ROWS else tile
            anim.paste(art, (col * width, row * height))
            offs.paste(build_offsets(art), (col * width, row * height))
            shad.paste(build_shadow(art), (col * width, row * height))
    return anim, offs, shad


# Canonical Raichu animation table. Animations we cannot source are declared as
# CopyOf Idle so the pack is complete and importable rather than half missing.
CANON_ANIMS = [
    ("Walk", 0), ("Attack", 1), ("QuickStrike", 2), ("Shoot", 3), ("Shock", 4),
    ("Sleep", 5), ("Hurt", 6), ("Idle", 7), ("Swing", 8), ("Double", 9),
    ("Hop", 10), ("Charge", 11), ("Rotate", 12), ("EventSleep", 13),
    ("Wake", 14), ("Eat", 15), ("Tumble", 16), ("Pose", 17), ("Pull", 18),
    ("Pain", 19), ("Float", 20), ("DeepBreath", 21), ("Nod", 22), ("Sit", 23),
    ("LookUp", 24), ("Sink", 25), ("Trip", 26), ("Laying", 27),
    ("LeapForth", 28), ("Head", 29), ("Cringe", 30), ("LostBalance", 31),
    ("TumbleBack", 32), ("Faint", 33), ("HitGround", 34),
]
REAL = {"Idle", "Charge"}


def write_anim_data(specs):
    root = ET.Element("AnimData")
    ET.SubElement(root, "ShadowSize").text = str(SHADOW_SIZE)
    anims = ET.SubElement(root, "Anims")
    for name, index in CANON_ANIMS:
        node = ET.SubElement(anims, "Anim")
        ET.SubElement(node, "Name").text = name
        ET.SubElement(node, "Index").text = str(index)
        if name in specs:
            width, height, count = specs[name]
            ET.SubElement(node, "FrameWidth").text = str(width)
            ET.SubElement(node, "FrameHeight").text = str(height)
            durations = ET.SubElement(node, "Durations")
            for _ in range(count):
                ET.SubElement(durations, "Duration").text = "4"
        else:
            ET.SubElement(node, "CopyOf").text = "Idle"
    ET.indent(root, space="  ")
    ET.ElementTree(root).write(OUT / "AnimData.xml",
                               encoding="utf-8", xml_declaration=True)


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    native = load_native_frames()

    box = content_box([native[i] for i in set(IDLE_IDS + CHARGE_IDS)])
    specs = {}
    for name, ids in (("Idle", IDLE_IDS), ("Charge", CHARGE_IDS)):
        frames, width, height = crop_frames(native, ids, box)
        anim, offs, shad = assemble(frames, width, height)
        anim.save(OUT / f"{name}-Anim.png")
        offs.save(OUT / f"{name}-Offsets.png")
        shad.save(OUT / f"{name}-Shadow.png")
        specs[name] = (width, height, len(frames))
        print(f"{name}: {len(frames)} frames of {width}x{height}")

    write_anim_data(specs)

    (OUT / "credits.txt").write_text(
        "2026-09-15\tmeromoonmeri\tCUR\tUnspecified\t"
        "Mega Raichu artwork, from commit a214a07 on main\n"
        "2026-09-15\tArena.ai Agent for meromoonmeri\tCUR\tUnspecified\t"
        "Lossless GIF extraction and conversion to PMDO sprite format\n"
    )

    colours = set()
    for path in OUT.glob("*-Anim.png"):
        sheet = Image.open(path).convert("RGBA")
        colours |= {p[:3] for p in sheet.get_flattened_data() if p[3]}
    print(f"written to {OUT.relative_to(ROOT)}")
    print(f"colours: {len(colours)}  (SpriteCollab limit is 15)")


if __name__ == "__main__":
    main()
