#!/usr/bin/env python3
"""
Plage Pokémon Mystery Dungeon Sky — Version Large Animée (10 Calques Max)
========================================================================
Conforme aux directives strictes de l'utilisateur :
- "layer plus large de la plage pmd sky" : format panoramique 1152 x 432 px
  (48 x 18 tuiles de 24 px PMDO / 144 x 54 tuiles de 8 px)
- "garder le layout original juste agrandir la plage"
- "avec la mer animée" : cycle complet de 4 frames (f1..f4) pour l'océan et l'écume
- "(tu dois faire en multicalque sur fondmajenta la méthode render canonique)"
- "faut que la map est 10 layer max : sable / chemin / cliff / roche / tree / mer / ciel etc"

Les 10 calques canoniques :
  01_ciel           : Dégradé ciel azur PMD, brume d'horizon, étoiles & lune la nuit
  02_cliff_arriere  : Falaises lointaines et promontoires côtiers sur l'horizon
  03_roche_arriere  : Monolithes et rochers marins émergeant des flots
  04_mer            : Surface océanique animée (f1..f4) avec houle et miroitements
  05_sable          : Vaste étendue de sable doré de la plage PMD (sol continu 100%)
  06_ecume_mer      : Déferlement et flux/reflux de l'écume blanche sur le sable (f1..f4)
  07_chemin         : Sentier battu de sable damé et coquillages traversant la plage
  08_cliff_plage    : Parois rocheuses et falaises côtières encadrant l'anse
  09_roche_plage    : Roches, galets et blocs côtiers posés sur le sable
  10_tree           : Palmiers tropicaux PMD (troncs galbés, noix de coco et canopée)
"""

import sys
import os
import math
import struct
import json
import zipfile
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
from pathlib import Path

# Paths
REPO_ROOT = Path(__file__).resolve().parents[2]
OUT_DIR = REPO_ROOT / 'renders/plage_pmd_sky_large'
PMDO_DIR = REPO_ROOT / 'sprites/plage_pmd_sky_pmdo'
BRUTS_DIR = REPO_ROOT / 'source/plage_pmd_sky_large/bruts'
SRC_DIR = REPO_ROOT / 'source/plage_pmd_sky_large'

for d in [OUT_DIR, PMDO_DIR, BRUTS_DIR, SRC_DIR]:
    d.mkdir(parents=True, exist_ok=True)

for sub in ['jour', 'magenta', 'nuit', 'nuit_magenta']:
    (OUT_DIR / sub).mkdir(parents=True, exist_ok=True)

# Abyss Night Filter
sys.path.insert(0, str(REPO_ROOT / 'source/cote_v4_abyss'))
from night import night

# Canvas Dimensions
W = 1152
H = 432
TILE_SIZE = 24
N_TILES_X = W // TILE_SIZE  # 48
N_TILES_Y = H // TILE_SIZE  # 18

print(f"=== Génération Plage PMD Sky Large ({W}x{H} px / {N_TILES_X}x{N_TILES_Y} tuiles 24px) ===")

# Reference files
ref_dir = REPO_ROOT / 'renders/references_54d3731/04_plage/jour'
raw_plage_path = REPO_ROOT / 'renders/references_54d3731/bruts/04_plage.png'
raw_img = Image.open(raw_plage_path).convert('RGBA')

# Chroma key raw image
raw_arr = np.array(raw_img)
r_raw, g_raw, b_raw = [raw_arr[:, :, i].astype(int) for i in range(3)]
is_mag_raw = (r_raw > 35) & (b_raw > 35) & (r_raw > g_raw * 1.8) & (b_raw > g_raw * 1.8)
raw_arr[is_mag_raw] = 0

print("Référence brute chargée et nettoyée.")
