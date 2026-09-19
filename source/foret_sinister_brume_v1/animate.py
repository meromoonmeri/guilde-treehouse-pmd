#!/usr/bin/env python3
"""Animation V1 — brume derivante + lucioles (overlay transparent).

Src brume : bruts/brume_magenta.png (generee). Magenta -> alpha par inondation.
Lucioles : procedeurales (gouttes additives, drift Lissajous, clignotement).
48 frames x 100 ms = 4,8 s, boucle exacte (periodes divisant 48).
Sorties : overlay_XX.png, anim_overlay.webp, preview_scene.gif/webp (x0.5).
"""
import os
import numpy as np
from PIL import Image
from scipy import ndimage

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
REN = os.path.join(ROOT, "renders", "foret_sinister_brume_v1")
ANIM = os.path.join(REN, "anim")
os.makedirs(ANIM, exist_ok=True)

W, H = 848, 1264
N, DT = 48, 100

# ---------- brume sur noir : alpha depuis la luminance ----------
mist = np.asarray(Image.open(os.path.join(REN, "bruts", "brume_noir.png")).convert("RGB")).astype(float)
lum_m = mist.sum(axis=2) / 3.0
alpha = np.clip((lum_m - 6) * (255.0 / 120.0), 0, 255).astype(np.uint8)
ys, xs = np.where(alpha > 8)
y0, y1 = max(ys.min() - 4, 0), min(ys.max() + 5, mist.shape[0])
x0, x1 = max(xs.min() - 4, 0), min(xs.max() + 5, mist.shape[1])
band = np.zeros((y1 - y0, x1 - x0, 4), np.uint8)
band[:, :, :3] = mist[y0:y1, x0:x1].astype(np.uint8)
band[:, :, 3] = alpha[y0:y1, x0:x1]
band = ndimage.gaussian_filter(band.astype(float), sigma=(1.2, 1.2, 0)).astype(np.uint8)
Image.fromarray(band).save(os.path.join(ANIM, "mist_band.png"))
print("band:", band.shape, "alpha px:", int((band[:, :, 3] > 0).sum()))
BH, BW = band.shape[:2]

# ---------- lucioles deterministes ----------
rng = np.random.default_rng(5)
flies = []
for _ in range(54):
    flies.append({
        "x": float(rng.uniform(60, W - 60)), "y": float(rng.uniform(150, H - 60)),
        "ax": float(rng.uniform(8, 22)), "ay": float(rng.uniform(6, 16)),
        "px": int(rng.choice([48, 24, 16])), "py": int(rng.choice([48, 24])),
        "phx": float(rng.uniform(0, 6.283)), "phy": float(rng.uniform(0, 6.283)),
        "r": int(rng.choice([1, 2, 2])),
        "pb": int(rng.choice([48, 24, 16])), "phb": float(rng.uniform(0, 6.283)),
    })

def mist_dx(t, amp, period, phase):
    return amp * np.sin(2 * np.pi * t / period + phase)

def mist_alpha(t, period=24):
    return 0.82 + 0.18 * np.sin(2 * np.pi * t / period)

def paste_add(dst_rgb, dst_a, src, dx, dy, global_a):
    """Colle src (RGBA) sur dst avec alpha*global_a (over)."""
    h, w = src.shape[:2]
    x0, y0 = int(round(dx)), int(round(dy))
    cx0, cy0 = max(x0, 0), max(y0, 0)
    cx1, cy1 = min(x0 + w, W), min(y0 + h, H)
    if cx1 <= cx0 or cy1 <= cy0:
        return
    s = src[cy0 - y0:cy1 - y0, cx0 - x0:cx1 - x0].astype(float)
    a = (s[:, :, 3] / 255.0) * global_a
    d = dst_rgb[cy0:cy1, cx0:cx1].astype(float)
    da = dst_a[cy0:cy1, cx0:cx1].astype(float) / 255.0
    out_a = a + da * (1 - a)
    out_rgb = (s[:, :, :3] * a[:, :, None] + d * da[:, :, None] * (1 - a[:, :, None]))
    out_rgb = np.where(out_a[:, :, None] > 0, out_rgb / np.maximum(out_a[:, :, None], 1e-6), 0)
    dst_rgb[cy0:cy1, cx0:cx1] = out_rgb.astype(np.uint8)
    dst_a[cy0:cy1, cx0:cx1] = (out_a * 255).astype(np.uint8)

scene = np.asarray(Image.open(os.path.join(REN, "SinisterGenV1_composite.png")).convert("RGB"))
frames_overlay, frames_prev = [], []
for t in range(N):
    rgb = np.zeros((H, W, 3), np.uint8)
    alp = np.zeros((H, W), np.uint8)
    ma = mist_alpha(t) * 0.30
    xbase = (W - BW) // 2
    paste_add(rgb, alp, band, xbase + mist_dx(t, 30, 48, 0.0), 560, ma)
    paste_add(rgb, alp, band, xbase + mist_dx(t, 24, 48, 2.1), 950, ma * 0.65)
    ov = np.dstack([rgb, alp])
    # lucioles (additif ecrase sur overlay)
    for f in flies:
        fx = f["x"] + f["ax"] * np.sin(2 * np.pi * t / f["px"] + f["phx"])
        fy = f["y"] + f["ay"] * np.sin(2 * np.pi * t / f["py"] + f["phy"])
        bl = 0.5 + 0.5 * np.sin(2 * np.pi * t / f["pb"] + f["phb"])
        inten = 0.25 + 0.75 * bl ** 2
        ix, iy, r = int(round(fx)), int(round(fy)), f["r"]
        col = np.array([215, 255, 160], float)
        for dy in range(-r - 1, r + 2):
            for dx in range(-r - 1, r + 2):
                d2 = dx * dx + dy * dy
                px, pyy = ix + dx, iy + dy
                if not (0 <= px < W and 0 <= pyy < H):
                    continue
                if d2 <= r * r:
                    a = inten
                elif d2 <= (r + 1) ** 2:
                    a = inten * 0.35
                else:
                    continue
                old = ov[pyy, px].astype(float)
                oa = old[3] / 255.0
                na = a + oa * (1 - a)
                ncol = (col * a + old[:3] * oa * (1 - a)) / max(na, 1e-6)
                ov[pyy, px, :3] = ncol.astype(np.uint8)
                ov[pyy, px, 3] = int(na * 255)
    Image.fromarray(ov).save(os.path.join(ANIM, "overlay_%02d.png" % t))
    frames_overlay.append(Image.fromarray(ov))
    # preview composite x0.5
    a = (ov[:, :, 3:4].astype(float) / 255.0)
    comp = (ov[:, :, :3].astype(float) * a + scene.astype(float) * (1 - a)).astype(np.uint8)
    frames_prev.append(Image.fromarray(comp).resize((W // 2, H // 2), Image.BILINEAR))

frames_overlay[0].save(os.path.join(REN, "anim_overlay.webp"), save_all=True,
                       append_images=frames_overlay[1:], duration=DT, loop=0, lossless=False, quality=85, method=6)
frames_prev[0].save(os.path.join(REN, "preview_scene.gif"), save_all=True,
                    append_images=frames_prev[1:], duration=DT, loop=0)
frames_prev[0].save(os.path.join(REN, "preview_scene.webp"), save_all=True,
                    append_images=frames_prev[1:], duration=DT, loop=0, lossless=False, quality=85)
print("OK anim: %d frames" % N)
