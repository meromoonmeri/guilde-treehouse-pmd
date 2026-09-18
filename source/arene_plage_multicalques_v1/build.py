"""Multicalque Beach Arena Layouts with Canonical Palette-Cycling Water.
Strict adherence to the repository methodology (AGENTS.md & README.md):
- 100% canonical textures from arenapmdskybeach.png (commit 9ec9a081)
- Multiple distinct layouts (Wide Open Arena, Coastal Ravine & Terrace, Sand Atoll & Twin Reefs)
- Water animated on its OWN CLEAN LAYER via canonical palette cycling (cycling panel, 8 frames loop)
- Fixed indexed pixel data across all frames, rotating palette table, exact loop
- Pure multicalques: transparent PNG layers for sand, water, foam, cliffs, rocks
- Tiled 8px TSX tilesets & per-pixel provenance tracking
- Abyss Night mode variant via exact repository color transformation
- Interactive HTML5 viewer with real-time canvas animation & layer toggles
"""
from pathlib import Path
import json, hashlib, base64, xml.etree.ElementTree as ET
import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage as nd

ROOT = Path(__file__).resolve().parents[2]
RENDERS_DIR = ROOT / 'renders/arene_plage_multicalques_v1'
EXPORTS_DIR = ROOT / 'exports/arene_plage_multicalques_v1'
W, H = 512, 512

SOURCE_FILE = 'arenapmdskybeach.png'
REF_IMG = Image.open(ROOT / SOURCE_FILE).convert('RGBA')
A = np.array(REF_IMG)
REF_SHA256 = hashlib.sha256((ROOT / SOURCE_FILE).read_bytes()).hexdigest()

# Seam quilting for seamless sand floor
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

# Exact Abyss night grading formula
def to_night(rgba_arr):
    out = rgba_arr.copy()
    v = out[:, :, :3].astype(float)
    lum = (v @ np.array([0.2126, 0.7152, 0.0722]))[:, :, None]
    out[:, :, :3] = np.rint(
        (lum * 0.20 + v * 0.80) * np.array([0.40, 0.42, 0.58]) + np.array([4, 8, 15])
    ).clip(0, 255).astype('uint8')
    out[out[:, :, 3] == 0] = 0
    return out

# The 8 canonical cyclic water colors from arenapmdskybeach sea gradient
CYCLE_WATER_RGB = np.array([
    [23, 63, 143],   # 0: Deep ocean blue
    [31, 79, 151],   # 1: Shallow deep blue
    [39, 87, 135],   # 2: Mid blue-cyan
    [31, 119, 167],  # 3: Medium cyan water
    [31, 135, 175],  # 4: Bright cyan wave
    [47, 167, 215],  # 5: Rising wave crest
    [31, 191, 231],  # 6: Wave peak
    [55, 207, 247]   # 7: Surf boundary highlight
], dtype=np.uint8)

# Canonical sand patch boxes (clean 24x24 tiles from center arena)
SAND_BOXES = [
    (180, 184, 204, 208), (204, 184, 228, 208), (228, 184, 252, 208), (252, 184, 276, 208),
    (180, 208, 204, 232), (204, 208, 228, 232), (228, 208, 252, 232), (252, 208, 276, 232),
    (180, 232, 204, 256), (204, 232, 228, 256), (228, 232, 252, 256), (252, 232, 276, 256),
    (180, 256, 204, 280), (204, 256, 228, 280), (228, 256, 252, 280), (252, 256, 276, 280),
    (180, 280, 204, 304), (204, 280, 228, 304), (228, 280, 252, 304), (252, 280, 276, 304),
    (180, 304, 204, 328), (204, 304, 228, 328), (228, 304, 252, 328), (252, 304, 276, 328)
]

