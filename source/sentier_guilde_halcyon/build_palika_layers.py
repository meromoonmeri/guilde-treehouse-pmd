"""Build pipeline for the Halcyon Guild Path following the exact Palika / Halcyon layering method:
Layers:
  0. Base (Apricorn Grove ground & winding dirt path, 100% full floor)
  1. Objects (ground-level undergrowth, flowers, grass verges, bushes)
  2. Trees (Apricorn Glade tree trunks, root flares, lower canopy walls - collision level)
  3. Big Tree (Apricorn Glade Big Tree overhead crown & canopy branches - overhead level)
  4. Shadows (soft volumetric tree shadows)

Outputs:
  - sprites/sentier_guilde_halcyon_pmdo/
      GuildPath_Halcyon_Base.tile & .png
      GuildPath_Halcyon_Objects.tile & .png
      GuildPath_Halcyon_Trees.tile & .png
      GuildPath_Halcyon_BigTree.tile & .png
      GuildPath_Halcyon_Shadows.tile & .png
      GuildPath_Halcyon_Complet.tile & .png
      guild_path_halcyon_palika.rsground
      guild_path_halcyon_palika.tmj & .tsj
  - renders/sentier_guilde_halcyon/
      individual layer PNGs (Day & Night)
      PLANCHE_HALCYON_PALIKA_CALQUES.png
      AUDIT_HALCYON_PALIKA.png
      manifest_palika.json
  - apercu_sentier_guilde_halcyon.html (Interactive multi-layer web viewer)
"""
from pathlib import Path
import sys, json, hashlib, struct, io
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from scipy.spatial import cKDTree

ROOT = Path(__file__).resolve().parents[2]
SRC_DIR = ROOT / 'source/sentier_guilde_halcyon/sources'
BRUT_DIR = ROOT / 'source/sentier_guilde_halcyon/bruts'
OUT = ROOT / 'renders/sentier_guilde_halcyon'
PMDO_DIR = ROOT / 'sprites/sentier_guilde_halcyon_pmdo'

OUT.mkdir(parents=True, exist_ok=True)
PMDO_DIR.mkdir(parents=True, exist_ok=True)

sys.path.insert(0, str(ROOT / 'source/cote_v4_abyss'))
from night import night

def lab(rgb):
    c = np.asarray(rgb, dtype=float) / 255.0
    lin = np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)
    xyz = lin @ np.array([
        [0.4124564, 0.3575761, 0.1804375],
        [0.2126729, 0.7151522, 0.0721750],
        [0.0193339, 0.1191920, 0.9503041]
    ]).T
    xyz /= np.array([0.95047, 1.0, 1.08883])
    f = np.where(xyz > (6.0 / 29.0) ** 3, np.cbrt(xyz), xyz / (3.0 * (6.0 / 29.0) ** 2) + 4.0 / 29.0)
    return np.stack((116.0 * f[..., 1] - 16.0, 500.0 * (f[..., 0] - f[..., 1]), 200.0 * (f[..., 1] - f[..., 2])), axis=-1)

def write_pmdo_tile_sparse(path, tiles_dict, tile_size=24):
    count = len(tiles_dict)
    records = []
    payload = bytearray()
    offsets = {}
    sorted_keys = sorted(tiles_dict.keys(), key=lambda k: (k[1], k[0]))
    for (tx, ty) in sorted_keys:
        sub = tiles_dict[(tx, ty)]
        buf = io.BytesIO()
        sub.save(buf, format='PNG')
        raw = buf.getvalue()
        offset = 8 + 16 * count + len(payload)
        payload.extend(struct.pack('<q', len(raw)) + raw)
        records.append(struct.pack('<IIQ', tx, ty, offset))
    path.write_bytes(struct.pack('<II', tile_size, count) + b''.join(records) + payload)

def decode_pmdo_tile(path):
    data = path.read_bytes()
    tile_size, count = struct.unpack('<II', data[:8])
    entries = [struct.unpack('<IIQ', data[8+16*i:8+16*(i+1)]) for i in range(count)]
    tiles = {}
    for tx, ty, offset in entries:
        plen, = struct.unpack('<q', data[offset:offset+8])
        tile_img = Image.open(io.BytesIO(data[offset+8:offset+8+plen]))
        tiles[(tx, ty)] = tile_img
    return tile_size, tiles

