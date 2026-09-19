#!/usr/bin/env python3
"""
Test de construction des 10 calques élargis (1152x432) avec mer animée 4 frames.
"""
import sys
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
ref_dir = REPO_ROOT / 'renders/references_54d3731/04_plage/jour'
W, H = 1152, 432

# Load 768x432 references
ciel_ref = Image.open(ref_dir / '01_ciel.png')
sable_ref = Image.open(ref_dir / '05_sable_visible.png')
rochers_ref = Image.open(ref_dir / '06_rochers_arriere.png')
palmiers_ref = Image.open(ref_dir / '07_rochers_palmiers_avant.png')
mer_ref = Image.open(ref_dir / '08_mer_et_ecume_fixe.png')

print("Dimensions de référence :", ciel_ref.size)
print("Dimensions cibles :", (W, H))

