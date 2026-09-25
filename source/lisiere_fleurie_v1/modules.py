"""Bibliothèque de modules natifs Vast Steppe (Halcyon 1522c7a8) pour « Lisière fleurie V1 ».

Tous les pixels proviennent des feuilles .tile natives décodées (alpha droit, alpha binaire vérifié).
Chaque module est une composante connexe complète isolée dans la feuille (masque exact), jamais une
mosaïque de fragments. Placement = translation par multiples de 8 px uniquement : aucune mise à l'échelle,
aucune rotation, aucun miroir, aucune recoloration.
"""
from __future__ import annotations

import hashlib
import json
import sys
from dataclasses import dataclass
from pathlib import Path

import numpy as np
from scipy import ndimage

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
REF = ROOT / 'source/amp_plains_fleurie_v1/references'
sys.path.insert(0, str(ROOT / 'tools'))
import pmdo_tiles as T  # noqa: E402

SHEETS = ['Vast_Steppe_Base', 'Vast_Steppe_Cliifs', 'Vast_Steppe_Objects_Under',
          'Vast_Steppe_Objects', 'Vast_Steppe_Fringe', 'Vast_Steppe_Flower_Animations']
SHEET_ID = {n: i for i, n in enumerate(SHEETS)}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_sheets() -> dict[str, np.ndarray]:
    out = {}
    for n in SHEETS:
        size, atlas, _ = T.tile_to_atlas(REF / f'{n}.tile')
        assert size == 8
        a = np.array(atlas)
        assert not ((a[..., 3] > 0) & (a[..., 3] < 255)).any(), n  # alpha binaire natif
        out[n] = a
    return out


@dataclass
class Module:
    name: str
    sheet: str
    sx: int          # origine tuile (multiple de 8) dans la feuille
    sy: int
    mask: np.ndarray  # bool (h, w) : pixels appartenant au module
    note: str = ''

    @property
    def w(self):
        return self.mask.shape[1]

    @property
    def h(self):
        return self.mask.shape[0]


def component(sheets, name, sheet, bx, by, note=''):
    """Composante connexe (8-connexité) dont la boîte commence en (bx, by) dans la feuille."""
    a = sheets[sheet]
    lab, _ = ndimage.label(a[..., 3] > 0, structure=np.ones((3, 3)))
    ids = [i + 1 for i, sl in enumerate(ndimage.find_objects(lab))
           if sl[1].start == bx and sl[0].start == by]
    assert len(ids) == 1, (name, sheet, bx, by, ids)
    sl = ndimage.find_objects(lab)[ids[0] - 1]
    x0, y0 = sl[1].start // 8 * 8, sl[0].start // 8 * 8
    x1, y1 = -(-sl[1].stop // 8) * 8, -(-sl[0].stop // 8) * 8
    mask = lab[y0:y1, x0:x1] == ids[0]
    return Module(name, sheet, x0, y0, mask, note)


def build_modules(sheets):
    m = {}
    # Instances choisies = exemplaires complets (non coupés par un bord), hash identiques aux autres copies.
    m['canopee'] = component(sheets, 'canopee', 'Vast_Steppe_Fringe', 344, 104, 'canopée 126x72, 4 copies natives identiques')
    m['tronc'] = component(sheets, 'tronc', 'Vast_Steppe_Objects', 368, 159, 'tronc + ombre d’herbe 80x41, 6 copies natives identiques')
    m['rocher_a'] = component(sheets, 'rocher_a', 'Vast_Steppe_Objects', 48, 80, 'gros rocher, galet à droite')
    m['rocher_b'] = component(sheets, 'rocher_b', 'Vast_Steppe_Objects', 320, 64, 'gros rocher, galet à gauche')
    m['touffe_a'] = component(sheets, 'touffe_a', 'Vast_Steppe_Objects_Under', 424, 16, 'touffe sombre A')
    m['touffe_b'] = component(sheets, 'touffe_b', 'Vast_Steppe_Objects_Under', 48, 32, 'touffe sombre B')
    m['galet_a'] = component(sheets, 'galet_a', 'Vast_Steppe_Objects_Under', 40, 120, 'galet plat A')
    m['galet_b'] = component(sheets, 'galet_b', 'Vast_Steppe_Objects_Under', 112, 304, 'galet plat B')
    return m


# Arbre natif : canopée (Fringe, au-dessus du joueur) + tronc (Objects), décalage natif constant
# mesuré sur les 4 arbres complets de vast_steppe_entrance : tronc = canopée + (24, 48) en origines tuile.
TREE_TRUNK_OFFSET = (24, 48)

# Fleurs animées natives : bloc 3x3 tuiles, poses en colonnes 0-2 / 3-5 / 6-8 de la feuille 72x24,
# séquence native des clés [0, 1, 0, 2], cadences natives 8, 10 et 14 frames de jeu.
FLOWER_SEQUENCE = [0, 1, 0, 2]
FLOWER_CLOCKS = [8, 10, 14]


def flower_pose(sheets, pose):
    a = sheets['Vast_Steppe_Flower_Animations']
    return a[0:24, pose * 24:(pose + 1) * 24]


# Colonnes du module corniche + couloir + sortie lumineuse (feuille Cliifs, lignes 0..279).
# La bande de corniche est cyclique : raccord natif sans couture entre x=511 et x=0 (mesuré).
CLIFF_H = 280
CORRIDOR = (152, 360)     # colonnes natives contenant les parois du couloir et la sortie
PURE_RIGHT = (360, 512)   # corniche pure à droite du couloir
PURE_LEFT = (0, 152)      # corniche pure à gauche du couloir


def cliff_columns(width, corridor_x):
    """Colonne native pour chaque colonne de destination (bande cyclique, translation seule)."""
    left = corridor_x
    right = width - corridor_x - (CORRIDOR[1] - CORRIDOR[0])
    ring = (PURE_RIGHT[1] - PURE_RIGHT[0]) + (PURE_LEFT[1] - PURE_LEFT[0])  # 304 px de corniche pure
    assert 0 <= left <= ring and 0 <= right <= ring, (left, right)
    assert corridor_x % 8 == 0 and width % 8 == 0
    cols = []
    for i in range(left):                      # finit sur le bord gauche du couloir (col. native 151)
        cols.append((CORRIDOR[0] - left + i) % 512)
    cols += list(range(CORRIDOR[0], CORRIDOR[1]))
    for i in range(right):                     # commence après le couloir (col. native 360)
        cols.append((CORRIDOR[1] + i) % 512)
    cols = np.array(cols)
    # Contrôle : on ne traverse jamais le couloir natif dans les prolongements.
    ext = np.concatenate([cols[:left], cols[left + CORRIDOR[1] - CORRIDOR[0]:]])
    assert not ((ext >= CORRIDOR[0]) & (ext < CORRIDOR[1])).any()
    return cols


if __name__ == '__main__':
    s = load_sheets()
    mods = build_modules(s)
    print(json.dumps({k: [v.sheet, v.sx, v.sy, v.w, v.h, int(v.mask.sum())] for k, v in mods.items()}, indent=1))
