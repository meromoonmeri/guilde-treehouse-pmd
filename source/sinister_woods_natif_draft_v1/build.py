#!/usr/bin/env python3
"""Sinister Woods style forest entrance — south->north native relayout.

Guide = V3 forest_guide composition only. Final pixels: 100% native
(Mystifying Forest + Southern Jungle), no mirror/rotation/scale/recolor.
Per-layer NPZ provenance: source_sxy[y,x] = [src_id, sx, sy] or -1.
"""
import json, hashlib, os, random
import numpy as np
from PIL import Image
from scipy import ndimage

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SRC = os.path.join(ROOT, "source", "sinister_woods_natif_draft_v1")
EXP = os.path.join(ROOT, "exports", "sinister_woods_natif_draft_v1")
os.makedirs(EXP, exist_ok=True)

spec = json.load(open(os.path.join(SRC, "spec.json")))
W, H = spec["scene"]["width"], spec["scene"]["height"]

SRC_IDS = {"mystifying": 0, "jungle": 1}
sources = {}
sha = {}
for name, fname in spec["sources"].items():
    p = os.path.join(ROOT, fname)
    im = Image.open(p).convert("RGB")
    sources[name] = np.asarray(im)
    h = hashlib.sha256(open(p, "rb").read()).hexdigest()
    sha[name] = {"file": fname, "sha256": h, "size": list(im.size)}

class Layer:
    def __init__(self):
        self.rgba = np.zeros((H, W, 4), np.uint8)
        self.prov = np.full((H, W, 3), -1, np.int16)
    def blit(self, src_name, sbox, dst, mask=None):
        sx0, sy0, sx1, sy1 = sbox
        dx, dy = dst
        w, h = sx1 - sx0, sy1 - sy0
        # clip to canvas
        cx0, cy0 = max(dx, 0), max(dy, 0)
        cx1, cy1 = min(dx + w, W), min(dy + h, H)
        if cx1 <= cx0 or cy1 <= cy0:
            return
        ox0, oy0 = cx0 - dx, cy0 - dy
        src = sources[src_name]
        sh, sw = src.shape[:2]
        # clip to source
        sxa, sya = sx0 + ox0, sy0 + oy0
        sxb, syb = sxa + (cx1 - cx0), sya + (cy1 - cy0)
        assert 0 <= sxa and 0 <= sya and sxb <= sw and syb <= sh, (src_name, sbox, dst)
        patch = src[sya:syb, sxa:sxb]
        if mask is not None:
            m = mask[oy0:oy0 + (cy1 - cy0), ox0:ox0 + (cx1 - cx0)]
        else:
            m = np.ones((cy1 - cy0, cx1 - cx0), bool)
        if not m.any():
            return
        region = self.rgba[cy0:cy1, cx0:cx1]
        region[m, :3] = patch[m]
        region[m, 3] = 255
        yy, xx = np.mgrid[cy0:cy1, cx0:cx1]
        self.prov[cy0:cy1, cx0:cx1][m] = np.stack(
            [np.full(m.sum(), SRC_IDS[src_name]),
             (xx[m] - dx + sx0).astype(np.int16),
             (yy[m] - dy + sy0).astype(np.int16)], axis=1)
    def save(self, name):
        Image.fromarray(self.rgba).save(os.path.join(EXP, name + ".png"))
        np.savez_compressed(os.path.join(EXP, name + "_source.npz"),
                            source_sxy=self.prov)

layers = {}
def L(name):
    layers[name] = Layer()
    return layers[name]

# ---------- 01_soil : brick tiling of two native grass fields ----------
soil = L("01_soil")
GF = spec["soil_fields"]
fields = [("mystifying", GF["GF1"]), ("mystifying", GF["GF2"])]
T = GF["tile"]
rng = random.Random(7)
wins = []
for src, (fx0, fy0, fx1, fy1) in fields:
    for wy in range(fy0, fy1 - T + 1, 16):
        for wx in range(fx0, fx1 - T + 1, 16):
            wins.append((src, wx, wy))
