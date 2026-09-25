#!/usr/bin/env python3
"""Outils PMDO (RogueEssence 0.8.12) — lecture/écriture de feuilles .tile et rendu de cartes .rsground.

Usage :
  .venv/bin/python tools/pmdo_tiles.py decode  <feuille.tile> [--out atlas.png]
  .venv/bin/python tools/pmdo_tiles.py inventory <dossier> [--out dossier_atlas]
  .venv/bin/python tools/pmdo_tiles.py render  <carte.rsground> --sheets <dossier_atlas> [...] [--out rendu.png] [--phase 0]

Format .tile (lecture moteur auditée) : int32 tileSize, int32 count, count × (int32 x, int32 y, int64 offset) ;
à chaque offset : int64 longueur PNG puis PNG (pixels prémultipliés). L'atlas exporté est dé-prémultiplié (alpha droit).
"""
import argparse
import io
import json
import struct
import sys
from pathlib import Path

import numpy as np
from PIL import Image


def unpremultiply(rgba):
    a = rgba[:, :, 3:4].astype(np.uint32)
    rgb = rgba[:, :, :3].astype(np.uint32)
    out = rgba.copy()
    nz = a[:, :, 0] > 0
    rgb_u = np.where(a > 0, np.minimum(255, (rgb * 255 + a // 2) // np.maximum(a, 1)), 0)
    out[:, :, :3] = rgb_u.astype(np.uint8)
    out[~nz, :3] = 0
    return out


def read_tile(path):
    """Retourne (tile_size, {(x, y): np.uint8 RGBA prémultiplié})."""
    data = Path(path).read_bytes()
    size, count = struct.unpack_from('<ii', data)
    tiles, cache = {}, {}
    for i in range(count):
        x, y, address = struct.unpack_from('<iiq', data, 8 + i * 16)
        if address not in cache:
            n, = struct.unpack_from('<q', data, address)
            im = Image.open(io.BytesIO(data[address + 8:address + 8 + n])).convert('RGBA')
            cache[address] = np.array(im)
        tiles[(x, y)] = cache[address]
    return size, tiles


def tile_to_atlas(path, straight_alpha=True):
    size, tiles = read_tile(path)
    if not tiles:
        return size, Image.new('RGBA', (size, size)), {}
    w = (max(x for x, _ in tiles) + 1) * size
    h = (max(y for _, y in tiles) + 1) * size
    atlas = np.zeros((h, w, 4), np.uint8)
    for (x, y), px in tiles.items():
        atlas[y * size:(y + 1) * size, x * size:(x + 1) * size] = px
    if straight_alpha:
        atlas = unpremultiply(atlas)
    meta = {'tile_size': size, 'count': len(tiles), 'atlas_size': [w, h],
            'occupied': sorted([list(k) for k in tiles])}
    return size, Image.fromarray(atlas), meta


class SheetBank:
    """Feuilles disponibles par nom : atlas PNG (alpha droit) + taille de tuile."""

    def __init__(self):
        self.sheets = {}

    def add_dir(self, folder):
        folder = Path(folder)
        for p in sorted(folder.rglob('*.tile')):
            size, atlas, _ = tile_to_atlas(p)
            self.sheets.setdefault(p.stem, (size, np.array(atlas)))
        for p in sorted(folder.rglob('*.png')):
            name = p.stem
            if name.endswith('_atlas'):
                name = name[:-6]
            if name in self.sheets:
                continue
            meta = p.with_suffix('.json')
            size = 8
            if meta.exists():
                try:
                    size = json.loads(meta.read_text()).get('tile_size', 8)
                except Exception:
                    pass
            self.sheets[name] = (size, np.array(Image.open(p).convert('RGBA')))

    def get(self, name, x, y, tex_size=1):
        if name not in self.sheets:
            return None
        size, atlas = self.sheets[name]
        # TexLoc indexe des tuiles de la taille propre à la feuille (8 px pour TexSize 1, 24 px pour TexSize 3).
        x0, y0 = x * size, y * size
        if y0 + size > atlas.shape[0] or x0 + size > atlas.shape[1]:
            return None
        return atlas[y0:y0 + size, x0:x0 + size]


def composite(dst, src, x, y):
    h, w = src.shape[:2]
    H, W = dst.shape[:2]
    if x >= W or y >= H or x + w <= 0 or y + h <= 0:
        return
    x1, y1 = max(x, 0), max(y, 0)
    x2, y2 = min(x + w, W), min(y + h, H)
    s = src[y1 - y:y2 - y, x1 - x:x2 - x].astype(np.float32)
    d = dst[y1:y2, x1:x2].astype(np.float32)
    sa = s[:, :, 3:4] / 255.0
    da = d[:, :, 3:4] / 255.0
    oa = sa + da * (1 - sa)
    rgb = np.where(oa > 0, (s[:, :, :3] * sa + d[:, :, :3] * da * (1 - sa)) / np.maximum(oa, 1e-6), 0)
    dst[y1:y2, x1:x2, :3] = np.clip(rgb + 0.5, 0, 255).astype(np.uint8)
    dst[y1:y2, x1:x2, 3] = np.clip(oa[:, :, 0] * 255 + 0.5, 0, 255).astype(np.uint8)


def load_ground(path):
    raw = Path(path).read_bytes().decode('utf-8-sig')
    return json.loads(raw)['Object']


def render_ground(ground, bank, phase=0, layer_filter=None, missing=None):
    tex = ground.get('TexSize', 1)
    cell = 8 * tex
    layers = ground['Layers']
    w = len(layers[0]['Tiles']) * cell
    h = len(layers[0]['Tiles'][0]) * cell
    out = np.zeros((h, w, 4), np.uint8)
    per_layer = []
    for li, L in enumerate(layers):
        if layer_filter is not None and li not in layer_filter:
            continue
        img = np.zeros((h, w, 4), np.uint8)
        for x, col in enumerate(L['Tiles']):
            for y, t in enumerate(col):
                for anim in t.get('Layers', []):
                    frames = anim.get('Frames', [])
                    if not frames:
                        continue
                    fr = frames[phase % len(frames)]
                    px = bank.get(fr['Sheet'], fr['TexLoc']['X'], fr['TexLoc']['Y'], tex)
                    if px is None:
                        if missing is not None:
                            missing[fr['Sheet']] = missing.get(fr['Sheet'], 0) + 1
                        continue
                    composite(img, px, x * cell, y * cell)
        per_layer.append((L.get('Name', f'layer{li}'), img))
        composite(out, img, 0, 0)
    return out, per_layer


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest='cmd', required=True)
    d = sub.add_parser('decode'); d.add_argument('tile'); d.add_argument('--out')
    i = sub.add_parser('inventory'); i.add_argument('folder'); i.add_argument('--out', required=True)
    r = sub.add_parser('render'); r.add_argument('ground'); r.add_argument('--sheets', nargs='+', required=True)
    r.add_argument('--out', required=True); r.add_argument('--phase', type=int, default=0); r.add_argument('--layers', action='store_true')
    a = ap.parse_args()
    if a.cmd == 'decode':
        size, atlas, meta = tile_to_atlas(a.tile)
        out = Path(a.out) if a.out else Path(a.tile).with_suffix('.png')
        atlas.save(out)
        out.with_suffix('.json').write_text(json.dumps(meta))
        print(f'{a.tile}: tuile {size}px, {meta["count"]} tuiles, atlas {meta["atlas_size"]} -> {out}')
    elif a.cmd == 'inventory':
        outdir = Path(a.out); outdir.mkdir(parents=True, exist_ok=True)
        rows = []
        for p in sorted(Path(a.folder).rglob('*.tile')):
            size, atlas, meta = tile_to_atlas(p)
            dst = outdir / (p.stem + '.png')
            if not dst.exists():
                atlas.save(dst)
                dst.with_suffix('.json').write_text(json.dumps({k: v for k, v in meta.items() if k != 'occupied'}))
            rows.append({'sheet': p.stem, 'source': str(p), 'tile_size': size, 'count': meta['count'], 'atlas': meta['atlas_size']})
            print(f'{p.stem:45s} tuile {size:2d}px  {meta["count"]:6d} tuiles  atlas {meta["atlas_size"]}')
        (outdir / 'INVENTAIRE.json').write_text(json.dumps(rows, indent=1, ensure_ascii=False))
    elif a.cmd == 'render':
        bank = SheetBank()
        for s in a.sheets:
            bank.add_dir(s)
        g = load_ground(a.ground)
        missing = {}
        out, per_layer = render_ground(g, bank, a.phase, missing=missing)
        Image.fromarray(out).save(a.out)
        print(f'{a.ground}: {out.shape[1]}x{out.shape[0]} -> {a.out}')
        if a.layers:
            base = Path(a.out)
            for k, (name, img) in enumerate(per_layer):
                safe = ''.join(c if c.isalnum() else '_' for c in name)
                Image.fromarray(img).save(base.with_name(f'{base.stem}_L{k:02d}_{safe}.png'))
        if missing:
            print('Feuilles absentes :', json.dumps(missing, ensure_ascii=False))


if __name__ == '__main__':
    main()
