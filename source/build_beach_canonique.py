"""Plage PMD Sky canonique — layouts en calques, eau animée native d'EoSO.

Toutes les cellules posées sont des copies exactes des tuiles natives 24 px de
ExplorersOfSkyOrigins (Minemaker0430), commit épinglé dans
source/beach_eoso/sources_eoso.json :
- D01P11A_layer1  : terrain (mer statique de secours, sable)
- beach_animation : eau CANNONIQUEMENT animée, 17 frames, FrameLength 16, pas +33
- D01P11A_layer2  : falaises, palmiers, herbe, rochers (calque avant)

Aucune rotation, recoloration, retournement ni pixel redessiné.
Usage : python source/build_beach_canonique.py
"""
from pathlib import Path
from PIL import Image
import json, struct, io, hashlib, base64

R = Path(__file__).resolve().parents[1]
N = R / 'source/beach_eoso/natifs'
O = R / 'sprites/beach_canonique_v1'
O.mkdir(parents=True, exist_ok=True)
L1, L2, BA = 'D01P11A_layer1', 'D01P11A_layer2', 'beach_animation'
COMMIT = 'bed944992c32e7e7927cc3480c72edb0b1782e26'
T = 24                      # TexSize 3 -> 24 px
GW, GH = 44, 30             # cellules par carte
FRAMES, STRIDE, FRAMELEN = 17, 33, 16


def load(name):
    raw = (N / f'{name}.tile').read_bytes()
    size, n = struct.unpack_from('<II', raw)
    assert size == T
    tiles = {}
    for i in range(n):
        x, y, off = struct.unpack_from('<IIQ', raw, 8 + 16 * i)
        length = struct.unpack_from('<q', raw, off)[0]
        im = Image.open(io.BytesIO(raw[off + 8:off + 8 + length])).convert('RGBA')
        assert im.size == (T, T)
        tiles[x, y] = im
    return tiles, raw


sheets, raws, pins = {}, {}, {}
for name in (L1, L2, BA):
    sheets[name], raws[name] = load(name)
    pins[name] = {'path': f'Content/Tile/{name}.tile',
                  'git_blob_sha1': hashlib.sha1(b'blob ' + str(len(raws[name])).encode() + b'\0' + raws[name]).hexdigest(),
                  'sha256': hashlib.sha256(raws[name]).hexdigest(),
                  'tiles': len(sheets[name])}
pins_file = {'repository': 'Minemaker0430/ExplorersOfSkyOrigins', 'commit': COMMIT, 'sources': pins}
(R / 'source/beach_eoso/sources_eoso.json').write_text(json.dumps(pins_file, indent=2))

SAND_ROWS = range(8, 12)      # sable ondulé natif de layer1 (rangées pures)
SAND_X0, SAND_X1 = 5, 30   # colonnes de sable pur (hors mer/brun)
SEA_BASE = 1                  # rangée turquoise de secours sous l'eau animée

# Blocs « détails » = rectangles exacts de tuiles de layer2 (copie intégrale).
BLOCKS = {
    'falaise_gauche': (L2, 0, 2, 9, 9),
    'falaise_droite': (L2, 24, 2, 32, 6),
    'palmiers_gauche': (L2, 1, 10, 6, 12),
    'palmiers_milieu': (L2, 13, 10, 18, 12),
    'falaise_basse': (L2, 19, 10, 24, 13),
    'herbe_bas': (L2, 0, 14, 32, 15),
    'rochers_petits': (L2, 13, 7, 14, 7),
    'buisson': (L2, 23, 7, 23, 7),
    'pente_sable': (L2, 30, 7, 32, 9),
}

