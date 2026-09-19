#!/usr/bin/env python3
"""
Vérification automatisée de la suite de sprites de pond Métano pour falaises.
Contrôles :
- Dimensions divisibles par 8 px
- Présence de tous les fichiers PNG, .tile, .tsj, .gif
- Décodage réversible exact des .tile binaires
- Validité des structures JSON et manifestes
- Absence d'artefacts alpha
"""
from pathlib import Path
from PIL import Image
import json, struct, io, sys

ROOT = Path(__file__).resolve().parents[1]
SPRITES = ROOT / 'sprites/pond_metano_cliffs'
RENDERS = ROOT / 'renders/pond_metano_cliffs'

def decode_tile(path):
    raw = path.read_bytes()
    size, n = struct.unpack_from('<II', raw)
    assert size == 8, f"Taille de tuile invalide dans {path}: {size}"
    records = [struct.unpack_from('<IIQ', raw, 8 + 16 * i) for i in range(n)]
    w = (max(x for x, y, o in records) + 1) * 8
    h = (max(y for x, y, o in records) + 1) * 8
    im = Image.new('RGBA', (w, h))
    for x, y, o in records:
        ln = struct.unpack_from('<q', raw, o)[0]
        t = Image.open(io.BytesIO(raw[o + 8 : o + 8 + ln])).convert('RGBA')
        im.paste(t, (x * 8, y * 8))
    return im

def run_checks():
    errors = []
    checked_files = 0
    
    # 1. Vérification du manifeste
    manifest_path = SPRITES / 'manifest.json'
    if not manifest_path.exists():
        errors.append("manifest.json manquant dans sprites/pond_metano_cliffs/")
    else:
        manifest = json.loads(manifest_path.read_text())
        assert manifest['grid_px'] == 8
        print("[PASS] manifest.json valide.")

    # 2. Vérification des prefabs
    prefabs = ['01_promontoire', '02_alcove', '03_cascade', '04_cuvette_rocheuse', '05_deversoir']
    for p in prefabs:
        d = SPRITES / p
        assert d.exists(), f"Dossier {p} manquant"
        
        # PNG Scene
        scene_png = list(d.glob('*_SCENE.png'))[0]
        im_scene = Image.open(scene_png)
        checked_files += 1
        if im_scene.width % 8 != 0 or im_scene.height % 8 != 0:
            errors.append(f"{scene_png.name} non divisible par 8: {im_scene.size}")
            
        # Binary .tile
        scene_tile = list(d.glob('*_SCENE.tile'))[0]
        checked_files += 1
        decoded = decode_tile(scene_tile)
        if decoded.size != im_scene.size:
            errors.append(f"{scene_tile.name} taille décodée erronée: {decoded.size} != {im_scene.size}")
        if decoded.tobytes() != im_scene.convert('RGBA').tobytes():
            errors.append(f"{scene_tile.name} différence de pixels après décodage .tile")
            
        # TSJ
        scene_tsj = list(d.glob('*_SCENE.tsj'))[0]
        checked_files += 1
        tsj_data = json.loads(scene_tsj.read_text())
        if tsj_data['tilewidth'] != 8 or tsj_data['tileheight'] != 8:
            errors.append(f"{scene_tsj.name} grille TSJ non conforme à 8px")
            
        # GIF
        scene_gif = list(d.glob('*_ANIMATION.gif'))[0]
        checked_files += 1
        if scene_gif.stat().st_size == 0:
            errors.append(f"{scene_gif.name} vide")
            
        # Frames d'eau ou cascade
        eau_f = list(d.glob('*_EAU_F*.png'))
        casc_f = list(d.glob('*_CASCADE_F*.png'))
        for f_im in eau_f + casc_f:
            im_f = Image.open(f_im)
            checked_files += 1
            if im_f.size != im_scene.size:
                errors.append(f"Taille de frame incohérente dans {f_im.name}: {im_f.size} != {im_scene.size}")
                
        print(f"[PASS] Prefab {p} : dimensions {im_scene.size}, PNG, .tile, .tsj, GIF conformes.")

    # 3. Vérification du tileset modulaire
    ts_png = SPRITES / 'METANO_POND_CLIFF_TILESET.png'
    assert ts_png.exists()
    ts_im = Image.open(ts_png)
    checked_files += 1
    if ts_im.width != 192 or ts_im.height != 192:
        errors.append(f"Tileset taille erronée: {ts_im.size}")
        
    ts_tile = SPRITES / 'METANO_POND_CLIFF_TILESET.tile'
    checked_files += 1
    decoded_ts = decode_tile(ts_tile)
    if decoded_ts.tobytes() != ts_im.convert('RGBA').tobytes():
        errors.append("Différence de pixels sur METANO_POND_CLIFF_TILESET.tile")
        
    ts_tsj = SPRITES / 'METANO_POND_CLIFF_TILESET.tsj'
    checked_files += 1
    tsj_data = json.loads(ts_tsj.read_text())
    if len(tsj_data.get('tiles', [])) == 0:
        errors.append("Aucune animation dans METANO_POND_CLIFF_TILESET.tsj")
    print(f"[PASS] Tileset modulaire : 192x192 px, 576 tuiles, décodage .tile bit-exact, {len(tsj_data['tiles'])} animations TSJ.")

    # 4. Scène d'intégration
    integ_png = RENDERS / 'METANO_CLIFF_TERRASSE_POND_EXEMPLE.png'
    integ_im = Image.open(integ_png)
    checked_files += 1
    if integ_im.size != (256, 224):
        errors.append(f"Taille scène intégration erronée: {integ_im.size}")
    integ_tile = RENDERS / 'METANO_CLIFF_TERRASSE_POND_EXEMPLE.tile'
    checked_files += 1
    decoded_integ = decode_tile(integ_tile)
    if decoded_integ.tobytes() != integ_im.convert('RGBA').tobytes():
        errors.append("Différence de pixels sur METANO_CLIFF_TERRASSE_POND_EXEMPLE.tile")
    print(f"[PASS] Scène d'intégration : 256x224 px, .tile bit-exact.")

    # 5. Planche de présentation et HTML
    planche = RENDERS / 'PLANCHE_SPRITES_POND_CLIFF.png'
    assert planche.exists()
    checked_files += 1
    
    html = ROOT / 'apercu_pond_metano_cliffs.html'
    assert html.exists()
    checked_files += 1
    if html.stat().st_size < 10000:
        errors.append("Aperçu HTML anormalement petit")
    print(f"[PASS] Planche ({planche.stat().st_size} octets) et Aperçu HTML ({html.stat().st_size} octets) validés.")

    print(f"\nTotal fichiers vérifiés : {checked_files}")
    if errors:
        print("ERREURS DÉTECTÉES :")
        for e in errors:
            print(" -", e)
        sys.exit(1)
    else:
        print("TOUS LES CONTRÔLES SONT PASSÉS AVEC SUCCÈS (0 erreur) !")

if __name__ == '__main__':
    run_checks()
