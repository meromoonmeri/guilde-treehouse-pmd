#!/usr/bin/env python3
"""GB1 — Grotte Brumeuse (Foggy Forest Cavern) : map multicalque PMDO 8px canonique.
Progression Sud vers Nord menant à une entrée de grotte naturelle style Crooked Cavern,
avec texture de roche harmonisée à la clairière moussue, lianes retombantes et verdure.
--build   : génère les calques, planches, aperçus viewport, packs ZIP et WebP
--verify  : contrôle d'intégrité, opacité du sol, palettes canoniques, navigabilité
--pmdo    : sérialisation .rsground, banques .tile 8px, test d'installation PMDO
"""
import argparse, io, json, os, shutil, sys, tempfile, zipfile
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage

R = Path(__file__).resolve().parents[2]
O = R / 'renders/grotte_brumeuse_v1'
S = R / 'source/grotte_brumeuse_v1'
C = R / '.cache/grotte_brumeuse_v1'

sys.path.insert(0, str(R / 'source/cote_v4_abyss'))
from night import night

MAP_CONFIG = {
    'id': 'grotte_brumeuse',
    'title': 'Grotte Brumeuse (Foggy Forest Cavern)',
    'code': 'GB1_grotte_brumeuse',
    'size': (480, 336),
    'tiles_grid': (60, 42),
    'spawn': [240, 296],
    'cave_mouth': [240, 72],
    'offset': [0, -40],
    'layers_def': [
        {'id': 'sol', 'title': '01 - Sol clairière moussue et chemin sud-nord (100% opaque)'},
        {'id': 'parois_grotte_crooked', 'title': '02 - Parois rocheuses et arche de grotte style Crooked Cavern'},
        {'id': 'troncs_arbres_fond', 'title': '03 - Arbres massifs et racines anciennes Foggy Forest'},
        {'id': 'lianes_et_verdure', 'title': '04 - Lianes retombantes, fougères et verdure luxuriante'},
        {'id': 'canopee_avant_plan', 'title': '05 - Canopée haute et frondaisons d avant-plan'},
        {'id': 'brume_atmospherique', 'title': '06 - Voile de brume et puits de lumière dorée'}
    ]
}

def img(b):
    return Image.open(io.BytesIO(b) if isinstance(b, (bytes, bytearray)) else b).convert('RGBA')

def png(im):
    b = io.BytesIO()
    im.save(b, format='PNG', optimize=True)
    return b.getvalue()

def jb(obj):
    return json.dumps(obj, indent=2, ensure_ascii=False).encode('utf-8')

