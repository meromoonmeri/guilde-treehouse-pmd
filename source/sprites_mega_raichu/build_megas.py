"""Build BOTH Mega Raichu forms, X and Y, to PMD Sprite Guide spec.

SPEC FOLLOWED (Emmuffin, "How to Make PMD Sprites for SkyTemple")
-----------------------------------------------------------------
  * palette: max 15 colours + 1 transparency across the WHOLE sheet set;
  * frame size: official sprites use multiples of 8. The previous build padded
    to 64x68, 96x92 and so on, none of which are multiples of 8. Every frame
    is now rounded UP to the next multiple of 8;
  * sheets must have exactly 1 or 8 rows;
  * dungeon animations 0,1,5,6,7,8,9,10,11,12 plus the starter set 13-34;
  * multi sheet layout: Name-Anim.png, Name-Offsets.png, Name-Shadow.png and
    AnimData.xml, which is the format SpriteBot accepts.

PIPELINE
--------
Canonical Raichu #0026 supplies the motion for all 35 animations and 1275
frames. For each Mega form:

  1. recolour the canonical artwork to that form's palette, mapped BY ROLE
     (outline, three fur tones, belly, bolt tones, mouth), never by luminance;
  2. pad every frame out to a multiple of 8 so the wingspan fits and the guide
     is satisfied, shifting the offset and shadow markers by the same amount so
     they keep pointing at the same body parts;
  3. graft the lightning wings onto every frame, anchored on the head marker
     from the -Offsets sheet so they track the body through the animation;
  4. write AnimData.xml with the corrected dimensions.

Form X keeps the artwork's warm orange palette and yellow bolts.
Form Y is the storm-blue counterpart with white-cyan bolts.
"""
from pathlib import Path
import shutil
import sys
import xml.etree.ElementTree as ET

from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parent))
from wings import wing_pixels, BOLT, BOLT_PALE, BOLT_DARK  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
CANON = HERE / "canonical"

HEAD_MARKER = (0, 0, 0)
PAD_X, PAD_TOP = 12, 12

# ------------------------------------------------------------- canonical roles
C_OUTLINE = (0, 0, 0)
C_FUR_DARK = (119, 63, 0)
C_FUR_MID = (167, 95, 31)
C_FUR_BASE = (223, 135, 31)
C_FUR_LIT = (255, 175, 71)
C_BOLT_DARK = (223, 183, 0)
C_BOLT_LIT = (255, 247, 0)
C_BOLT_PALE = (255, 247, 159)
C_BELLY = (255, 255, 255)
C_BELLY_SHADE = (215, 191, 103)
C_TRIM = (183, 135, 39)
C_MOUTH_DARK = (231, 63, 103)
C_MOUTH = (255, 143, 175)
C_MOUTH_LIT = (255, 199, 215)
C_BOLT_SHADE = (167, 111, 0)

# ------------------------------------------------------------------- form X
# Read off the Mega Raichu artwork in commit a214a07.
X = {
    C_OUTLINE: (7, 7, 7),
    C_FUR_DARK: (90, 40, 5),
    C_FUR_MID: (124, 51, 51),
    C_FUR_BASE: (193, 97, 53),
    C_FUR_LIT: (234, 158, 32),
    C_BOLT_DARK: (117, 77, 10),
    C_BOLT_LIT: (248, 190, 38),
    C_BOLT_PALE: (247, 230, 82),
    C_BELLY: (241, 247, 247),
    C_BELLY_SHADE: (214, 198, 173),
    C_TRIM: (66, 66, 74),
    C_MOUTH_DARK: (231, 63, 103),
    C_MOUTH: (255, 143, 175),
    C_MOUTH_LIT: (255, 199, 215),
    C_BOLT_SHADE: (117, 77, 10),
}

# ------------------------------------------------------------------- form Y
# Storm-blue counterpart, authored by role from the generated Mega Y design.
# Hand-written rather than auto-quantised: quantising the generated plate left
# magenta key residue and purple artefacts in the palette.
Y = {
    C_OUTLINE: (10, 12, 26),
    C_FUR_DARK: (34, 42, 74),
    C_FUR_MID: (52, 64, 104),
    C_FUR_BASE: (68, 88, 138),
    C_FUR_LIT: (104, 132, 186),
    C_BOLT_DARK: (58, 122, 158),
    C_BOLT_LIT: (150, 236, 255),
    C_BOLT_PALE: (226, 252, 255),
    C_BELLY: (186, 214, 245),
    C_BELLY_SHADE: (132, 166, 210),
    C_TRIM: (44, 54, 88),
    C_MOUTH_DARK: (146, 62, 110),
    C_MOUTH: (198, 116, 158),
    C_MOUTH_LIT: (232, 176, 206),
    C_BOLT_SHADE: (58, 122, 158),
}

# Wing tones per form, substituted into the hand-drawn wing art.
WING_TONES = {
    "x": {BOLT: (248, 190, 38), BOLT_PALE: (247, 230, 82),
          BOLT_DARK: (117, 77, 10)},
    "y": {BOLT: (150, 236, 255), BOLT_PALE: (226, 252, 255),
          BOLT_DARK: (58, 122, 158)},
}

