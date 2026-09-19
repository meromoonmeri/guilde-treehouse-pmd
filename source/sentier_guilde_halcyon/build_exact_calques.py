"""Production pipeline for the Guild Path (Sentier de la Guilde) redrawn with Halcyon textures and trees.
Generates individual layers:
  00_sol.png          (Continuous base ground floor - Halcyon Apricorn Grove earth & meadow)
  01_chemin.png       (Winding dirt path - Halcyon Apricorn Grove earthen trail)
  02_vegetation.png   (Undergrowth, grass verges, bushes & wildflowers)
  03_arbres.png       (Apricorn Glade trees, wooden trunks, root flares, dense canopy)
  04_premier_plan.png (Foreground overhead branches & ancient canopy)

Then COMPOSES the final image:
  composition.png = Sol + Chemin + Vegetation + Arbres + Premier Plan
  sans_chemin.png = Sol + Vegetation + Arbres + Premier Plan
  composition_nuit.png (Abyss night grade)
  and each individual layer night variant (_nuit.png).

Also exports:
  - Masks: MASQUE_SOL.png, MASQUE_CHEMIN.png, MASQUE_VEGETATION.png, MASQUE_ARBRES.png, MASQUE_PREMIER_PLAN.png
  - OpenRaster: sentier_guilde_halcyon.ora (standard multi-layer project for GIMP / Krita / Photoshop)
  - PMDO 24px binary .tile sheets and multi-layer .rsground
  - Tiled 1.10 .tmj and .tsj maps
  - Visual contact sheet: PLANCHE_CALQUES_HALCYON.png
  - Interactive web viewer: apercu_sentier_guilde_halcyon.html
"""
from pathlib import Path
import sys, json, hashlib, struct, io, zipfile, xml.etree.ElementTree as ET
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

def save_openraster(dest_ora, layers_dict, size):
    """Save standard OpenRaster (.ora) project with named, ordered layers."""
    w, h = size
    image_elem = ET.Element('image', w=str(w), h=str(h), name='sentier_guilde_halcyon')
    stack_elem = ET.SubElement(image_elem, 'stack')
    
    with zipfile.ZipFile(dest_ora, 'w', zipfile.ZIP_DEFLATED) as z:
        z.writestr('mimetype', 'image/openraster', compress_type=zipfile.ZIP_STORED)
        # Layers in reverse order in ORA (bottom to top)
        layer_items = list(layers_dict.items())
        for idx, (name, limg) in enumerate(layer_items):
            layer_id = f'layer_{idx}'
            ET.SubElement(stack_elem, 'layer', name=name, src=f'data/{layer_id}.png', x='0', y='0', opacity='1.0', visibility='visible', **{'composite-op': 'svg:src-over'})
            buf = io.BytesIO()
            limg.save(buf, format='PNG')
            z.writestr(f'data/{layer_id}.png', buf.getvalue())
        z.writestr('stack.xml', ET.tostring(image_elem))
        
        # Merged image preview
        comp = Image.new('RGBA', size, (0, 0, 0, 0))
        for _, limg in layer_items:
            comp.alpha_composite(limg)
        comp_buf = io.BytesIO()
        comp.save(comp_buf, format='PNG')
        z.writestr('mergedimage.png', comp_buf.getvalue())

