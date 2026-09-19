#!/usr/bin/env python3
"""
Test de segmentation et génération des 10 calques de la Plage PMD Sky Large.
"""
from pathlib import Path
import numpy as np
from PIL import Image

REPO_ROOT = Path(__file__).resolve().parents[2]
raw_plage = Image.open(REPO_ROOT / 'renders/references_54d3731/bruts/04_plage.png').convert('RGBA')
ref_dir = REPO_ROOT / 'renders/references_54d3731/04_plage/jour'

print("Raw plage size:", raw_plage.size)
for p in sorted(ref_dir.glob('*.png')):
    im = Image.open(p)
    print(f"  Ref layer {p.name}: {im.size} {im.mode}")

