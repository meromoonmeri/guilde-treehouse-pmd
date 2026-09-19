#!/usr/bin/env python3
"""Un cliff Métano / Halcyon — méthode validée (tuiles canoniques 8 px uniquement).

Nouvelle composition (géométrie inédite) construite EXCLUSIVEMENT avec des tuiles
natives de `Metano_Town_Base` / `Metano_Town_Cliffs` / `Metano_Town_Animation_Tileset`.
Aucun pixel généré, aucune recoloration, rotation ou rééchantillonnage : les faces
hautes répètent des rangées natives entières, comme dans `build_metano_pixel_perfect.py`.
Pas d'import PMDO réel ; collisions non fournies.
"""
from pathlib import Path
from PIL import Image
import json, struct, io, math, hashlib, base64

R = Path(__file__).resolve().parents[2]
S = Path(__file__).resolve().parent
O = R / 'exports' / 'cliff_metano_halcyon_v1'
O.mkdir(parents=True, exist_ok=True)

W, H = 1024, 768
GW, GH = W // 8, H // 8
BASE = 'Metano_Town_Base'
CLIFF = 'Metano_Town_Cliffs'
ANIM = 'Metano_Town_Animation_Tileset'
NAT = R / 'source' / 'falaises_metano' / 'natifs'
NAT_ANIM = R / 'source' / 'eau_metano' / 'natifs'

SOURCE = {}
SOURCE_INFO = {}
for name in (BASE, CLIFF, ANIM):
    base_dir = NAT_ANIM if name == ANIM else NAT
    raw = (base_dir / f'{name}.tile').read_bytes()
    size, n = struct.unpack_from('<II', raw)
    assert size == 8
    tiles = {}
    for i in range(n):
        x, y, off = struct.unpack_from('<IIQ', raw, 8 + 16 * i)
        length = struct.unpack_from('<q', raw, off)[0]
        im = Image.open(io.BytesIO(raw[off + 8:off + 8 + length])).convert('RGBA')
        tiles[(x, y)] = im
    SOURCE[name] = tiles
    SOURCE_INFO[name] = {'sha256': hashlib.sha256(raw).hexdigest(), 'tiles': n}

TILES, ORIGINS, LOOKUP, PROXIES, ANIMATIONS = [], [], {}, {}, {}


def tile_id(sheet, x, y):
    key = (sheet, x, y)
    if key not in LOOKUP:
        im = SOURCE[sheet].get((x, y))
        if im is None:
            LOOKUP[key] = 0
        else:
            LOOKUP[key] = len(TILES) + 1
            TILES.append(im.copy())
            ORIGINS.append({'sheet': sheet, 'texloc': [x, y]})
    return LOOKUP[key]


def animated(refs):
    frames = tuple(tile_id(*r) for r in refs)
    if len(set(frames)) == 1:
        return frames[0]
    assert all(frames)
    if frames not in PROXIES:
        PROXIES[frames] = len(TILES) + 1
        TILES.append(TILES[frames[0] - 1].copy())
        o = dict(ORIGINS[frames[0] - 1]);
        o['role'] = 'animation_first_frame'
        ORIGINS.append(o)
        ANIMATIONS[PROXIES[frames]] = frames
    return PROXIES[frames]


def put(layer, x, y, gid):
    if gid and 0 <= x < GW and 0 <= y < GH:
        layer[y * GW + x] = gid


def ground():
    return [tile_id(BASE, x % 16, 80 + y % 16) for y in range(GH) for x in range(GW)]


def cliff_column(layer, dx, sx, offset, extension, minsy):
    rows = [y for x, y in SOURCE[CLIFF] if x == sx and y >= minsy and SOURCE[CLIFF][x, y].getbbox()]
    if not rows:
        return
    last = max(rows)
    insert = last - 4
    body = list(range(insert - 4, insert))
    for sy in range(minsy, insert):
        put(layer, dx, sy + offset, tile_id(CLIFF, sx, sy))
    for j in range(extension):
        put(layer, dx, insert + offset + j, tile_id(CLIFF, sx, body[j % 4]))
    for sy in range(insert, last + 1):
        put(layer, dx, insert + offset + extension + (sy - insert), tile_id(CLIFF, sx, sy))


