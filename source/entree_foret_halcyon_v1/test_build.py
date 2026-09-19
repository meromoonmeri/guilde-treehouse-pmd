#!/usr/bin/env python3
"""Tests de l'entrée de forêt : sol et rochers canoniques, arbres présents, carte recomposable."""
import importlib.util
import json
import sys
import struct, io
import xml.etree.ElementTree as ET
from pathlib import Path

import numpy as np
from PIL import Image

HERE = Path(__file__).resolve().parent
R = HERE.parents[1]
O = R / 'exports' / 'entree_foret_halcyon_v1'
_spec = importlib.util.spec_from_file_location('nat', R / 'source' / 'structures_metano_treasure_v1' / 'native.py')
nat = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(nat)
REF = HERE / 'references'


def unprem_set(name):
    raw = (REF / name).read_bytes()
    size, n = struct.unpack_from('<ii', raw)
    out = set()
    for i in range(n):
        x, y, off = struct.unpack_from('<iiq', raw, 8 + 16 * i)
        length = struct.unpack_from('<q', raw, off)[0]
        im = Image.open(io.BytesIO(raw[off + 8:off + 8 + length])).convert('RGBA')
        im.putdata([(round(r * 255 / a), round(g * 255 / a), round(b * 255 / a), a) if 0 < a < 255 else (r, g, b, a) for r, g, b, a in im.getdata()])
        out.add(im.tobytes())
    return out


def blocks_canonical(png, banks):
    a = np.array(Image.open(png).convert('RGBA'))
    bad = tot = 0
    for y in range(0, a.shape[0], 8):
        for x in range(0, a.shape[1], 8):
            blk = a[y:y + 8, x:x + 8]
            if blk[:, :, 3].max() == 0:
                continue
            tot += 1
            if blk.tobytes() not in banks:
                bad += 1
    return tot, bad


def main():
    f = []
    base = unprem_set('Vast_Steppe_Base.tile')
    tot, bad = blocks_canonical(O / 'entree_00_sol.png', base)
    print(f'sol: {tot} blocs, {bad} non canoniques')
    if bad:
        f.append('sol non canonique')

    # rochers : pixels opaques == pixels du rendu Amp Plains (canonique)
    amp = nat.read_ground(REF / 'amp_plains_entrance.rsground')
    acache = {'Amp Plains Entrance Layer 1': nat.read_tile(REF / 'AmpPlains_Entrance_L1.tile'),
              'Amp Plains Entrance Layer 2': nat.read_tile(REF / 'AmpPlains_Entrance_L2.tile')}
    arender, _ = nat.render_ground(amp, acache)
    aa = np.array(arender.convert('RGBA'))
    aa_set = {tuple(p) for p in aa[aa[:, :, 3] > 0].reshape(-1, 4)}
    for p in sorted((O / 'rochers').glob('*.png')):
        rk = np.array(Image.open(p).convert('RGBA'))
        opaque = rk[rk[:, :, 3] > 0].reshape(-1, 4)
        miss = sum(1 for q in opaque if tuple(q) not in aa_set)
        print(f'{p.name}: {len(opaque)} px opaques, {miss} hors référence')
        if miss:
            f.append(f'{p.name} non canonique')

    arbres = np.array(Image.open(O / 'entree_02_arbres.png').convert('RGBA'))
    if (arbres[:, :, 3] > 0).sum() == 0:
        f.append('arbres vides')
    # arbres canoniques : chaque pixel opaque vient d'un sprite canonique extrait
    tset = set()
    for p in sorted((O / 'trees_canoniques').glob('*.png')):
        t = np.array(Image.open(p).convert('RGBA'))
        tset |= {tuple(q) for q in t[t[:, :, 3] > 0].reshape(-1, 4)}
    miss = sum(1 for q in arbres[arbres[:, :, 3] > 0].reshape(-1, 4) if tuple(q) not in tset)
    print(f'arbres: {(arbres[:,:,3]>0).sum()} px, {miss} hors sprites canoniques')
    if miss:
        f.append('arbres non canoniques')

    # recomposition composite
    sol = np.array(Image.open(O / 'entree_00_sol.png').convert('RGBA'))
    roch = np.array(Image.open(O / 'entree_01_rochers.png').convert('RGBA'))
    comp = np.array(Image.open(O / 'entree_composite.png').convert('RGBA'))
    acc = sol.astype(np.float64)
    for layer in (roch, arbres):
        a = layer[:, :, 3:4].astype(np.float64) / 255.0
        acc[:, :, :3] = layer[:, :, :3] * a + acc[:, :, :3] * (1 - a)
        acc[:, :, 3] = 255
    if np.abs(acc.astype(np.uint8).astype(int) - comp.astype(int)).max() > 1:
        f.append('composite != recomposition')

    ET.parse(O / 'entree_foret.tmx')
    ET.parse(O / 'entree_sol.tsx')
    prov = json.loads((O / 'provenance.json').read_text())
    for name, meta in prov.items():
        if nat.sha256(REF / name) != meta['sha256']:
            f.append(f'référence modifiée {name}')

    print('FAILURES:' if f else 'OK', len(f))
    for x in f:
        print(' -', x)
    return 1 if f else 0


if __name__ == '__main__':
    sys.exit(main())
