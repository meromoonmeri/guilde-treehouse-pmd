#!/usr/bin/env python3
"""Sinister Woods entrance — GENERATED render lot (not native pixels).

Bruts -> magenta keying -> independent layers -> 512x640 scene + anim.
Generated pixels: resampling/repartition documented and allowed here.
NOT certified as native tiles; see README.
"""
import json, hashlib, os, zipfile
import numpy as np
from PIL import Image
from scipy import ndimage

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SRC = os.path.join(ROOT, "source", "sinister_woods_gen_v1")
REN = os.path.join(ROOT, "renders", "sinister_woods_gen_v1")
BRUTS = os.path.join(REN, "bruts")
LAY = os.path.join(REN, "calques")
ANIM = os.path.join(REN, "anim")
for d in (LAY, ANIM):
    os.makedirs(d, exist_ok=True)

W, H = 512, 640

def sha(f):
    return hashlib.sha256(open(f, "rb").read()).hexdigest()

def key(f):
    """Magenta -> alpha. Returns RGBA array + fg mask. Despill edge fringe."""
    a = np.asarray(Image.open(f).convert("RGB")).astype(int)
    R, G, B = a[:, :, 0], a[:, :, 1], a[:, :, 2]
    mag = (R > 150) & (B > 150) & (G < 190) & ((R + B) / 2 > G + 40)
    fg = ~mag
    # drop tiny specks (<150px)
    lab, n = ndimage.label(fg)
    for i in range(1, n + 1):
        if (lab == i).sum() < 150:
            fg[lab == i] = False
    rgba = np.zeros((*fg.shape, 4), np.uint8)
    rgba[fg, :3] = a[fg].astype(np.uint8)
    rgba[fg, 3] = 255
    # despill: edge fg pixels with magenta tint get R,B clamped toward G
    edge = fg & ~ndimage.binary_erosion(fg)
    ring2 = fg & ~ndimage.binary_erosion(fg, iterations=2) & ~edge
    er, eg, eb = a[:, :, 0], a[:, :, 1], a[:, :, 2]
    tint = (edge | ring2) & (er > 120) & (eb > 120) & (np.minimum(er, eb) > eg + 20)
    rgba[tint, 0] = np.minimum(er[tint], eg[tint] + 30).astype(np.uint8)
    rgba[tint, 2] = np.minimum(eb[tint], eg[tint] + 30).astype(np.uint8)
    return rgba, fg

# ---------------- terrain -> opaque 512x640 base ----------------
t_rgba, t_fg = key(os.path.join(BRUTS, "terrain_foret_sombre.png"))
th, tw = t_fg.shape
# fixed content crop (margins，快): x 36..812, y 60..1030 -> ratio 0.8 exactly
CX0, CY0, CX1, CY1 = 36, 60, 812, 1030
assert (CX1 - CX0) * H == (CY1 - CY0) * W, "crop must match 512:640"
base_crop = t_rgba[CY0:CY1, CX0:CX1]
base_img = Image.fromarray(base_crop).resize((W, H), Image.LANCZOS)
base = np.asarray(base_img)
# inpaint residual transparency (magenta corners) by nearest fill
alpha = base[:, :, 3]
if (alpha == 0).any():
    frac = (alpha == 0).mean()
    print("base transparent frac after resize: %.3f" % frac)
    assert frac < 0.03, "too much magenta inside terrain crop"
    _, idx = ndimage.distance_transform_edt(alpha == 0, return_indices=True)
    filled = base[idx[0], idx[1]]
    filled[:, :, 3] = 255
    base = filled
else:
    base[:, :, 3] = 255
Image.fromarray(base).save(os.path.join(LAY, "00_base_terrain.png"))
np.save(os.path.join(LAY, "_base_crop.npy"), np.array([CX0, CY0, CX1, CY1]))

# ---------------- specimens ----------------
a_rgba, a_fg = key(os.path.join(BRUTS, "arbres_specimens.png"))
lab, n = ndimage.label(a_fg)
specs = []
for i in range(1, n + 1):
    ys, xs = np.where(lab == i)
    s = len(xs)
    if s < 150:
        continue
    specs.append((s, int(xs.min()), int(ys.min()), int(xs.max()) + 1, int(ys.max()) + 1))
specs.sort(reverse=True)
print("specimens:", specs)
names = ["arbre_A", "arbre_B", "arbre_C", "buisson_A", "buisson_B",
         "caillou_1", "caillou_2", "caillou_3", "caillou_4"]
spec_files = {}
for k, (s, x0, y0, x1, y1) in enumerate(specs):
    nm = names[k] if k < len(names) else ("obj_%d" % k)
    Image.fromarray(a_rgba[y0:y1, x0:x1]).save(os.path.join(LAY, "spec_" + nm + ".png"))
    spec_files[nm] = (x0, y0, x1, y1, s)

