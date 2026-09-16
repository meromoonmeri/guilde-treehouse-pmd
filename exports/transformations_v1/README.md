# Transformations — prochain livrable visuel : pilote Dracaufeu

**17 septembre 2026 · Prototype artistique, pas intégration PMDO certifiée.**

Ouvrir `apercu_transformations_v1.html` à la racine du dépôt, en conservant le dossier `exports/transformations_v1` à sa place. La galerie charge seulement les trois GIF sélectionnés, sans dupliquer tous les médias dans son HTML. Serveur local facultatif : `.venv/bin/python source/transformations_v1/serve_gallery.py` puis port 8000.

## Livré

| Séquence | Transformation | État persistant |
|---|---|---|
| Dynamax | 8 directions, Dracaufeu normal → agrandissement visuel ×3 | 8 boucles, nuages en orbite et particules |
| Gigamax | 8 directions, Dracaufeu normal → véritable sprite Gigamax | 8 boucles ; corps natif final statique par direction |
| Téracristallisation Feu | 8 directions, coque, fracture, assemblage du candélabre | 8 boucles, reflets sur le corps et éclats sur la couronne |

**48 GIF finaux**, chacun de **8 secondes**. Chaque timeline possède 240 phases à 2 ticks/phase, sur une base de 60 ticks/s. Le codec GIF peut fusionner des images identiques ; la durée décodée est testée. Les boucles de 240 phases synchronisent le cycle natif de 60 ticks de Dracaufeu, les composants de 48 phases et les orbites. Le redémarrage d'une transformation n'est pas une transformation inverse : utiliser le mode « État persistant » pour une boucle d'état.

La Téracristallisation est présentée en **vue rapprochée ×2**, au plus proche voisin, pour rendre ses facettes lisibles. Ce cadrage ne modifie pas les coordonnées des calques exportés.

### Chorégraphie

- **Dynamax/Gigamax** : appel au sol, bord de colonne descendant du haut du cadre jusqu'au Pokémon, deux densités de colonne cyclées indépendamment, branches générées et ramifications calculées, particules aspirées. Le volume et la quantité d'éclairs sont plus importants pour Gigamax. Une coque énergétique et un pulse masquent le changement, puis se dissipent. Trois groupes de nuages tournent à des vitesses et profondeurs différentes.
- **Téra Feu** : croissance depuis le sol, prismes réfractifs, fermeture d'une coque facettée réellement opaque, fissures puis fragments expulsés. La couronne se construit de bas en haut ; les reflets du corps sont limités à l'alpha du sprite, pendant et après la transformation.
- Changement logique à la phase **132 / 4,4 secondes**. Les phases 129 à 135 sont vérifiées opaques dans les huit directions pour les trois séquences.

## Fichiers et reconstruction

- `gifs/{dynamax,gigantamax,tera_fire}_{D,DR,R,UR,U,UL,L,DL}.gif` : transformations.
- `gifs/*_hold_*.gif` : boucles persistantes.
- `review/*_storyboard.png` : huit instants par séquence.
- `review/*_eight_final_views.png` : états finaux des huit directions, décodés depuis les GIF livrés.
- `components/` : six composants extraits/interpolés, plus les couronnes Feu/Eau statiques et provisoires. Eau n'a pas de transformation assemblée dans ce lot.
- `layers/` : **sept calques séparés pour la direction D seulement** : sol, arrière, personnage, reflets du corps, avant, accessoire, voile opaque. Les pages entièrement vides sont omises.
- `manifest.json` : ancrage, cadence, ordre des calques, pages et numéros de phases. Canvas transparent 256×288, pied au point **(128,250)**. Les pages `.8x5.png` ont 8 colonnes et 5 rangées de cellules rectangulaires 256×288, soit 40 phases. Ne pas importer ces pages comme des tilesets de terrain ni leur inventer une extension binaire `.dir`.
- `verification.json` : résultats mécaniques et hashes des sources.

Les sept autres directions sont reproductibles via le script ; leurs calques ne sont **pas** tous exportés. Les PNG paginés sont des sources pour un futur import, pas un contrôleur moteur qui joue automatiquement la timeline. Les acteurs sont présents dans un calque distinct ; les pages ne modifient pas les originaux natifs.

```bash
.venv/bin/python source/transformations_v1/build_sequences.py
.venv/bin/python source/transformations_v1/verify_sequences.py
.venv/bin/python -m unittest source.transformations_v1.crown_attachment.test_attachment -v
```

## Vérifié et non vérifié

**Vérifié :** 168 contrôles de masquage intégral autour du changement ; 1 920 phases Téra sans reflets hors silhouette ; 24 fermetures périodiques à la phase théorique 240 ; 48 GIF décodés à 8 000 ms ; géométrie RGBA des pages ; hashes natifs inchangés. Les différences entre la dernière et la première image des boucles sont enregistrées et comparées aux différences courantes. Certaines dépassent légèrement le 95e percentile : la fermeture mathématique ne suffit pas à garantir une fluidité artistique parfaite. Cinq tests unitaires d'attachement passent également.

**Non vérifié / restant :** import et lecture réels dans Ground/Dungeon PMDO ; performance et contrôleur moteur ; taille/collision en jeu ; calibration de toutes les espèces ; calques de toutes les directions ; occultations spécifiques cornes/oreilles ; approbation artistique des angles de couronne ; autres types et transformations inverses. Aucun test historique PMDO n'est présenté comme une validation de ce lot.

Les couronnes restent des **accessoires sans tête ni visage intégré**. Le retrait volontaire des yeux du joyau frontal suit la correction du projet, mais signifie que ces variantes ne sont pas des copies pixel-exactes des bijoux canoniques. La couronne Feu doit encore faire l'objet d'une revue des huit angles ; les 18 autres types ne sont pas animés ici (Eau existe seulement comme accessoire statique).

## Provenance

- Acteurs : sources SpriteCollab, originaux et fichiers `credits.txt` préservés dans `source/mega_evolution_v1/references/charizard/` et `source/transformations_v1/references/charizard_gmax/`.
- Gigamax : slot `sprite/0006/0003`, révision `3609a86be2a4c8ad7cf255bd2255f044daafe24f`, crédit `<@!276369635304275968>`, `CC_BY-NC_4`. Ce n'est pas un Dracaufeu normal agrandi. Respecter les crédits/licences exacts des deux fichiers, sans attribuer une licence unique inventée à tout le lot.
- Composants VFX et couronnes : images générées conservées dans `source/transformations_v1/generation/`, extraction avec alpha, interpolation par flux optique, puis chorégraphie calculée. **240 phases ne signifie pas 240 dessins manuels.** Les éclairs secondaires, les orbites, les particules, les facettes de fermeture et les reflets sont calculés.
- Sol sombre de démonstration : décor neutre calculé pour la revue, pas terrain canonique PMD ni scène extraite de PMDO.
