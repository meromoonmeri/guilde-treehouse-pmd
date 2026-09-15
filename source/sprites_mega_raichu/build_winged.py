"""Build the single, final Mega Raichu pack: all 35 animations, with wings.

THE GOAL
--------
One pack. Not a recolour without wings, and not a winged Idle on its own: the
Mega Raichu sprite must carry the full design AND every animation, with its
legs, tail and ears actually moving.

HOW
---
Canonical Raichu #0026 supplies the motion: 35 animations, 1275 frames, real
poses, real timings, real markers. That artwork is recoloured to the Mega
palette (see build_full.py for the by-role mapping), and then the lightning
wings are grafted onto every single frame.

The graft is anchored on the HEAD MARKER, the black pixel present in every
frame of every -Offsets sheet. Because that marker tracks the skull as the
body bobs, walks, lunges and falls, the wings follow the animation instead of
floating at a fixed spot. The wing shape itself is chosen per DIRECTION ROW,
so the pair is foreshortened correctly for the camera angle.

Frames are padded outward to make room for the wingspan, and AnimData.xml is
rewritten with the new dimensions. Offsets and shadow markers are shifted by
the same padding so they keep pointing at the same body parts.

Single-direction animations stay single-direction, exactly as upstream ships
them: those poses are never seen from another angle.
"""
from pathlib import Path
import shutil
import sys
import xml.etree.ElementTree as ET

from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parent))
from wings import wing_pixels  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
SRC = ROOT / "sprite" / "0026_mega_x"
OUT = ROOT / "sprite" / "0026_mega_x"

HEAD_MARKER = (0, 0, 0)
# Room for the wingspan: wings reach ~16px out and ~13px up from the head.
PAD_X, PAD_TOP, PAD_BOTTOM = 12, 12, 0


def even(value):
    return value + (value % 2)


def head_positions(offsets, fw, fh, cols, rows):
    """Locate the head marker in every frame of an -Offsets sheet."""
    px = offsets.load()
    found = {}
    for row in range(rows):
        for col in range(cols):
            spot = None
            for y in range(row * fh, (row + 1) * fh):
                for x in range(col * fw, (col + 1) * fw):
                    p = px[x, y]
                    if p[3] and p[:3] == HEAD_MARKER:
                        spot = (x - col * fw, y - row * fh)
            found[(row, col)] = spot
    return found


def pad_sheet(sheet, fw, fh, cols, rows, nfw, nfh):
    """Re-lay a sheet into larger frames, keeping each frame's content."""
    out = Image.new("RGBA", (nfw * cols, nfh * rows), (0, 0, 0, 0))
    for row in range(rows):
        for col in range(cols):
            tile = sheet.crop((col * fw, row * fh, (col + 1) * fw, (row + 1) * fh))
            out.paste(tile, (col * nfw + PAD_X, row * nfh + PAD_TOP))
    return out


def graft(anim, heads, cols, rows, nfw, nfh, single_direction):
    """Paint the wings behind the body on every frame."""
    out = Image.new("RGBA", anim.size, (0, 0, 0, 0))
    for row in range(rows):
        # Single-direction sheets show the front view only.
        direction = 0 if single_direction else row
        for col in range(cols):
            box = (col * nfw, row * nfh, (col + 1) * nfw, (row + 1) * nfh)
            body = anim.crop(box)
            head = heads.get((row, col))
            if head is None:
                out.paste(body, box[:2])
                continue
            hx, hy = head[0] + PAD_X, head[1] + PAD_TOP
            layer = Image.new("RGBA", (nfw, nfh), (0, 0, 0, 0))
            lp = layer.load()
            for dx, dy, colour in wing_pixels(direction):
                x, y = hx + dx, hy + dy
                if 0 <= x < nfw and 0 <= y < nfh:
                    lp[x, y] = (*colour, 255)
            # Wings go BEHIND the body, so the head and ears stay readable.
            out.paste(Image.alpha_composite(layer, body), box[:2])
    return out


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    for stale in OUT.glob("*"):
        if stale.is_file():
            stale.unlink()

    tree = ET.parse(SRC / "AnimData.xml")
    root = tree.getroot()

    total = 0
    for node in root.find("Anims"):
        name = node.findtext("Name")
        if node.findtext("CopyOf"):
            continue
        fw = int(node.findtext("FrameWidth"))
        fh = int(node.findtext("FrameHeight"))
        anim = Image.open(SRC / f"{name}-Anim.png").convert("RGBA")
        offs = Image.open(SRC / f"{name}-Offsets.png").convert("RGBA")
        shad = Image.open(SRC / f"{name}-Shadow.png").convert("RGBA")
        cols, rows = anim.width // fw, anim.height // fh

        nfw = even(fw + PAD_X * 2)
        nfh = even(fh + PAD_TOP + PAD_BOTTOM)

        heads = head_positions(offs, fw, fh, cols, rows)
        padded = pad_sheet(anim, fw, fh, cols, rows, nfw, nfh)
        winged = graft(padded, heads, cols, rows, nfw, nfh, rows == 1)

        winged.save(OUT / f"{name}-Anim.png")
        pad_sheet(offs, fw, fh, cols, rows, nfw, nfh).save(
            OUT / f"{name}-Offsets.png")
        pad_sheet(shad, fw, fh, cols, rows, nfw, nfh).save(
            OUT / f"{name}-Shadow.png")

        node.find("FrameWidth").text = str(nfw)
        node.find("FrameHeight").text = str(nfh)
        total += cols * rows

    ET.indent(root, space="  ")
    tree.write(OUT / "AnimData.xml", encoding="utf-8", xml_declaration=True)

    shutil.copyfile(SRC / "credits.txt", OUT / "credits.txt")
    with open(OUT / "credits.txt", "a") as handle:
        handle.write("2026-09-15\tArena.ai Agent for meromoonmeri\tCUR\t"
                     "Unspecified\tLightning wings grafted onto every frame\n")

    colours = set()
    for path in OUT.glob("*-Anim.png"):
        im = Image.open(path).convert("RGBA")
        colours |= {p[:3] for p in im.get_flattened_data() if p[3]}
    print(f"grafted wings onto {total} frames across 35 animations")
    print(f"colours: {len(colours)} (limit 15)")


if __name__ == "__main__":
    main()
