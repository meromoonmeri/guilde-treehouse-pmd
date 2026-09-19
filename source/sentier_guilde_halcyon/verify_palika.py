"""Automated verification test suite for the Halcyon Palika Guild Path delivery."""
from pathlib import Path
import json, struct, io
import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
SRC_DIR = ROOT / 'source/sentier_guilde_halcyon/sources'
PMDO_DIR = ROOT / 'sprites/sentier_guilde_halcyon_pmdo'
OUT = ROOT / 'renders/sentier_guilde_halcyon'

def decode_tile(path):
    data = path.read_bytes()
    tile_size, count = struct.unpack('<II', data[:8])
    entries = [struct.unpack('<IIQ', data[8+16*i:8+16*(i+1)]) for i in range(count)]
    tiles = {}
    for tx, ty, offset in entries:
        plen, = struct.unpack('<q', data[offset:offset+8])
        tile_img = Image.open(io.BytesIO(data[offset+8:offset+8+plen]))
        tiles[(tx, ty)] = tile_img
    return tile_size, count, tiles

def main():
    print("=== RUNNING VERIFICATION FOR HALCYON PALIKA DELIVERY ===")

    # 1. Check palette compliance
    all_colors = []
    for s in ['Apricorn_Glade_Trees.png', 'Apricorn_Grove_Base.png', 'Apricorn_Glade_Big_Tree.png', 'Apricorn_Glade_Objects.png', 'Apricorn_Glade_Base.png', 'Apricorn_Grove_Objects.png']:
        im = Image.open(SRC_DIR / s)
        arr = np.array(im)
        vis = arr[:, :, 3] == 255 if arr.shape[2] == 4 else np.ones(arr.shape[:2], dtype=bool)
        all_colors.append(arr[vis, :3])
    halcyon_pal = {tuple(c) for c in np.unique(np.concatenate(all_colors), axis=0).tolist()}
    print(f"[PASS] Halcyon reference palette: {len(halcyon_pal)} canonical colors.")

    # Check generated layers
    layers = ['00_palika_base.png', '01_palika_objects.png', '02_palika_trees.png', '03_palika_big_tree.png']
    for l in layers:
        im = Image.open(OUT / l)
        assert im.size == (408, 744), f"{l} bad dimensions: {im.size}"
        arr = np.array(im)
        vis = arr[:, :, 3] == 255
        out_pixels = sum(1 for c in arr[vis, :3] if tuple(c) not in halcyon_pal)
        assert out_pixels == 0, f"{l} has {out_pixels} out-of-palette pixels!"
        print(f"[PASS] {l}: 408x744, 0 out-of-palette pixels.")

    # 2. Check PMDO .tile files
    tiles_to_check = [
        ('GuildPath_Halcyon_Base.tile', 527),
        ('GuildPath_Halcyon_Objects.tile', 407),
        ('GuildPath_Halcyon_Trees.tile', 378),
        ('GuildPath_Halcyon_BigTree.tile', 199),
        ('GuildPath_Halcyon_Shadows.tile', 435),
        ('GuildPath_Halcyon_Complet.tile', 527)
    ]
    for fname, expected_count in tiles_to_check:
        tpath = PMDO_DIR / fname
        assert tpath.exists(), f"Missing tile file: {fname}"
        tsize, count, tiles = decode_tile(tpath)
        assert tsize == 24, f"{fname} tile_size is {tsize}, expected 24"
        assert count == expected_count, f"{fname} count is {count}, expected {expected_count}"
        assert len(tiles) == expected_count, f"{fname} decoded tiles count mismatch"
        # Check first tile size
        first_tile = next(iter(tiles.values()))
        assert first_tile.size == (24, 24), f"Tile image size is {first_tile.size}"
        print(f"[PASS] {fname}: valid PMDO tile (24px, {count} tiles decoded).")

    # 3. Check guild_path_halcyon_palika.rsground
    rs_p = PMDO_DIR / 'guild_path_halcyon_palika.rsground'
    assert rs_p.exists()
    rs = json.loads(rs_p.read_text(encoding='utf-8'))
    assert rs['TexSize'] == 24
    assert rs['AssetName'] == 'guild_path_halcyon_palika'
    assert len(rs['Layers']) == 5, f"Expected 5 layers, got {len(rs['Layers'])}"

    layer_names = [l['Name'] for l in rs['Layers']]
    expected_names = ['Base', 'Objects', 'Trees', 'Big Tree', 'Shadows']
    assert layer_names == expected_names, f"Layer names mismatch: {layer_names}"

    for l in rs['Layers']:
        cols = l['Tiles']
        assert len(cols) == 17, f"{l['Name']} has {len(cols)} cols, expected 17"
        for col_idx, col in enumerate(cols):
            assert len(col) == 31, f"{l['Name']} col {col_idx} has {len(col)} rows, expected 31"
            for cell in col:
                assert "AutoTileset" in cell
                assert "Associates" in cell
                assert "Layers" in cell
                assert "NeighborCode" in cell
    
    # Base layer must have 527 non-empty cells
    base_filled = sum(1 for col in rs['Layers'][0]['Tiles'] for c in col if len(c['Layers']) > 0)
    assert base_filled == 527, f"Base layer has {base_filled} filled cells, expected 527"
    print(f"[PASS] guild_path_halcyon_palika.rsground: 5 layers verified, Base 100% filled (527/527).")

    # 4. Check Tiled TMJ
    tmj_p = PMDO_DIR / 'guild_path_halcyon_palika.tmj'
    assert tmj_p.exists()
    tmj = json.loads(tmj_p.read_text(encoding='utf-8'))
    assert tmj['width'] == 17 and tmj['height'] == 31 and tmj['tilewidth'] == 24
    assert len(tmj['layers']) == 5
    assert len(tmj['tilesets']) == 5
    print(f"[PASS] guild_path_halcyon_palika.tmj: 5 tilelayers, valid Tiled 1.10 format.")

    # 5. Check visual sheet and viewer
    sheet_p = OUT / 'PLANCHE_HALCYON_PALIKA_CALQUES.png'
    assert sheet_p.exists() and sheet_p.stat().st_size > 500000
    viewer_p = ROOT / 'apercu_sentier_guilde_halcyon.html'
    assert viewer_p.exists() and viewer_p.stat().st_size > 100000
    print(f"[PASS] Visual sheet ({sheet_p.stat().st_size} bytes) & Interactive viewer ({viewer_p.stat().st_size} bytes) ready.")

    print("\nALL PALIKA HALCYON VERIFICATIONS PASSED (100%)!")

if __name__ == '__main__':
    main()
