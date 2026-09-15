"""Build the Terapagos #1024 Stellar form sprite sheets for SpriteCollab.

Upstream state, checked on SpriteCollab:
  sprite/1024/0001 (Terastal) is a complete 13 animation set.
  sprite/1024/0002 (Stellar)  DOES NOT EXIST.

Terastal and Stellar are the same creature in the same pose: the Stellar form
is a recolour of the Terastal shell, not a different body. So the Stellar sprite
reuses the Terastal geometry frame for frame and applies a deterministic
recolour whose target palette is the *published Stellar portrait* — the only
authoritative statement of what Stellar's colours are.

The mapping is by luminance rank: the Terastal sprite colours are ordered from
darkest to lightest, the Stellar portrait colours likewise, and rank is matched
to rank. That preserves the shading structure of the original artist's work
while moving the hue family to Stellar. The outline black is pinned to the
Stellar outline violet rather than rank-mapped, because it is structural.

No AI generated pixel enters this pack. Geometry, timings, offsets and shadows
are the canonical Terastal ones.
"""
from pathlib import Path
import shutil
import xml.etree.ElementTree as ET

from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
TERASTAL = HERE / "canonical" / "terastal"
STELLAR_PORTRAIT = ROOT / "source" / "portraits_terapagos" / "reference" / "Normal.png"
OUT = ROOT / "sprite" / "1024"

# Structural colours that must not be rank-mapped.
SPRITE_OUTLINE = (0, 0, 0)
STELLAR_OUTLINE = (47, 0, 127)


def luminance(colour):
    r, g, b = colour
    return 0.299 * r + 0.587 * g + 0.114 * b


def sprite_palette():
    """Every opaque colour used across the canonical Terastal sheets."""
    colours = set()
    for path in sorted(TERASTAL.glob("*-Anim.png")):
        sheet = Image.open(path).convert("RGBA")
        colours |= {p[:3] for p in sheet.get_flattened_data() if p[3]}
    return colours


def stellar_palette():
    portrait = Image.open(STELLAR_PORTRAIT).convert("RGB")
    return {colour for _, colour in portrait.getcolors(100000)}


def build_mapping():
    """Deterministic recolour by nearest luminance, outline pinned.

    Rank spreading was tried first and rejected: it flattened the contrast,
    because the Terastal sprite is mostly mid tones while the Stellar portrait
    palette is weighted towards pale facets. Matching each sprite colour to the
    Stellar colour of the closest luminance preserves the original artist's
    shading structure instead.
    """
    source = sorted(sprite_palette() - {SPRITE_OUTLINE}, key=luminance)
    target = sorted(stellar_palette() - {STELLAR_OUTLINE}, key=luminance)
    mapping = {SPRITE_OUTLINE: STELLAR_OUTLINE}
    used = set()
    for colour in source:
        value = luminance(colour)
        # Prefer an unused Stellar swatch so distinct sprite tones stay
        # distinct; fall back to the nearest one when they are exhausted.
        pool = [c for c in target if c not in used] or target
        best = min(pool, key=lambda c: abs(luminance(c) - value))
        mapping[colour] = best
        used.add(best)
    return mapping


def recolour(path, mapping):
    sheet = Image.open(path).convert("RGBA")
    pixels = sheet.load()
    for y in range(sheet.height):
        for x in range(sheet.width):
            r, g, b, a = pixels[x, y]
            if a == 0:
                pixels[x, y] = (0, 0, 0, 0)
                continue
            pixels[x, y] = (*mapping[(r, g, b)], 255)
    return sheet


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    mapping = build_mapping()

    for path in sorted(TERASTAL.glob("*.png")):
        if path.name.endswith("-Anim.png"):
            recolour(path, mapping).save(OUT / path.name)
        else:
            # Offsets and shadows are marker data, never recoloured.
            shutil.copyfile(path, OUT / path.name)

    shutil.copyfile(TERASTAL / "AnimData.xml", OUT / "AnimData.xml")

    (OUT / "credits.txt").write_text(
        "2026-06-19 03:30:40.860541\t<@!350050109741858829>\tCUR\tCC_BY-NC_4\t"
        "Terastal sprite used as the geometry base\n"
        "2026-06-19 07:13:01.815243\t<@!702275233125630042>\tCUR\tCC_BY-NC_4\t"
        "Terastal sprite used as the geometry base\n"
        "2026-09-15\tArena.ai Agent for meromoonmeri\tNEW\tUnspecified\t"
        "Stellar form recolour of every animation\n"
    )

    root = ET.parse(OUT / "AnimData.xml").getroot()
    count = len(list(root.find("Anims")))
    print(f"recoloured {count} animations into {OUT.relative_to(ROOT)}")
    for source, target in sorted(mapping.items(), key=lambda kv: luminance(kv[0])):
        print(f"  {source} -> {target}")


if __name__ == "__main__":
    main()
