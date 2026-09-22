#!/usr/bin/env python3
"""Reverie Town v2 — quadrant Nord-Est (RVT2_NE), 100 % natif.

Plateau nord-est à contour en escalier : liseré ouest natif, bord gauche, face haute (couronne rangée 14),
descente native T3->T5->T7 (colonnes natives tx 81..91 verbatim, marches de 64 px), mur principal
(couronne rangée 30) avec cascade animée, porte, escalier, puis terrasses montantes natives U1..U3.
Bande ouest de terrain bas (cols 0-15) avec la route nord native de Métano (sortie nord), village au sud.
123 x 99 tuiles de 8 px = 984 x 792 px (41 x 33 cases).
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'reverie_town_v1'))
from assemble import Scene, place_object, place_animated, sand_tile_mask, blit_masked, dark_tile_mask  # noqa: E402

W, H = 123, 99
R3 = 14   # couronne du niveau haut (ouest du plateau) = ligne native y 8*14+5
R7 = 30   # couronne du mur principal (= R3 + 16 : marches natives 64 + 64 px)


def place_objects(s):
    """Objets natifs (Metano_Town_Objects) : arbres propres, bâtiments (découpe automatique), détails propres."""
    trees = [  # lisière ouest (arbres à cheval sur le bord), plateau haut, terrasses, sud
             ('arbre_a', -4, 0), ('arbre_g', -4, 10), ('arbre_b', -4, 20), ('arbre_c', -4, 30), ('arbre_d', -4, 40),
             ('arbre_72', -4, 50), ('arbre_f', -4, 60), ('arbre_e', -4, 70), ('arbre_a', -4, 80), ('arbre_g', -4, 90),
             ('arbre_c', 36, 0), ('arbre_g', 50, 2), ('arbre_a', 68, 0), ('arbre_d', 82, 2), ('arbre_72', 96, 0),
             ('arbre_e', 104, 3), ('arbre_f', 113, 6), ('arbre_b', 40, 16), ('arbre_c', 88, 14), ('arbre_g', 74, 18),
             ('arbre_d', 8, 58), ('arbre_a', 4, 68), ('arbre_b', 26, 90), ('arbre_c', 44, 92), ('arbre_e', 88, 60),
             ('arbre_g', 112, 64), ('arbre_a', 114, 92), ('arbre_f', 96, 94)]
    for name, c, r in trees:
        place_object(s, 'objets', name, c, r, cutout=False)
    houses = [('dojo', 20, 50), ('maison_shellder', 52, 48), ('maison_turtwig', 26, 68), ('maison_dome', 8, 82),
              ('maison_treecko', 44, 80), ('etal_kecleon', 93, 55), ('hutte_paille', 104, 78),
              ('maison_chikorita', 56, 12), ('tente', 21, 2)]
    for name, c, r in houses:
        place_object(s, 'objets', name, c, r)
    details = [('buisson_a', 54, 44), ('buisson_baie_a', 58, 43), ('buisson_c', 72, 44), ('buisson_baie_b', 92, 46),
               ('souche_a', 38, 46), ('panneau', 90, 44), ('tonneau', 48, 62), ('barriere', 66, 60),
               ('table_ronde', 62, 86), ('table_tasses', 78, 92), ('table_large', 96, 70), ('foin_a', 114, 72),
               ('foin_b', 118, 76), ('souche_grande', 14, 70), ('boite_lettres', 50, 68), ('seaux', 66, 66),
               ('buisson_d', 102, 45), ('buisson_baie_c', 114, 44), ('buisson_e', 40, 74), ('buisson_f', 32, 94),
               ('buisson_baie_d', 90, 82), ('buissons_rangee', 100, 96), ('souche_b', 116, 60), ('caisses', 30, 64),
               # plateau
               ('buisson_b', 46, 26), ('buisson_baie_c', 70, 26), ('souche_a', 78, 24), ('buisson_d', 96, 26),
               ('buisson_baie_a', 52, 20), ('barriere', 86, 24), ('buisson_e', 24, 10), ('buisson_baie_b', 30, 4),
               ('buisson_f', 108, 12), ('souche_b', 118, 2)]
    for name, c, r in details:
        place_object(s, 'objets', name, c, r, cutout=False)


def build():
    s = Scene('RVT2_NE', W, H)
    s.layer('sol'); s.layer('falaises'); s.layer('anim', phases=4); s.layer('objets')
    s.grass_fill('sol', 0, 0, W, H, seed=11)

    # --- 01 falaises ---------------------------------------------------------------------------------------
    col = 18
    s.rim_west(col, 0, R3 - 1)                                  # liseré ouest rangées 0..12
    col = s.module('bord_gauche', col, R3)                      # 18-19
    col = s.face(col, R3, 12, 'face_c', 0)                      # 20-31 face haute
    # descente native : fin de face T3 (tx 81) -> bloc T5 (82-84) -> raccord (85) -> début T7 (86-91)
    s.blit('falaises', 'Metano_Town_Cliffs', 81, 40, 11, 28, col, R3)   # cols 32-42, rangées 14..41
    col += 11                                                   # 43
    col = s.module('cascade_statique', col, R7)                 # 43-50
    col = s.module('face_b', col, R7)                           # 51-59
    col = s.module('porte', col, R7)                            # 60-69
    col = s.face(col, R7, 8, 'face_c', 9)                       # 70-77
    col = s.module('escalier', col, R7)                         # 78-90
    col = s.face(col, R7, 7, 'face_c', 0)                       # 91-97
    s.blit('falaises', 'Metano_Town_Cliffs', 164, 56, 1, 12, col, R7); col += 1   # 98 colonne native tx 164
    s.blit('falaises', 'Metano_Town_Cliffs', 165, 39, 24, 29, col, R7 - 17)       # 99-122 : U1..U3 natives
    assert col + 24 == W

    # --- 02 anim : cascade (4 images natives) + mare native au pied ---------------------------------------
    place_animated(s, 'anim', 'cascade', 43, R7 - 3)
    place_animated(s, 'anim', 'mare', 43, R7 + 12)

    # --- 00 sol : chemins natifs relocalisés ------------------------------------------------------------
    # a) route nord native de Métano (Base tuiles 26-47 x 0-46 : route verticale + amorce du virage), posée
    #    cols 6-27 avec dy = +6 pour que le virage vers l'est passe SOUS le pied du mur (rangée 42) et non
    #    derrière le bord gauche. Les 6 rangées du haut (0-5) reprennent les rangées natives 0-5 de la route
    #    (seule répétition de tuiles de la carte : 6 rangées de route droite, bord de carte).
    m = sand_tile_mask(208, 0, 384, 376, keep_seed=(250, 100))
    m &= ~dark_tile_mask(208, 0, 384, 376)
    blit_masked(s, 'sol', 'Metano_Town_Base', 208, 0, m, 26 - 20, 6)
    blit_masked(s, 'sol', 'Metano_Town_Base', 208, 0, m[:6], 26 - 20, 0)
    # b) chemin natif du pied de l'escalier est (Base x 1064-1512, y 544-1032), décalage escalier : (-73, -26)
    m = sand_tile_mask(1064, 544, 1512, 1032, keep_seed=(1256, 556))
    m &= ~dark_tile_mask(1064, 544, 1512, 1032)
    blit_masked(s, 'sol', 'Metano_Town_Base', 1064, 544, m, 133 - 73, 68 - 26)

    # --- 03 objets -------------------------------------------------------------------------------------
    place_objects(s)
    return s


if __name__ == '__main__':
    s = build()
    n = s.verify()
    out = Path(__file__).resolve().parents[2] / 'exports/reverie_town_v2/RVT2_NE'
    s.export(out, 'RVT2_NE')
    print(f'RVT2_NE : {n} tuiles vérifiées, export -> {out}')
