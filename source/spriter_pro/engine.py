"""Spriter Pro — moteur de composition de cartes EXCLUSIVEMENT en tuiles canoniques.

Même contrat que `source/build_metano_pixel_perfect.py` :
- chaque cellule posée est la copie exacte d'une tuile native 8x8 (Base, Cliffs,
  Animation_Tileset, River_Animation_1..4) ;
- aucun ImageDraw sur les assets, aucune recoloration, rotation, retournement,
  agrandissement ni pixel redessiné ;
- les seules images réduites sont les planches de présentation nommées apercu.

Le moteur ajoute au pipeline d'origine :
- un contrôle de contraintes avant tout placement (audit `validate_layout`) ;
- un nouveau primitif `lake()` : bassin canonique isolé (pas de tracé de berge,
  uniquement des rangées natives du réservoir de Metano_Town_Base) ;
- la production de N cartes déclarées dans layouts.py, atlas/provenance/Tiled inclus.
"""
from pathlib import Path
from PIL import Image
import json, struct, io, math, hashlib

R = Path(__file__).resolve().parents[2]

# --- Sources natives épinglées -------------------------------------------------
BASE = 'Metano_Town_Base'
CLIFF = 'Metano_Town_Cliffs'
ANIM = 'Metano_Town_Animation_Tileset'
RIVERS = [f'Metano_Town_River_Animation_{i}' for i in range(1, 5)]
PATHS = {BASE: R / 'source/falaises_metano/natifs' / f'{BASE}.tile',
         CLIFF: R / 'source/falaises_metano/natifs' / f'{CLIFF}.tile'}
PATHS.update({n: R / 'source/eau_metano/natifs' / f'{n}.tile' for n in [ANIM] + RIVERS})

W, H = 2048, 1536          # rendu natif d'une carte
GW, GH = 256, 192          # cellules de 8 px
GRID = 8
COLS = 64                  # colonnes de l'atlas

# Bandes source autorisées (comme le pack pixel-perfect d'origine).
GRASS_RECT = (0, 80, 16, 16)                 # Base x=0..15, y=80..95
CLIFF_COLUMNS = set(range(57, 93)) | set(range(114, 122)) | set(range(162, 189))
LAKE_COLS = range(103, 145)                  # réservoir canonique (42 tuiles)
NECK_COLS = range(123, 134)                  # chenal canonique (11 tuiles)
LAKE_ROWS = range(0, 57)                     # rangées source verticales du réservoir
NECK_ROWS = (50, 51)                         # rangées source du chenal


def load_sources():
    """Lit les .tile natifs ; renvoie (tuiles par feuille, infos de provenance)."""
    source, info = {}, {}
    for name, path in PATHS.items():
        raw = path.read_bytes()
        size, n = struct.unpack_from('<II', raw)
        assert size == 8, f'{name}: taille de tuile attendue 8 px'
        tiles = {}
        for i in range(n):
            x, y, off = struct.unpack_from('<IIQ', raw, 8 + 16 * i)
            length = struct.unpack_from('<q', raw, off)[0]
            im = Image.open(io.BytesIO(raw[off + 8:off + 8 + length])).convert('RGBA')
            assert im.size == (8, 8)
            tiles[x, y] = im
        source[name] = tiles
        info[name] = {'path': str(path.relative_to(R)),
                      'git_blob_sha1': hashlib.sha1(b'blob ' + str(len(raw)).encode() + b'\0' + raw).hexdigest(),
                      'sha256': hashlib.sha256(raw).hexdigest(),
                      'tiles': n}
    return source, info


