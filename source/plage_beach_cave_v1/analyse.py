#!/usr/bin/env python3
"""Mesures qui justifient le plan d'agrandissement (voir ANALYSE.md).

    .venv/bin/python source/plage_beach_cave_v1/analyse.py  -> analyse.json

Toutes les mesures portent sur le rendu composite de la carte EoSO `beach`
(17 frames). « Raccord » = erreur quadratique moyenne (MSE, RGB 0-255) entre
la dernière colonne (ou rangée) de pixels d'un bloc et la première colonne
(ou rangée) du bloc suivant.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from tilelib import CELL, HERE, REF, cell_frames, composite, load_ground, load_sheets, render_layer  # noqa: E402


def main():
    sheets = load_sheets()
    ground = load_ground(REF / 'EoSO__beach.rsground')['Object']
    frames = np.stack([np.asarray(composite(ground, sheets, f)) for f in range(17)]).astype(np.float64)  # 17,H,W,4
    W, H = 33, 16
    report = {'grid': [W, H], 'cell_px': CELL}

    # 1. animation : frames distinctes, rangées statiques
    distinct = len({frames[f].tobytes() for f in range(17)})
    static_rows = [y for y in range(7) if all(np.array_equal(frames[0, y * CELL:(y + 1) * CELL], frames[f, y * CELL:(y + 1) * CELL]) for f in range(17))]
    anim = next(layer for layer in ground['Layers'] if layer['Name'] == 'Anim')
    lengths = {len(cell_frames(t)) for col in anim['Tiles'] for t in col if cell_frames(t)}
    frame_len = {t['Layers'][0]['FrameLength'] for col in anim['Tiles'] for t in col if t['Layers']}
    report['animation'] = {'distinct_composite_frames': distinct, 'frames_per_cell': sorted(lengths), 'frame_length_ticks': sorted(frame_len),
                           'static_rows': static_rows, 'animated_rows': [y for y in range(7) if y not in static_rows]}

    # 2. raccords de colonnes existants et raccords de boucle de blocs candidats
    def col_seam(a, b):  # colonne a à gauche de colonne b
        left = frames[:, :, a * CELL + CELL - 1, :3]
        right = frames[:, :, b * CELL, :3]
        return float(np.mean((left - right) ** 2))

    existing = [col_seam(x, x + 1) for x in range(W - 1)]
    report['column_seams_original'] = {'median': float(np.median(existing)), 'max': float(np.max(existing)), 'values': [round(v, 1) for v in existing]}
    candidates = []
    for width in (8, 12, 16):
        for a in range(9, 25 - width + 1):
            b = a + width
            if b > 25:
                continue
            candidates.append({'block': [a, b], 'width': width, 'loop_seam': round(col_seam(b - 1, a), 1)})
    candidates.sort(key=lambda c: c['loop_seam'])
    report['column_block_candidates'] = candidates[:12]

    # 3. raccords de rangées du calque Back (sable), colonnes 5-27
    back = np.asarray(render_layer(next(l for l in ground['Layers'] if l['Name'] == 'Back'), sheets, 0)).astype(np.float64)
    c0, c1 = 5, 28

    def row_seam(a, b):
        top = back[a * CELL + CELL - 1, c0 * CELL:c1 * CELL, :3]
        bottom = back[b * CELL, c0 * CELL:c1 * CELL, :3]
        return float(np.mean((top - bottom) ** 2))

    rows = list(range(6, 13))
    report['back_row_seams'] = {'rows': rows, 'columns': [c0, c1 - 1], 'matrix': [[round(row_seam(a, b), 1) for b in rows] for a in rows]}
    sequences = {
        'original 7,8,9,10,11': [7, 8, 9, 10, 11],
        'choisie 7,8,9,9,9,9,9,10,11': [7, 8, 9, 9, 9, 9, 9, 10, 11],
        'alternance 7,8,9,8,9,8,9,10,11': [7, 8, 9, 8, 9, 8, 9, 10, 11],
        'rangee 8 repetee 7,8,8,8,8,8,9,10,11': [7, 8, 8, 8, 8, 8, 9, 10, 11],
    }
    report['back_row_sequences'] = {name: {'seams': [round(row_seam(s[i], s[i + 1]), 1) for i in range(len(s) - 1)]} for name, s in sequences.items()}
    for v in report['back_row_sequences'].values():
        v['max'] = max(v['seams'])

    # 4. période horizontale du sable (identité des cellules Back)
    back_layer = next(l for l in ground['Layers'] if l['Name'] == 'Back')['Tiles']
    sheet = sheets['D01P11A_layer1']
    periods = {}
    for y in (8, 9, 10):
        ids = [sheet.payload_id(*cell_frames(back_layer[x][y])[0][1:]) for x in range(c0, c1)]
        periods[y] = {p: sum(1 for i in range(len(ids) - p) if ids[i] == ids[i + p]) / max(1, len(ids) - p) for p in (4, 8, 12)}
    report['back_sand_period_match_ratio'] = periods

    (HERE / 'analyse.json').write_text(json.dumps(report, ensure_ascii=False, indent=1))
    print(json.dumps({k: report[k] for k in ('animation', 'column_seams_original')}, ensure_ascii=False)[:600])
    print('meilleurs blocs :', report['column_block_candidates'][:5])
    print('sequences :', report['back_row_sequences'])
    print('periodes :', periods)


if __name__ == '__main__':
    main()