def ribbon(layer, start_x, offset_y, extra_px, flats):
    cols = list(range(57, 93))
    for seg in range(flats):
        cols.extend(range(114, 122) if seg % 2 else range(85, 93))
    while start_x // 8 + len(cols) < GW:
        cols.append(188)
    for i, sx in enumerate(cols):
        dx = start_x // 8 + i
        if 0 <= dx < GW:
            minsy = 56 if 85 <= sx <= 92 and i >= 36 else 26 if sx < 93 else 38 if sx >= 162 else 54
            cliff_column(layer, dx, sx, offset_y // 8, extra_px // 8, minsy)


def waterfall(water, cx, top, end):
    rows = (end - top) // 8
    assert rows >= 17
    for y in range(rows):
        sy = y if y < 6 else (13 + y - (rows - 4) if y >= rows - 4 else 8 + (y - 6) % 4)
        for x in range(8):
            refs = [(ANIM, 1 + 9 * f + x, 62 + sy) for f in range(4)]
            put(water, cx // 8 - 4 + x, top // 8 + y, animated(refs))


BLANK = Image.new('RGBA', (8, 8))
STRAIGHT = {}


def straight_tile(gid):
    if gid not in STRAIGHT:
        im = TILES[gid - 1].copy()
        im.putdata([(round(r * 255 / a), round(g * 255 / a), round(b * 255 / a), a) if 0 < a < 255 else (r, g, b, a) for r, g, b, a in im.getdata()])
        STRAIGHT[gid] = im
    return STRAIGHT[gid]


def render(layer, frame=0):
    out = Image.new('RGBA', (W, H))
    for i, gid in enumerate(layer):
        if gid:
            actual = ANIMATIONS[gid][frame] if gid in ANIMATIONS else gid
            out.paste(straight_tile(actual), ((i % GW) * 8, (i // GW) * 8))
    return out


def build():
    g = ground()
    cliffs = [0] * (GW * GH)
    water = [0] * (GW * GH)
    # Nouvelle géométrie : un grand rempart traversant avec retour à gauche, une chute ancrée au sommet de la face.
    ribbon(cliffs, 0, 160, 128, 12)
    cx = 512
    col = cx // 8
    top = next((y for y in range(GH) if cliffs[y * GW + col]), None)
    if top is not None:
        waterfall(water, cx, top * 8, min(H, top * 8 + 208))
    grass_png = render(g)
    cliff_png = render(cliffs)
    dry = Image.alpha_composite(grass_png, cliff_png)
    grass_png.save(O / 'herbe.png')
    cliff_png.save(O / 'falaises.png')
    dry.save(O / 'cliff_sec.png')
    for f in range(4):
        w = render(water, f)
        w.save(O / f'eau_frame_{f+1}.png')
        Image.alpha_composite(dry, w).save(O / f'cliff_eau_frame_{f+1}.png')

    manifest = {
        'reference': 'Palikadude/Halcyon', 'commit': 'da6c2130d641507447e6386a5e47a296e8cb4c71',
        'size_px': [W, H], 'grid_px': 8, 'cellules': [GW, GH],
        'sources': SOURCE_INFO,
        'layers': ['herbe.png', 'falaises.png', 'eau_frame_1..4.png'],
        'method': 'Méthode validée : tuiles canoniques 8 px uniquement, faces hautes par répétition de rangées natives, chute en 4 frames natives.',
        'not_validated': ['Import PMDO réel', 'Collisions / transitions'],
    }
    (O / 'manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n')
    (O / 'provenance.json').write_text(json.dumps({'atlas_entries': len(TILES), 'origins': ORIGINS}, ensure_ascii=False, indent=2) + '\n')

    def uri(p):
        return 'data:image/png;base64,' + base64.b64encode(p.read_bytes()).decode()
    view = {'dry': uri(O / 'cliff_sec.png'), 'water': [uri(O / f'eau_frame_{i}.png') for i in range(1, 5)]}
    html = f'''<!doctype html><html lang="fr"><meta charset="utf-8"><title>Cliff Métano — Halcyon</title>
<style>body{{background:#14231e;color:#ecdfba;font:16px system-ui;max-width:1100px;margin:32px auto;padding:16px}}h1{{font-size:30px}}canvas{{image-rendering:pixelated;display:block;margin:8px 0}}button{{margin:6px}}</style>
<h1>Cliff Métano / Halcyon — tuiles canoniques 8 px</h1>
<p>Méthode validée : aucune texture générée ; faces par répétition de rangées natives, chute animée en 4 frames natives.</p>
<canvas id="c" width="{W}" height="{H}" style="width:{W}px"></canvas>
<button onclick="set(0)">sec</button><button onclick="set(1)">eau f1</button><button onclick="set(2)">eau f2</button><button onclick="set(3)">eau f3</button><button onclick="set(4)">eau f4</button>
<script>const D={json.dumps(view)};const c=document.getElementById('c');const x=c.getContext('2d');const imgs={{}};
function load(u){{if(!imgs[u]){{const i=new Image();i.src=u;imgs[u]=i}}return imgs[u]}}
function set(k){{x.clearRect(0,0,{W},{H});const d=load(D.dry);if(d.complete)x.drawImage(d,0,0);if(k>0){{const w=load(D.water[k-1]);if(w.complete)x.drawImage(w,0,0)}}}}
set(0);const d=load(D.dry);d.onload=()=>set(0);</script></html>'''
    (R / 'apercu_cliff_metano_halcyon_v1.html').write_text(html)
    print('cliff composé ; entrées atlas canoniques :', len(TILES), '; animations :', len(ANIMATIONS))


if __name__ == '__main__':
    build()
