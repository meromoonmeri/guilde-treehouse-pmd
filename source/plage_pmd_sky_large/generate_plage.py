#!/usr/bin/env python3
"""
Génération complète de la Plage PMD Sky Large (1152x432) en 10 calques max.
"""
import sys
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
ref_dir = REPO_ROOT / 'renders/references_54d3731/04_plage/jour'
raw_plage = Image.open(REPO_ROOT / 'renders/references_54d3731/bruts/04_plage.png').convert('RGBA')

# Target size
W, H = 1152, 432
print(f"Génération Plage Large {W}x{H}...")

# 1. Base references
ciel_ref = Image.open(ref_dir / '01_ciel.png')
sable_ref = Image.open(ref_dir / '05_sable_visible.png')
rochers_ref = Image.open(ref_dir / '06_rochers_arriere.png')
palmiers_ref = Image.open(ref_dir / '07_rochers_palmiers_avant.png')
mer_ref = Image.open(ref_dir / '08_mer_et_ecume_fixe.png')

print("Références chargées avec succès.")
