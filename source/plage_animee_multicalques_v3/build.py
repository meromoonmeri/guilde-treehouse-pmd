"""Plage Animée Multicalques V3 — PMD Coastal Arena with Cloud Wrap & Water Palette Cycling.
Adheres strictly to the user's specification:
- Background: distant PMD sky with PMD clouds animated in seamless wrap overlay loop
- Animated sea on its OWN CLEAN LAYER, animated the PMD way via palette cycling (32 synchronized phases)
- Sand on its OWN CLEAN LAYER
- Coastal red rock cliffs & boulders ON TOP of sand on their OWN CLEAN LAYER
- Pure multicalques: transparent PNG for every element
- Final animated WebP (ANIMATION_WRAP.webp) + GIF preview (SCENE_ANIMEE.gif)
- Interactive HTML5 viewer with real-time canvas animation & layer toggles
"""
from pathlib import Path
import json, hashlib, base64, math
import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage as nd

ROOT = Path(__file__).resolve().parents[2]
RENDERS_DIR = ROOT / 'renders/plage_animee_multicalques_v3'
EXPORTS_DIR = ROOT / 'exports/plage_animee_multicalques_v3'
W, H = 768, 512
N_FRAMES = 32
FRAME_MS = 100 # 3.2s total loop

# Load sources
SKY_SRC = Image.open(ROOT / 'source/cote_v2/ciel_sans_nuages.png').convert('RGBA')
CLOUD_TILES = [
    (Image.open(ROOT / 'sprites/cote_v2/COTEV2_NUAGE_01.png').convert('RGBA'), 32, 24),
    (Image.open(ROOT / 'sprites/cote_v2/COTEV2_NUAGE_02.png').convert('RGBA'), 280, 48),
    (Image.open(ROOT / 'sprites/cote_v2/COTEV2_NUAGE_03.png').convert('RGBA'), 540, 16)
]
BEACH_REF = Image.open(ROOT / 'arenapmdskybeach.png').convert('RGBA')
A = np.array(BEACH_REF)

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

