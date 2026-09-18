"""Plage Animée Multicalques V3 — Generated Layer Pipeline.
Methodology:
- Separate image generations on magenta (#FF00FF) guided by arenapmdskybeach.png
- Chroma-keying with binary alpha & defringing
- Color quantization snapped to the canonical 147 PMD palette colors of arenapmdskybeach.png
- Multi-layer stack:
  00_ciel_pmd (Sky background)
  01_nuages_wrap (32-frame horizontal wrap clouds overlay, period = 768 px)
  02_eau_mer_animee (Generated sea texture on its own layer, animated via canonical 8-color PMD palette cycling, 32 frames)
  03_ecume_rivage (Shoreline foam boundary)
  04_sable_plage (Generated golden sand arena floor on its own layer)
  05_falaises_et_rochers (Generated red rock cliffs & ledges on its own layer)
  06_rochers_avant_plan (Generated foreground reefs and rocks on its own layer)
- Deliverables:
  - Transparent PNGs for all layers (Day and Night variants)
  - 32 frames of palette cycling water
  - 32 frames of cloud wrap
  - ANIMATION_WRAP.webp (32 frames, lossless loop)
  - SCENE_ANIMEE.gif and SCENE_ANIMEE_NUIT.gif
  - 02_eau_mer_animee_seule.gif
  - arene_plage_generee_editable.ora (OpenRaster multi-layer source)
  - manifest.json
  - apercu_plage_animee_multicalques_v3.html (Interactive live gallery)
"""
from pathlib import Path
import json, hashlib, base64, math, io, zipfile, xml.etree.ElementTree as ET
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
from scipy.spatial import KDTree

ROOT = Path(__file__).resolve().parents[2]
RENDERS_DIR = ROOT / 'renders/plage_animee_multicalques_v3'
EXPORTS_DIR = ROOT / 'exports/plage_animee_multicalques_v3'
BRUTS_DIR = ROOT / 'renders/arene_plage_multicalques_v2/bruts'

W, H = 768, 512
N_FRAMES = 32
FRAME_MS = 100 # 3.2s total loop

# Canonical sources
SKY_SRC = Image.open(ROOT / 'source/cote_v2/ciel_sans_nuages.png').convert('RGBA')
CLOUD_TILES = [
    (Image.open(ROOT / 'sprites/cote_v2/COTEV2_NUAGE_01.png').convert('RGBA'), 32, 24),
    (Image.open(ROOT / 'sprites/cote_v2/COTEV2_NUAGE_02.png').convert('RGBA'), 280, 48),
    (Image.open(ROOT / 'sprites/cote_v2/COTEV2_NUAGE_03.png').convert('RGBA'), 540, 16)
]
BEACH_REF = Image.open(ROOT / 'arenapmdskybeach.png').convert('RGBA')
A_REF = np.array(BEACH_REF)

# Build KDTree of the 147 canonical colors in arenapmdskybeach.png
REF_COLORS = np.unique(A_REF[:, :, :3].reshape(-1, 3), axis=0)
COLOR_TREE = KDTree(REF_COLORS)

# Canonical 8 cyclic water colors from arenapmdskybeach
CYCLE_WATER_RGB = np.array([
    [23, 63, 143],   # 0: Deep ocean blue
    [31, 79, 151],   # 1: Shallow deep blue
    [39, 87, 135],   # 2: Mid blue-cyan
    [31, 119, 167],  # 3: Medium cyan water
    [31, 135, 175],  # 4: Bright cyan wave
    [47, 167, 215],  # 5: Wave crest
    [31, 191, 231],  # 6: Wave peak
    [55, 207, 247]   # 7: Surf boundary highlight
], dtype=float)

def key_magenta(im, target_size=(W, H)):
    """Chroma keys out magenta background, resizes to target_size, and defringes."""
    resized = im.resize(target_size, Image.Resampling.NEAREST).convert('RGBA')
    a = np.array(resized)
    r = a[:, :, 0].astype(float)
    g = a[:, :, 1].astype(float)
    b = a[:, :, 2].astype(float)
    # Magenta detector
    mag = (r > 70) & (b > 65) & (r > g * 1.35) & (b > g * 1.35)
    a[mag] = 0
    a[~mag, 3] = 255
    return a

