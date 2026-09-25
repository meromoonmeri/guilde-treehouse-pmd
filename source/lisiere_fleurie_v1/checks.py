"""Contrôles de composition (occlusion, chevauchements, cellules) partagés par build et verify."""
from __future__ import annotations

import numpy as np

from modules import TREE_TRUNK_OFFSET


def cells(x, y, w, h):
    return {(cx, cy) for cx in range(x // 8, (x + w + 7) // 8) for cy in range(y // 8, (y + h + 7) // 8)}


def footprint(mods, sheets, kind, name, x, y):
    """Masque plein-carte (bool) et cellules 8x8 d'un élément posé."""
    if kind == 'flower':
        a = sheets['Vast_Steppe_Flower_Animations'][0:24, 0:72, 3] > 0
        mask = a[:, 0:24] | a[:, 24:48] | a[:, 48:72]   # union des 3 poses
    else:
        mask = mods[name].mask
    return mask, cells(x, y, mask.shape[1], mask.shape[0])


def layout_problems(layout, out, mods, sheets):
    W, H = layout['size']
    canopy = out['canopees'].rgba[..., 3] > 0
    cliff = out['corniche'].rgba[..., 3] > 0
    probs = []
    placed = []
    for name, x, y in layout['small']:
        placed.append(('small', name, x, y))
    for name, x, y in layout['rocks']:
        placed.append(('rock', name, x, y))
    for x, y, clock in layout['flowers']:
        placed.append(('flower', 'fleur', x, y))
        if clock not in (8, 10, 14):
            probs.append(f'cadence non native {clock} en {(x, y)}')
    for x, y in layout['trees']:
        placed.append(('trunk', 'tronc', x + TREE_TRUNK_OFFSET[0], y + TREE_TRUNK_OFFSET[1]))
    occupied = {}
    for kind, name, x, y in placed:
        mask, cs = footprint(mods, sheets, kind, name, x, y)
        h, w = mask.shape
        ys, xs = np.nonzero(mask)
        ty, tx = ys + y, xs + x
        ok = (ty >= 0) & (ty < H) & (tx >= 0) & (tx < W)
        ty, tx = ty[ok], tx[ok]
        if kind != 'trunk':
            if len(ty) < mask.sum():
                probs.append(f'{name} {(x, y)} coupé par le bord')
            hid = canopy[ty, tx].mean() if len(ty) else 1
            if hid > 0:
                probs.append(f'{name} {(x, y)} caché à {hid:.0%} sous les canopées')
        if cliff[ty, tx].any():
            probs.append(f'{name} {(x, y)} déborde sur la corniche ({int(cliff[ty, tx].sum())} px)')
        if kind == 'trunk':
            continue   # les troncs peuvent se chevaucher entre eux (forêt dense, ordre du peintre)
        for c in cs:
            if c in occupied:
                probs.append(f'{name} {(x, y)} partage la cellule {c} avec {occupied[c]}')
            occupied[c] = (name, x, y)
    # Les éléments bas ne doivent pas être recouverts par un tronc (pixels opaques de Objects).
    trunk = np.zeros((H, W), bool)
    for x, y in layout['trees']:
        tx0, ty0 = x + TREE_TRUNK_OFFSET[0], y + TREE_TRUNK_OFFSET[1]
        m = mods['tronc'].mask
        ys, xs = np.nonzero(m)
        ty, tx = ys + ty0, xs + tx0
        ok = (ty >= 0) & (ty < H) & (tx >= 0) & (tx < W)
        trunk[ty[ok], tx[ok]] = True
    for kind, name, x, y in placed:
        if kind in ('small', 'flower', 'rock'):
            mask, _ = footprint(mods, sheets, kind, name, x, y)
            ys, xs = np.nonzero(mask)
            ty, tx = ys + y, xs + x
            ok = (ty >= 0) & (ty < H) & (tx >= 0) & (tx < W)
            if trunk[ty[ok], tx[ok]].any():
                probs.append(f'{name} {(x, y)} chevauche un tronc/ombre')
    return probs
