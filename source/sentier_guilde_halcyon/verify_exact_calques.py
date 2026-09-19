"""Verification suite for the multi-layer Guild Path delivery (Halcyon style)."""
from pathlib import Path
import json, struct, io, zipfile, xml.etree.ElementTree as ET
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
    print("=== TESTS DE VÉRIFICATION MULTICALQUES SENTIER DE LA GUILDE ===")

    # 1. Palette Halcyon
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
        im = Image.open(SRC_DIR / s)
        arr = np.array(im)
        vis = arr[:, :, 3] == 255 if arr.shape[2] == 4 else np.ones(arr.shape[:2], dtype=bool)
        all_colors.append(arr[vis, :3])
    halcyon_pal = {tuple(c) for c in np.unique(np.concatenate(all_colors), axis=0).tolist()}
    print(f"[TEST 1/6 PASS] Palette Halcyon : {len(halcyon_pal)} couleurs canoniques.")

    # 2. Dimensions et conformité palette des calques
    layers = ['00_sol.png', '01_chemin.png', '02_vegetation.png', '03_arbres.png', '04_premier_plan.png']
    for l in layers:
        im = Image.open(OUT / l)
        assert im.size == (408, 744), f"Mauvaises dimensions pour {l} : {im.size}"
        arr = np.array(im)
        vis = arr[:, :, 3] == 255
        out_px = sum(1 for c in arr[vis, :3] if tuple(c) not in halcyon_pal)
        assert out_px == 0, f"{l} contient {out_px} pixels hors palette !"
        print(f"  [OK] {l} : 408x744 px, 0 pixel hors palette.")
    print("[TEST 2/6 PASS] Tous les calques respectent strictement la palette Halcyon.")

    # 3. Exacte recomposition alpha
    comp_ref = Image.open(OUT / 'composition.png')
    recomp = Image.new('RGBA', (408, 744), (0, 0, 0, 0))
    for l in layers:
        recomp.alpha_composite(Image.open(OUT / l))
    assert recomp.tobytes() == comp_ref.tobytes(), "La recomposition alpha des calques ne correspond pas au PNG final !"
    print("[TEST 3/6 PASS] Recomposition alpha exacte : Sol + Chemin + Végétation + Arbres + 1er Plan = composition.png.")

    # 4. OpenRaster .ora
    ora_path = OUT / 'sentier_guilde_halcyon.ora'
    assert ora_path.exists(), "Fichier .ora manquant !"
    with zipfile.ZipFile(ora_path) as z:
        assert 'mimetype' in z.namelist()
        assert 'stack.xml' in z.namelist()
        assert 'mergedimage.png' in z.namelist()
        xml_root = ET.fromstring(z.read('stack.xml'))
        layer_elems = xml_root.findall('.//layer')
        assert len(layer_elems) == 5, f"Le .ora doit avoir 5 calques, trouvé : {len(layer_elems)}"
    print("[TEST 4/6 PASS] Projet OpenRaster sentier_guilde_halcyon.ora valide (5 calques, metadata XML, preview).")

    # 5. Fichiers binaires PMDO .tile
    pmdo_tiles = [
        ('GuildPath_Sol.tile', 527),
        ('GuildPath_Chemin.tile', 240),
        ('GuildPath_Vegetation.tile', 407),
        ('GuildPath_Arbres.tile', 391),
        ('GuildPath_PremierPlan.tile', 169),
        ('GuildPath_Complet.tile', 527)
    ]
    for tname, exp_count in pmdo_tiles:
        tsize, count, tiles = decode_tile(PMDO_DIR / tname)
        assert tsize == 24 and count == exp_count
        assert len(tiles) == exp_count
        first = next(iter(tiles.values()))
        assert first.size == (24, 24)
    print("[TEST 5/6 PASS] Toutes les feuilles .tile PMDO sont valides et décodables (24px).")

    # 6. PMDO .rsground et Tiled .tmj
    rs = json.loads((PMDO_DIR / 'guild_path_halcyon_layers.rsground').read_text(encoding='utf-8'))
    assert rs['TexSize'] == 24 and len(rs['Layers']) == 5
    tmj = json.loads((PMDO_DIR / 'guild_path_halcyon_layers.tmj').read_text(encoding='utf-8'))
    assert tmj['width'] == 17 and tmj['height'] == 31 and len(tmj['layers']) == 5
    print("[TEST 6/6 PASS] guild_path_halcyon_layers.rsground et .tmj conformes au moteur.")

    print("\nTOUS LES TESTS SONT VALIDÉS AVEC SUCCÈS (100%) !")

if __name__ == '__main__':
    main()
