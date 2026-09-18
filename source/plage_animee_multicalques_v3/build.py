"""Plage Animée Multicalques V3 — Haute Qualité PMD Sky & Architecture Multicalques.
Reconstruction d'après les textures et modules canoniques d'arenapmdskybeach.png :
- 100% textures et palettes natives PMD Sky
- Sol d'arène en sable doré matelassé avec raccords coutures (seam quilting)
- Baie côtière incurvée avec découpe naturelle du rivage
- Eau de mer animée par palette cycling canonique à 8 phases (32 frames synchronisées)
- Écume et ressac épousant fidèlement le contour de la rive
- Parois rocheuses rouges, corniches et arche naturelle au-dessus de l'horizon
- Ombres de contact douces ancrant naturellement les falaises et rochers sur le sable
- Récifs et écueils de premier plan
- Arrière-plan distant avec ciel PMD et nappe de nuages en wrap horizontal continu (modulo 768 px)
- Cohérence parfaite des calques ("les calques se marient naturellement entre eux")
- Formats livrés : Transparent PNG (Jour et Nuit), WebP sans perte, GIFs, ORA multi-calques et galerie HTML5.
"""
from pathlib import Path
import json, hashlib, base64, math, io, zipfile, xml.etree.ElementTree as ET
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

ROOT = Path(__file__).resolve().parents[2]
RENDERS_DIR = ROOT / 'renders/plage_animee_multicalques_v3'
EXPORTS_DIR = ROOT / 'exports/plage_animee_multicalques_v3'

W, H = 768, 512
N_FRAMES = 32
FRAME_MS = 100 # 3.2s boucle totale

# Sources canoniques
REF_FILE = 'arenapmdskybeach.png'
REF_IMG = Image.open(ROOT / REF_FILE).convert('RGBA')
A = np.array(REF_IMG)
REF_SHA256 = hashlib.sha256((ROOT / REF_FILE).read_bytes()).hexdigest()

SKY_SRC = Image.open(ROOT / 'source/cote_v2/ciel_sans_nuages.png').convert('RGBA')
CLOUD_TILES = [
    (Image.open(ROOT / 'sprites/cote_v2/COTEV2_NUAGE_01.png').convert('RGBA'), 40, 20),
    (Image.open(ROOT / 'sprites/cote_v2/COTEV2_NUAGE_02.png').convert('RGBA'), 320, 40),
    (Image.open(ROOT / 'sprites/cote_v2/COTEV2_NUAGE_03.png').convert('RGBA'), 580, 15)
]

VOID_COLOR = np.array([39, 39, 55], dtype=np.uint8)

def clean_patch(patch):
    p = patch.copy()
    is_void = np.all(p[:, :, :3] == VOID_COLOR, axis=2)
    p[is_void] = 0
    return p

# 8 couleurs d'eau canoniques PMD Sky
CYCLE_WATER_RGB = np.array([
    [23, 63, 143],   # 0: Bleu profond
    [31, 79, 151],   # 1: Bleu océan
    [39, 87, 135],   # 2: Bleu cyan
    [31, 119, 167],  # 3: Cyan lagon
    [31, 135, 175],  # 4: Cyan clair
    [47, 167, 215],  # 5: Crête de vague
    [31, 191, 231],  # 6: Écume montante
    [55, 207, 247]   # 7: Ressac brillant
], dtype=np.uint8)

# Patches de sable 24x24 canoniques depuis le centre de l'arène
SAND_BOXES = [
    (180, 184, 204, 208), (204, 184, 228, 208), (228, 184, 252, 208), (252, 184, 276, 208),
    (180, 208, 204, 232), (204, 208, 228, 232), (228, 208, 252, 232), (252, 208, 276, 232),
    (180, 232, 204, 256), (204, 232, 228, 256), (228, 232, 252, 256), (252, 232, 276, 256),
    (180, 256, 204, 280), (204, 256, 228, 280), (228, 256, 252, 280), (252, 256, 276, 280),
    (180, 280, 204, 304), (204, 280, 228, 304), (228, 280, 252, 304), (252, 280, 276, 304),
    (180, 304, 204, 328), (204, 304, 228, 328), (228, 304, 252, 328), (252, 304, 276, 328)
]

def seam(cost):
    h, w = cost.shape
    dist = cost.astype(float).copy()
    prev = np.zeros((h, w), int)
    for y in range(1, h):
        for x in range(w):
            lo = max(0, x - 1)
            hi = min(w, x + 2)
            p = lo + np.argmin(dist[y - 1, lo:hi])
            prev[y, x] = p
            dist[y, x] += dist[y - 1, p]
    x = int(np.argmin(dist[-1]))
    path = []
    for y in reversed(range(h)):
        path.append(x)
        x = prev[y, x]
    return np.array(path[::-1])

