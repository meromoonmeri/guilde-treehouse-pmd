#!/usr/bin/env python3
"""Paquet natif PMDO 0.8.12.0 pour sud->nord V4 : 4 .rsground + banques .tile.

Tuiles = cellules 8 px exactes des calques PNG (pixels natifs des references,
translation seule). Dedup par contenu dans une banque par carte et par mode.
Collisions : premiere passe automatique a affiner dans l'editeur.
Aucun test dans le moteur PMDO (absent du bac a sable).
"""
import importlib.util
import json
import sys
from pathlib import Path

import numpy as np
from PIL import Image

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
_spec = importlib.util.spec_from_file_location('pmdo_cote_build', ROOT / 'source/pmdo_cote/build.py')
_pmdo = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_pmdo)
TileBank, auto = _pmdo.TileBank, _pmdo.auto

OUT = ROOT / 'exports/zones_south_north_v4'
NATIF = OUT / 'paquet_natif'
T = 8

MAPS = {
    'arid_dungeon_entrance': dict(label='Entree aride', size=(408, 560),
                                  trunk_blocks=[(4, 44, 6, 49), (45, 53, 45, 57)],
                                  mouth=[190, 87, 32, 16]),
    'violet_underground_road': dict(label='Couloir violet', size=(504, 488),
                                    trunk_blocks=[], mouth=[132, 136, 32, 16]),
}