LAYOUTS = [
    {'id': '01_cote_reference', 'name': 'La côte de la référence',
     'description': 'Mer au nord, grande plage, falaises aux deux bords, palmiers et herbe au sud : la composition de la planche TSR, en tuiles natives animées.',
     'shore': 8, 'blocks': [('falaise_gauche', 0, 5), ('falaise_droite', 35, 5),
                            ('palmiers_gauche', 6, 19), ('palmiers_milieu', 24, 21),
                            ('rochers_petits', 18, 17), ('buisson', 32, 19), ('herbe_bas', 0, 28), ('herbe_bas', 33, 28)]},
    {'id': '02_crique_palmiers', 'name': 'La crique aux palmiers',
     'description': 'Rivage plus haut, trois bosquets de palmiers sur le sable et falaises resserrées.',
     'shore': 6, 'blocks': [('falaise_gauche', 0, 3), ('falaise_droite', 35, 3),
                            ('palmiers_gauche', 4, 17), ('palmiers_milieu', 16, 19),
                            ('palmiers_milieu', 28, 17), ('herbe_bas', 0, 28), ('herbe_bas', 33, 28)]},
    {'id': '03_lagon_rocheux', 'name': 'Le lagon rocheux',
     'description': 'Grande mer piquetée d\u2019îlots rocheux natifs, plage basse ouverte.',
     'shore': 12, 'blocks': [('falaise_droite', 8, 1), ('falaise_droite', 26, 4),
                             ('rochers_petits', 20, 21), ('buisson', 34, 22),
                             ('palmiers_milieu', 10, 22), ('herbe_bas', 0, 28), ('herbe_bas', 33, 28)]},
    {'id': '04_plage_etroite', 'name': 'La plage étroite',
     'description': 'Couloir de sable encadré de hautes falaises empilées, comme un accès abrité.',
     'shore': 10, 'blocks': [('falaise_gauche', 0, 7), ('falaise_gauche', 0, 15),
                             ('falaise_droite', 35, 7), ('falaise_basse', 34, 14),
                             ('palmiers_gauche', 5, 23), ('herbe_bas', 0, 28), ('herbe_bas', 33, 28)]},
    {'id': '05_double_rivage', 'name': 'Le double rivage',
     'description': 'Mer au nord et chenal d\u2019eau animée traversant le sable, palmiers entre les deux.',
     'shore': 6, 'channel': 20, 'blocks': [('falaise_gauche', 0, 3), ('falaise_droite', 35, 3),
                                           ('palmiers_milieu', 18, 14), ('buisson', 12, 16),
                                           ('herbe_bas', 0, 28), ('herbe_bas', 33, 28)]},
    {'id': '06_anse_rocheuse', 'name': 'L\u2019anse rocheuse',
     'description': 'Un îlot rocheux face à la plage, falaises et palmiers en cadre.',
     'shore': 8, 'blocks': [('falaise_droite', 16, 1), ('falaise_gauche', 0, 5),
                            ('falaise_droite', 35, 5), ('palmiers_milieu', 20, 20),
                            ('rochers_petits', 12, 18), ('herbe_bas', 0, 28), ('herbe_bas', 33, 28)]},
]


def anim_tile(row, sx, f):
    return sheets[BA][sx + STRIDE * f, row]


def build(cfg):
    p = O / cfg['id']
    (p / 'calques').mkdir(parents=True, exist_ok=True)
    shore = cfg['shore']
    channel = cfg.get('channel')
    back = Image.new('RGBA', (GW * T, GH * T))
    front = Image.new('RGBA', (GW * T, GH * T))

    # Calque terrain : mer de secours au nord, sable natif sous le rivage.
    for y in range(GH):
        for x in range(GW):
            if y < shore:
                src = sheets[L1][x % 33, SEA_BASE]
            else:
                src = sheets[L1][SAND_X0 + (x % (SAND_X1 - SAND_X0 + 1)), SAND_ROWS[(y - shore) % len(SAND_ROWS)]]
            back.paste(src, (x * T, y * T))

    # Calque avant : blocs natifs de layer2.
    for name, bx, by in cfg['blocks']:
        sheet, x0, y0, x1, y1 = BLOCKS[name]
        for ty in range(y0, y1 + 1):
            for tx in range(x0, x1 + 1):
                t = sheets[sheet].get((tx, ty))
                dx, dy = bx + (tx - x0), by + (ty - y0)
                if t and 0 <= dx < GW and 0 <= dy < GH:
                    front.paste(t, (dx * T, dy * T), t)

    # Calque eau animée : mer profonde répétée puis les 7 bandes natives du rivage,
    # et éventuellement un chenal (bandes 3..5) entre deux sables.
    water_frames = []
    for f in range(FRAMES):
        w = Image.new('RGBA', (GW * T, GH * T))
        for y in range(GH):
            if y < shore:
                row = 0
            elif y < shore + 7:
                row = y - shore
            elif channel is not None and channel <= y < channel + 3:
                row = 3 + (y - channel)
            else:
                continue
            for x in range(GW):
                t = anim_tile(row, x % 33, f)
                w.paste(t, (x * T, y * T), t)
        water_frames.append(w)

    back.save(p / 'calques/back.png')
    front.save(p / 'calques/front.png')
    for f, w in enumerate(water_frames):
        w.save(p / 'calques' / f'eau_{f + 1:02d}.png')
    comp = back.copy()
    comp = Image.alpha_composite(comp, water_frames[0])
    comp = Image.alpha_composite(comp, front)
    comp.save(p / 'composition_frame01.png')
    return cfg | {'cellules': [GW, GH], 'tile_px': T, 'frames': FRAMES,
                  'frame_ticks': FRAMELEN, 'stride': STRIDE}


records = [build(c) for c in LAYOUTS]

