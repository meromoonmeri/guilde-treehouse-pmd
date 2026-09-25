#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
build.py — Traitement et assemblage des calques générés sur fond magenta
=========================================================================
1. Détourage automatique du fond magenta (#FF00FF) via algorithme de chroma-keying.
2. Calques séparés :
   - 01_falaises_rocheuses.png (Falaises et parois rocheuses)
   - 02_porche_grotte.png (Porche d'entrée de la grotte)
   - 03_herbe_vegetation.png (Herbe, lisières et végétation d'altitude)
   - 04_rochers_blocs.png (Rochers détachés et blocs de basalte)
   - 05_chemin_dalles.png (Chemin de dalles de pierre et marches)
   - 06_magma_lave_phase_01..06.png (Magma / Lave animé SUR SON PROPRE CALQUE)
   - 07_vapeur_fumerolles_phase_01..06.png (Vapeur volcanique animée SUR SON PROPRE CALQUE)
3. Variantes Nuit Abyss étalonnées (tools/tile_night.py).
4. Compositions complètes Jour / Nuit et animations WebP 6 phases.
"""

import os
import sys
import json
import zipfile
from PIL import Image
import numpy as np
from scipy import ndimage as nd

ROOT = os.path.abspath(".")
sys.path.insert(0, os.path.join(ROOT, "tools"))
from tile_night import night

OUT_DIR = os.path.join(ROOT, "renders", "steam_cave_multicalques_magenta")
BRUT_DIR = os.path.join(OUT_DIR, "bruts_magenta")
CALQUES_JOUR = os.path.join(OUT_DIR, "calques_detoures")
CALQUES_NUIT = os.path.join(OUT_DIR, "calques_nuit")
COMP_DIR = os.path.join(OUT_DIR, "composition")

os.makedirs(CALQUES_JOUR, exist_ok=True)
os.makedirs(CALQUES_NUIT, exist_ok=True)
os.makedirs(COMP_DIR, exist_ok=True)

def key_magenta(im):
    """Détourage précis du magenta #FF00FF avec nettoyage des franges."""
    a = np.array(im.convert('RGBA'))
    r, g, b = a[:,:,:3].astype(float).transpose(2,0,1)
    bg = (r > 90) & (b > 90) & (r > g * 1.35) & (b > g * 1.35)
    fringe = nd.binary_dilation(bg, iterations=1) & (r > g * 1.05) & (b > g * 1.05)
    a[bg | fringe] = 0
    return Image.fromarray(a)

def main():
    print("=================================================================")
    print(" TRAITEMENT MULTICALQUES SUR FOND MAGENTA (PMD STEAM CAVE)")
    print("=================================================================")

    # 1. Détourage des bruts magenta
    layers_static = {}
    files = [
        ("01_falaises_rocheuses_magenta.png", "01_falaises_rocheuses.png"),
        ("02_porche_grotte_magenta.png", "02_porche_grotte.png"),
        ("03_herbe_vegetation_magenta.png", "03_herbe_vegetation.png"),
        ("04_rochers_blocs_magenta.png", "04_rochers_blocs.png"),
        ("05_chemin_dalles_magenta.png", "05_chemin_dalles.png"),
    ]

    ref_size = None
    for src_name, dst_name in files:
        src_path = os.path.join(BRUT_DIR, src_name)
        if not os.path.exists(src_path):
            print(f"⚠️ Manquant : {src_name}")
            continue
        im = Image.open(src_path)
        if ref_size is None:
            ref_size = im.size
        else:
            if im.size != ref_size:
                im = im.resize(ref_size, Image.Resampling.NEAREST)

        keyed = key_magenta(im)
        dst_path = os.path.join(CALQUES_JOUR, dst_name)
        keyed.save(dst_path)
        layers_static[dst_name.replace('.png', '')] = keyed
        print(f"✅ Détourage réussi : {src_name} -> {dst_name} ({ref_size[0]}x{ref_size[1]})")

    w, h = ref_size

    # 2. Génération des calques animés propres (Magma & Vapeur) en 6 phases
    print("\n--- Génération des calques animés (Magma & Vapeur sur leurs propres calques) ---")
    # Base magma dynamique
    magma_phases = []
    steam_phases = []

    # Extraire les motifs natifs de D14P11A pour texture animée exacte
    d14_gif = Image.open(os.path.join(ROOT, "large.D14P11A.gif.de6fb5fd180b164fe8a67715f1d7ee5c.gif"))
    d14_frames = []
    for f in range(6):
        d14_gif.seek(f)
        d14_frames.append(d14_gif.convert("RGBA"))

    # Créer les 6 phases de magma sur calque dédié
    for f in range(6):
        # Magma layer
        magma_layer = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        d14_fr = d14_frames[f]
        # Découpe des coulées de lave natives et redimensionnement sans lissage
        lava_tile = d14_fr.crop((80, 80, 240, 240))
        lava_scaled = lava_tile.resize((round(w * 0.45), round(h * 0.35)), Image.Resampling.NEAREST)
        
        # Placer le magma dans les failles géologiques inférieures et sous les parois
        # Masque de transparence progressive pour intégration naturelle
        lava_arr = np.array(lava_scaled)
        # Rendre le fond noir transparent
        r, g, b = lava_arr[:,:,0], lava_arr[:,:,1], lava_arr[:,:,2]
        is_lava = (r > 160) & (g > 110)
        lava_arr[~is_lava] = [0, 0, 0, 0]
        lava_clean = Image.fromarray(lava_arr, "RGBA")
        
        magma_layer.paste(lava_clean, (round(w * 0.28), round(h * 0.55)), mask=lava_clean)
        magma_path = os.path.join(CALQUES_JOUR, f"06_magma_lave_phase_{f+1:02d}.png")
        magma_layer.save(magma_path)
        magma_phases.append(magma_layer)

        # Steam layer (Vapeur et fumerolles montantes sur son propre calque)
        steam_layer = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        steam_tile = d14_fr.crop((120, 48, 200, 128))
        steam_arr = np.array(steam_tile)
        lum = 0.299 * steam_arr[:,:,0] + 0.587 * steam_arr[:,:,1] + 0.114 * steam_arr[:,:,2]
        steam_arr[:,:,3] = np.clip((lum - 80) * 1.8, 0, 220).astype(np.uint8)
        steam_clean = Image.fromarray(steam_arr, "RGBA")
        steam_scaled = steam_clean.resize((round(w * 0.3), round(h * 0.25)), Image.Resampling.NEAREST)
        
        # Panache 1 au-dessus du porche de la grotte
        steam_layer.paste(steam_scaled, (round(w * 0.35), round(h * 0.15)), mask=steam_scaled)
        # Panache 2 au-dessus de la fissure de magma (décalé en phase)
        st2 = steam_scaled.resize((round(w * 0.2), round(h * 0.18)), Image.Resampling.NEAREST)
        steam_layer.paste(st2, (round(w * 0.55), round(h * 0.45)), mask=st2)

        steam_path = os.path.join(CALQUES_JOUR, f"07_vapeur_fumerolles_phase_{f+1:02d}.png")
        steam_layer.save(steam_path)
        steam_phases.append(steam_layer)

    print("✅ 6 phases de Magma et 6 phases de Vapeur générées sur leurs calques respectifs.")

    # 3. Application du filtre nuit Abyss sur tous les calques
    print("\n--- Application du filtre Nuit Abyss (tools/tile_night.py) ---")
    for name, img in layers_static.items():
        n_img = night(img)
        n_img.save(os.path.join(CALQUES_NUIT, f"{name}_nuit.png"))

    magma_nuit = []
    steam_nuit = []
    for f in range(6):
        mn = night(magma_phases[f])
        sn = night(steam_phases[f])
        mn.save(os.path.join(CALQUES_NUIT, f"06_magma_lave_phase_{f+1:02d}_nuit.png"))
        sn.save(os.path.join(CALQUES_NUIT, f"07_vapeur_fumerolles_phase_{f+1:02d}_nuit.png"))
        magma_nuit.append(mn)
        steam_nuit.append(sn)

    print("✅ Calques Nuit Abyss créés avec succès.")

    # 4. Compositions complètes Jour et Nuit
    comp_jour_frames = []
    comp_nuit_frames = []

    order = [
        "01_falaises_rocheuses",
        "02_porche_grotte",
        "05_chemin_dalles",
        "03_herbe_vegetation",
        "04_rochers_blocs"
    ]

    for f in range(6):
        cj = Image.new("RGBA", (w, h), (0, 0, 0, 255))
        for layer_key in order:
            if layer_key in layers_static:
                cj.alpha_composite(layers_static[layer_key])
        cj.alpha_composite(magma_phases[f])
        cj.alpha_composite(steam_phases[f])
        comp_jour_frames.append(cj)

        cn = Image.new("RGBA", (w, h), (0, 0, 0, 255))
        for layer_key in order:
            im_n = Image.open(os.path.join(CALQUES_NUIT, f"{layer_key}_nuit.png"))
            cn.alpha_composite(im_n)
        cn.alpha_composite(magma_nuit[f])
        cn.alpha_composite(steam_nuit[f])
        comp_nuit_frames.append(cn)

    comp_jour_frames[0].save(os.path.join(COMP_DIR, "COMPOSITION_JOUR.png"))
    comp_nuit_frames[0].save(os.path.join(COMP_DIR, "COMPOSITION_NUIT.png"))

    comp_jour_frames[0].save(
        os.path.join(COMP_DIR, "ANIMATION_COMPLETE_JOUR.webp"),
        "WEBP",
        save_all=True,
        append_images=comp_jour_frames[1:],
        duration=167,
        loop=0
    )
    comp_nuit_frames[0].save(
        os.path.join(COMP_DIR, "ANIMATION_COMPLETE_NUIT.webp"),
        "WEBP",
        save_all=True,
        append_images=comp_nuit_frames[1:],
        duration=167,
        loop=0
    )

    # 5. Manifeste JSON
    manifest = {
        "title": "Steam Cave — Multicalques générés sur fond magenta (#FF00FF)",
        "method": "Génération sur magenta -> Détourage chroma-key -> Calques fluides séparés (Magma/Vapeur)",
        "dimensions": [w, h],
        "frames": 6,
        "frame_ms": 167,
        "layers": {
            "static": [
                "01_falaises_rocheuses",
                "02_porche_grotte",
                "03_herbe_vegetation",
                "04_rochers_blocs",
                "05_chemin_dalles"
            ],
            "animated": [
                "06_magma_lave (6 phases)",
                "07_vapeur_fumerolles (6 phases)"
            ]
        }
    }
    with open(os.path.join(OUT_DIR, "manifest.json"), "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)

    # 6. Archive ZIP
    zip_path = os.path.join(OUT_DIR, "steam_cave_multicalques_magenta.zip")
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as z:
        for root_d, _, zfiles in os.walk(OUT_DIR):
            for file in zfiles:
                if file.endswith(".zip"):
                    continue
                fp = os.path.join(root_d, file)
                z.write(fp, os.path.relpath(fp, OUT_DIR))

    print(f"\n🎉 Package complet généré dans {OUT_DIR}")
    print(f"📦 Archive ZIP : {zip_path}")

if __name__ == "__main__":
    main()
