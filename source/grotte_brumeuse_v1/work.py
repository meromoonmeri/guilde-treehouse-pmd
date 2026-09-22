#!/usr/bin/env python3
"""GB1 — Grotte Brumeuse PMDO : Forêt style Foggy Forest & Grotte Crooked Cavern harmonisée.
Progression Sud vers Nord avec entrée rocheuse drapée de lianes et verdure.
--build   : génère les calques bruts magenta, calques transparents, planches, aperçus viewport, packs ZIP et WebP
--verify  : contrôle d'intégrité, opacité du sol, guides magenta, navigabilité 17px Sud->Nord
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
    'title': 'Grotte Brumeuse (Foggy Forest & Crooked Cavern)',
    'size': (480, 336),
    'tiles_grid': (60, 42),
    'spawn': [240, 296],
    'cave_portal': [240, 95],
    'offset': [0, -40],
    'layers_def': [
        {'id': '01_sol', 'title': '01 - Sol clairiere et seuil de grotte (100% opaque)'},
        {'id': '02_parois_grotte_crooked', 'title': '02 - Parois rocheuses et arche Crooked Cavern harmonisee'},
        {'id': '03_arbres_lisiere_fond', 'title': '03 - Arbres de lisiere et sous-bois Foggy Forest'},
        {'id': '04_lianes_et_verdure', 'title': '04 - Lianes suspendues tombantes et buissons moussus'},
        {'id': '05_canopee_avant_plan', 'title': '05 - Canopee haute de frondaisons avant-plan'},
        {'id': '06_brume_atmospherique', 'title': '06 - Voile de brume et rai de lumiere dore'}
    ]
}

MAGENTA = (255, 0, 255)

def img(b):
    return Image.open(io.BytesIO(b) if isinstance(b, (bytes, bytearray)) else b).convert('RGBA')

def png(im):
    b = io.BytesIO()
    im.save(b, format='PNG', optimize=True)
    return b.getvalue()

def jb(obj):
    return json.dumps(obj, indent=2, ensure_ascii=False).encode('utf-8')

def apply_magenta_bg(im_rgba):
    """Place une image RGBA sur un fond magenta pur #FF00FF pour isolation et audit."""
    bg = Image.new('RGB', im_rgba.size, MAGENTA)
    bg.paste(im_rgba, (0, 0), im_rgba)
    return bg

def keyout_magenta(im_rgb):
    """Convertit un calque avec fond magenta pur en RGBA transparent 32-bit sans résidu."""
    arr = np.array(im_rgb)
    is_mag = (arr[:, :, 0] == 255) & (arr[:, :, 1] == 0) & (arr[:, :, 2] == 255)
    rgba = np.dstack([arr[:, :, :3], np.where(is_mag, 0, 255).astype(np.uint8)])
    return Image.fromarray(rgba)