# ---------------- frises: split giant CC by overlap cuts ----------------
f_rgba, f_fg = key(os.path.join(BRUTS, "frises_avant_plan.png"))
fh, fw = f_fg.shape
lab, n = ndimage.label(f_fg)
comps = []
for i in range(1, n + 1):
    ys, xs = np.where(lab == i)
    if len(xs) >= 150:
        comps.append((len(xs), int(xs.min()), int(ys.min()), int(xs.max()) + 1, int(ys.max()) + 1))
comps.sort(reverse=True)
print("frise comps:", comps)
giant = comps[0]
gx0, gy0, gx1, gy1 = giant[1:]
# column fg counts in candidate bands -> thinnest cut columns
colcount = f_fg[gy0:gy1, gx0:gx1].sum(axis=0)
band1 = range(230, 430)
band2 = range(700, 900)
c1 = gx0 + min(band1, key=lambda x: colcount[x - gx0])
c2 = gx0 + min(band2, key=lambda x: colcount[x - gx0])
print("cut columns:", c1, c2, "counts:", colcount[c1 - gx0], colcount[c2 - gx0])
OV = 6  # overlap: duplicated pixels stay identical across layers
parts = {
    "frise_gauche": (gx0, gy0, c1 + OV, gy1),
    "arche_haut": (c1 - OV, 300, c2 + OV, gy1),
    "frise_droite": (c2 - OV, gy0, gx1, gy1),
    "herbe_bas": comps[1][1:],
}
frise_files = {}
for nm, (x0, y0, x1, y1) in parts.items():
    sub = f_rgba[y0:y1, x0:x1].copy()
    sub[~f_fg[y0:y1, x0:x1]] = (0, 0, 0, 0)
    Image.fromarray(sub).save(os.path.join(LAY, "part_" + nm + ".png"))
    frise_files[nm] = (x0, y0, x1, y1)

# ---------------- scene assembly ----------------
def paste(canvas, img, dst):
    dx, dy = dst
    h, w = img.shape[:2]
    cx0, cy0 = max(dx, 0), max(dy, 0)
    cx1, cy1 = min(dx + w, W), min(dy + h, H)
    if cx1 <= cx0 or cy1 <= cy0:
        return
    patch = img[cy0 - dy:cy1 - dy, cx0 - dx:cx1 - dx]
    m = patch[:, :, 3] > 0
    canvas[cy0:cy1, cx0:cx1][m] = patch[m]

def scaled(path, f):
    im = Image.open(path)
    nw, nh = max(int(im.width * f), 1), max(int(im.height * f), 1)
    return np.asarray(im.resize((nw, nh), Image.LANCZOS))

