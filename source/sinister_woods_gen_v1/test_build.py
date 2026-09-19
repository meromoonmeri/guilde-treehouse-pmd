#!/usr/bin/env python3
"""Tests for sinister_woods_gen_v1 (generated render lot)."""
import json, os
import numpy as np
from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
REN = os.path.join(ROOT, "renders", "sinister_woods_gen_v1")
LAY = os.path.join(REN, "calques")
ANIM = os.path.join(REN, "anim")
W, H = 512, 640
man = json.load(open(os.path.join(REN, "manifest.json")))
order = man["layers_order"]
ok = 0

def check(name, cond):
    global ok
    assert cond, "FAIL: " + name
    ok += 1
    print("PASS:", name)

# 1. dims divisible by 8, all layers same size RGBA
check("scene 512x640 div8", W % 8 == 0 and H % 8 == 0)
layers = {}
for nm in order:
    a = np.asarray(Image.open(os.path.join(LAY, nm + ".png")))
    check("layer %s RGBA 512x640" % nm, a.shape == (H, W, 4))
    layers[nm] = a

# 2. base opaque, others have transparency
check("base opaque", (layers["00_base_terrain"][:, :, 3] == 255).all())
for nm in order[1:]:
    a = layers[nm][:, :, 3]
    check("layer %s has both fg+bg" % nm, (a > 0).any() and (a == 0).any())

# 3. recomposition == composite byte-exact
comp = np.zeros((H, W, 3), np.uint8)
for nm in order:
    la = layers[nm]
    m = la[:, :, 3] > 0
    comp[m] = la[m][:, :3]
ref = np.asarray(Image.open(os.path.join(REN, "scene_composite.png")).convert("RGB"))
check("recomposition byte-exact", np.array_equal(comp, ref))

# 4. no magenta/purple residue in any layer
for nm in order:
    la = layers[nm].astype(int)
    m = la[:, :, 3] > 0
    R, G, B = la[:, :, 0], la[:, :, 1], la[:, :, 2]
    purp = m & (R > 130) & (B > 130) & (np.minimum(R, B) > G + 30)
    bluev = m & (B > 150) & (B > G + 60) & (B > R + 30)
    check("no purple in %s" % nm, not (purp | bluev).any())

# 5. anim frames exist, correct sizes
for i in range(4):
    a = np.asarray(Image.open(os.path.join(ANIM, "pulse_%d.png" % i)))
    check("pulse_%d RGBA" % i, a.shape == (H, W, 4))
for i in range(8):
    a = np.asarray(Image.open(os.path.join(ANIM, "firefly_%d.png" % i)))
    check("firefly_%d RGBA" % i, a.shape == (H, W, 4))

# 6. pulse frames differ, loop closes (3->0 alpha pattern symmetric)
p0 = np.asarray(Image.open(os.path.join(ANIM, "pulse_0.png")))[:, :, 3]
p2 = np.asarray(Image.open(os.path.join(ANIM, "pulse_2.png")))[:, :, 3]
check("pulse varies", p2.sum() > p0.sum() and p0.sum() == 0)

# 7. firefly frames differ from each other
f = [np.asarray(Image.open(os.path.join(ANIM, "firefly_%d.png" % i))) for i in range(8)]
check("fireflies all differ", all(not np.array_equal(f[i], f[(i + 1) % 8]) for i in range(8)))

# 8. grove mask non-empty and centered top-half
gm = np.asarray(Image.open(os.path.join(ANIM, "_grove_mask.png")))
check("grove mask sane", 1000 < (gm > 0).sum() < 40000)

# 9. path reaches south edge on base (tan pixels at bottom center)
base = layers["00_base_terrain"][:, :, :3].astype(int)
south = base[632:640, 216:296]
tan = (south[:, :, 0] > 110) & (south[:, :, 0] - south[:, :, 2] > 15)
check("path reaches south edge", tan.mean() > 0.5)

# 10. manifest consistency
check("manifest counts match", all(man["counts"][nm] == int((layers[nm][:, :, 3] > 0).sum()) for nm in order))
check("manifest bruts present", all(os.path.exists(os.path.join(REN, "bruts", f)) for f in man["bruts"]))

print("ALL %d TESTS PASS" % ok)
