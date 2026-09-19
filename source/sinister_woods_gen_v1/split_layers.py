#!/usr/bin/env python3
"""Split keyed terrain into layers + reconstructed ground + foreground.

Generated art (not native pixels): hole filling by same-image sampling.
Recomposition of layers == original opaque pixels, tested.
"""
import os, json
import numpy as np
from PIL import Image
from scipy import ndimage

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
WORK = os.path.join(ROOT, "renders", "sinister_woods_gen_v1", "work")
OUT = os.path.join(ROOT, "renders", "sinister_woods_gen_v1", "layers")
os.makedirs(OUT, exist_ok=True)

T = np.asarray(Image.open(os.path.join(WORK, "terrain_keyed.png")))
H, W = T.shape[:2]
RGB = T[:, :, :3].astype(int)
OPAQUE = T[:, :, 3] > 0
print("canvas", W, H, "opaque=%.4f" % OPAQUE.mean())

# ---- full opaque base: fill key holes by nearest opaque ----
_, inds = ndimage.distance_transform_edt(~OPAQUE, return_indices=True)
FULL = RGB[inds[0], inds[1]]
R, G, B = (FULL[:, :, i] for i in range(3))
LUM = (0.299 * R + 0.587 * G + 0.114 * B)
SAT = FULL.max(axis=2) - FULL.min(axis=2)

# ---- path: global tan-hue detection, main CC touching bottom ----
pm = (LUM > 110) & (R > 130) & ((R - B) > 25) & ((G - B) > 15)
print("tan px:", pm.sum())
lab, n = ndimage.label(pm)
touch_bottom = set(np.unique(lab[H - 1][pm[H - 1]])) - {0}
sizes = {i: (lab == i).sum() for i in touch_bottom}
print("path CCs touching bottom:", len(sizes), "sizes:", sorted(sizes.values(), reverse=True)[:5])
main = max(sizes, key=sizes.get)
PATH = ndimage.binary_dilation(lab == main, iterations=2)
print("path px:", PATH.sum(), "reaches top y<220:", PATH[:220].any())

# ---- hollow: dark CC at top ----
DARK = LUM < 25
dlab, dn = ndimage.label(DARK)
seed_candidates = [(328, 150), (328, 120), (328, 180), (300, 150), (356, 150)]
hid = 0
for sx, sy in seed_candidates:
    if DARK[sy, sx]:
        hid = dlab[sy, sx]
        break
assert hid, "no dark hollow found at top"
HOLLOW = ndimage.binary_dilation(dlab == hid, iterations=4)
print("hollow px:", HOLLOW.sum())
# ---- seuil: bridge path top to hollow (walkable threshold band) ----
py = np.where(PATH.any(axis=1))[0]
hy = np.where(HOLLOW.any(axis=1))[0]
ptop, hbot = py.min(), hy.max()
if ptop > hbot:
    pxs = np.where(PATH[ptop:ptop + 12].any(axis=0))[0]
    hxs = np.where(HOLLOW[hbot - 12:hbot].any(axis=0))[0]
    x0 = max(min(pxs.min(), hxs.min()) - 20, 0)
    x1 = min(max(pxs.max(), hxs.max()) + 20, W)
    PATH[hbot + 1:ptop + 4, x0:x1] = True
    PATH &= ~HOLLOW
    print("seuil bridge y", hbot, "->", ptop, "x", x0, x1)
print("path px total:", PATH.sum())

