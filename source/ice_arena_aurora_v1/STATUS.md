# Nouvelle demande : zones animées, exemple glace + aurore

Produit une scène512×720 d’accès sud vers l’arène, aurore canonique en arrière-plan et glaces/fissures natives en calques.64étapes de6ticks=6,4s.128PNG animés,2atlas,8calques statiques,2GIFs et2WebP sans perte. Galerie autonome `apercu_arene_glace_aurores_animees_v1.html`.

Important : les recherches dans les arbres complets des3dépôts inspectés n’ont pas identifié le cycle canonique de ce BG. L’utilisateur a été prévenu AVANT production que le mouvement livré serait une proposition nouvelle sur l’image canonique. Ne jamais renommer cette ondulation « animation native extraite ». Ne pas utiliser OndeBoréale/Aurora_Beam comme faux BG de remplacement.

Pixels de l’aurore copiés depuis leurs coordonnées sources, ondulation entière par colonne (±6px maximum par rapport au dessin initial). Étoiles : formes/RGB fixes, opacité variable. Terrain invariant. La première découpe de glace par simple palette créait des trous dans les reflets ; remplacée par retrait du ciel connecté au bord, restauration des trous intérieurs et modules de paroi complets. Aperçus inspectés après correction.

Reproduction : `.venv/bin/python source/ice_arena_aurora_v1/build.py` puis `package.py`.10tests dédiés avant création du ZIP/rapport. Pas de collision ou import moteur annoncé. Conserver sources originales et références de recherche. Autres tâches ouvertes.
