"""Plage Animée Multicalques V3 — Conforme à la méthode canonique PMD Sky Port & Rendu Généré.
Strictement aligné sur les exigences utilisateur et les méthodes des anciens rendus :
1. Terrain complet généré sur magenta (#FF00FF) : renders/arene_plage_multicalques_v3/bruts/terrain_magenta.png
2. Sol complet généré séparément sous les reliefs : renders/arene_plage_multicalques_v3/bruts/sol_complet.png
3. Découpage en plans de profondeur strictement alignés et disjoints :
   - 01_sol_complet_genere (sol de sable sous-jacent complet)
   - 02_sol_sable_visible (arène centrale en sable fin)
   - 03_falaises_arriere (arches et parois encadrant l'horizon)
   - 04_falaises_gauche (massif rocheux rouge ouest)
   - 05_falaises_droite (massif rocheux rouge est)
   - 06_rochers_avant_plan (récifs côtiers et écueils de premier plan)
   - 07_ombres_contact (ombres douces ancrant les rochers sur le sable)
4. Animation de l'eau authentique PMD Sky Port (issue de large.D25P11A.gif / Côte Escarpée) :
   - 30 frames canoniques, 130 ms par frame (boucle 3,9 s)
   - 10 teintes marines authentiques PMD Sky
5. Ciel PMD distant et nappe de nuages en wrap horizontal continu (boucle exacte modulo 648 px à l'étape 30)
6. Assertion stricte : la fusion des calques de terrain restitue exactement le dessin généré détouré.
7. Livrables : PNGs jour/nuit, WebP sans perte, GIFs, ORA éditable, manifest.json et visionneuse HTML5.
"""
from pathlib import Path
import json, hashlib, base64, io, zipfile, xml.etree.ElementTree as ET
import numpy as np
from PIL import Image, ImageFilter
from scipy import ndimage as nd

ROOT = Path(__file__).resolve().parents[2]
RENDERS_DIR = ROOT / 'renders/plage_animee_multicalques_v3'
EXPORTS_DIR = ROOT / 'exports/plage_animee_multicalques_v3'
BRUTS_DIR = ROOT / 'renders/arene_plage_multicalques_v3/bruts'

# Dimensions canoniques de la côte PMD Sky (D25)
W, H = 648, 504
N_FRAMES = 30
FRAME_MS = 130 # PMD Sky native frame duration (3.9s total loop)

# Sources canoniques
D25_FILE = 'large.D25P11A.gif.1859d89ca99571b9d779dbb182a1b681.gif'
D25_PATH = ROOT / D25_FILE
D25_SHA256 = hashlib.sha256(D25_PATH.read_bytes()).hexdigest()

SKY_SRC = Image.open(ROOT / 'source/cote_v2/ciel_sans_nuages.png').convert('RGBA')
CLOUD_TILES = [
    (Image.open(ROOT / 'sprites/cote_v2/COTEV2_NUAGE_01.png').convert('RGBA'), 32, 16),
    (Image.open(ROOT / 'sprites/cote_v2/COTEV2_NUAGE_02.png').convert('RGBA'), 260, 32),
    (Image.open(ROOT / 'sprites/cote_v2/COTEV2_NUAGE_03.png').convert('RGBA'), 480, 12)
]

def key_magenta(im):
    """Détourage précis du magenta #FF00FF avec élimination des franges."""
    a = np.array(im.convert('RGBA'))
    r, g, b = a[:, :, :3].astype(float).transpose(2, 0, 1)
    mag = (r > 70) & (b > 65) & (r > g * 1.35) & (b > g * 1.35)
    fringe = nd.binary_dilation(mag, iterations=1) & (r > g * 1.1) & (b > g * 1.1)
    a[mag | fringe] = 0
    a[~mag & ~fringe, 3] = 255
    return a

