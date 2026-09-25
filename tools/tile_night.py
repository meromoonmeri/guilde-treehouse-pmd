#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
tools/tile_night.py — Filtre nocturne officiel New Era / Abyss (blob 438383f4).
Applique la transformation colorimétrique exacte sur les tuiles natives.
"""
import sys
import os
import numpy as np
from PIL import Image

def night(image):
    a = np.array(image.convert('RGBA'))
    rgb = a[:, :, :3].astype('float64')
    r, g, b = rgb[:, :, 0], rgb[:, :, 1], rgb[:, :, 2]
    gr = 0.299 * r + 0.587 * g + 0.114 * b
    lum = gr / 255.0
    k = 0.20 + 0.30 * lum
    sat = 0.95
    r2 = (r * sat + gr * (1 - sat)) * (k * 0.52)
    g2 = (g * sat + gr * (1 - sat)) * (k * 0.70)
    b2 = (b * sat + gr * (1 - sat)) * (k * 1.60) + 6 * lum
    out = np.stack([r2, g2, b2], axis=2).clip(0, 255).astype('uint8')
    mask = a[:, :, 3] > 0
    a[:, :, :3][mask] = out[mask]
    return Image.fromarray(a)

def grade(image, mode='nuit'):
    return night(image) if mode == 'nuit' else image.copy()

if __name__ == '__main__':
    if len(sys.argv) < 3:
        print("Usage: python3 tools/tile_night.py <input_img> <output_img>")
        sys.exit(1)
    in_p, out_p = sys.argv[1], sys.argv[2]
    im = Image.open(in_p)
    out_im = night(im)
    out_im.save(out_p)
    print(f"Filtre nuit Abyss appliqué : {out_p}")
