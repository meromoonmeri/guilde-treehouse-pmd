#!/usr/bin/env python3
"""Sinister Woods forest entrance — GENERATED render lot (methode rendus generes).

Inputs: 2 generated bruts on magenta (scene + bare ground).
Pipeline: magenta flood cutout -> blue-parasite cleanup -> color/texture
partition into planes -> review sheets -> gallery/ZIP.
Generated pixels are PMD-style art, NOT native certified tiles.
"""
import json, hashlib, os
import numpy as np
from PIL import Image
from scipy import ndimage

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SRC = os.path.join(ROOT, "source", "sinister_woods_partition_v1")
BRUTS = os.path.join(ROOT, "renders", "sinister_woods_gen_v1", "bruts")
EXP = os.path.join(ROOT, "renders", "sinister_woods_gen_v1")
os.makedirs(EXP, exist_ok=True)
os.makedirs(SRC, exist_ok=True)

A = np.asarray(Image.open(os.path.join(BRUTS, "foret_entree_magenta.png")).convert("RGB")).astype(int)
H, W, _ = A.shape
assert (W % 8 == 0) and (H % 8 == 0), (W, H)
R, G, B = A[:, :, 0], A[:, :, 1], A[:, :, 2]

# ---------- 1. magenta flood alpha ----------
# wide rule catches anti-aliased magenta fringe; dark canopy/path/rock excluded
maglike = (R > 100) & (B > 100) & (G < 110) & ((R - G) > 40) & ((B - G) > 40)
seed = np.zeros_like(maglike)
seed[0, :] = maglike[0, :]; seed[-1, :] = maglike[-1, :]
seed[:, 0] = maglike[:, 0]; seed[:, -1] = maglike[:, -1]
outside = ndimage.binary_propagation(seed, mask=maglike)
terrain = ~outside
print("terrain px: %d (%.1f%%), interior magenta holes: %d"
      % (terrain.sum(), 100 * terrain.sum() / terrain.size, (maglike & terrain).sum()))
Image.fromarray((terrain * 255).astype(np.uint8)).save(os.path.join(EXP, "_review_alpha.png"))

# preliminary path mask (for same-family donor search)
m_chemin_pre = terrain & (R > 115) & (G > 95) & (B < 140) & ((R - B) > 18) & ((G - B) > 5)

# preliminary path mask (for same-family donor search)
m_chemin_pre = terrain & (R > 115) & (G > 95) & (B < 140) & ((R - B) > 18) & ((G - B) > 5)

# ---------- 2. blue parasites ----------
blue = terrain & (B > 100) & (B - R > 40) & (B - G > 15)
# include the shards' dark outlines (else a dark oval remains)
blue = ndimage.binary_dilation(blue, iterations=3) & terrain
lab, n = ndimage.label(blue)
print("blue CCs:", n)
clean = A.copy()
for i in range(1, n + 1):
    ys, xs = np.where(lab == i)
    if len(xs) == 0:
        continue
    x0, x1 = xs.min(), xs.max() + 1
    y0, y1 = ys.min(), ys.max() + 1
    print("  blue #%d: n=%d bbox=(%d,%d,%d,%d)" % (i, len(xs), x0, y0, x1, y1))
    h, w = y1 - y0, x1 - x0
    # per-pixel ring-median inpaint from clean terrain neighbours (no foreign blobs)
    fam = m_chemin_pre[y0:y1, x0:x1]
    for (yy, xx) in zip(ys, xs):
        want_path = fam[yy - y0, xx - x0]
        done = False
        for rad in (3, 5, 8, 12, 18, 26):
            r0, r1 = max(yy - rad, 0), min(yy + rad + 1, H)
            c0, c1 = max(xx - rad, 0), min(xx + rad + 1, W)
            ring = terrain[r0:r1, c0:c1] & ~blue[r0:r1, c0:c1]
            if want_path:
                ring &= m_chemin_pre[r0:r1, c0:c1]
            else:
                ring &= ~m_chemin_pre[r0:r1, c0:c1]
            if ring.sum() >= 12:
                clean[yy, xx] = np.median(A[r0:r1, c0:c1][ring], axis=0)
                done = True
                break
        if not done:
            clean[yy, xx] = np.median(A[max(yy-30,0):yy+30, max(xx-30,0):xx+30].reshape(-1, 3), axis=0)
    print("    -> ring-median inpaint, want_path=%s" % bool(fam.mean() > 0.25))
R, G, B = clean[:, :, 0], clean[:, :, 1], clean[:, :, 2]
blue_after = terrain & (B > 100) & (B - R > 40) & (B - G > 15)
print("blue remaining:", blue_after.sum())

# ---------- 3. partition (priority order) ----------
SUM = R + G + B
MX = np.maximum(np.maximum(R, G), B)
MN = np.minimum(np.minimum(R, G), B)
SAT = MX - MN