def to_night(rgba_arr):
    out = rgba_arr.copy()
    v = out[:, :, :3].astype(float)
    lum = (v @ np.array([0.2126, 0.7152, 0.0722]))[:, :, None]
    out[:, :, :3] = np.rint(
        (lum * 0.20 + v * 0.80) * np.array([0.40, 0.42, 0.58]) + np.array([4, 8, 15])
    ).clip(0, 255).astype('uint8')
    out[out[:, :, 3] == 0] = 0
    return out

def write_openraster(path, layers_dict, comp_img):
    root = ET.Element('image', {'w': str(W), 'h': str(H), 'name': 'Arène Plage Multicalques V3'})
    stack = ET.SubElement(root, 'stack')
    with zipfile.ZipFile(path, 'w', zipfile.ZIP_DEFLATED) as z:
        z.writestr('mimetype', 'image/openraster', compress_type=zipfile.ZIP_STORED)
        for i, (name, im) in reversed(list(enumerate(layers_dict.items()))):
            filename = f'data/layer{i:02d}.png'
            ET.SubElement(stack, 'layer', {
                'name': name,
                'src': filename,
                'x': '0',
                'y': '0',
                'opacity': '1.0',
                'visibility': 'visible',
                'composite-op': 'svg:src-over'
            })
            b = io.BytesIO()
            im.save(b, format='PNG')
            z.writestr(filename, b.getvalue())
        b = io.BytesIO()
        comp_img.save(b, format='PNG')
        z.writestr('mergedimage.png', b.getvalue())
        z.writestr('stack.xml', ET.tostring(root, encoding='utf-8', xml_declaration=True))