def to_night(rgba_arr):
    """Formule canonique d'étalonnage nocturne Abyss du dépôt."""
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
    water_frames_dir = RENDERS_DIR / '02_eau_mer_port_frames'
    clouds_frames_dir = RENDERS_DIR / '01_nuages_wrap_frames'
    water_frames_dir.mkdir(exist_ok=True)
    clouds_frames_dir.mkdir(exist_ok=True)

    yy, xx = np.mgrid[:H, :W]

    # =========================================================================
    # 1. Chargement & Normalisation des Bruts Générés (Terrain & Sol Complet)
    # =========================================================================
    raw_terrain = Image.open(BRUTS_DIR / 'terrain_magenta.png').resize((W, H), Image.Resampling.NEAREST)
    raw_floor = Image.open(BRUTS_DIR / 'sol_complet.png').resize((W, H), Image.Resampling.NEAREST)

    ta = key_magenta(raw_terrain)
    fa = key_magenta(raw_floor)

    valid = ta[:, :, 3] > 0
    void = ~valid

    # =========================================================================
    # 2. Partition des Calques de Terrain (Cohérence & Emboîtement 100% Exacts)
    # =========================================================================
    r, g, b = ta[:, :, :3].astype(float).transpose(2, 0, 1)
    # Détection de la matière sable doré vs structure rocheuse rouge
    is_sand = valid & (r > 130) & (g > 100) & (b < 120) & (r > b * 1.2)

    # Masques spatiaux disjoints
    left_cliffs = valid & ~is_sand & (xx < 220)
    right_cliffs = valid & ~is_sand & (xx > 428)
    rear_arch = valid & ~is_sand & (yy < 120) & ~left_cliffs & ~right_cliffs
    front_reefs = valid & ~is_sand & (yy >= 380) & ~left_cliffs & ~right_cliffs
    visible_sand = valid & ~left_cliffs & ~right_cliffs & ~rear_arch & ~front_reefs

    # Vérification de partition mathématiquement parfaite
    terrain_masks = {
        '04_sol_sable_visible': visible_sand,
        '05_falaises_arriere': rear_arch,
        '06_falaises_gauche': left_cliffs,
        '07_falaises_droite': right_cliffs,
        '08_rochers_avant_plan': front_reefs
    }
    sum_check = sum(m.astype(int) for m in terrain_masks.values())
    assert np.all(sum_check[valid] == 1), "Chaque pixel valide doit appartenir à exactement un calque"
    assert np.all(sum_check[void] == 0), "Aucun pixel de terrain dans la zone de vide"

    # =========================================================================
    # 3. Sol Complet Sous-Jacent (Underlay continu sans trou)
    # =========================================================================
    floor_arr = fa.copy()
    floor_arr[void] = 0

    # =========================================================================
    # 4. Ombres de Contact Douces (Calculées sur les silhouettes des reliefs)
    # =========================================================================
    structures = left_cliffs | right_cliffs | rear_arch | front_reefs
    sh_mask = Image.fromarray((structures * 255).astype(np.uint8))
    sh_shifted = Image.new('L', (W, H))
    sh_shifted.paste(sh_mask, (0, 3)) # Décalage zénithal 3px vers le bas
    shadow_alpha = np.array(sh_shifted.filter(ImageFilter.GaussianBlur(1.0))).astype(float) * 0.35
    shadow_alpha[structures | void] = 0 # Pas d'ombre sur les rochers eux-mêmes ni dans le vide

    shadow_arr = np.zeros((H, W, 4), np.uint8)
    shadow_arr[:, :, :3] = [18, 16, 26] # Ombre douce naturelle
    shadow_arr[:, :, 3] = np.rint(shadow_alpha).astype(np.uint8)

    # =========================================================================
    # 5. Ciel PMD Sky Distant (Arrière-plan statique)
    # =========================================================================
    sky_im = Image.new('RGBA', (W, H))
    sky_crop = SKY_SRC.crop((0, 0, W, 100))
    sky_im.paste(sky_crop, (0, 0))
    sky_arr = np.array(sky_im)
    sky_arr_night = to_night(sky_arr)

    # =========================================================================
    # 6. Nuages PMD en Wrap Horizontal Continu (30 frames, boucle modulo 648 px)
    # =========================================================================
    cloud_strip = Image.new('RGBA', (W, 140))
    for im, cx, cy in CLOUD_TILES:
        for shift in [-W, 0, W]:
            cloud_strip.alpha_composite(im, (cx + shift, cy))
    cloud_strip_arr = np.array(cloud_strip)

    cloud_frames_day = []
    cloud_frames_night = []
    for f in range(N_FRAMES):
        offset = int(round((f * W) / N_FRAMES)) % W
        rolled = np.roll(cloud_strip_arr, offset, axis=1)
        full_cloud = np.zeros((H, W, 4), dtype=np.uint8)
        full_cloud[:140, :] = rolled
        # Les nuages ne s'affichent que dans le ciel/horizon supérieur
        full_cloud[yy > 90] = 0

        im_c_d = Image.fromarray(full_cloud)
        im_c_n = Image.fromarray(to_night(full_cloud))
        im_c_d.save(clouds_frames_dir / f'nuages_frame_{f:02d}_jour.png')
        im_c_n.save(clouds_frames_dir / f'nuages_frame_{f:02d}_nuit.png')
        cloud_frames_day.append(im_c_d)
        cloud_frames_night.append(im_c_n)

    # =========================================================================
    # 7. Eau de Mer Animée Canonique PMD Sky Port (issue de large.D25P11A.gif)
    # 30 frames réelles, 130 ms par frame
    # =========================================================================
    d25_im = Image.open(D25_PATH)
    d25_frames = []
    for f in range(N_FRAMES):
        d25_im.seek(f)
        d25_frames.append(np.array(d25_im.convert('RGBA')))

    water_mask = void & (yy >= 35) # Zone maritime dans l'ouverture d'horizon
    sample_y = (260 + (yy % 200)).astype(int)

    water_frames_day = []
    water_frames_night = []
    for f in range(N_FRAMES):
        w_arr = np.zeros((H, W, 4), np.uint8)
        w_arr[water_mask] = d25_frames[f][sample_y[water_mask], xx[water_mask]]

        im_w_d = Image.fromarray(w_arr)
        im_w_n = Image.fromarray(to_night(w_arr))
        im_w_d.save(water_frames_dir / f'eau_mer_frame_{f:02d}_jour.png')
        im_w_n.save(water_frames_dir / f'eau_mer_frame_{f:02d}_nuit.png')
        water_frames_day.append(im_w_d)
        water_frames_night.append(im_w_n)

    # =========================================================================
    # 8. Sauvegarde de Tous les Calques Individuels (Jour & Nuit)
    # =========================================================================
    layers_dict_day = {
        '00_ciel_pmd': sky_im,
        '01_nuages_wrap': cloud_frames_day[0],
        '02_eau_mer_port': water_frames_day[0],
        '03_sol_sable_complet': Image.fromarray(floor_arr),
        '04_sol_sable_visible': Image.fromarray(np.where(visible_sand[:, :, None], ta, 0)),
        '05_falaises_arriere': Image.fromarray(np.where(rear_arch[:, :, None], ta, 0)),
        '06_falaises_gauche': Image.fromarray(np.where(left_cliffs[:, :, None], ta, 0)),
        '07_falaises_droite': Image.fromarray(np.where(right_cliffs[:, :, None], ta, 0)),
        '08_rochers_avant_plan': Image.fromarray(np.where(front_reefs[:, :, None], ta, 0)),
        '09_ombres_contact': Image.fromarray(shadow_arr)
    }

    layers_dict_night = {}
    for k, im in layers_dict_day.items():
        arr_d = np.array(im)
        arr_n = to_night(arr_d)
        im_n = Image.fromarray(arr_n)
        layers_dict_night[k] = im_n
        im.save(RENDERS_DIR / f'{k}_jour.png')
        im_n.save(RENDERS_DIR / f'{k}_nuit.png')

    # =========================================================================
    # 9. Composition des 30 Frames Animées & Vérification d'Opacité
    # =========================================================================
    scene_frames_day = []
    scene_frames_night = []

    for f in range(N_FRAMES):
        # Jour
        comp_d = Image.new('RGBA', (W, H))
        comp_d.alpha_composite(sky_im)
        comp_d.alpha_composite(cloud_frames_day[f])
        comp_d.alpha_composite(water_frames_day[f])
        comp_d.alpha_composite(layers_dict_day['04_sol_sable_visible'])
        comp_d.alpha_composite(layers_dict_day['09_ombres_contact'])
        comp_d.alpha_composite(layers_dict_day['05_falaises_arriere'])
        comp_d.alpha_composite(layers_dict_day['06_falaises_gauche'])
        comp_d.alpha_composite(layers_dict_day['07_falaises_droite'])
        comp_d.alpha_composite(layers_dict_day['08_rochers_avant_plan'])
        scene_frames_day.append(comp_d)

        # Nuit
        comp_n = Image.new('RGBA', (W, H))
        comp_n.alpha_composite(Image.fromarray(sky_arr_night))
        comp_n.alpha_composite(cloud_frames_night[f])
        comp_n.alpha_composite(water_frames_night[f])
        comp_n.alpha_composite(layers_dict_night['04_sol_sable_visible'])
        comp_n.alpha_composite(layers_dict_night['09_ombres_contact'])
        comp_n.alpha_composite(layers_dict_night['05_falaises_arriere'])
        comp_n.alpha_composite(layers_dict_night['06_falaises_gauche'])
        comp_n.alpha_composite(layers_dict_night['07_falaises_droite'])
        comp_n.alpha_composite(layers_dict_night['08_rochers_avant_plan'])
        scene_frames_night.append(comp_n)

    # Vérification d'opacité stricte
    assert np.all(np.array(scene_frames_day[0])[:, :, 3] == 255), "La scène doit être 100% opaque"

    # Sauvegarde des images statiques
    scene_frames_day[0].save(RENDERS_DIR / 'COMPOSITION_JOUR.png')
    scene_frames_night[0].save(RENDERS_DIR / 'COMPOSITION_NUIT.png')

    # WebP animé (30 frames @ 130 ms, boucle 3,9 s sans perte)
    scene_frames_day[0].save(
        RENDERS_DIR / 'ANIMATION_WRAP.webp',
        save_all=True,
        append_images=scene_frames_day[1:],
        duration=FRAME_MS,
        loop=0,
        lossless=True
    )

    # GIF Jour
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

    # GIF Nuit
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

    # GIF Eau seule
    pal_water = water_frames_day[0].convert('RGB').quantize(colors=32)
    gif_water = [im.convert('RGB').quantize(palette=pal_water, dither=Image.Dither.NONE) for im in water_frames_day]
    gif_water[0].save(
        RENDERS_DIR / '02_eau_mer_port_animee_seule.gif',
        save_all=True,
        append_images=gif_water[1:],
        duration=FRAME_MS,
        loop=0,
        disposal=1,
        optimize=False
    )

    # OpenRaster Multi-Calques Éditable
    ora_stack = {
        '00_ciel_pmd': sky_im,
        '01_nuages_wrap_phase0': cloud_frames_day[0],
        '02_eau_mer_port_phase0': water_frames_day[0],
        '03_sol_sable_complet': layers_dict_day['03_sol_sable_complet'],
        '04_sol_sable_visible': layers_dict_day['04_sol_sable_visible'],
        '05_ombres_contact': layers_dict_day['09_ombres_contact'],
        '06_falaises_arriere': layers_dict_day['05_falaises_arriere'],
        '07_falaises_gauche': layers_dict_day['06_falaises_gauche'],
        '08_falaises_droite': layers_dict_day['07_falaises_droite'],
        '09_rochers_avant_plan': layers_dict_day['08_rochers_avant_plan']
    }
    write_openraster(RENDERS_DIR / 'arene_plage_generee_editable.ora', ora_stack, scene_frames_day[0])

    # Manifest JSON
    manifest = {
        'version': 'PlageAnimeeMulticalquesV3',
        'title': 'Arène Plage PMD Sky — Calques Générés Alignés & Eau Canonique PMD Port',
        'dimensions': [W, H],
        'frames': N_FRAMES,
        'frame_ms': FRAME_MS,
        'loop_ms': N_FRAMES * FRAME_MS,
        'water_source': D25_FILE,
        'water_sha256': D25_SHA256,
        'terrain_sources': [
            'renders/arene_plage_multicalques_v3/bruts/terrain_magenta.png',
            'renders/arene_plage_multicalques_v3/bruts/sol_complet.png'
        ],
        'layers': [
            {'id': '00_ciel_pmd', 'file': '00_ciel_pmd_jour.png', 'description': 'Ciel distant PMD Sky azur'},
            {'id': '01_nuages_wrap', 'file': '01_nuages_wrap_jour.png', 'description': 'Nuages PMD animés en wrap horizontal continu (30 frames, période 648 px)'},
            {'id': '02_eau_mer_port', 'file': '02_eau_mer_port_jour.png', 'description': 'Eau de mer authentique PMD Sky Port (30 frames, 130 ms, 10 teintes marines)'},
            {'id': '03_sol_sable_complet', 'file': '03_sol_sable_complet_jour.png', 'description': 'Sol de sable complet généré sous-jacent'},
            {'id': '04_sol_sable_visible', 'file': '04_sol_sable_visible_jour.png', 'description': 'Arène centrale en sable doré fin'},
            {'id': '05_falaises_arriere', 'file': '05_falaises_arriere_jour.png', 'description': 'Parois et arche de falaise rouge d\'arrière-plan'},
            {'id': '06_falaises_gauche', 'file': '06_falaises_gauche_jour.png', 'description': 'Massif de falaise rouge flanc ouest'},
            {'id': '07_falaises_droite', 'file': '07_falaises_droite_jour.png', 'description': 'Massif de falaise rouge flanc est'},
            {'id': '08_rochers_avant_plan', 'file': '08_rochers_avant_plan_jour.png', 'description': 'Récifs côtiers et écueils de premier plan'},
            {'id': '09_ombres_contact', 'file': '09_ombres_contact_jour.png', 'description': 'Ombres de contact ancrant les reliefs sur le sable'}
        ],
        'outputs': {
            'composition_day': 'COMPOSITION_JOUR.png',
            'composition_night': 'COMPOSITION_NUIT.png',
            'animation_webp': 'ANIMATION_WRAP.webp',
            'scene_gif_day': 'SCENE_ANIMEE.gif',
            'scene_gif_night': 'SCENE_ANIMEE_NUIT.gif',
            'water_gif': '02_eau_mer_port_animee_seule.gif',
            'openraster_ora': 'arene_plage_generee_editable.ora'
        }
    }
    (RENDERS_DIR / 'manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n')
    (EXPORTS_DIR / 'manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n')

    # Galerie HTML5 Interactive
    def to_b64(path):
        return 'data:image/png;base64,' + base64.b64encode(path.read_bytes()).decode()

    html_data = {
        'dimensions': [W, H],
        'fps': 8,
        'frame_ms': FRAME_MS,
        'layers_day': [
            {'id': '00_ciel_pmd', 'name': '00 · Ciel PMD Sky', 'src': to_b64(RENDERS_DIR / '00_ciel_pmd_jour.png'), 'animated': False},
            {'id': '01_nuages_wrap', 'name': '01 · Nuages Wrap (30 frames)', 'frames': [to_b64(clouds_frames_dir / f'nuages_frame_{f:02d}_jour.png') for f in range(N_FRAMES)], 'animated': True},
            {'id': '02_eau_mer_port', 'name': '02 · Mer PMD Port (30 frames)', 'frames': [to_b64(water_frames_dir / f'eau_mer_frame_{f:02d}_jour.png') for f in range(N_FRAMES)], 'animated': True},
            {'id': '03_sol_sable_complet', 'name': '03 · Sol Sable Complet (Généré)', 'src': to_b64(RENDERS_DIR / '03_sol_sable_complet_jour.png'), 'animated': False},
            {'id': '04_sol_sable_visible', 'name': '04 · Sol Sable Visible', 'src': to_b64(RENDERS_DIR / '04_sol_sable_visible_jour.png'), 'animated': False},
            {'id': '05_ombres_contact', 'name': '05 · Ombres de Contact Naturelles', 'src': to_b64(RENDERS_DIR / '09_ombres_contact_jour.png'), 'animated': False},
            {'id': '06_falaises_arriere', 'name': '06 · Falaises & Arche Arrière', 'src': to_b64(RENDERS_DIR / '05_falaises_arriere_jour.png'), 'animated': False},
            {'id': '07_falaises_gauche', 'name': '07 · Falaise Flanc Gauche', 'src': to_b64(RENDERS_DIR / '06_falaises_gauche_jour.png'), 'animated': False},
            {'id': '08_falaises_droite', 'name': '08 · Falaise Flanc Droit', 'src': to_b64(RENDERS_DIR / '07_falaises_droite_jour.png'), 'animated': False},
            {'id': '09_rochers_avant_plan', 'name': '09 · Récifs & Écueils Avant-Plan', 'src': to_b64(RENDERS_DIR / '08_rochers_avant_plan_jour.png'), 'animated': False}
        ],
        'layers_night': [
            {'id': '00_ciel_pmd', 'name': '00 · Ciel PMD Sky', 'src': to_b64(RENDERS_DIR / '00_ciel_pmd_nuit.png'), 'animated': False},
            {'id': '01_nuages_wrap', 'name': '01 · Nuages Wrap (30 frames)', 'frames': [to_b64(clouds_frames_dir / f'nuages_frame_{f:02d}_nuit.png') for f in range(N_FRAMES)], 'animated': True},
            {'id': '02_eau_mer_port', 'name': '02 · Mer PMD Port (30 frames)', 'frames': [to_b64(water_frames_dir / f'eau_mer_frame_{f:02d}_nuit.png') for f in range(N_FRAMES)], 'animated': True},
            {'id': '03_sol_sable_complet', 'name': '03 · Sol Sable Complet (Généré)', 'src': to_b64(RENDERS_DIR / '03_sol_sable_complet_nuit.png'), 'animated': False},
            {'id': '04_sol_sable_visible', 'name': '04 · Sol Sable Visible', 'src': to_b64(RENDERS_DIR / '04_sol_sable_visible_nuit.png'), 'animated': False},
            {'id': '05_ombres_contact', 'name': '05 · Ombres de Contact Naturelles', 'src': to_b64(RENDERS_DIR / '09_ombres_contact_nuit.png'), 'animated': False},
            {'id': '06_falaises_arriere', 'name': '06 · Falaises & Arche Arrière', 'src': to_b64(RENDERS_DIR / '05_falaises_arriere_nuit.png'), 'animated': False},
            {'id': '07_falaises_gauche', 'name': '07 · Falaise Flanc Gauche', 'src': to_b64(RENDERS_DIR / '06_falaises_gauche_nuit.png'), 'animated': False},
            {'id': '08_falaises_droite', 'name': '08 · Falaise Flanc Droit', 'src': to_b64(RENDERS_DIR / '07_falaises_droite_nuit.png'), 'animated': False},
            {'id': '09_rochers_avant_plan', 'name': '09 · Récifs & Écueils Avant-Plan', 'src': to_b64(RENDERS_DIR / '08_rochers_avant_plan_nuit.png'), 'animated': False}
        ]
    }

    html_content = f"""<!DOCTYPE html>
<html lang="fr">
<head>
<meta charset="utf-8">
<title>Arène Plage PMD Sky · Eau Animée PMD Port & Calques Alignés</title>
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
    max-width: 1100px;
  }}
  .canvas-wrapper {{
    position: relative;
    width: {W}px;
    height: {H}px;
    background: #000;
    border-radius: 8px;
    overflow: hidden;
    box-shadow: 0 4px 16px rgba(0,0,0,0.7);
  }}
  canvas {{
    image-rendering: pixelated;
    image-rendering: crisp-edges;
    display: block;
    width: {W}px;
    height: {H}px;
  }}
  .controls-sidebar {{
    width: 340px;
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
  <h1>Arène Plage PMD Sky — Eau PMD Port & Calques Parfaitement Concordants</h1>
  <p class="subtitle">Architecture multicalques pure issue du rendu complet généré sur magenta et de l'eau authentique du Port de PMD Sky (D25). <strong>Les calques concordent à 100% sans coupure artificielle</strong> : falaises et arches, sol sous-jacent complet, ombres de contact, nuages en wrap horizontal et rouleaux de ressac canoniques.</p>
</header>

<div class="main-container">
  <div class="canvas-wrapper">
    <canvas id="viewCanvas" width="{W}" height="{H}"></canvas>
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
        <label><span>Vitesse FPS</span><span id="fpsVal">7.7 fps (130 ms)</span></label>
        <input type="range" id="fpsSlider" min="2" max="20" value="8" oninput="updateFps(this.value)">
      </div>
      <div class="btn-row" style="margin-top: 10px;">
        <button id="btnPlayPause" class="active" onclick="togglePlay()">⏸️ Pause</button>
        <button onclick="stepFrame()">⏭️ +1 Frame</button>
      </div>
      <div style="font-size: 11px; color: var(--text-muted); margin-top: 8px;" id="frameInfo">Frame: 0 / {N_FRAMES} (0.00s)</div>
    </div>

    <div class="control-group">
      <h3>Visibilité des 10 Calques</h3>
      <div id="layerList"></div>
      <p class="note">Tous les calques proviennent de la même composition générée : désactivez les falaises pour voir le sol de sable continu sous-jacent et les ombres.</p>
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
let fps = 7.7;
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
    // Le sol complet sous-jacent (03) est masqué par défaut pour ne pas doubler avec le sol visible
    chk.checked = layer.id !== '03_sol_sable_complet';
    cache.day[idx].visible = chk.checked;
    cache.night[idx].visible = chk.checked;
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
  currentFrame = (currentFrame + 1) % {N_FRAMES};
  render();
}}

function updateFps(val) {{
  fps = parseFloat(val);
  const ms = Math.round(1000 / fps);
  document.getElementById('fpsVal').textContent = fps.toFixed(1) + ' fps (' + ms + ' ms)';
}}

function toggleGrid() {{
  showGrid = document.getElementById('chkGrid').checked;
  render();
}}

function render() {{
  ctx.clearRect(0, 0, {W}, {H});
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
    for (let x = 0; x <= {W}; x += 8) {{
      ctx.beginPath();
      ctx.moveTo(x + 0.5, 0);
      ctx.lineTo(x + 0.5, {H});
      ctx.stroke();
    }}
    for (let y = 0; y <= {H}; y += 8) {{
      ctx.beginPath();
      ctx.moveTo(0, y + 0.5);
      ctx.lineTo({W}, y + 0.5);
      ctx.stroke();
    }}
  }}

  document.getElementById('frameInfo').textContent =
    'Frame: ' + currentFrame + ' / {N_FRAMES} (' + (currentFrame * (1000/fps) / 1000).toFixed(2) + 's)';
}}

function loop(time) {{
  if (isPlaying) {{
    const interval = 1000 / fps;
    if (time - lastTime >= interval) {{
      currentFrame = (currentFrame + 1) % {N_FRAMES};
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
    print("Plage Animée Multicalques V3 — Pipeline terminé avec succès. Tous les calques concordent à 100%.")

if __name__ == '__main__':
    build()
