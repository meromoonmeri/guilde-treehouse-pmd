#!/usr/bin/env python3
"""Reverie Town — quadrant Nord-Est (RVT_NE) : plateau au nord, terrasses natives montant vers l'est,
mur principal composé avec le kit (porte, cascade animée, escalier), village en contrebas.
123 x 99 tuiles de 8 px = 984 x 792 px = 41 x 33 cases de 24 px (même format que cliffdaytest.rsground).
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from assemble import Scene, T, place_object, place_animated, sand_tile_mask, blit_masked, river_animation, dark_tile_mask  # noqa: E402

W, H = 123, 99
R = 26  # rangée de couronne du mur principal (ligne de couronne y = 8*26+5 = 213 px)


def build():
    s = Scene('RVT_NE', W, H)
    s.layer('sol'); s.layer('falaises'); s.layer('anim', phases=4); s.layer('objets')

    # --- 00 sol : herbe native partout (plateau et contrebas) ---------------------------------------------
    s.grass_fill('sol', 0, 0, W, H, seed=11)

    # --- 01 falaises : bord ouest + bloc composé + course native porte->terrasses ------------------------
    col = 37
    s.rim_west(col, 0, R - 1)                      # liseré ouest du plateau, rangées 0..24
    col = s.module('bord_gauche', col, R)          # 37-38
    col = s.face(col, R, 9, 'face_c', 0)           # 39-47 face plate
    col = s.module('cascade_statique', col, R)     # 48-55 cascade (image fixe native, animée par 02)
    col = s.module('face_b', col, R)               # 56-64
    col = s.module('porte', col, R)                # 65-74 porte de grotte
    col = s.face(col, R, 10, 'face_c', 9)          # 75-84
    col = s.module('escalier', col, R)             # 85-97 escalier de bois
    s.blit('falaises', 'Metano_Town_Cliffs', 164, R, 1, 12, col, R); col += 1   # 98 face native tx164
    # terrasses montantes natives U1..U3 (macro C), calées : tx165 -> col 99, ty39 -> rangée 9
    s.blit('falaises', 'Metano_Town_Cliffs', 165, 39, 24, 29, col, R - 17)
    assert col + 24 == W

    # --- 02 anim : cascade animée (4 images natives), mare au pied, rivière/étang animés -----------------
    place_animated(s, 'anim', 'cascade', 48, R - 3)   # images 64x120 calées sur la cascade statique
    place_animated(s, 'anim', 'mare', 48, 38)          # mare native (3 images, période 3 sur 4 phases)

    # --- 00 sol (suite) : chemins natifs relocalisés (couloirs de sable de la Base, tuiles entières) -------
    # Chemin natif du pied de l'escalier est (feuille x 1224-1295, y 544) vers le sud : fenêtre Base
    # x 1064..1512, y 544..1032 posée avec le décalage (-66,-30) tuiles, composante connexe du pied d'escalier.
    m = sand_tile_mask(1064, 544, 1512, 1032, keep_seed=(1256, 556))
    m &= ~dark_tile_mask(1064, 544, 1512, 1032)   # écarte les tuiles à pixels très sombres (objet isolé de la Base)
    blit_masked(s, 'sol', 'Metano_Town_Base', 1064, 544, m, 133 - 66, 68 - 30 + 0)

    # --- 03 objets : forêt de bordure, maisons, arbres, détails --------------------------------------------
    # Arbres propres (tuiles natives entières). Lisière ouest, bosquets du plateau, coin sud-est.
    trees = [('arbre_a', 0, 0), ('arbre_b', 9, 5), ('arbre_g', 0, 9), ('arbre_c', 10, 14), ('arbre_d', 1, 19),
             ('arbre_f', 11, 24), ('arbre_a', 3, 29), ('arbre_e', 12, 34), ('arbre_g', 0, 39), ('arbre_b', 10, 44),
             ('arbre_c', 2, 49), ('arbre_d', 12, 54), ('arbre_a', 0, 59), ('arbre_f', 9, 64), ('arbre_e', 1, 69),
             ('arbre_g', 11, 74), ('arbre_b', 2, 79), ('arbre_c', 12, 84), ('arbre_d', 0, 89), ('arbre_a', 10, 93),
             ('arbre_72', 20, 2), ('arbre_e', 26, 12), ('arbre_f', 20, 26),
             # bosquets sur le plateau
             ('arbre_c', 42, 0), ('arbre_g', 58, 3), ('arbre_a', 74, 0), ('arbre_d', 90, 1), ('arbre_72', 106, 0),
             ('arbre_b', 66, 13), ('arbre_f', 113, 4), ('arbre_e', 82, 14),
             # sud-est et sud
             ('arbre_a', 113, 55), ('arbre_g', 112, 92), ('arbre_c', 22, 92), ('arbre_b', 30, 40), ('arbre_d', 20, 48)]
    for name, c, r in trees:
        place_object(s, 'objets', name, c, r, cutout=False)
    # Bâtiments (découpe automatique des taches de sable natives autour).
    houses = [('dojo', 40, 44), ('maison_shellder', 52, 60), ('maison_turtwig', 28, 58), ('maison_dome', 16, 74),
              ('maison_treecko', 38, 78), ('etal_kecleon', 91, 53), ('hutte_paille', 104, 76),
              ('maison_chikorita', 48, 8)]
    for name, c, r in houses:
        place_object(s, 'objets', name, c, r)
    # Détails propres.
    details = [('buisson_a', 44, 39), ('buisson_baie_a', 60, 40), ('buisson_c', 78, 40), ('buisson_baie_b', 82, 42),
               ('souche_a', 36, 42), ('panneau', 86, 44), ('tonneau', 68, 60), ('barriere', 60, 72),
               ('table_ronde', 60, 84), ('table_tasses', 60, 92), ('table_large', 100, 80), ('foin_a', 112, 66),
               ('foin_b', 116, 70), ('souche_grande', 20, 60), ('boite_lettres', 50, 72), ('seaux', 66, 66),
               ('buisson_d', 100, 42), ('buisson_baie_c', 110, 40), ('buisson_e', 38, 68), ('buisson_f', 30, 88),
               ('buisson_baie_d', 88, 74), ('buissons_rangee', 100, 94), ('souche_b', 116, 60),
               # plateau
               ('buisson_b', 40, 20), ('buisson_baie_c', 62, 22), ('souche_a', 70, 20), ('buisson_d', 96, 22),
               ('buisson_baie_a', 54, 18), ('barriere', 84, 20)]
    for name, c, r in details:
        place_object(s, 'objets', name, c, r, cutout=False)
    return s


if __name__ == '__main__':
    s = build()
    n = s.verify()
    out = Path(__file__).resolve().parents[2] / 'exports/reverie_town_v1/RVT_NE'
    files = s.export(out, 'RVT_NE')
    print(f'RVT_NE : {n} tuiles vérifiées, export -> {out}')