# TSJ par feuille native (animations incluses pour beach_animation).
for name in (L1, L2, BA):
    tiles = sheets[name]
    w = (max(x for x, y in tiles) + 1) * T
    h = (max(y for x, y in tiles) + 1) * T
    img = Image.new('RGBA', (w, h))
    for (x, y), t in tiles.items():
        img.paste(t, (x * T, y * T))
    img.save(O / f'{name}.png')
    ts = {'type': 'tileset', 'version': '1.10', 'name': name, 'tilewidth': T, 'tileheight': T,
          'columns': w // T, 'tilecount': (w // T) * (h // T), 'margin': 0, 'spacing': 0,
          'image': f'{name}.png', 'imagewidth': w, 'imageheight': h, 'tiles': []}
    if name == BA:
        for row in range(7):
            for sx in range(33):
                ts['tiles'].append({'id': row * (w // T) + sx,
                                    'animation': [{'tileid': row * (w // T) + sx + STRIDE * f,
                                                   'duration': 267} for f in range(FRAMES)]})
    (O / f'{name}.tsj').write_text(json.dumps(ts))

# TMJ 3 calques par carte (firstgids cumulés, recherche par dictionnaire d'octets).
COLW = {name: (max(x for x, y in sheets[name]) + 1) for name in (L1, L2, BA)}
ROWH = {name: (max(y for x, y in sheets[name]) + 1) for name in (L1, L2, BA)}
N1, NBA, N2 = COLW[L1] * ROWH[L1], COLW[BA] * ROWH[BA], COLW[L2] * ROWH[L2]
FIRSTGID = {L1: 1, BA: 1 + N1, L2: 1 + N1 + NBA}
LOOK = {}
for name in (L1, L2, BA):
    d = {}
    for (tx, ty), t in sheets[name].items():
        d.setdefault(t.tobytes(), FIRSTGID[name] + ty * COLW[name] + tx)
    LOOK[name] = d

for rec in records:
    p = O / rec['id']
    tm_layers = []
    for lid, (png_name, sheet, lname) in enumerate([('back.png', L1, 'back'),
                                                    ('eau_01.png', BA, 'eau_animee'),
                                                    ('front.png', L2, 'front')]):
        im = Image.open(p / 'calques' / png_name).convert('RGBA')
        data = []
        for y in range(GH):
            for x in range(GW):
                key = im.crop((x * T, y * T, x * T + T, y * T + T)).tobytes()
                data.append(LOOK[sheet].get(key, 0))
        tm_layers.append({'id': lid + 1, 'name': lname, 'type': 'tilelayer', 'x': 0, 'y': 0,
                          'width': GW, 'height': GH, 'opacity': 1, 'visible': True, 'data': data})
    tm = {'type': 'map', 'version': '1.10', 'orientation': 'orthogonal', 'renderorder': 'right-down',
          'width': GW, 'height': GH, 'tilewidth': T, 'tileheight': T, 'infinite': False,
          'nextlayerid': 4, 'nextobjectid': 1, 'layers': tm_layers,
          'tilesets': [{'firstgid': 1, 'source': f'../{L1}.tsj'},
                       {'firstgid': 1 + N1, 'source': f'../{BA}.tsj'},
                       {'firstgid': 1 + N1 + NBA, 'source': f'../{L2}.tsj'}]}
    (p / 'carte.tmj').write_text(json.dumps(tm, separators=(',', ':')))

manifest = {'repository': pins_file['repository'], 'commit': COMMIT, 'sources': pins,
            'tile_px': T, 'frames': FRAMES, 'frame_ticks': FRAMELEN, 'stride': STRIDE,
            'maps': records,
            'rules': ['Every placed tile is an exact copy of a native EoSO 24px tile',
                      'Water is the native beach_animation 17-frame cycle, FrameLength 16',
                      'No rotation, flip, recolor, rescale or repainted pixel',
                      'New compositions inspired by the TSR beach reference; not official maps']}
(O / 'provenance.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2))

# Aperçu HTML.
def uri(p):
    return 'data:image/png;base64,' + base64.b64encode(p.read_bytes()).decode()

view = []
for rec in records:
    p = O / rec['id']
    view.append({'id': rec['id'], 'name': rec['name'], 'description': rec['description'],
                 'back': uri(p / 'calques/back.png'), 'front': uri(p / 'calques/front.png'),
                 'water': [uri(p / 'calques' / f'eau_{f + 1:02d}.png') for f in range(FRAMES)]})
(R / 'apercu_beach_canonique_v1.html').write_text(
    (R / 'source/beach_eoso/viewer.html').read_text().replace('__DATA__', json.dumps(view, ensure_ascii=False)))
print('Done :', len(records), 'cartes plage canoniques,', FRAMES, 'frames natives d\u2019eau.')
