# Arène glacée large V3 — ciel séparé, aurore en wrap

## Correction demandée

- **768 × 512**, contre 512 × 640 en V2 : nouvelle génération en paysage, aire de combat ovale plus large et approche sud courte. L'ancien portrait n'a pas été étiré horizontalement.
- **Ciel régénéré indépendamment** du terrain, sans aurore intégrée. Les petites étoiles du nouveau ciel sont extraites sur un calque séparé et fixe ; ciel + étoiles reconstituent exactement le ciel normalisé.
- **Aurore RGBA périodique**, défilement horizontal vers la gauche, derrière le terrain. Le ciel, les étoiles et le terrain ne défilent pas.
- Terrain complet généré sur magenta, sol complet généré séparément, détourage et séparation en plans alignés. **Pas d'assemblage de bouts de maps.**

## Fichiers

- `calques/` : ciel, étoiles et 7 plans de terrain, PNG RGBA 768 × 512.
- `arene_large_editable.ora` : tous les plans dans l'ordre, aurore à la phase 0 incluse.
- `animation/AreneLargeV3_Aurore_Wrap792.png` : texture transparente répétable de 792 × 240.
- `animation/AreneLargeV3_Aurore_Loop.webp` : overlay seul animé, sans perte et avec transparence.
- `animation/frames/` : les **198 phases RGBA** de l'overlay, 768 × 240, placement (0,0).
- `review/animation.gif` : scène complète, 198 phases, boucle de **26,4 secondes**. Palette GIF réduite ; PNG/WebP font autorité pour les couleurs et l'alpha.
- `review/scene_*.png` : instantanés pleine résolution ; `terrain_detoure.png` : terrain seul.
- `placement_recipe.json` : recette descriptive de placement/défilement, **pas un fichier natif PMDO**.
- `manifest.json` : provenance, hashes, normalisation et limites.
- `apercu.html` dans le ZIP ; à la racine du dépôt : `apercu_arene_glace_large_v3.html`. Lecteur autonome, calques activables, pause, curseur et bouton « Voir le raccord de boucle ».

## Wrap exact

La texture mesure 792 pixels. Pour un temps t en secondes :

```
source_x = (screen_x + floor(t * 30)) modulo 792
```

Le lecteur affiche deux copies jointives de la texture. Une période dure 792 / 30 = **26,4 s**. Pour les exports, chaque étape avance de 4 pixels : **198 étapes de 8 ticks à 60 Hz**. GIF/WebP alternent 130,130,140 ms pour représenter exactement cette durée dans leurs unités entières.

La phase 198 est identique pixel par pixel à la phase 0 ; elle n'est pas ajoutée comme dernière image répétée. Le passage 197 → 0 avance des mêmes 4 pixels que tous les autres passages. Toutes ces translations, y compris le raccord, sont vérifiées.

Le raccord spatial est traité par alpha : bords des motifs atténués sur 24 pixels en cosinus, bord inférieur sur 20 pixels, colonnes de jonction exactement transparentes. Il s'agit de rideaux distincts adoucis aux limites, pas d'un ruban continu redessiné. Aucun fondu temporel de la scène et aucun déplacement du terrain ne masquent la boucle.

## Proportions et calques

Les nouvelles générations sont normalisées **uniformément**, en nearest-neighbor, puis complétées par de petites marges ; jamais de redimensionnement anisotrope. Pour le terrain 1264 × 848, l'image devient 763 × 512, posée à x=2 sur 768 × 512. Les dimensions exactes de chaque brut sont consignées dans le manifeste.

Les 6 masques visibles sont disjoints et reconstituent exactement le terrain détouré ; le 7e plan est le sol généré sous les reliefs. Les plans sont éditables mais les faces cachées des falaises ne sont pas reconstruites pour des déplacements arbitraires d'objets.

## Origine / limites

Terrain et ciel : nouvelles images générées, inspirées des références PMD fournies ; **pas des pixels natifs certifiés**. Aurore : dessin canonique issu de `aurorepmdsky.png`, via les poses déjà produites du lot V1 ; trois poses, placements et alpha adaptés pour construire cette nouvelle bande périodique. Les sources et hashes sont conservés au manifeste. Le mouvement horizontal est nouvellement écrit : **ce n'est pas le cycle officiel extrait du jeu**.

Références PMD : Pokémon / Nintendo / Creatures / GAME FREAK / Chunsoft ; fichiers de référence fournis dans le dépôt, droits de leurs ayants droit. Aucune nouvelle autorisation de redistribution n'est présumée.

13 tests dédiés : proportions, hashes, partitions, recomposition, ciel/étoiles, grille/alpha, raccord spatial, boucle exacte, translation de chaque phase, exports, terrain fixe, timing, ORA et WebP sans perte. Syntaxe JavaScript contrôlée ; pas de test interactif dans un navigateur ni d'import, collision, warp ou parallax PMDO validé. Candidat visuel à examiner, autres zones et programme guilde toujours ouverts.

Reconstruction : `.venv/bin/python source/arene_glace_large_v3/build.py`, puis `.venv/bin/python source/arene_glace_large_v3/package.py`.
