#!/usr/bin/env python3
"""Reverie Town — quadrant Nord-Ouest (RVT_NO) : plateau haut à l'ouest, terrasses natives descendant vers
l'est (T0..T7 verbatim), mur principal avec escalier, porte et cascade, village en contrebas.
123 x 99 tuiles de 8 px = 984 x 792 px (41 x 33 cases de 24 px).
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from assemble import Scene, T, place_object, place_animated, sand_tile_mask, blit_masked, dark_tile_mask  # noqa: E402

W, H = 123, 99
R0 = 8            # couronne du plateau haut (ouest) : bloc T0
R7 = R0 + 28      # couronne du mur principal (niveau T7) = 36 ; pied du mur rangée 48


def build():
    s = Scene('RVT_NO', W, H)
    s.layer('sol'); s.layer('falaises'); s.layer('anim', phases=4); s.layer('objets')
    s.grass_fill('sol', 0, 0, W, H, seed=23)

    # --- 01 falaises -------------------------------------------------------------------------------------
    col = s.face(0, R0, 12, 'face_c', 3)                     # 0-11 : face du plateau haut jusqu'au bord ouest
    # terrasses descendantes natives T0..T7 sans le bord gauche de T0 (le plateau continue vers l'ouest)
    s.blit('falaises', 'Metano_Town_Cliffs', 59, 26, 31, 42, col, R0 - 2)   # tx 59-89, ty 26-67
    col += 31                                                 # 43
    col = s.face(col, R7, 19, 'face_c', 0)                    # 43-61
    col = s.module('escalier', col, R7)                       # 62-74
    col = s.module('face_b', col, R7)                         # 75-83
    col = s.module('porte', col, R7)                          # 84-93
    col = s.module('face_a', col, R7)                         # 94-95
    col = s.module('cascade_statique', col, R7)               # 96-103
    col = s.face(col, R7, 19, 'face_c', 0)                    # 104-122
    assert col == W, col

    # --- 02 anim : cascade animée + mare ------------------------------------------------------------------
    place_animated(s, 'anim', 'cascade', 96, R7 - 3)
    place_animated(s, 'anim', 'mare', 96, R7 + 12)

    # --- 00 sol : chemins natifs du pied de l'escalier ouest (tx 92-100), fenêtre Base x 224..1064, y 544..952
    # décalage : tx 92 -> col 64 (dx = -28), rangée 68 -> 48 (dy = -20)
    m = sand_tile_mask(224, 544, 1064, 952, keep_seed=(772, 556))
    m &= ~dark_tile_mask(224, 544, 1064, 952)
    blit_masked(s, 'sol', 'Metano_Town_Base', 224, 544, m, 28 - 28, 68 - 20)

    # --- 03 objets ---------------------------------------------------------------------------------------
    trees = [  # plateau haut et terrasses
             ('arbre_a', 0, 0), ('arbre_g', 12, 0), ('arbre_b', 26, 0), ('arbre_72', 40, 4), ('arbre_c', 52, 10),
             ('arbre_d', 66, 8), ('arbre_f', 80, 12), ('arbre_e', 94, 6), ('arbre_a', 108, 10), ('arbre_g', 114, 22),
             ('arbre_b', 50, 20), ('arbre_c', 72, 20), ('arbre_72', 30, 12),
             # lisière est
             ('arbre_d', 113, 50), ('arbre_a', 112, 60), ('arbre_f', 114, 70), ('arbre_e', 112, 80), ('arbre_g', 113, 90),
             ('arbre_b', 104, 56), ('arbre_c', 103, 88),
             # sud-ouest
             ('arbre_g', 0, 94), ('arbre_72', 20, 92), ('arbre_f', 2, 62)]
    for name, c, r in trees:
        place_object(s, 'objets', name, c, r, cutout=False)
    houses = [('dojo', 70, 54), ('maison_shellder', 46, 70), ('maison_turtwig', 24, 64), ('maison_dome', 30, 80),
              ('hutte_paille', 56, 82), ('etal_kecleon', 2, 72), ('maison_treecko', 90, 74),
              ('maison_chikorita', 100, 22)]
    for name, c, r in houses:
        place_object(s, 'objets', name, c, r)
    details = [('buisson_a', 46, 50), ('buisson_baie_a', 56, 52), ('souche_a', 78, 50), ('panneau', 60, 56),
               ('tonneau', 66, 72), ('barriere', 62, 72), ('table_ronde', 76, 84), ('table_tasses', 84, 88),
               ('foin_a', 60, 66), ('foin_b', 64, 70), ('souche_grande', 34, 92), ('boite_lettres', 62, 76),
               ('seaux', 88, 70), ('buisson_d', 104, 50), ('buisson_baie_c', 108, 66), ('buisson_e', 8, 46),
               ('buisson_f', 40, 88), ('buisson_baie_d', 96, 96), ('buissons_rangee', 30, 96),
               # plateau
               ('buisson_b', 6, 4), ('buisson_baie_b', 20, 5), ('souche_b', 60, 26), ('buisson_c', 86, 26),
               ('barriere', 106, 26), ('buisson_baie_a', 44, 24)]
    for name, c, r in details:
        place_object(s, 'objets', name, c, r, cutout=False)
    return s


if __name__ == '__main__':
    s = build()
    n = s.verify()
    out = Path(__file__).resolve().parents[2] / 'exports/reverie_town_v1/RVT_NO'
    s.export(out, 'RVT_NO')
    print(f'RVT_NO : {n} tuiles vérifiées, export -> {out}')
