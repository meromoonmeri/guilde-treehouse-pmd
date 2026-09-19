#!/usr/bin/env python3
"""Tests for sinister_woods_gen_v1 (generated render lot, not native tiles)."""
import os, json
import numpy as np
from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
EXP = os.path.join(ROOT, "renders", "sinister_woods_gen_v1")
W, H = 1408, 768
PLANES = ["01_sol", "02_chemin", "03_rochers", "04_buissons",
          "05_vegetation", "06_ombres", "07_grotte"]
ok = 0

def check(name, cond, extra=""):
    global ok
    assert cond, "FAIL %s %s" % (name, extra)
    ok += 1
    print("PASS %s %s" % (name, extra))

# 1. bruts exist, 1408x768, div8
for f in ["bruts/foret_entree_magenta.png", "bruts/sol_nu_magenta.png"]:
    im = Image.open(os.path.join(EXP, f))
    check("brut " + f, im.size == (W, H) and W % 8 == 0 and H % 8 == 0)

# 2. planes exist, RGBA, full canvas
planes = {}
for p in PLANES:
    im = Image.open(os.path.join(EXP, "SinisterGen_%s.png" % p))
    check("plane " + p, im.size == (W, H) and im.mode == "RGBA")
    planes[p] = np.asarray(im)

# 3. alpha strictly 0/255
for p in PLANES:
    a = planes[p][:, :, 3]
    check("alpha01 " + p, set(np.unique(a)) <= {0, 255})

# 4. partition: every terrain pixel in exactly one plane
cover = np.zeros((H, W), int)
for p in PLANES:
    cover += (planes[p][:, :, 3] > 0).astype(int)
check("cover<=1", cover.max() == 1, "max=%d" % cover.max())
n_terrain = (cover == 1).sum()
check("terrain>80%", n_terrain > 0.80 * W * H, "%d" % n_terrain)

# 5. recomposition == composite
comp = np.asarray(Image.open(os.path.join(EXP, "SinisterGen_composite.png")).convert("RGB"))
rec = np.zeros((H, W, 3), np.uint8)
for p in PLANES:
    m = planes[p][:, :, 3] > 0
    rec[m] = planes[p][m][:, :3]
check("recompose", np.array_equal(rec, comp))

# 6. no magenta / fringe in planes
for p in PLANES:
    a = planes[p].astype(int)
    m = a[:, :, 3] > 0
    R, G, B = a[:, :, 0][m], a[:, :, 1][m], a[:, :, 2][m]
    fringe = ((R > 100) & (B > 100) & (G < 110) & ((R - G) > 40) & ((B - G) > 40)).sum()
    check("nomagenta " + p, fringe == 0, "%d" % fringe)

# 7. no blue parasite left
for p in PLANES:
    a = planes[p].astype(int)
    m = a[:, :, 3] > 0
    R, G, B = a[:, :, 0][m], a[:, :, 1][m], a[:, :, 2][m]
    blue = ((B > 100) & (B - R > 40) & (B - G > 15)).sum()
    check("noblue " + p, blue == 0, "%d" % blue)

# 8. path touches south edge (arrival) and reaches grotte bbox
m = (planes["02_chemin"][:, :, 3] > 0)
check("arrival", m[-1, :].sum() > 20, "%d" % m[-1, :].sum())
g = (planes["07_grotte"][:, :, 3] > 0)
gy, gx = np.where(g)
check("grotte-north", gy.min() < 200 and 700 < gx.mean() < 900,
      "bbox x[%d,%d] y[%d,%d]" % (gx.min(), gx.max(), gy.min(), gy.max()))
check("path-top", m[:300, :].sum() > 500, "%d" % m[:300, :].sum())

# 9. every plane non-trivial (>500px) except documented small ones
for p in PLANES:
    n = (planes[p][:, :, 3] > 0).sum()
    check("nonempty " + p, n > 500, "%d" % n)

# 10. manifest + bonus ground
man = json.load(open(os.path.join(EXP, "manifest_partition_7calques.json")))
check("manifest", man["lot"] == "sinister_woods_partition_v1" and len(man["planes"]) == 7)
bg = Image.open(os.path.join(EXP, "SinisterGen_00_sol_nu.png"))
check("bonus", bg.size == (W, H))

print("ALL %d TESTS PASS" % ok)
