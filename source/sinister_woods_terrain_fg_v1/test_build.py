#!/usr/bin/env python3
"""Tests for sinister_woods_gen_v1 (generated art, PMD-DA proposal — not native)."""
import os, json
import numpy as np
from PIL import Image
from scipy import ndimage

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
LAY = os.path.join(ROOT, "renders", "sinister_woods_gen_v1", "layers")
W, H, N = 656, 1376, 0

def check(name, cond, extra=""):
    global N
    N += 1
    print(("PASS %02d " % N) + name, extra)
    assert cond, "FAIL: " + name

def load(n):
    return np.asarray(Image.open(os.path.join(LAY, n)))

base = load("01_sol.png")
chemin = load("02_chemin.png")
rochers = load("03_rochers.png")
g = load("04_arbres_gauche.png")
d = load("05_arbres_droit.png")
grotte = load("06_grotte.png")
fg = load("07_avant_plan.png")

# 1. dims + grid
for n, a in [("sol", base), ("chemin", chemin), ("rochers", rochers), ("G", g),
             ("D", d), ("grotte", grotte), ("fg", fg)]:
    check("dims %s 656x1376 RGBA" % n, a.shape == (H, W, 4))
check("canvas divisible by 8", W % 8 == 0 and H % 8 == 0)

# 2. base opaque
check("base fully opaque", (base[:, :, 3] == 255).all())

# 3. others have transparency and content
for n, a in [("chemin", chemin), ("rochers", rochers), ("G", g), ("D", d),
             ("grotte", grotte), ("fg", fg)]:
    al = a[:, :, 3] > 0
    check("%s has content+transparency" % n, 500 < al.sum() < W * H - 500, "%d px" % al.sum())

# 4. element layers are disjoint (partition)
masks = [chemin[:, :, 3] > 0, rochers[:, :, 3] > 0, g[:, :, 3] > 0,
         d[:, :, 3] > 0, grotte[:, :, 3] > 0]
tot = np.zeros((H, W), int)
for m in masks:
    tot += m
check("element layers disjoint", (tot <= 1).all(), "overlap=%d" % (tot > 1).sum())

# 5. recomposition sans FG == base ground where no element + elements
comp_nofg = load("_composite_sans_fg.png")[:, :, :3]
keyed = np.asarray(Image.open(os.path.join(
    ROOT, "renders", "sinister_woods_gen_v1", "work", "terrain_keyed.png")))
orig_opaque = keyed[:, :, 3] > 0
union = tot > 0
# where elements sit on originally-opaque art, composite must equal it exactly
uo = union & orig_opaque
el = comp_nofg[uo] == keyed[:, :, :3][uo]
check("elements == original art pixels", bool(el.all()))
filled = (union & ~orig_opaque).sum()
check("filled fringe < 0.6% of canvas", filled < W * H * 0.006, "%d px" % filled)
# where no element and originally opaque, composite == original ground
gm = ~union & orig_opaque
check("ground == original where kept", bool((comp_nofg[gm] == keyed[:, :, :3][gm]).all()))

# 6. full composite == layers stacked
fullc = load("_composite.png")[:, :, :3]
stack = base[:, :, :3].copy()
for a in [chemin, rochers, g, d, grotte, fg]:
    m = a[:, :, 3] > 0
    stack[m] = a[m][:, :3]
check("composite == stack", bool((stack == fullc).all()))

# 7. no residual magenta anywhere
for n, a in [("sol", base), ("chemin", chemin), ("rochers", rochers), ("G", g),
             ("D", d), ("grotte", grotte), ("fg", fg)]:
    R, Gc, B = (a[:, :, i].astype(int) for i in range(3))
    mag = (R > 150) & (B > 150) & (Gc < 150) & (a[:, :, 3] > 0)
    check("no magenta in %s" % n, not mag.any(), "%d" % mag.sum())

# 8. path connectivity: bottom edge -> hollow
pm = chemin[:, :, 3] > 0
hm = grotte[:, :, 3] > 0
both = pm | ndimage.binary_dilation(hm, iterations=3)
lab, _ = ndimage.label(both)
bottom_ids = set(np.unique(lab[H - 1][both[H - 1]])) - {0}
hy, hx = np.where(hm)
hid = lab[hy[len(hy) // 2], hx[len(hx) // 2]]
check("path connects south edge to grove", hid in bottom_ids)

# 9. arrival span + hollow readable
span = pm[H - 4].sum()
check("arrival span >= 48px", span >= 48, "%d" % span)
check("hollow >= 8000px", hm.sum() >= 8000, "%d" % hm.sum())

# 10. manifest matches
man = json.load(open(os.path.join(LAY, "manifest.json")))
check("manifest canvas", man["canvas"] == [W, H])
check("manifest counts match", man["counts"]["chemin"] == int(pm.sum()))

print("ALL %d TESTS PASS" % N)