def snap_to_canonical_palette(rgba_arr):
    """Snaps visible RGB pixels to the nearest canonical PMD palette color."""
    out = rgba_arr.copy()
    mask = out[:, :, 3] > 0
    if not mask.any():
        return out
    pts = out[mask, :3]
    _, indices = COLOR_TREE.query(pts)
    out[mask, :3] = REF_COLORS[indices]
    return out

def to_night(rgba_arr):
    """Transforms a layer into its night-time palette."""
    out = rgba_arr.copy()
    v = out[:, :, :3].astype(float)
    lum = (v @ np.array([0.2126, 0.7152, 0.0722]))[:, :, None]
    out[:, :, :3] = np.rint(
        (lum * 0.20 + v * 0.80) * np.array([0.40, 0.42, 0.58]) + np.array([4, 8, 15])
    ).clip(0, 255).astype('uint8')
    out[out[:, :, 3] == 0] = 0
    return out

def get_cyclic_palette(frame_idx):
    k, t = divmod(frame_idx % N_FRAMES, 4)
    t = t / 4.0
    c0 = np.roll(CYCLE_WATER_RGB, -k, axis=0)
    c1 = np.roll(CYCLE_WATER_RGB, -(k + 1), axis=0)
    return np.rint((1 - t) * c0 + t * c1).astype('uint8')

