"""Verification suite for the hybrid PMDO Guild Path deliverable.
Validates:
1. Exact dimensions 408x744 (multiples of 8px and 24px)
2. 100% Palette compliance with canonical sources
3. Disjoint layer recomposition matching terrain.png (0 pixel difference)
4. Decoded PMDO .tile matching terrain.png (0 pixel difference)
5. Valid JSON structure of guild_path.rsground
"""
import sys, json, io, struct
from pathlib import Path
import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).parent
RENDERS = ROOT / 'renders/sentier_guilde_hybride'
PMDO_DIR = ROOT / 'sprites/sentier_guilde_pmdo'

def decode_pmdo_tile_24(path):
    raw = path.read_bytes()
    tile_size, count = struct.unpack_from('<II', raw, 0)
    assert tile_size == 24, f"Unexpected tile size: {tile_size}"
    records = [struct.unpack_from('<IIQ', raw, 8 + i * 16) for i in range(count)]
    max_x = max(r[0] for r in records)
    max_y = max(r[1] for r in records)
    w = (max_x + 1) * tile_size
    h = (max_y + 1) * tile_size
    out = Image.new('RGBA', (w, h))
    cache = {}
    for tx, ty, off in records:
        if off not in cache:
            length, = struct.unpack_from('<q', raw, off)
            cache[off] = Image.open(io.BytesIO(raw[off + 8:off + 8 + length])).convert('RGBA')
        out.paste(cache[off], (tx * tile_size, ty * tile_size))
    return out

def main():
    print("Running verification for Sentier de la Guilde Hybride...")

    # 1. Check dimensions
    terrain_im = Image.open(RENDERS / 'terrain.png').convert('RGBA')
    w, h = terrain_im.size
    assert w == 408 and h == 744, f"Unexpected terrain dimensions: {w}x{h}"
    assert w % 24 == 0 and h % 24 == 0
    assert w % 8 == 0 and h % 8 == 0

    # 2. Check layers
    l1_im = Image.open(RENDERS / '01_sable_plage.png').convert('RGBA')
    l2_im = Image.open(RENDERS / '02_verdure_skypeak.png').convert('RGBA')
    l3_im = Image.open(RENDERS / '03_arbres_metano.png').convert('RGBA')
    l4_im = Image.open(RENDERS / '04_decorations_fleurs.png').convert('RGBA')

    for name, lim in [('01_sable_plage', l1_im), ('02_verdure_skypeak', l2_im),
                      ('03_arbres_metano', l3_im), ('04_decorations_fleurs', l4_im)]:
        assert lim.size == (w, h)
        arr = np.array(lim)
        vis = arr[:, :, 3] > 0
        assert (np.isin(arr[:, :, 3], [0, 255])).all(), f"Non-binary alpha in {name}"
        assert (arr[~vis] == 0).all(), f"Non-zero RGB under alpha 0 in {name}"

    # 3. Check disjointness of terrain base layers
    a1 = np.array(l1_im)[:, :, 3] > 0
    a2 = np.array(l2_im)[:, :, 3] > 0
    a3 = np.array(l3_im)[:, :, 3] > 0
    base_sum = a1.astype(int) + a2.astype(int) + a3.astype(int)
    assert base_sum.max() == 1, "Base layers overlap!"
    assert base_sum.min() == 1, "Base layers have unassigned pixels!"

    # 4. Check recomposition
    recomposed = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    recomposed.alpha_composite(l1_im)
    recomposed.alpha_composite(l2_im)
    recomposed.alpha_composite(l3_im)
    recomposed.alpha_composite(l4_im)
    assert recomposed.tobytes() == terrain_im.tobytes(), "Recomposed layers do not match terrain.png!"

    # 5. Check palettes against canonical banks
    beach_bank = Image.open(HERE / 'sources/beach_sand_bank.png')
    b_cols = np.unique(np.array(beach_bank).reshape(-1, 3), axis=0)
    b_set = {tuple(c) for c in b_cols.tolist()}

    sp_bank = Image.open(HERE / 'sources/skypeak_grass_bank.png')
    sp_cols = np.unique(np.array(sp_bank).reshape(-1, 3), axis=0)
    sp_set = {tuple(c) for c in sp_cols.tolist()}

    tree_bank = Image.open(HERE / 'sources/metano_tree_leaves_bank.png')
    mt_cols = np.unique(np.array(tree_bank).reshape(-1, 3), axis=0)
    mt_set = {tuple(c) for c in mt_cols.tolist()}

    u1 = np.unique(np.array(l1_im)[a1, :3], axis=0)
    u2 = np.unique(np.array(l2_im)[a2, :3], axis=0)
    u3 = np.unique(np.array(l3_im)[a3, :3], axis=0)

    assert all(tuple(c) in b_set for c in u1), "Out-of-palette pixels in sand layer!"
    assert all(tuple(c) in sp_set for c in u2), "Out-of-palette pixels in Sky Peak meadow layer!"
    assert all(tuple(c) in mt_set for c in u3), "Out-of-palette pixels in Metano tree canopy layer!"

    # 6. Check PMDO .tile decoding
    decoded_tile = decode_pmdo_tile_24(PMDO_DIR / 'GuildPath.tile')
    assert decoded_tile.tobytes() == terrain_im.tobytes(), "Decoded GuildPath.tile does not match terrain.png!"

    # 7. Check PMDO .rsground
    rsground_json = json.loads((PMDO_DIR / 'guild_path.rsground').read_text(encoding='utf-8-sig'))
    assert rsground_json['Object']['AssetName'] == 'guild_path'
    assert rsground_json['Object']['TexSize'] == 3

    # 8. Check sheets
    assert (RENDERS / 'PLANCHE_SENTIER_GUILDE.png').stat().st_size > 50000
    assert (RENDERS / 'AUDIT_MATIERES_HYBRIDES.png').stat().st_size > 50000

    report = {
        'status': 'PASS',
        'map': 'guild_path',
        'dimensions_px': [w, h],
        'tiles_24px': [w // 24, h // 24],
        'tiles_8px': [w // 8, h // 8],
        'sand_layer_pixels': int(a1.sum()),
        'meadow_layer_pixels': int(a2.sum()),
        'canopy_layer_pixels': int(a3.sum()),
        'flowers_layer_pixels': int((np.array(l4_im)[:, :, 3] > 0).sum()),
        'recomposition_match': True,
        'pmdo_tile_decoded_match': True,
        'palette_compliance': {
            'sand_treasure_town_beach': {'allowed': len(b_set), 'used': len(u1), 'out_of_palette': 0},
            'verdure_sky_peak': {'allowed': len(sp_set), 'used': len(u2), 'out_of_palette': 0},
            'verdure_metano_town_tree': {'allowed': len(mt_set), 'used': len(u3), 'out_of_palette': 0}
        }
    }
    (RENDERS / 'verification.json').write_text(json.dumps(report, indent=2))
    print("ALL VERIFICATION CHECKS PASSED WITH 100% SUCCESS!")

if __name__ == '__main__':
    main()
