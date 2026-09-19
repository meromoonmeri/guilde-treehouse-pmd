#!/usr/bin/env python3
"""Vérifie que le cliff n'est composé QUE de tuiles canoniques 8 px des feuilles source.

Chaque bloc 8x8 non vide des calques herbe / falaises / eau doit être identique à au
moins une tuile native de Metano_Town_Base / Metano_Town_Cliffs / Metano_Town_Animation_Tileset.
"""
import struct, io, sys
from pathlib import Path
import numpy as np
from PIL import Image

R = Path(__file__).resolve().parents[2]
O = R / 'exports' / 'cliff_metano_halcyon_v1'
NAT = R / 'source' / 'falaises_metano' / 'natifs'
NAT_ANIM = R / 'source' / 'eau_metano' / 'natifs'


def load(name, d):
    raw = (d / f'{name}.tile').read_bytes()
    size, n = struct.unpack_from('<II', raw)
    out = set()
    for i in range(n):
        x, y, off = struct.unpack_from('<IIQ', raw, 8 + 16 * i)
        length = struct.unpack_from('<q', raw, off)[0]
        im = Image.open(io.BytesIO(raw[off + 8:off + 8 + length])).convert('RGBA')
        im.putdata([(round(r * 255 / a), round(g * 255 / a), round(b * 255 / a), a) if 0 < a < 255 else (r, g, b, a) for r, g, b, a in im.getdata()])
        out.add(im.tobytes())
    return out


def check(png, banks, label, allow_empty=True):
    a = np.array(Image.open(png).convert('RGBA'))
    bad = 0
    tot = 0
    for y in range(0, a.shape[0], 8):
        for x in range(0, a.shape[1], 8):
            blk = a[y:y + 8, x:x + 8]
            if blk[:, :, 3].max() == 0:
                continue
            tot += 1
            if blk.tobytes() not in banks:
                bad += 1
    print(f'{label}: {tot} blocs, {bad} non canoniques')
    return bad


def main():
    base = load('Metano_Town_Base', NAT)
    cliff = load('Metano_Town_Cliffs', NAT)
    anim = load('Metano_Town_Animation_Tileset', NAT_ANIM)
    # unpremultiply not needed: blocks compared as stored (same pipeline)
    bad = 0
    bad += check(O / 'herbe.png', base, 'herbe')
    bad += check(O / 'falaises.png', cliff | base, 'falaises')
    for f in range(1, 5):
        bad += check(O / f'eau_frame_{f}.png', anim, f'eau f{f}')
    print('FAILURES' if bad else 'OK', bad)
    return 1 if bad else 0


if __name__ == '__main__':
    sys.exit(main())
