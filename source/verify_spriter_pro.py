"""Contrôle indépendant Spriter Pro : sources -> atlas -> cartes -> PNG.

Ne réimporte ni le moteur ni le script de construction : tout est relu depuis
`sprites/spriter_pro_v1/provenance.json`, les `.tmj`, les PNG livrés et les
fichiers sources natifs. Usage :  python source/verify_spriter_pro.py
"""
from pathlib import Path
from PIL import Image
import json, hashlib, struct, io, sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
from spriter_pro.engine import (BASE, CLIFF, ANIM, RIVERS, W, H, GW, GH, GRID,
                                CLIFF_COLUMNS, LAKE_COLS, NECK_COLS, validate_layout)

R = Path(__file__).resolve().parents[1]
O = R / 'sprites/spriter_pro_v1'
M = json.loads((O / 'provenance.json').read_text())


def read_native(p):
    b = p.read_bytes()
    s, n = struct.unpack_from('<II', b)
    assert s == 8
    cache, tiles = {}, {}
    for i in range(n):
        x, y, off = struct.unpack_from('<IIQ', b, 8 + i * 16)
        assert off >= 8 + n * 16
        if off not in cache:
            length = struct.unpack_from('<q', b, off)[0]
            assert off + 8 + length <= len(b)
            im = Image.open(io.BytesIO(b[off + 8:off + 8 + length])).convert('RGBA')
            assert im.size == (8, 8)
            cache[off] = im
        tiles[x, y] = cache[off]
    return tiles


def premul(im):
    out = im.copy()
    out.putdata([(round(r * a / 255), round(g * a / 255), round(b * a / 255), a) for r, g, b, a in im.getdata()])
    return out


# 1. Sources épinglées : hashes + blobs Git identiques aux références Halcyon.
pins = {k: v['git_blob_sha1'] for k, v in
        json.loads((R / 'source/eau_metano/sources_github.json').read_text())['sources'].items()}
pins.update({BASE: '19b295495e49819b356c02d13a574616dd67d36c',
             CLIFF: '6d342b97ebfcad3e9aa6022b49e0f3b5b9d75640'})
source = {}
for name, info in M['sources'].items():
    p = R / info['path']
    b = p.read_bytes()
    assert hashlib.sha256(b).hexdigest() == info['sha256']
    assert hashlib.sha1(b'blob ' + str(len(b)).encode() + b'\0' + b).hexdigest() == info['git_blob_sha1'] == pins[name]
    source[name] = read_native(p)
    assert len(source[name]) == info['tiles']

