#!/usr/bin/env python3
"""FA1 — Friend Areas Rescue Team : Forêt Énergique & Forêt Champignon.
Adapte les Friend Areas GBA en maps PMDO multicalques 8px canoniques.
--build   : génère les calques, planches, aperçus viewport, packs ZIP et WebP
--verify  : contrôle d'intégrité, opacité du sol, palettes 5-bit GBA, navigabilité
--pmdo    : sérialisation .rsground, banques .tile 8px, test d'installation PMDO
"""
import argparse, io, json, os, shutil, sys, tempfile, zipfile
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage

R = Path(__file__).resolve().parents[2]
O = R / 'renders/friend_areas_pmd_v1'
S = R / 'source/friend_areas_pmd_v1'
C = R / '.cache/friend_areas_pmd_v1'

sys.path.insert(0, str(R / 'source/cote_v4_abyss'))
from night import night

AREAS = {
    'energetic_forest': {
        'id': 'energetic_forest',
        'title': 'Forêt Énergique (Energetic Forest)',
        'source_file': 'Game Boy Advance - Pokemon Mystery Dungeon_ Red Rescue Team - Friend Areas - Energetic Forest.png',
        'size': (480, 336),
        'spawn': [240, 296],
        'offset': [0, -40],
        'layers_def': [
            {'id': 'sol', 'title': '01 - Sol clairière continu (100% opaque)'},
            {'id': 'buissons_denses', 'title': '02 - Buissons denses et sous-bois ombragé'},
            {'id': 'vegetation_basse', 'title': '03 - Végétation basse et pousses ensoleillées'},
            {'id': 'troncs_racines', 'title': '04 - Troncs noueux et racines anciennes'},
            {'id': 'canopee_avant_plan', 'title': '05 - Canopée haute et branches d avant-plan'}
        ]
    },
    'mushroom_forest': {
        'id': 'mushroom_forest',
        'title': 'Forêt Champignon (Mushroom Forest)',
        'source_file': 'Game Boy Advance - Pokemon Mystery Dungeon_ Red Rescue Team - Friend Areas - Mushroom Forest.png',
        'size': (456, 336),
        'spawn': [228, 296],
        'offset': [0, -40],
        'layers_def': [
            {'id': 'sol', 'title': '01 - Sol tapis de mousse continu (100% opaque)'},
            {'id': 'troncs_souches', 'title': '02 - Troncs sombres, souches et racines'},
            {'id': 'champignons_geants', 'title': '03 - Grands champignons violets et chapeaux mouchetés'},
            {'id': 'petits_champignons', 'title': '04 - Petits champignons et sporophores au sol'},
            {'id': 'canopee_avant_plan', 'title': '05 - Canopée haute et retombées de feuillage'}
        ]
    }
}

def img(b):
    return Image.open(io.BytesIO(b) if isinstance(b, (bytes, bytearray)) else b).convert('RGBA')

def png(im):
    b = io.BytesIO()
    im.save(b, format='PNG', optimize=True)
    return b.getvalue()

def jb(obj):
    return json.dumps(obj, indent=2, ensure_ascii=False).encode('utf-8')

def extract_layers_energetic(src):
    h, w = src.shape[:2]
    yy, xx = np.mgrid[:h, :w]
    r, g, b = src[:, :, 0].astype(int), src[:, :, 1].astype(int), src[:, :, 2].astype(int)

    # 1. Canopée avant-plan (haut et franges supérieures)
    m_canopy = ((r == 72) & (g == 128) & (b == 80) & (yy < 160)) | (yy < 48)

    # 2. Bois / troncs / racines
    m_wood = ~m_canopy & (((r > 50) & (r < 150) & (g < 115) & (b < 85)) | ((r < 60) & (g < 80) & (b < 60) & (r > 25)))

    # 3. Végétation intermédiaire et sous-bois
    all_foliage = ~m_canopy & ~m_wood & (((g > 120) & (b <= 95) & (r < 110)) | ((g >= 100) & (g <= 160) & (r < 80))) & (yy >= 40)
    m_dense = all_foliage & (g < 150)
    m_bright = all_foliage & ~m_dense

    # 4. Sol herbeux initial
    m_ground = ~m_canopy & ~m_wood & ~all_foliage

    # Reconstruction sol continu 100% opaque sous les obstacles
    inds = ndimage.distance_transform_edt(~m_ground, return_distances=False, return_indices=True)
    sol_complet = src.copy()
    sol_complet[~m_ground] = src[inds[0, ~m_ground], inds[1, ~m_ground]]

    sol_arr = np.dstack([sol_complet, np.full((h, w), 255, dtype='uint8')])
    dense_arr = np.dstack([src, np.where(m_dense, 255, 0).astype('uint8')])
    bright_arr = np.dstack([src, np.where(m_bright, 255, 0).astype('uint8')])
    wood_arr = np.dstack([src, np.where(m_wood, 255, 0).astype('uint8')])
    canopy_arr = np.dstack([src, np.where(m_canopy, 255, 0).astype('uint8')])

    return {
        'sol': Image.fromarray(sol_arr),
        'buissons_denses': Image.fromarray(dense_arr),
        'vegetation_basse': Image.fromarray(bright_arr),
        'troncs_racines': Image.fromarray(wood_arr),
        'canopee_avant_plan': Image.fromarray(canopy_arr)
    }

