"""Verification test suite for the Halcyon swapped Guild Path delivery."""
from pathlib import Path
import json, struct, io, zipfile, xml.etree.ElementTree as ET
import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
BANKS_DIR = ROOT / 'source/sentier_guilde_halcyon/banks'
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
    print("=== VÉRIFICATION DU SENTIER DE LA GUILDE RETEXTURÉ HALCYON ===")

    # 1. Dimensions
    w, h = 408, 744
    layers = ['00_sol.png', '01_chemin.png', '02_vegetation.png', '03_arbres.png', '04_decorations_fleurs.png']
    for l in layers:
        im = Image.open(OUT / l)
        assert im.size == (w, h), f"Bad dimensions for {l}: {im.size}"
        print(f"  [OK] {l} : {im.size}")

    # 2. Palette compliance with Halcyon banks
    path_bank = np.unique(np.array(Image.open(BANKS_DIR / 'halcyon_path_bank.png')).reshape(-1, 3), axis=0)
    grass_bank = np.unique(np.array(Image.open(BANKS_DIR / 'halcyon_grass_bank.png')).reshape(-1, 3), axis=0)
    tree_bank = np.unique(np.array(Image.open(BANKS_DIR / 'halcyon_tree_bank.png')).reshape(-1, 3), axis=0)

    p_set = {tuple(c) for c in path_bank.tolist()}
    g_set = {tuple(c) for c in grass_bank.tolist()}
    t_set = {tuple(c) for c in tree_bank.tolist()}

    c_arr = np.array(Image.open(OUT / '01_chemin.png'))
    c_vis = c_arr[:, :, 3] == 255
    assert all(tuple(c) in p_set for c in c_arr[c_vis, :3]), "Chemin contient des couleurs hors banque Halcyon !"
    print(f"  [OK] 01_chemin.png : 100% conforme banque terre battue Halcyon ({len(p_set)} coul).")

    v_arr = np.array(Image.open(OUT / '02_vegetation.png'))
    v_vis = v_arr[:, :, 3] == 255
    assert all(tuple(c) in g_set for c in v_arr[v_vis, :3]), "Végétation contient des couleurs hors banque Halcyon !"
    print(f"  [OK] 02_vegetation.png : 100% conforme banque herbe Halcyon ({len(g_set)} coul).")

    a_arr = np.array(Image.open(OUT / '03_arbres.png'))
    a_vis = a_arr[:, :, 3] == 255
    assert all(tuple(c) in t_set for c in a_arr[a_vis, :3]), "Arbres contient des couleurs hors banque Halcyon !"
    print(f"  [OK] 03_arbres.png : 100% conforme banque arbres Halcyon ({len(t_set)} coul).")

    # 3. Composition match
    comp_ref = Image.open(OUT / 'composition.png')
    recomp = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    recomp.alpha_composite(Image.open(OUT / '00_sol.png'))
    recomp.alpha_composite(Image.open(OUT / '02_vegetation.png'))
    recomp.alpha_composite(Image.open(OUT / '01_chemin.png'))
    recomp.alpha_composite(Image.open(OUT / '03_arbres.png'))
    recomp.alpha_composite(Image.open(OUT / '04_decorations_fleurs.png'))
    assert recomp.tobytes() == comp_ref.tobytes(), "Recomposition mismatch!"
    print("  [OK] Recomposition alpha exacte : Sol + Végétation + Chemin + Arbres + Fleurs == composition.png")

    # 4. PMDO .tile
    tsize, count, tiles = decode_tile(PMDO_DIR / 'GuildPath.tile')
    assert tsize == 24 and count == 527
    assert len(tiles) == 527
    print(f"  [OK] PMDO GuildPath.tile : 24px, 527 tuiles décodées avec succès.")

    # 5. OpenRaster .ora
    with zipfile.ZipFile(OUT / 'sentier_guilde_halcyon.ora') as z:
        assert 'stack.xml' in z.namelist() and 'mergedimage.png' in z.namelist()
        xml = ET.fromstring(z.read('stack.xml'))
        assert len(xml.findall('.//layer')) == 5
    print("  [OK] sentier_guilde_halcyon.ora : Projet OpenRaster 5 calques valide.")

    print("\nTOUTES LES VÉRIFICATIONS SONT VALIDÉES À 100% !")

if __name__ == '__main__':
    main()
