# -*- coding: utf-8 -*-
import struct, io, json, os
from PIL import Image

def load_tilesheet(path):
    d=open(path,'rb').read()
    tsize, count = struct.unpack('<ii', d[:8])
    n=count
    tiles={}
    for i in range(n):
        x,y,off = struct.unpack('<iiq', d[8+16*i:24+16*i])
        ln = struct.unpack('<q', d[off:off+8])[0]
        img = Image.open(io.BytesIO(d[off+8:off+8+ln])).convert('RGBA')
        tiles[(x,y)] = img
    return tsize, tiles

def load_ground(path):
    with io.open(path, encoding='utf-8-sig') as f:
        return json.load(f)['Object']


_SHEETS = {}


def render_ground(g, halcyon_dir):
    """Recompose l'image d'une ground map RogueEssence a partir de ses calques."""
    layers = g['Layers']
    W = len(layers[0]['Tiles']); H = len(layers[0]['Tiles'][0])
    canvas = Image.new('RGBA', (W * 8, H * 8), (0, 0, 0, 0))
    for L in layers:
        if not L.get('Visible', True):
            continue
        T = L['Tiles']
        for x in range(W):
            for y in range(H):
                for sub in T[x][y]['Layers']:
                    fr = sub['Frames'][0]
                    name = fr['Sheet']
                    if not name:
                        continue
                    if name not in _SHEETS:
                        p = os.path.join(halcyon_dir, 'Content', 'Tile', name + '.tile')
                        if not os.path.exists(p):
                            _SHEETS[name] = {}
                        else:
                            _SHEETS[name] = load_tilesheet(p)[1]
                    img = _SHEETS[name].get((fr['TexLoc']['X'], fr['TexLoc']['Y']))
                    if img is not None:
                        canvas.alpha_composite(img, (x * 8, y * 8))
    return canvas
