#!/usr/bin/env python3
"""
Génération des sprites et tilesets d'étangs / mares (ponds) de Métano Town / Treasure Town pour falaises.
- 5 modules d'étangs préfabriqués étalonnés pour falaises
- Découpage multicalques (Sol/Falaise, Eau animée 4 frames, Objets/Pierres de gué, Chutes)
- Tileset modulaire complet 8x8 px pour l'import PMDO ("PNG to Tileset")
- Formats natifs PMDO (.tile), Tiled (.tsj), PNG transparents et GIF animés
- Scène d'intégration sur falaise avec promontoire
- Aperçu interactif HTML autonome
"""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import json, io, struct, hashlib, math
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
OUT_SPRITES = ROOT / 'sprites/pond_metano_cliffs'
OUT_RENDERS = ROOT / 'renders/pond_metano_cliffs'
OUT_SPRITES.mkdir(parents=True, exist_ok=True)
OUT_RENDERS.mkdir(parents=True, exist_ok=True)

# -------------------------------------------------------------
# 1. Utilitaires techniques PMDO
# -------------------------------------------------------------
def straight(im):
    """PNG standard sans prémultiplication alpha pour éviter les halos sombres."""
    out = im.copy()
    data = []
    for r, g, b, a in im.getdata():
        if 0 < a < 255:
            data.append((round(r * 255 / a), round(g * 255 / a), round(b * 255 / a), a))
        else:
            data.append((r, g, b, a))
    out.putdata(data)
    return out

def write_native(im, path):
    """Écriture au format binaire .tile utilisé par PMDO (tuiles de 8x8 px)."""
    assert im.width % 8 == 0 and im.height % 8 == 0
    records = []
    payload = bytearray()
    seen = {}
    cols = im.width // 8
    rows = im.height // 8
    n = cols * rows
    for y in range(rows):
        for x in range(cols):
            tile = im.crop((x * 8, y * 8, x * 8 + 8, y * 8 + 8))
            key = tile.tobytes()
            if key not in seen:
                seen[key] = 8 + 16 * n + len(payload)
                b = io.BytesIO()
                tile.save(b, format='PNG')
                v = b.getvalue()
                payload.extend(struct.pack('<q', len(v)) + v)
            records.append(struct.pack('<IIQ', x, y, seen[key]))
    path.write_bytes(struct.pack('<II', 8, n) + b''.join(records) + payload)

def decode_native(path):
    """Lecture d'un fichier .tile en image RGBA."""
    raw = path.read_bytes()
    size, n = struct.unpack_from('<II', raw)
    assert size == 8
    records = [struct.unpack_from('<IIQ', raw, 8 + 16 * i) for i in range(n)]
    w = (max(x for x, y, o in records) + 1) * 8
    h = (max(y for x, y, o in records) + 1) * 8
    im = Image.new('RGBA', (w, h))
    for x, y, o in records:
        length = struct.unpack_from('<q', raw, o)[0]
        t = Image.open(io.BytesIO(raw[o + 8 : o + 8 + length])).convert('RGBA')
        im.paste(t, (x * 8, y * 8))
    return im

