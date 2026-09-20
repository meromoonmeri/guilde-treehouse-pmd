#!/usr/bin/env python3
"""Deuxième passe : modules répétables pour les extensions (voir ANALYSE.md).

    .venv/bin/python source/plage_cote_v2/analyse2.py  -> analyse2.json

« Bande » = tranche de cellules comparée entre deux colonnes (ou deux rangées)
sur TOUTES les frames : MSE RGB 0-255 entre les deux strips de pixels.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from tilelib import CELL, HERE, REF, TileSheet, composite, load_ground  # noqa: E402

W, H, FRAMES = 27, 21, 15


def main():
    sheet = TileSheet(REF / 'EoSO__Brine_Cave_Entrance.tile')
    ground = load_ground(REF / 'EoSO__Brine_Cave_Entrance.rsground')['Object']
    frames = np.stack([np.asarray(composite(ground, {'Brine Cave Entrance': sheet}, f)) for f in range(FRAMES)]).astype(np.float64)

    def colstrip(a, b, y0, y1):
        u = frames[:, y0 * CELL:(y1) * CELL, a * CELL:(a + 1) * CELL, :3]
        v = frames[:, y0 * CELL:(y1) * CELL, b * CELL:(b + 1) * CELL, :3]
        return float(np.mean((u - v) ** 2))

    def rowstrip(a, b, x0, x1):
        u = frames[:, a * CELL:(a + 1) * CELL, x0 * CELL:(x1) * CELL, :3]
        v = frames[:, b * CELL:(b + 1) * CELL, x0 * CELL:(x1) * CELL, :3]
        return float(np.mean((u - v) ** 2))

    report = {}

    def best_pairs(fn, rng, n=6, exclude_self=True):
        pairs = []
        for a in rng:
            for b in rng:
                if a == b:
                    continue
                pairs.append((round(fn(a, b), 1), a, b))
        pairs.sort()
        return pairs[:n]

    # 1. colonnes : auto-similarité sur toute la hauteur (module d'extension droite)
    report['col_full_matrix'] = [[round(colstrip(a, b, 0, H), 1) for b in range(W)] for a in range(W)]
    report['col_full_best'] = best_pairs(lambda a, b: colstrip(a, b, 0, H), range(W))
    # colonnes pures mer (rangs 17-21) et rive+mer (16-21)
    report['col_sea1719_best'] = best_pairs(lambda a, b: colstrip(a, b, 17, H), range(W))
    report['col_shore16_best'] = best_pairs(lambda a, b: colstrip(a, b, 16, H), range(W))
    # colonnes mur seul (rangs 0-5, hors emprise de l'embouchure 7-13)
    wall_cols = list(range(0, 7)) + list(range(14, W))
    report['col_wall_best'] = best_pairs(lambda a, b: colstrip(a, b, 0, 6), wall_cols)
    # colonnes sol seul (rangs 9-14)
    report['col_floor_best'] = best_pairs(lambda a, b: colstrip(a, b, 9, 15), range(7, 25))

    # 2. rangées : auto-similarité (modules d'extension hauteur)
    report['row_full_matrix'] = [[round(rowstrip(a, b, 0, W), 1) for b in range(H)] for a in range(H)]
    report['row_full_best'] = best_pairs(lambda a, b: rowstrip(a, b, 0, W), range(H))
    report['row_sea_best'] = best_pairs(lambda a, b: rowstrip(a, b, 0, W), range(17, H))
    report['row_wall_best'] = best_pairs(lambda a, b: rowstrip(a, b, 0, W), range(0, 5))
    report['row_floor_best'] = best_pairs(lambda a, b: rowstrip(a, b, 7, 25), range(9, 16))

    # 3. coutures de boucle de blocs de colonnes candidats (extension droite) :
    #    bloc [p, q) recollé sur lui-même : derniere colonne q-1 -> premiere p
    r = json.loads((HERE / 'analyse.json').read_text())
    seam = r['col_seams_full']

    def loop(p, q):
        return seam[q - 1]  # q-1 -> q serait la suite ; q-1 -> p est la boucle, mesuree plus bas

    blocks = []
    frames_col = None  # reuse colstrip on wrap: compare column q-1 vs p directly via strips
    for width in (4, 5, 6, 7, 8, 10, 12, 14):
        best = None
        for p in range(13, W - width + 1):
            q = p + width
            v = colstrip(q - 1, p, 0, H)
            if best is None or v < best[0]:
                best = (round(v, 1), p, q)
        blocks.append({'width': width, 'loop_mse': best[0], 'block': [best[1], best[2]]})
    report['right_extension_blocks'] = sorted(blocks, key=lambda x: x['loop_mse'])

    # 4. pareil pour un bloc de rangées de mer inséré dans la mer profonde (17-20)
    seamr = r['row_seams_full']
    rblocks = []
    for width in (1, 2, 3, 4):
        best = None
        for p in range(17, H - width + 1):
            q = p + width
            v = rowstrip(q - 1, p, 0, W)
            if best is None or v < best[0]:
                best = (round(v, 1), p, q)
        rblocks.append({'width': width, 'loop_mse': best[0], 'block': [best[1], best[2]]})
    report['sea_row_blocks'] = sorted(rblocks, key=lambda x: x['loop_mse'])

    (HERE / 'analyse2.json').write_text(json.dumps(report, ensure_ascii=False, indent=1))
    for k in ('col_full_best', 'col_sea1719_best', 'col_shore16_best', 'col_wall_best', 'col_floor_best',
              'row_full_best', 'row_sea_best', 'row_wall_best', 'row_floor_best'):
        print(k, report[k])
    print('right_extension_blocks', report['right_extension_blocks'])
    print('sea_row_blocks', report['sea_row_blocks'])


if __name__ == '__main__':
    main()
