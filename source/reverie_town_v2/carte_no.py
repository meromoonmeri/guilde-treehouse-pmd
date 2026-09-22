#!/usr/bin/env python3
"""Reverie Town v2 — quadrant Nord-Ouest (RVT2_NO) : vrai plateau de coin nord-ouest.

Le plateau occupe le nord-ouest et NE touche PAS le bord est : son côté est est visible. Comme la feuille native
Métano n'a aucun bord orienté est, ce côté utilise la feuille MIROIR (option « comme CLIFF MIROR » choisie par
l'utilisateur) : montée en escalier miroir (T7->T5->T3 retournés), bord droit clair miroir et liseré est miroir.
Tout le reste est natif : face haute depuis le bord ouest, descente native T3->T5->T7, mur principal (couronne
rangée 30) avec escalier, porte, cascade animée. Bande est de terrain bas (cols 104-122) avec la route nord native.
123 x 99 tuiles de 8 px = 984 x 792 px (41 x 33 cases).
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'reverie_town_v1'))
from assemble import Scene, place_object, place_animated, sand_tile_mask, blit_masked, dark_tile_mask  # noqa: E402

W, H = 123, 99
R3 = 14   # couronne du niveau haut (ouest et est du plateau)
R7 = 30   # couronne du mur principal


def place_objects(s):
    """Objets natifs (Metano_Town_Objects) : arbres propres, bâtiments (découpe automatique), détails propres."""
    trees = [  # plateau haut, lisière est (à cheval sur le bord), sud
             ('arbre_a', 0, 0), ('arbre_g', 14, 2), ('arbre_b', 30, 0), ('arbre_c', 46, 3), ('arbre_d', 62, 0),
             ('arbre_72', 74, 0), ('arbre_f', 22, 14), ('arbre_b', 56, 16), ('arbre_g', 70, 14),
             ('arbre_c', 117, 0), ('arbre_a', 117, 10), ('arbre_d', 117, 20), ('arbre_b', 117, 30),
             ('arbre_g', 117, 56), ('arbre_f', 117, 66), ('arbre_a', 117, 76), ('arbre_c', 117, 86),
             ('arbre_d', 2, 60), ('arbre_a', 0, 92), ('arbre_g', 20, 92), ('arbre_e', 60, 92), ('arbre_b', 96, 90),
             ('arbre_c', 92, 64)]
    for name, c, r in trees:
        place_object(s, 'objets', name, c, r, cutout=False)
    houses = [('dojo', 74, 50), ('maison_shellder', 36, 46), ('maison_turtwig', 22, 60), ('maison_dome', 30, 80),
              ('hutte_paille', 56, 82), ('etal_kecleon', 2, 70), ('maison_treecko', 90, 74),
              ('maison_chikorita', 34, 12), ('tente', 84, 3)]
    for name, c, r in houses:
        place_object(s, 'objets', name, c, r)
    details = [('buisson_a', 32, 43), ('buisson_baie_a', 62, 44), ('souche_a', 100, 46), ('panneau', 28, 43),
               ('tonneau', 52, 60), ('barriere', 62, 70), ('table_ronde', 76, 84), ('table_tasses', 84, 88),
               ('foin_a', 60, 60), ('foin_b', 64, 64), ('souche_grande', 34, 92), ('boite_lettres', 62, 76),
               ('seaux', 88, 70), ('buisson_d', 96, 44), ('buisson_baie_c', 108, 66), ('buisson_e', 8, 42),
               ('buisson_f', 40, 88), ('buisson_baie_d', 96, 96), ('buissons_rangee', 30, 96), ('caisses', 70, 60),
               ('buisson_baie_b', 72, 44), ('buisson_c', 84, 44),
               # plateau
               ('buisson_b', 6, 8), ('buisson_baie_b', 20, 5), ('souche_b', 60, 26), ('buisson_c', 86, 26),
               ('barriere', 66, 22), ('buisson_baie_a', 48, 24), ('buisson_d', 96, 8), ('buisson_f', 12, 24),
               ('buisson_e', 100, 2), ('buisson_baie_c', 80, 26)]
    for name, c, r in details:
        place_object(s, 'objets', name, c, r, cutout=False)


def build():
    s = Scene('RVT2_NO', W, H)
    s.layer('sol'); s.layer('falaises'); s.layer('anim', phases=4); s.layer('objets')
    s.grass_fill('sol', 0, 0, W, H, seed=23)

    # --- 01 falaises ---------------------------------------------------------------------------------------
    col = s.face(0, R3, 6, 'face_c', 4)                         # 0-5 : face haute depuis le bord ouest
    s.blit('falaises', 'Metano_Town_Cliffs', 81, 40, 11, 28, col, R3)   # 6-16 : descente native T3->T5->T7
    col += 11                                                   # 17
    col = s.module('escalier', col, R7)                         # 17-29
    col = s.module('face_b', col, R7)                           # 30-38
    col = s.module('porte', col, R7)                            # 39-48
    col = s.module('face_a', col, R7)                           # 49-50
    col = s.module('cascade_statique', col, R7)                 # 51-58
    col = s.face(col, R7, 22, 'face_c', 0)                      # 59-80
    # montée MIROIR (feuille RVT_Cliffs_Miroir) : miroir des colonnes natives 81..91, mêmes rangées
    col = s.mirror_blit(81, 91, 40, 67, col, R3)                # 81-91
    col = s.face(col, R3, 10, 'face_c', 2)                      # 92-101 : face haute (native)
    col = s.module('bord_droit_clair_miroir', col, R3)          # 102-103 : extrémité droite (miroir)
    s.rim_east(103, 0, R3 - 1)                                  # liseré est (miroir) rangées 0..12
    assert col == 104
    # cols 104-122 : bande est de terrain bas

    # --- 02 anim : cascade (4 images natives) + mare native au pied ---------------------------------------
    place_animated(s, 'anim', 'cascade', 51, R7 - 3)
    place_animated(s, 'anim', 'mare', 51, R7 + 12)

    # --- 00 sol : chemins natifs relocalisés ------------------------------------------------------------
    # a) route nord native (Base tuiles 26-47 x 0-46) dans la bande est : cols 108-129 (le virage sort par
    #    le bord est), dy = +6 ; rangées 0-5 = rangées natives 0-5 (bord de carte).
    m = sand_tile_mask(208, 0, 384, 376, keep_seed=(250, 100))
    m &= ~dark_tile_mask(208, 0, 384, 376)
    blit_masked(s, 'sol', 'Metano_Town_Base', 208, 0, m, 26 + 82, 6)
    blit_masked(s, 'sol', 'Metano_Town_Base', 208, 0, m[:6], 26 + 82, 0)
    # b) chemin natif du pied de l'escalier ouest (Base x 224-1064, y 544-952) : planches tx 92 -> col 19
    m = sand_tile_mask(224, 544, 1064, 952, keep_seed=(772, 556))
    m &= ~dark_tile_mask(224, 544, 1064, 952)
    blit_masked(s, 'sol', 'Metano_Town_Base', 224, 544, m, 28 - 73, 68 - 26)

    # --- 03 objets -------------------------------------------------------------------------------------
    place_objects(s)
    return s


if __name__ == '__main__':
    s = build()
    n = s.verify()
    out = Path(__file__).resolve().parents[2] / 'exports/reverie_town_v2/RVT2_NO'
    s.export(out, 'RVT2_NO')
    print(f'RVT2_NO : {n} tuiles vérifiées, export -> {out}')
