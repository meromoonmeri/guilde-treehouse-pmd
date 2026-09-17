# État V6 — Eat pour tous

9 packs complets base + ajouts ; 57 GIFs dans la galerie autonome `apercu_guilde_eat_tous_v6.html`.

- **Nouveaux candidats :** Canarticho, Pandespiègle, Dimoret, Tarpaud ;16étapes et8vues natives distinctes, sans miroir. Cadences propres à chaque espèce dans `NEW_TICKS`.
- **Conservés V5 :** Gardevoir raffiné et Balignon sans bras,16étapes×8vues.
- **Natifs conservés exactement :** Draby, Ptiravi, Pachirisu ;1vue,4frames,6/8/6/8ticks. Ne pas présenter cela comme neuf cycles à huit vues.
- Aucun aliment ajouté au personnage : Food_* et émote restent des éléments de scène distincts. Le poireau et la feuille natifs restent des accessoires identitaires.

82 tests PASS, dont11 V6 : ressources originales, XML natif, réutilisations V5, cycles fermés nouveaux, diversité des dessins, repères identiques pour rendus identiques, accessoires visibles, pieds/ombres, palettes natives et57GIFs. La feuille de Pandespiègle n’est pas visible dans les vues natives U/UL : masque vide attendu, pas de feuille inventée derrière la tête. 9 précontrôles locaux donjon PASS.

Les quatre générations sont des études : articulation finale au pixel des parties natives, et non génération brute approuvée. **Art à examiner ; intégration/runtime PMDO non testés.** Le suivi actualisé compte124actions du profil32 encore sans cycle local ; les neuf Eat ne terminent pas le programme global.

Toutes les propositions de guilde déjà présentées sont retenues par l’utilisateur (structures/QG/annexes, végétation, animations). Les structures ne sont pas encore dessinées. Cette sélection n’approuve pas des dessins inédits ou leur intégration. Les cartes utilisateur restent intactes.

Reproduction : `.venv/bin/python source/guild_eat_all_v6/build.py`, puis `gallery.py` et `progress.py` dans le même dossier. Tests : `PYTHONPATH=source/pmd_character_pipeline .venv/bin/python -m unittest source.guild_eat_all_v6.test_build`.