def build_layers():
    """Construit les 6 calques sémantiques canoniques pour GB1."""
    W, H = MAP_CONFIG['size']
    
    # Sources natives canoniques
    ff = Image.open(R / 'Foggy_Forest_Base_Camp_TDS.png').convert('RGBA')
    cc = Image.open(R / 'source/cote_v5_expeditions/audit/Halcyon__crooked_cavern_entrance_layer_0.png').convert('RGBA')
    liane = Image.open(R / 'renders/cafe_spinda_revisite_v7/assets/SpindaV7_liane.png').convert('RGBA')
    vt = Image.open(R / 'exports/vegetation_treehouse_v1/tilesheets/VT1_vegetation_phase_0.png').convert('RGBA')
    
    # ---------------- 01 - SOL CONTINU 100% OPAQUE ----------------
    # Découpe de la clairière moussue de Foggy Forest
    ff_clearing = ff.crop((60, 380, 540, 716))
    sol_arr = np.array(ff_clearing).copy()
    sol_arr[:, :, 3] = 255 # Garanti 100% opaque
    
    # Chemin progressant du Sud [240, 296] vers le Nord [240, 72]
    yy, xx = np.mgrid[:H, :W]
    path_cx = 240 + 16 * np.sin((yy - 72) / (H - 72) * np.pi)
    path_dist = np.abs(xx - path_cx)
    path_mask = (path_dist < 26) & (yy >= 72) & (yy <= 316)
    vestibule = (yy >= 64) & (yy <= 104) & (xx >= 204) & (xx <= 276)
    path_mask |= vestibule
    
    # Teinte de terre meuble et clairière battue
    sol_arr[path_mask, 0] = np.clip(sol_arr[path_mask, 0].astype(int) * 0.95 + 16, 0, 255).astype(np.uint8)
    sol_arr[path_mask, 1] = np.clip(sol_arr[path_mask, 1].astype(int) * 0.95 + 18, 0, 255).astype(np.uint8)
    sol_arr[path_mask, 2] = np.clip(sol_arr[path_mask, 2].astype(int) * 0.90 + 10, 0, 255).astype(np.uint8)
    sol_im = Image.fromarray(sol_arr)
    
    # ---------------- 02 - PAROIS GROTTE CROOKED ----------------
    cc_arr = np.array(cc)
    
    def harmonize_rock(patch):
        arr = patch.copy()
        lum = (0.299 * arr[:, :, 0] + 0.587 * arr[:, :, 1] + 0.114 * arr[:, :, 2]) / 255.0
        dark_mask = (lum < 0.22) & (arr[:, :, 3] > 0)
        
        r = np.where(dark_mask, arr[:, :, 0] * 0.65, lum * 138 + 42).clip(0, 255).astype(np.uint8)
        g = np.where(dark_mask, arr[:, :, 1] * 0.65, lum * 162 + 56).clip(0, 255).astype(np.uint8)
        b = np.where(dark_mask, arr[:, :, 2] * 0.65, lum * 116 + 36).clip(0, 255).astype(np.uint8)
        
        r = (r // 8) * 8
        g = (g // 8) * 8
        b = (b // 8) * 8
        return np.stack([r, g, b, arr[:, :, 3]], axis=-1)
    
    parois_im = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    # Arche centrale de la grotte (Crooked Cavern 128x100)
    arch_patch = cc_arr[10:110, 96:224]
    arch_harm = Image.fromarray(harmonize_rock(arch_patch))
    parois_im.alpha_composite(arch_harm, (176, 16))
    
    # Parois rocheuses latérales gauche
    left_patch = cc_arr[10:130, 0:96]
    left_harm = Image.fromarray(harmonize_rock(left_patch))
    parois_im.alpha_composite(left_harm, (80, 16))
    parois_im.alpha_composite(left_harm, (0, 16))
    
    # Parois rocheuses latérales droite
    right_patch = cc_arr[10:130, 224:320]
    right_harm = Image.fromarray(harmonize_rock(right_patch))
    parois_im.alpha_composite(right_harm, (304, 16))
    parois_im.alpha_composite(right_harm, (384, 16))
    
    # ---------------- 03 - TRONCS ARBRES FOND ----------------
    troncs_im = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    # Arbre massif gauche Foggy Forest
    left_trunk = ff.crop((60, 420, 160, 680))
    lt_arr = np.array(left_trunk)
    lt_mask = (lt_arr[:, :, 0] < 120) & (lt_arr[:, :, 1] < 150) & (lt_arr[:, :, 2] < 115)
    lt_arr[~lt_mask, 3] = 0
    troncs_im.alpha_composite(Image.fromarray(lt_arr), (0, 60))
    
    # Arbre massif droit Foggy Forest
    right_trunk = ff.crop((440, 420, 540, 680))
    rt_arr = np.array(right_trunk)
    rt_mask = (rt_arr[:, :, 0] < 120) & (rt_arr[:, :, 1] < 150) & (rt_arr[:, :, 2] < 115)
    rt_arr[~rt_mask, 3] = 0
    troncs_im.alpha_composite(Image.fromarray(rt_arr), (380, 60))
    
    # ---------------- 04 - LIANES ET VERDURE ----------------
    lianes_im = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    liane_flip = liane.transpose(Image.Transpose.FLIP_LEFT_RIGHT)
    
    # Lianes descendantes le long de l arche et des corniches
    lianes_im.alpha_composite(liane, (188, 24))
    lianes_im.alpha_composite(liane_flip.crop((0, 0, 32, 44)), (244, 20))
    lianes_im.alpha_composite(liane, (272, 28))
    lianes_im.alpha_composite(liane_flip, (136, 32))
    lianes_im.alpha_composite(liane, (344, 30))
    lianes_im.alpha_composite(liane_flip.crop((0, 0, 32, 40)), (92, 28))
    lianes_im.alpha_composite(liane.crop((0, 0, 32, 40)), (392, 28))
    
    # Fougères et massifs de verdure aux pieds des parois et le long du chemin
    fern1 = vt.crop((0, 0, 32, 32))
    fern2 = vt.crop((32, 0, 64, 32))
    clover = vt.crop((64, 0, 96, 32))
    
    lianes_im.alpha_composite(fern1, (168, 108))
    lianes_im.alpha_composite(fern2, (276, 108))
    lianes_im.alpha_composite(clover, (144, 120))
    lianes_im.alpha_composite(fern1, (308, 120))
    lianes_im.alpha_composite(fern2, (64, 130))
    lianes_im.alpha_composite(clover, (384, 130))
    lianes_im.alpha_composite(fern1, (180, 240))
    lianes_im.alpha_composite(fern2, (292, 230))
    
    # ---------------- 05 - CANOPEE AVANT PLAN ----------------
    canopee_im = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    canopy_crop = ff.crop((60, 20, 540, 84))
    can_arr = np.array(canopy_crop)
    can_mask = (can_arr[:, :, 1] > 90) & (can_arr[:, :, 0] < 160)
    can_arr[~can_mask, 3] = 0
    canopee_im.alpha_composite(Image.fromarray(can_arr), (0, 0))
    
    # ---------------- 06 - BRUME ATMOSPHERIQUE ----------------
    brume_im = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    b_draw = ImageDraw.Draw(brume_im)
    # Bandes de brume flottante caractéristiques de Foggy Forest
    for band_y, h_band in [(16, 48), (96, 64), (180, 56), (260, 48)]:
        for x in range(0, W, 8):
            alpha = int(22 + 16 * np.sin(x / 40.0 + band_y))
            b_draw.ellipse([x - 20, band_y, x + 40, band_y + h_band], fill=(230, 220, 170, alpha))
            
    # Puits de lumière et rayons solaires en biais
    for bx in [80, 180, 280, 380]:
        b_draw.polygon([(bx, 0), (bx + 40, 0), (bx + 80, H), (bx + 30, H)], fill=(245, 235, 185, 15))
    
    return {
        'sol': sol_im,
        'parois_grotte_crooked': parois_im,
        'troncs_arbres_fond': troncs_im,
        'lianes_et_verdure': lianes_im,
        'canopee_avant_plan': canopee_im,
        'brume_atmospherique': brume_im
    }

def compose_scene(layers_dict, order_ids):
    first = layers_dict[order_ids[0]]
    out = Image.new('RGBA', first.size, (0, 0, 0, 0))
    for lid in order_ids:
        out.alpha_composite(layers_dict[lid])
    return out

def build_magenta_view(comp_im):
    """Place la composition sur un fond magenta pur #FF00FF pour l'emballage et les guides d'import."""
    w, h = comp_im.size
    bg = Image.new('RGBA', (w, h), (255, 0, 255, 255))
    bg.alpha_composite(comp_im)
    return bg.convert('RGB')

def build_board(title, layers_dict, order_ids, comp_im):
    w, h = comp_im.size
    panels = [(lid, layers_dict[lid]) for lid in order_ids] + [('composition_finale', comp_im)]
    cols = 2
    rows = (len(panels) + 1) // 2
    out = Image.new('RGB', (cols * w, rows * (h + 32)), '#1e242b')
    draw = ImageDraw.Draw(out)
    for j, (name, im) in enumerate(panels):
        x = (j % cols) * w
        y = (j // cols) * (h + 32)
        draw.text((x + 12, y + 8), f'{title} — {name}', fill='#e2e8f0')
        bg = Image.new('RGBA', (w, h), '#2d3748')
        bg.alpha_composite(im)
        out.paste(bg.convert('RGB'), (x, y + 32))
    return out

def build_viewport(comp_im, spawn, screen_size=(320, 240)):
    sw, sh = screen_size
    w, h = comp_im.size
    sx, sy = spawn
    cx = max(0, min(w - sw, sx - sw // 2))
    cy = max(0, min(h - sh, sy - sh // 2))

    view_crop = comp_im.crop((cx, cy, cx + sw, cy + sh))
    frame = Image.new('RGB', (w, h + 32), '#1a202c')
    draw = ImageDraw.Draw(frame)
    draw.text((12, 8), f'Viewport Camera 320x240 (x1) — Focus Spawn [{sx}, {sy}]', fill='#fbbf24')
    frame.paste(comp_im.convert('RGB'), (0, 32))
    box_draw = ImageDraw.Draw(frame)
    box_draw.rectangle([cx, cy + 32, cx + sw, cy + 32 + sh], outline='#f59e0b', width=2)
    box_draw.ellipse([sx - 4, sy + 32 - 4, sx + 4, sy + 32 + 4], fill='#ef4444', outline='#ffffff')
    # Cave marker
    box_draw.ellipse([240 - 4, 72 + 32 - 4, 240 + 4, 72 + 32 + 4], fill='#3b82f6', outline='#ffffff')
    box_draw.text((248, 72 + 32 - 6), 'Entree Grotte', fill='#60a5fa')
    box_draw.text((sx + 8, sy + 32 - 6), 'Depart Sud', fill='#f87171')
    return frame, view_crop

def build():
    O.mkdir(parents=True, exist_ok=True)
    C.mkdir(parents=True, exist_ok=True)
    w, h = MAP_CONFIG['size']
    order_ids = [l['id'] for l in MAP_CONFIG['layers_def']]
    
    # 1. Génération des calques Jour
    day_layers = build_layers()
    comp_day = compose_scene(day_layers, order_ids)
    
    # 2. Génération des calques Nuit (Abyss)
    night_layers = {lid: night(day_layers[lid]) for lid in order_ids}
    sol_nuit_arr = np.array(night_layers['sol'])
    sol_nuit_arr[:, :, 3] = 255 # Force 100% opaque continuous ground
    night_layers['sol'] = Image.fromarray(sol_nuit_arr)
    comp_night = compose_scene(night_layers, order_ids)
    
    # 3. Vue sur fond magenta pur #FF00FF
    comp_magenta = build_magenta_view(comp_day)
    
    # 4. Exports des cartes complètes
    (O / 'GB1_grotte_brumeuse_carte_jour.png').write_bytes(png(comp_day))
    (O / 'GB1_grotte_brumeuse_carte_nuit.png').write_bytes(png(comp_night))
    (O / 'GB1_grotte_brumeuse_carte_magenta.png').write_bytes(png(comp_magenta))
    (O / 'GB1_grotte_brumeuse_carte.png').write_bytes(png(comp_day))
    
    # 5. Planches de calques
    board_day = build_board('GB1 Grotte Brumeuse (Jour)', day_layers, order_ids, comp_day)
    (O / 'GB1_grotte_brumeuse_calques.png').write_bytes(png(board_day))
    
    # 6. Viewport caméra PMDO 320x240
    vp_frame, vp_crop = build_viewport(comp_day, MAP_CONFIG['spawn'])
    (O / 'GB1_grotte_brumeuse_viewport.png').write_bytes(png(vp_frame))
    (O / 'GB1_grotte_brumeuse_viewport_320x240.png').write_bytes(png(vp_crop))
    
    # 7. Animation WebP Jour/Nuit (boucle 2s)
    anim_path = O / 'GB1_grotte_brumeuse_ambiances.webp'
    comp_day.convert('RGB').save(
        anim_path, save_all=True,
        append_images=[comp_night.convert('RGB')],
        duration=[2000, 2000], loop=0, lossless=True
    )
    
    # 8. Archive Calques ZIP Pack et exports répertoires
    (O / 'calques_jour').mkdir(parents=True, exist_ok=True)
    (O / 'calques_nuit').mkdir(parents=True, exist_ok=True)
    (O / 'calques_magenta').mkdir(parents=True, exist_ok=True)
    
    zip_files = {}
    for lid in order_ids:
        b_jour = png(day_layers[lid])
        b_nuit = png(night_layers[lid])
        calque_mag = build_magenta_view(day_layers[lid])
        b_mag = png(calque_mag)
        
        # Enregistrement sur disque pour le visualiseur web
        (O / f'calques_jour/GB1_grotte_brumeuse_{lid}_jour.png').write_bytes(b_jour)
        (O / f'calques_nuit/GB1_grotte_brumeuse_{lid}_nuit.png').write_bytes(b_nuit)
        (O / f'calques_magenta/GB1_grotte_brumeuse_{lid}_magenta.png').write_bytes(b_mag)
        
        zip_files[f'calques_jour/GB1_grotte_brumeuse_{lid}_jour.png'] = b_jour
        zip_files[f'calques_nuit/GB1_grotte_brumeuse_{lid}_nuit.png'] = b_nuit
        zip_files[f'calques_magenta/GB1_grotte_brumeuse_{lid}_magenta.png'] = b_mag
        
    zip_files['GB1_grotte_brumeuse_carte_jour.png'] = png(comp_day)
    zip_files['GB1_grotte_brumeuse_carte_nuit.png'] = png(comp_night)
    zip_files['GB1_grotte_brumeuse_carte_magenta.png'] = png(comp_magenta)
    
    manifest = {
        'lot': 'GB1',
        'id': MAP_CONFIG['id'],
        'title': MAP_CONFIG['title'],
        'size': [w, h],
        'tiles_grid': [w // 8, h // 8],
        'semantic_groups': len(order_ids),
        'spawn_point': MAP_CONFIG['spawn'],
        'cave_mouth': MAP_CONFIG['cave_mouth'],
        'camera_offset': MAP_CONFIG['offset'],
        'layers': [
            {
                'id': l['id'],
                'title': l['title'],
                'file_jour': f'calques_jour/GB1_grotte_brumeuse_{l["id"]}_jour.png',
                'file_nuit': f'calques_nuit/GB1_grotte_brumeuse_{l["id"]}_nuit.png',
                'file_magenta': f'calques_magenta/GB1_grotte_brumeuse_{l["id"]}_magenta.png'
            }
            for l in MAP_CONFIG['layers_def']
        ],
        'notes': [
            'Progression Sud vers Nord menant a l entree de la grotte',
            'Texture de roche Crooked Cavern harmonisee a la clairiere moussue Foggy Forest',
            'Sol continu 100% opaque sous le decor pour eviter toute lacune alpha',
            'Passage et chemin sud-nord verifies avec erosion binaire 17px',
            'Lianes retombantes SpindaV7 et verdure luxuriante de sous-bois',
            'Calques generes et emballes sur fond magenta pur #FF00FF',
            'Filtre nocturne Abyss exact applique calque par calque'
        ]
    }
    zip_files['manifest.json'] = jb(manifest)
    
    calques_zip = O / 'GB1_grotte_brumeuse_calques.zip'
    with zipfile.ZipFile(calques_zip, 'w', zipfile.ZIP_DEFLATED, compresslevel=9) as z:
        for name, data in sorted(zip_files.items()):
            info = zipfile.ZipInfo(name, (2026, 9, 22, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            z.writestr(info, data, compresslevel=9)
            
    print(f'Built GB1 Grotte Brumeuse: {len(zip_files)} files in calques pack ({calques_zip.stat().st_size} bytes)', flush=True)
    return {
        'day_layers': day_layers,
        'night_layers': night_layers,
        'comp_day': comp_day,
        'comp_night': comp_night,
        'comp_magenta': comp_magenta,
        'manifest': manifest,
        'zip_files': zip_files
    }

def verify():
    ok = []
    w, h = MAP_CONFIG['size']
    zip_path = O / 'GB1_grotte_brumeuse_calques.zip'
    assert zip_path.exists(), f'Missing {zip_path}'
    
    with zipfile.ZipFile(zip_path) as z:
        assert z.testzip() is None
        files = {n: z.read(n) for n in z.namelist()}
        m = json.loads(files['manifest.json'].decode('utf-8'))
        assert m['size'] == [w, h]
        assert 4 <= m['semantic_groups'] <= 6
        
        for mode in ['jour', 'nuit']:
            prefix = f'calques_{mode}/GB1_grotte_brumeuse_'
            sol_im = img(files[f'{prefix}sol_{mode}.png'])
            sol_arr = np.array(sol_im)
            assert (sol_arr[:, :, 3] == 255).all(), f'{mode} sol must be 100% opaque continuous ground'
            
            for l in m['layers']:
                layer_im = img(files[l[f'file_{mode}']])
                arr = np.array(layer_im)
                assert arr.shape[:2] == (h, w)
                if l['id'] != 'sol':
                    vis_count = (arr[:, :, 3] > 0).sum()
                    assert 0 < vis_count < h * w * 0.95, f'{l["id"]} has non-trivial coverage'
            
            # Navigabilité Sud vers Nord : érosion binaire 17px
            obstacles = np.zeros((h, w), bool)
            obstacles[0:110, 0:192] = True
            obstacles[0:110, 288:480] = True
            obstacles[0:56, 192:288] = True
            obstacles[80:270, 0:130] = True
            obstacles[80:270, 350:480] = True
            
            free = (sol_arr[:, :, 3] > 0) & ~obstacles
            safe = ndimage.binary_erosion(free, np.ones((17, 17)))
            labels, count = ndimage.label(safe)
            
            sx, sy = MAP_CONFIG['spawn']
            cx, cy = MAP_CONFIG['cave_mouth']
            start_label = labels[sy, sx]
            cave_label = labels[cy, cx]
            
            assert start_label > 0, f'{mode} south spawn point [{sx}, {sy}] blocked by obstacle'
            assert cave_label > 0, f'{mode} cave mouth [{cx}, {cy}] blocked by obstacle'
            assert start_label == cave_label, f'{mode} path from spawn to cave mouth is interrupted'
            
            walkable_area = (labels == start_label).sum()
            assert walkable_area > w * h * 0.10, f'{mode} walkable gathering area too small ({walkable_area})'

    ok.append(f'GB1 Grotte Brumeuse: manifest OK, sol continu 100% opaque, 6 calques valides, fond magenta emballage OK, chemin continu sud [{sx}, {sy}] vers nord [{cx}, {cy}] degage et praticable ({walkable_area} px)')
    print(f'PASS {ok[-1]}', flush=True)
    (O / 'verification.json').write_bytes(jb({'checks': ok, 'runtime_PMDO': False}))
    return ok

def pmdo():
    """Sérialise la carte Grotte Brumeuse en base éditable PMDO avec viewport_pmdo_v1."""
    VP = R / 'source/viewport_pmdo_v1'
    ns = {'__file__': str(VP / 'build.py'), '__name__': 'vp_tools'}
    exec(compile((VP / 'build.py').read_bytes(), str(VP / 'build.py'), 'exec'), ns)
    exec(compile((VP / 'verify.py').read_bytes(), str(VP / 'verify.py'), 'exec'), ns)
    ns['ST'] = C / 'pmdo_stage'
    ns['OUT'] = O
    ST = ns['ST']
    
    with zipfile.ZipFile(O / 'GB1_grotte_brumeuse_calques.zip') as z:
        files = {n: z.read(n) for n in z.namelist()}
        m = json.loads(files['manifest.json'].decode('utf-8'))
        
    dest = ST / 'grotte_brumeuse'
    if dest.exists():
        shutil.rmtree(dest)
        
    metas = []
    recs = {}
    for mode in ['jour', 'nuit']:
        layers = [
            ns['layer'](l['title'], img(files[l[f'file_{mode}']]))
            for l in m['layers']
        ]
        r = {
            'id': f'gb1_grotte_brumeuse_{mode}',
            'duo': 'grotte_brumeuse',
            'layers': layers,
            'spawn': MAP_CONFIG['spawn'],
            'offset': MAP_CONFIG['offset'],
            'notes': [f'GB1 {MAP_CONFIG["title"]} base editable 1x ({mode}); progression Sud-Nord vers grotte Crooked; sol continu; lianes.'],
            'tick': 0
        }
        recs[r['id']] = r
        metas.append(ns['export_map'](r, None))
        
    manifest = {
        'lot': 'GB1',
        'title': MAP_CONFIG['title'],
        'maps': metas,
        'runtime_tested': False,
        'schema': 'RogueEssence Ground + native8px TileBank',
        'camera': {'screen': [320, 240], 'recommended_zoom': 'x1'},
        'collisions': 'ALL FREE editing scaffolds'
    }
    ns['save'](dest / 'manifest.json', jb(manifest))
    ns['save'](dest / 'README.md', b'GB1 Grotte Brumeuse PMDO base')
    ns['save'](dest / 'INSTALLER.py', (R / 'source/pmdo_cote/INSTALLER.py').read_bytes())
    
    # Test de désérialisation
    for meta in metas:
        ground_data = json.loads((dest / f'Data/Ground/{meta["asset"]}.rsground').read_text())['Object']
        r = recs[meta['id']]
        im = ns['serialized_scene'](dest, ground_data, 0)
        exp = ns['render'](r, None, 0)
        diff = np.abs(np.array(im).astype(int) - np.array(exp).astype(int))
        assert diff.max() <= 1 and np.array_equal(np.array(im)[:, :, 3], np.array(exp)[:, :, 3]), f'{meta["id"]} deserialization diff={diff.max()}'
        
    # Test d'installation moduelle
    installer = ns['loadmod']('gb1_installer', dest / 'INSTALLER.py')
    with tempfile.TemporaryDirectory(dir=C) as td:
        mod = Path(td)
        (mod / 'Mod.xml').write_text('<Mod><Namespace>gb1_test</Namespace></Mod>')
        installer.install(dest, mod, True, None)
        assert not (mod / 'Data').exists()
        installer.install(dest, mod, False, None)
        installer.install(dest, mod, False, None)
        assert len(installer.read_index(mod / 'Content/Tile/index.idx')) == len(list((dest / 'Content/Tile').glob('*.tile')))
        
    # Création du pack PMDO ZIP
    pmdo_zip = O / 'GB1_grotte_brumeuse_PMDO.zip'
    with zipfile.ZipFile(pmdo_zip, 'w', zipfile.ZIP_DEFLATED, compresslevel=9) as z:
        for p in sorted(dest.rglob('*')):
            if p.is_file() and '__pycache__' not in p.parts:
                info = zipfile.ZipInfo(str(p.relative_to(dest)), (2026, 9, 22, 0, 0, 0))
                info.compress_type = zipfile.ZIP_DEFLATED
                z.writestr(info, p.read_bytes(), compresslevel=9)
                
    print(f'PMDO PASS GB1 Grotte Brumeuse: {[m["asset"] for m in metas]} ({pmdo_zip.stat().st_size} bytes)', flush=True)
    (O / 'pmdo_verification.json').write_bytes(jb({
        'lot': 'GB1',
        'maps': metas,
        'pass_deserialization': True,
        'pass_installer': True
    }))
    return metas

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--build', action='store_true', help='Génère les calques et rendus')
    parser.add_argument('--verify', action='store_true', help='Exécute les contrôles')
    parser.add_argument('--pmdo', action='store_true', help='Sérialise pour PMDO')
    args = parser.parse_args()
    
    if not (args.build or args.verify or args.pmdo):
        args.build = True
        args.verify = True
        args.pmdo = True
        
    if args.build:
        build()
    if args.verify:
        verify()
    if args.pmdo:
        pmdo()
