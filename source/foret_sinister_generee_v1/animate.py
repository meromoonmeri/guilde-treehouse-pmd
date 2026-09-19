#!/usr/bin/env python3
"""Animation V1 — fremissement subtil des canopees (8 frames x 150 ms).

frame0 = brut exact ; boucle fermee frame8 == frame0 ; seuls les pixels
du calque 06_canpees bougent. Mouvement propose, pas un cycle officiel.
"""
import os
import numpy as np
from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
REN = os.path.join(ROOT, "renders", "foret_sinister_generee_v1")
CAL = os.path.join(REN, "calques")
ANI = os.path.join(REN, "animation")
os.makedirs(ANI, exist_ok=True)

brut = np.asarray(Image.open(os.path.join(REN, "bruts", "foret_sinister_complete.png")).convert("RGB")).astype(float)
H, W, _ = brut.shape
can = np.asarray(Image.open(os.path.join(CAL, "SinisterGenV1_06_canpees.png")))[:, :, 3] > 0
print("canopy px:", int(can.sum()))

NF, MS = 8, 150
yy, xx = np.mgrid[0:H, 0:W].astype(float)

def field(t):
    return (0.055 * np.sin(2 * np.pi * (xx / 424.0 + t / NF))
            + 0.035 * np.sin(2 * np.pi * (yy / 316.0 - t / 4.0) + 1.0))

f0 = field(0)
frames = []
for t in range(NF):
    d = field(t) - f0
    img = brut.copy()
    img[can] = np.clip(brut[can] * (1 + d[can][:, None]), 0, 255)
    fim = Image.fromarray(img.round().astype(np.uint8))
    fim.save(os.path.join(ANI, "frame_%02d.png" % t))
    frames.append(fim)

# cloture boucle : champ t=8 == champ t=0
assert np.allclose(field(NF) - f0, 0, atol=1e-9)
# frame0 exacte
assert (np.asarray(frames[0]).astype(int) != brut.astype(int)).sum() == 0
# seuls canopee bougent entre 0 et 4
moved = (np.asarray(frames[4]).astype(int) != np.asarray(frames[0]).astype(int)).any(axis=2)
assert (moved & (~can)).sum() == 0 and moved.sum() > 1000
print("frames OK, px bouges f4:", int(moved.sum()))

frames[0].save(os.path.join(REN, "SinisterGenV1_animation.webp"), save_all=True,
               append_images=frames[1:], duration=MS, loop=0, lossless=True)
print("webp lossless OK")
frames[0].save(os.path.join(REN, "SinisterGenV1_animation.gif"), save_all=True,
               append_images=frames[1:], duration=MS, loop=0)
print("gif OK (apercu 256 couleurs)")