def write_tsj(name, im, anims, path):
    """Génération du format tileset Tiled JSON .tsj."""
    tsj_data = {
        'type': 'tileset',
        'version': '1.10',
        'name': name,
        'tilewidth': 8,
        'tileheight': 8,
        'columns': im.width // 8,
        'tilecount': (im.width // 8) * (im.height // 8),
        'margin': 0,
        'spacing': 0,
        'image': name + '.png',
        'imagewidth': im.width,
        'imageheight': im.height,
        'tiles': anims
    }
    path.write_text(json.dumps(tsj_data, indent=2))

def create_gif(frames, path, duration=167):
    """Création d'un GIF animé en boucle à 167 ms (10 ticks à 60Hz)."""
    p_frames = []
    for f in frames:
        alpha = f.split()[3]
        f_rgb = f.convert('RGB')
        f_p = f_rgb.convert('P', palette=Image.Palette.ADAPTIVE, colors=255)
        mask = Image.eval(alpha, lambda a: 255 if a <= 128 else 0)
        f_p.paste(255, mask)
        p_frames.append(f_p)
    p_frames[0].save(
        path,
        save_all=True,
        append_images=p_frames[1:],
        duration=duration,
        loop=0,
        transparency=255,
        disposal=2
    )

# -------------------------------------------------------------
# 2. Chargement des textures sources
# -------------------------------------------------------------
BASE_PNG = ROOT / 'source/amp_plains_fleurie_v1/references/Metano_Town_Base.png'
CLIFF_TILE = ROOT / 'source/falaises_metano/natifs/Metano_Town_Cliffs.tile'
CASC_PNG = ROOT / 'sprites/eau_metano/Cascades_Metano_Exact.png'
WATER_COMP_PNG = ROOT / 'sprites/eau_metano/Riviere_Metano_Compacte.png'
ALT_OBJ_PNG = ROOT / 'source/antre_harmonie_v3/references/Altere_Pond_Objects.png'

base_im = Image.open(BASE_PNG).convert('RGBA')
cliff_im = decode_native(CLIFF_TILE)
casc_im = Image.open(CASC_PNG).convert('RGBA')
water_comp_im = Image.open(WATER_COMP_PNG).convert('RGBA')
alt_obj_im = Image.open(ALT_OBJ_PNG).convert('RGBA')

# Patchs roche et herbe
patch_roche = cliff_im.crop((912, 472, 976, 520)) # 64x48
patch_rebord = cliff_im.crop((912, 448, 976, 472)) # 64x24
patch_pied = cliff_im.crop((912, 528, 976, 544)) # 64x16
patch_herbe = base_im.crop((0, 640, 64, 704)) # 64x64

# Stepping stones (pas japonais)
step0 = Image.open(ROOT / 'renders/antre_harmonie_v3/sprites/pas_japonais_natif_0.png').convert('RGBA')
step1 = Image.open(ROOT / 'renders/antre_harmonie_v3/sprites/pas_japonais_natif_1.png').convert('RGBA')
step2 = Image.open(ROOT / 'renders/antre_harmonie_v3/sprites/pas_japonais_natif_2.png').convert('RGBA')

# River rock / boulder
river_rock = base_im.crop((943, 298, 983, 322))
if river_rock.size != (40, 24):
    river_rock = alt_obj_im.crop((456, 104, 480, 127)).resize((40, 24), Image.Resampling.NEAREST)

def get_water_tile(tx, ty, phase):
    y_off = (ty + 61 * phase) * 8
    return water_comp_im.crop((tx * 8, y_off, tx * 8 + 8, y_off + 8))

CALM_WATER_TILES = [
    (1, 0), (8, 0), (10, 0), (14, 0),
    (0, 1), (3, 1), (5, 1), (9, 1),
    (2, 2), (6, 2), (11, 2), (13, 2)
]

def make_water_surface(w, h, phase, style='calm'):
    im = Image.new('RGBA', (w, h))
    cols = w // 8
    rows = h // 8
    for y in range(rows):
        for x in range(cols):
            idx = (x * 3 + y * 7 + (1 if style=='shallow' else 0)) % len(CALM_WATER_TILES)
            tx, ty = CALM_WATER_TILES[idx]
            tile = get_water_tile(tx, ty, phase)
            im.paste(tile, (x * 8, y * 8))
    return im

# -------------------------------------------------------------
# 3. Construction des 5 modules d'étangs de falaise (Prefabs)
# -------------------------------------------------------------

# --- MODULE 1 : Petite Mare de Promontoire (80x64 px) ---
def build_prefab_01():
    w, h = 80, 64
    d = OUT_SPRITES / '01_promontoire'
    d.mkdir(parents=True, exist_ok=True)
    
    sol = Image.new('RGBA', (w, h))
    for y in range(0, h, 64):
        for x in range(0, w, 64):
            sol.paste(patch_herbe, (x, y))
            
    sol.paste(base_im.crop((146*8, 60*8, 152*8, 61*8)), (16, 8))
    for y in range(16, 48, 8):
        sol.paste(base_im.crop((124*8, 55*8, 125*8, 56*8)), (8, y))
    for y in range(16, 48, 8):
        sol.paste(base_im.crop((129*8, 55*8, 130*8, 56*8)), (64, y))
    sol.paste(base_im.crop((146*8, 63*8, 152*8, 64*8)), (16, 44))
    
    rebord_clip = patch_rebord.crop((0, 8, 64, 24))
    sol.paste(rebord_clip, (0, 48))
    sol.paste(rebord_clip.crop((0, 0, 16, 16)), (64, 48))
    
    eau_frames = []
    water_mask = Image.new('L', (w, h), 0)
    draw_m = ImageDraw.Draw(water_mask)
    draw_m.ellipse([14, 14, 66, 46], fill=255)
    
    for p in range(4):
        surf = make_water_surface(w, h, p, style='calm')
        eau_f = Image.new('RGBA', (w, h), (0, 0, 0, 0))
        eau_f.paste(surf, (0, 0), water_mask)
        eau_frames.append(eau_f)
        
    objets = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    stone = step0.crop((8, 4, 24, 20))
    objets.paste(stone, (34, 26), stone)
    
    scenes = [Image.alpha_composite(Image.alpha_composite(sol, ef), objets) for ef in eau_frames]
    
    sol.save(d / 'METANO_CLIFF_POND_01_SOL.png')
    for p in range(4):
        eau_frames[p].save(d / f'METANO_CLIFF_POND_01_EAU_F{p+1}.png')
    objets.save(d / 'METANO_CLIFF_POND_01_OBJETS.png')
    scenes[0].save(d / 'METANO_CLIFF_POND_01_SCENE.png')
    create_gif(scenes, d / 'METANO_CLIFF_POND_01_ANIMATION.gif')
    
    write_native(scenes[0], d / 'METANO_CLIFF_POND_01_SCENE.tile')
    write_tsj('METANO_CLIFF_POND_01_SCENE', scenes[0], [], d / 'METANO_CLIFF_POND_01_SCENE.tsj')
    print("Prefab 01 Promontoire généré.")
    return scenes

# --- MODULE 2 : Étang d'Alcôve de Paroi (144x112 px) ---
def build_prefab_02():
    w, h = 144, 112
    d = OUT_SPRITES / '02_alcove'
    d.mkdir(parents=True, exist_ok=True)
    
    sol = Image.new('RGBA', (w, h))
    for y in range(0, h, 64):
        for x in range(0, w, 64):
            sol.paste(patch_herbe, (x, y))
            
    for x in range(0, w, 64):
        sol.paste(patch_rebord.crop((0, 0, min(64, w - x), 24)), (x, 0))
    for x in range(0, w, 64):
        sol.paste(patch_roche.crop((0, 0, min(64, w - x), 16)), (x, 16))
        
    for x in range(16, 128, 64):
        sub_rock = base_im.crop((888, 16, 888 + min(64, 128 - x), 24))
        sol.paste(sub_rock, (x, 32))
        
    for y in range(32, 72, 16):
        sol.paste(base_im.crop((848, 96, 864, 112)), (8, y))
    for y in range(32, 72, 16):
        sol.paste(base_im.crop((1096, 96, 1112, 112)), (120, y))
        
    for x in range(20, 124, 48):
        bw = min(48, 124 - x)
        sol.paste(base_im.crop((146*8, 63*8, 146*8 + bw, 64*8)), (x, 80))
        
    eau_frames = []
    water_mask = Image.new('L', (w, h), 0)
    draw_m = ImageDraw.Draw(water_mask)
    draw_m.rounded_rectangle([18, 34, 126, 82], radius=10, fill=255)
    
    for p in range(4):
        surf = make_water_surface(w, h, p, style='calm')
        eau_f = Image.new('RGBA', (w, h), (0, 0, 0, 0))
        eau_f.paste(surf, (0, 0), water_mask)
        eau_frames.append(eau_f)
        
    objets = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    objets.paste(step0, (36, 52), step0)
    objets.paste(step1, (64, 52), step1)
    objets.paste(step2, (92, 52), step2)
    
    rock_small = alt_obj_im.crop((456, 104, 472, 120))
    objets.paste(rock_small, (14, 68), rock_small)
    
    scenes = [Image.alpha_composite(Image.alpha_composite(sol, ef), objets) for ef in eau_frames]
    
    sol.save(d / 'METANO_CLIFF_POND_02_SOL_FALAISE.png')
    for p in range(4):
        eau_frames[p].save(d / f'METANO_CLIFF_POND_02_EAU_F{p+1}.png')
    objets.save(d / 'METANO_CLIFF_POND_02_OBJETS.png')
    scenes[0].save(d / 'METANO_CLIFF_POND_02_SCENE.png')
    create_gif(scenes, d / 'METANO_CLIFF_POND_02_ANIMATION.gif')
    
    write_native(scenes[0], d / 'METANO_CLIFF_POND_02_SCENE.tile')
    write_tsj('METANO_CLIFF_POND_02_SCENE', scenes[0], [], d / 'METANO_CLIFF_POND_02_SCENE.tsj')
    print("Prefab 02 Alcôve généré.")
    return scenes

# --- MODULE 3 : Grand Bassin avec Cascade & Déversoir (208x160 px) ---
def build_prefab_03():
    w, h = 208, 160
    d = OUT_SPRITES / '03_cascade'
    d.mkdir(parents=True, exist_ok=True)
    
    sol = Image.new('RGBA', (w, h))
    for y in range(0, h, 64):
        for x in range(0, w, 64):
            sol.paste(patch_herbe, (x, y))
            
    for x in range(0, 88, 64):
        sol.paste(patch_rebord.crop((0, 0, min(64, 88 - x), 24)), (x, 0))
        sol.paste(patch_roche.crop((0, 0, min(64, 88 - x), 16)), (x, 16))
    for x in range(120, w, 64):
        sol.paste(patch_rebord.crop((0, 0, min(64, w - x), 24)), (x, 0))
        sol.paste(patch_roche.crop((0, 0, min(64, w - x), 16)), (x, 16))
        
    sol.paste(patch_roche.crop((16, 0, 48, 36)), (88, 0))
    
    for y in range(36, 120, 24):
        sol.paste(base_im.crop((848, 96, 864, 120)), (8, y))
        sol.paste(base_im.crop((1096, 96, 1112, 120)), (184, y))
        
    for x in range(0, 88, 64):
        sol.paste(patch_rebord.crop((0, 0, min(64, 88 - x), 24)), (x, 128))
        sol.paste(patch_pied.crop((0, 0, min(64, 88 - x), 16)), (x, 144))
    for x in range(120, w, 64):
        sol.paste(patch_rebord.crop((0, 0, min(64, w - x), 24)), (x, 128))
        sol.paste(patch_pied.crop((0, 0, min(64, w - x), 16)), (x, 144))
        
    deversoir_sol = base_im.crop((920, 56, 952, 72))
    sol.paste(deversoir_sol, (88, 128))
    sol.paste(patch_roche.crop((16, 0, 48, 16)), (88, 144))
    
    eau_frames = []
    water_mask = Image.new('L', (w, h), 0)
    draw_m = ImageDraw.Draw(water_mask)
    draw_m.rounded_rectangle([18, 36, 190, 130], radius=14, fill=255)
    
    for p in range(4):
        surf = make_water_surface(w, h, p, style='calm')
        eau_f = Image.new('RGBA', (w, h), (0, 0, 0, 0))
        eau_f.paste(surf, (0, 0), water_mask)
        eau_frames.append(eau_f)
        
    cascade_frames = []
    for p in range(4):
        casc_layer = Image.new('RGBA', (w, h), (0, 0, 0, 0))
        c_src = casc_im.crop((p * 64, 0, (p + 1) * 64, 136))
        
        chute_amont = c_src.crop((16, 8, 48, 48))
        casc_layer.paste(chute_amont, (88, 12), chute_amont)
        
        ecume = c_src.crop((8, 104, 56, 122))
        casc_layer.paste(ecume, (80, 48), ecume)
        
        chute_aval = c_src.crop((16, 0, 48, 32))
        casc_layer.paste(chute_aval, (88, 128), chute_aval)
        
        cascade_frames.append(casc_layer)
        
    objets = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    objets.paste(river_rock, (44, 76), river_rock)
    objets.paste(step1, (134, 76), step1)
    objets.paste(step2, (158, 76), step2)
    rock_small = alt_obj_im.crop((456, 104, 472, 120))
    objets.paste(rock_small, (76, 116), rock_small)
    objets.paste(rock_small, (122, 116), rock_small)
    
    scenes = []
    for p in range(4):
        comp = Image.alpha_composite(sol, eau_frames[p])
        comp = Image.alpha_composite(comp, cascade_frames[p])
        comp = Image.alpha_composite(comp, objets)
        scenes.append(comp)
        
    sol.save(d / 'METANO_CLIFF_POND_03_SOL_FALAISE.png')
    for p in range(4):
        eau_frames[p].save(d / f'METANO_CLIFF_POND_03_EAU_F{p+1}.png')
        cascade_frames[p].save(d / f'METANO_CLIFF_POND_03_CASCADE_F{p+1}.png')
    objets.save(d / 'METANO_CLIFF_POND_03_OBJETS.png')
    scenes[0].save(d / 'METANO_CLIFF_POND_03_SCENE.png')
    create_gif(scenes, d / 'METANO_CLIFF_POND_03_ANIMATION.gif')
    
    write_native(scenes[0], d / 'METANO_CLIFF_POND_03_SCENE.tile')
    write_tsj('METANO_CLIFF_POND_03_SCENE', scenes[0], [], d / 'METANO_CLIFF_POND_03_SCENE.tsj')
    print("Prefab 03 Cascade généré.")
    return scenes

# --- MODULE 4 : Cuvette Rocheuse Pure (112x88 px) ---
def build_prefab_04():
    w, h = 112, 88
    d = OUT_SPRITES / '04_cuvette_rocheuse'
    d.mkdir(parents=True, exist_ok=True)
    
    sol = Image.new('RGBA', (w, h))
    for y in range(0, h, 48):
        for x in range(0, w, 64):
            sol.paste(patch_roche.crop((0, 0, min(64, w - x), min(48, h - y))), (x, y))
            
    for x in range(0, w, 64):
        sol.paste(patch_rebord.crop((0, 8, min(64, w - x), 24)), (x, 0))
    for x in range(0, w, 64):
        sol.paste(patch_pied.crop((0, 0, min(64, w - x), 16)), (x, 72))
        
    for x in range(16, 96, 64):
        sol.paste(base_im.crop((888, 16, 888 + min(64, 96 - x), 24)), (x, 16))
    for x in range(16, 96, 64):
        sol.paste(base_im.crop((912, 56, 912 + min(64, 96 - x), 64)), (x, 64))
    for y in range(24, 64, 16):
        sol.paste(base_im.crop((848, 96, 864, 112)), (8, y))
    for y in range(24, 64, 16):
        sol.paste(base_im.crop((1096, 96, 1112, 112)), (88, y))
        
    eau_frames = []
    water_mask = Image.new('L', (w, h), 0)
    draw_m = ImageDraw.Draw(water_mask)
    draw_m.rounded_rectangle([18, 20, 94, 68], radius=8, fill=255)
    
    for p in range(4):
        surf = make_water_surface(w, h, p, style='shallow')
        eau_f = Image.new('RGBA', (w, h), (0, 0, 0, 0))
        eau_f.paste(surf, (0, 0), water_mask)
        eau_frames.append(eau_f)
        
    objets = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    objets.paste(step1, (40, 36), step1)
    
    scenes = [Image.alpha_composite(Image.alpha_composite(sol, ef), objets) for ef in eau_frames]
    
    sol.save(d / 'METANO_CLIFF_POND_04_ROCHE.png')
    for p in range(4):
        eau_frames[p].save(d / f'METANO_CLIFF_POND_04_EAU_F{p+1}.png')
    objets.save(d / 'METANO_CLIFF_POND_04_OBJETS.png')
    scenes[0].save(d / 'METANO_CLIFF_POND_04_SCENE.png')
    create_gif(scenes, d / 'METANO_CLIFF_POND_04_ANIMATION.gif')
    
    write_native(scenes[0], d / 'METANO_CLIFF_POND_04_SCENE.tile')
    write_tsj('METANO_CLIFF_POND_04_SCENE', scenes[0], [], d / 'METANO_CLIFF_POND_04_SCENE.tsj')
    print("Prefab 04 Cuvette Rocheuse généré.")
    return scenes

# --- MODULE 5 : Déversoir & Chute de Falaise (64x96 px) ---
def build_prefab_05():
    w, h = 64, 96
    d = OUT_SPRITES / '05_deversoir'
    d.mkdir(parents=True, exist_ok=True)
    
    sol = Image.new('RGBA', (w, h))
    for y in range(0, h, 48):
        sol.paste(patch_roche.crop((0, 0, w, min(48, h - y))), (0, y))
        
    sol.paste(patch_rebord.crop((0, 0, 16, 24)), (0, 0))
    sol.paste(patch_rebord.crop((48, 0, 64, 24)), (48, 0))
    
    seuil = base_im.crop((920, 56, 952, 72))
    sol.paste(seuil, (16, 16))
    
    sol.paste(patch_pied.crop((0, 0, w, 16)), (0, 80))
    
    cascade_frames = []
    for p in range(4):
        casc_layer = Image.new('RGBA', (w, h), (0, 0, 0, 0))
        c_src = casc_im.crop((p * 64, 0, (p + 1) * 64, 136))
        
        lip = c_src.crop((16, 0, 48, 20))
        casc_layer.paste(lip, (16, 0), lip)
        
        chute = c_src.crop((16, 20, 48, 76))
        casc_layer.paste(chute, (16, 20), chute)
        
        foam = c_src.crop((8, 104, 56, 126))
        casc_layer.paste(foam, (8, 72), foam)
        
        cascade_frames.append(casc_layer)
        
    scenes = [Image.alpha_composite(sol, cf) for cf in cascade_frames]
    
    sol.save(d / 'METANO_CLIFF_POND_05_FALAISE.png')
    for p in range(4):
        cascade_frames[p].save(d / f'METANO_CLIFF_POND_05_CASCADE_F{p+1}.png')
    scenes[0].save(d / 'METANO_CLIFF_POND_05_SCENE.png')
    create_gif(scenes, d / 'METANO_CLIFF_POND_05_ANIMATION.gif')
    
    write_native(scenes[0], d / 'METANO_CLIFF_POND_05_SCENE.tile')
    write_tsj('METANO_CLIFF_POND_05_SCENE', scenes[0], [], d / 'METANO_CLIFF_POND_05_SCENE.tsj')
    print("Prefab 05 Déversoir généré.")
    return scenes

# -------------------------------------------------------------
# 4. Construction du Tileset Modulaire Complet (192x192 px, 24x24 tuiles)
# -------------------------------------------------------------
def build_modular_tileset():
    tw, th = 24, 24
    w, h = tw * 8, th * 8
    tileset_f1 = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    
    for y in range(0, 4):
        for x in range(16, 24):
            t = patch_herbe.crop(((x - 16) * 8, y * 8, (x - 15) * 8, (y + 1) * 8))
            tileset_f1.paste(t, (x * 8, y * 8))
            
    for y in range(0, 4):
        for x in range(16, 24):
            t = patch_roche.crop(((x - 16) * 8, y * 8, (x - 15) * 8, (y + 1) * 8))
            tileset_f1.paste(t, (x * 8, (y + 4) * 8))
            
    for y in range(0, 3):
        for x in range(16, 24):
            t = patch_rebord.crop(((x - 16) * 8, y * 8, (x - 15) * 8, (y + 1) * 8))
            tileset_f1.paste(t, (x * 8, (y + 8) * 8))
    for x in range(16, 24):
        t = patch_pied.crop(((x - 16) * 8, 0, (x - 15) * 8, 8))
        tileset_f1.paste(t, (x * 8, 11 * 8))
        
    for y in range(0, 4):
        for x in range(0, 8):
            t = base_im.crop((888 + x * 8, 16 + y * 8, 896 + x * 8, 24 + y * 8))
            tileset_f1.paste(t, (x * 8, y * 8))
            
    for x in range(0, 8):
        t = base_im.crop((912 + x * 8, 56, 920 + x * 8, 64))
        tileset_f1.paste(t, ((x + 8) * 8, 0))
        t2 = base_im.crop((912 + x * 8, 64, 920 + x * 8, 72))
        tileset_f1.paste(t2, ((x + 8) * 8, 8))
    for y in range(0, 2):
        for x in range(0, 4):
            tw_rock = base_im.crop((848 + x * 8, 96 + y * 8, 856 + x * 8, 104 + y * 8))
            tileset_f1.paste(tw_rock, ((x + 8) * 8, (y + 2) * 8))
            te_rock = base_im.crop((1096 + x * 8, 96 + y * 8, 1104 + x * 8, 104 + y * 8))
            tileset_f1.paste(te_rock, ((x + 12) * 8, (y + 2) * 8))
            
    for x in range(0, 8):
        t = base_im.crop((146 * 8 + x * 8, 60 * 8, 147 * 8 + x * 8, 61 * 8))
        tileset_f1.paste(t, (x * 8, 4 * 8))
    for x in range(0, 8):
        t = base_im.crop((146 * 8 + x * 8, 63 * 8, 147 * 8 + x * 8, 64 * 8))
        tileset_f1.paste(t, (x * 8, 5 * 8))
    for y in range(0, 2):
        for x in range(0, 4):
            tg_w = base_im.crop((124 * 8, (55 + y) * 8, 125 * 8, (56 + y) * 8))
            tileset_f1.paste(tg_w, ((x + 8) * 8, (y + 4) * 8))
            tg_e = base_im.crop((129 * 8, (55 + y) * 8, 130 * 8, (56 + y) * 8))
            tileset_f1.paste(tg_e, ((x + 12) * 8, (y + 4) * 8))
    tileset_f1.paste(base_im.crop((146*8, 60*8, 148*8, 62*8)), (0, 6*8))
    tileset_f1.paste(base_im.crop((152*8, 60*8, 154*8, 62*8)), (16, 6*8))
    tileset_f1.paste(base_im.crop((146*8, 62*8, 148*8, 64*8)), (32, 6*8))
    tileset_f1.paste(base_im.crop((152*8, 62*8, 154*8, 64*8)), (48, 6*8))
    
    for y in range(0, 8):
        for x in range(0, 16):
            idx = (x * 3 + y * 7) % len(CALM_WATER_TILES)
            tx, ty = CALM_WATER_TILES[idx]
            t = get_water_tile(tx, ty, phase=0)
            tileset_f1.paste(t, (x * 8, (y + 8) * 8))
            
    casc_f1 = casc_im.crop((0, 0, 64, 136))
    tileset_f1.paste(casc_f1.crop((16, 0, 48, 16)), (0, 16 * 8))
    tileset_f1.paste(casc_f1.crop((16, 16, 48, 48)), (0, 18 * 8))
    tileset_f1.paste(casc_f1.crop((8, 104, 56, 120)), (0, 22 * 8))
    
    tileset_f1.paste(step0, (8 * 8, 16 * 8), step0)
    tileset_f1.paste(step1, (12 * 8, 16 * 8), step1)
    tileset_f1.paste(step2, (8 * 8, 19 * 8), step2)
    rock_s = alt_obj_im.crop((456, 104, 472, 120))
    tileset_f1.paste(rock_s, (12 * 8, 19 * 8), rock_s)
    lily = alt_obj_im.crop((497, 106, 510, 119))
    if lily.size[0] > 0 and lily.size[1] > 0:
        tileset_f1.paste(lily, (14 * 8, 21 * 8), lily)
        
    atlas_4f = Image.new('RGBA', (w, h * 4))
    anims_tsj = []
    
    for p in range(4):
        sheet_p = tileset_f1.copy()
        for y in range(0, 8):
            for x in range(0, 16):
                idx = (x * 3 + y * 7) % len(CALM_WATER_TILES)
                tx, ty = CALM_WATER_TILES[idx]
                t = get_water_tile(tx, ty, phase=p)
                sheet_p.paste(t, (x * 8, (y + 8) * 8))
        c_p = casc_im.crop((p * 64, 0, (p + 1) * 64, 136))
        sheet_p.paste(c_p.crop((16, 0, 48, 16)), (0, 16 * 8))
        sheet_p.paste(c_p.crop((16, 16, 48, 48)), (0, 18 * 8))
        sheet_p.paste(c_p.crop((8, 104, 56, 120)), (0, 22 * 8))
        
        atlas_4f.paste(sheet_p, (0, p * h))
        
    for y in range(8, 16):
        for x in range(0, 16):
            tid = y * tw + x
            frames = [{'tileid': tid + p * (tw * th), 'duration': 167} for p in range(4)]
            anims_tsj.append({'id': tid, 'animation': frames})
            
    tileset_f1.save(OUT_SPRITES / 'METANO_POND_CLIFF_TILESET.png')
    atlas_4f.save(OUT_SPRITES / 'METANO_POND_CLIFF_TILESET_ANIM_4F.png')
    write_native(tileset_f1, OUT_SPRITES / 'METANO_POND_CLIFF_TILESET.tile')
    write_tsj('METANO_POND_CLIFF_TILESET', tileset_f1, anims_tsj, OUT_SPRITES / 'METANO_POND_CLIFF_TILESET.tsj')
    print("Tileset modulaire complet généré (576 tuiles, 4 phases animées).")

# -------------------------------------------------------------
# 5. Scène de démonstration : Terrasse de Falaise avec Étang (256x224 px)
# -------------------------------------------------------------
def build_integration_scene():
    w, h = 256, 224
    scene_base = Image.new('RGBA', (w, h))
    
    for y in range(0, h, 64):
        for x in range(0, w, 64):
            scene_base.paste(patch_herbe, (x, y))
            
    for x in range(0, w, 64):
        scene_base.paste(patch_rebord.crop((0, 0, min(64, w - x), 24)), (x, 0))
        scene_base.paste(patch_roche.crop((0, 0, min(64, w - x), 24)), (x, 24))
        
    for x in range(40, 176, 64):
        scene_base.paste(base_im.crop((888, 16, 888 + min(64, 176 - x), 24)), (x, 48))
        
    for y in range(56, 120, 24):
        scene_base.paste(base_im.crop((848, 96, 864, 120)), (32, y))
        scene_base.paste(base_im.crop((1096, 96, 1112, 120)), (184, y))
        
    for x in range(0, w, 64):
        scene_base.paste(patch_rebord.crop((0, 0, min(64, w - x), 24)), (x, 168))
        scene_base.paste(patch_roche.crop((0, 0, min(64, w - x), 32)), (x, 192))
        
    water_mask = Image.new('L', (w, h), 0)
    draw_m = ImageDraw.Draw(water_mask)
    draw_m.rounded_rectangle([42, 52, 182, 122], radius=12, fill=255)
    
    eau_frames = []
    for p in range(4):
        surf = make_water_surface(w, h, p, style='calm')
        eau_f = Image.new('RGBA', (w, h), (0, 0, 0, 0))
        eau_f.paste(surf, (0, 0), water_mask)
        eau_frames.append(eau_f)
        
    cascade_frames = []
    for p in range(4):
        casc_layer = Image.new('RGBA', (w, h), (0, 0, 0, 0))
        c_src = casc_im.crop((p * 64, 0, (p + 1) * 64, 136))
        chute = c_src.crop((16, 16, 48, 56))
        casc_layer.paste(chute, (104, 20), chute)
        foam = c_src.crop((8, 104, 56, 120))
        casc_layer.paste(foam, (96, 56), foam)
        cascade_frames.append(casc_layer)
        
    objets = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    objets.paste(river_rock, (56, 80), river_rock)
    objets.paste(step0, (116, 82), step0)
    objets.paste(step1, (144, 82), step1)
    
    scenes = []
    for p in range(4):
        comp = Image.alpha_composite(scene_base, eau_frames[p])
        comp = Image.alpha_composite(comp, cascade_frames[p])
        comp = Image.alpha_composite(comp, objets)
        scenes.append(comp)
        
    scenes[0].save(OUT_RENDERS / 'METANO_CLIFF_TERRASSE_POND_EXEMPLE.png')
    create_gif(scenes, OUT_RENDERS / 'METANO_CLIFF_TERRASSE_POND_EXEMPLE.gif')
    write_native(scenes[0], OUT_RENDERS / 'METANO_CLIFF_TERRASSE_POND_EXEMPLE.tile')
    print("Scène d'intégration de terrasse avec étang générée.")

# -------------------------------------------------------------
# 6. Planche de présentation complète (Proof Sheet)
# -------------------------------------------------------------
def build_proof_sheet():
    board_w, board_h = 1000, 720
    board = Image.new('RGB', (board_w, board_h), '#1a292b')
    draw = ImageDraw.Draw(board)
    
    font_path = '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'
    font_reg = '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'
    f_title = ImageFont.truetype(font_path, 22)
    f_sub = ImageFont.truetype(font_reg, 13)
    f_card = ImageFont.truetype(font_path, 13)
    f_tiny = ImageFont.truetype(font_reg, 11)
    
    draw.text((30, 20), "SPRITES DE POND PMD MÉTANO TOWN / TREASURE TOWN POUR FALAISES", font=f_title, fill='#dce9db')
    draw.text((30, 52), "Pixels natifs 8 px · Cadence 4 frames (10 ticks / 167 ms) · Multicalques Sol / Eau / Objets · Compatible PMDO & Tiled", font=f_sub, fill='#9ebebc')
    
    modules_info = [
        ('01_promontoire/METANO_CLIFF_POND_01_SCENE.png', "01. Promontoire", "80 × 64 px (10×8)", 30, 80),
        ('02_alcove/METANO_CLIFF_POND_02_SCENE.png', "02. Alcôve Falaise", "144 × 112 px (18×14)", 140, 80),
        ('03_cascade/METANO_CLIFF_POND_03_SCENE.png', "03. Grand Bassin & Cascade", "208 × 160 px (26×20)", 320, 80),
        ('04_cuvette_rocheuse/METANO_CLIFF_POND_04_SCENE.png', "04. Cuvette Rocheuse", "112 × 88 px (14×11)", 560, 80),
        ('05_deversoir/METANO_CLIFF_POND_05_SCENE.png', "05. Déversoir Falaise", "64 × 96 px (8×12)", 700, 80)
    ]
    
    for rel_path, title, dims, x, y in modules_info:
        im = Image.open(OUT_SPRITES / rel_path).convert('RGBA')
        draw.rectangle([x - 5, y - 5, x + im.width + 5, y + im.height + 25], outline='#37524f', fill='#23383a')
        board.paste(im, (x, y), im)
        draw.text((x, y + im.height + 2), title, font=f_card, fill='#dfcc8a')
        draw.text((x, y + im.height + 15), dims, font=f_tiny, fill='#9ebebc')
        
    ts_im = Image.open(OUT_SPRITES / 'METANO_POND_CLIFF_TILESET.png').convert('RGBA')
    draw.rectangle([25, 295, 25 + 192 + 10, 295 + 192 + 45], outline='#37524f', fill='#23383a')
    board.paste(ts_im, (30, 300), ts_im)
    draw.text((30, 500), "Tileset Modulaire Complet (24×24 tuiles de 8 px)", font=f_card, fill='#dfcc8a')
    draw.text((30, 518), "192 × 192 px · Berges rocheuses, herbe Métano, cascades, pierres de gué", font=f_tiny, fill='#9ebebc')
    
    integ_im = Image.open(OUT_RENDERS / 'METANO_CLIFF_TERRASSE_POND_EXEMPLE.png').convert('RGBA')
    draw.rectangle([255, 295, 255 + 256 + 10, 295 + 224 + 45], outline='#37524f', fill='#23383a')
    board.paste(integ_im, (260, 300), integ_im)
    draw.text((260, 532), "Exemple d'Intégration sur Terrasse de Falaise (32×28 tuiles)", font=f_card, fill='#dfcc8a')
    draw.text((260, 550), "256 × 224 px · Raccord naturel promontoire, paroi haute et vide en contrebas", font=f_tiny, fill='#9ebebc')
    
    draw.rectangle([545, 295, 965, 680], outline='#557a75', fill='#1f3335')
    draw.text((560, 310), "GUIDE D'IMPORT PMDO DEV", font=f_card, fill='#dfcc8a')
    guide_lines = [
        "1. PNG to Tileset : Importer à échelle 1x, grille de 8 px.",
        "2. Fichiers binaires : .tile fournis pour chargement direct.",
        "3. Tiled : .tsj fournis avec animations configurées à 167 ms.",
        "4. Ordre des calques recommandé dans l'éditeur :",
        "     - Calque 1 (Fond) : METANO_CLIFF_POND_*_SOL.png",
        "     - Calque 2 (Eau) : METANO_CLIFF_POND_*_EAU_F1..F4.png",
        "     - Calque 3 (Cascades) : METANO_CLIFF_POND_*_CASCADE_F1..F4.png",
        "     - Calque 4 (Objets) : METANO_CLIFF_POND_*_OBJETS.png",
        "5. Raccords : La palette et la roche s'alignent strictement avec",
        "   Metano_Town_Cliffs, Metano_Town_Base et Altere_Pond.",
        "6. Aucun redimensionnement arbitraire ni flou : pixel art net."
    ]
    for i, line in enumerate(guide_lines):
        draw.text((560, 340 + i * 22), line, font=f_tiny, fill='#e4ece0')
        
    board.save(OUT_RENDERS / 'PLANCHE_SPRITES_POND_CLIFF.png')
    print("Planche de présentation générée.")

# -------------------------------------------------------------
# 7. Génération du Manifeste JSON et de l'Aperçu HTML autonome
# -------------------------------------------------------------
def b64_uri(path):
    import base64
    raw = Path(path).read_bytes()
    return 'data:image/png;base64,' + base64.b64encode(raw).decode('ascii')

def build_manifest_and_html():
    manifest = {
        'name': 'METANO_CLIFF_POND_SPRITES',
        'target_engine': 'PMDO 0.8.12 Dev / Tiled 1.10',
        'grid_px': 8,
        'animation': {
            'frames': 4,
            'frame_length_ticks': 10,
            'duration_ms_per_frame': 167,
            'timing_proof': 'source/eau_metano/animations_carte.json'
        },
        'prefabs': {
            '01_promontoire': {
                'name': 'Petite Mare de Promontoire',
                'size_px': [80, 64],
                'grid_tiles': [10, 8],
                'desc': 'Étang compact adapté pour un rebord ou promontoire rocheux étroit.',
                'files': [
                    '01_promontoire/METANO_CLIFF_POND_01_SCENE.png',
                    '01_promontoire/METANO_CLIFF_POND_01_SOL.png',
                    '01_promontoire/METANO_CLIFF_POND_01_OBJETS.png',
                    '01_promontoire/METANO_CLIFF_POND_01_ANIMATION.gif'
                ]
            },
            '02_alcove': {
                'name': 'Étang d’Alcôve de Paroi',
                'size_px': [144, 112],
                'grid_tiles': [18, 14],
                'desc': 'Étang niché contre une haute paroi de falaise au nord, avec 3 pierres de gué pour traverser.',
                'files': [
                    '02_alcove/METANO_CLIFF_POND_02_SCENE.png',
                    '02_alcove/METANO_CLIFF_POND_02_SOL_FALAISE.png',
                    '02_alcove/METANO_CLIFF_POND_02_OBJETS.png',
                    '02_alcove/METANO_CLIFF_POND_02_ANIMATION.gif'
                ]
            },
            '03_cascade': {
                'name': 'Grand Bassin de Falaise avec Cascade & Déversoir',
                'size_px': [208, 160],
                'grid_tiles': [26, 20],
                'desc': 'Grand bassin scénique avec cascade amont tombant dans l’eau, grand rocher naturel et déversoir sud.',
                'files': [
                    '03_cascade/METANO_CLIFF_POND_03_SCENE.png',
                    '03_cascade/METANO_CLIFF_POND_03_SOL_FALAISE.png',
                    '03_cascade/METANO_CLIFF_POND_03_OBJETS.png',
                    '03_cascade/METANO_CLIFF_POND_03_ANIMATION.gif'
                ]
            },
            '04_cuvette_rocheuse': {
                'name': 'Cuvette Rocheuse Pure',
                'size_px': [112, 88],
                'grid_tiles': [14, 11],
                'desc': 'Bassin 100% minéral creusé à même la roche de falaise sans herbe, pour pics rocheux et crêtes.',
                'files': [
                    '04_cuvette_rocheuse/METANO_CLIFF_POND_04_SCENE.png',
                    '04_cuvette_rocheuse/METANO_CLIFF_POND_04_ROCHE.png',
                    '04_cuvette_rocheuse/METANO_CLIFF_POND_04_OBJETS.png',
                    '04_cuvette_rocheuse/METANO_CLIFF_POND_04_ANIMATION.gif'
                ]
            },
            '05_deversoir': {
                'name': 'Déversoir & Chute de Falaise',
                'size_px': [64, 96],
                'grid_tiles': [8, 12],
                'desc': 'Seuil rocheux où l’eau de l’étang s’évacue en cascade verticale vers le niveau inférieur.',
                'files': [
                    '05_deversoir/METANO_CLIFF_POND_05_SCENE.png',
                    '05_deversoir/METANO_CLIFF_POND_05_FALAISE.png',
                    '05_deversoir/METANO_CLIFF_POND_05_ANIMATION.gif'
                ]
            }
        },
        'modular_tileset': {
            'file': 'METANO_POND_CLIFF_TILESET.png',
            'size_px': [192, 192],
            'grid_tiles': [24, 24],
            'total_tiles': 576,
            'animated_sheet': 'METANO_POND_CLIFF_TILESET_ANIM_4F.png',
            'pmdo_tile': 'METANO_POND_CLIFF_TILESET.tile',
            'tiled_tsj': 'METANO_POND_CLIFF_TILESET.tsj'
        },
        'integration_example': {
            'file': 'METANO_CLIFF_TERRASSE_POND_EXEMPLE.png',
            'gif': 'METANO_CLIFF_TERRASSE_POND_EXEMPLE.gif',
            'size_px': [256, 224],
            'grid_tiles': [32, 28]
        }
    }
    
    (OUT_SPRITES / 'manifest.json').write_text(json.dumps(manifest, indent=2, ensure_ascii=False))
    
    data_html = {
        'modules': {
            '01_promontoire': {
                'name': "01. Petite Mare de Promontoire",
                'dims': "80 × 64 px (10 × 8 tuiles de 8 px)",
                'desc': "Conçue pour se nicher sur un petit promontoire ou une terrasse étroite de falaise, avec rebord de roche au sud et rive herbeuse.",
                'w': 80, 'h': 64,
                'sol': b64_uri(OUT_SPRITES / '01_promontoire/METANO_CLIFF_POND_01_SOL.png'),
                'eau': [b64_uri(OUT_SPRITES / f'01_promontoire/METANO_CLIFF_POND_01_EAU_F{p+1}.png') for p in range(4)],
                'objets': b64_uri(OUT_SPRITES / '01_promontoire/METANO_CLIFF_POND_01_OBJETS.png'),
                'scene': b64_uri(OUT_SPRITES / '01_promontoire/METANO_CLIFF_POND_01_SCENE.png')
            },
            '02_alcove': {
                'name': "02. Étang d'Alcôve de Paroi",
                'dims': "144 × 112 px (18 × 14 tuiles de 8 px)",
                'desc': "Encastré directement au pied d'une haute paroi de falaise Métano au nord avec ombre sur l'eau, et 3 pierres de gué pour traverser.",
                'w': 144, 'h': 112,
                'sol': b64_uri(OUT_SPRITES / '02_alcove/METANO_CLIFF_POND_02_SOL_FALAISE.png'),
                'eau': [b64_uri(OUT_SPRITES / f'02_alcove/METANO_CLIFF_POND_02_EAU_F{p+1}.png') for p in range(4)],
                'objets': b64_uri(OUT_SPRITES / '02_alcove/METANO_CLIFF_POND_02_OBJETS.png'),
                'scene': b64_uri(OUT_SPRITES / '02_alcove/METANO_CLIFF_POND_02_SCENE.png')
            },
            '03_cascade': {
                'name': "03. Grand Bassin avec Cascade & Déversoir",
                'dims': "208 × 160 px (26 × 20 tuiles de 8 px)",
                'desc': "Bassin scénique majeur alimenté par une cascade supérieure avec remous d'écume, grand rocher insulaire, et déversoir rocheux sud plongeant dans le vide.",
                'w': 208, 'h': 160,
                'sol': b64_uri(OUT_SPRITES / '03_cascade/METANO_CLIFF_POND_03_SOL_FALAISE.png'),
                'eau': [b64_uri(OUT_SPRITES / f'03_cascade/METANO_CLIFF_POND_03_EAU_F{p+1}.png') for p in range(4)],
                'cascade': [b64_uri(OUT_SPRITES / f'03_cascade/METANO_CLIFF_POND_03_CASCADE_F{p+1}.png') for p in range(4)],
                'objets': b64_uri(OUT_SPRITES / '03_cascade/METANO_CLIFF_POND_03_OBJETS.png'),
                'scene': b64_uri(OUT_SPRITES / '03_cascade/METANO_CLIFF_POND_03_SCENE.png')
            },
            '04_cuvette_rocheuse': {
                'name': "04. Cuvette Rocheuse Pure (Sans herbe)",
                'dims': "112 × 88 px (14 × 11 tuiles de 8 px)",
                'desc': "Bassin 100% minéral creusé dans la roche brute de falaise Métano sans herbe, pour hauteurs rocailleuses, grottes et pics escarpés.",
                'w': 112, 'h': 88,
                'sol': b64_uri(OUT_SPRITES / '04_cuvette_rocheuse/METANO_CLIFF_POND_04_ROCHE.png'),
                'eau': [b64_uri(OUT_SPRITES / f'04_cuvette_rocheuse/METANO_CLIFF_POND_04_EAU_F{p+1}.png') for p in range(4)],
                'objets': b64_uri(OUT_SPRITES / '04_cuvette_rocheuse/METANO_CLIFF_POND_04_OBJETS.png'),
                'scene': b64_uri(OUT_SPRITES / '04_cuvette_rocheuse/METANO_CLIFF_POND_04_SCENE.png')
            },
            '05_deversoir': {
                'name': "05. Déversoir & Chute de Falaise",
                'dims': "64 × 96 px (8 × 12 tuiles de 8 px)",
                'desc': "Module d'évacuation de bord de falaise où l'étang déborde en cascade verticale avec retombée d'écume.",
                'w': 64, 'h': 96,
                'sol': b64_uri(OUT_SPRITES / '05_deversoir/METANO_CLIFF_POND_05_FALAISE.png'),
                'cascade': [b64_uri(OUT_SPRITES / f'05_deversoir/METANO_CLIFF_POND_05_CASCADE_F{p+1}.png') for p in range(4)],
                'scene': b64_uri(OUT_SPRITES / '05_deversoir/METANO_CLIFF_POND_05_SCENE.png')
            }
        },
        'tileset': {
            'w': 192, 'h': 192,
            'img': b64_uri(OUT_SPRITES / 'METANO_POND_CLIFF_TILESET.png')
        },
        'integration': {
            'w': 256, 'h': 224,
            'img': b64_uri(OUT_RENDERS / 'METANO_CLIFF_TERRASSE_POND_EXEMPLE.png'),
            'gif': b64_uri(OUT_RENDERS / 'METANO_CLIFF_TERRASSE_POND_EXEMPLE.gif')
        },
        'planche': b64_uri(OUT_RENDERS / 'PLANCHE_SPRITES_POND_CLIFF.png')
    }
    
    html_content = """<!doctype html>
<html lang="fr">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>PMD Métano / Treasure Town — Sprites de Pond pour Falaises</title>
<style>
:root { color-scheme: dark; --teal: #407b77; --gold: #dfcc8a; --bg: #142123; --panel: #1d2e30; --border: #355052; }
* { box-sizing: border-box; }
body { margin: 0; background: var(--bg); color: #e4ece0; font: 14px/1.6 system-ui, -apple-system, sans-serif; }
header { background: #18282a; border-bottom: 1px solid var(--border); padding: 22px 28px; }
.badge { display: inline-block; font-size: 11px; letter-spacing: 2px; color: var(--gold); text-transform: uppercase; font-weight: bold; margin-bottom: 6px; }
h1 { margin: 0 0 6px; font-size: 26px; color: #f2f7f0; }
.sub { color: #a2bebc; margin: 0; }
nav.controls { display: flex; align-items: center; gap: 14px; flex-wrap: wrap; background: #192b2d; border-bottom: 1px solid var(--border); padding: 12px 28px; position: sticky; top: 0; z-index: 100; }
button { background: #2b4345; border: 1px solid #4a6c6d; color: #f2f7f0; padding: 7px 15px; border-radius: 5px; font: inherit; cursor: pointer; transition: background .15s; }
button:hover { background: #375558; border-color: var(--gold); }
button.active { background: var(--teal); border-color: var(--gold); color: #fff; }
label { display: flex; align-items: center; gap: 6px; cursor: pointer; user-select: none; }
select { background: #2b4345; border: 1px solid #4a6c6d; color: #f2f7f0; padding: 6px 12px; border-radius: 5px; font: inherit; }
.tabs { display: flex; gap: 4px; padding: 16px 28px 0; background: #162426; border-bottom: 1px solid var(--border); }
.tab-btn { background: #1c3032; border: 1px solid var(--border); border-bottom: none; border-radius: 6px 6px 0 0; color: #a2bebc; padding: 9px 18px; font-weight: 600; }
.tab-btn.active { background: var(--panel); color: var(--gold); border-color: var(--gold) var(--gold) var(--panel); }
main { padding: 28px; max-width: 1400px; margin: auto; }
.tab-content { display: none; }
.tab-content.active { display: block; }
.grid-prefabs { display: grid; grid-template-columns: repeat(auto-fit, minmax(420px, 1fr)); gap: 24px; }
.card { background: var(--panel); border: 1px solid var(--border); border-radius: 8px; overflow: hidden; display: flex; flex-direction: column; }
.card-head { padding: 12px 18px; background: #223739; border-bottom: 1px solid var(--border); display: flex; justify-content: space-between; align-items: center; }
.card-title { font-weight: bold; color: var(--gold); font-size: 15px; }
.card-dims { font-size: 11px; color: #9ebebc; }
.stage { min-height: 240px; display: flex; align-items: center; justify-content: center; background: repeating-conic-gradient(#263b3d 0% 25%, #213436 0% 50%) 0/16px 16px; padding: 20px; overflow: auto; position: relative; }
canvas { image-rendering: pixelated; image-rendering: crisp-edges; display: block; box-shadow: 0 4px 14px rgba(0,0,0,.4); }
.card-footer { padding: 14px 18px; font-size: 12px; color: #c4d7d3; border-top: 1px solid var(--border); background: #1a2a2c; }
.layer-toggles { display: flex; gap: 10px; margin-top: 8px; font-size: 11px; flex-wrap: wrap; }
.layer-toggles label { background: #273e40; padding: 3px 8px; border-radius: 4px; border: 1px solid #3c5d60; }
.guide-box { background: #1d2e30; border-left: 4px solid var(--gold); padding: 18px 24px; border-radius: 0 8px 8px 0; margin-bottom: 24px; line-height: 1.7; }
.guide-box h3 { margin: 0 0 8px; color: var(--gold); }
code { background: #132022; padding: 2px 6px; border-radius: 4px; color: #e4e2a8; font-family: monospace; font-size: 12px; }
table { width: 100%; border-collapse: collapse; margin: 16px 0; font-size: 13px; }
th, td { text-align: left; padding: 8px 12px; border-bottom: 1px solid var(--border); }
th { color: var(--gold); background: #233739; }
</style>
</head>
<body>
<header>
  <div class="badge">Pokémon Donjon Mystère · Bourg-Trésor / Métano Town</div>
  <h1>Sprites de Pond (Mares & Étangs) pour Falaises</h1>
  <p class="sub">5 modules complets préfabriqués étalonnés pour falaises + Tileset modulaire 8px + Découpage multicalques natif PMDO Dev</p>
</header>

<nav class="controls">
  <button id="btn-play">Pause</button>
  <button id="btn-next">Frame suivante</button>
  <span id="frame-indicator" style="font-weight: bold; color: var(--gold); min-width: 90px;">Frame 1 / 4</span>
  <div style="height: 20px; width: 1px; background: var(--border);"></div>
  <label>Zoom :
    <select id="zoom-select">
      <option value="1">1× (Natif 100%)</option>
      <option value="2" selected>2× (Pixel Art)</option>
      <option value="3">3× (Grand)</option>
      <option value="4">4× (Détail)</option>
    </select>
  </label>
  <label><input type="checkbox" id="chk-grid"> Grille 8 px</label>
</nav>

<div class="tabs">
  <button class="tab-btn active" data-tab="prefabs">01. Les 5 Modules d'Étangs</button>
  <button class="tab-btn" data-tab="tileset">02. Tileset Modulaire (24×24)</button>
  <button class="tab-btn" data-tab="integration">03. Scène d'Intégration Falaise</button>
  <button class="tab-btn" data-tab="planche">04. Planche Complète</button>
  <button class="tab-btn" data-tab="guide">05. Guide d'Import PMDO</button>
</div>

<main>
  <!-- TAB 1 : PREFABS -->
  <div id="tab-prefabs" class="tab-content active">
    <div class="guide-box">
      <h3>Modules préfabriqués prêts à l'emploi pour terrasses et parois</h3>
      Ces 5 modules sont calibrés aux dimensions exactes de Métano Town et prêts à être importés dans PMDO via <code>PNG to Tileset</code>. Vous pouvez activer ou masquer les calques individuellement ci-dessous pour inspecter la séparation Sol / Eau / Objets / Cascades.
    </div>
    <div class="grid-prefabs" id="prefabs-container"></div>
  </div>

  <!-- TAB 2 : TILESET MODULAIRE -->
  <div id="tab-tileset" class="tab-content">
    <div class="guide-box">
      <h3>Tileset Modulaire Complet (192 × 192 px — 576 tuiles de 8 px)</h3>
      Ce tileset regroupe l'intégralité des briques élémentaires pour dessiner n'importe quel plan d'eau ou méandre sur vos falaises. Fichiers fournis : <code>METANO_POND_CLIFF_TILESET.png</code>, <code>METANO_POND_CLIFF_TILESET.tile</code> (PMDO natif), et <code>METANO_POND_CLIFF_TILESET.tsj</code> (Tiled).
    </div>
    <div class="card">
      <div class="card-head">
        <span class="card-title">METANO_POND_CLIFF_TILESET — Planche 24×24 tuiles</span>
        <span class="card-dims">192 × 192 px</span>
      </div>
      <div class="stage">
        <canvas id="canvas-tileset" width="192" height="192"></canvas>
      </div>
      <div class="card-footer">
        <b>Organisation des zones du tileset :</b><br>
        • Lignes 0-3 : Paroi falaise plongeant dans l'eau (ombre portée, fond rocheux) & berges rocheuses sud/latérales.<br>
        • Lignes 4-7 : Berges herbeuses Métano complètes (N, S, E, O, coins intérieurs et extérieurs).<br>
        • Lignes 8-15 : Surfaces d'eau animées (eau profonde, eau peu profonde, vaguelettes 4 phases).<br>
        • Lignes 16-23 : Cascades amont, déversoirs de falaise, pierres de gué (pas japonais) et rochers émergés.
      </div>
    </div>
  </div>

  <!-- TAB 3 : INTEGRATION FALAISE -->
  <div id="tab-integration" class="tab-content">
    <div class="guide-box">
      <h3>Démonstration : Terrasse de Falaise avec Étang (256 × 224 px — 32 × 28 tuiles)</h3>
      Exemple concret montrant l'étang d'alcôve avec cascade amont et pierres de gué intégré sur une falaise à plusieurs niveaux, avec chemin herbeux et plongée vers le vide au sud.
    </div>
    <div class="card">
      <div class="card-head">
        <span class="card-title">METANO_CLIFF_TERRASSE_POND_EXEMPLE</span>
        <span class="card-dims">256 × 224 px · Animation synchronisée 4 frames</span>
      </div>
      <div class="stage">
        <canvas id="canvas-integ" width="256" height="224"></canvas>
      </div>
    </div>
  </div>

  <!-- TAB 4 : PLANCHE -->
  <div id="tab-planche" class="tab-content">
    <div class="guide-box">
      <h3>Planche de Présentation & Synthèse</h3>
      Vue d'ensemble HD de tous les sprites et modules du pack.
    </div>
    <div style="text-align: center; overflow: auto; background: #162426; padding: 18px; border-radius: 8px; border: 1px solid var(--border);">
      <img id="img-planche" style="max-width: 100%; height: auto; image-rendering: pixelated; border-radius: 4px;" alt="Planche de synthèse">
    </div>
  </div>

  <!-- TAB 5 : GUIDE PMDO -->
  <div id="tab-guide" class="tab-content">
    <div class="guide-box">
      <h3>Protocole d'importation dans PMDO Dev</h3>
      <p>Pour intégrer ces étangs dans vos cartes de falaises (comme vos fichiers <code>cliffnordouesttest1.rsground</code> et <code>cliffdaytest.rsground</code>) :</p>
      <table>
        <thead>
          <tr>
            <th>Élément</th>
            <th>Fichier</th>
            <th>Calque suggéré</th>
            <th>Usage</th>
          </tr>
        </thead>
        <tbody>
          <tr>
            <td>Sol & Parois</td>
            <td><code>METANO_CLIFF_POND_*_SOL.png</code></td>
            <td>Layer 1 ou New Layer (Base)</td>
            <td>Terrain statique : herbe, roche de falaise et bordures</td>
          </tr>
          <tr>
            <td>Eau animée (4 frames)</td>
            <td><code>METANO_CLIFF_POND_*_EAU_F1..F4.png</code></td>
            <td>River ou Layer animé</td>
            <td>Surface de l'eau transparente (cycle de 10 ticks = 167 ms)</td>
          </tr>
          <tr>
            <td>Cascades & Déversoir</td>
            <td><code>METANO_CLIFF_POND_*_CASCADE_F1..F4.png</code></td>
            <td>River / Chute</td>
            <td>Chute d'eau vive et écume au pied</td>
          </tr>
          <tr>
            <td>Objets & Traversée</td>
            <td><code>METANO_CLIFF_POND_*_OBJETS.png</code></td>
            <td>Objects Under ou Objects</td>
            <td>Pierres de gué, rochers émergés, nénuphars</td>
          </tr>
        </tbody>
      </table>
      <h4>Règles d'importation PMDO confirmées :</h4>
      <ul>
        <li><b>PNG to Tileset :</b> Choisir une taille de tuile stricte de <b>8 px</b>. Les dimensions de toutes les images sont rigoureusement des multiples de 8.</li>
        <li><b>Nommage unique :</b> Tous les fichiers portent le préfixe unique <code>METANO_CLIFF_POND_*</code> pour éviter tout conflit de basename dans l'éditeur.</li>
        <li><b>Transparence directe :</b> Format RGBA straight alpha sans aucun halo noir ni prémultiplication.</li>
      </ul>
    </div>
  </div>
</main>

<script>
const DATA = __DATA__;
let currentFrame = 0;
let isPlaying = true;
let zoom = 2;
let showGrid = false;
let lastTick = performance.now();
const FRAME_DURATION = 167;

const loadedImages = {};

function loadImage(src) {
  return new Promise((resolve, reject) => {
    const im = new Image();
    im.onload = () => resolve(im);
    im.onerror = reject;
    im.src = src;
  });
}

const prefabsContainer = document.getElementById('prefabs-container');
const prefabCanvases = {};
const layerStates = {};

for (const [key, mod] of Object.entries(DATA.modules)) {
  layerStates[key] = { sol: true, eau: true, cascade: true, objets: true };
  
  const card = document.createElement('div');
  card.className = 'card';
  card.innerHTML = `
    <div class="card-head">
      <span class="card-title">${mod.name}</span>
      <span class="card-dims">${mod.dims}</span>
    </div>
    <div class="stage">
      <canvas id="canvas-${key}" width="${mod.w}" height="${mod.h}"></canvas>
    </div>
    <div class="card-footer">
      <div>${mod.desc}</div>
      <div class="layer-toggles">
        <label><input type="checkbox" checked data-layer="sol" data-key="${key}"> Sol & Falaise</label>
        <label><input type="checkbox" checked data-layer="eau" data-key="${key}"> Eau animée</label>
        ${mod.cascade ? `<label><input type="checkbox" checked data-layer="cascade" data-key="${key}"> Cascade / Déversoir</label>` : ''}
        ${mod.objets ? `<label><input type="checkbox" checked data-layer="objets" data-key="${key}"> Objets & Gué</label>` : ''}
      </div>
    </div>
  `;
  prefabsContainer.appendChild(card);
  prefabCanvases[key] = document.getElementById(`canvas-${key}`);
}

function drawCanvas(canvas, drawFn) {
  const ctx = canvas.getContext('2d');
  ctx.imageSmoothingEnabled = false;
  ctx.clearRect(0, 0, canvas.width, canvas.height);
  drawFn(ctx);
  
  if (showGrid) {
    ctx.strokeStyle = 'rgba(223, 204, 138, 0.35)';
    ctx.lineWidth = 0.5;
    for (let x = 0; x <= canvas.width; x += 8) {
      ctx.beginPath(); ctx.moveTo(x, 0); ctx.lineTo(x, canvas.height); ctx.stroke();
    }
    for (let y = 0; y <= canvas.height; y += 8) {
      ctx.beginPath(); ctx.moveTo(0, y); ctx.lineTo(canvas.width, y); ctx.stroke();
    }
  }
  
  canvas.style.width = (canvas.width * zoom) + 'px';
  canvas.style.height = (canvas.height * zoom) + 'px';
}

function renderAll() {
  for (const [key, mod] of Object.entries(DATA.modules)) {
    const canvas = prefabCanvases[key];
    const state = layerStates[key];
    drawCanvas(canvas, (ctx) => {
      if (state.sol && loadedImages[mod.sol]) ctx.drawImage(loadedImages[mod.sol], 0, 0);
      if (state.eau && mod.eau && loadedImages[mod.eau[currentFrame]]) ctx.drawImage(loadedImages[mod.eau[currentFrame]], 0, 0);
      if (state.cascade && mod.cascade && loadedImages[mod.cascade[currentFrame]]) ctx.drawImage(loadedImages[mod.cascade[currentFrame]], 0, 0);
      if (state.objets && mod.objets && loadedImages[mod.objets]) ctx.drawImage(loadedImages[mod.objets], 0, 0);
    });
  }
  
  const tsCanvas = document.getElementById('canvas-tileset');
  if (tsCanvas && loadedImages[DATA.tileset.img]) {
    drawCanvas(tsCanvas, (ctx) => {
      ctx.drawImage(loadedImages[DATA.tileset.img], 0, 0);
    });
  }
  
  const integCanvas = document.getElementById('canvas-integ');
  if (integCanvas && loadedImages[DATA.integration.img]) {
    drawCanvas(integCanvas, (ctx) => {
      ctx.drawImage(loadedImages[DATA.integration.img], 0, 0);
    });
  }
}

function loop(now) {
  if (isPlaying && now - lastTick >= FRAME_DURATION) {
    currentFrame = (currentFrame + 1) % 4;
    document.getElementById('frame-indicator').textContent = `Frame ${currentFrame + 1} / 4`;
    lastTick = now;
    renderAll();
  }
  requestAnimationFrame(loop);
}

document.getElementById('btn-play').onclick = function() {
  isPlaying = !isPlaying;
  this.textContent = isPlaying ? 'Pause' : 'Reprendre';
};

document.getElementById('btn-next').onclick = function() {
  isPlaying = false;
  document.getElementById('btn-play').textContent = 'Reprendre';
  currentFrame = (currentFrame + 1) % 4;
  document.getElementById('frame-indicator').textContent = `Frame ${currentFrame + 1} / 4`;
  renderAll();
};

document.getElementById('zoom-select').onchange = function() {
  zoom = parseInt(this.value, 10);
  renderAll();
};

document.getElementById('chk-grid').onchange = function() {
  showGrid = this.checked;
  renderAll();
};

prefabsContainer.addEventListener('change', (e) => {
  if (e.target.dataset.layer) {
    const key = e.target.dataset.key;
    const layer = e.target.dataset.layer;
    layerStates[key][layer] = e.target.checked;
    renderAll();
  }
});

document.querySelectorAll('.tab-btn').forEach(btn => {
  btn.onclick = function() {
    document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
    document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
    this.classList.add('active');
    document.getElementById('tab-' + this.dataset.tab).classList.add('active');
    renderAll();
  };
});

async function init() {
  const urls = [];
  for (const mod of Object.values(DATA.modules)) {
    urls.push(mod.sol);
    if (mod.eau) urls.push(...mod.eau);
    if (mod.cascade) urls.push(...mod.cascade);
    if (mod.objets) urls.push(mod.objets);
  }
  urls.push(DATA.tileset.img);
  urls.push(DATA.integration.img);
  
  document.getElementById('img-planche').src = DATA.planche;
  
  await Promise.all(urls.map(async u => {
    if (!loadedImages[u]) loadedImages[u] = await loadImage(u);
  }));
  
  renderAll();
  requestAnimationFrame(loop);
}

init();
</script>
</body>
</html>
"""
    html_filled = html_content.replace('__DATA__', json.dumps(data_html))
    (ROOT / 'apercu_pond_metano_cliffs.html').write_text(html_filled, encoding='utf-8')
    print("Aperçu HTML généré : apercu_pond_metano_cliffs.html")

if __name__ == '__main__':
    build_prefab_01()
    build_prefab_02()
    build_prefab_03()
    build_prefab_04()
    build_prefab_05()
    build_modular_tileset()
    build_integration_scene()
    build_proof_sheet()
    build_manifest_and_html()