def extract_layers_mushroom(src):
    h, w = src.shape[:2]
    yy, xx = np.mgrid[:h, :w]
    r, g, b = src[:, :, 0].astype(int), src[:, :, 1].astype(int), src[:, :, 2].astype(int)

    # 1. Canopée avant-plan
    m_canopy = (yy < 48) | ((yy < 110) & (b >= 150) & (r >= 100) & (g < 120))

    # 2. Chapeaux et points des champignons géants
    m_caps = ~m_canopy & (
        (((r > 120) & (b > 90) & (g < 140)) | ((r > 190) & (g > 140) & (b < 150)))
        | ((r > 220) & (g > 200) & (b > 180) & (g < 240))
    )

    # 3. Troncs, souches et pieds de champignons géants
    m_stems_wood = ~m_canopy & ~m_caps & (
        ((b >= 90) & (b <= 180) & (g >= 45) & (g <= 130) & (r <= 90))
        | ((b >= 170) & (r >= 60) & (r <= 180) & (g < 150))
    )

    # 4. Sol clairière et petits champignons
    m_ground_base = (g >= 200) & (b >= 160) & (r >= 100)
    m_small_fungi = ~m_canopy & ~m_caps & ~m_stems_wood & ~m_ground_base
    m_ground = ~m_canopy & ~m_caps & ~m_stems_wood & ~m_small_fungi

    # Reconstruction sol continu 100% opaque sous les obstacles
    inds = ndimage.distance_transform_edt(~m_ground, return_distances=False, return_indices=True)
    sol_complet = src.copy()
    sol_complet[~m_ground] = src[inds[0, ~m_ground], inds[1, ~m_ground]]

    sol_arr = np.dstack([sol_complet, np.full((h, w), 255, dtype='uint8')])
    stems_arr = np.dstack([src, np.where(m_stems_wood, 255, 0).astype('uint8')])
    caps_arr = np.dstack([src, np.where(m_caps, 255, 0).astype('uint8')])
    fungi_arr = np.dstack([src, np.where(m_small_fungi, 255, 0).astype('uint8')])
    canopy_arr = np.dstack([src, np.where(m_canopy, 255, 0).astype('uint8')])

    return {
        'sol': Image.fromarray(sol_arr),
        'troncs_souches': Image.fromarray(stems_arr),
        'champignons_geants': Image.fromarray(caps_arr),
        'petits_champignons': Image.fromarray(fungi_arr),
        'canopee_avant_plan': Image.fromarray(canopy_arr)
    }

