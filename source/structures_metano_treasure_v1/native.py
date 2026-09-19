#!/usr/bin/env python3
"""Lecteur indépendant des ressources natives .tile / .rsground (RogueEssence / PMDO).

Aucune génération de pixels ici : ce module décode les fichiers binaires et JSON
des dépôts de référence et recompose leurs atlas / cartes tels quels.
"""
from __future__ import annotations

import hashlib
import io
import json
import struct
from pathlib import Path

import numpy as np
from PIL import Image

R = Path(__file__).resolve().parents[2]
REF = Path(__file__).resolve().parent / 'references'

PROVENANCE_REPO = {
    'Halcyon': {
        'url': 'https://github.com/Palikadude/Halcyon',
        'branch': 'master',
        'commit': 'da6c2130d641507447e6386a5e47a296e8cb4c71',
    },
    'ExplorersOfSkyOrigins': {
        'url': 'https://github.com/Minemaker0430/ExplorersOfSkyOrigins',
        'branch': 'main',
        'commit': 'bed9449',
    },
}


def sha256(path: Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read_tile(path: Path):
    """Decode a native .tile sheet -> {(x, y): RGBA ndarray of side `cell_px`}."""
    data = Path(path).read_bytes()
    size, count = struct.unpack_from('<ii', data)
    assert size > 0, (path.name, size)
    tiles, cache = {}, {}
    for i in range(count):
        x, y, address = struct.unpack_from('<iiq', data, 8 + i * 16)
        if address not in cache:
            n, = struct.unpack_from('<q', data, address)
            image = Image.open(io.BytesIO(data[address + 8:address + 8 + n])).convert('RGBA')
            assert image.size == (size, size), (path.name, image.size)
            cache[address] = np.array(image)
        assert (x, y) not in tiles, (path.name, x, y)
        tiles[(x, y)] = cache[address]
    return tiles


def tile_cell(path: Path) -> int:
    return struct.unpack_from('<ii', Path(path).read_bytes())[0]


def tile_sheet(path: Path, pad: int = 0):
    """Recompose a .tile into a single atlas image, tiles placed by their own (x, y)."""
    tiles = read_tile(path)
    c = tile_cell(path)
    maxx = max(x for x, _ in tiles)
    maxy = max(y for _, y in tiles)
    w = (maxx + 1) * (c + pad)
    h = (maxy + 1) * (c + pad)
    sheet = np.zeros((h, w, 4), np.uint8)
    for (x, y), t in tiles.items():
        ox, oy = x * (c + pad), y * (c + pad)
        sheet[oy:oy + c, ox:ox + c] = t
    return Image.fromarray(sheet), tiles


def unique_tiles(path: Path):
    """Distinct 8x8 tiles of a sheet, by pixel content (first occurrence order)."""
    tiles = read_tile(path)
    seen, out = {}, []
    for (x, y) in sorted(tiles):
        key = tiles[(x, y)].tobytes()
        if key not in seen:
            seen[key] = (x, y)
            out.append(((x, y), tiles[(x, y)]))
    return out


def read_ground(path: Path):
    obj = json.loads(Path(path).read_text(encoding='utf-8-sig'))['Object']
    return obj


def ground_size(obj):
    cell = obj['TexSize'] * 8
    layers = obj['Layers']
    return (len(layers[0]['Tiles']) * cell, len(layers[0]['Tiles'][0]) * cell, cell)


def ground_layer_names(obj):
    return [(i, l['Name'], l.get('Visible', True)) for i, l in enumerate(obj['Layers'])]


def render_ground(obj, sheet_cache, layer_filter=None, phase=None, max_cells=None):
    """Recompose a Ground map from its layers. sheet_cache: {sheet_name: {TexLoc: 8x8 array}}.

    phase: callable(sheet_name, frame_index) -> frame index actually used.
    """
    cell = obj['TexSize'] * 8
    w, h = len(obj['Layers'][0]['Tiles']), len(obj['Layers'][0]['Tiles'][0])
    if max_cells:
        w, h = min(w, max_cells[0]), min(h, max_cells[1])
    canvas = np.zeros((h * cell, w * cell, 4), np.float64)  # premultiplied alpha, float compositing
    missing = set()

    def blit(img, ox, oy):
        # Native .tile pixels are premultiplied (rgb <= alpha); composite in that space.
        c = img.shape[0]
        dst = canvas[oy:oy + c, ox:ox + c]
        sa = img[:, :, 3:4].astype(np.float64) / 255.0
        src = img[:, :, :3].astype(np.float64)  # already premultiplied
        oa = sa + dst[:, :, 3:4] * (1.0 - sa)
        oc = src + dst[:, :, :3] * (1.0 - sa)
        canvas[oy:oy + c, ox:ox + c, :3] = oc
        canvas[oy:oy + c, ox:ox + c, 3:4] = oa

    for li, layer in enumerate(obj['Layers']):
        if layer_filter and li not in layer_filter:
            continue
        for x, column in enumerate(layer['Tiles'][:w]):
            for y, tile in enumerate(column[:h]):
                if not tile:
                    continue
                for sub in tile.get('Layers', []):
                    frames = sub.get('Frames', [])
                    if not frames:
                        continue
                    idx = 0
                    if phase is not None and len(frames) > 1:
                        idx = phase('', len(frames))
                    frame = frames[idx % len(frames)]
                    sheet = frame.get('Sheet', '')
                    bank = sheet_cache.get(sheet)
                    if bank is None:
                        missing.add(sheet)
                        continue
                    loc = frame.get('TexLoc', {})
                    img = bank.get((loc.get('X', 0), loc.get('Y', 0)))
                    if img is None:
                        missing.add(f'{sheet}@{loc.get("X", 0)},{loc.get("Y", 0)}')
                        continue
                    blit(img, x * cell, y * cell)
    out = np.zeros_like(canvas, np.uint8)
    a = canvas[:, :, 3:4]
    with np.errstate(invalid='ignore', divide='ignore'):
        rgb = np.where(a > 0, canvas[:, :, :3] / np.maximum(a, 1e-9), 0.0)
    out[:, :, :3] = np.clip(np.round(rgb), 0, 255)
    out[:, :, 3] = np.clip(np.round(a[:, :, 0] * 255.0), 0, 255)
    return Image.fromarray(out), missing


def sheets_from_tiles(paths):
    """{sheet_name: {(x, y): 8x8 array}} for a list of .tile paths."""
    return {Path(p).stem: read_tile(p) for p in paths}


def provenance():
    out = {}
    for p in sorted(REF.iterdir()):
        if p.is_file():
            repo = 'Halcyon' if p.stem.startswith('Metano') else 'ExplorersOfSkyOrigins'
            kind = 'Tile' if p.suffix == '.tile' else 'Ground'
            out[p.name] = {
                **PROVENANCE_REPO[repo],
                'repo_path': f'{"Content/Tile" if kind == "Tile" else "Data/Ground"}/{p.name}',
                'sha256': sha256(p),
                'bytes': p.stat().st_size,
            }
    return out


if __name__ == '__main__':
    import sys
    out = Path(sys.argv[1]) if len(sys.argv) > 1 else Path('/tmp/sheets')
    out.mkdir(parents=True, exist_ok=True)
    for p in sorted(REF.glob('*.tile')):
        tiles = read_tile(p)
        c = tile_cell(p)
        sheet, _ = tile_sheet(p)
        sheet.save(out / f'{p.stem}__sheet.png')
        xs = [x for x, _ in tiles]
        ys = [y for _, y in tiles]
        print(f'{p.name:40s} cell={c:3d}px tiles={len(tiles):6d} span={max(xs)+1}x{max(ys)+1} sheet={sheet.size[0]}x{sheet.size[1]}px')
