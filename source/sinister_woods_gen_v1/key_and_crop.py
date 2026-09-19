#!/usr/bin/env python3
"""Key magenta, despill, crop to common 656x1376 canvas (divisible by 8)."""
import os
import numpy as np
from PIL import Image
from scipy import ndimage

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
BRUTS = os.path.join(ROOT, "renders", "sinister_woods_gen_v1", "bruts")
WORK = os.path.join(ROOT, "renders", "sinister_woods_gen_v1", "work")
os.makedirs(WORK, exist_ok=True)

X0, X1 = 56, 712  # 656 px, art bbox rounded to 8px

def key_magenta(rgb):
    R, G, B = rgb[:, :, 0].astype(int), rgb[:, :, 1].astype(int), rgb[:, :, 2].astype(int)
    core = (R > 150) & (B > 150) & (G < 150)
    # region growing: near-magenta tints adjacent to core (fringe + interior specks)
    near = (R > 120) & (B > 120) & ((R - G) > 25) & ((B - G) > 25)
    grown = core.copy()
    for _ in range(3):
        grown = grown | (ndimage.binary_dilation(grown, iterations=1) & near)
    mag = grown
    # kill strongly tinted edge pixels outright
    edge = ndimage.binary_dilation(mag, iterations=1) & ~mag
    kill = edge & (R > 120) & ((R - G) > 40) & ((B - G) > 40)
    mag = mag | kill
    rgba = np.dstack([rgb, np.full(rgb.shape[:2], 255, np.uint8)])
    rgba[mag, 3] = 0
    # despill kept edge pixels
    edge = ndimage.binary_dilation(mag, iterations=1) & ~mag
    er, eg, eb = (rgb[:, :, i].astype(int) for i in range(3))
    fix = edge & ((er > eg + 12) | (eb > eg + 12))
    er[fix] = np.minimum(er[fix], eg[fix] + 12)
    eb[fix] = np.minimum(eb[fix], eg[fix] + 12)
    rgba[:, :, 0][fix] = er[fix]
    rgba[:, :, 1][fix] = eg[fix]
    rgba[:, :, 2][fix] = eb[fix]
    return rgba

for name in ["terrain_magenta", "avant_plan_magenta"]:
    rgb = np.asarray(Image.open(os.path.join(BRUTS, name + ".png")).convert("RGB"))
    rgba = key_magenta(rgb)
    rgba = rgba[:, X0:X1]
    Image.fromarray(rgba).save(os.path.join(WORK, name.replace("_magenta", "_keyed") + ".png"))
    print(name, rgba.shape, "opaque=%.3f" % (rgba[:, :, 3] > 0).mean())
print("OK ->", WORK)