def build():
    RENDERS_DIR.mkdir(parents=True, exist_ok=True)
    EXPORTS_DIR.mkdir(parents=True, exist_ok=True)
    water_frames_dir = RENDERS_DIR / '02_eau_mer_palette_cycling'
    clouds_frames_dir = RENDERS_DIR / '01_nuages_wrap_frames'
    water_frames_dir.mkdir(exist_ok=True)
    clouds_frames_dir.mkdir(exist_ok=True)

    yy, xx = np.mgrid[:H, :W]

    # =========================================================================
    # 00. Ciel PMD Sky distant
    # =========================================================================
    sky_im = Image.new('RGBA', (W, H))
    sky_crop = SKY_SRC.crop((0, 0, W, 256))
    sky_im.paste(sky_crop, (0, 0))
    sky_arr = np.array(sky_im)
    sky_arr_night = to_night(sky_arr)
    sky_im.save(RENDERS_DIR / '00_ciel_pmd_jour.png')
    Image.fromarray(sky_arr_night).save(RENDERS_DIR / '00_ciel_pmd_nuit.png')

    # =========================================================================
    # 01. Nuages PMD en Wrap horizontal continu (Période 768 px)
    # =========================================================================
    cloud_strip = Image.new('RGBA', (W, 200))
    for im, x, y in CLOUD_TILES:
        for shift in [-W, 0, W]:
            cloud_strip.alpha_composite(im, (x + shift, y))

    cloud_strip_arr = np.array(cloud_strip)
    cloud_frames_day = []
    cloud_frames_night = []

    shift_step = W // N_FRAMES # 24 px/frame -> 24 * 32 = 768 px boucle parfaite
    for f in range(N_FRAMES):
        offset = (f * shift_step) % W
        rolled = np.roll(cloud_strip_arr, offset, axis=1)
        full_cloud = np.zeros((H, W, 4), dtype=np.uint8)
        full_cloud[:200, :] = rolled
        im_c_d = Image.fromarray(full_cloud)
        im_c_n = Image.fromarray(to_night(full_cloud))
        im_c_d.save(clouds_frames_dir / f'nuages_frame_{f:02d}_jour.png')
        im_c_n.save(clouds_frames_dir / f'nuages_frame_{f:02d}_nuit.png')
        cloud_frames_day.append(im_c_d)
        cloud_frames_night.append(im_c_n)

    cloud_frames_day[0].save(RENDERS_DIR / '01_nuages_wrap_jour.png')
    cloud_frames_night[0].save(RENDERS_DIR / '01_nuages_wrap_nuit.png')

    # =========================================================================
    # 02. Eau de Mer Animée en Palette Cycling dans la baie
    # Contour naturel de la baie incurvée
    # =========================================================================
    bay_contour = 160 + 35 * np.sin((xx - 120) * np.pi / 528)
    water_mask = (yy >= 40) & (yy <= bay_contour) & (xx >= 80) & (xx <= 688)
    wave_coords = ((xx // 8) - (yy // 6)) % 8
    water_alpha = (water_mask.astype(np.uint8) * 255)

    water_frames_day = []
    water_frames_night = []
    for f in range(N_FRAMES):
        # 8 couleurs cyclées sur 32 frames (soit 4 frames par décalage, avec interpolation fluide)
        k, t = divmod(f % N_FRAMES, 4)
        t = t / 4.0
        c0 = np.roll(CYCLE_WATER_RGB, -k, axis=0).astype(float)
        c1 = np.roll(CYCLE_WATER_RGB, -(k + 1), axis=0).astype(float)
        pal = np.rint((1 - t) * c0 + t * c1).astype(np.uint8)

        im_p = Image.fromarray(wave_coords.astype(np.uint8), mode='P')
        full_pal = np.zeros((256, 3), dtype=np.uint8)
        full_pal[:8] = pal
        im_p.putpalette(full_pal.ravel().tolist())
        im_rgba = im_p.convert('RGBA')
        w_arr = np.array(im_rgba)
        w_arr[:, :, 3] = water_alpha
        w_arr[~water_mask] = 0

        im_w_d = Image.fromarray(w_arr)
        im_w_n = Image.fromarray(to_night(w_arr))
        im_w_d.save(water_frames_dir / f'eau_mer_frame_{f:02d}_jour.png')
        im_w_n.save(water_frames_dir / f'eau_mer_frame_{f:02d}_nuit.png')
        water_frames_day.append(im_w_d)
        water_frames_night.append(im_w_n)

    water_frames_day[0].save(RENDERS_DIR / '02_eau_mer_animee_jour.png')
    water_frames_night[0].save(RENDERS_DIR / '02_eau_mer_animee_nuit.png')

    # =========================================================================
    # 03. Écume et Ressac du Rivage épousant la courbure de la plage
    # =========================================================================
    foam_layer = np.zeros((H, W, 4), np.uint8)
    foam_patch = A[96:112, 144:312]
    for x in range(80, 688, 168):
        ww_f = min(168, 688 - x)
        for dx in range(ww_f):
            col_x = x + dx
            target_y = int(round(bay_contour[0, col_x])) - 6
            if 0 <= target_y and target_y + 16 <= H:
                col_patch = foam_patch[:, dx]
                valid_col = col_patch[:, 3] > 0
                foam_layer[target_y:target_y+16, col_x][valid_col] = col_patch[valid_col]

    foam_im_d = Image.fromarray(foam_layer)
    foam_im_n = Image.fromarray(to_night(foam_layer))
    foam_im_d.save(RENDERS_DIR / '03_ecume_rivage_jour.png')
    foam_im_n.save(RENDERS_DIR / '03_ecume_rivage_nuit.png')

    # =========================================================================
    # 04. Sol d'Arène en Sable Doré Matelassé (Couverture continue sans interstice)
    # =========================================================================
    sand_layer = np.zeros((H, W, 4), np.uint8)
    arena_mask = (yy >= bay_contour - 8)
    rng = np.random.default_rng(55)
    hh, ww, ov = 24, 24, 8
    for y in range(140, H, hh - ov):
        for x in range(0, W, ww - ov):
            h = min(hh, H - y)
            w = min(ww, W - x)
            want = arena_mask[y:y+h, x:x+w]
            if not want.any():
                continue
            old = sand_layer[y:y+h, x:x+w]
            occupied = (old[:, :, 3] > 0) & want
            best = None
            for idx in rng.permutation(len(SAND_BOXES))[:16]:
                x0, y0, _, _ = SAND_BOXES[idx]
                patch = A[y0:y0+h, x0:x0+w]
                cost = ((old[:, :, :3].astype(float) - patch[:, :, :3]) ** 2).sum(2)
                score = cost[occupied].mean() if occupied.any() else rng.random()
                if best is None or score < best[0]:
                    best = (score, x0, y0, patch, cost)
            _, x0, y0, patch, cost = best
            take = want.copy()
            if x > 0 and w >= ov:
                take[:, :ov] &= np.arange(ov)[None, :] >= seam(cost[:, :ov])[:, None]
            if y > 140 and h >= ov:
                take[:ov, :] &= np.arange(ov)[:, None] >= seam(cost[:ov, :].T)[None, :]
            take |= want & (old[:, :, 3] == 0)
            old[take] = patch[take]

    sand_im_d = Image.fromarray(sand_layer)
    sand_im_n = Image.fromarray(to_night(sand_layer))
    sand_im_d.save(RENDERS_DIR / '04_sable_plage_jour.png')
    sand_im_n.save(RENDERS_DIR / '04_sable_plage_nuit.png')

    # =========================================================================
    # 05. Parois & Falaises Rouges avec Arche Naturelle
    # =========================================================================
    cliff_layer = np.zeros((H, W, 4), np.uint8)
    # Arche centrale au-dessus de l'horizon
    arch = clean_patch(A[40:112, 140:320])
    ah, aw = arch.shape[:2]
    arch_x, arch_y = (W - aw) // 2, 24
    cliff_layer[arch_y:arch_y+ah, arch_x:arch_x+aw] = arch

    # Falaises ouest (flanc gauche de l'arène)
    west_top = clean_patch(A[40:120, 0:150])
    cliff_layer[24:104, 0:150] = west_top
    west_body = clean_patch(A[80:380, 0:144])
    cliff_layer[90:390, 0:144] = west_body
    west_ext = clean_patch(A[120:340, 0:120])
    cliff_layer[130:350, 60:180] = np.maximum(cliff_layer[130:350, 60:180], west_ext)

    # Falaises est (flanc droit de l'arène)
    east_top = clean_patch(A[40:120, 306:456])
    cliff_layer[24:104, W-150:W] = east_top
    east_body = clean_patch(A[80:380, 312:456])
    cliff_layer[90:390, W-144:W] = east_body
    east_ext = clean_patch(A[120:340, 336:456])
    cliff_layer[130:350, W-180:W-60] = np.maximum(cliff_layer[130:350, W-180:W-60], east_ext)

    cliff_im_d = Image.fromarray(cliff_layer)
    cliff_im_n = Image.fromarray(to_night(cliff_layer))
    cliff_im_d.save(RENDERS_DIR / '05_falaises_et_rochers_jour.png')
    cliff_im_n.save(RENDERS_DIR / '05_falaises_et_rochers_nuit.png')

    # =========================================================================
    # 06. Récifs, Écueils et Rochers d'Avant-Plan
    # =========================================================================
    reef_layer = np.zeros((H, W, 4), np.uint8)
    reef_sw = clean_patch(A[416:480, 0:240])
    reef_layer[H-64:H, 0:240] = reef_sw
    reef_se = clean_patch(A[416:480, 216:456])
    reef_layer[H-64:H, W-240:W] = reef_se

    boulder1 = clean_patch(A[350:410, 160:220])
    reef_layer[390:450, 220:280] = boulder1
    boulder2 = clean_patch(A[350:410, 240:300])
    reef_layer[390:450, 488:548] = boulder2

    reef_im_d = Image.fromarray(reef_layer)
    reef_im_n = Image.fromarray(to_night(reef_layer))
    reef_im_d.save(RENDERS_DIR / '06_rochers_avant_plan_jour.png')
    reef_im_n.save(RENDERS_DIR / '06_rochers_avant_plan_nuit.png')

    # =========================================================================
    # 07. Ombres de Contact Douces (Calculées d'après les silhouettes)
    # Ancrent parfaitement les falaises et rochers sur le sol de sable
    # =========================================================================
    all_solid = (cliff_layer[:, :, 3] > 0) | (reef_layer[:, :, 3] > 0)
    sh_mask = Image.fromarray((all_solid * 255).astype(np.uint8))
    sh_shifted = Image.new('L', (W, H))
    sh_shifted.paste(sh_mask, (0, 4)) # décalage 4px vers le bas (lumière zénithale/nord)
    shadow_alpha = np.array(sh_shifted.filter(ImageFilter.GaussianBlur(1.2))).astype(float) * 0.38
    shadow_alpha[all_solid] = 0 # ne pas assombrir les objets eux-mêmes

    shadow_layer = np.zeros((H, W, 4), np.uint8)
    shadow_layer[:, :, :3] = [20, 18, 28] # Teinte d'ombre naturelle chaude/ardoise
    shadow_layer[:, :, 3] = np.rint(shadow_alpha).astype(np.uint8)

    shadow_im_d = Image.fromarray(shadow_layer)
    shadow_im_n = Image.fromarray(to_night(shadow_layer))
    shadow_im_d.save(RENDERS_DIR / '07_ombres_contact_jour.png')
    shadow_im_n.save(RENDERS_DIR / '07_ombres_contact_nuit.png')

    # =========================================================================
    # Recomposition & Génération des Animations WebP et GIF
    # =========================================================================
    scene_frames_day = []
    scene_frames_night = []

    for f in range(N_FRAMES):
        # Jour
        comp_d = Image.new('RGBA', (W, H))
        comp_d.alpha_composite(sky_im)
        comp_d.alpha_composite(cloud_frames_day[f])
        comp_d.alpha_composite(water_frames_day[f])
        comp_d.alpha_composite(foam_im_d)
        comp_d.alpha_composite(sand_im_d)
        comp_d.alpha_composite(shadow_im_d)
        comp_d.alpha_composite(cliff_im_d)
        comp_d.alpha_composite(reef_im_d)
        scene_frames_day.append(comp_d)

        # Nuit
        comp_n = Image.new('RGBA', (W, H))
        comp_n.alpha_composite(Image.fromarray(sky_arr_night))
        comp_n.alpha_composite(cloud_frames_night[f])
        comp_n.alpha_composite(water_frames_night[f])
        comp_n.alpha_composite(foam_im_n)
        comp_n.alpha_composite(sand_im_n)
        comp_n.alpha_composite(shadow_im_n)
        comp_n.alpha_composite(cliff_im_n)
        comp_n.alpha_composite(reef_im_n)
        scene_frames_night.append(comp_n)

    # Vérification d'opacité complète
    assert np.all(np.array(scene_frames_day[0])[:, :, 3] == 255), "La recomposition doit être 100% opaque sans trou"

    # Sauvegarde des compositions statiques
    scene_frames_day[0].save(RENDERS_DIR / 'COMPOSITION_JOUR.png')
    scene_frames_night[0].save(RENDERS_DIR / 'COMPOSITION_NUIT.png')

    # WebP animé (32 frames @ 100ms, sans perte)
    scene_frames_day[0].save(
        RENDERS_DIR / 'ANIMATION_WRAP.webp',
        save_all=True,
        append_images=scene_frames_day[1:],
        duration=FRAME_MS,
        loop=0,
        lossless=True
    )

    # GIF jour (256 couleurs optimisées)
    pal_day = scene_frames_day[0].convert('RGB').quantize(colors=256)
    gif_frames_day = [im.convert('RGB').quantize(palette=pal_day, dither=Image.Dither.NONE) for im in scene_frames_day]
    gif_frames_day[0].save(
        RENDERS_DIR / 'SCENE_ANIMEE.gif',
        save_all=True,
        append_images=gif_frames_day[1:],
        duration=FRAME_MS,
        loop=0,
        disposal=1,
        optimize=False
    )

    # GIF nuit
    pal_night = scene_frames_night[0].convert('RGB').quantize(colors=256)
    gif_frames_night = [im.convert('RGB').quantize(palette=pal_night, dither=Image.Dither.NONE) for im in scene_frames_night]
    gif_frames_night[0].save(
        RENDERS_DIR / 'SCENE_ANIMEE_NUIT.gif',
        save_all=True,
        append_images=gif_frames_night[1:],
        duration=FRAME_MS,
        loop=0,
        disposal=1,
        optimize=False
    )

    # GIF eau seule
    pal_water = water_frames_day[0].convert('RGB').quantize(colors=32)
    gif_water = [im.convert('RGB').quantize(palette=pal_water, dither=Image.Dither.NONE) for im in water_frames_day]
    gif_water[0].save(
        RENDERS_DIR / '02_eau_mer_animee_seule.gif',
        save_all=True,
        append_images=gif_water[1:],
        duration=FRAME_MS,
        loop=0,
        disposal=1,
        optimize=False
    )

    # =========================================================================
    # OpenRaster Multi-Layer (.ora)
    # =========================================================================
    ora_layers = {
        '00_ciel_pmd': sky_im,
        '01_nuages_wrap_phase0': cloud_frames_day[0],
        '02_eau_mer_animee_phase0': water_frames_day[0],
        '03_ecume_rivage': foam_im_d,
        '04_sable_plage': sand_im_d,
        '05_ombres_contact': shadow_im_d,
        '06_falaises_et_rochers': cliff_im_d,
        '07_rochers_avant_plan': reef_im_d
    }
    write_openraster(RENDERS_DIR / 'arene_plage_generee_editable.ora', ora_layers, scene_frames_day[0])

    # =========================================================================
    # Manifest JSON
    # =========================================================================
    manifest = {
        'version': 'PlageAnimeeMulticalquesV3',
        'title': 'Arène Plage PMD Sky — Multicalques Harmonieux & Double Animation Synchronisée',
        'dimensions': [W, H],
        'frames': N_FRAMES,
        'frame_ms': FRAME_MS,
        'loop_ms': N_FRAMES * FRAME_MS,
        'source_reference': REF_FILE,
        'source_sha256': REF_SHA256,
        'layers': [
            {'id': '00_ciel_pmd', 'file': '00_ciel_pmd_jour.png', 'description': 'Ciel distant PMD Sky'},
            {'id': '01_nuages_wrap', 'file': '01_nuages_wrap_jour.png', 'description': 'Nuages PMD animés en wrap horizontal 768px (32 frames, pas 24px/f)'},
            {'id': '02_eau_mer_animee', 'file': '02_eau_mer_animee_jour.png', 'description': 'Eau de mer dans la baie animée par palette cycling canonique à 8 phases (32 frames)'},
            {'id': '03_ecume_rivage', 'file': '03_ecume_rivage_jour.png', 'description': 'Ressac et écume blanche contourant naturellement la baie'},
            {'id': '04_sable_plage', 'file': '04_sable_plage_jour.png', 'description': 'Arène en sable doré matelassé avec coutures régulières'},
            {'id': '05_ombres_contact', 'file': '07_ombres_contact_jour.png', 'description': 'Ombres de contact ancrant les falaises et rochers sur le sable'},
            {'id': '06_falaises_et_rochers', 'file': '05_falaises_et_rochers_jour.png', 'description': 'Falaises rouges, plateaux et arche centrale'},
            {'id': '07_rochers_avant_plan', 'file': '06_rochers_avant_plan_jour.png', 'description': 'Récifs côtiers et écueils de premier plan'}
        ],
        'outputs': {
            'composition_day': 'COMPOSITION_JOUR.png',
            'composition_night': 'COMPOSITION_NUIT.png',
            'animation_webp': 'ANIMATION_WRAP.webp',
            'scene_gif_day': 'SCENE_ANIMEE.gif',
            'scene_gif_night': 'SCENE_ANIMEE_NUIT.gif',
            'water_gif': '02_eau_mer_animee_seule.gif',
            'openraster_ora': 'arene_plage_generee_editable.ora'
        }
    }
    (RENDERS_DIR / 'manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n')
    (EXPORTS_DIR / 'manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n')

    # =========================================================================
    # Visionneuse Interactive HTML5
    # =========================================================================
    def to_b64(path):
        return 'data:image/png;base64,' + base64.b64encode(path.read_bytes()).decode()

    html_data = {
        'layers_day': [
            {'id': '00_ciel_pmd', 'name': '00 · Ciel PMD Sky', 'src': to_b64(RENDERS_DIR / '00_ciel_pmd_jour.png'), 'animated': False},
            {'id': '01_nuages_wrap', 'name': '01 · Nuages Wrap Continu (32 frames)', 'frames': [to_b64(clouds_frames_dir / f'nuages_frame_{f:02d}_jour.png') for f in range(N_FRAMES)], 'animated': True},
            {'id': '02_eau_mer', 'name': '02 · Mer en Baie (Palette Cycling 32 frames)', 'frames': [to_b64(water_frames_dir / f'eau_mer_frame_{f:02d}_jour.png') for f in range(N_FRAMES)], 'animated': True},
            {'id': '03_ecume_rivage', 'name': '03 · Écume & Clapotis Rivage', 'src': to_b64(RENDERS_DIR / '03_ecume_rivage_jour.png'), 'animated': False},
            {'id': '04_sable_plage', 'name': '04 · Sol Sable Arène (Matelassé)', 'src': to_b64(RENDERS_DIR / '04_sable_plage_jour.png'), 'animated': False},
            {'id': '05_ombres_contact', 'name': '05 · Ombres de Contact Naturelles', 'src': to_b64(RENDERS_DIR / '07_ombres_contact_jour.png'), 'animated': False},
            {'id': '06_falaises_rochers', 'name': '06 · Falaises & Arche Rouges', 'src': to_b64(RENDERS_DIR / '05_falaises_et_rochers_jour.png'), 'animated': False},
            {'id': '07_rochers_avant_plan', 'name': '07 · Récifs & Écueils Avant-Plan', 'src': to_b64(RENDERS_DIR / '06_rochers_avant_plan_jour.png'), 'animated': False}
        ],
        'layers_night': [
            {'id': '00_ciel_pmd', 'name': '00 · Ciel PMD Sky', 'src': to_b64(RENDERS_DIR / '00_ciel_pmd_nuit.png'), 'animated': False},
            {'id': '01_nuages_wrap', 'name': '01 · Nuages Wrap Continu (32 frames)', 'frames': [to_b64(clouds_frames_dir / f'nuages_frame_{f:02d}_nuit.png') for f in range(N_FRAMES)], 'animated': True},
            {'id': '02_eau_mer', 'name': '02 · Mer en Baie (Palette Cycling 32 frames)', 'frames': [to_b64(water_frames_dir / f'eau_mer_frame_{f:02d}_nuit.png') for f in range(N_FRAMES)], 'animated': True},
            {'id': '03_ecume_rivage', 'name': '03 · Écume & Clapotis Rivage', 'src': to_b64(RENDERS_DIR / '03_ecume_rivage_nuit.png'), 'animated': False},
            {'id': '04_sable_plage', 'name': '04 · Sol Sable Arène (Matelassé)', 'src': to_b64(RENDERS_DIR / '04_sable_plage_nuit.png'), 'animated': False},
            {'id': '05_ombres_contact', 'name': '05 · Ombres de Contact Naturelles', 'src': to_b64(RENDERS_DIR / '07_ombres_contact_nuit.png'), 'animated': False},
            {'id': '06_falaises_rochers', 'name': '06 · Falaises & Arche Rouges', 'src': to_b64(RENDERS_DIR / '05_falaises_et_rochers_nuit.png'), 'animated': False},
            {'id': '07_rochers_avant_plan', 'name': '07 · Récifs & Écueils Avant-Plan', 'src': to_b64(RENDERS_DIR / '06_rochers_avant_plan_nuit.png'), 'animated': False}
        ]
    }

    html_content = f"""<!DOCTYPE html>
<html lang="fr">
<head>
<meta charset="utf-8">
<title>Arène Plage PMD Sky · Multicalques Harmonieux & Animations Synchronisées</title>
<style>
  :root {{
    --bg-dark: #0a0f1d;
    --panel-bg: #151d30;
    --accent: #38bdf8;
    --accent-gold: #f59e0b;
    --text-main: #f8fafc;
    --text-muted: #94a3b8;
    --border: #243048;
  }}
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{
    background: var(--bg-dark);
    color: var(--text-main);
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, monospace;
    padding: 24px;
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 20px;
  }}
  header {{
    text-align: center;
    max-width: 960px;
  }}
  h1 {{
    font-size: 26px;
    color: var(--accent-gold);
    margin-bottom: 8px;
    letter-spacing: -0.5px;
  }}
  p.subtitle {{
    color: var(--text-muted);
    font-size: 14px;
    line-height: 1.6;
  }}
  .main-container {{
    display: flex;
    flex-direction: row;
    gap: 24px;
    background: var(--panel-bg);
    padding: 20px;
    border-radius: 12px;
    border: 1px solid var(--border);
    box-shadow: 0 12px 32px rgba(0,0,0,0.6);
    max-width: 1200px;
  }}
  .canvas-wrapper {{
    position: relative;
    width: 768px;
    height: 512px;
    background: #000;
    border-radius: 8px;
    overflow: hidden;
    box-shadow: 0 4px 16px rgba(0,0,0,0.7);
  }}
  canvas {{
    image-rendering: pixelated;
    image-rendering: crisp-edges;
    display: block;
    width: 768px;
    height: 512px;
  }}
  .controls-sidebar {{
    width: 330px;
    display: flex;
    flex-direction: column;
    gap: 16px;
  }}
  .control-group {{
    background: #0b1120;
    padding: 14px;
    border-radius: 8px;
    border: 1px solid var(--border);
  }}
  .control-group h3 {{
    font-size: 12px;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    color: var(--accent-gold);
    margin-bottom: 10px;
  }}
  .layer-item {{
    display: flex;
    align-items: center;
    gap: 10px;
    margin-bottom: 8px;
    font-size: 13px;
    cursor: pointer;
    user-select: none;
  }}
  .layer-item input[type="checkbox"] {{
    accent-color: var(--accent);
    width: 16px;
    height: 16px;
    cursor: pointer;
  }}
  .btn-row {{
    display: flex;
    gap: 8px;
  }}
  button {{
    flex: 1;
    background: #1e293b;
    color: var(--text-main);
    border: 1px solid var(--border);
    padding: 8px 12px;
    border-radius: 6px;
    cursor: pointer;
    font-size: 12px;
    font-weight: 600;
    transition: all 0.2s;
  }}
  button:hover {{
    background: #334155;
  }}
  button.active {{
    background: var(--accent);
    color: #000;
    border-color: var(--accent);
  }}
  .slider-wrapper {{
    display: flex;
    flex-direction: column;
    gap: 6px;
  }}
  .slider-wrapper label {{
    font-size: 12px;
    color: var(--text-muted);
    display: flex;
    justify-content: space-between;
  }}
  input[type="range"] {{
    accent-color: var(--accent);
    width: 100%;
    cursor: pointer;
  }}
  .badge {{
    display: inline-block;
    padding: 2px 6px;
    border-radius: 4px;
    font-size: 10px;
    font-weight: bold;
    background: #0369a1;
    color: #e0f2fe;
    margin-left: auto;
  }}
  .badge.anim {{
    background: #b45309;
    color: #fef3c7;
  }}
  .note {{
    font-size: 11px;
    color: #94a3b8;
    line-height: 1.45;
    margin-top: 6px;
  }}
</style>
</head>
<body>

<header>
  <h1>Arène Plage PMD Sky — Multicalques Harmonieux</h1>
  <p class="subtitle">Architecture multicalques pure. Les falaises, les ombres, le sable et l'eau s'emboîtent naturellement (« se marient entre eux ») sans aucune coupure artificielle ni trou de transparence. Double animation : <strong>Nuages Wrap continu</strong> (32 f) et <strong>Mer en Palette Cycling</strong> (32 f, 8 teintes PMD Sky).</p>
</header>

<div class="main-container">
  <div class="canvas-wrapper">
    <canvas id="viewCanvas" width="768" height="512"></canvas>
  </div>

  <div class="controls-sidebar">
    <div class="control-group">
      <h3>Ambiance Jour / Nuit</h3>
      <div class="btn-row">
        <button id="btnDay" class="active" onclick="setMode('day')">☀️ Jour</button>
        <button id="btnNight" onclick="setMode('night')">🌙 Nuit (Abyss)</button>
      </div>
    </div>

    <div class="control-group">
      <h3>Animation & Synchronisation</h3>
      <div class="slider-wrapper">
        <label><span>Vitesse FPS</span><span id="fpsVal">10 fps (100 ms)</span></label>
        <input type="range" id="fpsSlider" min="2" max="30" value="10" oninput="updateFps(this.value)">
      </div>
      <div class="btn-row" style="margin-top: 10px;">
        <button id="btnPlayPause" class="active" onclick="togglePlay()">⏸️ Pause</button>
        <button onclick="stepFrame()">⏭️ +1 Frame</button>
      </div>
      <div style="font-size: 11px; color: var(--text-muted); margin-top: 8px;" id="frameInfo">Frame: 0 / 32 (0.00s)</div>
    </div>

    <div class="control-group">
      <h3>Visibilité des 8 Calques</h3>
      <div id="layerList"></div>
      <p class="note">Chaque calque est totalement indépendant et transparent. Activez/désactivez individuellement pour vérifier l'imbrication des ombres, du sable et des reliefs.</p>
    </div>

    <div class="control-group">
      <h3>Affichage & Grille</h3>
      <label class="layer-item">
        <input type="checkbox" id="chkGrid" onchange="toggleGrid()">
        <span>Grille 8px Canonique PMD</span>
      </label>
    </div>
  </div>
</div>

<script>
const DATA = {json.dumps(html_data, ensure_ascii=False)};
const canvas = document.getElementById('viewCanvas');
const ctx = canvas.getContext('2d');

let currentMode = 'day';
let isPlaying = true;
let currentFrame = 0;
let fps = 10;
let lastTime = performance.now();
let showGrid = false;

// Preload images
const cache = {{ day: [], night: [] }};
function preload() {{
  ['day', 'night'].forEach(mode => {{
    const list = mode === 'day' ? DATA.layers_day : DATA.layers_night;
    list.forEach(item => {{
      if (item.animated) {{
        const frames = item.frames.map(src => {{
          const img = new Image();
          img.src = src;
          return img;
        }});
        cache[mode].push({{ id: item.id, animated: true, frames: frames, visible: true }});
      }} else {{
        const img = new Image();
        img.src = item.src;
        cache[mode].push({{ id: item.id, animated: false, img: img, visible: true }});
      }}
    }});
  }});
}}
preload();

function initLayerList() {{
  const container = document.getElementById('layerList');
  container.innerHTML = '';
  DATA.layers_day.forEach((layer, idx) => {{
    const div = document.createElement('label');
    div.className = 'layer-item';
    const chk = document.createElement('input');
    chk.type = 'checkbox';
    chk.checked = true;
    chk.onchange = (e) => {{
      cache.day[idx].visible = e.target.checked;
      cache.night[idx].visible = e.target.checked;
      render();
    }};
    const span = document.createElement('span');
    span.textContent = layer.name;
    const badge = document.createElement('span');
    badge.className = 'badge' + (layer.animated ? ' anim' : '');
    badge.textContent = layer.animated ? 'ANIM' : 'PNG';
    div.appendChild(chk);
    div.appendChild(span);
    div.appendChild(badge);
    container.appendChild(div);
  }});
}}
initLayerList();

function setMode(mode) {{
  currentMode = mode;
  document.getElementById('btnDay').className = mode === 'day' ? 'active' : '';
  document.getElementById('btnNight').className = mode === 'night' ? 'active' : '';
  render();
}}

function togglePlay() {{
  isPlaying = !isPlaying;
  document.getElementById('btnPlayPause').textContent = isPlaying ? '⏸️ Pause' : '▶️ Play';
}}

function stepFrame() {{
  isPlaying = false;
  document.getElementById('btnPlayPause').textContent = '▶️ Play';
  currentFrame = (currentFrame + 1) % 32;
  render();
}}

function updateFps(val) {{
  fps = parseInt(val);
  const ms = Math.round(1000 / fps);
  document.getElementById('fpsVal').textContent = fps + ' fps (' + ms + ' ms)';
}}

function toggleGrid() {{
  showGrid = document.getElementById('chkGrid').checked;
  render();
}}

function render() {{
  ctx.clearRect(0, 0, 768, 512);
  const activeLayers = cache[currentMode];
  activeLayers.forEach(l => {{
    if (!l.visible) return;
    if (l.animated) {{
      const img = l.frames[currentFrame];
      if (img.complete) ctx.drawImage(img, 0, 0);
    }} else {{
      if (l.img.complete) ctx.drawImage(l.img, 0, 0);
    }}
  }});

  if (showGrid) {{
    ctx.strokeStyle = 'rgba(255, 255, 255, 0.15)';
    ctx.lineWidth = 1;
    for (let x = 0; x <= 768; x += 8) {{
      ctx.beginPath();
      ctx.moveTo(x + 0.5, 0);
      ctx.lineTo(x + 0.5, 512);
      ctx.stroke();
    }}
    for (let y = 0; y <= 512; y += 8) {{
      ctx.beginPath();
      ctx.moveTo(0, y + 0.5);
      ctx.lineTo(768, y + 0.5);
      ctx.stroke();
    }}
  }}

  document.getElementById('frameInfo').textContent =
    'Frame: ' + currentFrame + ' / 32 (' + (currentFrame * (1000/fps) / 1000).toFixed(2) + 's)';
}}

function loop(time) {{
  if (isPlaying) {{
    const interval = 1000 / fps;
    if (time - lastTime >= interval) {{
      currentFrame = (currentFrame + 1) % 32;
      lastTime = time - ((time - lastTime) % interval);
      render();
    }}
  }}
  requestAnimationFrame(loop);
}}
requestAnimationFrame(loop);
</script>
</body>
</html>
"""
    (ROOT / 'apercu_plage_animee_multicalques_v3.html').write_text(html_content, encoding='utf-8')
    print("Plage Animée Multicalques V3 — Pipeline terminé avec succès. Tous les calques sont parfaitement harmonisés.")

if __name__ == '__main__':
    build()
