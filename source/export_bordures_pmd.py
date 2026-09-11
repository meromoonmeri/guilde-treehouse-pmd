"""Exporte les vingt motifs redessinés en PNG/TSJ et les charge dans Tiled."""
from pathlib import Path
from PIL import Image
import json
from exterior_animation import save_png
from rebuild_falaise import grade, SPECS

BANK = Path(__file__).resolve().parent / 'bordures_pmd'


def attach_tileset(root, mode, files):
    definitions = json.loads((BANK / 'definitions.json').read_text(encoding='utf-8'))
    _, _, mul, add, saturation = SPECS[mode]
    atlas = grade(Image.open(BANK / 'bordures_redessinees.png').convert('RGBA'), mul, add, saturation)
    png_path = f'tilesets/bordures_pmd_{mode}.png'
    tsj_path = f'tiled/bordures_pmd_{mode}.tsj'
    catalogue_path = f'tiled/catalogue_bordures_pmd_{mode}.tmj'
    save_png(atlas, root / png_path)
    tiles = []
    for item in definitions['motifs']:
        tiles.append({'id': item['id'], 'class': item['famille'], 'properties': [
            {'name': 'nom', 'type': 'string', 'value': item['nom']},
            {'name': 'motif', 'type': 'string', 'value': item['id_motif']},
            {'name': 'orientation', 'type': 'string', 'value': item['orientation']},
        ]})
    data = {'type': 'tileset', 'version': '1.10', 'tiledversion': '1.11.0',
            'name': 'Bordures PMD Sky — redessin '+mode, 'tilewidth': 24, 'tileheight': 24,
            'tilecount': 20, 'columns': 5, 'margin': 0, 'spacing': 0,
            'image': '../'+png_path, 'imagewidth': atlas.width, 'imageheight': atlas.height,
            'objectalignment': 'bottomleft', 'tiles': tiles}
    (root / tsj_path).write_text(json.dumps(data, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    # L'atlas est disponible dans la palette de la carte existante. Son rendu
    # organique est adapté localement dans le PNG de falaise, pas forcé en blocs.
    map_path = root / files['tiled']
    scene = json.loads(map_path.read_text(encoding='utf-8'))
    firstgid = max(t['firstgid']+t['tilecount'] for t in scene['tilesets'])
    scene['tilesets'].append({'firstgid': firstgid, 'source': Path(tsj_path).name})
    map_path.write_text(json.dumps(scene, ensure_ascii=False, separators=(',', ':')), encoding='utf-8')
    catalogue = {'type': 'map', 'version': '1.10', 'tiledversion': '1.11.0', 'orientation': 'orthogonal',
                 'renderorder': 'right-down', 'tilewidth': 24, 'tileheight': 24, 'width': 5, 'height': 4,
                 'infinite': False, 'nextlayerid': 2, 'nextobjectid': 1,
                 'tilesets': [{'firstgid': 1, 'source': Path(tsj_path).name}],
                 'layers': [{'id': 1, 'name': 'Vingt motifs orientés', 'type': 'tilelayer',
                             'visible': True, 'opacity': 1, 'x': 0, 'y': 0,
                             'width': 5, 'height': 4, 'data': list(range(1, 21))}]}
    (root / catalogue_path).write_text(json.dumps(catalogue, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    files['tileset_bordures'] = {'png': png_path, 'tiled': tsj_path, 'catalogue': catalogue_path,
                               'tile_size': 24, 'count': 20}
