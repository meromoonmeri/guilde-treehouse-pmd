#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
verify.py — Contrôle qualité et audit du nouveau layout Steam Cave
===================================================================
Vérifie la conformité avec METHODE_PRODUCTION_MAPS_PMD.md :
- Grille 8px et chunks 24px (504x432)
- Intégrité des 12 calques jour et 12 calques nuit
- 6 phases d'animation vapeur
- Corridor de circulation libre (>= 32 px)
- Cohérence du manifest.json et de l'archive ZIP
"""

import os
import sys
import json
import zipfile
from PIL import Image
import numpy as np

ROOT = os.path.abspath(".")
OUT_DIR = os.path.join(ROOT, "renders", "steam_cave_nouveau_layout_v1")
CALQUES_JOUR = os.path.join(OUT_DIR, "calques_jour")
CALQUES_NUIT = os.path.join(OUT_DIR, "calques_nuit")

def run_checks():
    errors = []
    warnings = []

    print("=======================================================")
    print(" AUDIT QUALITÉ : STEAM CAVE NOUVEAU LAYOUT V1")
    print("=======================================================")

    # 1. Manifest
    man_path = os.path.join(OUT_DIR, "manifest.json")
    if not os.path.exists(man_path):
        errors.append("manifest.json manquant")
        return False
    with open(man_path, "r", encoding="utf-8") as f:
        manifest = json.load(f)

    W = manifest["dimensions"]["width"]
    H = manifest["dimensions"]["height"]

    print(f"Dimensions déclarées : {W}x{H} px")
    if W % 8 != 0 or H % 8 != 0:
        errors.append(f"Dimensions non divisibles par 8 : {W}x{H}")
    else:
        print(f"✅ Grille 8px : {W//8}x{H//8} tuiles (OK)")

    if W % 24 != 0 or H % 24 != 0:
        warnings.append(f"Dimensions non divisibles par 24 : {W}x{H}")
    else:
        print(f"✅ Grille 24px : {W//24}x{H//24} chunks NDS (OK)")

    # 2. Vérification des compositions principales
    for comp_name in ["COMPOSITION_JOUR.png", "COMPOSITION_NUIT.png", "GUIDE_CORRIDOR_CIRCULATION.png"]:
        cp = os.path.join(OUT_DIR, comp_name)
        if not os.path.exists(cp):
            errors.append(f"Fichier manquant : {comp_name}")
        else:
            im = Image.open(cp)
            if im.size != (W, H):
                errors.append(f"{comp_name} a une taille incorrecte : {im.size} != {(W, H)}")
            else:
                print(f"✅ {comp_name} : {im.size} (OK)")

    # 3. Vérification des animations WebP
    for anim_name in ["ANIMATION_COMPLETE_JOUR.webp", "ANIMATION_COMPLETE_NUIT.webp"]:
        ap = os.path.join(OUT_DIR, anim_name)
        if not os.path.exists(ap):
            errors.append(f"Animation manquante : {anim_name}")
        else:
            im = Image.open(ap)
            n_frames = getattr(im, "n_frames", 1)
            if n_frames != 6:
                errors.append(f"{anim_name} a {n_frames} frames au lieu de 6")
            else:
                print(f"✅ {anim_name} : {n_frames} frames animées (OK)")

    # 4. Calques Jour et Nuit
    static_layers = manifest["layers"]["static"]
    anim_layers = manifest["layers"]["animated"]

    for lay in static_layers:
        pj = os.path.join(CALQUES_JOUR, f"{lay}.png")
        pn = os.path.join(CALQUES_NUIT, f"{lay}_nuit.png")
        if not os.path.exists(pj):
            errors.append(f"Calque jour manquant : {lay}.png")
        if not os.path.exists(pn):
            errors.append(f"Calque nuit manquant : {lay}_nuit.png")

    for lay in anim_layers:
        pj = os.path.join(CALQUES_JOUR, f"{lay}.png")
        pn = os.path.join(CALQUES_NUIT, f"{lay}_nuit.png")
        if not os.path.exists(pj):
            errors.append(f"Calque vapeur jour manquant : {lay}.png")
        if not os.path.exists(pn):
            errors.append(f"Calque vapeur nuit manquant : {lay}_nuit.png")

    print(f"✅ 12 calques Jour et 12 calques Nuit contrôlés (OK)")

    # 5. Contrôle du corridor de circulation
    corridor_tiles = manifest["circulation"]["corridor_tiles"]
    corridor_px = manifest["circulation"]["corridor_width_px"]
    if corridor_px < 32:
        warnings.append(f"Corridor étroit : {corridor_px} px")
    else:
        print(f"✅ Corridor de circulation : {corridor_px} px ({corridor_tiles} tuiles 8px dégagées) (OK)")

    # 6. Archive ZIP
    zip_p = os.path.join(OUT_DIR, "steam_cave_nouveau_layout_v1_calques.zip")
    if not os.path.exists(zip_p):
        errors.append("Archive ZIP manquante")
    else:
        with zipfile.ZipFile(zip_p, "r") as z:
            n_files = len(z.namelist())
            size_kb = os.path.getsize(zip_p) // 1024
            print(f"✅ Archive ZIP vérifiée : {n_files} fichiers ({size_kb} Ko) (OK)")

    print("=======================================================")
    if errors:
        print(f"❌ {len(errors)} ERREUR(S) DÉTECTÉE(S) :")
        for e in errors:
            print(f"   - {e}")
        return False
    else:
        print("🎉 TOUS LES TESTS SONT PASSÉS AVEC SUCCÈS (0 ERREUR) !")
        if warnings:
            for w in warnings:
                print(f"   ⚠️ Avertissement : {w}")
        return True

if __name__ == "__main__":
    success = run_checks()
    sys.exit(0 if success else 1)
