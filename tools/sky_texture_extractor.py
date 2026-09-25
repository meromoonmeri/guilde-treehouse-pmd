#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
sky_texture_extractor.py — Outil d'audit et d'extraction de textures & animations PMD Sky.

Fonctionnalités :
1. Audit des images et GIFs NDS (dimensions, grille 8px/24px, nombre de frames, détection des tuiles animées).
2. Décomposition en calques : calque de fond statique + calques animés par phase (avec transparence).
3. Export de planches de tuiles 8x8 dédupliquées pour PMDO / Tiled.
4. Classification automatique du type de ressource d'après la nomenclature Chunsoft NDS :
   - DxxPyy : Donjon / Ground Map jouable
   - TxxPyy : Ville / Village / Hub
   - VxxPyy : Vignette / Fond cinématique
   - SxxPyy : Épisode spécial
   - PxxPyy : Panorama / Illustration plein écran
"""

import os
import sys
import json
import argparse
from PIL import Image
import numpy as np

def classify_sky_name(filename):
    """Détermine le type de ressource et son statut jouable d'après la convention NDS."""
    base = os.path.basename(filename).upper()
    # Nettoyage des préfixes éventuels (large.D14P11A.gif... -> D14P11A)
    for part in base.split('.'):
        if len(part) >= 6 and part[0] in ('D', 'T', 'V', 'S', 'P') and part[1:3].isdigit():
            base = part
            break

    prefix = base[0] if len(base) > 0 else '?'
    group_id = base[1:3] if len(base) >= 3 and base[1:3].isdigit() else '??'
    panel = base[3:6] if len(base) >= 6 else ''
    variant = base[6] if len(base) >= 7 else ''

    classification = {
        "ident": base,
        "prefix": prefix,
        "group_id": group_id,
        "panel": panel,
        "variant": variant,
        "type": "Inconnu",
        "playable_ground": False,
        "description": ""
    }

    if prefix == 'D':
        classification["type"] = "Dungeon Ground Map"
        classification["playable_ground"] = True
        classification["description"] = f"Carte de donjon / relais / entrée / salle de boss (Groupe {group_id})"
    elif prefix == 'T':
        classification["type"] = "Town / Hub Ground Map"
        classification["playable_ground"] = True
        classification["description"] = f"Lieu de village / carrefour / extérieur de guilde (Groupe {group_id})"
    elif prefix == 'S':
        classification["type"] = "Special Episode Ground Map"
        classification["playable_ground"] = True
        classification["description"] = f"Carte d'épisode spécial (Igglybuff, Grovyle, etc. Groupe {group_id})"
    elif prefix == 'V':
        classification["type"] = "Vignette / Cutscene BG"
        classification["playable_ground"] = False
        classification["description"] = f"Fond de cinématique / illustration scénarisée (Groupe {group_id})"
    elif prefix == 'P':
        classification["type"] = "Panorama / Picture"
        classification["playable_ground"] = False
        classification["description"] = f"Illustration plein écran / panorama de décor (Groupe {group_id})"
    elif 'TILESET' in base:
        classification["type"] = "Procedural Dungeon Tileset"
        classification["playable_ground"] = False
        classification["description"] = "Tileset d'étage procédural (DPC/DTEF pour donjons aléatoires)"

    return classification

def audit_file(filepath):
    """Analyse en profondeur une ressource graphique Sky."""
    if not os.path.exists(filepath):
        return {"error": f"Fichier non trouvé: {filepath}"}

    img = Image.open(filepath)
    n_frames = getattr(img, 'n_frames', 1)
    w, h = img.size

    div_8 = (w % 8 == 0) and (h % 8 == 0)
    div_24 = (w % 24 == 0) and (h % 24 == 0)
    cols_8, rows_8 = w // 8, h // 8
    cols_24, rows_24 = w // 24, h // 24

    frames_rgba = []
    for f in range(n_frames):
        img.seek(f)
        frames_rgba.append(np.array(img.convert('RGBA')))

    animated_cells = []
    static_cells = []
    
    if n_frames > 1:
        diff_any = np.zeros((h, w), dtype=bool)
        for f in range(1, n_frames):
            diff_f = np.any(frames_rgba[f] != frames_rgba[0], axis=-1)
            diff_any = diff_any | diff_f
        
        for cy in range(rows_8):
            for cx in range(cols_8):
                cell_diff = diff_any[cy*8:(cy+1)*8, cx*8:(cx+1)*8]
                if np.any(cell_diff):
                    animated_cells.append((cx, cy))
                else:
                    static_cells.append((cx, cy))
    else:
        static_cells = [(cx, cy) for cy in range(rows_8) for cx in range(cols_8)]

    meta = classify_sky_name(filepath)

    return {
        "file": os.path.basename(filepath),
        "path": filepath,
        "classification": meta,
        "dimensions": {"width": w, "height": h},
        "grid_8px": {"cols": cols_8, "rows": rows_8, "valid": div_8},
        "grid_24px_chunks": {"cols": cols_24, "rows": rows_24, "valid": div_24},
        "frames_count": n_frames,
        "is_animated": n_frames > 1,
        "total_8px_tiles": cols_8 * rows_8,
        "animated_8px_tiles": len(animated_cells),
        "static_8px_tiles": len(static_cells),
        "animated_ratio": round(len(animated_cells) / max(1, cols_8 * rows_8) * 100, 2),
        "animated_cells_coords": animated_cells[:50]  # aperçu des 50 premiers
    }

