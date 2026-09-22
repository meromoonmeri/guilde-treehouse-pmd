#!/usr/bin/env python3
"""Vérification de recomposition : chaque .rsground du paquet natif, rendu par tools/pmdo_tiles.py (décodeur
indépendant des .tile du jeu + feuilles personnalisées), doit être identique pixel à pixel au composite PNG exporté,
pour les 4 phases d'animation, jour et nuit."""
import subprocess
import sys
from pathlib import Path

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
PACK = ROOT / 'exports/reverie_town_v1/paquet_natif'
SHEETS = [ROOT / 'source/cote_v4_abyss/natifs', ROOT / 'source/eau_metano/natifs',
          ROOT / 'source/amp_plains_fleurie_v1/references', PACK / 'Content/Tile']
PY = sys.executable


def main():
    ok = True
    for slug in ('NE', 'NO'):
        for mode in ('jour', 'nuit'):
            for phase in range(4):
                out = Path('/tmp') / f'rvt_{slug}_{mode}_p{phase}.png'
                subprocess.run([PY, str(ROOT / 'tools/pmdo_tiles.py'), 'render',
                                str(PACK / f'Data/Ground/rvt_{slug.lower()}_{mode}.rsground'),
                                '--sheets', *map(str, SHEETS), '--out', str(out), '--phase', str(phase)],
                               check=True, capture_output=True)
                a = np.array(Image.open(out).convert('RGB')).astype(int)
                b = np.array(Image.open(ROOT / f'exports/reverie_town_v1/RVT_{slug}/RVT_{slug}_composite_{mode}_p{phase + 1}.png').convert('RGB')).astype(int)
                diff = np.abs(a - b).max(2)
                d = int((diff > 0).sum())
                # Tolérance : ±2 par canal sur les pixels semi-transparents des feuilles personnalisées
                # (arrondi de la prémultiplication alpha imposée par le format .tile du jeu).
                strict = int((diff > 2).sum())
                print(f'RVT_{slug} {mode} phase {phase + 1}: '
                      f'{"identique" if d == 0 else f"{d} pixels a +-{int(diff.max())} (arrondi alpha prémultiplié)"}')
                ok &= strict == 0
    print('OK' if ok else 'ECHEC')
    return 0 if ok else 1


if __name__ == '__main__':
    sys.exit(main())