m_chemin = terrain & (R > 115) & (G > 95) & (B < 140) & ((R - B) > 18) & ((G - B) > 5)
m_rocher = terrain & ~m_chemin & (R > 80) & (B > 80) & (SAT < 32) & (SUM > 280) & (SUM < 520)
# grotte: purple-black opening vs green-black foliage. Brightness cannot
# separate them (both SUM~60); hue does: opening G-R<0, foliage G-R~+39.
# Zone (680,50,790,210), rule SUM<110 & (G-R)<12, largest CC, holes filled.
zone = np.zeros_like(terrain); zone[50:210, 640:790] = True
cand = terrain & zone & (SUM < 110) & ((G - R) < 12)
lab0, n0 = ndimage.label(cand)
if n0:
    sizes0 = ndimage.sum(cand, lab0, range(1, n0 + 1))
    core = lab0 == (1 + int(np.argmax(sizes0)))
    m_grotte = ndimage.binary_fill_holes(core)
    # organic portal frame: intersect with documented ellipse (cuts only dark px)
    yy, xx = np.mgrid[0:H, 0:W]
    m_grotte &= ((xx - 707) / 67.0) ** 2 + ((yy - 131) / 60.0) ** 2 <= 1.0
else:
    m_grotte = np.zeros_like(terrain)
# ombres: strict deep hollows only
m_ombre = terrain & ~m_chemin & ~m_rocher & ~m_grotte & (SUM < 38)
# vegetation haute: texture = highlight density (light-green speckles)
hi = terrain & (G > 55) & ((G - R) > 20) & ((G - B) > 8)
dens = ndimage.uniform_filter(hi.astype(float), size=24)
rest = terrain & ~m_chemin & ~m_rocher & ~m_grotte & ~m_ombre
# sol vs vegetation: spatial split along the path corridor (smooth boundary).
# Color/texture cannot separate dark moss from dark canopy in this art.
corridor = ndimage.binary_dilation(m_chemin, iterations=90)
m_vege = rest & ~corridor
# buissons: mid-green small blobs near center band (630..990) not already taken
center = np.zeros_like(terrain); center[:, 560:1050] = True
cand_b = terrain & center & ~m_chemin & ~m_rocher & ~m_grotte & ~m_ombre & (G > 45) & (G < 110) & (R < 70) & (R > 5)
labb, nb = ndimage.label(cand_b)
m_buisson = np.zeros_like(terrain)
for i in range(1, nb + 1):
    s = (labb == i).sum()
    if 150 <= s <= 6000:
        m_buisson |= labb == i
m_buisson &= ~m_vege
# sol = remainder (central corridor ground)
m_sol = terrain & ~m_chemin & ~m_rocher & ~m_grotte & ~m_ombre & ~m_vege & ~m_buisson

masks = [("01_sol", m_sol), ("02_chemin", m_chemin), ("03_rochers", m_rocher),
         ("04_buissons", m_buisson), ("05_vegetation", m_vege),
         ("06_ombres", m_ombre), ("07_grotte", m_grotte)]
for name, m in masks:
    print("%-14s %d (%.1f%%)" % (name, m.sum(), 100 * m.sum() / terrain.sum()))
tot = sum(m.sum() for _, m in masks)
print("partition cover: %d / %d, overlap check:" % (tot, terrain.sum()), tot == terrain.sum())

# ---------- 4. save planes ----------
for name, m in masks:
    rgba = np.zeros((H, W, 4), np.uint8)
    rgba[m, :3] = clean[m]
    rgba[m, 3] = 255
    Image.fromarray(rgba).save(os.path.join(EXP, "SinisterGen_%s.png" % name))
# recomposition check
comp = np.zeros((H, W, 3), np.uint8)
for _, m in masks:
    comp[m] = clean[m]
base = np.zeros((H, W, 3), np.uint8)
base[terrain] = clean[terrain]
print("recomposition exact:", np.array_equal(comp, base))
Image.fromarray(base).save(os.path.join(EXP, "SinisterGen_composite.png"))

# ---------- 5. review sheet ----------
cols = {"01_sol": (90, 140, 90), "02_chemin": (210, 180, 120), "03_rochers": (160, 160, 170),
        "04_buissons": (60, 200, 80), "05_vegetation": (10, 90, 40),
        "06_ombres": (120, 40, 160), "07_grotte": (255, 60, 60)}
sheet = np.full((H, W, 3), 255, np.uint8)
sheet[terrain] = (40, 40, 40)
for name, m in masks:
    sheet[m] = cols[name]
small = Image.fromarray(sheet).resize((W // 2, H // 2), Image.NEAREST)
small.save(os.path.join(EXP, "_review_partition.png"))
# zoom strips: grotte + shard area + path mid
for name, box in {"grotte": (700, 60, 900, 260), "shard": (680, 400, 860, 540), "rocks": (600, 280, 950, 400)}.items():
    x0, y0, x1, y1 = box
    pair = np.zeros((y1 - y0, (x1 - x0) * 2 + 8, 3), np.uint8) + 255
    pair[:, :x1 - x0] = A[y0:y1, x0:x1]
    pair[:, x1 - x0 + 8:] = base[y0:y1, x0:x1]
    Image.fromarray(pair).save(os.path.join(EXP, "_review_%s.png" % name))
print("OK ->", EXP)