def extract_layers(filepath, out_dir):
    """
    Extrait les calques d'une image/GIF animé :
    - `01_base_statique.png` : Les zones statiques du décor.
    - `02_animation_phase_X.png` : Les zones animées isolées sur fond transparent pour chaque phase.
    """
    os.makedirs(out_dir, exist_ok=True)
    img = Image.open(filepath)
    n_frames = getattr(img, 'n_frames', 1)
    w, h = img.size
    cols_8, rows_8 = w // 8, h // 8

    frames_rgba = []
    for f in range(n_frames):
        img.seek(f)
        frames_rgba.append(np.array(img.convert('RGBA')))

    # Détection des tuiles animées
    animated_mask = np.zeros((h, w), dtype=bool)
    if n_frames > 1:
        diff_any = np.zeros((h, w), dtype=bool)
        for f in range(1, n_frames):
            diff_f = np.any(frames_rgba[f] != frames_rgba[0], axis=-1)
            diff_any = diff_any | diff_f
        
        for cy in range(rows_8):
            for cx in range(cols_8):
                if np.any(diff_any[cy*8:(cy+1)*8, cx*8:(cx+1)*8]):
                    animated_mask[cy*8:(cy+1)*8, cx*8:(cx+1)*8] = True

    # 1. Base statique : pixels là où animated_mask est False (ou image complète si 1 frame)
    base_arr = frames_rgba[0].copy()
    if n_frames > 1:
        # Remplacer les tuiles animées par de la transparence dans le calque statique pur
        base_arr[animated_mask] = [0, 0, 0, 0]
    base_img = Image.fromarray(base_arr, 'RGBA')
    base_img.save(os.path.join(out_dir, "01_sol_parois_statiques.png"), "PNG")

    # 2. Phases animées : pixels là où animated_mask est True, le reste transparent
    if n_frames > 1:
        for f in range(n_frames):
            anim_arr = np.zeros((h, w, 4), dtype=np.uint8)
            anim_arr[animated_mask] = frames_rgba[f][animated_mask]
            anim_img = Image.fromarray(anim_arr, 'RGBA')
            anim_img.save(os.path.join(out_dir, f"02_animation_phase_{f+1:02d}.png"), "PNG")

    # Manifest JSON d'extraction
    manifest = {
        "source": os.path.basename(filepath),
        "dimensions": [w, h],
        "frames": n_frames,
        "layers": {
            "static_base": "01_sol_parois_statiques.png",
            "animated_phases": [f"02_animation_phase_{f+1:02d}.png" for f in range(n_frames)] if n_frames > 1 else []
        }
    }
    with open(os.path.join(out_dir, "layers_manifest.json"), "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)

    return manifest

def main():
    parser = argparse.ArgumentParser(description="Audit et extracteur de textures/animations PMD Sky")
    parser.add_argument("path", help="Chemin vers le fichier ou dossier à auditer/extraire")
    parser.add_argument("--extract", help="Dossier de sortie pour extraire les calques", default=None)
    parser.add_argument("--json", action="store_true", help="Sortie au format JSON")
    args = parser.parse_args()

    if os.path.isfile(args.path):
        res = audit_file(args.path)
        if args.extract:
            extract_meta = extract_layers(args.path, args.extract)
            res["extraction"] = extract_meta
        if args.json:
            print(json.dumps(res, indent=2, ensure_ascii=False))
        else:
            c = res["classification"]
            print(f"\n=======================================================")
            print(f" AUDIT ASSET : {res['file']}")
            print(f"=======================================================")
            print(f"Type             : {c['type']}")
            print(f"Statut PMDO      : {'✅ MAP JOUABLE (Ground)' if c['playable_ground'] else 'ℹ️ FOND / CINÉMATIQUE (BG)'}")
            print(f"Description      : {c['description']}")
            print(f"Dimensions       : {res['dimensions']['width']}x{res['dimensions']['height']} px")
            print(f"Grille 8px       : {res['grid_8px']['cols']}x{res['grid_8px']['rows']} tuiles ({'OK' if res['grid_8px']['valid'] else 'ERREUR'})")
            print(f"Grille 24px NDS  : {res['grid_24px_chunks']['cols']}x{res['grid_24px_chunks']['rows']} chunks ({'OK' if res['grid_24px_chunks']['valid'] else 'NON'})")
            print(f"Animation        : {res['frames_count']} frame(s)")
            if res['is_animated']:
                print(f"Tuiles animées   : {res['animated_8px_tiles']} / {res['total_8px_tiles']} ({res['animated_ratio']}%)")
            if args.extract:
                print(f"Extraction       : Calques exportés vers {args.extract}")
            print(f"=======================================================\n")
    elif os.path.isdir(args.path):
        files = sorted(os.listdir(args.path))
        results = []
        for f in files:
            fp = os.path.join(args.path, f)
            if f.lower().endswith(('.gif', '.png', '.jpg', '.jpeg')):
                results.append(audit_file(fp))
        if args.json:
            print(json.dumps(results, indent=2, ensure_ascii=False))
        else:
            print(f"Audit de {len(results)} fichiers dans {args.path} terminé.")

if __name__ == "__main__":
    main()