def harmonize_crooked_rock(im_rgba):
    """Harmonise la roche de Crooked Cavern vers la palette pierre/mousse de Foggy Forest."""
    arr = np.array(im_rgba).copy()
    rgb = arr[:, :, :3].astype(float)
    lum = (0.299 * rgb[:, :, 0] + 0.587 * rgb[:, :, 1] + 0.114 * rgb[:, :, 2]) / 255.0
    
    # Courbe tonale pierre moussue canonique
    r = (lum * 135 + 36).clip(0, 255).astype(np.uint8)
    g = (lum * 162 + 48).clip(0, 255).astype(np.uint8)
    b = (lum * 110 + 34).clip(0, 255).astype(np.uint8)
    
    # Préservation des fissures sombres
    dark = (lum < 0.25)
    r[dark] = (rgb[dark, 0] * 0.75 + 10).clip(0, 255).astype(np.uint8)
    g[dark] = (rgb[dark, 1] * 0.85 + 15).clip(0, 255).astype(np.uint8)
    b[dark] = (rgb[dark, 2] * 0.70 + 10).clip(0, 255).astype(np.uint8)
    
    # Quantification 5-bit GBA (multiples de 8)
    r = (r // 8) * 8
    g = (g // 8) * 8
    b = (b // 8) * 8
    
    return Image.fromarray(np.dstack([r, g, b, arr[:, :, 3]]))

def generate_layers_day():
    w, h = MAP_CONFIG['size']
    
    # Sources canoniques
    ff_raw = Image.open(R / 'Foggy_Forest_Base_Camp_TDS.png').convert('RGBA')
    cc_raw = Image.open(R / 'source/cote_v5_expeditions/audit/Halcyon__crooked_cavern_entrance_layer_0.png').convert('RGBA')
    liane_raw = Image.open(R / 'renders/cafe_spinda_revisite_v7/assets/SpindaV7_liane.png').convert('RGBA')
    
    # -------------------------------------------------------------
    # BASE FORET ET EXTRACTION ARBRES/SOL
    # -------------------------------------------------------------
    # Sentier et clairière Sud Foggy Forest (y=480..792, x=60..540)
    ff_path_crop = ff_raw.crop((60, 480, 540, 792))
    sol_base = Image.new('RGBA', (w, h), (0, 0, 0, 255))
    sol_base.paste(ff_path_crop, (0, 24))
    sol_base.paste(ff_path_crop.crop((0, 0, w, 24)), (0, 0))

    # Masque organique arrondi des arbres en lisière
    t_mask_im = Image.new('L', (w, h), 0)
    d_tm = ImageDraw.Draw(t_mask_im)
    d_tm.ellipse([70, 140, 155, 218], fill=255)
    d_tm.ellipse([70, 240, 155, 318], fill=255)
    d_tm.ellipse([0, 160, 48, 238], fill=255)
    d_tm.ellipse([325, 140, 410, 218], fill=255)
    d_tm.ellipse([325, 240, 410, 318], fill=255)
    d_tm.ellipse([432, 160, 480, 238], fill=255)
    tree_mask = np.array(t_mask_im) > 0

    arr_base = np.array(sol_base)

    # CALQUE 3 : Arbres de lisière isolés
    l_arbres_arr = np.zeros((h, w, 4), dtype=np.uint8)
    l_arbres_arr[tree_mask] = arr_base[tree_mask]
    l_arbres = Image.fromarray(l_arbres_arr)

    # CALQUE 1 : Sol continu 100% opaque sous les arbres
    sol_clean = arr_base.copy()
    inds = ndimage.distance_transform_edt(tree_mask, return_distances=False, return_indices=True)
    sol_clean[tree_mask] = arr_base[inds[0, tree_mask], inds[1, tree_mask]]

    # Nettoyage des reliquats de tentes au nord
    turf_patch = sol_clean[50:95, 180:220]
    sol_clean[0:45, 80:160] = np.tile(turf_patch, (1, 2, 1))[:45, :80]
    sol_clean[0:45, 320:420] = np.tile(turf_patch, (1, 3, 1))[:45, :100]

    # Dégradé seuil et antre sombre sous l'arche de la grotte (y: 65..120, x: 212..268)
    for y_pos in range(65, 120):
        ratio = (120 - y_pos) / 55.0
        dark_shade = np.array([35, 42, 32], dtype=float)
        earth_shade = np.array([110, 130, 95], dtype=float)
        target = (dark_shade * ratio + earth_shade * (1.0 - ratio)).astype(np.uint8)
        target = (target // 8) * 8
        sol_clean[y_pos, 212:268, :3] = target

    l_sol = Image.fromarray(sol_clean)

    # -------------------------------------------------------------
    # CALQUE 2 : Parois rocheuses et arche Crooked Cavern harmonisée
    # -------------------------------------------------------------
    # Silhouette canonique de falaise Crooked Cavern
    S_poly = (320, 240)
    ground_mask = Image.new('L', S_poly, 0)
    d_poly = ImageDraw.Draw(ground_mask)
    poly = [(0,219),(17,211),(28,187),(48,176),(65,158),(88,150),(108,137),(123,126),(141,119),(166,118),(187,130),(204,143),(222,159),(243,176),(261,184),(280,205),(300,219),(320,231),(320,240),(0,240)]
    d_poly.polygon(poly, fill=255)

    cc_arr = np.array(cc_raw)
    rock_alpha = np.where(np.array(ground_mask) == 0, 255, 0).astype(np.uint8)
    cc_arr[:, :, 3] = rock_alpha
    rock_cc = Image.fromarray(cc_arr)
    harm_rock = harmonize_crooked_rock(rock_cc)

    # Assemblage falaise continue sur 480 px avec extensions miroirs
    l_parois = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    l_parois.paste(harm_rock, (80, 0), harm_rock)
    left_ext = harm_rock.crop((0, 0, 80, 240)).transpose(Image.FLIP_LEFT_RIGHT)
    l_parois.paste(left_ext, (0, 0), left_ext)
    right_ext = harm_rock.crop((240, 0, 320, 240)).transpose(Image.FLIP_LEFT_RIGHT)
    l_parois.paste(right_ext, (400, 0), right_ext)

    # Découpe de l'ouverture voûtée du portail (laisse passer le joueur)
    p_arr = np.array(l_parois)
    mask_hole = Image.new('L', (w, h), 255)
    d_hole = ImageDraw.Draw(mask_hole)
    d_hole.rectangle([212, 85, 268, 125], fill=0)
    d_hole.ellipse([212, 68, 268, 98], fill=0)
    p_arr[:, :, 3] = (p_arr[:, :, 3].astype(float) * (np.array(mask_hole) / 255.0)).astype(np.uint8)
    l_parois = Image.fromarray(p_arr)

    # -------------------------------------------------------------
    # CALQUE 4 : Lianes suspendues tombantes et buissons moussus
    # -------------------------------------------------------------
    l_lianes = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    liane_flip = liane_raw.transpose(Image.FLIP_LEFT_RIGHT)
    liane_short = liane_raw.crop((0, 0, 32, 40))

    # Lianes drapées sur les stalactites de l'arche et corniches
    l_lianes.alpha_composite(liane_raw, (198, 28))
    l_lianes.alpha_composite(liane_flip, (252, 26))
    l_lianes.alpha_composite(liane_short, (226, 18))

    # Lianes sur les gradins rocheux latéraux
    l_lianes.alpha_composite(liane_flip, (135, 24))
    l_lianes.alpha_composite(liane_raw, (315, 24))
    l_lianes.alpha_composite(liane_raw, (50, 40))
    l_lianes.alpha_composite(liane_flip, (400, 40))

    # Buissons moussus Foggy Forest canoniques le long du pied de falaise
    bush_raw = ff_raw.crop((125, 475, 157, 502)) # 32x27
    b_mask = Image.new('L', (32, 27), 0)
    d_b = ImageDraw.Draw(b_mask)
    d_b.ellipse([2, 2, 29, 24], fill=255)
    b_arr = np.array(bush_raw)
    b_arr[:, :, 3] = np.array(b_mask)
    native_bush = Image.fromarray(b_arr)

    l_lianes.alpha_composite(native_bush, (168, 115))
    l_lianes.alpha_composite(native_bush.transpose(Image.FLIP_LEFT_RIGHT), (280, 115))
    l_lianes.alpha_composite(native_bush, (110, 138))
    l_lianes.alpha_composite(native_bush.transpose(Image.FLIP_LEFT_RIGHT), (338, 138))
    l_lianes.alpha_composite(native_bush, (50, 175))
    l_lianes.alpha_composite(native_bush.transpose(Image.FLIP_LEFT_RIGHT), (398, 175))

    # -------------------------------------------------------------
    # CALQUE 5 : Canopée haute avant-plan
    # -------------------------------------------------------------
    l_canopee = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    canopy_src = ff_raw.crop((60, 10, 540, 74))
    c_mask = Image.new('L', (w, 64), 0)
    d_c = ImageDraw.Draw(c_mask)
    pts = [(0, 0), (w, 0), (w, 36), (400, 30), (320, 20), (240, 14), (160, 20), (80, 30), (0, 36)]
    d_c.polygon(pts, fill=255)
    c_arr = np.array(canopy_src)
    c_arr[:, :, 3] = np.array(c_mask)
    l_canopee.paste(Image.fromarray(c_arr), (0, 0))

    # -------------------------------------------------------------
    # CALQUE 6 : Voile de brume atmosphérique
    # -------------------------------------------------------------
    yy, xx = np.mgrid[:h, :w]
    b1 = np.exp(-((yy - 120) / 45.0) ** 2) * 0.7
    b2 = np.exp(-((yy - 200) / 60.0) ** 2) * 0.5
    dr = 0.8 + 0.2 * np.sin(xx / 40.0) * np.cos(yy / 30.0)
    alpha = (((b1 + b2) * dr).clip(0, 1.0) * 45).astype(np.uint8)
    alpha[alpha < 8] = 0 # Découpe nette de la nappe
    l_brume = Image.fromarray(np.dstack([
        np.full((h, w), 175, dtype=np.uint8),
        np.full((h, w), 195, dtype=np.uint8),
        np.full((h, w), 150, dtype=np.uint8),
        alpha
    ]))

    return {
        '01_sol': l_sol,
        '02_parois_grotte_crooked': l_parois,
        '03_arbres_lisiere_fond': l_arbres,
        '04_lianes_et_verdure': l_lianes,
        '05_canopee_avant_plan': l_canopee,
        '06_brume_atmospherique': l_brume
    }

def compose_scene(layers_dict, order_ids):
    first = layers_dict[order_ids[0]]
    out = Image.new('RGBA', first.size, (0, 0, 0, 0))
    for lid in order_ids:
        out.alpha_composite(layers_dict[lid])
    return out

def build_board(title, layers_dict, order_ids, comp_im, bg_color='#1e242b'):
    w, h = comp_im.size
    panels = [(lid, layers_dict[lid]) for lid in order_ids] + [('composition_finale', comp_im)]
    cols = 2
    rows = (len(panels) + 1) // 2
    out = Image.new('RGB', (cols * w, rows * (h + 32)), bg_color)
    draw = ImageDraw.Draw(out)
    for j, (name, im) in enumerate(panels):
        x = (j % cols) * w
        y = (j // cols) * (h + 32)
        draw.text((x + 12, y + 8), f'{title} — {name}', fill='#e2e8f0')
        bg = Image.new('RGBA', (w, h), '#2d3748')
        bg.alpha_composite(im)
        out.paste(bg.convert('RGB'), (x, y + 32))
    return out

def build_magenta_board(title, magenta_dict, order_ids):
    first = magenta_dict[order_ids[0]]
    w, h = first.size
    panels = [(lid, magenta_dict[lid]) for lid in order_ids]
    cols = 2
    rows = (len(panels) + 1) // 2
    out = Image.new('RGB', (cols * w, rows * (h + 32)), '#1e242b')
    draw = ImageDraw.Draw(out)
    for j, (name, im) in enumerate(panels):
        x = (j % cols) * w
        y = (j // cols) * (h + 32)
        draw.text((x + 12, y + 8), f'{title} — {name} [Fond Magenta #FF00FF]', fill='#f472b6')
        out.paste(im, (x, y + 32))
    return out

def build_viewport(comp_im, spawn, portal, screen_size=(320, 240)):
    sw, sh = screen_size
    w, h = comp_im.size
    sx, sy = spawn
    px, py = portal
    cx = max(0, min(w - sw, sx - sw // 2))
    cy = max(0, min(h - sh, sy - sh // 2))

    view_crop = comp_im.crop((cx, cy, cx + sw, cy + sh))
    frame = Image.new('RGB', (w, h + 32), '#1a202c')
    draw = ImageDraw.Draw(frame)
    draw.text((12, 8), f'Viewport Camera 320x240 (x1) — Focus Spawn Sud [{sx}, {sy}] -> Grotte [{px}, {py}]', fill='#fbbf24')
    frame.paste(comp_im.convert('RGB'), (0, 32))
    
    box_draw = ImageDraw.Draw(frame)
    box_draw.rectangle([cx, cy + 32, cx + sw, cy + 32 + sh], outline='#f59e0b', width=2)
    box_draw.ellipse([sx - 5, sy + 32 - 5, sx + 5, sy + 32 + 5], fill='#22c55e', outline='#ffffff', width=2)
    box_draw.ellipse([px - 5, py + 32 - 5, px + 5, py + 32 + 5], fill='#3b82f6', outline='#ffffff', width=2)
    box_draw.line([(sx, sy + 32), (px, py + 32)], fill='#fbbf24', width=2)
    
    return frame, view_crop

def build():
    O.mkdir(parents=True, exist_ok=True)
    (O / 'bruts_magenta').mkdir(parents=True, exist_ok=True)
    (O / 'calques_jour').mkdir(parents=True, exist_ok=True)
    (O / 'calques_nuit').mkdir(parents=True, exist_ok=True)
    C.mkdir(parents=True, exist_ok=True)

    order_ids = [l['id'] for l in MAP_CONFIG['layers_def']]
    w, h = MAP_CONFIG['size']

    # 1. Génération des calques jour
    day_layers = generate_layers_day()

    # 2. Génération des calques sur fond magenta pur #FF00FF (exigence guide)
    magenta_layers = {}
    for lid in order_ids:
        mag_im = apply_magenta_bg(day_layers[lid])
        magenta_layers[lid] = mag_im
        (O / f'bruts_magenta/GB1_grotte_brumeuse_{lid}_magenta.png').write_bytes(png(mag_im))

    board_mag = build_magenta_board('GB1 Grotte Brumeuse', magenta_layers, order_ids)
    (O / 'GB1_grotte_brumeuse_planche_magenta.png').write_bytes(png(board_mag))

    # 3. Export des calques jour avec alpha propre (emballage final)
    for lid in order_ids:
        (O / f'calques_jour/GB1_grotte_brumeuse_{lid}_jour.png').write_bytes(png(day_layers[lid]))

    # 4. Génération des calques nuit via transformation canonique Abyss
    night_layers = {}
    for lid in order_ids:
        if lid == '01_sol':
            sol_nuit_arr = np.array(night(day_layers[lid]))
            sol_nuit_arr[:, :, 3] = 255 # Force 100% opaque
            night_layers[lid] = Image.fromarray(sol_nuit_arr)
        else:
            night_layers[lid] = night(day_layers[lid])
        (O / f'calques_nuit/GB1_grotte_brumeuse_{lid}_nuit.png').write_bytes(png(night_layers[lid]))

    # 5. Compositions finales
    comp_day = compose_scene(day_layers, order_ids)
    comp_night = compose_scene(night_layers, order_ids)

    (O / 'GB1_grotte_brumeuse_carte_jour.png').write_bytes(png(comp_day))
    (O / 'GB1_grotte_brumeuse_carte_nuit.png').write_bytes(png(comp_night))
    (O / 'GB1_grotte_brumeuse_carte.png').write_bytes(png(comp_day))

    # Planche calques transparents + composite
    board_day = build_board('GB1 Grotte Brumeuse (Jour)', day_layers, order_ids, comp_day)
    (O / 'GB1_grotte_brumeuse_calques.png').write_bytes(png(board_day))

    # Viewport 320x240 PMDO
    vp_frame, vp_crop = build_viewport(comp_day, MAP_CONFIG['spawn'], MAP_CONFIG['cave_portal'])
    (O / 'GB1_grotte_brumeuse_viewport.png').write_bytes(png(vp_frame))
    (O / 'GB1_grotte_brumeuse_viewport_320x240.png').write_bytes(png(vp_crop))

    # WebP animé transition jour/nuit (2000 ms boucle continue)
    anim_path = O / 'GB1_grotte_brumeuse_ambiances.webp'
    comp_day.convert('RGB').save(
        anim_path,
        save_all=True,
        append_images=[comp_night.convert('RGB')],
        duration=[2000, 2000],
        loop=0,
        lossless=True
    )

    # 6. Emballage du pack ZIP Calques complet
    zip_files = {}
    for lid in order_ids:
        zip_files[f'bruts_magenta/GB1_grotte_brumeuse_{lid}_magenta.png'] = png(magenta_layers[lid])
        zip_files[f'calques_jour/GB1_grotte_brumeuse_{lid}_jour.png'] = png(day_layers[lid])
        zip_files[f'calques_nuit/GB1_grotte_brumeuse_{lid}_nuit.png'] = png(night_layers[lid])
    zip_files['GB1_grotte_brumeuse_carte_jour.png'] = png(comp_day)
    zip_files['GB1_grotte_brumeuse_carte_nuit.png'] = png(comp_night)
    zip_files['GB1_grotte_brumeuse_planche_magenta.png'] = png(board_mag)

    manifest = {
        'lot': 'GB1',
        'id': MAP_CONFIG['id'],
        'title': MAP_CONFIG['title'],
        'theme': 'Foggy Forest avec entree Crooked Cavern rocheuse harmonisee, lianes suspendues et verdure',
        'progression': 'Sud vers Nord (clairiere ouverte vers seuil de grotte rocheuse)',
        'size': list(MAP_CONFIG['size']),
        'tiles_grid': list(MAP_CONFIG['tiles_grid']),
        'semantic_groups': len(order_ids),
        'spawn_point': MAP_CONFIG['spawn'],
        'cave_portal': MAP_CONFIG['cave_portal'],
        'camera_offset': MAP_CONFIG['offset'],
        'layers': [
            {
                'id': l['id'],
                'title': l['title'],
                'file_magenta': f'bruts_magenta/GB1_grotte_brumeuse_{l["id"]}_magenta.png',
                'file_jour': f'calques_jour/GB1_grotte_brumeuse_{l["id"]}_jour.png',
                'file_nuit': f'calques_nuit/GB1_grotte_brumeuse_{l["id"]}_nuit.png'
            }
            for l in MAP_CONFIG['layers_def']
        ],
        'notes': [
            'Calques bruts d abord generes sur fond magenta pur #FF00FF pour isolation pixel perfect',
            'Emballage final avec alpha propre 32-bit sans residu magenta',
            'Sol 01 continu 100% opaque sous les falaises et troncs pour eviter toute lacune alpha',
            'Texture rocheuse Crooked Cavern harmonisee ton sur ton avec la clairiere moussue Foggy Forest',
            'Lianes PMD SpindaV7 drapees sur l arche et gradins rocheux avec buissons moussus canoniques',
            'Parcours Sud->Nord verifie par erosion binaire 17px'
        ]
    }
    zip_files['manifest.json'] = jb(manifest)

    calques_zip_path = O / 'GB1_grotte_brumeuse_calques.zip'
    with zipfile.ZipFile(calques_zip_path, 'w', zipfile.ZIP_DEFLATED, compresslevel=9) as z:
        for name, data in sorted(zip_files.items()):
            info = zipfile.ZipInfo(name, (2026, 9, 22, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            z.writestr(info, data, compresslevel=9)

    print(f'Built GB1 Grotte Brumeuse: {len(zip_files)} files in calques pack ({calques_zip_path.stat().st_size} bytes)', flush=True)

    # 7. Génération du visualiseur interactif HTML
    viewer_py = S / 'build_viewer.py'
    if viewer_py.exists():
        ns_v = {'__file__': str(viewer_py), '__name__': '__viewer__'}
        exec(compile(viewer_py.read_bytes(), str(viewer_py), 'exec'), ns_v)
        ns_v['main']()

    return {
        'day_layers': day_layers,
        'magenta_layers': magenta_layers,
        'night_layers': night_layers,
        'comp_day': comp_day,
        'comp_night': comp_night,
        'manifest': manifest
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

        # Vérification des guides magenta
        for l in m['layers']:
            mag_im = img(files[l['file_magenta']])
            assert mag_im.size == (w, h)
            mag_arr = np.array(mag_im)
            is_pure_mag = (mag_arr[:, :, 0] == 255) & (mag_arr[:, :, 1] == 0) & (mag_arr[:, :, 2] == 255)
            if l['id'] != '01_sol':
                assert is_pure_mag.sum() > 0, f'{l["id"]} doit contenir du fond magenta pur'

        # Vérification des calques transparents jour et nuit
        for mode in ['jour', 'nuit']:
            prefix = f'calques_{mode}/GB1_grotte_brumeuse_'
            sol_im = img(files[f'{prefix}01_sol_{mode}.png'])
            sol_arr = np.array(sol_im)
            assert (sol_arr[:, :, 3] == 255).all(), f'{mode} 01_sol doit etre 100% opaque sans lacune'

            for l in m['layers']:
                arr = np.array(img(files[l[f'file_{mode}']]))
                assert arr.shape[:2] == (h, w)
                if l['id'] != '01_sol':
                    vis_count = (arr[:, :, 3] > 0).sum()
                    max_ratio = 0.95 if 'brume' in l['id'] else 0.85
                    assert 0 < vis_count <= h * w * max_ratio, f'{l["id"]} couverture invalide ({vis_count})'

        # Vérification de la navigabilité Sud -> Nord (érosion 17px)
        sol_arr = np.array(img(files['calques_jour/GB1_grotte_brumeuse_01_sol_jour.png']))
        parois_arr = np.array(img(files['calques_jour/GB1_grotte_brumeuse_02_parois_grotte_crooked_jour.png']))
        arbres_arr = np.array(img(files['calques_jour/GB1_grotte_brumeuse_03_arbres_lisiere_fond_jour.png']))

        obstacles = (parois_arr[:, :, 3] > 0) | (arbres_arr[:, :, 3] > 0)
        free = (sol_arr[:, :, 3] > 0) & ~obstacles
        safe = ndimage.binary_erosion(free, np.ones((17, 17)))
        labels, count = ndimage.label(safe)

        sx, sy = MAP_CONFIG['spawn']
        px, py = MAP_CONFIG['cave_portal']
        start_label = labels[sy, sx]
        portal_label = labels[py, px]

        assert start_label > 0, f'Spawn [{sx}, {sy}] bloque par un obstacle'
        assert portal_label > 0, f'Portail grotte [{px}, {py}] bloque par un obstacle'
        assert start_label == portal_label, f'Le parcours Sud [{sx},{sy}] vers Nord [{px},{py}] est coupe !'

        walkable_area = (labels == start_label).sum()
        assert walkable_area > w * h * 0.15, f'Zone praticable trop petite ({walkable_area})'

    ok.append(f'GB1 Grotte Brumeuse: manifest OK, guides magenta conformes, sol 100% opaque, 6 calques valides, navigabilite Sud->Nord verifiee 17px ({walkable_area} px)')
    print(f'PASS {ok[-1]}', flush=True)

    (O / 'verification.json').write_bytes(jb({'checks': ok, 'walkable_area_px': int(walkable_area)}))
    return ok

def pmdo():
    """Sérialise la map Grotte Brumeuse en base PMDO 0.8.12 (.rsground et .tile)."""
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
            'notes': [f'GB1 Grotte Brumeuse base editable 1x ({mode}); progression Sud->Nord; lianes et verdure.'],
            'tick': 0
        }
        recs[r['id']] = r
        metas.append(ns['export_map'](r, None))

    manifest = {
        'area_id': 'grotte_brumeuse',
        'lot': 'GB1',
        'title': MAP_CONFIG['title'],
        'maps': metas,
        'runtime_tested': False,
        'schema': 'RogueEssence Ground + native8px TileBank',
        'camera': {'screen': [320, 240], 'recommended_zoom': 'x1'},
        'collisions': 'ALL FREE editing scaffolds'
    }
    ns['save'](dest / 'manifest.json', jb(manifest))
    ns['save'](dest / 'README.md', b'GB1 Grotte Brumeuse PMDO base 0.8.12')
    ns['save'](dest / 'INSTALLER.py', (R / 'source/pmdo_cote/INSTALLER.py').read_bytes())

    # Vérification de désérialisation
    for meta in metas:
        ground_data = json.loads((dest / f'Data/Ground/{meta["asset"]}.rsground').read_text())['Object']
        r = recs[meta['id']]
        im = ns['serialized_scene'](dest, ground_data, 0)
        exp = ns['render'](r, None, 0)
        diff = np.abs(np.array(im).astype(int) - np.array(exp).astype(int))
        assert diff.max() <= 2 and np.array_equal(np.array(im)[:, :, 3], np.array(exp)[:, :, 3]), f'{meta["id"]} diff={diff.max()}'

    # Test installateur dry-run et réinstallation
    installer = ns['loadmod']('gb1_installer', dest / 'INSTALLER.py')
    with tempfile.TemporaryDirectory(dir=C) as td:
        mod = Path(td)
        (mod / 'Mod.xml').write_text('<Mod><Namespace>gb1_test</Namespace></Mod>')
        installer.install(dest, mod, True, None)
        assert not (mod / 'Data').exists()
        installer.install(dest, mod, False, None)
        installer.install(dest, mod, False, None)
        assert len(installer.read_index(mod / 'Content/Tile/index.idx')) == len(list((dest / 'Content/Tile').glob('*.tile')))

    # Emballage ZIP PMDO
    pmdo_zip_path = O / 'GB1_grotte_brumeuse_PMDO.zip'
    with zipfile.ZipFile(pmdo_zip_path, 'w', zipfile.ZIP_DEFLATED, compresslevel=9) as z:
        for p in sorted(dest.rglob('*')):
            if p.is_file() and '__pycache__' not in p.parts:
                info = zipfile.ZipInfo(str(p.relative_to(dest)), (2026, 9, 22, 0, 0, 0))
                info.compress_type = zipfile.ZIP_DEFLATED
                z.writestr(info, p.read_bytes(), compresslevel=9)

    report = [m['asset'] for m in metas]
    print(f'PMDO PASS grotte_brumeuse: {report} ({pmdo_zip_path.stat().st_size} bytes)', flush=True)

    (O / 'pmdo_verification.json').write_bytes(jb({
        'pmdo_maps': report,
        'zip_size_bytes': pmdo_zip_path.stat().st_size,
        'verified_deserialization': True
    }))
    return report

def main():
    p = argparse.ArgumentParser()
    p.add_argument('--build', action='store_true')
    p.add_argument('--verify', action='store_true')
    p.add_argument('--pmdo', action='store_true')
    args = p.parse_args()

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

if __name__ == '__main__':
    main()
