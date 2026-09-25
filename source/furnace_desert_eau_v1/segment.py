"""Segmentation de Furnace Desert (PMD Rescue Team, 456x336) en matières.

Classes : ciel, sable (sol), halo et siphon (cuvette centrale), cascades de sable, roches,
premier plan (roches/piliers du bas), ombres de contact sur le sable.
Couleur ET silhouette : les reflets khaki des roches ont la teinte du sable, donc les roches
sont définies par leurs contours sombres remplis, pas par la teinte seule.
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
from PIL import Image
from scipy import ndimage as nd

HERE = Path(__file__).resolve().parent
REFERENCE = HERE / 'references/furnace_desert_rt_original_456x336.png'


def hsv(a):
    f = a[..., :3].astype(float) / 255
    r, g, b = f[..., 0], f[..., 1], f[..., 2]
    mx, mn = f.max(-1), f.min(-1)
    d = np.maximum(mx - mn, 1e-6)
    h = np.where(mx == r, ((g - b) / d) % 6, np.where(mx == g, (b - r) / d + 2, (r - g) / d + 4)) * 60
    s = np.where(mx > 0, (mx - mn) / np.maximum(mx, 1e-6), 0)
    return h, s, mx


def segment(path=REFERENCE):
    a = np.array(Image.open(path).convert('RGBA'))
    H, W = a.shape[:2]
    h, s, v = hsv(a)
    blue = (h > 180) & (h < 245) & (s > 0.12)
    warm = (h >= 30) & (h <= 66)
    sandlike = warm & (v >= 0.66) & (s >= 0.12)
    dark = (v < 0.62) | ((s < 0.30) & ~blue & ~sandlike)
    # remplissage des silhouettes sombres, bordure répliquée (évite l'érosion des bords d'image)
    pad = 6
    dk = np.pad(dark, pad, mode='edge')
    rock = nd.binary_fill_holes(nd.binary_closing(dk, iterations=2))[pad:-pad, pad:-pad]
    sky = blue & ~rock
    lab, n = nd.label(sky)
    if n:
        keep = [i + 1 for i, sl in enumerate(nd.find_objects(lab)) if sl[0].start < 60]
        sky = np.isin(lab, keep)
    # nuages / lueur d'horizon clairs attachés au ciel
    light = (v > 0.88) & (s < 0.14) & ~rock
    sky = nd.binary_propagation(sky, mask=sky | (light & (np.arange(H)[:, None] < 110)))
    sand_all = sandlike & ~rock & ~sky
    lab, n = nd.label(sand_all)
    objs = nd.find_objects(lab)
    sizes = nd.sum(sand_all, lab, range(1, n + 1))
    main = int(np.argmax(sizes)) + 1
    falls = np.zeros((H, W), bool)
    sand = lab == main
    for i, sl in enumerate(objs):
        k = i + 1
        if k == main:
            continue
        hgt, wid = sl[0].stop - sl[0].start, sl[1].stop - sl[1].start
        if sl[0].start < 8 and hgt > 60 and wid < 60:
            falls |= lab == k                      # cascades de sable (colonnes hautes en haut)
        elif nd.binary_dilation(lab == k, iterations=2)[sand].any():
            sand |= lab == k                       # poches collées au sol
        else:
            rock |= lab == k                       # reflets khaki isolés = roche
    # halo clair et cuvette du siphon (anneaux entourés par le halo)
    halo_col = sand & (s < 0.46) & (v > 0.97)
    lab, n = nd.label(nd.binary_closing(halo_col, iterations=2))
    cy, cx = H * 0.57, W * 0.5
    best, bestd = None, 1e9
    for i, sl in enumerate(nd.find_objects(lab)):
        yy, xx = (sl[0].start + sl[0].stop) / 2, (sl[1].start + sl[1].stop) / 2
        area = (lab[sl] == i + 1).sum()
        d = abs(yy - cy) + abs(xx - cx)
        if area > 800 and d < bestd:
            best, bestd = i + 1, d
    halo_blob = lab == best
    pit = nd.binary_fill_holes(halo_blob) & ~halo_blob & sand
    pit = nd.binary_opening(pit, iterations=1)
    pit_lab, pn = nd.label(pit)
    if pn > 1:
        sizes = nd.sum(pit, pit_lab, range(1, pn + 1))
        pit = pit_lab == (int(np.argmax(sizes)) + 1)
    pit = nd.binary_fill_holes(pit)
    halo = nd.binary_fill_holes(halo_blob | pit) & ~pit & sand
    # premier plan : roches touchant le bas de l'image
    lab, n = nd.label(rock)
    fg = np.zeros((H, W), bool)
    for i, sl in enumerate(nd.find_objects(lab)):
        if sl[0].stop >= H - 1 and sl[0].start > H * 0.6:
            fg |= lab == i + 1
    # ombres de contact : sable sombre proche des roches (hors cascades)
    dist = nd.distance_transform_edt(~rock)
    darker = sand & (v < 0.93) & (dist <= 12)
    other = ~(sky | sand | falls | rock)
    return {
        'rgba': a, 'sky': sky, 'sand': sand, 'falls': falls, 'rock': rock & ~fg, 'foreground': fg,
        'pit': pit, 'halo': halo, 'shadow': darker, 'unclassified': other, 'hsv': (h, s, v),
    }


if __name__ == '__main__':
    seg = segment()
    a = seg['rgba']
    H, W = a.shape[:2]
    vis = np.zeros((H, W, 3), np.uint8)
    colors = {'sky': (60, 120, 255), 'sand': (250, 220, 80), 'falls': (255, 150, 40), 'rock': (90, 70, 50),
              'foreground': (40, 30, 20), 'halo': (255, 250, 200), 'pit': (255, 60, 60), 'shadow': (170, 120, 40),
              'unclassified': (255, 0, 255)}
    for k in ['sky', 'sand', 'falls', 'rock', 'foreground', 'halo', 'pit', 'shadow', 'unclassified']:
        vis[seg[k]] = colors[k]
    for k in colors:
        print(k, int(seg[k].sum()))
    src = Image.fromarray(a).convert('RGB').resize((W * 2, H * 2), Image.NEAREST)
    out = Image.new('RGB', (W * 4 + 10, H * 2))
    out.paste(src, (0, 0))
    out.paste(Image.fromarray(vis).resize((W * 2, H * 2), Image.NEAREST), (W * 2 + 10, 0))
    out.save('/tmp/v_seg2.png')