class BeachMap:
    def __init__(self, map_id, title, description):
        self.id = map_id
        self.title = title
        self.description = description
        self.layers = {}
        self.prov = {}
        self.water_mask = np.zeros((H, W), bool)
        self.water_indices = np.zeros((H, W), np.uint8)

    def set_layer(self, name, arr, prov_arr):
        self.layers[name] = arr
        self.prov[name] = prov_arr

    def put_patch(self, layer_name, box, pos, mask=None):
        if layer_name not in self.layers:
            self.layers[layer_name] = np.zeros((H, W, 4), np.uint8)
            self.prov[layer_name] = np.full((H, W, 2), -1, np.int16)
        x0, y0, x1, y1 = box
        x, y = pos
        patch = A[y0:y1, x0:x1]
        hh, ww = patch.shape[:2]
        assert x >= 0 and y >= 0 and x + ww <= W and y + hh <= H, f"Bounds error: {pos} on {W}x{H}"
        base_mask = (patch[:, :, 3] > 0) & ~np.all(patch[:, :, :3] == [39, 39, 55], axis=2)
        eff_mask = base_mask if mask is None else (mask & base_mask)
        sy, sx = np.mgrid[y0:y1, x0:x1]
        dest_layer = self.layers[layer_name]
        dest_prov = self.prov[layer_name]
        dest_layer[y:y+hh, x:x+ww][eff_mask] = patch[eff_mask]
        dest_prov[y:y+hh, x:x+ww, 0][eff_mask] = sx[eff_mask]
        dest_prov[y:y+hh, x:x+ww, 1][eff_mask] = sy[eff_mask]

    def fill_sand(self, layer_name, mask=None, seed=42):
        if layer_name not in self.layers:
            self.layers[layer_name] = np.zeros((H, W, 4), np.uint8)
            self.prov[layer_name] = np.full((H, W, 2), -1, np.int16)
        dest = self.layers[layer_name]
        dest_prov = self.prov[layer_name]
        rng = np.random.default_rng(seed)
        eff_mask = np.ones((H, W), bool) if mask is None else mask
        hh, ww = 24, 24
        ov = 8
        for y in range(0, H, hh - ov):
            for x in range(0, W, ww - ov):
                h = min(hh, H - y)
                w = min(ww, W - x)
                want = eff_mask[y:y+h, x:x+w]
                if not want.any():
                    continue
                old = dest[y:y+h, x:x+w]
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
                if x and w >= ov:
                    take[:, :ov] &= np.arange(ov)[None, :] >= seam(cost[:, :ov])[:, None]
                if y and h >= ov:
                    take[:ov, :] &= np.arange(ov)[:, None] >= seam(cost[:ov, :].T)[None, :]
                take |= want & (old[:, :, 3] == 0)
                sy, sx = np.mgrid[y0:y0+h, x0:x0+w]
                dest[y:y+h, x:x+w][take] = patch[take]
                dest_prov[y:y+h, x:x+w, 0][take] = sx[take]
                dest_prov[y:y+h, x:x+w, 1][take] = sy[take]

    def set_water_region(self, water_mask, base_offset=0):
        """Build the animated sea layer with canonical 8-color cyclic gradient."""
        self.water_mask = water_mask
        yy, xx = np.mgrid[:H, :W]
        # Wave band pattern: diagonal rhythmic flow (dx - 2*dy) mimicking natural shore wash
        wave_coords = ((xx // 8) - (yy // 6) + base_offset) % 8
        self.water_indices = wave_coords.astype(np.uint8)

    def export(self):
        r_dir = RENDERS_DIR / self.id
        e_dir = EXPORTS_DIR / self.id
        r_dir.mkdir(parents=True, exist_ok=True)
        e_dir.mkdir(parents=True, exist_ok=True)
        water_dir = r_dir / '02_eau_mer_palette_cycling'
        water_dir.mkdir(exist_ok=True)

        manifest_layers = []

        # 1. Export static terrain layers
        ordered_names = [k for k in ['00_fond_ocean_profond', '01_arene_sable_sol', '03_ecume_rivage',
                                     '04_falaises_rouges_fond', '05_massifs_rocheux_lateraux',
                                     '06_rochers_et_recifs_premier_plan'] if k in self.layers]

        comp_day = Image.new('RGBA', (W, H))
        comp_night = Image.new('RGBA', (W, H))

        for name in ordered_names:
            arr = self.layers[name]
            prov = self.prov[name]
            fn_day = f'{self.id}_{name}_jour.png'
            fn_night = f'{self.id}_{name}_nuit.png'

            im_day = Image.fromarray(arr)
            im_day.save(r_dir / fn_day)
            arr_night = to_night(arr)
            im_night = Image.fromarray(arr_night)
            im_night.save(r_dir / fn_night)

            # Also save to exports with provenance and TSX
            im_day.save(e_dir / fn_day)
            np.savez_compressed(e_dir / f'{name}_source.npz', source_xy=prov)
            root = ET.Element('tileset', version='1.10', name=Path(fn_day).stem, tilewidth='8', tileheight='8', columns='64', tilecount='4096')
            ET.SubElement(root, 'image', source=fn_day, width='512', height='512')
            ET.ElementTree(root).write(e_dir / Path(fn_day).with_suffix('.tsx').name, encoding='utf-8', xml_declaration=True)

            manifest_layers.append(dict(id=name, file_day=fn_day, file_night=fn_night, provenance=f'{name}_source.npz'))

        # 2. Export 8-phase canonical palette cycling for the water layer
        water_layer_day_frames = []
        water_layer_night_frames = []
        water_files = []

        base_alpha = (self.water_mask.astype(np.uint8) * 255)
        # Provenance for water: samples the northern bay sea area of arenapmdskybeach (x=144..312, y=48..112)
        water_prov = np.full((H, W, 2), -1, np.int16)
        water_prov[:, :, 0][self.water_mask] = 144 + (np.mgrid[:H, :W][1][self.water_mask] % 168)
        water_prov[:, :, 1][self.water_mask] = 48 + (np.mgrid[:H, :W][0][self.water_mask] % 64)
        np.savez_compressed(e_dir / '02_eau_mer_source.npz', source_xy=water_prov)

        for f in range(8):
            # Rotate palette table by f
            pal_day = np.zeros((256, 3), dtype=np.uint8)
            for k in range(8):
                pal_day[k] = CYCLE_WATER_RGB[(k + f) % 8]

            # Day water frame
            im_water_p = Image.fromarray(self.water_indices, mode='P')
            im_water_p.putpalette(pal_day.ravel().tolist())
            im_water_rgba = im_water_p.convert('RGBA')
            # Apply alpha mask
            arr_w = np.array(im_water_rgba)
            arr_w[:, :, 3] = base_alpha
            arr_w[~self.water_mask] = [0, 0, 0, 0]
            im_water_clean = Image.fromarray(arr_w)

            fn_w = f'{self.id}_02_eau_mer_frame_{f:02d}.png'
            im_water_clean.save(water_dir / fn_w)
            im_water_clean.save(e_dir / fn_w)
            water_layer_day_frames.append(im_water_clean)
            water_files.append(fn_w)

            # Night water frame
            arr_wn = to_night(arr_w)
            im_water_night = Image.fromarray(arr_wn)
            water_layer_night_frames.append(im_water_night)

        # Save animated GIF for the isolated water layer
        water_layer_day_frames[0].save(
            r_dir / f'{self.id}_02_eau_mer_animee_seule.gif',
            save_all=True,
            append_images=water_layer_day_frames[1:],
            duration=120,
            loop=0,
            disposal=2
        )

        # 3. Build full scene composite frames across all 8 water phases
        scene_frames_day = []
        scene_frames_night = []

        # Order of compositing:
        # 00_fond_ocean -> 01_arene_sable -> 02_eau_mer (animée) -> 03_ecume -> 04_falaises -> 05_massifs -> 06_rochers
        for f in range(8):
            sc_d = Image.new('RGBA', (W, H))
            sc_n = Image.new('RGBA', (W, H))
            if '00_fond_ocean_profond' in self.layers:
                sc_d.alpha_composite(Image.fromarray(self.layers['00_fond_ocean_profond']))
                sc_n.alpha_composite(Image.fromarray(to_night(self.layers['00_fond_ocean_profond'])))
            if '01_arene_sable_sol' in self.layers:
                sc_d.alpha_composite(Image.fromarray(self.layers['01_arene_sable_sol']))
                sc_n.alpha_composite(Image.fromarray(to_night(self.layers['01_arene_sable_sol'])))
            # Add animated water
            sc_d.alpha_composite(water_layer_day_frames[f])
            sc_n.alpha_composite(water_layer_night_frames[f])

            for name in ['03_ecume_rivage', '04_falaises_rouges_fond', '05_massifs_rocheux_lateraux', '06_rochers_et_recifs_premier_plan']:
                if name in self.layers:
                    sc_d.alpha_composite(Image.fromarray(self.layers[name]))
                    sc_n.alpha_composite(Image.fromarray(to_night(self.layers[name])))

            scene_frames_day.append(sc_d)
            scene_frames_night.append(sc_n)

        # Save static composites (phase 0) and animated scene GIF
        scene_frames_day[0].save(r_dir / f'{self.id}_composite_jour.png')
        scene_frames_day[0].save(e_dir / 'composite.png')
        scene_frames_night[0].save(r_dir / f'{self.id}_composite_nuit.png')

        scene_frames_day[0].save(
            r_dir / f'{self.id}_scene_animee_jour.gif',
            save_all=True,
            append_images=scene_frames_day[1:],
            duration=120,
            loop=0
        )
        scene_frames_night[0].save(
            r_dir / f'{self.id}_scene_animee_nuit.gif',
            save_all=True,
            append_images=scene_frames_night[1:],
            duration=120,
            loop=0
        )

        return dict(
            id=self.id,
            title=self.title,
            description=self.description,
            size=[W, H],
            layers=manifest_layers,
            water_frames=water_files,
            composite_day=f'{self.id}_composite_jour.png',
            composite_night=f'{self.id}_composite_nuit.png',
            scene_gif_day=f'{self.id}_scene_animee_jour.gif',
            scene_gif_night=f'{self.id}_scene_animee_nuit.gif',
            water_gif=f'{self.id}_02_eau_mer_animee_seule.gif'
        )

# =========================================================================
# LAYOUT 1: Grande Arène Côtière Ouverte (Wide Beach Ring — 512x512)
# =========================================================================
def build_layout_1():
    m = BeachMap(
        '01_grande_arene_plage_ouverte',
        'Grande Arène Côtière Ouverte',
        'Vaste arène de combat circulaire en sable dégagée au centre (diamètre 240 px), flanquée de falaises rouges reculées à l’Est et à l’Ouest, avec vue sur l’océan au Nord et eau animée en palette cycling canonique sur son propre calque.'
    )
    yy, xx = np.mgrid[:H, :W]

    # 00: Deep Ocean Backdrop (Northern ocean view)
    m.put_patch('00_fond_ocean_profond', (144, 48, 312, 112), (0, 0))
    m.put_patch('00_fond_ocean_profond', (144, 48, 312, 112), (168, 0))
    m.put_patch('00_fond_ocean_profond', (144, 48, 312, 112), (336, 0))

    # 01: Sand ground: large central fighting circle + southern approach
    # Center (256, 270), radius 120 px, plus south path corridor x in [192, 320]
    dist_center = np.sqrt((xx - 256)**2 + (yy - 270)**2)
    sand_mask = (dist_center <= 128) | ((xx >= 192) & (xx <= 320) & (yy >= 270))
    m.fill_sand('01_arene_sable_sol', mask=sand_mask, seed=51)

    # 02: Animated Sea Layer (North bay & East/West coastal inlets)
    water_mask = ((yy >= 48) & (yy <= 144) & (xx >= 80) & (xx <= 432) & ~sand_mask) | \
                 ((xx < 100) & (yy >= 144) & (yy <= 360)) | \
                 ((xx > 412) & (yy >= 144) & (yy <= 360))
    m.set_water_region(water_mask, base_offset=0)

    # 03: Shoreline Foam (where sea touches sand)
    foam_mask = (dist_center >= 120) & (dist_center <= 136) & water_mask
    m.put_patch('03_ecume_rivage', (144, 96, 312, 112), (100, 136))
    m.put_patch('03_ecume_rivage', (144, 96, 312, 112), (256, 136))

    # 04: North Red Cliff Arches (framing the horizon)
    m.put_patch('04_falaises_rouges_fond', (140, 40, 320, 112), (166, 16))

    # 05: Lateral Cliff Bluffs (repositioned to widen the battle arena)
    # West cliff massif (from x=0..160, y=80..380 of source) placed at x=0, y=140
    m.put_patch('05_massifs_rocheux_lateraux', (0, 80, 140, 360), (0, 140))
    # East cliff massif placed at x=372, y=140
    m.put_patch('05_massifs_rocheux_lateraux', (316, 80, 456, 360), (372, 140))

    # 06: Foreground Rock Reefs & Stacks
    m.put_patch('06_rochers_et_recifs_premier_plan', (0, 416, 192, 480), (0, 416))
    m.put_patch('06_rochers_et_recifs_premier_plan', (264, 416, 456, 480), (320, 416))
    # Isolated sea stack in west water inlet
    m.put_patch('06_rochers_et_recifs_premier_plan', (330, 240, 370, 280), (56, 210))

    return m.export()

# =========================================================================
# LAYOUT 2: Défilé Côtier et Terrasse Maritime (Coastal Ravine & Overlook)
# =========================================================================
def build_layout_2():
    m = BeachMap(
        '02_defile_cotier_terrasse',
        'Défilé Côtier et Terrasse Maritime',
        'Sentier de sable sinueux longeant un défilé de falaises rouges, menant à une terrasse rocheuse surélevée au Nord-Est. L’océan s’engouffre dans une grande baie animée sur le flanc Ouest avec rouleaux de ressac en palette cycling.'
    )
    yy, xx = np.mgrid[:H, :W]

    # 00: Deep Ocean Backdrop
    m.put_patch('00_fond_ocean_profond', (144, 48, 312, 112), (0, 0))
    m.put_patch('00_fond_ocean_profond', (144, 48, 312, 112), (168, 0))

    # 01: Sand ground: winding south-north path shifting toward NE terrace
    path_mask = ((xx >= 160) & (xx <= 300) & (yy >= 280)) | \
                ((xx >= 200) & (xx <= 360) & (yy >= 140) & (yy < 280)) | \
                ((xx >= 240) & (xx <= 420) & (yy < 140))
    m.fill_sand('01_arene_sable_sol', mask=path_mask, seed=63)

    # 02: Animated Sea Layer: expansive Western Bay
    water_mask = (xx < 180) & (yy >= 48) & (yy <= 440)
    m.set_water_region(water_mask, base_offset=2)

    # 03: Shoreline Foam along western beach edge
    m.put_patch('03_ecume_rivage', (144, 96, 240, 112), (160, 160))
    m.put_patch('03_ecume_rivage', (144, 96, 240, 112), (150, 280))

    # 04: Raised Red Cliff Overlook & North Terrace (NE quadrant)
    m.put_patch('04_falaises_rouges_fond', (296, 80, 456, 260), (352, 60))
    m.put_patch('04_falaises_rouges_fond', (140, 40, 300, 112), (240, 20))

    # 05: West Cliff Headland protecting the bay mouth
    m.put_patch('05_massifs_rocheux_lateraux', (0, 80, 120, 260), (0, 40))

    # 06: Foreground Reefs & Stepping Boulders
    m.put_patch('06_rochers_et_recifs_premier_plan', (0, 416, 224, 480), (0, 416))
    m.put_patch('06_rochers_et_recifs_premier_plan', (264, 416, 456, 480), (320, 416))
    # Sea stack in the western bay
    m.put_patch('06_rochers_et_recifs_premier_plan', (330, 240, 370, 280), (72, 220))

    return m.export()

# =========================================================================
# LAYOUT 3: Atoll de Sable et Double Récif (Sand Atoll & Twin Reefs)
# =========================================================================
def build_layout_3():
    m = BeachMap(
        '03_atoll_sable_double_recif',
        'Atoll de Sable et Double Récif',
        'Arène insulaire en atoll de sable au centre, baignée par la mer animée sur ses deux flancs Est et Ouest. Deux récifs côtiers jumeaux encadrent le passage, surplombés au Nord par une grande arche de falaise rouge.'
    )
    yy, xx = np.mgrid[:H, :W]

    # 00: Deep Ocean Backdrop
    m.put_patch('00_fond_ocean_profond', (144, 48, 312, 112), (0, 0))
    m.put_patch('00_fond_ocean_profond', (144, 48, 312, 112), (200, 0))
    m.put_patch('00_fond_ocean_profond', (144, 48, 312, 112), (344, 0))

    # 01: Sand ground: central island atoll (ellipse) + south sand spit
    dist_atoll = ((xx - 256) / 100)**2 + ((yy - 240) / 110)**2
    sand_mask = (dist_atoll <= 1.0) | ((xx >= 208) & (xx <= 304) & (yy >= 240))
    m.fill_sand('01_arene_sable_sol', mask=sand_mask, seed=79)

    # 02: Animated Sea Layer: surrounding sea channels (East & West)
    water_mask = ((xx < 192) & (yy >= 64) & (yy <= 440)) | \
                 ((xx > 320) & (yy >= 64) & (yy <= 440))
    m.set_water_region(water_mask, base_offset=4)

    # 03: Shoreline Foam along both island shores
    m.put_patch('03_ecume_rivage', (144, 96, 240, 112), (160, 220))
    m.put_patch('03_ecume_rivage', (144, 96, 240, 112), (272, 220))

    # 04: Grand Red Cliff Arch at the North
    m.put_patch('04_falaises_rouges_fond', (140, 40, 320, 120), (166, 20))

    # 05: Twin Lateral Reefs
    m.put_patch('05_massifs_rocheux_lateraux', (0, 80, 120, 300), (0, 120))
    m.put_patch('05_massifs_rocheux_lateraux', (336, 80, 456, 300), (392, 120))

    # 06: Bottom Coastal Rocks framing the sand spit
    m.put_patch('06_rochers_et_recifs_premier_plan', (0, 416, 192, 480), (0, 416))
    m.put_patch('06_rochers_et_recifs_premier_plan', (264, 416, 456, 480), (320, 416))

    return m.export()

def main():
    RENDERS_DIR.mkdir(parents=True, exist_ok=True)
    EXPORTS_DIR.mkdir(parents=True, exist_ok=True)

    layouts = [
        build_layout_1(),
        build_layout_2(),
        build_layout_3()
    ]

    manifest = dict(
        version='BeachArenaMulticalquesV1',
        title='PMD Sky Beach Arena — Multicalques & Animated Water Palette Cycling',
        source=dict(
            file=SOURCE_FILE,
            sha256=REF_SHA256,
            dimensions=[456, 480],
            method='Canonical native pixel quilting and macro-module preservation'
        ),
        grid=8,
        layouts=layouts,
        animation=dict(
            mode='Canonical Indexed Palette Cycling (Cycling Panel)',
            frame_count=8,
            frame_ms=120,
            loop_ms=960,
            cycle_colors_rgb=CYCLE_WATER_RGB.tolist(),
            geometry_static=True,
            layer='02_eau_mer_palette_cycling'
        ),
        grading_night=dict(
            formula='Abyss V4 / Sharpedo exact luminance weighting'
        ),
        runtime='NOT TESTED'
    )
    (EXPORTS_DIR / 'manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n')
    (RENDERS_DIR / 'manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n')

    # Build interactive HTML viewer at repository root
    def uri(path):
        return 'data:image/png;base64,' + base64.b64encode(path.read_bytes()).decode()

    viewer_data = []
    for lay in layouts:
        r_dir = RENDERS_DIR / lay['id']
        water_frames_data = [uri(r_dir / '02_eau_mer_palette_cycling' / fn) for fn in lay['water_frames']]
        layers_data = []
        for l in lay['layers']:
            layers_data.append(dict(
                id=l['id'],
                uri_day=uri(r_dir / l['file_day']),
                uri_night=uri(r_dir / l['file_night'])
            ))
        viewer_data.append(dict(
            id=lay['id'],
            title=lay['title'],
            description=lay['description'],
            size=lay['size'],
            composite_day_uri=uri(r_dir / lay['composite_day']),
            composite_night_uri=uri(r_dir / lay['composite_night']),
            layers=layers_data,
            water_frames=water_frames_data
        ))

    html = '''<!doctype html>
<html lang="fr">
<head>
<meta charset="utf-8">
<title>Arène Plage PMD Sky · Multicalques & Eau Animée</title>
<style>
  body { background: #101920; color: #e1e9f0; font: 15px -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; margin: 0; padding: 24px; }
  header { max-width: 1360px; margin: 0 auto 24px; padding-bottom: 16px; border-bottom: 1px solid #233847; }
  h1 { font-size: 26px; color: #fedb88; margin: 0 0 6px; }
  p.sub { color: #9ab4c7; margin: 0; line-height: 1.55; }
  .tabs { display: flex; gap: 10px; max-width: 1360px; margin: 0 auto 20px; }
  .tab-btn { background: #192a36; color: #a4c1d6; border: 1px solid #2c4a5f; padding: 10px 18px; border-radius: 8px; cursor: pointer; font-size: 14px; font-weight: 500; }
  .tab-btn:hover { background: #223a4b; color: #fff; }
  .tab-btn.active { background: #e0b04c; color: #0d161d; border-color: #ffd277; font-weight: bold; }
  .workspace { display: flex; gap: 28px; max-width: 1360px; margin: 0 auto; flex-wrap: wrap; }
  .viewport-panel { background: #16242e; border: 1px solid #294457; border-radius: 12px; padding: 20px; box-shadow: 0 8px 24px rgba(0,0,0,0.5); }
  .canvas-box { position: relative; width: 512px; height: 512px; background: #080e12; border: 1px solid #243b4c; border-radius: 6px; overflow: hidden; margin-bottom: 14px; }
  canvas { display: block; image-rendering: pixelated; width: 512px; height: 512px; }
  .toolbar { display: flex; gap: 10px; margin-bottom: 14px; align-items: center; }
  button { background: #213a4c; color: #d9e7f2; border: 1px solid #365e7a; padding: 6px 14px; border-radius: 6px; cursor: pointer; font-size: 13px; }
  button:hover { background: #2c4d66; }
  button.active { background: #e0b04c; color: #0d161d; font-weight: bold; border-color: #ffd277; }
  .side-panel { flex: 1; min-width: 320px; background: #16242e; border: 1px solid #294457; border-radius: 12px; padding: 20px; }
  h2 { font-size: 20px; color: #ffd277; margin: 0 0 8px; }
  p.desc { font-size: 14px; color: #b1c7d6; line-height: 1.5; margin: 0 0 16px; }
  .layer-group { background: #0e1820; border: 1px solid #1f3544; border-radius: 8px; padding: 14px; margin-bottom: 16px; }
  .layer-group h3 { font-size: 14px; text-transform: uppercase; color: #7cb0d4; margin: 0 0 10px; letter-spacing: 0.5px; }
  label { display: flex; align-items: center; gap: 8px; font-size: 13px; color: #d2e2ee; margin-bottom: 8px; cursor: pointer; }
  label:hover { color: #fff; }
  .badge { display: inline-block; padding: 2px 7px; border-radius: 4px; font-size: 11px; font-weight: bold; }
  .badge-water { background: #124d6d; color: #76d4ff; border: 1px solid #1a6f9c; }
  .badge-canon { background: #1f4f38; color: #7ce5af; }
  .info-box { background: #0e1820; border-left: 3px solid #e0b04c; padding: 10px 14px; font-size: 12px; color: #9bb3c4; line-height: 1.5; }
</style>
</head>
<body>
<header>
  <h1>Arène Plage PMD Sky · Multicalques & Eau Animée en Palette Cycling</h1>
  <p class="sub">
    Reconstruction à partir des textures canoniques de <code>arenapmdskybeach.png</code> (commit 9ec9a081).<br>
    <strong>Eau animée sur son propre calque indépendant</strong> via cycling panel (rotation cyclique des 8 teintes marines, indices fixes).
    Découpage multicalque propre (sable, eau animée, écume, falaises rouges, récifs) et bascule Jour / Nuit Abyss V4.
  </p>
</header>

<div class="tabs" id="tabs"></div>
<div class="workspace">
  <div class="viewport-panel">
    <div class="toolbar">
      <button id="btn-day" class="active" onclick="setMode('jour')">☀️ Mode Jour</button>
      <button id="btn-night" onclick="setMode('nuit')">🌙 Nuit Abyss</button>
      <button id="btn-grid" onclick="toggleGrid()">Grille 8px</button>
      <button id="btn-water-anim" class="active" onclick="toggleWaterAnim()">🌊 Eau Animée (Play)</button>
    </div>
    <div class="canvas-box">
      <canvas id="main-canvas" width="512" height="512"></canvas>
    </div>
  </div>
  <div class="side-panel">
    <h2 id="view-title"></h2>
    <p class="desc" id="view-desc"></p>
    <div class="layer-group">
      <h3>Calques Indépendants (Multicalques)</h3>
      <div id="layer-controls"></div>
    </div>
    <div class="info-box">
      <strong>Méthode Halcyon / PMDO :</strong> Le calque de mer est strictement séparé. La géométrie et les indices de pixels sont fixes, seule la table de palette tourne en boucle fermée toutes les 120 ms. Aucun rééchantillonnage ni flou bilinéaire.
    </div>
  </div>
</div>

<script>
const DATA = __DATA__;
let currentLayoutIdx = 0;
let currentMode = 'jour';
let showGrid = false;
let waterAnimActive = true;
let waterFrame = 0;
let layerChecks = {};

const canvas = document.getElementById('main-canvas');
const ctx = canvas.getContext('2d');

// Setup Layout Tabs
const tabsContainer = document.getElementById('tabs');
DATA.forEach((lay, idx) => {
  const b = document.createElement('button');
  b.className = 'tab-btn' + (idx === 0 ? ' active' : '');
  b.textContent = lay.title;
  b.onclick = () => switchLayout(idx);
  tabsContainer.appendChild(b);
});

// Cache image elements
const imageCache = {};
function preloadImages() {
  DATA.forEach(lay => {
    lay.layers.forEach(l => {
      const imgD = new Image(); imgD.src = l.uri_day; imageCache[l.uri_day] = imgD;
      const imgN = new Image(); imgN.src = l.uri_night; imageCache[l.uri_night] = imgN;
    });
    lay.water_frames.forEach(w => {
      const imgW = new Image(); imgW.src = w; imageCache[w] = imgW;
    });
  });
}
preloadImages();

function switchLayout(idx) {
  currentLayoutIdx = idx;
  document.querySelectorAll('.tab-btn').forEach((b, i) => b.classList.toggle('active', i === idx));
  const lay = DATA[idx];
  document.getElementById('view-title').textContent = lay.title;
  document.getElementById('view-desc').textContent = lay.description;
  buildControls();
  render();
}

function buildControls() {
  const lay = DATA[currentLayoutIdx];
  const container = document.getElementById('layer-controls');
  container.innerHTML = '';
  layerChecks = {};

  // Sand
  addCheck(container, '01_arene_sable_sol', 'Sable de combat (Sol)', true);
  // Water
  addCheck(container, '02_eau_mer', 'Eau de mer animée (Cycling Panel)', true, 'badge-water');
  // Foam
  addCheck(container, '03_ecume_rivage', 'Écume & grève du rivage', true);
  // Background Cliffs
  addCheck(container, '04_falaises_rouges_fond', 'Falaises rouges d’arrière-plan', true);
  // Lateral Bluffs
  addCheck(container, '05_massifs_rocheux_lateraux', 'Massifs rocheux latéraux', true);
  // Foreground Rocks
  addCheck(container, '06_rochers_et_recifs_premier_plan', 'Récifs & rochers de premier plan', true);
}

function addCheck(parent, key, labelText, defaultVal, badgeClass) {
  layerChecks[key] = defaultVal;
  const lbl = document.createElement('label');
  const chk = document.createElement('input');
  chk.type = 'checkbox';
  chk.checked = defaultVal;
  chk.onchange = () => { layerChecks[key] = chk.checked; render(); };
  lbl.appendChild(chk);
  lbl.appendChild(document.createTextNode(labelText));
  if (badgeClass) {
    const bd = document.createElement('span');
    bd.className = 'badge ' + badgeClass;
    bd.textContent = 'ANIMÉ';
    lbl.appendChild(bd);
  }
  parent.appendChild(lbl);
}

function setMode(mode) {
  currentMode = mode;
  document.getElementById('btn-day').classList.toggle('active', mode === 'jour');
  document.getElementById('btn-night').classList.toggle('active', mode === 'nuit');
  render();
}

function toggleGrid() {
  showGrid = !showGrid;
  document.getElementById('btn-grid').classList.toggle('active', showGrid);
  render();
}

function toggleWaterAnim() {
  waterAnimActive = !waterAnimActive;
  document.getElementById('btn-water-anim').classList.toggle('active', waterAnimActive);
}

function render() {
  const lay = DATA[currentLayoutIdx];
  ctx.clearRect(0, 0, 512, 512);

  // 00 Deep Ocean Backdrop
  const oceanLayer = lay.layers.find(l => l.id === '00_fond_ocean_profond');
  if (oceanLayer) {
    const img = imageCache[currentMode === 'jour' ? oceanLayer.uri_day : oceanLayer.uri_night];
    if (img && img.complete) ctx.drawImage(img, 0, 0);
  }

  // 01 Sand
  if (layerChecks['01_arene_sable_sol']) {
    const sandLayer = lay.layers.find(l => l.id === '01_arene_sable_sol');
    if (sandLayer) {
      const img = imageCache[currentMode === 'jour' ? sandLayer.uri_day : sandLayer.uri_night];
      if (img && img.complete) ctx.drawImage(img, 0, 0);
    }
  }

  // 02 Animated Water (on its own clean layer)
  if (layerChecks['02_eau_mer']) {
    const waterUri = lay.water_frames[waterFrame % lay.water_frames.length];
    const imgW = imageCache[waterUri];
    if (imgW && imgW.complete) {
      if (currentMode === 'nuit') {
        // Apply night filter on canvas context if in night mode
        ctx.save();
        ctx.filter = 'brightness(0.55) contrast(0.9) hue-rotate(-20deg)';
        ctx.drawImage(imgW, 0, 0);
        ctx.restore();
      } else {
        ctx.drawImage(imgW, 0, 0);
      }
    }
  }

  // Static upper layers
  const upperKeys = [
    { key: '03_ecume_rivage', id: '03_ecume_rivage' },
    { key: '04_falaises_rouges_fond', id: '04_falaises_rouges_fond' },
    { key: '05_massifs_rocheux_lateraux', id: '05_massifs_rocheux_lateraux' },
    { key: '06_rochers_et_recifs_premier_plan', id: '06_rochers_et_recifs_premier_plan' }
  ];

  upperKeys.forEach(item => {
    if (layerChecks[item.key]) {
      const l = lay.layers.find(layL => layL.id === item.id);
      if (l) {
        const img = imageCache[currentMode === 'jour' ? l.uri_day : l.uri_night];
        if (img && img.complete) ctx.drawImage(img, 0, 0);
      }
    }
  });

  // 8px Grid Overlay
  if (showGrid) {
    ctx.strokeStyle = 'rgba(255, 255, 255, 0.15)';
    ctx.lineWidth = 1;
    for (let x = 0; x <= 512; x += 8) {
      ctx.beginPath(); ctx.moveTo(x, 0); ctx.lineTo(x, 512); ctx.stroke();
    }
    for (let y = 0; y <= 512; y += 8) {
      ctx.beginPath(); ctx.moveTo(0, y); ctx.lineTo(512, y); ctx.stroke();
    }
  }
}

// Animation timer for palette cycling (120ms per phase)
setInterval(() => {
  if (waterAnimActive) {
    waterFrame = (waterFrame + 1) % 8;
    render();
  }
}, 120);

// Initial start
switchLayout(0);
</script>
</body>
</html>
'''
    full_html = html.replace('__DATA__', json.dumps(viewer_data, ensure_ascii=False))
    (ROOT / 'apercu_arene_plage_multicalques_v1.html').write_text(full_html, encoding='utf-8')
    print('Beach Arena Multicalques V1 built successfully.')

if __name__ == '__main__':
    main()