def build_map(map_id, mode):
    cfg = MAPS[map_id]
    W, H = cfg['size']
    gw, gh = W // T, H // T
    man = json.loads((OUT / 'manifest.json').read_text())
    info = next(m for m in man['maps'] if m['id'] == map_id)
    bank = TileBank(f'SN4_{map_id}_{mode}'.upper())
    layers_json = []
    blocked = set()
    for li, l in enumerate(info['layers']):
        f = l['file_jour'] if mode == 'jour' else l['file_nuit']
        img = Image.open(OUT / map_id / f).convert('RGBA')
        tiles = [[None] * gh for _ in range(gw)]
        for x in range(gw):
            for y in range(gh):
                tile = img.crop((x * T, y * T, x * T + T, y * T + T))
                ref = bank.add(tile, x, y)
                tiles[x][y] = auto([ref], 60) if ref else auto()
                if ref and li > 0 and (np.array(tile)[:, :, 3] > 0).mean() >= 0.5:
                    blocked.add((x, y))
        layers_json.append({'Name': f"{li:02d} {l['id']}", 'Layer': 0,
                            'Visible': True, 'Tiles': tiles})
    for (x0, y0, x1, y1) in cfg['trunk_blocks']:
        for x in range(x0, x1 + 1):
            for y in range(y0, y1 + 1):
                blocked.add((x, y))
    obs = [[{'Bounds': {'X': x * T, 'Y': y * T, 'Width': T, 'Height': T},
             'Tags': 1 if (x, y) in blocked else 0}
            for y in range(gh)] for x in range(gw)]
    entry = None
    for y in range(gh - 4, gh // 2, -1):
        for dx in range(gw // 2):
            for x in (gw // 2 + dx, gw // 2 - dx):
                if all(obs[x + i][y + j]['Tags'] == 0
                       for i in (-1, 0, 1) for j in (-1, 0, 1)):
                    entry = (x, y)
                    break
            if entry:
                break
        if entry:
            break
    mx, my, mw, mh = cfg['mouth']
    markers = [
        {'EntName': 'entrance', 'Direction': 0, 'EntEnabled': True, 'triggerType': 0,
         'Collider': {'X': entry[0] * T - 8, 'Y': entry[1] * T - 8, 'Width': 16, 'Height': 16}},
        {'EntName': 'donjon_seuil', 'Direction': 0, 'EntEnabled': True, 'triggerType': 0,
         'Collider': {'X': mx, 'Y': my, 'Width': mw, 'Height': mh}},
    ]
    asset = f'sn4_{map_id}_{mode}'
    obj = {'$type': 'RogueEssence.Ground.GroundMap, RogueEssence', 'TexSize': 1,
           'Name': {'DefaultText': f"{cfg['label']} ({mode}) - V4", 'LocalTexts': {}},
           'Released': False,
           'Comment': ('Sud->nord V4 : tuiles 8 px natives des references PMD Sky '
                       '(translation seule). Collisions : premiere passe auto a affiner. '
                       'Aucune destination de donjon liee.'),
           'obstacles': obs,
           'rand': {'$type': 'RogueElements.ReRandom, RogueElements', 'FirstSeed': 0,
                    's': [16294208416658607535, 7960286522194355700, 487617019471545679,
                          17909611376780542444]},
           'Status': {},
           'Background': {'$type': 'RogueEssence.Dungeon.MapBG, RogueEssence',
                          'MapLoc': {'X': 0, 'Y': 0},
                          'BGAnim': {'AnimIndex': '', 'FrameTime': 1, 'StartFrame': -1,
                                     'EndFrame': -1, 'AnimDir': -1, 'Alpha': 255, 'AnimFlip': 0},
                          'BGMovement': {'X': 0, 'Y': 0}, 'Parallax': '0, 0',
                          'RepeatX': False, 'RepeatY': False},
           'BlankBG': auto(), 'Layers': layers_json, 'AssetName': asset, 'Music': '',
           'EdgeView': 0, 'NoSwitching': False, 'ViewCenter': None,
           'ViewOffset': {'X': 0, 'Y': 0}, 'ActiveChar': None,
           'Decorations': [{'Name': 'Vos decorations', 'Layer': 0, 'Visible': True, 'Anims': []}],
           'Entities': [{'Name': 'Vos objets et personnages', 'Visible': True, 'MapChars': [],
                         'GroundObjects': [], 'Spawners': [], 'Markers': markers}]}
    (NATIF / 'Data/Ground').mkdir(parents=True, exist_ok=True)
    (NATIF / f'Data/Ground/{asset}.rsground').write_text(
        json.dumps({'Version': '0.8.12.0', 'Object': obj}, ensure_ascii=False, separators=(',', ':')))
    bank.write(NATIF / f'Content/Tile/{bank.name}.tile')
    return {'asset': asset, 'file': f'Data/Ground/{asset}.rsground', 'grid': [gw, gh],
            'size_px': [W, H], 'entry_tile': list(entry), 'sheets': [bank.name],
            'custom_tiles': len(bank.data),
            'blocked_tiles': sum(t['Tags'] == 1 for col in obs for t in col)}


INSTALLER = '''#!/usr/bin/env python3
"""Copie le paquet natif sud->nord V4 dans un dossier MODS de PMDO.
Usage : python INSTALLER.py "C:/chemin/vers/PMDO/MODS/SouthNorthV4"  (le dossier est cree)
Copie Data/Ground/*.rsground et Content/Tile/*.tile. Aucun fichier du jeu n'est ecrase.
Ce paquet n'a pas ete teste dans le moteur : ouvrir d'abord dans PMDO Dev."""
import shutil
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
if len(sys.argv) != 2:
    print(__doc__)
    sys.exit(1)
dest = Path(sys.argv[1])
copied = 0
for sub in ('Data/Ground', 'Content/Tile'):
    for f in sorted((HERE / sub).glob('*')):
        target = dest / sub / f.name
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(f, target)
        copied += 1
        print('copie', target)
print(f'{copied} fichiers copies dans {dest}')
'''


def main():
    manifest = {'native_schema_version': '0.8.12.0', 'tex_size': 1, 'tile_px': T,
                'runtime_tested': False,
                'collision_note': ('Premiere passe automatique : parois/bouches opaques >= 50 %, '
                                   'pieds de troncs arides. A affiner dans l editeur.'),
                'warp_note': ('Marqueur donjon_seuil fourni sans destination : raccorder '
                              'dans l editeur.'),
                'maps': []}
    for map_id in MAPS:
        for mode in ('jour', 'nuit'):
            info = build_map(map_id, mode)
            manifest['maps'].append(info)
            print(info['asset'], info['grid'], 'tuiles banque:', info['custom_tiles'],
                  'bloquees:', info['blocked_tiles'], 'entree:', info['entry_tile'])
    (NATIF / 'manifest.json').write_text(json.dumps(manifest, indent=1, ensure_ascii=False))
    (NATIF / 'INSTALLER.py').write_text(INSTALLER)


if __name__ == '__main__':
    main()