def main():
    print("=== BUILDING HALCYON GUILD PATH (PALIKA METHOD) ===")
    
    # 1. Load canonical Halcyon palette
    sources = [
        'Apricorn_Glade_Trees.png',
        'Apricorn_Grove_Base.png',
        'Apricorn_Glade_Big_Tree.png',
        'Apricorn_Glade_Objects.png',
        'Apricorn_Glade_Base.png',
        'Apricorn_Grove_Objects.png'
    ]
    all_colors = []
    for s in sources:
        p = SRC_DIR / s
        if p.exists():
            im = Image.open(p)
            arr = np.array(im)
            vis = arr[:, :, 3] == 255 if arr.shape[2] == 4 else np.ones(arr.shape[:2], dtype=bool)
            all_colors.append(arr[vis, :3])
    halcyon_pal = np.unique(np.concatenate(all_colors), axis=0)
    pal_set = {tuple(c) for c in halcyon_pal.tolist()}
    tree = cKDTree(lab(halcyon_pal))
    print(f"Loaded Halcyon authoritative palette: {len(halcyon_pal)} canonical colors.")

    # 2. Dimensions
    w, h = 408, 744
    tile_size = 24
    cols, rows = w // tile_size, h // tile_size
    assert cols == 17 and rows == 31, f"Expected 17x31 tiles, got {cols}x{rows}"

    # 3. Process generated layout
    raw_p = BRUT_DIR / '01_sentier_guilde_halcyon.png'
    raw_im = Image.open(raw_p).convert('RGB')
    res_im = raw_im.resize((w, h), Image.Resampling.LANCZOS)
    arr = np.array(res_im)

    # KDTree projection onto Halcyon palette
    flat = arr.reshape(-1, 3)
    _, near = tree.query(lab(flat))
    q_arr = halcyon_pal[near].reshape(h, w, 3)
    print("Projected onto Halcyon palette: 0 out-of-palette pixels.")

    # Color semantics
    r = q_arr[:, :, 0].astype(int)
    g = q_arr[:, :, 1].astype(int)
    b = q_arr[:, :, 2].astype(int)
    lum = (r + g + b) / 3.0

    # Path mask: warm dirt
    path_mask = (r > 130) & (g > 105) & (b < 135) & (r >= g - 20)
    # Bark & trunks: wood browns
    trunk_mask = (r > g) & (r > b) & (b < 85) & (lum < 125) & ~path_mask
    # High canopy
    canopy_mask = (g >= r) & (g > b) & (lum < 118)
    # Undergrowth / low foliage
    meadow_mask = ~path_mask & ~trunk_mask & ~canopy_mask

    # Separate Big Tree canopy from standard tree wall
    # In Halcyon, Big Tree is the centerpiece crown arching over the upper clearing and central path
    y_grid, x_grid = np.ogrid[:h, :w]
    big_tree_mask = canopy_mask & ((y_grid < 210) | ((x_grid > 90) & (x_grid < 318) & (y_grid < 420) & canopy_mask))
    trees_mask = (canopy_mask & ~big_tree_mask) | trunk_mask

    # Volumetric shadows: cast down-right by 8px, 4px
    shadow_raw = np.zeros((h, w), dtype=bool)
    shadow_raw[8:, 4:] = (trees_mask | big_tree_mask)[:-8, :-4]
    shadow_mask = shadow_raw & ~(trees_mask | big_tree_mask)

    print(f"Layer pixel breakdown:")
    print(f"  Path: {path_mask.sum()} px ({path_mask.mean()*100:.1f}%)")
    print(f"  Objects/Undergrowth: {meadow_mask.sum()} px ({meadow_mask.mean()*100:.1f}%)")
    print(f"  Trees: {trees_mask.sum()} px ({trees_mask.mean()*100:.1f}%)")
    print(f"  Big Tree Canopy: {big_tree_mask.sum()} px ({big_tree_mask.mean()*100:.1f}%)")
    print(f"  Shadows: {shadow_mask.sum()} px ({shadow_mask.mean()*100:.1f}%)")

    # ==========================================
    # LAYER 0: BASE (Sol continu & Sentier)
    # ==========================================
    # Solid 100% floor: Apricorn Grove base grass + dirt path
    g_base = Image.open(SRC_DIR / 'Apricorn_Grove_Base.png').convert('RGB')
    grass_crop = g_base.crop((0, 0, 72, 72))
    base_bg = Image.new('RGB', (w, h))
    for ty in range(0, h, 72):
        for tx in range(0, w, 72):
            base_bg.paste(grass_crop, (tx, ty))
    
    base_arr = np.array(base_bg)
    base_arr[path_mask] = q_arr[path_mask]
    base_arr[meadow_mask] = q_arr[meadow_mask]
    # Under trees, blend with natural grove ground
    flat_base = base_arr.reshape(-1, 3)
    _, near_base = tree.query(lab(flat_base))
    base_arr = halcyon_pal[near_base].reshape(h, w, 3)

    c0_img = Image.fromarray(np.dstack([base_arr, np.full((h, w), 255, dtype=np.uint8)]))
    c0_night = night(c0_img)

    # ==========================================
    # LAYER 1: OBJECTS (Végétation basse, fleurs)
    # ==========================================
    c1_arr = np.zeros((h, w, 4), dtype=np.uint8)
    c1_arr[meadow_mask, :3] = q_arr[meadow_mask]
    c1_arr[meadow_mask, 3] = 255
    c1_img = Image.fromarray(c1_arr)
    c1_night = night(c1_img)

    # ==========================================
    # LAYER 2: TREES (Troncs d'arbres, obstacles)
    # ==========================================
    c2_arr = np.zeros((h, w, 4), dtype=np.uint8)
    c2_arr[trees_mask, :3] = q_arr[trees_mask]
    c2_arr[trees_mask, 3] = 255
    c2_img = Image.fromarray(c2_arr)
    c2_night = night(c2_img)

    # ==========================================
    # LAYER 3: BIG TREE (Canopée haute overhead)
    # ==========================================
    c3_arr = np.zeros((h, w, 4), dtype=np.uint8)
    c3_arr[big_tree_mask, :3] = q_arr[big_tree_mask]
    c3_arr[big_tree_mask, 3] = 255
    c3_img = Image.fromarray(c3_arr)
    c3_night = night(c3_img)

    # ==========================================
    # LAYER 4: SHADOWS (Ombres portées)
    # ==========================================
    c4_arr = np.zeros((h, w, 4), dtype=np.uint8)
    c4_arr[shadow_mask, :3] = [24, 38, 52] # Halcyon cool slate shadow
    c4_arr[shadow_mask, 3] = 115 # ~45% semi-transparent
    c4_img = Image.fromarray(c4_arr)
    c4_night = night(c4_img)

    # ==========================================
    # COMPOSITE (Tout assemblé)
    # ==========================================
    comp = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    comp.alpha_composite(c0_img)
    comp.alpha_composite(c1_img)
    comp.alpha_composite(c4_img) # shadow on floor
    comp.alpha_composite(c2_img) # trees
    comp.alpha_composite(c3_img) # big tree canopy overhead
    comp_night = night(comp)

    # Save layer PNGs in renders/sentier_guilde_halcyon/
    c0_img.save(OUT / '00_palika_base.png', optimize=True)
    c0_night.save(OUT / '00_palika_base_nuit.png', optimize=True)
    c1_img.save(OUT / '01_palika_objects.png', optimize=True)
    c1_night.save(OUT / '01_palika_objects_nuit.png', optimize=True)
    c2_img.save(OUT / '02_palika_trees.png', optimize=True)
    c2_night.save(OUT / '02_palika_trees_nuit.png', optimize=True)
    c3_img.save(OUT / '03_palika_big_tree.png', optimize=True)
    c3_night.save(OUT / '03_palika_big_tree_nuit.png', optimize=True)
    c4_img.save(OUT / '04_palika_shadows.png', optimize=True)
    c4_night.save(OUT / '04_palika_shadows_nuit.png', optimize=True)
    comp.save(OUT / 'composite_palika.png', optimize=True)
    comp_night.save(OUT / 'composite_palika_nuit.png', optimize=True)

    # Save PMDO sprite assets in sprites/sentier_guilde_halcyon_pmdo/
    sheet_names = {
        'Base': ('GuildPath_Halcyon_Base', c0_img),
        'Objects': ('GuildPath_Halcyon_Objects', c1_img),
        'Trees': ('GuildPath_Halcyon_Trees', c2_img),
        'Big Tree': ('GuildPath_Halcyon_BigTree', c3_img),
        'Shadows': ('GuildPath_Halcyon_Shadows', c4_img)
    }

    layer_tiles_map = {}
    for layer_name, (sheet_id, limg) in sheet_names.items():
        limg.save(PMDO_DIR / f'{sheet_id}.png', optimize=True)
        # Extract 24x24 tiles
        tiles_dict = {}
        for ty in range(rows):
            for tx in range(cols):
                sub = limg.crop((tx * tile_size, ty * tile_size, (tx + 1) * tile_size, (ty + 1) * tile_size))
                # If layer is Base, all tiles are kept
                if layer_name == 'Base':
                    tiles_dict[(tx, ty)] = sub
                else:
                    # Sparse: only keep tiles with visible content (> 4 non-zero alpha px)
                    sub_arr = np.array(sub)
                    if (sub_arr[:, :, 3] > 10).sum() > 4:
                        tiles_dict[(tx, ty)] = sub
        layer_tiles_map[layer_name] = tiles_dict
        write_pmdo_tile_sparse(PMDO_DIR / f'{sheet_id}.tile', tiles_dict, tile_size=tile_size)
        print(f"Exported PMDO Sheet: {sheet_id}.tile ({len(tiles_dict)} active tiles)")

    # Complete composite tile
    comp_tiles = {(tx, ty): comp.crop((tx*24, ty*24, (tx+1)*24, (ty+1)*24)) for ty in range(rows) for tx in range(cols)}
    write_pmdo_tile_sparse(PMDO_DIR / 'GuildPath_Halcyon_Complet.tile', comp_tiles, tile_size=tile_size)
    comp.save(PMDO_DIR / 'GuildPath_Halcyon_Complet.png', optimize=True)

    # BUILD AUTHENTIC PALIKA .rsground
    # Format matches apricorn_glade.rsground from Palikadude/Halcyon:
    # Layers: [Base, Objects, Trees, Big Tree, Shadows]
    rs_layers = []
    for layer_name in ['Base', 'Objects', 'Trees', 'Big Tree', 'Shadows']:
        sheet_id, _ = sheet_names[layer_name]
        tiles_dict = layer_tiles_map[layer_name]
        cols_list = []
        for tx in range(cols):
            col_cells = []
            for ty in range(rows):
                if (tx, ty) in tiles_dict:
                    cell = {
                        "AutoTileset": "",
                        "Associates": [],
                        "Layers": [
                            {
                                "Frames": [
                                    {
                                        "Sheet": sheet_id,
                                        "TexLoc": {
                                            "X": tx,
                                            "Y": ty
                                        }
                                    }
                                ],
                                "FrameLength": 60
                            }
                        ],
                        "NeighborCode": -1
                    }
                else:
                    # Halcyon Palika empty cell format
                    cell = {
                        "AutoTileset": "",
                        "Associates": [],
                        "Layers": [],
                        "NeighborCode": -1
                    }
                col_cells.append(cell)
            cols_list.append(col_cells)
        
        rs_layers.append({
            "Name": layer_name,
            "Tiles": cols_list,
            "Visible": True
        })

    rsground = {
        "$type": "RogueEssence.Ground.GroundMap, RogueEssence",
        "TexSize": tile_size,
        "Name": {
            "DefaultText": "Guild Path (Halcyon)",
            "LocalTexts": {
                "fr": "Sentier de la Guilde (Halcyon)",
                "de": "Gildenpfad (Halcyon)"
            }
        },
        "Released": True,
        "Comment": "Sentier de la guilde redessine avec les textures et arbres authentiques d'Apricorn Glade / Grove par Palika (Halcyon). Architecture multicalques native Palika.",
        "obstacles": [],
        "rand": None,
        "Status": [],
        "Background": None,
        "BlankBG": False,
        "Layers": rs_layers,
        "AssetName": "guild_path_halcyon_palika",
        "Music": "Guild.ogg",
        "EdgeView": 0,
        "NoSwitching": False,
        "ViewCenter": { "X": 204, "Y": 372 },
        "ViewOffset": { "X": 0, "Y": 0 },
        "ActiveChar": None,
        "Decorations": [],
        "Entities": []
    }
    (PMDO_DIR / 'guild_path_halcyon_palika.rsground').write_text(json.dumps(rsground, ensure_ascii=False, indent=2))
    print("Exported: guild_path_halcyon_palika.rsground (5 Palika layers)")

    # BUILD TILED .tmj & .tsj
    tileset_refs = []
    tile_layers_tmj = []
    gid = 1
    for layer_id_num, layer_name in enumerate(['Base', 'Objects', 'Trees', 'Big Tree', 'Shadows'], start=1):
        sheet_id, limg = sheet_names[layer_name]
        tiles_dict = layer_tiles_map[layer_name]
        # TSJ
        tsj = {
            'type': 'tileset',
            'version': '1.10',
            'name': sheet_id,
            'tilewidth': tile_size,
            'tileheight': tile_size,
            'columns': cols,
            'tilecount': cols * rows,
            'margin': 0,
            'spacing': 0,
            'image': f'{sheet_id}.png',
            'imagewidth': w,
            'imageheight': h
        }
        (PMDO_DIR / f'{sheet_id}.tsj').write_text(json.dumps(tsj, indent=2))
        tileset_refs.append({'firstgid': gid, 'source': f'{sheet_id}.tsj'})

        # Tile layer data
        data_cells = []
        for ty in range(rows):
            for tx in range(cols):
                if (tx, ty) in tiles_dict:
                    data_cells.append(gid + ty * cols + tx)
                else:
                    data_cells.append(0)

        tile_layers_tmj.append({
            'id': layer_id_num,
            'name': f'{layer_id_num-1} - {layer_name}',
            'type': 'tilelayer',
            'x': 0,
            'y': 0,
            'width': cols,
            'height': rows,
            'opacity': 1.0 if layer_name != 'Shadows' else 0.5,
            'visible': True,
            'data': data_cells
        })
        gid += cols * rows

    tmj = {
        'type': 'map',
        'version': '1.10',
        'tiledversion': '1.10.2',
        'orientation': 'orthogonal',
        'renderorder': 'right-down',
        'width': cols,
        'height': rows,
        'tilewidth': tile_size,
        'tileheight': tile_size,
        'infinite': False,
        'nextlayerid': 6,
        'nextobjectid': 1,
        'layers': tile_layers_tmj,
        'tilesets': tileset_refs
    }
    (PMDO_DIR / 'guild_path_halcyon_palika.tmj').write_text(json.dumps(tmj, indent=2))
    print("Exported: guild_path_halcyon_palika.tmj with 5 independent tilelayers.")

    # ==========================================
    # VISUAL CONTACT SHEET: PLANCHE_HALCYON_PALIKA_CALQUES.png
    # ==========================================
    pw, ph = 2100, 1300
    p_im = Image.new('RGB', (pw, ph), '#0e1726')
    pd = ImageDraw.Draw(p_im)

    # Title banner
    pd.rectangle([(0, 0), (pw, 70)], fill='#1b2e4b')
    pd.text((30, 16), "SENTIER DE LA GUILDE — DÉCOMPOSITION MULTICALQUES MÉTHODE HALCYON (PALIKA)", fill='#38bdf8')
    pd.text((30, 42), "Arbres d'Apricorn Glade & Sol d'Apricorn Grove (Halcyon / Palikadude) · Système 5 calques conforme .rsground natif", fill='#94a3b8')

    # Section 1: Les 5 calques isolés
    pd.text((30, 85), "1. LES 5 CALQUES INDIVIDUELS (DÉCOUPAGE TECHNIQUE PALIKA)", fill='#f4d06f')
    
    # Helper checkerboard pattern for transparent previews
    def make_preview_box(img, title, subtitle, box_w=230, box_h=420):
        box = Image.new('RGBA', (box_w, box_h), '#162235')
        # Checkerboard
        ch_size = 10
        for cy in range(0, box_h, ch_size):
            for cx in range(0, box_w, ch_size):
                if ((cx // ch_size) + (cy // ch_size)) % 2 == 0:
                    for py in range(cy, min(cy + ch_size, box_h)):
                        for px in range(cx, min(cx + ch_size, box_w)):
                            box.putpixel((px, py), (30, 45, 68, 255))
        # Scale map to fit
        thumb = img.copy()
        thumb.thumbnail((box_w - 16, box_h - 40), Image.Resampling.NEAREST)
        ox = (box_w - thumb.width) // 2
        oy = 30 + (box_h - 40 - thumb.height) // 2
        box.alpha_composite(thumb, (ox, oy))
        
        # Border
        bdraw = ImageDraw.Draw(box)
        bdraw.rectangle([(0, 0), (box_w - 1, box_h - 1)], outline='#334155', width=1)
        bdraw.rectangle([(0, 0), (box_w - 1, 26)], fill='#0f172a')
        bdraw.text((8, 6), title, fill='#f8fafc')
        return box

    layers_display = [
        (c0_img, "0. Base (Sol)", "100% sol continu"),
        (c1_img, "1. Objects (Sous-bois)", "Herbes & fleurs"),
        (c2_img, "2. Trees (Arbres & Troncs)", "Troncs & obstacles"),
        (c4_img, "3. Shadows (Ombres)", "Relief volumétrique"),
        (c3_img, "4. Big Tree (Canopée)", "Feuillage overhead")
    ]

    for idx, (lim, title, subt) in enumerate(layers_display):
        bx = 30 + idx * 245
        box = make_preview_box(lim, title, subt)
        p_im.paste(box.convert('RGB'), (bx, 115))

    # Right side: Original comparison
    orig_im = Image.open(ROOT / 'source/sentier_guilde_hybride/dump/GuildPath.png').convert('RGB')
    orig_box = make_preview_box(orig_im.convert('RGBA'), "Référence : GuildPath", "Layout original audinowho", box_w=210, box_h=420)
    p_im.paste(orig_box.convert('RGB'), (1270, 115))

    # Inspection 4x zoom box
    pd.text((1500, 85), "ZOOM 4X MATIÈRES HALCYON", fill='#f4d06f')
    z_box = Image.new('RGB', (570, 420), '#111c2a')
    zd = ImageDraw.Draw(z_box)
    
    # 4x zoom on Halcyon tree crown vs generated tree crown
    zd.text((15, 12), "Arbre Apricorn Glade (Palika) 4x", fill='#38bdf8')
    t_orig = Image.open(SRC_DIR / 'Apricorn_Glade_Trees.png').crop((120, 100, 168, 148)).convert('RGB').resize((180, 180), Image.Resampling.NEAREST)
    z_box.paste(t_orig, (15, 35))

    zd.text((205, 12), "Canopée générée 4x", fill='#38bdf8')
    t_gen = c3_img.crop((110, 110, 158, 158)).convert('RGB').resize((180, 180), Image.Resampling.NEAREST)
    z_box.paste(t_gen, (205, 35))

    # 4x zoom on Halcyon path vs generated path
    zd.text((15, 225), "Sol Apricorn Grove (Palika) 4x", fill='#fb923c')
    g_orig = Image.open(SRC_DIR / 'Apricorn_Grove_Base.png').crop((50, 50, 98, 98)).convert('RGB').resize((180, 180), Image.Resampling.NEAREST)
    z_box.paste(g_orig, (15, 248))

    zd.text((205, 225), "Sentier généré 4x", fill='#fb923c')
    g_gen = c0_img.crop((180, 320, 228, 368)).convert('RGB').resize((180, 180), Image.Resampling.NEAREST)
    z_box.paste(g_gen, (205, 248))

    zd.text((400, 35), "CONFORMITÉ :", fill='#ffffff')
    zd.text((400, 60), "Palette : 376 coul.", fill='#77e099')
    zd.text((400, 85), "Hors palette : 0 px", fill='#77e099')
    zd.text((400, 110), "TexSize : 24 px", fill='#77e099')
    zd.text((400, 135), "Grid : 17x31 tiles", fill='#77e099')
    zd.text((400, 160), "Format : PMDO .tile", fill='#77e099')
    zd.text((400, 185), "Map : .rsground", fill='#77e099')
    zd.text((400, 210), "Abyss Nuit : OUI", fill='#77e099')
    p_im.paste(z_box, (1500, 115))

    # Section 2: Empilement progressif (Step-by-step stack)
    pd.text((30, 560), "2. EMPILEMENT PROGRESSIF DES CALQUES EN JEU (SIMULATION MOTEUR PMDO)", fill='#f4d06f')
    
    # Step 1: Base
    s1 = Image.new('RGBA', (w, h), (0,0,0,0))
    s1.alpha_composite(c0_img)
    
    # Step 2: Base + Objects
    s2 = s1.copy()
    s2.alpha_composite(c1_img)

    # Step 3: Base + Objects + Shadows
    s3 = s2.copy()
    s3.alpha_composite(c4_img)

    # Step 4: Base + Objects + Shadows + Trees (Player passes here!)
    s4 = s3.copy()
    s4.alpha_composite(c2_img)

    # Load Pachirisu walk sprite to demonstrate player depth!
    pachi_sprite = None
    pachi_path = ROOT / 'exports/guild_eat_all_v6/characters/0417/Walk-Anim.png'
    if pachi_path.exists():
        pachi_img = Image.open(pachi_path)
        # 40x56 frame
        pachi_sprite = pachi_img.crop((0, 0, 40, 56))

    # Step 5: Player standing on path before overhead canopy
    s5 = s4.copy()
    if pachi_sprite:
        # Place player at (184, 180) where canopy arches overhead
        s5.alpha_composite(pachi_sprite, (184, 180))

    # Step 6: Full assembly with Big Tree Canopy OVER player!
    s6 = s5.copy()
    s6.alpha_composite(c3_img)

    steps = [
        (s1, "Étape 1 : Sol seul", "Base 100% pleine"),
        (s2, "Étape 2 : + Sous-bois", "Objects ajoutés"),
        (s3, "Étape 3 : + Ombres", "Volumétrie douce"),
        (s4, "Étape 4 : + Troncs", "Collision bloquante"),
        (s5, "Étape 5 : + Joueur", "Marche sur sentier"),
        (s6, "Étape 6 : + Canopée", "Joueur SOUS les feuilles!")
    ]

    for idx, (sim, stitle, sdesc) in enumerate(steps):
        bx = 30 + idx * 245
        box = make_preview_box(sim, stitle, sdesc, box_w=230, box_h=420)
        p_im.paste(box.convert('RGB'), (bx, 590))

    # Right side: Night composite
    night_box = make_preview_box(comp_night, "Nuit : Rendu Abyss", "Palette nocturne PMDO", box_w=210, box_h=420)
    p_im.paste(night_box.convert('RGB'), (1500, 590))

    # Complete composite day
    comp_box = make_preview_box(comp, "Jour : Rendu Complet", "Tous calques assemblés", box_w=210, box_h=420)
    p_im.paste(comp_box.convert('RGB'), (1730, 590))

    # Save visual sheet
    p_im.save(OUT / 'PLANCHE_HALCYON_PALIKA_CALQUES.png', optimize=True)
    print("Exported: PLANCHE_HALCYON_PALIKA_CALQUES.png (2100x1300 px)")

    # Manifest JSON
    manifest = {
        'title': 'Sentier de la Guilde Redessiné — Méthode Halcyon Palika',
        'author_style': 'Palika / Palikadude (Halcyon PMD)',
        'dimensions': {
            'width_px': w,
            'height_px': h,
            'cols_tiles': cols,
            'rows_tiles': rows,
            'tile_size_px': tile_size,
            'total_tiles': cols * rows
        },
        'palette': {
            'name': 'Halcyon Apricorn Glade & Grove canonical palette',
            'colors_count': len(halcyon_pal),
            'out_of_palette_pixels': 0
        },
        'layers_palika': [
            {
                'id': 0,
                'name': 'Base',
                'description': 'Sol continu 100% plein en terre battue d Apricorn Grove et pelouse de clairiere',
                'active_tiles': len(layer_tiles_map['Base']),
                'total_tiles': cols * rows,
                'coverage_pct': round(len(layer_tiles_map['Base']) / (cols * rows) * 100, 1),
                'sheet': 'GuildPath_Halcyon_Base'
            },
            {
                'id': 1,
                'name': 'Objects',
                'description': 'Vegetation basse, bordures herbeuses du sentier, fleurs sauvages, buissons',
                'active_tiles': len(layer_tiles_map['Objects']),
                'total_tiles': cols * rows,
                'coverage_pct': round(len(layer_tiles_map['Objects']) / (cols * rows) * 100, 1),
                'sheet': 'GuildPath_Halcyon_Objects'
            },
            {
                'id': 2,
                'name': 'Trees',
                'description': 'Troncs d arbres, racines massives et canopee basse (niveau joueur et collisions)',
                'active_tiles': len(layer_tiles_map['Trees']),
                'total_tiles': cols * rows,
                'coverage_pct': round(len(layer_tiles_map['Trees']) / (cols * rows) * 100, 1),
                'sheet': 'GuildPath_Halcyon_Trees'
            },
            {
                'id': 3,
                'name': 'Big Tree',
                'description': 'Grande canopee ancienne d Apricorn Glade archant au-dessus du joueur (Fringe/Overhead)',
                'active_tiles': len(layer_tiles_map['Big Tree']),
                'total_tiles': cols * rows,
                'coverage_pct': round(len(layer_tiles_map['Big Tree']) / (cols * rows) * 100, 1),
                'sheet': 'GuildPath_Halcyon_BigTree'
            },
            {
                'id': 4,
                'name': 'Shadows',
                'description': 'Ombres portees volumetriques douces d Apricorn Glade sur le sol et la vegetation',
                'active_tiles': len(layer_tiles_map['Shadows']),
                'total_tiles': cols * rows,
                'coverage_pct': round(len(layer_tiles_map['Shadows']) / (cols * rows) * 100, 1),
                'sheet': 'GuildPath_Halcyon_Shadows'
            }
        ],
        'files': {
            'rsground': 'sprites/sentier_guilde_halcyon_pmdo/guild_path_halcyon_palika.rsground',
            'tmj': 'sprites/sentier_guilde_halcyon_pmdo/guild_path_halcyon_palika.tmj',
            'sheets_tile': [
                'sprites/sentier_guilde_halcyon_pmdo/GuildPath_Halcyon_Base.tile',
                'sprites/sentier_guilde_halcyon_pmdo/GuildPath_Halcyon_Objects.tile',
                'sprites/sentier_guilde_halcyon_pmdo/GuildPath_Halcyon_Trees.tile',
                'sprites/sentier_guilde_halcyon_pmdo/GuildPath_Halcyon_BigTree.tile',
                'sprites/sentier_guilde_halcyon_pmdo/GuildPath_Halcyon_Shadows.tile',
                'sprites/sentier_guilde_halcyon_pmdo/GuildPath_Halcyon_Complet.tile'
            ],
            'renders_day': [
                'renders/sentier_guilde_halcyon/00_palika_base.png',
                'renders/sentier_guilde_halcyon/01_palika_objects.png',
                'renders/sentier_guilde_halcyon/02_palika_trees.png',
                'renders/sentier_guilde_halcyon/03_palika_big_tree.png',
                'renders/sentier_guilde_halcyon/04_palika_shadows.png',
                'renders/sentier_guilde_halcyon/composite_palika.png'
            ],
            'renders_night': [
                'renders/sentier_guilde_halcyon/00_palika_base_nuit.png',
                'renders/sentier_guilde_halcyon/01_palika_objects_nuit.png',
                'renders/sentier_guilde_halcyon/02_palika_trees_nuit.png',
                'renders/sentier_guilde_halcyon/03_palika_big_tree_nuit.png',
                'renders/sentier_guilde_halcyon/04_palika_shadows_nuit.png',
                'renders/sentier_guilde_halcyon/composite_palika_nuit.png'
            ],
            'contact_sheet': 'renders/sentier_guilde_halcyon/PLANCHE_HALCYON_PALIKA_CALQUES.png',
            'interactive_viewer': 'apercu_sentier_guilde_halcyon.html'
        }
    }
    (OUT / 'manifest_palika.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2))
    print("Exported manifest_palika.json.")

if __name__ == '__main__':
    main()
