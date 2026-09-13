# Dix nouvelles falaises — palette Métano stricte et audit du dessin

**Bilan : 10 générées, 8 retenues visuellement, 2 à régénérer (07 et 11).** Les couleurs sont contrôlées sur les dix exports ; cela ne rend pas automatiquement leur motif conforme.

[Planche des dix, statuts visibles](PLANCHE_10_FACE_MER.png) · [Gros plans des bordures avant/après](AUDIT_BORDURES_AVANT_APRES.png) · [Aperçu animé et calques](../../apercu_caps_terrasses_v4.html)

## Contrôles effectués

- Références d’herbe, de roche, de rebord et de pied comparées aux ressources natives décodées.
- Palette jour verrouillée à **328 couleurs natives** par recherche de la couleur la plus proche en CIELAB : **0 pixel opaque hors palette**.
- Aucun redimensionnement du terrain, PNG RGBA à alpha binaire, pixels transparents à RGB nul.
- Nuit appliquée avec le filtre Abyss existant.
- Inspection des compositions et de coupes de couronne, avec deux rejets explicites.

**La correspondance des couleurs ne prouve pas l’identité des motifs ou un raccord parfait aux tuiles.** Aucun nouveau Ground ou test moteur livré.

## Huit dessins retenus après inspection

| Falaise | Transparent | Nuit | Magenta | Scène jour |
|---|---|---|---|---|
| Crochet droit | [PNG](08_crochet_droit_terrain.png) | [PNG](08_crochet_droit_terrain_nuit.png) | [PNG](08_crochet_droit_magenta.png) | [PNG](08_crochet_droit_scene.png) |
| Paliers décalés droits | [PNG](09_paliers_decales_droits_terrain.png) | [PNG](09_paliers_decales_droits_terrain_nuit.png) | [PNG](09_paliers_decales_droits_magenta.png) | [PNG](09_paliers_decales_droits_scene.png) |
| Double balcon gauche | [PNG](10_double_balcon_gauche_terrain.png) | [PNG](10_double_balcon_gauche_terrain_nuit.png) | [PNG](10_double_balcon_gauche_magenta.png) | [PNG](10_double_balcon_gauche_scene.png) |
| Paroi haute droite | [PNG](12_paroi_haute_droite_terrain.png) | [PNG](12_paroi_haute_droite_terrain_nuit.png) | [PNG](12_paroi_haute_droite_magenta.png) | [PNG](12_paroi_haute_droite_scene.png) |
| Avancée basse gauche | [PNG](13_avancee_basse_gauche_terrain.png) | [PNG](13_avancee_basse_gauche_terrain_nuit.png) | [PNG](13_avancee_basse_gauche_magenta.png) | [PNG](13_avancee_basse_gauche_scene.png) |
| Échancrure droite | [PNG](14_echancrure_droite_terrain.png) | [PNG](14_echancrure_droite_terrain_nuit.png) | [PNG](14_echancrure_droite_magenta.png) | [PNG](14_echancrure_droite_scene.png) |
| Trois gradins gauches | [PNG](15_trois_gradins_gauches_terrain.png) | [PNG](15_trois_gradins_gauches_terrain_nuit.png) | [PNG](15_trois_gradins_gauches_magenta.png) | [PNG](15_trois_gradins_gauches_scene.png) |
| Balcon renfoncé droit | [PNG](16_balcon_renfonce_droit_terrain.png) | [PNG](16_balcon_renfonce_droit_terrain_nuit.png) | [PNG](16_balcon_renfonce_droit_magenta.png) | [PNG](16_balcon_renfonce_droit_scene.png) |

## Deux sorties non retenues — reprise nécessaire

Ces fichiers restent visibles pour comprendre le rejet, pas comme des dessins certifiés conformes. La tentative de reprise de 07 a été bloquée par la limite de dix générations dans le tour.

- **07_anse_gauche** : Roche en petits galets verticaux et couronne en chapelet : le motif ne reprend pas la référence Métano. La palette verrouillée ne corrige pas cette erreur de dessin. [PNG corrigé en couleur seulement](07_anse_gauche_terrain.png) · [Sortie brute](bruts/07_anse_gauche.png).
- **11_corniche_oblique_gauche** : Rebord lisse en double bande et gros blocs trop simplifiés, différents de la couronne et du grain Métano demandés. Ne pas présenter comme une falaise conforme au contrôle de dessin. [PNG corrigé en couleur seulement](11_corniche_oblique_gauche_terrain.png) · [Sortie brute](bruts/11_corniche_oblique_gauche.png).

## Audit détaillé et sources

[Audit technique indépendant](../../source/caps_terrasses_v4/verification.json) · [Mesures de couleur par image](../../source/caps_terrasses_v4/audit_couleurs.json) · [Observations visuelles par image](../../source/caps_terrasses_v4/audit_visuel.json) · [Palette et provenance](../../source/caps_terrasses_v4/palette_canonique.json) · [Méthode reproductible](../../source/caps_terrasses_v4/README.md)

Les sorties brutes sont conservées dans `bruts/`. Les teintes des exports ont été corrigées, pas celles de ces originaux. Les masques de repérage dans `audit/` ne sont ni des collisions, ni des calques natifs de bordure.

[Six variantes précédentes](../caps_terrasses_v3/README.md) · [Fonds et océan 64 phases réutilisés](../caps_terrasses_v3/ocean/README.md). Le mod et les ressources natifs n’ont pas été modifiés.