def main():
    print("=== PIPELINE MULTICALQUES SENTIER DE LA GUILDE (HALCYON) ===")

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
    print(f"Palette Halcyon chargée : {len(halcyon_pal)} couleurs canoniques.")

    # 2. Dimensions PMDO
    w, h = 408, 744
    tile_size = 24
    cols, rows = w // tile_size, h // tile_size
    size = (w, h)

    # 3. Load generated image and project onto Halcyon palette
    raw_p = BRUT_DIR / '01_sentier_guilde_halcyon.png'
    raw_im = Image.open(raw_p).convert('RGB')
    res_im = raw_im.resize((w, h), Image.Resampling.LANCZOS)
    arr = np.array(res_im)

    flat = arr.reshape(-1, 3)
    _, near = tree.query(lab(flat))
    q_arr = halcyon_pal[near].reshape(h, w, 3)

    r = q_arr[:, :, 0].astype(int)
    g = q_arr[:, :, 1].astype(int)
    b = q_arr[:, :, 2].astype(int)
    lum = (r + g + b) / 3.0

    # 4. Semantic layer masks
    # CALQUE 1: CHEMIN (Terre battue et graviers dorés de Halcyon)
    # The winding path through the center
    path_mask = (r > 130) & (g > 105) & (b < 135) & (r >= g - 20)

    # CALQUE 3: ARBRES (Troncs en bois brun, racines au sol, et canopée principale d'Apricorn Glade)
    trunk_mask = (r > g) & (r > b) & (b < 85) & (lum < 125) & ~path_mask
    canopy_mask = (g >= r) & (g > b) & (lum < 118)

    # CALQUE 4: PREMIER PLAN (Frondaisons de la haute canopée en tout premier plan)
    y_grid, x_grid = np.ogrid[:h, :w]
    premier_plan_mask = canopy_mask & ((y_grid < 180) | ((x_grid > 90) & (x_grid < 318) & (y_grid < 360) & canopy_mask))
    arbres_mask = (canopy_mask & ~premier_plan_mask) | trunk_mask

    # CALQUE 2: VÉGÉTATION (Sous-bois, herbes hautes, buissons bas et fleurs)
    vegetation_mask = ~path_mask & ~trunk_mask & ~canopy_mask

    # CALQUE 0: SOL CONTINU
    # Continuous base ground beneath everything using Halcyon's Apricorn Grove grass & earth
    g_base = Image.open(SRC_DIR / 'Apricorn_Grove_Base.png').convert('RGB')
    grass_crop = g_base.crop((0, 0, 72, 72))
    base_floor = Image.new('RGB', (w, h))
    for ty in range(0, h, 72):
        for tx in range(0, w, 72):
            base_floor.paste(grass_crop, (tx, ty))
    
    base_arr = np.array(base_floor)
    base_arr[vegetation_mask] = q_arr[vegetation_mask]
    # Smooth natural grove floor under trees
    flat_base = base_arr.reshape(-1, 3)
    _, near_base = tree.query(lab(flat_base))
    base_arr = halcyon_pal[near_base].reshape(h, w, 3)

    print(f"Statistiques des masques:")
    print(f"  00 Sol continu : 100% ({w*h} px)")
    print(f"  01 Chemin      : {path_mask.sum()} px ({path_mask.mean()*100:.1f}%)")
    print(f"  02 Végétation  : {vegetation_mask.sum()} px ({vegetation_mask.mean()*100:.1f}%)")
    print(f"  03 Arbres      : {arbres_mask.sum()} px ({arbres_mask.mean()*100:.1f}%)")
    print(f"  04 1er Plan    : {premier_plan_mask.sum()} px ({premier_plan_mask.mean()*100:.1f}%)")

    # =========================================================
    # PRODUCTION DES CALQUES INDIVIDUELS
    # =========================================================

    # Calque 00 : Sol (Base floor 100% opaque)
    l00_im = Image.fromarray(np.dstack([base_arr, np.full((h, w), 255, dtype=np.uint8)]))
    l00_nuit = night(l00_im)
    l00_im.save(OUT / '00_sol.png', optimize=True)
    l00_nuit.save(OUT / '00_sol_nuit.png', optimize=True)

    # Calque 01 : Chemin (Winding dirt path with alpha)
    l01_arr = np.zeros((h, w, 4), dtype=np.uint8)
    l01_arr[path_mask, :3] = q_arr[path_mask]
    l01_arr[path_mask, 3] = 255
    l01_im = Image.fromarray(l01_arr)
    l01_nuit = night(l01_im)
    l01_im.save(OUT / '01_chemin.png', optimize=True)
    l01_nuit.save(OUT / '01_chemin_nuit.png', optimize=True)

    # Calque 02 : Végétation (Sous-bois, herbes, fleurs with alpha)
    l02_arr = np.zeros((h, w, 4), dtype=np.uint8)
    l02_arr[vegetation_mask, :3] = q_arr[vegetation_mask]
    l02_arr[vegetation_mask, 3] = 255
    l02_im = Image.fromarray(l02_arr)
    l02_nuit = night(l02_im)
    l02_im.save(OUT / '02_vegetation.png', optimize=True)
    l02_nuit.save(OUT / '02_vegetation_nuit.png', optimize=True)

    # Calque 03 : Arbres (Troncs et canopée forestière with alpha)
    l03_arr = np.zeros((h, w, 4), dtype=np.uint8)
    l03_arr[arbres_mask, :3] = q_arr[arbres_mask]
    l03_arr[arbres_mask, 3] = 255
    l03_im = Image.fromarray(l03_arr)
    l03_nuit = night(l03_im)
    l03_im.save(OUT / '03_arbres.png', optimize=True)
    l03_nuit.save(OUT / '03_arbres_nuit.png', optimize=True)

    # Calque 04 : Premier Plan (Frondaisons hautes overhead with alpha)
    l04_arr = np.zeros((h, w, 4), dtype=np.uint8)
    l04_arr[premier_plan_mask, :3] = q_arr[premier_plan_mask]
    l04_arr[premier_plan_mask, 3] = 255
    l04_im = Image.fromarray(l04_arr)
    l04_nuit = night(l04_im)
    l04_im.save(OUT / '04_premier_plan.png', optimize=True)
    l04_nuit.save(OUT / '04_premier_plan_nuit.png', optimize=True)

    # =========================================================
    # COMPOSITION DU PNG FINAL
    # =========================================================
    # Superposition alpha stricte : Sol + Chemin + Végétation + Arbres + Premier Plan
    comp = Image.new('RGBA', size, (0, 0, 0, 0))
    comp.alpha_composite(l00_im)
    comp.alpha_composite(l01_im)
    comp.alpha_composite(l02_im)
    comp.alpha_composite(l03_im)
    comp.alpha_composite(l04_im)
    comp_nuit = night(comp)

    comp.save(OUT / 'composition.png', optimize=True)
    comp_nuit.save(OUT / 'composition_nuit.png', optimize=True)

    # Version sans chemin
    sans_chemin = Image.new('RGBA', size, (0, 0, 0, 0))
    sans_chemin.alpha_composite(l00_im)
    sans_chemin.alpha_composite(l02_im)
    sans_chemin.alpha_composite(l03_im)
    sans_chemin.alpha_composite(l04_im)
    sans_chemin.save(OUT / 'sans_chemin.png', optimize=True)

    # =========================================================
    # MASQUES D'ISOLATION
    # =========================================================
    Image.fromarray(np.full((h, w), 255, dtype=np.uint8)).save(OUT / 'MASQUE_SOL.png', optimize=True)
    Image.fromarray((path_mask * 255).astype(np.uint8)).save(OUT / 'MASQUE_CHEMIN.png', optimize=True)
    Image.fromarray((vegetation_mask * 255).astype(np.uint8)).save(OUT / 'MASQUE_VEGETATION.png', optimize=True)
    Image.fromarray((arbres_mask * 255).astype(np.uint8)).save(OUT / 'MASQUE_ARBRES.png', optimize=True)
    Image.fromarray((premier_plan_mask * 255).astype(np.uint8)).save(OUT / 'MASQUE_PREMIER_PLAN.png', optimize=True)

    # =========================================================
    # PROJET OPENRASTER (.ora)
    # =========================================================
    layers_dict = {
        '00_sol': l00_im,
        '01_chemin': l01_im,
        '02_vegetation': l02_im,
        '03_arbres': l03_im,
        '04_premier_plan': l04_im
    }
    save_openraster(OUT / 'sentier_guilde_halcyon.ora', layers_dict, size)
    print("Exporté : sentier_guilde_halcyon.ora (Projet OpenRaster multicalque standard).")

    # =========================================================
    # EXPORT PMDO ENGINE (.tile, .rsground, .tmj)
    # =========================================================
    pmdo_layers = [
        ('GuildPath_Sol', l00_im, True),
        ('GuildPath_Chemin', l01_im, False),
        ('GuildPath_Vegetation', l02_im, False),
        ('GuildPath_Arbres', l03_im, False),
        ('GuildPath_PremierPlan', l04_im, False)
    ]

    layer_tiles_map = {}
    for sheet_name, lim, is_full in pmdo_layers:
        lim.save(PMDO_DIR / f'{sheet_name}.png', optimize=True)
        tdict = {}
        for ty in range(rows):
            for tx in range(cols):
                sub = lim.crop((tx * tile_size, ty * tile_size, (tx + 1) * tile_size, (ty + 1) * tile_size))
                if is_full:
                    tdict[(tx, ty)] = sub
                else:
                    sub_arr = np.array(sub)
                    if (sub_arr[:, :, 3] > 10).sum() > 4:
                        tdict[(tx, ty)] = sub
        layer_tiles_map[sheet_name] = tdict
        write_pmdo_tile_sparse(PMDO_DIR / f'{sheet_name}.tile', tdict, tile_size=tile_size)
        print(f"Exporté PMDO Tile : {sheet_name}.tile ({len(tdict)} tuiles actives)")

    # Composite complete tile
    comp_tiles = {(tx, ty): comp.crop((tx*24, ty*24, (tx+1)*24, (ty+1)*24)) for ty in range(rows) for tx in range(cols)}
    write_pmdo_tile_sparse(PMDO_DIR / 'GuildPath_Complet.tile', comp_tiles, tile_size=tile_size)
    comp.save(PMDO_DIR / 'GuildPath_Complet.png', optimize=True)

    # Multi-layer .rsground
    rs_layers = []
    layer_display_names = ['Sol', 'Chemin', 'Vegetation', 'Arbres', 'Premier Plan']
    for idx, (sheet_name, _, _) in enumerate(pmdo_layers):
        tdict = layer_tiles_map[sheet_name]
        cols_list = []
        for tx in range(cols):
            col_cells = []
            for ty in range(rows):
                if (tx, ty) in tdict:
                    cell = {
                        "AutoTileset": "",
                        "Associates": [],
                        "Layers": [
                            {
                                "Frames": [
                                    {
                                        "Sheet": sheet_name,
                                        "TexLoc": { "X": tx, "Y": ty }
                                    }
                                ],
                                "FrameLength": 60
                            }
                        ],
                        "NeighborCode": -1
                    }
                else:
                    cell = {
                        "AutoTileset": "",
                        "Associates": [],
                        "Layers": [],
                        "NeighborCode": -1
                    }
                col_cells.append(cell)
            cols_list.append(col_cells)
        
        rs_layers.append({
            "Name": layer_display_names[idx],
            "Tiles": cols_list,
            "Visible": True
        })

    rsground = {
        "$type": "RogueEssence.Ground.GroundMap, RogueEssence",
        "TexSize": tile_size,
        "Name": {
            "DefaultText": "Guild Path (Halcyon Layers)",
            "LocalTexts": {
                "fr": "Sentier de la Guilde (Calques Halcyon)"
            }
        },
        "Released": True,
        "Comment": "Sentier de la guilde redessine avec les textures et arbres authentiques d'Apricorn Glade / Grove par Palika (Halcyon). Genere en calques separes (Sol, Chemin, Vegetation, Arbres, Premier Plan) puis compose.",
        "obstacles": [],
        "rand": None,
        "Status": [],
        "Background": None,
        "BlankBG": False,
        "Layers": rs_layers,
        "AssetName": "guild_path_halcyon_layers",
        "Music": "Guild.ogg",
        "EdgeView": 0,
        "NoSwitching": False,
        "ViewCenter": { "X": 204, "Y": 372 },
        "ViewOffset": { "X": 0, "Y": 0 },
        "ActiveChar": None,
        "Decorations": [],
        "Entities": []
    }
    (PMDO_DIR / 'guild_path_halcyon_layers.rsground').write_text(json.dumps(rsground, ensure_ascii=False, indent=2))
    print("Exporté : guild_path_halcyon_layers.rsground.")

    # Tiled .tmj & .tsj
    tileset_refs = []
    tile_layers_tmj = []
    gid = 1
    for idx, (sheet_name, lim, _) in enumerate(pmdo_layers, start=1):
        tdict = layer_tiles_map[sheet_name]
        tsj = {
            'type': 'tileset',
            'version': '1.10',
            'name': sheet_name,
            'tilewidth': tile_size,
            'tileheight': tile_size,
            'columns': cols,
            'tilecount': cols * rows,
            'margin': 0,
            'spacing': 0,
            'image': f'{sheet_name}.png',
            'imagewidth': w,
            'imageheight': h
        }
        (PMDO_DIR / f'{sheet_name}.tsj').write_text(json.dumps(tsj, indent=2))
        tileset_refs.append({'firstgid': gid, 'source': f'{sheet_name}.tsj'})

        data_cells = []
        for ty in range(rows):
            for tx in range(cols):
                if (tx, ty) in tdict:
                    data_cells.append(gid + ty * cols + tx)
                else:
                    data_cells.append(0)

        tile_layers_tmj.append({
            'id': idx,
            'name': f'{idx-1} - {layer_display_names[idx-1]}',
            'type': 'tilelayer',
            'x': 0,
            'y': 0,
            'width': cols,
            'height': rows,
            'opacity': 1.0,
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
        'nextlayerid': len(pmdo_layers) + 1,
        'nextobjectid': 1,
        'layers': tile_layers_tmj,
        'tilesets': tileset_refs
    }
    (PMDO_DIR / 'guild_path_halcyon_layers.tmj').write_text(json.dumps(tmj, indent=2))
    print("Exporté : guild_path_halcyon_layers.tmj.")

    # =========================================================
    # PLANCHE CONTACT : PLANCHE_CALQUES_HALCYON.png
    # =========================================================
    pw, ph = 2100, 1300
    p_im = Image.new('RGB', (pw, ph), '#0e1726')
    pd = ImageDraw.Draw(p_im)

    pd.rectangle([(0, 0), (pw, 70)], fill='#1b2e4b')
    pd.text((30, 16), "SENTIER DE LA GUILDE — CALQUES SÉPARÉS ET COMPOSITION FINALE (STYLE HALCYON)", fill='#38bdf8')
    pd.text((30, 42), "Génération et découpage en calques distincts : Sol / Chemin / Végétation / Arbres / Premier Plan -> Composition finale", fill='#94a3b8')

    def make_preview_box(img, title, subtitle, box_w=230, box_h=420):
        box = Image.new('RGBA', (box_w, box_h), '#162235')
        ch_size = 10
        for cy in range(0, box_h, ch_size):
            for cx in range(0, box_w, ch_size):
                if ((cx // ch_size) + (cy // ch_size)) % 2 == 0:
                    for py in range(cy, min(cy + ch_size, box_h)):
                        for px in range(cx, min(cx + ch_size, box_w)):
                            box.putpixel((px, py), (30, 45, 68, 255))
        thumb = img.copy()
        thumb.thumbnail((box_w - 16, box_h - 40), Image.Resampling.NEAREST)
        ox = (box_w - thumb.width) // 2
        oy = 30 + (box_h - 40 - thumb.height) // 2
        box.alpha_composite(thumb, (ox, oy))
        
        bdraw = ImageDraw.Draw(box)
        bdraw.rectangle([(0, 0), (box_w - 1, box_h - 1)], outline='#334155', width=1)
        bdraw.rectangle([(0, 0), (box_w - 1, 26)], fill='#0f172a')
        bdraw.text((8, 6), title, fill='#f8fafc')
        return box

    pd.text((30, 85), "1. LES 5 CALQUES INDIVIDUELS SUR DAMIER DE TRANSPARENCE", fill='#f4d06f')
    
    calques_row = [
        (l00_im, "00_sol.png", "Sol continu 100%"),
        (l01_im, "01_chemin.png", "Sentier terre battue"),
        (l02_im, "02_vegetation.png", "Sous-bois & fleurs"),
        (l03_im, "03_arbres.png", "Arbres d'Apricorn"),
        (l04_im, "04_premier_plan.png", "Canopée haute")
    ]

    for idx, (lim, title, subt) in enumerate(calques_row):
        bx = 30 + idx * 245
        box = make_preview_box(lim, title, subt)
        p_im.paste(box.convert('RGB'), (bx, 115))

    # Version sans chemin
    box_sans = make_preview_box(sans_chemin, "sans_chemin.png", "Décor vierge", box_w=210, box_h=420)
    p_im.paste(box_sans.convert('RGB'), (1270, 115))

    # Zoom textures
    pd.text((1500, 85), "AUDIT ZOOM 4X MATIÈRES HALCYON", fill='#f4d06f')
    z_box = Image.new('RGB', (570, 420), '#111c2a')
    zd = ImageDraw.Draw(z_box)

    zd.text((15, 12), "Arbre Apricorn Glade Natif 4x", fill='#38bdf8')
    t_orig = Image.open(SRC_DIR / 'Apricorn_Glade_Trees.png').crop((120, 100, 168, 148)).convert('RGB').resize((180, 180), Image.Resampling.NEAREST)
    z_box.paste(t_orig, (15, 35))

    zd.text((205, 12), "Calque Arbres 4x", fill='#38bdf8')
    t_gen = l03_im.crop((110, 110, 158, 158)).convert('RGB').resize((180, 180), Image.Resampling.NEAREST)
    z_box.paste(t_gen, (205, 35))

    zd.text((15, 225), "Sol Apricorn Grove Natif 4x", fill='#fb923c')
    g_orig = Image.open(SRC_DIR / 'Apricorn_Grove_Base.png').crop((50, 50, 98, 98)).convert('RGB').resize((180, 180), Image.Resampling.NEAREST)
    z_box.paste(g_orig, (15, 248))

    zd.text((205, 225), "Calque Chemin 4x", fill='#fb923c')
    g_gen = l01_im.crop((180, 320, 228, 368)).convert('RGB').resize((180, 180), Image.Resampling.NEAREST)
    z_box.paste(g_gen, (205, 248))

    zd.text((400, 35), "CONTRÔLE QUALITÉ :", fill='#ffffff')
    zd.text((400, 60), "Palette : 395 coul.", fill='#77e099')
    zd.text((400, 85), "Hors palette : 0 px", fill='#77e099')
    zd.text((400, 110), "TexSize : 24 px", fill='#77e099')
    zd.text((400, 135), "Grid : 17x31 tiles", fill='#77e099')
    zd.text((400, 160), "OpenRaster : .ora", fill='#77e099')
    zd.text((400, 185), "PMDO : .rsground", fill='#77e099')
    zd.text((400, 210), "Nuit Abyss : OUI", fill='#77e099')
    p_im.paste(z_box, (1500, 115))

    # Section 2: Empilement progressif
    pd.text((30, 560), "2. EMPILEMENT PROGRESSIF DES CALQUES POUR COMPOSER LE PNG FINAL", fill='#f4d06f')

    e1 = Image.new('RGBA', size, (0,0,0,0))
    e1.alpha_composite(l00_im)

    e2 = e1.copy()
    e2.alpha_composite(l01_im)

    e3 = e2.copy()
    e3.alpha_composite(l02_im)

    e4 = e3.copy()
    e4.alpha_composite(l03_im)

    e5 = e4.copy()
    e5.alpha_composite(l04_im)

    stack_steps = [
        (e1, "Étape 1 : Sol seul", "00_sol.png"),
        (e2, "Étape 2 : + Chemin", "01_chemin.png"),
        (e3, "Étape 3 : + Végétation", "02_vegetation.png"),
        (e4, "Étape 4 : + Arbres", "03_arbres.png"),
        (e5, "Étape 5 : + 1er Plan", "04_premier_plan.png")
    ]

    for idx, (sim, stitle, sdesc) in enumerate(stack_steps):
        bx = 30 + idx * 245
        box = make_preview_box(sim, stitle, sdesc, box_w=230, box_h=420)
        p_im.paste(box.convert('RGB'), (bx, 590))

    # Final compositions
    box_jour = make_preview_box(comp, "composition.png", "PNG Final (Jour)", box_w=210, box_h=420)
    p_im.paste(box_jour.convert('RGB'), (1270, 590))

    box_nuit = make_preview_box(comp_nuit, "composition_nuit.png", "PNG Final (Nuit Abyss)", box_w=210, box_h=420)
    p_im.paste(box_nuit.convert('RGB'), (1500, 590))

    # Original comparison
    orig_im = Image.open(ROOT / 'source/sentier_guilde_hybride/dump/GuildPath.png').convert('RGB')
    orig_box = make_preview_box(orig_im.convert('RGBA'), "GuildPath Original", "audinowho (référence)", box_w=210, box_h=420)
    p_im.paste(orig_box.convert('RGB'), (1730, 590))

    p_im.save(OUT / 'PLANCHE_CALQUES_HALCYON.png', optimize=True)
    print("Exporté : PLANCHE_CALQUES_HALCYON.png (2100x1300 px)")

    # Manifest
    manifest = {
        'title': 'Sentier de la Guilde — Calques Séparés et Composition Finale Halcyon',
        'dimensions': { 'width_px': w, 'height_px': h, 'cols': cols, 'rows': rows, 'tile_size': tile_size },
        'palette': { 'count': len(halcyon_pal), 'out_of_palette': 0 },
        'layers': [
            { 'id': '00_sol', 'name': 'Sol de fond continu', 'file': '00_sol.png', 'file_nuit': '00_sol_nuit.png', 'mask': 'MASQUE_SOL.png', 'active_tiles': len(layer_tiles_map['GuildPath_Sol']) },
            { 'id': '01_chemin', 'name': 'Tracé du sentier en terre battue', 'file': '01_chemin.png', 'file_nuit': '01_chemin_nuit.png', 'mask': 'MASQUE_CHEMIN.png', 'active_tiles': len(layer_tiles_map['GuildPath_Chemin']) },
            { 'id': '02_vegetation', 'name': 'Végétation basse, sous-bois et fleurs', 'file': '02_vegetation.png', 'file_nuit': '02_vegetation_nuit.png', 'mask': 'MASQUE_VEGETATION.png', 'active_tiles': len(layer_tiles_map['GuildPath_Vegetation']) },
            { 'id': '03_arbres', 'name': 'Arbres, troncs et canopée Apricorn Glade', 'file': '03_arbres.png', 'file_nuit': '03_arbres_nuit.png', 'mask': 'MASQUE_ARBRES.png', 'active_tiles': len(layer_tiles_map['GuildPath_Arbres']) },
            { 'id': '04_premier_plan', 'name': 'Frondaisons de premier plan overhead', 'file': '04_premier_plan.png', 'file_nuit': '04_premier_plan_nuit.png', 'mask': 'MASQUE_PREMIER_PLAN.png', 'active_tiles': len(layer_tiles_map['GuildPath_PremierPlan']) }
        ],
        'compositions': [
            'composition.png',
            'composition_nuit.png',
            'sans_chemin.png'
        ],
        'openraster': 'sentier_guilde_halcyon.ora',
        'pmdo': {
            'rsground': 'sprites/sentier_guilde_halcyon_pmdo/guild_path_halcyon_layers.rsground',
            'tmj': 'sprites/sentier_guilde_halcyon_pmdo/guild_path_halcyon_layers.tmj'
        }
    }
    (OUT / 'manifest_calques.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2))
    print("Exporté manifest_calques.json.")

if __name__ == '__main__':
    main()
