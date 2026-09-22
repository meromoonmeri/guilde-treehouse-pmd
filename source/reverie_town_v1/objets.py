"""Objets natifs Métano (rectangles pixel alignés 8 px dans Metano_Town_Objects / Metano_Town_Animation_Tileset).

PROPRES : le rectangle ne contient que l'objet -> tuiles natives entières (référençables telles quelles dans
le paquet natif). DÉCOUPÉS : le rectangle natif contient aussi des taches de sable ou des voisins ; seuls les
pixels de l'objet sont conservés (aucun pixel repeint), les tuiles concernées sont marquées 'découpe'.
"""
O = 'Metano_Town_Objects'
OBJETS = {
    # --- arbres ronds propres ---
    'arbre_72': (O, 1440, 240, 1512, 312),
    'arbre_a': (O, 272, 696, 352, 768),
    'arbre_b': (O, 760, 128, 840, 200),
    'arbre_c': (O, 888, 1000, 968, 1072),
    'arbre_d': (O, 904, 296, 984, 368),
    'arbre_e': (O, 976, 1072, 1056, 1144),
    'arbre_f': (O, 776, 1264, 856, 1344),
    'arbre_g': (O, 992, 160, 1072, 240),
    # --- buissons, souches, petits objets propres ---
    'buisson_a': (O, 56, 624, 80, 648),
    'buisson_b': (O, 512, 280, 536, 304),
    'buisson_c': (O, 704, 504, 728, 528),
    'buisson_d': (O, 912, 424, 936, 448),
    'buisson_e': (O, 1176, 488, 1200, 512),
    'buisson_f': (O, 1432, 392, 1456, 416),
    'buisson_baie_a': (O, 336, 1344, 360, 1368),
    'buisson_baie_b': (O, 424, 184, 448, 208),
    'buisson_baie_c': (O, 576, 88, 600, 112),
    'buisson_baie_d': (O, 1280, 952, 1304, 976),
    'souche_a': (O, 168, 528, 192, 552),
    'souche_b': (O, 304, 384, 328, 408),
    'souche_grande': (O, 376, 496, 424, 544),
    'panneau': (O, 744, 200, 768, 232),
    'tonneau': (O, 1192, 952, 1216, 984),
    'barriere': (O, 624, 952, 672, 984),
    'table_tasses': (O, 1208, 720, 1256, 768),
    'table_ronde': (O, 1248, 656, 1296, 712),
    'table_large': (O, 1040, 680, 1096, 728),
    'foin_a': (O, 336, 816, 376, 848),
    'foin_b': (O, 816, 200, 856, 232),
    'boite_lettres': (O, 264, 496, 280, 528),
    'seaux': (O, 1096, 1264, 1120, 1288),
    'buissons_rangee': (O, 720, 1472, 800, 1512),
    # --- maisons Pokémon et bâtiments (découpés automatiquement si nécessaire) ---
    'dojo': (O, 1016, 504, 1240, 616),
    'maison_treecko': (O, 360, 272, 488, 376),
    'maison_chikorita': (O, 808, 496, 896, 592),
    'maison_turtwig': (O, 320, 552, 480, 664),
    'maison_dome': (O, 192, 568, 296, 672),
    'maison_shellder': (O, 496, 592, 608, 680),
    'hutte_paille': (O, 376, 888, 504, 1016),
    'etal_kecleon': (O, 1008, 752, 1168, 920),
    'tente': (O, 256, 248, 368, 320),
    'caisses': (O, 624, 1024, 688, 1120),
}
# Objets animés (feuille Animation) : rectangles par image (même taille) ; période = nombre d'images.
A = 'Metano_Town_Animation_Tileset'
ANIMES = {
    'cascade': [(A, 8 + 72 * k, 496, 72 + 72 * k, 616) for k in range(4)],
    'mare': [(A, 8 + 80 * k, 904, 80 + 80 * k, 952) for k in range(3)],
}