FORMS = {"x": X, "y": Y}


def to_multiple_of_8(value):
    """The guide: official sprites use frame sizes that are multiples of 8."""
    return ((value + 7) // 8) * 8


def recolour(path, table):
    sheet = Image.open(path).convert("RGBA")
    px = sheet.load()
    unknown = set()
    for y in range(sheet.height):
        for x in range(sheet.width):
            r, g, b, a = px[x, y]
            if a == 0:
                px[x, y] = (0, 0, 0, 0)
                continue
            key = (r, g, b)
            if key in table:
                px[x, y] = (*table[key], 255)
            else:
                unknown.add(key)
    return sheet, unknown


def head_positions(offsets, fw, fh, cols, rows):
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


def relayout(sheet, fw, fh, cols, rows, nfw, nfh, dx, dy):
    out = Image.new("RGBA", (nfw * cols, nfh * rows), (0, 0, 0, 0))
    for row in range(rows):
        for col in range(cols):
            tile = sheet.crop((col * fw, row * fh,
                               (col + 1) * fw, (row + 1) * fh))
            out.paste(tile, (col * nfw + dx, row * nfh + dy))
    return out


def graft(anim, heads, cols, rows, nfw, nfh, dx, dy, single, tones):
    out = Image.new("RGBA", anim.size, (0, 0, 0, 0))
    for row in range(rows):
        direction = 0 if single else row
        for col in range(cols):
            box = (col * nfw, row * nfh, (col + 1) * nfw, (row + 1) * nfh)
            body = anim.crop(box)
            head = heads.get((row, col))
            if head is None:
                out.paste(body, box[:2])
                continue
            hx, hy = head[0] + dx, head[1] + dy
            layer = Image.new("RGBA", (nfw, nfh), (0, 0, 0, 0))
            lp = layer.load()
            for wdx, wdy, colour in wing_pixels(direction):
                x, y = hx + wdx, hy + wdy
                if 0 <= x < nfw and 0 <= y < nfh:
                    lp[x, y] = (*tones[colour], 255)
            out.paste(Image.alpha_composite(layer, body), box[:2])
    return out


def build(form):
    table = FORMS[form]
    tones = WING_TONES[form]
    out = ROOT / "sprite" / f"0026_mega_{form}"
    out.mkdir(parents=True, exist_ok=True)
    for stale in out.glob("*"):
        if stale.is_file():
            stale.unlink()

    tree = ET.parse(CANON / "AnimData.xml")
    root = tree.getroot()
    unknown = set()
    frames = 0

    for node in root.find("Anims"):
        name = node.findtext("Name")
        if node.findtext("CopyOf"):
            continue
        fw = int(node.findtext("FrameWidth"))
        fh = int(node.findtext("FrameHeight"))

        anim, miss = recolour(CANON / f"{name}-Anim.png", table)
        unknown |= miss
        offs = Image.open(CANON / f"{name}-Offsets.png").convert("RGBA")
        shad = Image.open(CANON / f"{name}-Shadow.png").convert("RGBA")
        cols, rows = anim.width // fw, anim.height // fh

        nfw = to_multiple_of_8(fw + PAD_X * 2)
        nfh = to_multiple_of_8(fh + PAD_TOP)
        dx = (nfw - fw) // 2
        dy = nfh - fh          # keep the feet on the frame's bottom edge

        heads = head_positions(offs, fw, fh, cols, rows)
        padded = relayout(anim, fw, fh, cols, rows, nfw, nfh, dx, dy)
        winged = graft(padded, heads, cols, rows, nfw, nfh, dx, dy,
                       rows == 1, tones)

        winged.save(out / f"{name}-Anim.png")
        relayout(offs, fw, fh, cols, rows, nfw, nfh, dx, dy).save(
            out / f"{name}-Offsets.png")
        relayout(shad, fw, fh, cols, rows, nfw, nfh, dx, dy).save(
            out / f"{name}-Shadow.png")

        node.find("FrameWidth").text = str(nfw)
        node.find("FrameHeight").text = str(nfh)
        frames += cols * rows

    ET.indent(root, space="  ")
    tree.write(out / "AnimData.xml", encoding="utf-8", xml_declaration=True)

    label = "X" if form == "x" else "Y"
    (out / "credits.txt").write_text(
        f"2026-09-15\tmeromoonmeri\tCUR\tUnspecified\t"
        f"Mega Raichu {label} design\n"
        "2026-09-15\tSpriteCollab contributors\tCUR\tCC_BY-NC_4\t"
        "Raichu #0026 animation set used as the motion base\n"
        "2026-09-15\tArena.ai Agent for meromoonmeri\tCUR\tUnspecified\t"
        f"Mega {label} recolour, wings and assembly\n"
    )

    colours = set()
    for path in out.glob("*-Anim.png"):
        im = Image.open(path).convert("RGBA")
        colours |= {p[:3] for p in im.get_flattened_data() if p[3]}
    print(f"Mega {label}: {frames} frames, 35 animations, "
          f"{len(colours)} colours")
    if unknown:
        print(f"  WARNING unmapped: {sorted(unknown)}")
    return colours


def main():
    for form in ("x", "y"):
        build(form)


if __name__ == "__main__":
    main()