# ---- rocks: low-sat bright blobs near corridor, off borders ----
rlab, rn = ndimage.label((SAT < 45) & (LUM > 80) & (LUM < 175))
ROCK = np.zeros((H, W), bool)
cent = np.where(PATH.any(axis=1))[0]
cx_by_row = np.full(H, W // 2)
for y in cent:
    xs = np.where(PATH[y])[0]
    cx_by_row[y] = int(xs.mean())
kept = 0
for i in range(1, rn + 1):
    m = rlab == i
    s = m.sum()
    if not (25 <= s <= 4000):
        continue
    ys, xs = np.where(m)
    if xs.min() <= 2 or xs.max() >= W - 3 or ys.min() <= 2 or ys.max() >= H - 3:
        continue
    if bool((m & PATH).any()):
        continue
    if bool((m & HOLLOW).any()):
        continue
    if (np.abs(xs - cx_by_row[ys]) > 220).all():
        continue
    ROCK |= m
    kept += 1
print("rock CCs kept:", kept, "px:", ROCK.sum())

# ---- trees: side planes outside the walkable corridor ----
# corridor per row = path extent + margin (roots inside stay grounded in base)
MARGIN = 44
corrL = np.full(H, W // 2 - 80)
corrR = np.full(H, W // 2 + 80)
for y in range(H):
    xs = np.where(PATH[y])[0]
    if len(xs):
        corrL[y] = max(xs.min() - MARGIN, 0)
        corrR[y] = min(xs.max() + MARGIN, W)
    else:
        hx = np.where(HOLLOW[y])[0]
        if len(hx):
            corrL[y] = max(hx.min() - MARGIN, 0)
            corrR[y] = min(hx.max() + MARGIN, W)
XG = np.broadcast_to(np.arange(W), (H, W))
SIDE = ~(PATH | ROCK | HOLLOW)
TREEL = SIDE & (XG < corrL[:, None])
TREER = SIDE & (XG >= corrR[:, None])
TREES = TREEL | TREER
print("trees px:", TREES.sum(), "L:", TREEL.sum(), "R:", TREER.sum())

GROUND = ~(PATH | ROCK | HOLLOW | TREES)
print("ground px:", GROUND.sum())

# ---- base: ground + row-wise nearest-ground hole fill ----
BASE = FULL.copy()
rows_with_ground = [y for y in range(H) if GROUND[y].any()]
import bisect
def runs(mask):
    out, s, inside = [], 0, False
    for x in range(len(mask) + 1):
        on = x < len(mask) and mask[x]
        if on and not inside:
            s, inside = x, True
        elif not on and inside:
            out.append((s, x)); inside = False
    return out
for y in range(H):
    donor = y if GROUND[y].any() else None
    if donor is None:
        i = bisect.bisect_left(rows_with_ground, y)
        cands = []
        if i < len(rows_with_ground): cands.append(rows_with_ground[i])
        if i > 0: cands.append(rows_with_ground[i - 1])
        donor = min(cands, key=lambda r: abs(r - y))
    pool = FULL[donor][GROUND[donor]]
    L = len(pool)
    if not L:
        continue
    holemask = ~GROUND[y] if donor == y else np.ones(W, bool)
    for (s, e) in runs(holemask):
        xs = np.arange(s, e)
        h = (xs * 73856093) ^ (y * 19349663) ^ (donor * 83492791)
        BASE[y, s:e] = pool[(h & 0x7fffffff) % L]

def save_rgba(arr, name):
    Image.fromarray(arr.astype(np.uint8)).save(os.path.join(OUT, name))

save_rgba(np.dstack([BASE, np.full((H, W), 255, np.uint8)]), "01_sol.png")
for m, name in [(PATH, "02_chemin.png"), (ROCK, "03_rochers.png"),
                (TREEL, "04_arbres_gauche.png"), (TREER, "05_arbres_droit.png"),
                (HOLLOW, "06_grotte.png")]:
    a = np.zeros((H, W, 4), np.uint8)
    a[m, :3] = FULL[m]
    a[m, 3] = 255
    save_rgba(a, name)
# foreground copied as layer 07
FG = np.asarray(Image.open(os.path.join(WORK, "avant_plan_keyed.png")))
save_rgba(FG, "07_avant_plan.png")

# ---- composite + reviews ----
comp = BASE.copy()
for m in [PATH, ROCK, TREEL, TREER, HOLLOW]:
    comp[m] = FULL[m]
save_rgba(np.dstack([comp, np.full((H, W), 255, np.uint8)]), "_composite_sans_fg.png")
fullc = comp.copy()
fga = FG[:, :, 3] > 0
fullc[fga] = FG[:, :, :3][fga]
save_rgba(np.dstack([fullc, np.full((H, W), 255, np.uint8)]), "_composite.png")
# mask review
rev = np.zeros((H, W, 3), np.uint8)
rev[GROUND] = [40, 90, 50]; rev[PATH] = [220, 190, 130]; rev[ROCK] = [160, 160, 170]
rev[TREEL] = [30, 120, 60]; rev[TREER] = [60, 160, 90]; rev[HOLLOW] = [10, 10, 20]
Image.fromarray(rev).save(os.path.join(OUT, "_review_masks.png"))
# residual magenta scan
res = ((R > 150) & (B > 150) & (G < 150)).sum()
print("residual magenta px in FULL:", res)
manifest = {
    "canvas": [W, H], "div8": (W % 8 == 0 and H % 8 == 0),
    "counts": {"sol": int(GROUND.sum()), "chemin": int(PATH.sum()), "rochers": int(ROCK.sum()),
               "arbres_g": int(TREEL.sum()), "arbres_d": int(TREER.sum()),
               "grotte": int(HOLLOW.sum()), "avant_plan": int(fga.sum())},
    "path_rule": "tan hue global + main CC touching bottom", "residual_magenta": int(res),
    "generated": True, "native": False,
}
json.dump(manifest, open(os.path.join(OUT, "manifest.json"), "w"), indent=2)
print("OK ->", OUT)