def write_openraster(path, layers_dict, comp_img):
    """Saves a multi-layer stack in OpenRaster (.ora) standard format."""
    root = ET.Element('image', {'w': str(W), 'h': str(H), 'name': 'Arene Plage Multicalques V3'})
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

    # =========================================================================
    # Layer 00: Distant PMD Sky Background
    # =========================================================================
    sky_im = Image.new('RGBA', (W, H))
    sky_crop = SKY_SRC.crop((0, 0, W, 256))
    sky_im.paste(sky_crop, (0, 0))
    sky_arr = np.array(sky_im)
    sky_arr_night = to_night(sky_arr)
    sky_im.save(RENDERS_DIR / '00_ciel_pmd_jour.png')
    Image.fromarray(sky_arr_night).save(RENDERS_DIR / '00_ciel_pmd_nuit.png')

    # =========================================================================
    # Layer 01: Seamless PMD Cloud Wrap Strip (Period W = 768 px)
    # =========================================================================
    cloud_strip = Image.new('RGBA', (W, 240))
    for im, x, y in CLOUD_TILES:
        for shift in [-W, 0, W]:
            cloud_strip.alpha_composite(im, (x + shift, y))

    cloud_strip_arr = np.array(cloud_strip)
    cloud_frames_day = []
    cloud_frames_night = []

    shift_step = W // N_FRAMES # 24 px/frame -> 24 * 32 = 768 px exact modulo
    for f in range(N_FRAMES):
        offset = (f * shift_step) % W
        rolled = np.roll(cloud_strip_arr, offset, axis=1)
        full_cloud = np.zeros((H, W, 4), dtype=np.uint8)
        full_cloud[:240, :] = rolled
        im_c_d = Image.fromarray(full_cloud)
        im_c_n = Image.fromarray(to_night(full_cloud))
        im_c_d.save(clouds_frames_dir / f'nuages_frame_{f:02d}_jour.png')
        im_c_n.save(clouds_frames_dir / f'nuages_frame_{f:02d}_nuit.png')
        cloud_frames_day.append(im_c_d)
        cloud_frames_night.append(im_c_n)

    cloud_frames_day[0].save(RENDERS_DIR / '01_nuages_wrap_jour.png')
    cloud_frames_night[0].save(RENDERS_DIR / '01_nuages_wrap_nuit.png')

    # =========================================================================
    # Layer 02: Generated Sea Water with Canonical Palette Cycling
    # Generated brut: mer_eau_magenta.png
    # =========================================================================
    raw_sea = Image.open(BRUTS_DIR / 'mer_eau_magenta.png')
    sea_keyed = key_magenta(raw_sea, (W, H))
    yy, xx = np.mgrid[:H, :W]

    # Water occupies the coastal horizon (y in 140..350)
    # Restrict sea to water zone behind sand and cliffs
    sea_zone = (yy >= 140) & (yy <= 350) & (sea_keyed[:, :, 3] > 0)
    sea_keyed[~sea_zone] = 0

    # Extract wave pattern indices (0..7) from water brightness
    sea_lum = (sea_keyed[:, :, :3].astype(float) @ np.array([0.299, 0.587, 0.114]))
    # Add gentle diagonal spatial shift mimicking oceanic tide flow
    diag_phase = ((xx // 8) - (yy // 6)) % 8
    lum_phase = (np.clip(sea_lum / 32, 0, 7)).astype(int)
    wave_indices = ((lum_phase + diag_phase) % 8).astype(np.uint8)
    sea_alpha = (sea_zone.astype(np.uint8) * 255)

    water_frames_day = []
    water_frames_night = []
    for f in range(N_FRAMES):
        pal = get_cyclic_palette(f)
        im_p = Image.fromarray(wave_indices, mode='P')
        full_pal = np.zeros((256, 3), dtype=np.uint8)
        full_pal[:8] = pal
        im_p.putpalette(full_pal.ravel().tolist())
        im_rgba = im_p.convert('RGBA')
        w_arr = np.array(im_rgba)
        w_arr[:, :, 3] = sea_alpha
        w_arr[~sea_zone] = 0

        im_w_d = Image.fromarray(w_arr)
        im_w_n = Image.fromarray(to_night(w_arr))
        im_w_d.save(water_frames_dir / f'eau_mer_frame_{f:02d}_jour.png')
        im_w_n.save(water_frames_dir / f'eau_mer_frame_{f:02d}_nuit.png')
        water_frames_day.append(im_w_d)
        water_frames_night.append(im_w_n)

    water_frames_day[0].save(RENDERS_DIR / '02_eau_mer_animee_jour.png')
    water_frames_night[0].save(RENDERS_DIR / '02_eau_mer_animee_nuit.png')

    # =========================================================================
    # Layer 03: Shoreline Foam & Surf
    # =========================================================================
    foam_layer = np.zeros((H, W, 4), dtype=np.uint8)
    foam_patch = A_REF[96:112, 144:312]
    for x in range(120, 640, 168):
        ww = min(168, 640 - x)
        foam_layer[256:272, x:x+ww] = foam_patch[:, :ww]
    foam_im_d = Image.fromarray(foam_layer)
    foam_im_n = Image.fromarray(to_night(foam_layer))
    foam_im_d.save(RENDERS_DIR / '03_ecume_rivage_jour.png')
    foam_im_n.save(RENDERS_DIR / '03_ecume_rivage_nuit.png')

    # =========================================================================
    # Layer 04: Generated Beach Sand Arena Ground on its own layer
    # Generated brut: sable_complet_magenta.png
    # =========================================================================
    raw_sand = Image.open(BRUTS_DIR / 'sable_complet_magenta.png')
    sand_keyed = key_magenta(raw_sand, (W, H))
    # Sand arena mask: lower arena (y >= 268)
    sand_mask = (yy >= 268) & (sand_keyed[:, :, 3] > 0)
    sand_keyed[~sand_mask] = 0
    # Snap colors to canonical PMD palette
    sand_snapped = snap_to_canonical_palette(sand_keyed)

    sand_im_d = Image.fromarray(sand_snapped)
    sand_im_n = Image.fromarray(to_night(sand_snapped))
    sand_im_d.save(RENDERS_DIR / '04_sable_plage_jour.png')
    sand_im_n.save(RENDERS_DIR / '04_sable_plage_nuit.png')

    # =========================================================================
    # Layer 05: Generated Coastal Red Cliffs & Rock Formations on top of sand
    # Generated brut: falaises_rochers_magenta.png
    # =========================================================================
    raw_cliffs = Image.open(BRUTS_DIR / 'falaises_rochers_magenta.png')
    cliffs_keyed = key_magenta(raw_cliffs, (W, H))
    # Keep upper cliff terraces, side headlands, and central rock formations
    cliffs_mask = (cliffs_keyed[:, :, 3] > 0) & ((yy < 390) | (xx < 150) | (xx > 618))
    cliffs_keyed[~cliffs_mask] = 0
    # Snap colors to canonical PMD palette
    cliffs_snapped = snap_to_canonical_palette(cliffs_keyed)

    cliff_im_d = Image.fromarray(cliffs_snapped)
    cliff_im_n = Image.fromarray(to_night(cliffs_snapped))
    cliff_im_d.save(RENDERS_DIR / '05_falaises_et_rochers_jour.png')
    cliff_im_n.save(RENDERS_DIR / '05_falaises_et_rochers_nuit.png')

    # =========================================================================
    # Layer 06: Generated Foreground Reefs & Sea Stacks
    # Generated brut: recifs_avant_plan_magenta.png
    # =========================================================================
    raw_reefs = Image.open(BRUTS_DIR / 'recifs_avant_plan_magenta.png')
    reefs_keyed = key_magenta(raw_reefs, (W, H))
    # Keep bottom foreground edges (y >= 430, x < 220 or x > 548)
    reefs_mask = (reefs_keyed[:, :, 3] > 0) & ((yy >= 420) & ((xx < 220) | (xx > 548)))
    reefs_keyed[~reefs_mask] = 0
    reefs_snapped = snap_to_canonical_palette(reefs_keyed)

    reefs_im_d = Image.fromarray(reefs_snapped)
    reefs_im_n = Image.fromarray(to_night(reefs_snapped))
    reefs_im_d.save(RENDERS_DIR / '06_rochers_avant_plan_jour.png')
    reefs_im_n.save(RENDERS_DIR / '06_rochers_avant_plan_nuit.png')

    # =========================================================================
    # Full Scene Composition & Animated WebP / GIF
    # =========================================================================
    scene_frames_day = []
    scene_frames_night = []

    for f in range(N_FRAMES):
        # Day composition
        comp_d = Image.new('RGBA', (W, H))
        comp_d.alpha_composite(sky_im)
        comp_d.alpha_composite(cloud_frames_day[f])
        comp_d.alpha_composite(water_frames_day[f])
        comp_d.alpha_composite(foam_im_d)
        comp_d.alpha_composite(sand_im_d)
        comp_d.alpha_composite(cliff_im_d)
        comp_d.alpha_composite(reefs_im_d)
        scene_frames_day.append(comp_d)

        # Night composition
        comp_n = Image.new('RGBA', (W, H))
        comp_n.alpha_composite(Image.fromarray(sky_arr_night))
        comp_n.alpha_composite(cloud_frames_night[f])
        comp_n.alpha_composite(water_frames_night[f])
        comp_n.alpha_composite(foam_im_n)
        comp_n.alpha_composite(sand_im_n)
        comp_n.alpha_composite(cliff_im_n)
        comp_n.alpha_composite(reefs_im_n)
        scene_frames_night.append(comp_n)

    # Save static day/night compositions
    scene_frames_day[0].save(RENDERS_DIR / 'COMPOSITION_JOUR.png')
    scene_frames_night[0].save(RENDERS_DIR / 'COMPOSITION_NUIT.png')

    # Save animated WebP (lossless, 32 frames @ 100ms)
    scene_frames_day[0].save(
        RENDERS_DIR / 'ANIMATION_WRAP.webp',
        save_all=True,
        append_images=scene_frames_day[1:],
        duration=FRAME_MS,
        loop=0,
        lossless=True
    )

    # Save animated GIFs (reduced palette 256 colors)
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

    # Save isolated water gif
    pal_water = water_frames_day[0].convert('RGB').quantize(colors=64)
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
    # OpenRaster Multi-Layer (.ora) deliverable
    # =========================================================================
    ora_layers = {
        '00_ciel_pmd': sky_im,
        '01_nuages_wrap_phase0': cloud_frames_day[0],
        '02_eau_mer_animee_phase0': water_frames_day[0],
        '03_ecume_rivage': foam_im_d,
        '04_sable_plage': sand_im_d,
        '05_falaises_et_rochers': cliff_im_d,
        '06_rochers_avant_plan': reefs_im_d
    }
    write_openraster(RENDERS_DIR / 'arene_plage_generee_editable.ora', ora_layers, scene_frames_day[0])

    # =========================================================================
    # Manifest JSON
    # =========================================================================
    manifest = {
        'version': 'PlageAnimeeMulticalquesV3',
        'title': 'PMD Sky Beach Arena — Pure Multicalques with Generated Layers & Canonical Animations',
        'method': 'AI generation on magenta -> chroma-keying -> 147 canonical PMD color quantization -> aligned multicalques',
        'size': [W, H],
        'frames': N_FRAMES,
        'frame_ms': FRAME_MS,
        'loop_ms': N_FRAMES * FRAME_MS,
        'generated_inputs': [
            {'file': 'sable_complet_magenta.png', 'role': 'Ground sand arena floor'},
            {'file': 'falaises_rochers_magenta.png', 'role': 'Red rock cliffs and terraces'},
            {'file': 'recifs_avant_plan_magenta.png', 'role': 'Foreground coastal reefs & sea stacks'},
            {'file': 'mer_eau_magenta.png', 'role': 'Sea water surface texture for palette cycling'}
        ],
        'layers': [
            {'id': '00_ciel_pmd', 'file': '00_ciel_pmd_jour.png', 'type': 'static_sky'},
            {'id': '01_nuages_wrap', 'file': '01_nuages_wrap_jour.png', 'type': 'wrap_clouds_overlay', 'period': W, 'shift_per_frame': shift_step},
            {'id': '02_eau_mer_animee', 'file': '02_eau_mer_animee_jour.png', 'type': 'palette_cycling_water', 'cycle_colors': 8, 'phases': N_FRAMES},
            {'id': '03_ecume_rivage', 'file': '03_ecume_rivage_jour.png', 'type': 'surf_foam'},
            {'id': '04_sable_plage', 'file': '04_sable_plage_jour.png', 'type': 'generated_sand_arena'},
            {'id': '05_falaises_et_rochers', 'file': '05_falaises_et_rochers_jour.png', 'type': 'generated_red_cliffs'},
            {'id': '06_rochers_avant_plan', 'file': '06_rochers_avant_plan_jour.png', 'type': 'generated_foreground_reefs'}
        ],
        'outputs': {
            'composition_day_png': 'COMPOSITION_JOUR.png',
            'composition_night_png': 'COMPOSITION_NUIT.png',
            'animation_webp': 'ANIMATION_WRAP.webp',
            'scene_day_gif': 'SCENE_ANIMEE.gif',
            'scene_night_gif': 'SCENE_ANIMEE_NUIT.gif',
            'water_gif': '02_eau_mer_animee_seule.gif',
            'editable_ora': 'arene_plage_generee_editable.ora'
        }
    }
    (RENDERS_DIR / 'manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n')
    (EXPORTS_DIR / 'manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n')

    # =========================================================================
    # Standalone HTML5 Viewer apercu_plage_animee_multicalques_v3.html
    # =========================================================================
    def to_b64(path):
        return 'data:image/png;base64,' + base64.b64encode(path.read_bytes()).decode()

    html_data = {
        'layers_day': [
            {'id': '00_ciel_pmd', 'name': '00 · Ciel PMD', 'src': to_b64(RENDERS_DIR / '00_ciel_pmd_jour.png'), 'animated': False},
            {'id': '01_nuages_wrap', 'name': '01 · Nuages Wrap (32 frames)', 'frames': [to_b64(clouds_frames_dir / f'nuages_frame_{f:02d}_jour.png') for f in range(N_FRAMES)], 'animated': True},
            {'id': '02_eau_mer', 'name': '02 · Mer Palette Cycling (32 frames)', 'frames': [to_b64(water_frames_dir / f'eau_mer_frame_{f:02d}_jour.png') for f in range(N_FRAMES)], 'animated': True},
            {'id': '03_ecume_rivage', 'name': '03 · Écume & Clapotis Rivage', 'src': to_b64(RENDERS_DIR / '03_ecume_rivage_jour.png'), 'animated': False},
            {'id': '04_sable_plage', 'name': '04 · Sable Plage Arène (Généré)', 'src': to_b64(RENDERS_DIR / '04_sable_plage_jour.png'), 'animated': False},
            {'id': '05_falaises_rochers', 'name': '05 · Falaises & Rochers Rouges (Généré)', 'src': to_b64(RENDERS_DIR / '05_falaises_et_rochers_jour.png'), 'animated': False},
            {'id': '06_rochers_avant_plan', 'name': '06 · Récifs & Écueils Avant-Plan (Généré)', 'src': to_b64(RENDERS_DIR / '06_rochers_avant_plan_jour.png'), 'animated': False}
        ],
        'layers_night': [
            {'id': '00_ciel_pmd', 'name': '00 · Ciel PMD', 'src': to_b64(RENDERS_DIR / '00_ciel_pmd_nuit.png'), 'animated': False},
            {'id': '01_nuages_wrap', 'name': '01 · Nuages Wrap (32 frames)', 'frames': [to_b64(clouds_frames_dir / f'nuages_frame_{f:02d}_nuit.png') for f in range(N_FRAMES)], 'animated': True},
            {'id': '02_eau_mer', 'name': '02 · Mer Palette Cycling (32 frames)', 'frames': [to_b64(water_frames_dir / f'eau_mer_frame_{f:02d}_nuit.png') for f in range(N_FRAMES)], 'animated': True},
            {'id': '03_ecume_rivage', 'name': '03 · Écume & Clapotis Rivage', 'src': to_b64(RENDERS_DIR / '03_ecume_rivage_nuit.png'), 'animated': False},
            {'id': '04_sable_plage', 'name': '04 · Sable Plage Arène (Généré)', 'src': to_b64(RENDERS_DIR / '04_sable_plage_nuit.png'), 'animated': False},
            {'id': '05_falaises_rochers', 'name': '05 · Falaises & Rochers Rouges (Généré)', 'src': to_b64(RENDERS_DIR / '05_falaises_et_rochers_nuit.png'), 'animated': False},
            {'id': '06_rochers_avant_plan', 'name': '06 · Récifs & Écueils Avant-Plan (Généré)', 'src': to_b64(RENDERS_DIR / '06_rochers_avant_plan_nuit.png'), 'animated': False}
        ]
    }

    html_content = f"""<!DOCTYPE html>
<html lang="fr">
<head>
<meta charset="utf-8">
<title>Arène Plage Multicalques V3 — Calques Générés & Animations PMD</title>
<style>
  :root {{
    --bg-dark: #0f172a;
    --panel-bg: #1e293b;
    --accent: #38bdf8;
    --accent-gold: #f59e0b;
    --text-main: #f8fafc;
    --text-muted: #94a3b8;
    --border: #334155;
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
    max-width: 900px;
  }}
  h1 {{
    font-size: 24px;
    color: var(--accent);
    margin-bottom: 8px;
  }}
  p.subtitle {{
    color: var(--text-muted);
    font-size: 14px;
    line-height: 1.5;
  }}
  .main-container {{
    display: flex;
    flex-direction: row;
    gap: 24px;
    background: var(--panel-bg);
    padding: 20px;
    border-radius: 12px;
    border: 1px solid var(--border);
    box-shadow: 0 10px 25px rgba(0,0,0,0.5);
    max-width: 1200px;
  }}
  .canvas-wrapper {{
    position: relative;
    width: 768px;
    height: 512px;
    background: #000;
    border-radius: 8px;
    overflow: hidden;
    box-shadow: 0 4px 12px rgba(0,0,0,0.6);
  }}
  canvas {{
    image-rendering: pixelated;
    image-rendering: crisp-edges;
    display: block;
    width: 768px;
    height: 512px;
  }}
  .controls-sidebar {{
    width: 320px;
    display: flex;
    flex-direction: column;
    gap: 16px;
  }}
  .control-group {{
    background: #0f172a;
    padding: 14px;
    border-radius: 8px;
    border: 1px solid var(--border);
  }}
  .control-group h3 {{
    font-size: 13px;
    text-transform: uppercase;
    letter-spacing: 0.05em;
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
    background: var(--border);
    color: var(--text-main);
    border: none;
    padding: 8px 12px;
    border-radius: 6px;
    cursor: pointer;
    font-size: 12px;
    font-weight: 600;
    transition: all 0.2s;
  }}
  button.active {{
    background: var(--accent);
    color: #000;
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
</style>
</head>
<body>

<header>
  <h1>Arène Plage Multicalques V3 — Calques Générés & Animations PMD</h1>
  <p class="subtitle">Architecture multicalques pure (7 calques indépendants). Terrains générés sur magenta (#FF00FF) guidés par <code>arenapmdskybeach.png</code>, recadrés sur la palette canonique PMD (147 couleurs). Double animation synchronisée : <strong>Nuages Wrap horizontal</strong> (32 f) et <strong>Mer en Palette Cycling</strong> (32 f, 8 couleurs d'eau PMD).</p>
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
        <button id="btnNight" onclick="setMode('night')">🌙 Nuit</button>
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
      <h3>Visibilité des 7 Calques</h3>
      <div id="layerList"></div>
    </div>

    <div class="control-group">
      <h3>Affichage & Grille</h3>
      <label class="layer-item">
        <input type="checkbox" id="chkGrid" onchange="toggleGrid()">
        <span>Grille 8px PMD</span>
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
    print("Plage Animée Multicalques V3 pipeline executed successfully. All deliverables ready.")

if __name__ == '__main__':
    build()
