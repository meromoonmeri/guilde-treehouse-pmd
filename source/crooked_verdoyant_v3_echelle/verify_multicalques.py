"""Relecture indépendante des exports multicalques (PNG, Aseprite, Tiled + atlas 8 px) → verification_multicalques.json.
Même esprit que source/verify_zones_multicalques.py : décodage sans passer par le code d'écriture, 0 différence de pixel exigée."""
from __future__ import annotations
import base64, hashlib, json, struct, sys, zlib
from pathlib import Path
import numpy as np
from PIL import Image

R = Path(__file__).resolve().parents[2]
REN = R / 'renders/crooked_verdoyant_v3_echelle'
OUT = R / 'exports/crooked_verdoyant_v3_echelle/multicalques'
W, H, T = 928, 1152, 8


def decode_ase(path: Path):
    data = path.read_bytes()
    size, magic, count, w, h, depth, flags, speed = struct.unpack_from('<IHHHHHIH', data)
    assert size == len(data) and magic == 0xA5E0 and (w, h, depth) == (W, H, 32) and count == 1
    assert struct.unpack_from('<hhHH', data, 36) == (0, 0, T, T)
    pos = 128
    length, fmagic, n, duration = struct.unpack_from('<IHHH', data, pos); assert fmagic == 0xF1FA
    end = pos + length; pos += 16; names = []; cels = {}
    for _ in range(n):
        clen, kind = struct.unpack_from('<IH', data, pos); p = data[pos + 6:pos + clen]
        if kind == 0x2004:
            ln = struct.unpack_from('<H', p, 16)[0]; names.append(p[18:18 + ln].decode()); assert struct.unpack_from('<H', p)[0] & 1 and p[12] == 255
        elif kind == 0x2005:
            idx, x, y, alpha, typ = struct.unpack_from('<HhhBH', p); assert alpha == 255 and typ == 2
            cw, ch = struct.unpack_from('<HH', p, 16); im = Image.frombytes('RGBA', (cw, ch), zlib.decompress(p[20:]))
            cels[idx] = (x, y, im)
        pos += clen
    assert pos == end == len(data) and sorted(cels) == list(range(len(names)))
    ims = []
    for idx in sorted(cels):
        x, y, im = cels[idx]; canvas = Image.new('RGBA', (w, h)); canvas.paste(im, (x, y)); ims.append(canvas)
    return names, ims


def decode_tmj(path: Path):
    tm = json.loads(path.read_text())
    assert tm['width'] == W // T and tm['height'] == H // T and tm['tilewidth'] == tm['tileheight'] == T
    ts = json.loads((path.parent / tm['tilesets'][0]['source']).read_text())
    atlas = Image.open(path.parent / ts['image']).convert('RGBA'); cols = ts['columns']
    assert atlas.size == (ts['imagewidth'], ts['imageheight']) and ts['tilewidth'] == ts['tileheight'] == T
    ims = []; names = []
    for layer in tm['layers']:
        assert layer['encoding'] == 'base64' and layer['compression'] == 'zlib'
        gids = struct.unpack('<' + 'I' * (W // T * H // T), zlib.decompress(base64.b64decode(layer['data'])))
        im = Image.new('RGBA', (W, H))
        for i, g in enumerate(gids):
            if g:
                assert 1 <= g <= ts['tilecount']
                sx, sy = (g - 1) % cols * T, (g - 1) // cols * T
                im.paste(atlas.crop((sx, sy, sx + T, sy + T)), (i % (W // T) * T, i // (W // T) * T))
        ims.append(im); names.append(layer['name'])
    return names, ims, ts['tilecount']


def main():
    M = json.loads((OUT / 'multicalques.json').read_text())
    res = {'variants': {}}
    ok = True
    for tag, v in M['variants'].items():
        r = {}
        r['sha256_ok'] = all(hashlib.sha256((OUT / fn).read_bytes()).hexdigest() == sha for fn, sha in v['sha256'].items())
        pngs = [Image.open(OUT / v['files'][l['id']]).convert('RGBA') for l in M['layers']]
        # PNG export == calque de rendu
        src = REN / ('calques' if tag == 'jour' else 'nuit')
        r['png_equal_render_layers'] = all(im.tobytes() == Image.open(src / (v['files'][l['id']])).convert('RGBA').tobytes() for im, l in zip(pngs, M['layers']))
        comp = Image.new('RGBA', (W, H))
        for im in pngs:
            comp.alpha_composite(im)
        r['composition_equal_render'] = comp.tobytes() == Image.open(REN / f'composition_{tag}.png').convert('RGBA').tobytes()
        r['composition_file_equal'] = comp.tobytes() == Image.open(OUT / v['composition']).convert('RGBA').tobytes()
        names, ims = decode_ase(OUT / v['aseprite'])
        r['aseprite_layer_names_ok'] = names == [l['name'] for l in M['layers']]
        r['aseprite_pixels_equal'] = all(a.tobytes() == b.tobytes() for a, b in zip(ims, pngs)) and len(ims) == len(pngs)
        tnames, tims, count = decode_tmj(OUT / v['tiled'])
        r['tiled_layer_names_ok'] = tnames == [l['name'] for l in M['layers']]
        r['tiled_pixels_equal'] = all(a.tobytes() == b.tobytes() for a, b in zip(tims, pngs)) and len(tims) == len(pngs)
        r['atlas_tiles'] = count
        res['variants'][tag] = r
        ok &= all(x is True for x in r.values() if isinstance(x, bool))
    res['limits'] = ['Pas de validation interactive Aseprite/Tiled', 'Pas de test PMDO, collisions ni warps', 'Atlas 8 px dérivé de pixels générés (non canonique)']
    res['all_pass'] = bool(ok)
    (OUT / 'verification_multicalques.json').write_text(json.dumps(res, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps(res, ensure_ascii=False, indent=1))
    return 0 if ok else 1


if __name__ == '__main__':
    sys.exit(main())
