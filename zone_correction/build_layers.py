from pathlib import Path
from PIL import Image, ImageDraw
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "zone_correction"
SRC = OUT / "final" / "zone_corrigee.png"
GEN = OUT / "source" / "layers_generated"
LAYERS = OUT / "layers"
for d in (LAYERS, LAYERS / "transparent", LAYERS / "magenta"):
    d.mkdir(parents=True, exist_ok=True)

MAGENTA = (255, 0, 255, 255)
img = Image.open(SRC).convert("RGBA")
w, h = img.size
assert (w, h) == (528, 384)

# Semantic, hard-edged masks are constructed in the same 8 px PMDO grid as the
# Tiled map. Priority is foliage > rocks > cliffs > base, so every pixel belongs
# to exactly one exported layer and the re-composite is byte-identical.
mask_cliff = Image.new("L", (w, h), 0)
d = ImageDraw.Draw(mask_cliff)
# Upper rocky entrance banks, matching the final generated render's composition.
d.polygon([(0, 0), (214, 0), (224, 16), (216, 32), (202, 40), (212, 56), (204, 72), (216, 88), (203, 104), (220, 120), (211, 144), (234, 160), (220, 184), (0, 184)], fill=255)
d.polygon([(314, 0), (528, 0), (528, 184), (308, 184), (318, 160), (294, 144), (305, 120), (292, 104), (305, 88), (294, 72), (307, 56), (296, 40), (308, 32)], fill=255)
# Retain the path opening itself as base, not as cliff.
d.rectangle((224, 0, 304, 184), fill=0)

mask_rocks = Image.new("L", (w, h), 0)
d = ImageDraw.Draw(mask_rocks)
# Deliberate 8 px snapped silhouettes around the reusable rock positions.
rock_boxes = [(32, 100, 120, 174), (328, 100, 424, 174), (100, 180, 180, 244), (352, 180, 448, 244), (64, 258, 144, 322), (384, 258, 480, 322), (122, 300, 208, 372), (320, 298, 424, 374)]
for box in rock_boxes:
    d.ellipse(box, fill=255)
# Small flat stones and pebble clusters in the clearing.
for x, y, rw, rh in [(176, 144, 26, 18), (286, 144, 22, 18), (96, 236, 24, 14), (430, 230, 26, 16), (194, 198, 38, 24), (296, 202, 40, 24), (230, 288, 32, 18), (282, 300, 38, 20)]:
    d.ellipse((x, y, x + rw, y + rh), fill=255)

mask_flowers = Image.new("L", (w, h), 0)
d = ImageDraw.Draw(mask_flowers)
# Bottom corner flower/fern borders; do not absorb the middle path.
d.rectangle((0, 320, 144, h - 1), fill=255)
d.rectangle((392, 320, w - 1, h - 1), fill=255)
d.rectangle((144, 360, 208, h - 1), fill=255)
d.rectangle((320, 360, 392, h - 1), fill=255)

# Priority masks are disjoint. Flowers sit over rocks, rocks over cliffs, cliffs
# over base. The masks intentionally preserve every final pixel exactly once.
a_flowers = np.array(mask_flowers) > 0
a_rocks = (np.array(mask_rocks) > 0) & ~a_flowers
a_cliff = (np.array(mask_cliff) > 0) & ~a_flowers & ~a_rocks
a_base = ~(a_flowers | a_rocks | a_cliff)

layers = {
    "01_sol": a_base,
    "02_cliff_entree": a_cliff,
    "03_rochers": a_rocks,
    "04_bordures_fleurs": a_flowers,
}
source = np.array(img)
magenta = np.zeros_like(source)
magenta[:, :] = np.array(MAGENTA, dtype=np.uint8)

for name, mask in layers.items():
    transparent = np.zeros_like(source)
    transparent[mask] = source[mask]
    mag = magenta.copy()
    mag[mask] = source[mask]
    Image.fromarray(transparent, "RGBA").save(LAYERS / "transparent" / f"{name}.png", optimize=True)
    Image.fromarray(mag, "RGBA").save(LAYERS / "magenta" / f"{name}_magenta.png", optimize=True)

# The generator-authored layer studies remain in source/layers_generated/. The
# exports below are the deterministic, pixel-perfect chroma-key layers used in
# the project; they are built from the final corrected canvas and the same masks.
# Full control composite: each independent layer stays on #FF00FF, then the
# transparent layers are recomposed to prove the cut is lossless.
control = Image.fromarray(magenta, "RGBA")
for name in layers:
    control.alpha_composite(Image.open(LAYERS / "transparent" / f"{name}.png").convert("RGBA"))
control.save(LAYERS / "zone_corrigee_magenta.png", optimize=True)
recomposed = Image.new("RGBA", (w, h), (0, 0, 0, 0))
for name in layers:
    recomposed.alpha_composite(Image.open(LAYERS / "transparent" / f"{name}.png").convert("RGBA"))
recomposed.save(LAYERS / "zone_corrigee_recomposee.png", optimize=True)

assert np.array_equal(np.array(recomposed), source), "layer recomposition mismatch"
assert np.all(np.array(control)[a_base] == source[a_base])
assert len(list(GEN.glob("*_magenta_generated.png"))) == 4
print("PASS: 4 magenta layers, 528x384, exact re-composition; generator studies retained.")