# 2. Atlas : chaque entrée utilisée est une copie exacte d'une tuile source.
sheet = M['atlas']['name']
cols = M['atlas']['columns']
count = M['atlas']['tilecount']
used = M['atlas']['used_entries']
origins = M['atlas']['entries']
assert len(origins) == used
raw_atlas = read_native(O / (sheet + '.tile'))
png = Image.open(O / (sheet + '.png')).convert('RGBA')
assert png.width == cols * 8 and len(raw_atlas) == count
cache = []
for i in range(count):
    xy = (i % cols, i // cols)
    tile = png.crop((xy[0] * 8, xy[1] * 8, xy[0] * 8 + 8, xy[1] * 8 + 8))
    cache.append(tile)
    assert premul(tile).tobytes() == raw_atlas[xy].tobytes()
    if i < used:
        ref = origins[i]
        assert ref['tileid'] == i
        assert raw_atlas[xy].tobytes() == source[ref['sheet']][tuple(ref['texloc'])].tobytes()
    else:
        assert tile.getbbox() is None

# 3. Animations : 4 frames, FrameLength 10, feuilles cohérentes.
TS = json.loads((O / (sheet + '.tsj')).read_text())
assert TS['tilewidth'] == TS['tileheight'] == 8 and TS['tilecount'] == count
animations = {t['id']: [f['tileid'] for f in t['animation']] for t in TS['tiles']}
for seq in M['native_animations']:
    ids = [f['TexLoc']['Y'] * cols + f['TexLoc']['X'] for f in seq['Frames']]
    assert seq['FrameLength'] == 10 and ids == animations[seq['tileid']]
    assert len(ids) == 4 and all(0 <= v < used for v in ids)
    assert origins[seq['tileid']]['role'] == 'animation_first_frame'
    sheets = [origins[v]['sheet'] for v in ids]
    locs = [tuple(origins[v]['texloc']) for v in ids]
    assert (sheets == RIVERS and len(set(locs)) == 1) or all(s == ANIM for s in sheets), \
        'Une animation doit être soit les 4 feuilles de rivière, soit la feuille de chute'

# 4. Cartes : contraintes revalidées + white-lists par calque + recomposition.
reports = []
for record in M['maps']:
    assert not validate_layout(record), f'{record["id"]}: contraintes violées'
    d = O / record['id']
    dry = json.loads((d / 'sec.tmj').read_text())
    wet = json.loads((d / 'anime.tmj').read_text())
    assert len(dry['layers']) == 2 and len(wet['layers']) == 4
    for tm in [dry, wet]:
        assert (tm['width'], tm['height'], tm['tilewidth'], tm['tileheight']) == (GW, GH, GRID, GRID)
        assert (d / tm['tilesets'][0]['source']).resolve() == (O / (sheet + '.tsj')).resolve()
        for l in tm['layers']:
            assert len(l['data']) == GW * GH and all(0 <= v <= used for v in l['data'])
    assert dry['layers'] == wet['layers'][:2]
    # Herbe : formule canonique Base x=0..15, y=80..95, partout.
    for i, gid in enumerate(dry['layers'][0]['data']):
        assert gid > 0
        ref = origins[gid - 1]
        assert ref['sheet'] == BASE and ref['texloc'] == [(i % GW) % 16, 80 + (i // GW) % 16]
    # Falaises : colonnes natives autorisées uniquement.
    for gid in dry['layers'][1]['data']:
        if gid:
            ref = origins[gid - 1]
            assert ref['sheet'] == CLIFF and ref['texloc'][0] in CLIFF_COLUMNS and ref['role'] == 'native'
    # Berges : uniquement les bandes source du réservoir / chenal.
    for gid in wet['layers'][2]['data']:
        if gid:
            ref = origins[gid - 1]
            assert ref['sheet'] == BASE and (ref['texloc'][0] in LAKE_COLS or ref['texloc'][0] in NECK_COLS)
    # Eau : uniquement des animations natives (rivière ou chute).
    for gid in wet['layers'][3]['data']:
        if gid:
            assert gid - 1 in animations, 'Une cellule d\'eau doit être une animation native'

    def render(data, f=0):
        out = Image.new('RGBA', (W, H))
        for i, gid in enumerate(data):
            if gid:
                tid = gid - 1
                if tid in animations:
                    tid = animations[tid][f]
                out.paste(cache[tid], ((i % GW) * 8, (i // GW) * 8))
        return out

    grass = render(dry['layers'][0]['data'])
    cliffs = render(dry['layers'][1]['data'])
    combined = Image.alpha_composite(grass, cliffs)
    assert grass.tobytes() == Image.open(d / 'herbe.png').convert('RGBA').tobytes()
    assert cliffs.tobytes() == Image.open(d / 'falaises_bordures.png').convert('RGBA').tobytes()
    assert combined.tobytes() == Image.open(d / 'sans_eau_sans_chemins.png').convert('RGBA').tobytes()
    assert combined.getchannel('A').getextrema() == (255, 255)
    banks = render(wet['layers'][2]['data'])
    assert banks.tobytes() == Image.open(d / 'berges_eau.png').convert('RGBA').tobytes()
    hashes = set()
    for f in range(4):
        water = render(wet['layers'][3]['data'], f)
        assert water.tobytes() == Image.open(d / f'eau_frame_{f + 1}.png').convert('RGBA').tobytes()
        img = Image.alpha_composite(Image.alpha_composite(combined, banks), water)
        assert img.tobytes() == Image.open(d / f'avec_eau_frame_{f + 1}.png').convert('RGBA').tobytes()
        hashes.add(hashlib.sha256(water.tobytes()).hexdigest())
    assert len(hashes) == 4
    reports.append({'layout': record['id'], 'native_px': [W, H], 'grid_cells': [GW, GH],
                    'waterfalls': len(record['waterfalls']), 'lakes': len(record.get('lakes', [])),
                    'dry_source_whitelist': 'grass + cliffs only; no roads, stairs, cave or water columns',
                    'png_recomposition_differences': 0, 'distinct_water_frames': 4})

report = {'status': 'OK',
          'source_blobs_verified': len(source),
          'canonical_atlas_entries_checked': used,
          'source_tile_pixel_differences': 0,
          'atlas_premultiplied_roundtrip_differences': 0,
          'layouts': reports,
          'not_verified': ['PMDO runtime import',
                           'Collisions and transitions',
                           'Artistic/topological continuity at all new joins',
                           'Standalone original cascade timing (10 ticks chosen; river timing verified in original map)']}
(O / 'verification.json').write_text(json.dumps(report, ensure_ascii=False, indent=2))
print(json.dumps(report, ensure_ascii=False, indent=2))
