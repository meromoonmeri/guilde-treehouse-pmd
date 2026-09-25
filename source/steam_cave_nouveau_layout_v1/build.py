#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
build.py — Génération du nouveau layout Steam Cave (Grotte Vapeur)
===================================================================
Conforme au protocole METHODE_PRODUCTION_MAPS_PMD.md :
1. Références natives : Steam_Cave_entrance_TDS.png (504x440) + large.D14P11A.gif (456x384, 6 frames).
2. Spécification : Entrée extérieure asymétrique, progression en baïonnette sud-ouest -> nord,
   terrasse intermédiaire avec bassin/fumerolles de vapeur animée en 6 phases natives,
   grotte enchâssée sous auvent rocheux proéminent au nord.
3. Dimensions : 504 x 432 px (63 x 54 tuiles 8px, 21 x 18 chunks 24px).
4. Calques séparés jour + nuit Abyss étalonnés.
"""

import os
import sys
import json
import zipfile
from PIL import Image, ImageDraw
import numpy as np

# Importer le filtre nuit officiel
sys.path.insert(0, os.path.abspath("tools"))
from tile_night import night

ROOT = os.path.abspath(".")
OUT_DIR = os.path.join(ROOT, "renders", "steam_cave_nouveau_layout_v1")
CALQUES_JOUR = os.path.join(OUT_DIR, "calques_jour")
CALQUES_NUIT = os.path.join(OUT_DIR, "calques_nuit")
SPRITES_DIR = os.path.join(OUT_DIR, "sprites")

os.makedirs(CALQUES_JOUR, exist_ok=True)
os.makedirs(CALQUES_NUIT, exist_ok=True)
os.makedirs(SPRITES_DIR, exist_ok=True)

W, H = 504, 432  # 63 x 54 tuiles 8px, 21 x 18 chunks 24px

def load_sources():
    ref_ent_path = os.path.join(ROOT, "Steam_Cave_entrance_TDS.png")
    ref_gif_path = os.path.join(ROOT, "large.D14P11A.gif.de6fb5fd180b164fe8a67715f1d7ee5c.gif")

    if not os.path.exists(ref_ent_path):
        raise FileNotFoundError(f"Référence manquante : {ref_ent_path}")
    if not os.path.exists(ref_gif_path):
        raise FileNotFoundError(f"Référence manquante : {ref_gif_path}")

    im_ent = Image.open(ref_ent_path).convert("RGBA")
    im_gif = Image.open(ref_gif_path)
    gif_frames = []
    for f in range(im_gif.n_frames):
        im_gif.seek(f)
        gif_frames.append(im_gif.convert("RGBA"))

    return im_ent, gif_frames

def build_layout():
    im_ent, gif_frames = load_sources()
    ent_w, ent_h = im_ent.size  # 504 x 440

    # ---------------------------------------------------------
    # ÉTAPE 1 : EXTRACTION DES MODULES NATIFS DE STEAM CAVE
    # ---------------------------------------------------------
    # Grotte originale : X=216..288, Y=96..160 (72 x 64 px)
    cave_mouth = im_ent.crop((216, 96, 288, 160))
    cave_mouth.save(os.path.join(SPRITES_DIR, "porche_grotte_natif.png"))

    # Falaise supérieure gauche (Y=0..120, X=0..200)
    cliff_top_left = im_ent.crop((0, 0, 200, 120))
    # Falaise supérieure droite (Y=0..120, X=304..504)
    cliff_top_right = im_ent.crop((304, 0, 504, 120))

    # Paroi massive ouest (X=0..168, Y=120..384)
    cliff_west_wall = im_ent.crop((0, 120, 168, 384))
    # Paroi est (X=336..504, Y=120..384)
    cliff_east_wall = im_ent.crop((336, 120, 504, 384))

    # Sol herbeux / basalte (X=168..336, Y=240..432)
    ground_base = im_ent.crop((168, 240, 336, 432))
    # Sentier et marches (X=200..304, Y=200..320)
    path_stone = im_ent.crop((200, 200, 304, 320))

    # ---------------------------------------------------------
    # ÉTAPE 2 : EXTRACTION DE LA VAPEUR ANIMÉE (6 PHASES)
    # ---------------------------------------------------------
    # D14P11A possède des évents de vapeur active dans la zone Y=48..128, X=120..200 (80 x 80 px)
    steam_frames = []
    for f_idx, fr in enumerate(gif_frames):
        # Découpe d'une zone de vapeur riche
        steam_crop = fr.crop((120, 48, 200, 128))
        # Rendre transparent le fond noir ou rocheux statique en comparant les différences
        steam_frames.append(steam_crop)

    # Création du masque de vapeur animé (différence entre frames)
    arr_frames = [np.array(sf) for sf in steam_frames]
    diff_steam = np.zeros(arr_frames[0].shape[:2], dtype=bool)
    for f in range(1, len(arr_frames)):
        diff_steam |= np.any(arr_frames[f] != arr_frames[0], axis=-1)

    isolated_steam_frames = []
    for f in range(len(arr_frames)):
        s_arr = np.zeros_like(arr_frames[f])
        s_arr[diff_steam] = arr_frames[f][diff_steam]
        # Adoucir l'alpha pour intégration naturelle
        lum = 0.299*s_arr[:,:,0] + 0.587*s_arr[:,:,1] + 0.114*s_arr[:,:,2]
        s_arr[:,:,3] = np.clip(lum * 1.4, 0, 255).astype(np.uint8)
        s_im = Image.fromarray(s_arr, "RGBA")
        isolated_steam_frames.append(s_im)
        s_im.save(os.path.join(SPRITES_DIR, f"vapeur_fumerolle_phase_{f+1:02d}.png"))

    # ---------------------------------------------------------
    # ÉTAPE 3 : ASSEMBLAGE DU NOUVEAU LAYOUT EN CALQUES SÉPARÉS
    # ---------------------------------------------------------
    # Canvas 504 x 432 (divisible par 8 et 24)

    # Calque 1 : Arrière-plan & Hautes Falaises (Y: 0..120)
    l1_arriere = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    # Poser les falaises hautes de gauche et droite
    l1_arriere.paste(cliff_top_left, (0, 0))
    # Remplir le massif nord supérieur
    l1_arriere.paste(cliff_top_right, (304, 0))
    # Texture de roche de liaison centrale en haut
    top_bridge = im_ent.crop((120, 0, 224, 96))
    l1_arriere.paste(top_bridge, (200, 0))
    top_bridge_2 = im_ent.crop((280, 0, 384, 96))
    l1_arriere.paste(top_bridge_2, (204, 0))

    # Calque 2 : Sol complet et terrasses volcaniques reconstituées
    l2_sol = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    # Carrelage de base avec le sol natif répété proprement
    for y in range(0, H, 96):
        for x in range(0, W, 112):
            ground_tile = im_ent.crop((192, 280, 304, 376))
            l2_sol.paste(ground_tile, (x, y))

    # Calque 3 : Parois rocheuses et reliefs étagés (nouvelle géométrie organique)
    l3_parois = Image.new("RGBA", (W, H), (0, 0, 0, 0))

    # 1. Flanc Ouest plus dense et escarpé (crée la gorge d'arrivée)
    l3_parois.paste(cliff_west_wall, (0, 96))
    # Deuxième niveau de relief ouest avançant vers le centre
    west_ledge = im_ent.crop((40, 160, 160, 320))
    l3_parois.paste(west_ledge, (32, 180))

    # 2. Promontoire et falaise Est (belvédère)
    l3_parois.paste(cliff_east_wall, (336, 120))
    # Décrochement du belvédère est à pic sur le vide
    east_ledge = im_ent.crop((352, 200, 480, 350))
    l3_parois.paste(east_ledge, (376, 216))

    # 3. Terrasses intermédiaires au nord (autour de l'entrée)
    north_terrace = im_ent.crop((144, 80, 360, 144))
    l3_parois.paste(north_terrace, (168, 72))

    # Calque 4 : Porche d'entrée de la grotte (décalé à X=288, Y=80)
    # Dans le layout original c'est à X=216, Y=96. Ici décalé à X=288, Y=80 (nord-centre)
    l4_porche = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    cave_x = 288
    cave_y = 72
    l4_porche.paste(cave_mouth, (cave_x, cave_y))
    # Surplomb / auvent rocheux protecteur au-dessus du porche
    overhang = im_ent.crop((208, 80, 296, 112))
    l4_porche.paste(overhang, (cave_x - 8, cave_y - 16))

    # Calque 5 : Sentier en dalles volcaniques et marches (progression en baïonnette)
    l5_chemin = Image.new("RGBA", (W, H), (0, 0, 0, 0))

    # Segment 1 : Entrée au Sud-Ouest (X=96..176, Y=336..432)
    path_seg1 = im_ent.crop((208, 304, 288, 400))
    l5_chemin.paste(path_seg1, (96, 336))

    # Segment 2 : Biais vers le centre-est (X=160..280, Y=240..336)
    path_seg2 = im_ent.crop((208, 224, 296, 320))
    l5_chemin.paste(path_seg2, (176, 248))

    # Segment 3 : Rampe montante vers la terrasse du porche (X=272..352, Y=144..248)
    path_seg3 = im_ent.crop((216, 152, 288, 256))
    l5_chemin.paste(path_seg3, (280, 136))

    # Marches d'accès au porche de la grotte
    steps = im_ent.crop((232, 144, 272, 160))
    l5_chemin.paste(steps, (cave_x + 16, cave_y + 60))

    # Calque 6 : Bassin hydrothermal / Fumerolles de soufre (X=368..464, Y=208..288)
    l6_fumerolles = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    # Bassin rocheux extrait de D14P11A
    sulfur_basin = gif_frames[0].crop((120, 100, 208, 172))
    l6_fumerolles.paste(sulfur_basin, (368, 208))

    # Petit évent secondaire sur la gauche (X=112, Y=200)
    small_vent = gif_frames[0].crop((140, 110, 180, 150))
    l6_fumerolles.paste(small_vent, (112, 192))

    # Calque 7 : Volutes de vapeur animées (6 phases)
    # Positionnées sur le bassin hydrothermal (X=368, Y=168) et l'évent secondaire (X=104, Y=152)
    l7_vapeur_phases = []
    for f in range(6):
        l7 = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        st = isolated_steam_frames[f]
        # Grande fumerolle au-dessus du bassin est
        l7.paste(st, (376, 160), mask=st)
        # Petite fumerolle au-dessus de l'évent ouest (légèrement décalée en phase)
        st_small = isolated_steam_frames[(f + 2) % 6].resize((48, 48), Image.Resampling.NEAREST)
        l7.paste(st_small, (108, 160), mask=st_small)
        l7_vapeur_phases.append(l7)

    # ---------------------------------------------------------
    # ÉTAPE 4 : SAUVEGARDE DES CALQUES JOUR
    # ---------------------------------------------------------
    layers_dict = [
        ("01_falaises_arriere_plan", l1_arriere),
        ("02_sol_terrasses_volcaniques", l2_sol),
        ("03_parois_falaises", l3_parois),
        ("04_porche_grotte", l4_porche),
        ("05_chemins_et_dalles", l5_chemin),
        ("06_bassin_fumerolles", l6_fumerolles),
    ]

    for name, img in layers_dict:
        img.save(os.path.join(CALQUES_JOUR, f"{name}.png"), "PNG")

    for f_idx, v_layer in enumerate(l7_vapeur_phases):
        v_layer.save(os.path.join(CALQUES_JOUR, f"07_vapeur_phase_{f_idx+1:02d}.png"), "PNG")

    # ---------------------------------------------------------
    # ÉTAPE 5 : VARIANTES NUIT ABYSS (CALQUES ET COMPOSITIONS)
    # ---------------------------------------------------------
    print("Application du filtre nuit Abyss officiel sur les calques...")
    for name, img in layers_dict:
        night_img = night(img)
        night_img.save(os.path.join(CALQUES_NUIT, f"{name}_nuit.png"), "PNG")

    l7_vapeur_phases_nuit = []
    for f_idx, v_layer in enumerate(l7_vapeur_phases):
        v_nuit = night(v_layer)
        v_nuit.save(os.path.join(CALQUES_NUIT, f"07_vapeur_phase_{f_idx+1:02d}_nuit.png"), "PNG")
        l7_vapeur_phases_nuit.append(v_nuit)

    # ---------------------------------------------------------
    # ÉTAPE 6 : COMPOSITIONS GLOBALES JOUR & NUIT
    # ---------------------------------------------------------
    comp_jour_frames = []
    comp_nuit_frames = []

    for f in range(6):
        # Base statique combinée
        cj = Image.new("RGBA", (W, H), (0, 0, 0, 255))
        for _, lim in layers_dict:
            cj.alpha_composite(lim)
        cj.alpha_composite(l7_vapeur_phases[f])
        comp_jour_frames.append(cj)

        cn = Image.new("RGBA", (W, H), (0, 0, 0, 255))
        for name, _ in layers_dict:
            lim_n = Image.open(os.path.join(CALQUES_NUIT, f"{name}_nuit.png"))
            cn.alpha_composite(lim_n)
        cn.alpha_composite(l7_vapeur_phases_nuit[f])
        comp_nuit_frames.append(cn)

    # Image représentative initiale
    comp_jour_frames[0].save(os.path.join(OUT_DIR, "COMPOSITION_JOUR.png"), "PNG")
    comp_nuit_frames[0].save(os.path.join(OUT_DIR, "COMPOSITION_NUIT.png"), "PNG")

    # Animation complète WebP (6 frames, 166.7 ms par frame = 1000 ms le cycle complet)
    comp_jour_frames[0].save(
        os.path.join(OUT_DIR, "ANIMATION_COMPLETE_JOUR.webp"),
        "WEBP",
        save_all=True,
        append_images=comp_jour_frames[1:],
        duration=167,
        loop=0
    )
    comp_nuit_frames[0].save(
        os.path.join(OUT_DIR, "ANIMATION_COMPLETE_NUIT.webp"),
        "WEBP",
        save_all=True,
        append_images=comp_nuit_frames[1:],
        duration=167,
        loop=0
    )

    # ---------------------------------------------------------
    # ÉTAPE 7 : GUIDE DE CORRIDOR DE CIRCULATION (32px / 4 tuiles)
    # ---------------------------------------------------------
    corridor_img = comp_jour_frames[0].copy()
    draw = ImageDraw.Draw(corridor_img)
    # Trajectoire : (136, 432) -> (136, 360) -> (232, 280) -> (324, 180) -> (324, 110)
    waypoints = [(136, 432), (136, 360), (232, 280), (324, 180), (324, 110)]
    for i in range(len(waypoints) - 1):
        draw.line([waypoints[i], waypoints[i+1]], fill=(0, 255, 200, 220), width=32)
    for wp in waypoints:
        draw.ellipse((wp[0]-16, wp[1]-16, wp[0]+16, wp[1]+16), fill=(0, 255, 200, 255), outline=(255, 255, 255, 255))
    corridor_img.save(os.path.join(OUT_DIR, "GUIDE_CORRIDOR_CIRCULATION.png"), "PNG")

    # ---------------------------------------------------------
    # ÉTAPE 8 : MANIFEST JSON
    # ---------------------------------------------------------
    manifest = {
        "zone": "steam_cave_entree_v1",
        "title": "Steam Cave — Nouveau layout d'entrée asymétrique & fumerolles",
        "dimensions": {
            "width": W,
            "height": H,
            "tiles_8px": [W // 8, H // 8],
            "chunks_24px": [W // 24, H // 24]
        },
        "animation": {
            "frames": 6,
            "frame_ms": 167,
            "cycle_ms": 1000,
            "pmdo_framelength": 10
        },
        "references": {
            "primary": "Steam_Cave_entrance_TDS.png (504x440)",
            "animation_source": "large.D14P11A.gif (456x384, 6 frames)",
            "color_filter_night": "tools/tile_night.py (Abyss New Era blob 438383f4)"
        },
        "layers": {
            "static": [
                "01_falaises_arriere_plan",
                "02_sol_terrasses_volcaniques",
                "03_parois_falaises",
                "04_porche_grotte",
                "05_chemins_et_dalles",
                "06_bassin_fumerolles"
            ],
            "animated": [
                f"07_vapeur_phase_{f+1:02d}" for f in range(6)
            ]
        },
        "circulation": {
            "entry_point": [136, 432],
            "cave_mouth": [324, 110],
            "corridor_width_px": 32,
            "corridor_tiles": 4
        }
    }

    with open(os.path.join(OUT_DIR, "manifest.json"), "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2, ensure_ascii=False)

    # ---------------------------------------------------------
    # ÉTAPE 9 : PAQUET ZIP D'EXPORT COMPLET
    # ---------------------------------------------------------
    zip_path = os.path.join(OUT_DIR, "steam_cave_nouveau_layout_v1_calques.zip")
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as z:
        for root_d, _, files in os.walk(OUT_DIR):
            for file in files:
                if file.endswith(".zip"):
                    continue
                fp = os.path.join(root_d, file)
                arcname = os.path.relpath(fp, OUT_DIR)
                z.write(fp, arcname)

    print(f"✅ Nouveau layout Steam Cave généré avec succès dans {OUT_DIR}")
    print(f"✅ Archive ZIP complète : {zip_path}")
    return manifest

if __name__ == "__main__":
    build_layout()