class Studio:
    """Atelier : atlas canonique en croissance + primitives de pose."""

    def __init__(self, source, source_info):
        self.source = source
        self.source_info = source_info
        self.tiles = []        # images RGBA prémultipliées, copiées des sources
        self.origins = []      # provenance par entrée d'atlas
        self.lookup = {}
        self.proxies = {}
        self.animations = {}   # gid -> tuple de gids (4 frames)

    # -- atlas ----------------------------------------------------------------
    def tile_id(self, sheet, x, y):
        key = (sheet, x, y)
        if key not in self.lookup:
            im = self.source[sheet].get((x, y))
            if im is None:
                self.lookup[key] = 0
            else:
                self.lookup[key] = len(self.tiles) + 1
                self.tiles.append(im.copy())
                self.origins.append({'sheet': sheet, 'texloc': [x, y], 'role': 'native'})
        return self.lookup[key]

    def animated(self, refs):
        frames = tuple(self.tile_id(*ref) for ref in refs)
        if len(set(frames)) == 1:
            return frames[0]
        assert all(frames), 'Toute phase d\'eau posée doit exister dans les sources'
        if frames not in self.proxies:
            self.proxies[frames] = len(self.tiles) + 1
            self.tiles.append(self.tiles[frames[0] - 1].copy())
            origin = dict(self.origins[frames[0] - 1])
            origin['role'] = 'animation_first_frame'
            self.origins.append(origin)
            self.animations[self.proxies[frames]] = frames
        return self.proxies[frames]

    def put(self, layer, x, y, gid):
        if gid and 0 <= x < GW and 0 <= y < GH:
            layer[y * GW + x] = gid

    # -- primitives (copie conforme du pipeline pixel-perfect) ----------------
    def ground(self):
        return [self.tile_id(BASE, x % 16, 80 + y % 16) for y in range(GH) for x in range(GW)]

    def cliff_column(self, layer, dx, sx, offset, extension, minsy):
        rows = [y for x, y in self.source[CLIFF] if x == sx and y >= minsy and self.source[CLIFF][x, y].getbbox()]
        if not rows:
            return
        last = max(rows)
        insert = last - 4
        body = list(range(insert - 4, insert))
        assert all((sx, y) in self.source[CLIFF] for y in body)
        for sy in range(minsy, insert):
            self.put(layer, dx, sy + offset, self.tile_id(CLIFF, sx, sy))
        for j in range(extension):
            self.put(layer, dx, insert + offset + j, self.tile_id(CLIFF, sx, body[j % 4]))
        for sy in range(insert, last + 1):
            self.put(layer, dx, sy + offset + extension, self.tile_id(CLIFF, sx, sy))

    def ribbon(self, layer, start_x, offset_y, extra_px, flats):
        # Colonnes natives sans escaliers, grotte ni colonnes d'eau.
        cols = list(range(57, 93))
        for segment in range(flats):
            cols.extend(range(85, 93) if segment in [5, 9, 16, 21] else range(114, 122))
        cols.extend(range(162, 189))
        while start_x // 8 + len(cols) < GW:
            cols.append(188)
        for i, sx in enumerate(cols):
            dx = start_x // 8 + i
            if 0 <= dx < GW:
                minsy = 56 if 85 <= sx <= 92 and i >= 36 else 26 if sx < 93 else 38 if sx >= 162 else 54
                self.cliff_column(layer, dx, sx, offset_y // 8, extra_px // 8, minsy)

    def river_row(self, banks, water, dest_y, source_y, dx, lake=False):
        if not 0 <= dest_y < GH:
            return
        lo, hi = (103, 144) if lake else (123, 133)
        for sx in range(lo, hi + 1):
            tx = sx + dx
            self.put(banks, tx, dest_y, self.tile_id(BASE, sx, source_y))
            refs = [(sheet, sx, source_y) for sheet in RIVERS]
            ids = [self.tile_id(*ref) for ref in refs]
            if any(ids):
                # Une tuile d'eau absente des sources est transparente, jamais recolorée.
                if all(ids):
                    self.put(water, tx, dest_y, self.animated(refs))
                else:
                    assert len(set(ids)) == 1, 'Bordure animée source inattendue'

    def waterfall(self, water, cx, top, end):
        rows = (end - top) // 8
        assert rows >= 17, 'Une chute canonique mesure au moins 17 rangées'
        for y in range(rows):
            sy = y if y < 6 else (13 + y - (rows - 4) if y >= rows - 4 else 8 + (y - 6) % 4)
            for x in range(8):
                refs = [(ANIM, 1 + 9 * f + x, 62 + sy) for f in range(4)]
                self.put(water, cx // 8 - 4 + x, top // 8 + y, self.animated(refs))

    def lake(self, banks, water, cx, top_px, rows):
        """Bassin isolé : rangées natives consécutives du réservoir, sans berge tracée."""
        assert 1 <= rows <= len(LAKE_ROWS), 'Un bassin utilise au plus 57 rangées natives'
        dx = cx // 8 - 128
        for sy in range(rows):
            self.river_row(banks, water, top_px // 8 + sy, sy, dx, True)

    def stream(self, banks, water, cfg, ribbons):
        """Torrent nord -> sud : réservoir, chutes à travers les parois, chenaux."""
        cx = cfg['x']
        dx = cx // 8 - 128
        walls = [(456 + ribbons[j]['offset'], 544 + ribbons[j]['offset'] + ribbons[j]['extra']) for j in cfg['walls']]
        assert walls == sorted(walls), 'Les parois doivent être triées du nord au sud'
        for j in cfg['walls']:
            rr = ribbons[j]
            assert rr['x'] + 288 <= cx - 32 and cx + 32 <= rr['x'] + 288 + rr['flats'] * 64, \
                f'La chute en x={cx} doit tomber sur un front plat de la paroi {j}'
        shift = (walls[0][0] - 456) // 8
        assert shift >= 0
        for y in range(shift):
            self.river_row(banks, water, y, 0, dx, True)
        for sy in range(57):
            self.river_row(banks, water, shift + sy, sy, dx, True)
        intervals = []
        for i, (top, end) in enumerate(walls):
            next_top = walls[i + 1][0] if i + 1 < len(walls) else H
            # Une tuile au-dessus du pied : les pixels transparents de fin de chute laissent voir l'eau.
            for y in range(end // 8 - 1, next_top // 8):
                self.river_row(banks, water, y, 50 + (y - (end // 8 - 1)) % 2, dx)
            self.waterfall(water, cx, top, end)
            intervals.append({'center_x_px': cx, 'top_px': top, 'bottom_px': end})
        return intervals

    # -- rendu ------------------------------------------------------------------
    _straight_cache = {}

    def straight_tile(self, gid):
        if gid not in self._straight_cache:
            im = self.tiles[gid - 1].copy()
            im.putdata([(round(r * 255 / a), round(g * 255 / a), round(b * 255 / a), a) if 0 < a < 255 else (r, g, b, a)
                        for r, g, b, a in im.getdata()])
            self._straight_cache[gid] = im
        return self._straight_cache[gid]

    def render(self, layer, frame=0):
        out = Image.new('RGBA', (W, H))
        for i, gid in enumerate(layer):
            if gid:
                actual = self.animations[gid][frame] if gid in self.animations else gid
                out.paste(self.straight_tile(actual), ((i % GW) * 8, (i // GW) * 8))
        return out


# --- Contraintes (aucun pixel posé : audit déclaratif) -------------------------
def validate_layout(cfg):
    """Vérifie une déclaration AVANT toute pose. Renvoie la liste des problèmes."""
    problems = []
    ribbons = cfg['ribbons']
    for i, rr in enumerate(ribbons):
        top = 456 + rr['offset']
        bottom = 544 + rr['offset'] + rr['extra']
        if top < 0 or bottom > H:
            problems.append(f'paroi {i}: hors carte (top={top}, bottom={bottom})')
        if rr['offset'] % 8 or rr['extra'] % 8 or rr['x'] % 8:
            problems.append(f'paroi {i}: valeurs non alignées sur la grille 8 px')
        if rr['flats'] < 1:
            problems.append(f'paroi {i}: flats < 1')
    for s in cfg['streams']:
        cx = s['x']
        if not (0 <= cx <= W):
            problems.append(f'torrent x={cx}: hors carte')
        # Un torrent traverse toute la carte du nord au sud : chaque paroi doit
        # être percée par une chute, sinon la bande d'eau flotterait sur la face.
        if sorted(s['walls']) != list(range(len(ribbons))):
            problems.append(f'torrent x={cx}: doit traverser toutes les parois {sorted(s["walls"])}')
        walls = [(456 + ribbons[j]['offset'], 544 + ribbons[j]['offset'] + ribbons[j]['extra']) for j in s['walls']]
        if walls != sorted(walls):
            problems.append(f'torrent x={cx}: parois non triées nord -> sud')
        if walls and walls[0][0] < 456:
            problems.append(f'torrent x={cx}: première paroi au-dessus de y=456')
        for j in s['walls']:
            rr = ribbons[j]
            if not (rr['x'] + 288 <= cx - 32 and cx + 32 <= rr['x'] + 288 + rr['flats'] * 64):
                problems.append(f'torrent x={cx}: la chute ne tombe pas sur un front plat (paroi {j})')
        for top, end in walls:
            if (end - top) // 8 < 17:
                problems.append(f'torrent x={cx}: chute trop courte ({(end - top) // 8} rangées < 17)')
    for lk in cfg.get('lakes', []):
        if lk['rows'] < 1 or lk['rows'] > 57:
            problems.append(f'bassin x={lk["x"]}: {lk["rows"]} rangées (1..57)')
        if lk['top'] % 8 or lk['x'] % 8:
            problems.append(f'bassin x={lk["x"]}: non aligné sur 8 px')
        if lk['top'] + lk['rows'] * 8 > H:
            problems.append(f'bassin x={lk["x"]}: dépasse le bas de carte')
        band = (lk['x'] - 200, lk['x'] + 136)  # emprise px de la bande réservoir (42 tuiles)
        for s in cfg['streams']:
            sx0, sx1 = s['x'] - 200, s['x'] + 136
            if band[0] < sx1 and sx0 < band[1]:
                problems.append(f'bassin x={lk["x"]}: recouvre la bande du torrent x={s["x"]}')
        for other in cfg.get('lakes', []):
            if other is not lk:
                ox0, ox1 = other['x'] - 200, other['x'] + 136
                y_overlap = not (lk['top'] + lk['rows'] * 8 <= other['top']
                                 or other['top'] + other['rows'] * 8 <= lk['top'])
                if band[0] < ox1 and ox0 < band[1] and y_overlap:
                    problems.append(f'bassin x={lk["x"]}: recouvre le bassin x={other["x"]}')
        # Un bassin isolé doit rester entièrement dans une plaine visible :
        # sa hauteur ne coupe aucune face de paroi (couronne comprise).
        for i, rr in enumerate(ribbons):
            face_top = 456 + rr['offset']
            face_bottom = 544 + rr['offset'] + rr['extra']
            if lk['top'] < face_bottom and lk['top'] + lk['rows'] * 8 > face_top:
                problems.append(f'bassin x={lk["x"]}: coupe la face de la paroi {i}')
    return problems


def compile_layout(studio, cfg):
    """Pose une carte déclarée. Renvoie (calques, enregistrement)."""
    problems = validate_layout(cfg)
    assert not problems, f'{cfg["id"]}: ' + ' ; '.join(problems)
    g = studio.ground()
    cliffs = [0] * (GW * GH)
    banks = [0] * (GW * GH)
    water = [0] * (GW * GH)
    for rr in cfg['ribbons']:
        studio.ribbon(cliffs, rr['x'], rr['offset'], rr['extra'], rr['flats'])
    intervals = []
    for s in cfg['streams']:
        intervals += studio.stream(banks, water, s, cfg['ribbons'])
    for lk in cfg.get('lakes', []):
        studio.lake(banks, water, lk['x'], lk['top'], lk['rows'])
    record = {**cfg, 'dimensions_px': [W, H], 'cellules': [GW, GH], 'grid_px': GRID,
              'waterfalls': intervals,
              'dry_layers': ['herbe', 'falaises_bordures'],
              'wet_layers': ['herbe', 'falaises_bordures', 'berges_eau', 'eau_animee']}
    return [g, cliffs, banks, water], record


# --- Écriture atlas / .tile / TSJ / TMJ / provenance ---------------------------
BLANK = Image.new('RGBA', (8, 8))


def write_atlas(studio, out_dir, sheet):
    rows = math.ceil(len(studio.tiles) / COLS)
    atlas_raw = Image.new('RGBA', (COLS * 8, rows * 8))
    atlas_png = atlas_raw.copy()
    for i, t in enumerate(studio.tiles):
        atlas_raw.paste(t, ((i % COLS) * 8, (i // COLS) * 8))
        atlas_png.paste(studio.straight_tile(i + 1), ((i % COLS) * 8, (i // COLS) * 8))
    atlas_png.save(out_dir / (sheet + '.png'))
    count = COLS * rows
    payload = bytearray()
    offsets = {}
    entries = []
    for i in range(count):
        t = studio.tiles[i] if i < len(studio.tiles) else BLANK
        key = t.tobytes()
        if key not in offsets:
            offsets[key] = 8 + 16 * count + len(payload)
            b = io.BytesIO()
            t.save(b, format='PNG')
            raw = b.getvalue()
            payload.extend(struct.pack('<q', len(raw)) + raw)
        entries.append(struct.pack('<IIQ', i % COLS, i // COLS, offsets[key]))
    (out_dir / (sheet + '.tile')).write_bytes(struct.pack('<II', 8, count) + b''.join(entries) + payload)
    ts = {'type': 'tileset', 'version': '1.10', 'name': sheet, 'tilewidth': 8, 'tileheight': 8,
          'columns': COLS, 'tilecount': count, 'margin': 0, 'spacing': 0,
          'image': sheet + '.png', 'imagewidth': atlas_png.width, 'imageheight': atlas_png.height,
          'tiles': [{'id': gid - 1, 'animation': [{'tileid': f - 1, 'duration': 167} for f in frames]}
                    for gid, frames in studio.animations.items()]}
    (out_dir / (sheet + '.tsj')).write_text(json.dumps(ts, indent=2))
    return count


def write_tiled(out_dir, record, layers, sheet):
    for wet in (False, True):
        names = record['wet_layers'] if wet else record['dry_layers']
        ls = [{'id': i + 1, 'name': names[i], 'type': 'tilelayer', 'x': 0, 'y': 0,
               'width': GW, 'height': GH, 'opacity': 1, 'visible': True, 'data': layers[i]}
              for i in range(len(names))]
        tm = {'type': 'map', 'version': '1.10', 'orientation': 'orthogonal', 'renderorder': 'right-down',
              'width': GW, 'height': GH, 'tilewidth': 8, 'tileheight': 8, 'infinite': False,
              'nextlayerid': len(ls) + 1, 'nextobjectid': 1, 'layers': ls,
              'tilesets': [{'firstgid': 1, 'source': '../' + sheet + '.tsj'}]}
        (out_dir / ('anime.tmj' if wet else 'sec.tmj')).write_text(json.dumps(tm, separators=(',', ':')))


def write_provenance(out_dir, studio, source_info, records, sheet, count, rules):
    manifest = {'reference': 'Palikadude/Halcyon',
                'commit': 'da6c2130d641507447e6386a5e47a296e8cb4c71',
                'sources': source_info,
                'source_tile_px': 8,
                'atlas': {'name': sheet, 'columns': COLS, 'tilecount': count,
                          'used_entries': len(studio.tiles),
                          'entries': [{'tileid': i, **v} for i, v in enumerate(studio.origins)]},
                'maps': records,
                'native_animations': [
                    {'tileid': gid - 1,
                     'Frames': [{'Sheet': sheet, 'TexLoc': {'X': (v - 1) % COLS, 'Y': (v - 1) // COLS}} for v in frames],
                     'FrameLength': 10}
                    for gid, frames in studio.animations.items()],
                'rules': rules}
    (out_dir / 'provenance.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2))


RULES = [
    'Every placed tile is copied from a canonical source tile',
    'No generated artwork, painted shores, hue filters, rotations or resampling',
    'Dry ground is only Base cells x=0..15, y=80..95',
    'Dry cliffs use only canonical columns 57..92, 114..121, 162..188, excluding stairs/cave/water',
    'Lakes and reservoirs use only Base columns 103..144 (lake) and 123..133 (neck), rows 0..56 and 50..51',
    'Isolated lakes are whole native reservoir rows, never painted banks',
    'Tall faces and falls repeat whole native tile rows, never stretch',
    'New composition, not an official Metano map; collisions and transitions not provided',
]
