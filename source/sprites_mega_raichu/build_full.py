"""Build the COMPLETE Mega Raichu pack: 35 animations x 8 directions.

THE PROBLEM
-----------
The Mega Raichu artwork (commit a214a07) exists in exactly ONE camera angle,
facing the viewer, in two short loops. PMD needs 35 animations across 8
directions. Mirroring a front view, as the first pass did, leaves the character
staring at the camera from every angle: structurally valid, visually wrong.

THE APPROACH
------------
Canonical Raichu (#0026) already has all 35 animations in all 8 directions,
with real poses, real timings, real offsets and real shadows. Mega Raichu is
the same animal: same skeleton, same silhouette, same motion. What differs is
its COLOURING and its enlarged ear-bolts.

So the canonical animation set is the geometry source, and the Mega artwork is
the appearance source:

  1. every canonical frame keeps its pose, its timing and its marker sheets;
  2. its palette is replaced by the Mega palette through a BY-ROLE mapping
     derived from the two front-facing sprites, not by luminance guessing:
     outline, three fur tones, belly, bolt tones and eyes each map explicitly;
  3. the result is a Mega-coloured Raichu that animates correctly in all eight
     directions, for all thirty-five animations.

Offsets and shadow sheets are copied untouched: they are marker data and must
never be recoloured.

WHAT THIS IS NOT
----------------
This is a recolour of canonical geometry, not a redraw. The oversized
ear-bolts of the Mega design are NOT grafted onto every frame: doing that
convincingly across 35 animations and 8 angles is hand-animation work, not
something a script can fake. See README for the honest limits.
"""
from pathlib import Path
import shutil
import xml.etree.ElementTree as ET

from PIL import Image, ImageSequence

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
CANON = HERE / "canonical"
GIF = HERE / "source.gif"
OUT = ROOT / "sprite" / "0026_mega_x"

# ---------------------------------------------------------------- palettes
# Canonical Raichu, by role. Read off sprite/0026/Idle-Anim.png.
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
# Mouth interior, used only by animations that open the jaw (Eat, Shoot,
# DeepBreath, Pain, ...). Plus one extra bolt shadow used by Charge/Shock.
C_MOUTH_DARK = (231, 63, 103)
C_MOUTH = (255, 143, 175)
C_MOUTH_LIT = (255, 199, 215)
C_BOLT_SHADE = (167, 111, 0)

# Mega Raichu, by role. Read off the source GIF's front-facing frame.
M_OUTLINE = (7, 7, 7)
M_FUR_DARK = (90, 40, 5)
M_FUR_MID = (124, 51, 51)
M_FUR_BASE = (193, 97, 53)
M_FUR_LIT = (234, 158, 32)
M_BOLT_DARK = (117, 77, 10)
M_BOLT_LIT = (248, 190, 38)
M_BOLT_PALE = (247, 230, 82)
M_BELLY = (241, 247, 247)
M_BELLY_SHADE = (214, 198, 173)
M_TRIM = (66, 66, 74)
# The Mega source is a closed-mouth idle, so it provides no mouth colours.
# The canonical mouth pinks are KEPT AS-IS: flesh reads the same on both
# designs, and inventing a Mega-specific mouth would be fabrication.
M_MOUTH_DARK = C_MOUTH_DARK
M_MOUTH = C_MOUTH
M_MOUTH_LIT = C_MOUTH_LIT
# The extra canonical bolt shadow folds into the Mega bolt shadow.
M_BOLT_SHADE = M_BOLT_DARK

# The mapping is explicit and by ROLE. A luminance-rank mapping was rejected:
# the two palettes share zero colours and their luminance orders disagree
# (Mega's fur mid-tone is darker than canonical's bolt shadow), so ranking
# would have sent fur colours into the lightning and vice versa.
RECOLOUR = {
    C_OUTLINE: M_OUTLINE,
    C_FUR_DARK: M_FUR_DARK,
    C_FUR_MID: M_FUR_MID,
    C_FUR_BASE: M_FUR_BASE,
    C_FUR_LIT: M_FUR_LIT,
    C_BOLT_DARK: M_BOLT_DARK,
    C_BOLT_LIT: M_BOLT_LIT,
    C_BOLT_PALE: M_BOLT_PALE,
    C_BELLY: M_BELLY,
    C_BELLY_SHADE: M_BELLY_SHADE,
    C_TRIM: M_TRIM,
    C_MOUTH_DARK: M_MOUTH_DARK,
    C_MOUTH: M_MOUTH,
    C_MOUTH_LIT: M_MOUTH_LIT,
    C_BOLT_SHADE: M_BOLT_SHADE,
}


def recolour(path):
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
            if key in RECOLOUR:
                px[x, y] = (*RECOLOUR[key], 255)
            else:
                unknown.add(key)
    return sheet, unknown


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    for stale in OUT.glob("*"):
        if stale.is_file():
            stale.unlink()

    tree = ET.parse(CANON / "AnimData.xml")
    root = tree.getroot()

    all_unknown = set()
    drawn = 0
    for anim in root.find("Anims"):
        name = anim.findtext("Name")
        if anim.findtext("CopyOf"):
            continue
        drawn += 1
        sheet, unknown = recolour(CANON / f"{name}-Anim.png")
        sheet.save(OUT / f"{name}-Anim.png")
        all_unknown |= unknown
        # Marker sheets are data, never recoloured.
        for suffix in ("Offsets", "Shadow"):
            shutil.copyfile(CANON / f"{name}-{suffix}.png",
                            OUT / f"{name}-{suffix}.png")

    shutil.copyfile(CANON / "AnimData.xml", OUT / "AnimData.xml")

    (OUT / "credits.txt").write_text(
        "2026-09-15\tmeromoonmeri\tCUR\tUnspecified\t"
        "Mega Raichu design and artwork, commit a214a07\n"
        "2026-09-15\tSpriteCollab contributors\tCUR\tCC_BY-NC_4\t"
        "Raichu #0026 animation set used as the geometry base\n"
        "2026-09-15\tArena.ai Agent for meromoonmeri\tCUR\tUnspecified\t"
        "Mega recolour applied across all animations and directions\n"
    )

    colours = set()
    for path in OUT.glob("*-Anim.png"):
        im = Image.open(path).convert("RGBA")
        colours |= {p[:3] for p in im.get_flattened_data() if p[3]}

    print(f"{drawn} animations recoloured, all 8 directions each")
    print(f"colours: {len(colours)} (SpriteCollab limit 15)")
    if all_unknown:
        print(f"WARNING: {len(all_unknown)} unmapped canonical colours:")
        for c in sorted(all_unknown):
            print("   ", c)


if __name__ == "__main__":
    main()
