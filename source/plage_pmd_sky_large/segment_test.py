#!/usr/bin/env python3
"""
Test d'extraction et de synthèse des 10 calques canoniques.
"""
import sys
import numpy as np
from PIL import Image
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
raw = Image.open(REPO_ROOT / 'renders/references_54d3731/bruts/04_plage.png').convert('RGBA')
arr_raw = np.array(raw)

# Chroma key raw
r, g, b, a = [arr_raw[:, :, i].astype(int) for i in range(4)]
is_mag = (r > 35) & (b > 35) & (r > g * 1.8) & (b > g * 1.8)
arr_raw[is_mag] = 0

print("Raw cleaned size:", raw.size)
print("Non-magenta pixels:", (~is_mag).sum())