# placement table (8px grid) — tuned for 512x640
place = [
    ("01_arbre_B_devant_gauche", "spec_arbre_B.png", 0.42, (-24, 392)),
    ("02_arbre_C_devant_droit", "spec_arbre_C.png", 0.42, (384, 392)),
    ("03_arbre_A_milieu_gauche", "spec_arbre_A.png", 0.34, (88, 240)),
    ("04_buisson_A_milieu", "spec_buisson_A.png", 0.34, (152, 296)),
    ("05_buisson_B_milieu", "spec_buisson_B.png", 0.34, (248, 296)),
    ("06_frise_gauche", "part_frise_gauche.png", 0.86, (-160, 24)),
    ("07_frise_droite", "part_frise_droite.png", 0.86, (384, 24)),
    ("08_arche_grove", "part_arche_haut.png", 0.55, (128, 176)),
    ("09_herbe_bas_gauche", "part_herbe_bas.png", 0.60, (-8, 560)),
    ("10_herbe_bas_droite", "part_herbe_bas.png", 0.60, (264, 560)),
]
layers = {"00_base_terrain": base.copy()}
for lname, f, s, dst in place:
    img = scaled(os.path.join(LAY, f), s)
    if lname == "09_herbe_bas_gauche":
        img = img[:, :img.shape[1] // 2]
    if lname == "10_herbe_bas_droite":
        img = img[:, img.shape[1] // 2:]
    cv = np.zeros((H, W, 4), np.uint8)
    paste(cv, img, dst)
    layers[lname] = cv
    Image.fromarray(cv).save(os.path.join(LAY, lname + ".png"))

order = ["00_base_terrain"] + [p[0] for p in place]
# global residual-purple kill (no legitimate purple in this dark-green palette)
for nm in order:
    la = layers[nm]
    m = la[:, :, 3] > 0
    R, G, B = la[:, :, 0].astype(int), la[:, :, 1].astype(int), la[:, :, 2].astype(int)
    purp = m & (R > 130) & (B > 130) & (np.minimum(R, B) > G + 30)
    bluev = m & (B > 150) & (B > G + 60) & (B > R + 30)
    purp |= bluev
    la[purp] = np.stack([np.minimum(R[purp], G[purp] + 25),
                         G[purp],
                         np.minimum(B[purp], G[purp] + 25),
                         la[purp][:, 3]], axis=1).astype(np.uint8)
    Image.fromarray(la).save(os.path.join(LAY, nm + ".png"))
    print("despill", nm, int(purp.sum()))
comp = np.zeros((H, W, 3), np.uint8)
for nm in order:
    la = layers[nm]
    m = la[:, :, 3] > 0
    comp[m] = la[m][:, :3]
Image.fromarray(comp).save(os.path.join(REN, "scene_composite.png"))

# ---------------- grove pulse + fireflies ----------------
# grove mask in scene coords: dark CC near (256,~320); ellipse fallback
blum = base[:, :, :3].astype(int).mean(axis=2)
gm = (blum < 55)
roi = np.zeros_like(gm); roi[200:420, 150:362] = True
gm &= roi
lab, n = ndimage.label(gm)
best, gmask = 0, None
for i in range(1, n + 1):
    s = (lab == i).sum()
    if s > best:
        best, gmask = s, lab == i
if gmask is None or best > 6000 or best < 60:
    yy, xx = np.mgrid[0:H, 0:W]
    gmask = ((xx - 256) / 55) ** 2 + ((yy - 323) / 45) ** 2 <= 1
    print("grove: ellipse fallback (cc size=%s)" % best)
gmask = ndimage.binary_dilation(gmask, iterations=4)
print("grove scene px:", int(gmask.sum()))
Image.fromarray((gmask * 255).astype(np.uint8)).save(os.path.join(ANIM, "_grove_mask.png"))
# pulse: 4 frames of extra shadow alpha over grove
for i, al in enumerate([0, 70, 130, 70]):
    ov = np.zeros((H, W, 4), np.uint8)
    ov[gmask, :3] = (0, 0, 0)
    ov[gmask, 3] = al
    Image.fromarray(ov).save(os.path.join(ANIM, "pulse_%d.png" % i))
# fireflies: 10 dots, 8 frames drift+blink (procedural VFX)
rng = np.random.RandomState(11)
seeds = [(int(rng.uniform(90, 422)), int(rng.uniform(180, 520))) for _ in range(10)]
frames = []
for f in range(8):
    ov = np.zeros((H, W, 4), np.uint8)
    for k, (sx, sy) in enumerate(seeds):
        x = int(sx + 14 * np.sin(2 * np.pi * (f / 8) + k * 1.7))
        y = int(sy + 10 * np.cos(2 * np.pi * (f / 8) + k * 2.3))
        on = 0.35 + 0.65 * (0.5 + 0.5 * np.sin(2 * np.pi * (f / 8) + k * 3.1))
        al = int(230 * on)
        for dy in (-1, 0, 1):
            for dx in (-1, 0, 1):
                if abs(dx) + abs(dy) <= 1 and 0 <= x + dx < W and 0 <= y + dy < H:
                    ov[y + dy, x + dx] = (210, 255, 160, al if (dx == 0 and dy == 0) else al // 3)
    Image.fromarray(ov).save(os.path.join(ANIM, "firefly_%d.png" % f))
    frames.append(ov)
# animated preview GIF: base scene + pulse + fireflies
puls = [np.asarray(Image.open(os.path.join(ANIM, "pulse_%d.png" % (i % 4)))) for i in range(8)]
gifs = []
for i in range(8):
    fr = comp.copy()
    for ov in (puls[i], frames[i]):
        a = ov[:, :, 3:4].astype(int)
        fr = ((fr.astype(int) * (255 - a) + ov[:, :, :3].astype(int) * a) // 255).astype(np.uint8)
    gifs.append(Image.fromarray(fr))
gifs[0].save(os.path.join(REN, "scene_animee.gif"), save_all=True, append_images=gifs[1:],
             duration=150, loop=0)

manifest = {
    "lot": "sinister_woods_gen_v1", "scene": {"w": W, "h": H},
    "method": "GENERATED render (magenta keying). Not native tiles.",
    "bruts": {f: sha(os.path.join(BRUTS, f)) for f in sorted(os.listdir(BRUTS))},
    "references": ["Mystifying_Forest_entrance_TDS.png", "Southern_Jungle_entrance_S.png"],
    "terrain_crop": {"box": [CX0, CY0, CX1, CY1], "src": [tw, th]},
    "cut_columns": [int(c1), int(c2)],
    "specimens": spec_files, "frises": frise_files,
    "layers_order": order,
    "counts": {k: int((v[:, :, 3] > 0).sum()) for k, v in layers.items()},
    "anim": {"pulse": 4, "fireflies": 8, "gif_ms": 150},
}
json.dump(manifest, open(os.path.join(REN, "manifest.json"), "w"), indent=2)
print("counts:", manifest["counts"])
print("OK ->", REN)
