#!/usr/bin/env python3
"""Mesures de la source Brine_Cave_Entrance (EoSO) qui justifient les plans
d'agrandissement du lot plage_cote_v2 (voir ANALYSE.md).

    .venv/bin/python source/plage_cote_v2/analyse.py  -> analyse.json

Toutes les mesures portent sur le rendu composite de la carte EoSO
Brine_Cave_Entrance (27 x 21 cellules de 24 px, 1 calque, 15 frames par
cellule). « Raccord » = erreur quadratique moyenne (MSE, RGB 0-255) entre la
dernière colonne (ou rangée) de pixels d'un bloc et la première colonne (ou
rangée) du bloc suivant, toutes frames confondues.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

sys.path.insert(0, str(Path(__file__).resolve().parent))
from tilelib import CELL, HERE, REF, TileSheet, cell_frames, composite, load_ground  # noqa: E402

CACHE = HERE.parents[1] / '.cache/plage_cote_v2'
W, H = 27, 21
FRAMES = 15


def main():
    CACHE.mkdir(parents=True, exist_ok=True)
    sheet = TileSheet(REF / 'EoSO__Brine_Cave_Entrance.tile')
    ground = load_ground(REF / 'EoSO__Brine_Cave_Entrance.rsground')['Object']
    layer = ground['Layers'][0]
    tiles = layer['Tiles']
    assert layer['Name'] == 'New Layer' and len(tiles) == W and len(tiles[0]) == H

    frames = np.stack([np.asarray(composite(ground, {'Brine Cave Entrance': sheet}, f)) for f in range(FRAMES)]).astype(np.float64)
    report = {'grid': [W, H], 'cell_px': CELL, 'sheet': {'size': CELL, 'cells_w': sheet.width, 'cells_h': sheet.height}}

    # 1. animation : FrameLength, frames par cellule, cellules statiques
    lengths = {len(cell_frames(t)) for col in tiles for t in col if cell_frames(t)}
    frame_len = {a['FrameLength'] for col in tiles for t in col if t['Layers'] for a in t['Layers']}
    static, animated = [], []
    for x in range(W):
        for y in range(H):
            ids = {sheet.payload_id(tx, ty) for _, tx, ty in cell_frames(tiles[x][y])}
            (static if len(ids) == 1 else animated).append([x, y])
    report['animation'] = {'frames_per_cell': sorted(lengths), 'frame_length_ticks': sorted(v for v in frame_len if v is not None),
                           'frame_length_absent': None in frame_len,
                           'static_cells': len(static), 'animated_cells': len(animated),
                           'static_cols_uniform': [x for x in range(W) if all([x, y] in static for y in range(H))],
                           'static_rows_uniform': [y for y in range(H) if all([x, y] in static for x in range(W))]}
    # flipbook horizontal : frame k de (x, y) est en (x + 27k, y)
    flip_ok = all(cell_frames(tiles[0][0])[k][1] == 27 * k for k in range(FRAMES))
    report['animation']['horizontal_flipbook_step27'] = flip_ok

    # 2. obstacles : carte 8 px -> carte cellule (part de blocs libres)
    obst = ground['obstacles']
    free_map, free_ascii = [], []
    for x in range(W):
        colf, rowa = [], ''
        for y in range(H):
            tags = [obst[x * 3 + i][y * 3 + j]['Tags'] for i in range(3) for j in range(3)]
            f = sum(1 for t in tags if t == 0) / 9
            colf.append(round(f, 2))
            rowa += '.' if f == 1 else ('#' if f == 0 else '+')
        free_map.append(colf)
        free_ascii.append(rowa)
    report['obstacles_free_ratio'] = free_map
    report['obstacles_ascii'] = {'x->': free_ascii, 'legend': '. libre / + mixte / # bloque (par cellule 24 px)'}

    # 3. rendus de contrôle
    for f in (0, 7, 14):
        composite(ground, {'Brine Cave Entrance': sheet}, f).convert('RGB').save(CACHE / f'brine_f{f}.png')
    base = Image.open(CACHE / 'brine_f0.png').convert('RGB')
    g2 = base.resize((base.width * 2, base.height * 2), Image.NEAREST)
    d = ImageDraw.Draw(g2)
    for x in range(W + 1):
        d.line([(x * CELL * 2, 0), (x * CELL * 2, g2.height)], fill=(255, 0, 255), width=1)
    for y in range(H + 1):
        d.line([(0, y * CELL * 2), (g2.width, y * CELL * 2)], fill=(255, 0, 255), width=1)
    for x in range(0, W, 3):
        for y in range(0, H, 3):
            d.text((x * CELL * 2 + 3, y * CELL * 2 + 2), f'{x},{y}', fill=(255, 255, 0))
    g2.save(CACHE / 'brine_grid_f0.png')

    # 4. raccords de colonnes (MSE sur toutes les frames), complets et par bande
    def col_seam(a, b, y0=0, y1=H):
        left = frames[:, y0 * CELL:(y1) * CELL, a * CELL + CELL - 1, :3]
        right = frames[:, y0 * CELL:(y1) * CELL, b * CELL, :3]
        return float(np.mean((left - right) ** 2))

    def row_seam(a, b, x0=0, x1=W):
        top = frames[:, a * CELL + CELL - 1, x0 * CELL:(x1) * CELL, :3]
        bottom = frames[:, b * CELL, x0 * CELL:(x1) * CELL, :3]
        return float(np.mean((top - bottom) ** 2))

    report['col_seams_full'] = [round(col_seam(x, x + 1), 1) for x in range(W - 1)]
    report['row_seams_full'] = [round(row_seam(y, y + 1), 1) for y in range(H - 1)]

    # bandes utiles (affinées après lecture de la carte) — valeurs par paire (a, b)
    bands = {'wall_top_rows_0_7': (0, 8), 'sea_bottom_rows_13_20': (13, 21)}
    report['col_seam_matrix'] = {}
    for name, (y0, y1) in bands.items():
        report['col_seam_matrix'][name] = {'rows': [y0, y1 - 1],
                                           'matrix': [[round(col_seam(a, b, y0, y1), 1) for b in range(W)] for a in range(W)]}
    report['row_seam_matrix'] = {}
    for name, (x0, x1) in {'left_sea_cols_0_12': (0, 13), 'right_cols_13_26': (13, 27)}.items():
        report['row_seam_matrix'][name] = {'cols': [x0, x1 - 1],
                                           'matrix': [[round(row_seam(a, b, x0, x1), 1) for b in range(H)] for a in range(H)]}

    # 5. déduplication des flipbooks (cellule = séquence de 15 payloads)
    seqs = {}
    for x in range(W):
        for y in range(H):
            key = tuple(sheet.payload_id(tx, ty) for _, tx, ty in cell_frames(tiles[x][y]))
            seqs.setdefault(key, []).append([x, y])
    report['distinct_flipbooks'] = len(seqs)
    report['flipbook_reuse_over2'] = {k[0] + f'..x{len(v)}': v[:8] for k, v in seqs.items() if len(v) > 2}

    (HERE / 'analyse.json').write_text(json.dumps(report, ensure_ascii=False, indent=1))
    print(json.dumps(report['animation'], ensure_ascii=False))
    print('col seams full :', report['col_seams_full'])
    print('row seams full :', report['row_seams_full'])
    print('distinct flipbooks :', report['distinct_flipbooks'])
    print('carte obstacles (x->, y vers le bas) :')
    for y in range(H):
        print(' ', ' '.join(free_ascii_col[y] for free_ascii_col in [free_ascii]) if False else free_ascii[y])


if __name__ == '__main__':
    main()