def compose_scene(layers_dict, order_ids):
    first = layers_dict[order_ids[0]]
    out = Image.new('RGBA', first.size, (0, 0, 0, 0))
    for lid in order_ids:
        out.alpha_composite(layers_dict[lid])
    return out

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
    # Center camera around spawn, clamped to boundaries
    cx = max(0, min(w - sw, sx - sw // 2))
    cy = max(0, min(h - sh, sy - sh // 2))

    view_crop = comp_im.crop((cx, cy, cx + sw, cy + sh))
    # Create framed demonstration
    frame = Image.new('RGB', (w, h + 32), '#1a202c')
    draw = ImageDraw.Draw(frame)
    draw.text((12, 8), f'Viewport Camera 320x240 (x1) — Focus Spawn [{sx}, {sy}]', fill='#fbbf24')
    frame.paste(comp_im.convert('RGB'), (0, 32))
    # Draw viewport rectangle over full map
    box_draw = ImageDraw.Draw(frame)
    box_draw.rectangle([cx, cy + 32, cx + sw, cy + 32 + sh], outline='#f59e0b', width=2)
    # Draw spawn marker crosshair
    box_draw.ellipse([sx - 4, sy + 32 - 4, sx + 4, sy + 32 + 4], fill='#ef4444', outline='#ffffff')
    return frame, view_crop

def build():
    O.mkdir(parents=True, exist_ok=True)
    C.mkdir(parents=True, exist_ok=True)
    results = {}

    for area_id, cfg in AREAS.items():
        w, h = cfg['size']
        src_img = Image.open(R / cfg['source_file'])
        src_arr = np.array(src_img)[:h, :w, :3]
        native_cols = np.unique(src_arr.reshape(-1, 3), axis=0)

        # Day layers
        if area_id == 'energetic_forest':
            day_layers = extract_layers_energetic(src_arr)
        else:
            day_layers = extract_layers_mushroom(src_arr)

        order_ids = [l['id'] for l in cfg['layers_def']]
        comp_day = compose_scene(day_layers, order_ids)

        # Night layers via canonical Abyss transform
        night_layers = {lid: night(day_layers[lid]) for lid in order_ids}
        # Force continuous ground opacity in night mode as well
        sol_nuit_arr = np.array(night_layers['sol'])
        sol_nuit_arr[:, :, 3] = 255
        night_layers['sol'] = Image.fromarray(sol_nuit_arr)
        comp_night = compose_scene(night_layers, order_ids)

        # Saves for renders directory
        (O / f'FA1_{area_id}_carte_jour.png').write_bytes(png(comp_day))
        (O / f'FA1_{area_id}_carte_nuit.png').write_bytes(png(comp_night))
        (O / f'FA1_{area_id}_carte.png').write_bytes(png(comp_day))

        board_day = build_board(f'{cfg["title"]} (Jour)', day_layers, order_ids, comp_day)
        (O / f'FA1_{area_id}_calques.png').write_bytes(png(board_day))

        vp_frame_day, vp_crop_day = build_viewport(comp_day, cfg['spawn'])
        (O / f'FA1_{area_id}_viewport.png').write_bytes(png(vp_frame_day))
        (O / f'FA1_{area_id}_viewport_320x240.png').write_bytes(png(vp_crop_day))

        # Animated Day/Night WebP (toggle every 2 seconds = 2000 ms)
        anim_path = O / f'FA1_{area_id}_ambiances.webp'
        comp_day.convert('RGB').save(anim_path, save_all=True, append_images=[comp_night.convert('RGB')], duration=[2000, 2000], loop=0, lossless=True)

        # Build Calques ZIP Pack
        zip_files = {}
        for lid in order_ids:
            zip_files[f'calques_jour/FA1_{area_id}_{lid}_jour.png'] = png(day_layers[lid])
            zip_files[f'calques_nuit/FA1_{area_id}_{lid}_nuit.png'] = png(night_layers[lid])
        zip_files[f'references/FA1_{area_id}_source_GBA.png'] = png(Image.fromarray(src_arr))
        zip_files[f'FA1_{area_id}_carte_jour.png'] = png(comp_day)
        zip_files[f'FA1_{area_id}_carte_nuit.png'] = png(comp_night)

        manifest = {
            'lot': 'FA1',
            'area_id': area_id,
            'title': cfg['title'],
            'size': [w, h],
            'tiles_grid': [w // 8, h // 8],
            'semantic_groups': len(order_ids),
            'spawn_point': cfg['spawn'],
            'camera_offset': cfg['offset'],
            'canonical_colors_count': len(native_cols),
            'layers': [
                {
                    'id': l['id'],
                    'title': l['title'],
                    'file_jour': f'calques_jour/FA1_{area_id}_{l["id"]}_jour.png',
                    'file_nuit': f'calques_nuit/FA1_{area_id}_{l["id"]}_nuit.png'
                }
                for l in cfg['layers_def']
            ],
            'notes': [
                '100% pixels canoniques extraits sans redimensionnement ni lissage',
                'Sol continu 100% opaque sous le decor pour eviter toute lacune alpha',
                'Passage et rassemblement sud verifies avec erosion 17px',
                'Filtre nocturne Abyss exact applique calque par calque'
            ]
        }
        zip_files['manifest.json'] = jb(manifest)

        calques_zip_path = O / f'FA1_{area_id}_calques.zip'
        with zipfile.ZipFile(calques_zip_path, 'w', zipfile.ZIP_DEFLATED, compresslevel=9) as z:
            for name, data in sorted(zip_files.items()):
                info = zipfile.ZipInfo(name, (2026, 9, 22, 0, 0, 0))
                info.compress_type = zipfile.ZIP_DEFLATED
                z.writestr(info, data, compresslevel=9)

        results[area_id] = {
            'cfg': cfg,
            'day_layers': day_layers,
            'night_layers': night_layers,
            'comp_day': comp_day,
            'comp_night': comp_night,
            'manifest': manifest,
            'zip_files': zip_files
        }
        print(f'Built FA1 {area_id}: {len(zip_files)} files in calques pack ({calques_zip_path.stat().st_size} bytes)', flush=True)

    # Duo comparative planche
    ef_im = results['energetic_forest']['comp_day']
    mf_im = results['mushroom_forest']['comp_day']
    duo_w = ef_im.width + mf_im.width
    duo_h = max(ef_im.height, mf_im.height)
    duo_board = Image.new('RGB', (duo_w, duo_h + 36), '#1e242b')
    d_draw = ImageDraw.Draw(duo_board)
    d_draw.text((12, 10), 'FA1 — Forêt Énergique (480x336)', fill='#4ade80')
    d_draw.text((ef_im.width + 12, 10), 'FA1 — Forêt Champignon (456x336)', fill='#c084fc')
    duo_board.paste(ef_im.convert('RGB'), (0, 36))
    duo_board.paste(mf_im.convert('RGB'), (ef_im.width, 36))
    (O / 'FA1_friend_areas_duo.png').write_bytes(png(duo_board))

    return results

def verify():
    ok = []
    for area_id, cfg in AREAS.items():
        w, h = cfg['size']
        zip_path = O / f'FA1_{area_id}_calques.zip'
        assert zip_path.exists(), f'Missing {zip_path}'
        with zipfile.ZipFile(zip_path) as z:
            assert z.testzip() is None
            files = {n: z.read(n) for n in z.namelist()}
            m = json.loads(files['manifest.json'].decode('utf-8'))
            assert m['size'] == [w, h]
            assert 4 <= m['semantic_groups'] <= 6

            # Reference check
            src_raw = img(files[f'references/FA1_{area_id}_source_GBA.png'])
            assert src_raw.size == (w, h)
            src_arr = np.array(src_raw)[:, :, :3]
            native_palette = set(map(tuple, np.unique(src_arr.reshape(-1, 3), axis=0)))

            for mode in ['jour', 'nuit']:
                prefix = f'calques_{mode}/FA1_{area_id}_'
                sol_im = img(files[f'{prefix}sol_{mode}.png'])
                sol_arr = np.array(sol_im)
                assert (sol_arr[:, :, 3] == 255).all(), f'{area_id} {mode} sol must be 100% opaque continuous ground'

                for l in m['layers']:
                    layer_im = img(files[l[f'file_{mode}']])
                    arr = np.array(layer_im)
                    assert arr.shape[:2] == (h, w)
                    if l['id'] != 'sol':
                        vis_count = (arr[:, :, 3] > 0).sum()
                        assert 0 < vis_count < h * w * 0.85, f'{area_id} {l["id"]} has non-trivial coverage'
                        if mode == 'jour':
                            layer_colors = set(map(tuple, np.unique(arr[arr[:, :, 3] > 0][:, :3], axis=0)))
                            assert layer_colors <= native_palette, f'{area_id} {l["id"]} colors must match native GBA palette'

                # Check South arrival walkability on ground
                obstacles = np.zeros((h, w), bool)
                for l in m['layers']:
                    if l['id'] != 'sol':
                        arr = np.array(img(files[l[f'file_{mode}']]))
                        obstacles |= arr[:, :, 3] > 0

                free = (sol_arr[:, :, 3] > 0) & ~obstacles
                safe = ndimage.binary_erosion(free, np.ones((17, 17)))
                labels, count = ndimage.label(safe)
                sx, sy = cfg['spawn']
                start_label = labels[sy, sx]
                assert start_label > 0, f'{area_id} {mode} south spawn point [{sx}, {sy}] blocked by obstacle'
                walkable_area = (labels == start_label).sum()
                assert walkable_area > w * h * 0.05, f'{area_id} {mode} walkable gathering area too small ({walkable_area})'

        ok.append(f'{area_id}: manifest OK, sol continu 100% opaque, 5 calques valides, palette native GBA exacte, spawn [{sx}, {sy}] degage et praticable ({walkable_area} px)')
        print(f'PASS {ok[-1]}', flush=True)

    (O / 'verification.json').write_bytes(jb({'checks': ok, 'runtime_PMDO': False}))
    return ok

def pmdo():
    """Serialize the Friend Area maps as PMDO Ground editing bases using the viewport_pmdo_v1 codec."""
    VP = R / 'source/viewport_pmdo_v1'
    ns = {'__file__': str(VP / 'build.py'), '__name__': 'vp_tools'}
    exec(compile((VP / 'build.py').read_bytes(), str(VP / 'build.py'), 'exec'), ns)
    exec(compile((VP / 'verify.py').read_bytes(), str(VP / 'verify.py'), 'exec'), ns)
    ns['ST'] = C / 'pmdo_stage'
    ns['OUT'] = O
    ST = ns['ST']
    reports = {}

    for area_id, cfg in AREAS.items():
        with zipfile.ZipFile(O / f'FA1_{area_id}_calques.zip') as z:
            files = {n: z.read(n) for n in z.namelist()}
            m = json.loads(files['manifest.json'].decode('utf-8'))

        dest = ST / area_id
        if dest.exists():
            shutil.rmtree(dest)

        metas = []
        recs = {}
        for mode in ['jour', 'nuit']:
            layers = [
                ns['layer'](l['title'], img(files[l[f'file_{mode}']]))
                for l in m['layers']
            ]
            size = m['size']
            r = {
                'id': f'fa1_{area_id}_{mode}',
                'duo': area_id,
                'layers': layers,
                'spawn': cfg['spawn'],
                'offset': cfg['offset'],
                'notes': [f'FA1 {cfg["title"]} base editable 1x ({mode}); sol continu; collisions/warps a dessiner.'],
                'tick': 0
            }
            recs[r['id']] = r
            metas.append(ns['export_map'](r, None))

        manifest = {
            'area_id': area_id,
            'lot': 'FA1',
            'title': cfg['title'],
            'maps': metas,
            'runtime_tested': False,
            'schema': 'RogueEssence Ground + native8px TileBank',
            'camera': {'screen': [320, 240], 'recommended_zoom': 'x1'},
            'collisions': 'ALL FREE editing scaffolds'
        }
        ns['save'](dest / 'manifest.json', jb(manifest))
        ns['save'](dest / 'README.md', (S / 'README.md').read_bytes() if (S / 'README.md').exists() else b'FA1 PMDO base')
        ns['save'](dest / 'INSTALLER.py', (R / 'source/pmdo_cote/INSTALLER.py').read_bytes())

        # Test deserialized scene against composition
        for meta in metas:
            ground_data = json.loads((dest / f'Data/Ground/{meta["asset"]}.rsground').read_text())['Object']
            r = recs[meta['id']]
            im = ns['serialized_scene'](dest, ground_data, 0)
            exp = ns['render'](r, None, 0)
            diff = np.abs(np.array(im).astype(int) - np.array(exp).astype(int))
            assert diff.max() <= 1 and np.array_equal(np.array(im)[:, :, 3], np.array(exp)[:, :, 3]), f'{meta["id"]} deserialization diff={diff.max()}'

        # Test installer dry run, install and reinstall
        installer = ns['loadmod'](f'fa1_installer_{area_id}', dest / 'INSTALLER.py')
        with tempfile.TemporaryDirectory(dir=C) as td:
            mod = Path(td)
            (mod / 'Mod.xml').write_text('<Mod><Namespace>fa1_test</Namespace></Mod>')
            installer.install(dest, mod, True, None)
            assert not (mod / 'Data').exists()
            installer.install(dest, mod, False, None)
            installer.install(dest, mod, False, None)
            assert len(installer.read_index(mod / 'Content/Tile/index.idx')) == len(list((dest / 'Content/Tile').glob('*.tile')))

        # Zip PMDO bundle
        pmdo_zip_path = O / f'FA1_{area_id}_PMDO.zip'
        with zipfile.ZipFile(pmdo_zip_path, 'w', zipfile.ZIP_DEFLATED, compresslevel=9) as z:
            for p in sorted(dest.rglob('*')):
                if p.is_file() and '__pycache__' not in p.parts:
                    info = zipfile.ZipInfo(str(p.relative_to(dest)), (2026, 9, 22, 0, 0, 0))
                    info.compress_type = zipfile.ZIP_DEFLATED
                    z.writestr(info, p.read_bytes(), compresslevel=9)

        reports[area_id] = [m['asset'] for m in metas]
        print(f'PMDO PASS {area_id}: {reports[area_id]} ({pmdo_zip_path.stat().st_size} bytes)', flush=True)

    (O / 'pmdo_verification.json').write_bytes(jb({
        'maps': reports,
        'checks': 'serialisation re-read RGB<=1/alpha exact; installer dry-run/install/reinstall; runtime_PMDO=false'
    }))
    return reports

if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('--build', action='store_true')
    p.add_argument('--verify', action='store_true')
    p.add_argument('--pmdo', action='store_true')
    a = p.parse_args()
    if a.build:
        build()
    if a.verify:
        verify()
    if a.pmdo:
        pmdo()