# Canonical sand patch boxes from arenapmdskybeach
SAND_BOXES = [
    (180, 184, 204, 208), (204, 184, 228, 208), (228, 184, 252, 208), (252, 184, 276, 208),
    (180, 208, 204, 232), (204, 208, 228, 232), (228, 208, 252, 232), (252, 208, 276, 232),
    (180, 232, 204, 256), (204, 232, 228, 256), (228, 232, 252, 256), (252, 232, 276, 256),
    (180, 256, 204, 280), (204, 256, 228, 280), (228, 256, 252, 280), (252, 256, 276, 280),
    (180, 280, 204, 304), (204, 280, 228, 304), (228, 280, 252, 304), (252, 280, 276, 304)
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

def get_cyclic_palette(frame_idx):
    k, t = divmod(frame_idx % N_FRAMES, 4)
    t = t / 4.0
    c0 = np.roll(CYCLE_WATER_RGB, -k, axis=0)
    c1 = np.roll(CYCLE_WATER_RGB, -(k + 1), axis=0)
    return np.rint((1 - t) * c0 + t * c1).astype('uint8')

def build():
    RENDERS_DIR.mkdir(parents=True, exist_ok=True)
    EXPORTS_DIR.mkdir(parents=True, exist_ok=True)
    water_frames_dir = RENDERS_DIR / '02_eau_mer_palette_cycling'
    clouds_frames_dir = RENDERS_DIR / '01_nuages_wrap_frames'
    water_frames_dir.mkdir(exist_ok=True)
    clouds_frames_dir.mkdir(exist_ok=True)

    # -------------------------------------------------------------
    # Layer 00: Distant PMD Sky
    # -------------------------------------------------------------
    sky_im = Image.new('RGBA', (W, H))
    sky_crop = SKY_SRC.crop((0, 0, W, 256))
    sky_im.paste(sky_crop, (0, 0))
    sky_arr = np.array(sky_im)
    sky_arr_night = to_night(sky_arr)
    sky_im.save(RENDERS_DIR / '00_ciel_pmd_jour.png')
    Image.fromarray(sky_arr_night).save(RENDERS_DIR / '00_ciel_pmd_nuit.png')

    # -------------------------------------------------------------
    # Layer 01: Seamless PMD Cloud Wrap Strip (Period W = 768 px)
    # -------------------------------------------------------------
    cloud_strip = Image.new('RGBA', (W, 240))
    for im, x, y in CLOUD_TILES:
        for shift in [-W, 0, W]:
            cloud_strip.alpha_composite(im, (x + shift, y))

    cloud_strip_arr = np.array(cloud_strip)
    cloud_frames_day = []
    cloud_frames_night = []

    shift_step = W // N_FRAMES # 24 px per frame
    for f in range(N_FRAMES):
        offset = (f * shift_step) % W
        rolled = np.roll(cloud_strip_arr, offset, axis=1)
        full_cloud = np.zeros((H, W, 4), dtype=np.uint8)
        full_cloud[:240, :] = rolled
        im_c_d = Image.fromarray(full_cloud)
        im_c_n = Image.fromarray(to_night(full_cloud))
        im_c_d.save(clouds_frames_dir / f'nuages_frame_{f:02d}_jour.png')
        cloud_frames_day.append(im_c_d)
        cloud_frames_night.append(im_c_n)

    # Save static cloud reference (phase 0)
    cloud_frames_day[0].save(RENDERS_DIR / '01_nuages_wrap_jour.png')
    cloud_frames_night[0].save(RENDERS_DIR / '01_nuages_wrap_nuit.png')

    # -------------------------------------------------------------
    # Layer 02: Animated Coastal Sea on its OWN CLEAN LAYER
    # -------------------------------------------------------------
    yy, xx = np.mgrid[:H, :W]
    # Sea spans across the middle horizon (y in 140..340), behind the beach shoreline
    sea_mask = (yy >= 144) & (yy <= 340) & ~((yy > 260) & (xx > 180) & (xx < 588))
    # Diagonal wave movement mimicking natural surf flow
    wave_indices = (((xx // 8) - (yy // 6)) % 8).astype(np.uint8)
    sea_alpha = (sea_mask.astype(np.uint8) * 255)

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
        w_arr[~sea_mask] = [0, 0, 0, 0]

        im_w_d = Image.fromarray(w_arr)
        im_w_n = Image.fromarray(to_night(w_arr))
        im_w_d.save(water_frames_dir / f'eau_mer_frame_{f:02d}_jour.png')
        water_frames_day.append(im_w_d)
        water_frames_night.append(im_w_n)

    # Save static water reference (phase 0)
    water_frames_day[0].save(RENDERS_DIR / '02_eau_mer_animee_jour.png')
    water_frames_night[0].save(RENDERS_DIR / '02_eau_mer_animee_nuit.png')

    # -------------------------------------------------------------
    # Layer 03: Shoreline Foam & Surf
    # -------------------------------------------------------------
    foam_layer = np.zeros((H, W, 4), dtype=np.uint8)
    # Extract authentic foam from arenapmdskybeach (x=144..312, y=96..112)
    foam_patch = A[96:112, 144:312]
    for x in range(160, 560, 168):
        ww = min(168, 560 - x)
        foam_layer[256:272, x:x+ww] = foam_patch[:, :ww]
    foam_im_d = Image.fromarray(foam_layer)
    foam_im_n = Image.fromarray(to_night(foam_layer))
    foam_im_d.save(RENDERS_DIR / '03_ecume_rivage_jour.png')
    foam_im_n.save(RENDERS_DIR / '03_ecume_rivage_nuit.png')

    # -------------------------------------------------------------
    # Layer 04: Beach Sand Ground on its OWN CLEAN LAYER
    # -------------------------------------------------------------
    sand_layer = np.zeros((H, W, 4), dtype=np.uint8)
    # Sand arena shape: spacious central arena in lower half (y >= 268)
    sand_mask = (yy >= 268) & (xx >= 120) & (xx <= 648)
    rng = np.random.default_rng(88)
    hh, ww, ov = 24, 24, 8
    for y in range(268, H, hh - ov):
        for x in range(120, 648, ww - ov):
            h = min(hh, H - y)
            w = min(ww, 648 - x)
            want = sand_mask[y:y+h, x:x+w]
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
            if x > 120 and w >= ov:
                take[:, :ov] &= np.arange(ov)[None, :] >= seam(cost[:, :ov])[:, None]
            if y > 268 and h >= ov:
                take[:ov, :] &= np.arange(ov)[:, None] >= seam(cost[:ov, :].T)[None, :]
            take |= want & (old[:, :, 3] == 0)
            old[take] = patch[take]

    sand_im_d = Image.fromarray(sand_layer)
    sand_im_n = Image.fromarray(to_night(sand_layer))
    sand_im_d.save(RENDERS_DIR / '04_sable_plage_jour.png')
    sand_im_n.save(RENDERS_DIR / '04_sable_plage_nuit.png')

    # -------------------------------------------------------------
    # Layer 05: Coastal Red Rock Cliffs ON TOP of Sand
    # -------------------------------------------------------------
    cliff_layer = np.zeros((H, W, 4), dtype=np.uint8)
    # West cliff massif (from x=0..160, y=80..380 of source)
    p_w = A[80:360, 0:140]
    mask_w = ~np.all(p_w[:, :, :3] == [39, 39, 55], axis=2) & (p_w[:, :, 3] > 0)
    cliff_layer[120:400, 0:140][mask_w] = p_w[mask_w]

    # East cliff massif (from x=316..456, y=80..380 of source)
    p_e = A[80:360, 316:456]
    mask_e = ~np.all(p_e[:, :, :3] == [39, 39, 55], axis=2) & (p_e[:, :, 3] > 0)
    cliff_layer[120:400, 628:768][mask_e] = p_e[mask_e]

    # North Red Cliff Arch framing the sea horizon
    p_arch = A[40:112, 140:320]
    mask_arch = ~np.all(p_arch[:, :, :3] == [39, 39, 55], axis=2) & (p_arch[:, :, 3] > 0)
    cliff_layer[80:152, 294:474][mask_arch] = p_arch[mask_arch]

    cliff_im_d = Image.fromarray(cliff_layer)
    cliff_im_n = Image.fromarray(to_night(cliff_layer))
    cliff_im_d.save(RENDERS_DIR / '05_falaises_et_rochers_jour.png')
    cliff_im_n.save(RENDERS_DIR / '05_falaises_et_rochers_nuit.png')

    # -------------------------------------------------------------
    # Layer 06: Foreground Coastal Rocks & Sea Stacks
    # -------------------------------------------------------------
    rocks_layer = np.zeros((H, W, 4), dtype=np.uint8)
    # SW foreground reef
    p_sw = A[416:480, 0:180]
    mask_sw = ~np.all(p_sw[:, :, :3] == [39, 39, 55], axis=2)
    rocks_layer[448:512, 0:180][mask_sw] = p_sw[mask_sw]

    # SE foreground reef
    p_se = A[416:480, 276:456]
    mask_se = ~np.all(p_se[:, :, :3] == [39, 39, 55], axis=2)
    rocks_layer[448:512, 588:768][mask_se] = p_se[mask_se]

    # Sea stack in west shallows
    p_stack = A[240:280, 330:370]
    mask_stack = ~np.all(p_stack[:, :, :3] == [39, 39, 55], axis=2)
    rocks_layer[210:250, 80:120][mask_stack] = p_stack[mask_stack]

    rocks_im_d = Image.fromarray(rocks_layer)
    rocks_im_n = Image.fromarray(to_night(rocks_layer))
    rocks_im_d.save(RENDERS_DIR / '06_rochers_avant_plan_jour.png')
    rocks_im_n.save(RENDERS_DIR / '06_rochers_avant_plan_nuit.png')

    # -------------------------------------------------------------
    # 32 Composite Frames & Final Animated WebP / GIF
    # -------------------------------------------------------------
    scene_frames_day = []
    scene_frames_night = []

    for f in range(N_FRAMES):
        sc_d = Image.new('RGBA', (W, H))
        sc_n = Image.new('RGBA', (W, H))

        # 00: Ciel
        sc_d.alpha_composite(sky_im)
        sc_n.alpha_composite(Image.fromarray(sky_arr_night))

        # 01: Nuages wrap
        sc_d.alpha_composite(cloud_frames_day[f])
        sc_n.alpha_composite(cloud_frames_night[f])

        # 02: Eau mer animée
        sc_d.alpha_composite(water_frames_day[f])
        sc_n.alpha_composite(water_frames_night[f])

        # 03: Écume
        sc_d.alpha_composite(foam_im_d)
        sc_n.alpha_composite(foam_im_n)

        # 04: Sable
        sc_d.alpha_composite(sand_im_d)
        sc_n.alpha_composite(sand_im_n)

        # 05: Falaises et rochers sur le sable
        sc_d.alpha_composite(cliff_im_d)
        sc_n.alpha_composite(cliff_im_n)

        # 06: Rochers d'avant-plan
        sc_d.alpha_composite(rocks_im_d)
        sc_n.alpha_composite(rocks_im_n)

        scene_frames_day.append(sc_d)
        scene_frames_night.append(sc_n)

    # Save static composites
    scene_frames_day[0].save(RENDERS_DIR / 'COMPOSITION_JOUR.png')
    scene_frames_night[0].save(RENDERS_DIR / 'COMPOSITION_NUIT.png')

    # Save final animated WebP (lossless, method=4, loop=0)
    scene_frames_day[0].save(
        RENDERS_DIR / 'ANIMATION_WRAP.webp',
        save_all=True,
        append_images=scene_frames_day[1:],
        duration=FRAME_MS,
        loop=0,
        lossless=True,
        method=4
    )
    # Save animated GIF preview
    scene_frames_day[0].save(
        RENDERS_DIR / 'SCENE_ANIMEE.gif',
        save_all=True,
        append_images=scene_frames_day[1:],
        duration=FRAME_MS,
        loop=0
    )
    scene_frames_night[0].save(
        RENDERS_DIR / 'SCENE_ANIMEE_NUIT.gif',
        save_all=True,
        append_images=scene_frames_night[1:],
        duration=FRAME_MS,
        loop=0
    )

    # Save isolated water animation GIF
    water_frames_day[0].save(
        RENDERS_DIR / '02_eau_mer_animee_seule.gif',
        save_all=True,
        append_images=water_frames_day[1:],
        duration=FRAME_MS,
        loop=0,
        disposal=2
    )

    # Save manifest
    manifest = dict(
        version='PlageAnimeeMulticalquesV3',
        title='PMD Sky Beach Arena — Wrap Clouds & Palette Cycling Water Multicalques',
        size=[W, H],
        frames=N_FRAMES,
        frame_ms=FRAME_MS,
        loop_ms=N_FRAMES * FRAME_MS,
        layers=[
            dict(id='00_ciel_pmd', file='00_ciel_pmd_jour.png', type='static_sky'),
            dict(id='01_nuages_wrap', file='01_nuages_wrap_jour.png', type='wrap_clouds_overlay', period=W, shift_per_frame=shift_step),
            dict(id='02_eau_mer_animee', file='02_eau_mer_animee_jour.png', type='palette_cycling_water', cycle_colors=8, phases=N_FRAMES),
            dict(id='03_ecume_rivage', file='03_ecume_rivage_jour.png', type='surf_foam'),
            dict(id='04_sable_plage', file='04_sable_plage_jour.png', type='quilted_sand_arena'),
            dict(id='05_falaises_et_rochers', file='05_falaises_et_rochers_jour.png', type='red_cliffs_over_sand'),
            dict(id='06_rochers_avant_plan', file='06_rochers_avant_plan_jour.png', type='foreground_reefs')
        ],
        outputs=dict(
            composition_png='COMPOSITION_JOUR.png',
            animation_webp='ANIMATION_WRAP.webp',
            scene_gif='SCENE_ANIMEE.gif',
            scene_night_gif='SCENE_ANIMEE_NUIT.gif',
            water_gif='02_eau_mer_animee_seule.gif'
        )
    )
    (RENDERS_DIR / 'manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n')
    (EXPORTS_DIR / 'manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n')

    # Build interactive standalone HTML5 viewer
    def uri(path):
        return 'data:image/png;base64,' + base64.b64encode(path.read_bytes()).decode()

    layer_uris = {
        'ciel_d': uri(RENDERS_DIR / '00_ciel_pmd_jour.png'),
        'ciel_n': uri(RENDERS_DIR / '00_ciel_pmd_nuit.png'),
        'nuages_strip': uri(RENDERS_DIR / '01_nuages_wrap_jour.png'),
        'ecume_d': uri(RENDERS_DIR / '03_ecume_rivage_jour.png'),
        'ecume_n': uri(RENDERS_DIR / '03_ecume_rivage_nuit.png'),
        'sable_d': uri(RENDERS_DIR / '04_sable_plage_jour.png'),
        'sable_n': uri(RENDERS_DIR / '04_sable_plage_nuit.png'),
        'falaises_d': uri(RENDERS_DIR / '05_falaises_et_rochers_jour.png'),
        'falaises_n': uri(RENDERS_DIR / '05_falaises_et_rochers_nuit.png'),
        'rochers_d': uri(RENDERS_DIR / '06_rochers_avant_plan_jour.png'),
        'rochers_n': uri(RENDERS_DIR / '06_rochers_avant_plan_nuit.png'),
    }

    # Water frames uris (first 8 phases)
    water_uris = [uri(water_frames_dir / f'eau_mer_frame_{f:02d}_jour.png') for f in range(N_FRAMES)]

    html = '''<!doctype html>
<html lang="fr">
<head>
<meta charset="utf-8">
<title>Arène Plage PMD · Multicalques & Wrap / Palette Cycling</title>
<style>
  body { background: #111a22; color: #e1e9f0; font: 15px -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; margin: 0; padding: 24px; }
  header { max-width: 1250px; margin: 0 auto 20px; padding-bottom: 16px; border-bottom: 1px solid #233948; }
  h1 { font-size: 26px; color: #ffd677; margin: 0 0 6px; }
  p.sub { color: #9bb5c7; margin: 0; line-height: 1.55; }
  .workspace { display: flex; gap: 28px; max-width: 1250px; margin: 0 auto; flex-wrap: wrap; }
  .viewport-panel { background: #16242e; border: 1px solid #284457; border-radius: 12px; padding: 20px; box-shadow: 0 8px 24px rgba(0,0,0,0.5); }
  .canvas-box { position: relative; width: 768px; height: 512px; background: #080e12; border: 1px solid #243b4c; border-radius: 6px; overflow: hidden; margin-bottom: 14px; }
  canvas { display: block; image-rendering: pixelated; width: 768px; height: 512px; }
  .toolbar { display: flex; gap: 10px; margin-bottom: 14px; align-items: center; }
  button { background: #213a4c; color: #d9e7f2; border: 1px solid #365e7a; padding: 6px 14px; border-radius: 6px; cursor: pointer; font-size: 13px; }
  button:hover { background: #2c4d66; }
  button.active { background: #e0b04c; color: #0d161d; font-weight: bold; border-color: #ffd277; }
  .side-panel { flex: 1; min-width: 320px; background: #16242e; border: 1px solid #284457; border-radius: 12px; padding: 20px; }
  h2 { font-size: 20px; color: #ffd277; margin: 0 0 8px; }
  p.desc { font-size: 14px; color: #b1c7d6; line-height: 1.5; margin: 0 0 16px; }
  .layer-group { background: #0e1820; border: 1px solid #1f3544; border-radius: 8px; padding: 14px; margin-bottom: 16px; }
  .layer-group h3 { font-size: 14px; text-transform: uppercase; color: #7cb0d4; margin: 0 0 10px; letter-spacing: 0.5px; }
  label { display: flex; align-items: center; gap: 8px; font-size: 13px; color: #d2e2ee; margin-bottom: 8px; cursor: pointer; }
  label:hover { color: #fff; }
  .badge { display: inline-block; padding: 2px 7px; border-radius: 4px; font-size: 11px; font-weight: bold; }
  .badge-anim { background: #124d6d; color: #76d4ff; border: 1px solid #1a6f9c; }
  .badge-layer { background: #225134; color: #8fe8b1; }
  .info-box { background: #0e1820; border-left: 3px solid #e0b04c; padding: 10px 14px; font-size: 12px; color: #9bb3c4; line-height: 1.5; }
  .links { margin-top: 14px; }
  .links a { color: #fed677; text-decoration: none; font-size: 13px; margin-right: 14px; }
  .links a:hover { text-decoration: underline; }
</style>
</head>
<body>
<header>
  <h1>Arène Plage PMD · Multicalques & Nuages Wrap / Palette Cycling</h1>
  <p class="sub">
    Architecture fidèle à la méthode de l'ancien agent :<br>
    • <strong>Ciel et Nuages PMD :</strong> Nuages animés en <em>wrap overlay</em> horizontal avec boucle parfaite de 3,2 s (768 px modulo).<br>
    • <strong>Eau de mer sur son propre calque propre :</strong> Animée en <em>palette cycling</em> canonique (32 phases synchronisées avec le wrap).<br>
    • <strong>Sable sur son propre calque indépendant :</strong> Surface de combat dorée continue.<br>
    • <strong>Falaises et rochers rouges au-dessus du sable :</strong> Massifs côtiers sur leur propre calque dédié.<br>
    • <strong>Export WebP animé :</strong> <code>ANIMATION_WRAP.webp</code> (boucle sans perte 32 frames).
  </p>
</header>

<div class="workspace">
  <div class="viewport-panel">
    <div class="toolbar">
      <button id="btn-day" class="active" onclick="setMode('jour')">☀️ Jour</button>
      <button id="btn-night" onclick="setMode('nuit')">🌙 Nuit Abyss</button>
      <button id="btn-grid" onclick="toggleGrid()">Grille 8px</button>
      <button id="btn-play" class="active" onclick="togglePlay()">⏸️ Pause</button>
      <span id="speed-indicator" style="font-size:12px;color:#9bb5c7;margin-left:auto;">Cadence : 100 ms (3,2 s / boucle)</span>
    </div>
    <div class="canvas-box">
      <canvas id="view" width="768" height="512"></canvas>
    </div>
    <div class="links">
      <a href="renders/plage_animee_multicalques_v3/ANIMATION_WRAP.webp" target="_blank">📥 Voir ANIMATION_WRAP.webp</a>
      <a href="renders/plage_animee_multicalques_v3/SCENE_ANIMEE.gif" target="_blank">📥 Voir SCENE_ANIMEE.gif</a>
      <a href="renders/plage_animee_multicalques_v3/02_eau_mer_animee_seule.gif" target="_blank">📥 Eau de mer seule (GIF)</a>
    </div>
  </div>

  <div class="side-panel">
    <h2>Contrôle des Calques Indépendants</h2>
    <p class="desc">Chaque élément est généré et découpé sur son propre calque. Cochez / décochez pour vérifier l'indépendance parfaite du sable, des falaises, de l'eau animée et des nuages.</p>
    <div class="layer-group">
      <h3>Calques de Scène</h3>
      <label><input type="checkbox" id="chk-ciel" checked onchange="render()"> 00 · Ciel PMD lointain <span class="badge badge-layer">STATIQUE</span></label>
      <label><input type="checkbox" id="chk-nuages" checked onchange="render()"> 01 · Nuages PMD (Wrap Overlay) <span class="badge badge-anim">WRAP 24px/f</span></label>
      <label><input type="checkbox" id="chk-eau" checked onchange="render()"> 02 · Eau de mer (Cycling Panel) <span class="badge badge-anim">CYCLING 8-RGB</span></label>
      <label><input type="checkbox" id="chk-ecume" checked onchange="render()"> 03 · Écume & rivage <span class="badge badge-layer">CALQUE PROPRE</span></label>
      <label><input type="checkbox" id="chk-sable" checked onchange="render()"> 04 · Sable de plage (Sol) <span class="badge badge-layer">CALQUE PROPRE</span></label>
      <label><input type="checkbox" id="chk-falaises" checked onchange="render()"> 05 · Falaises & rochers rouges <span class="badge badge-layer">DESSUS SABLE</span></label>
      <label><input type="checkbox" id="chk-rochers" checked onchange="render()"> 06 · Récifs d'avant-plan <span class="badge badge-layer">AVANT-PLAN</span></label>
    </div>
    <div class="info-box">
      <strong>Boucle mathématique exacte :</strong> 32 frames × 24 px de décalage = exactement 768 px (largeur exacte de la scène). Les nuages et le cycling de palette reviennent simultanément à leur pose initiale au tick 32, sans aucun ressaut visuel.
    </div>
  </div>
</div>

<script>
const LAYERS = __LAYERS__;
const WATER_FRAMES = __WATER_FRAMES__;
const N = 32;
let frame = 0;
let running = true;
let mode = 'jour';
let grid = false;

const canvas = document.getElementById('view');
const ctx = canvas.getContext('2d');

const imgs = {};
function loadAll() {
  Object.entries(LAYERS).forEach(([k, u]) => {
    const im = new Image(); im.src = u; imgs[k] = im;
  });
  imgs['water'] = WATER_FRAMES.map(u => {
    const im = new Image(); im.src = u; return im;
  });
}
loadAll();

function setMode(m) {
  mode = m;
  document.getElementById('btn-day').classList.toggle('active', m === 'jour');
  document.getElementById('btn-night').classList.toggle('active', m === 'nuit');
  render();
}

function toggleGrid() {
  grid = !grid;
  document.getElementById('btn-grid').classList.toggle('active', grid);
  render();
}

function togglePlay() {
  running = !running;
  document.getElementById('btn-play').classList.toggle('active', running);
  document.getElementById('btn-play').textContent = running ? '⏸️ Pause' : '▶️ Reprendre';
}

function render() {
  ctx.clearRect(0, 0, 768, 512);

  // 00: Ciel
  if (document.getElementById('chk-ciel').checked) {
    const imSky = imgs[mode === 'jour' ? 'ciel_d' : 'ciel_n'];
    if (imSky && imSky.complete) ctx.drawImage(imSky, 0, 0);
  }

  // 01: Nuages Wrap Overlay
  if (document.getElementById('chk-nuages').checked) {
    const imClouds = imgs['nuages_strip'];
    if (imClouds && imClouds.complete) {
      const shift = (frame * 24) % 768;
      // Draw wrapped
      ctx.drawImage(imClouds, shift, 0);
      ctx.drawImage(imClouds, shift - 768, 0);
    }
  }

  // 02: Eau de mer en Palette Cycling
  if (document.getElementById('chk-eau').checked) {
    const wIm = imgs['water'][frame % N];
    if (wIm && wIm.complete) {
      if (mode === 'nuit') {
        ctx.save();
        ctx.filter = 'brightness(0.55) contrast(0.9) hue-rotate(-20deg)';
        ctx.drawImage(wIm, 0, 0);
        ctx.restore();
      } else {
        ctx.drawImage(wIm, 0, 0);
      }
    }
  }

  // 03: Écume
  if (document.getElementById('chk-ecume').checked) {
    const imF = imgs[mode === 'jour' ? 'ecume_d' : 'ecume_n'];
    if (imF && imF.complete) ctx.drawImage(imF, 0, 0);
  }

  // 04: Sable
  if (document.getElementById('chk-sable').checked) {
    const imS = imgs[mode === 'jour' ? 'sable_d' : 'sable_n'];
    if (imS && imS.complete) ctx.drawImage(imS, 0, 0);
  }

  // 05: Falaises et rochers
  if (document.getElementById('chk-falaises').checked) {
    const imC = imgs[mode === 'jour' ? 'falaises_d' : 'falaises_n'];
    if (imC && imC.complete) ctx.drawImage(imC, 0, 0);
  }

  // 06: Rochers d'avant-plan
  if (document.getElementById('chk-rochers').checked) {
    const imR = imgs[mode === 'jour' ? 'rochers_d' : 'rochers_n'];
    if (imR && imR.complete) ctx.drawImage(imR, 0, 0);
  }

  // Grille 8px
  if (grid) {
    ctx.strokeStyle = 'rgba(255, 255, 255, 0.15)';
    ctx.lineWidth = 1;
    for (let x = 0; x <= 768; x += 8) {
      ctx.beginPath(); ctx.moveTo(x, 0); ctx.lineTo(x, 512); ctx.stroke();
    }
    for (let y = 0; y <= 512; y += 8) {
      ctx.beginPath(); ctx.moveTo(0, y); ctx.lineTo(768, y); ctx.stroke();
    }
  }
}

// Tick loop (100 ms per frame)
setInterval(() => {
  if (running) {
    frame = (frame + 1) % N;
    render();
  }
}, 100);

// Initial render
setTimeout(render, 150);
</script>
</body>
</html>
'''
    full_html = html.replace('__LAYERS__', json.dumps(layer_uris, ensure_ascii=False)).replace('__WATER_FRAMES__', json.dumps(water_uris, ensure_ascii=False))
    (ROOT / 'apercu_plage_animee_multicalques_v3.html').write_text(full_html, encoding='utf-8')
    print('Plage Animée Multicalques V3 built successfully. WebP and HTML viewer ready.')

if __name__ == '__main__':
    build()