for row in range((H + T - 1) // T + 1):
    off = (row % 2) * (T // 2)
    for col in range(-1, (W + T - 1) // T + 1):
        src, wx, wy = wins[rng.randrange(len(wins))]
        soil.blit(src, (wx, wy, wx + T, wy + T), (col * T + off, row * T))
assert (soil.rgba[:, :, 3] == 255).all(), "soil must be fully opaque"

# ---------- path mask : Catmull-Rom through spec points ----------
def catmull(points, samples=400):
    pts = [points[0]] + points + [points[-1]]
    out = []
    for i in range(1, len(pts) - 2):
        p0, p1, p2, p3 = [np.array(p, float) for p in pts[i-1:i+3]]
        for t in np.linspace(0, 1, samples // (len(points) - 1)):
            t2, t3 = t * t, t * t * t
            out.append(0.5 * ((2*p1) + (-p0+p2)*t + (2*p0-5*p1+4*p2-p3)*t2 + (-p0+3*p1-3*p2+p3)*t3))
    return np.array(out)

PW = spec["path_width"]
curve = catmull([(y, x) for y, x in spec["path_curve"]])
path_mask = np.zeros((H, W), bool)
for (yy, xx) in curve:
    y0, y1 = max(int(yy)-2, 0), min(int(yy)+3, H)
    x0, x1 = max(int(xx)-PW//2, 0), min(int(xx)+PW//2, W)
    path_mask[y0:y1, x0:x1] = True
cy, cx = spec["clearing"]["center"][1], spec["clearing"]["center"][0]
rr = spec["clearing"]["r"]
yy, xx = np.mgrid[0:H, 0:W]
path_mask |= ((yy - cy) ** 2 + (xx - cx) ** 2) <= rr * rr
ax0, ay0, ax1, ay1 = spec["arrival_apron"]
path_mask[ay0:ay1, ax0:ax1] = True
Image.fromarray((path_mask * 255).astype(np.uint8)).save(os.path.join(EXP, "_review_path_mask.png"))

# ---------- 02_path : stamp native path patch, clip to mask ----------
path = L("02_path")
pfx0, pfy0, pfx1, pfy1 = spec["path_field"]
pwins = []
for wy in range(pfy0, pfy1 - 56 + 1, 8):
    for wx in range(pfx0, pfx1 - 56 + 1, 8):
        pwins.append((wx, wy))
assert pwins, "path field too small for 56px windows"
step = 40
for gy in range(-8, H, step):
    for gx in range(-8, W, step):
        # stamp only if near the path mask
        x0, x1 = max(gx, 0), min(gx + 56, W)
        y0, y1 = max(gy, 0), min(gy + 56, H)
        if not path_mask[y0:y1, x0:x1].any():
            continue
        wx, wy = pwins[rng.randrange(len(pwins))]
        sbox = (wx, wy, min(wx + 56, pfx1), min(wy + 56, pfy1))
        full = np.zeros((sbox[3]-sbox[1], sbox[2]-sbox[0]), bool)
        mx0, my0 = max(-gx, 0), max(-gy, 0)
        sub = path_mask[max(gy,0):min(gy+56,H), max(gx,0):min(gx+56,W)]
        full[my0:my0+sub.shape[0], mx0:mx0+sub.shape[1]] = sub
        path.blit("mystifying", sbox, (gx, gy), full)
# keep ONLY path pixels (erase stamps outside mask — blit already clips via mask)
assert (path.rgba[:, :, 3] > 0).sum() > 0

# ---------- cutout masks ----------
def rock_mask(src_arr, box):
    x0, y0, x1, y1 = box
    p = src_arr[y0:y1, x0:x1].astype(int)
    R, G, B = p[:, :, 0], p[:, :, 1], p[:, :, 2]
    keep = (R > 100) & (G > 90) & (B > 75) & ((G - R) < 12) & ((R - B) < 60)
    lab, n = ndimage.label(keep)
    if n == 0:
        return keep
    sizes = ndimage.sum(keep, lab, range(1, n + 1))
    biggest = 1 + int(np.argmax(sizes))
    m = lab == biggest
    return ndimage.binary_fill_holes(m)

def tuft_mask(src_arr, box):
    x0, y0, x1, y1 = box
    p = src_arr[y0:y1, x0:x1].astype(int)
    R, G, B = p[:, :, 0], p[:, :, 1], p[:, :, 2]
    keep = (G > 115) & ((G - R) > 8) & ((G - B) > 5)
    lab, n = ndimage.label(keep)
    m = np.zeros_like(keep)
    for i in range(1, n + 1):
        if (lab == i).sum() >= 20:
            m |= lab == i
    return m

# ---------- 03_undergrowth : tufts ----------
under = L("03_undergrowth")
for t in spec["tufts"]:
    m = tuft_mask(sources[t["src"]], t["box"])
    under.blit(t["src"], t["box"], t["dst"], m)

# ---------- 04_rocks ----------
rocks = L("04_rocks")
for r in spec["rocks"]:
    m = rock_mask(sources[r["src"]], r["box"])
    rocks.blit(r["src"], r["box"], r["dst"], m)

# ---------- 05_grove_dark ----------
grove = L("05_grove_dark")
g = spec["grove"]
grove.blit(g["interior_src"]["src"], g["interior_src"]["box"], g["interior_dst"])
grove.blit(g["deepslot_src"]["src"], g["deepslot_src"]["box"], g["deepslot_dst"])

# ---------- 06_trunks / 07_canopies : trees split + leaves arch ----------
trunks = L("06_trunks")
canop = L("07_canopies")
SPLIT = spec["trunk_split"]
OV = spec["canopy_overlap"]
for t in spec["trees"]:
    x0, y0, x1, y1 = t["box"]
    w, h = x1 - x0, y1 - y0
    cut = int(h * SPLIT)
    full_t = np.zeros((h, w), bool); full_t[cut:, :] = True
    full_c = np.zeros((h, w), bool); full_c[:cut + OV, :] = True
    trunks.blit(t["src"], t["box"], t["dst"], full_t)
    canop.blit(t["src"], t["box"], t["dst"], full_c)
for lv in spec["leaves_arch"]:
    canop.blit(lv["src"], lv["box"], lv["dst"])

# ---------- 08_fringe ----------
fringe = L("08_fringe")
for f in spec["fringe"]:
    fringe.blit(f["src"], f["box"], f["dst"])

# ---------- save, composite, manifest ----------
order = spec["layers_order"]
for name in order:
    layers[name].save("SinisterV1_" + name)
comp = np.zeros((H, W, 3), np.uint8)
for name in order:
    la = layers[name].rgba
    m = la[:, :, 3] > 0
    comp[m] = la[m][:, :3]
Image.fromarray(comp).save(os.path.join(EXP, "SinisterV1_composite.png"))

# review: cutouts sheet
sheet = []
for r in spec["rocks"]:
    x0, y0, x1, y1 = r["box"]
    p = sources[r["src"]][y0:y1, x0:x1].copy()
    m = rock_mask(sources[r["src"]], r["box"])
    sheet.append((p, m, "rock"))
for t in spec["tufts"][:2]:
    x0, y0, x1, y1 = t["box"]
    p = sources[t["src"]][y0:y1, x0:x1].copy()
    m = tuft_mask(sources[t["src"]], t["box"])
    sheet.append((p, m, "tuft"))
sw = max(p.shape[1] for p, m, k in sheet)
sh = sum(p.shape[0] + 4 for p, m, k in sheet)
canvas = np.full((sh, sw * 2 + 8, 3), 255, np.uint8)
yy = 0
for p, m, k in sheet:
    h, w = p.shape[:2]
    canvas[yy:yy+h, 0:w] = p
    masked = np.full_like(p, 255)
    masked[m] = p[m]
    canvas[yy:yy+h, sw+8:sw+8+w] = masked
    yy += h + 4
Image.fromarray(canvas).save(os.path.join(EXP, "_review_cutouts.png"))

manifest = {
    "lot": spec["lot"], "scene": spec["scene"], "layers_order": order,
    "sources": sha, "guide": spec["guide_reused"],
    "counts": {n: int((layers[n].rgba[:, :, 3] > 0).sum()) for n in order},
}
json.dump(manifest, open(os.path.join(EXP, "manifest.json"), "w"), indent=2)
print("counts:", manifest["counts"])
print("OK ->", EXP)
