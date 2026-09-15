# Antre des cascades — V2 générée et multicouche

Cette version remplace l’approche « conversion de l’arène volcanique » par un **nouveau décor d’antre cohérent**, généré à partir des références PMD `images.png` et `IMG_4912.jpeg`. L’ancienne livraison reste intacte.

## Ce qui a été généré
- Une paroi rocheuse continue, avec six ouvertures, piliers et bordures latérales, puis des rebords rocheux en bas. Les zones d’eau sont réservées sur magenta avant détourage.
- Quatre motifs verticaux de cascades, isolés sur magenta, ajustés aux six ouvertures du nouveau décor.
- Quatre motifs d’écume isolés sur magenta, utilisés en poses successives sur des calques distincts des cascades. La planche produite est une grille 2 × 2, inspectée et découpée comme telle.
- Un nouveau fond d’eau complet, situé sous le décor, y compris dans la partie inférieure.
- La plateforme pierre/bois générée pour la V1 est réutilisée et réajustée au nouvel antre : 170 × 180, position (155,132). Ce n’est pas une nouvelle génération de cette plateforme. Couronne, plancher et passerelle restent séparés.

Les bruts sont conservés dans `bruts/`. Ce sont des **adaptations générées dans le style PMD**, pas des textures natives certifiées ou des sprites officiels extraits. La roche forme ici une enceinte stratifiée avec des ouvertures régulières ; les matériaux cherchent la cohérence visuelle avec les références sans prétendre les reproduire pixel pour pixel.

## 28 calques alignés — 480 × 312
**8 statiques** : ombre de la plateforme ; paroi du fond ; bordure gauche ; bordure droite ; roches avant/bas ; couronne de pierre ; plancher en bois ; passerelle sud.

**20 animés** : fond d’eau complet ; liserés eau/pierre ; 6 cascades individuelles ; 6 écumes d’impact individuelles ; 6 remous individuels.

Les cascades sont adaptées au **nouveau layout**, et non superposées aux anciennes coordonnées de lave. Axes et pieds : (64,196), (152,164), (216,119), (264,119), (327,164), (417,196). Les arrivées latérales suivent une courte courbe depuis leurs ouvertures. Les masques sont limités aux canaux libres de roche et restent continus de l’ouverture au pied.

## Animation
40 phases × 80 ms = **3,2 secondes**. Les motifs générés de cascade sont ramenés à une texture de 80 px de haut, puis décalés de 2 px par phase vers le bas à l’intérieur de silhouettes fixes. La texture effectue exactement un tour par boucle. Ce wrap vertical est une animation reconstruite ; les extrémités du motif généré ne sont pas certifiées comme une texture spatialement sans couture.

Les écumes générées changent de pose toutes les 5 phases, avec des déphasages entre chutes. Les remous sont dessinés procéduralement et s’étendent sur l’eau sans traverser les rochers ni la plateforme. Le bassin utilise le nouveau matériau généré réduit à 20 couleurs, avec une déformation périodique limitée à 2 px. **Ce n’est ni une animation native récupérée, ni une simulation physique des fluides.**

## Ouvrir
- `../../apercu_antre_cascades_v2.html` : galerie animée autonome, sélection de chaque calque.
- `arene/COMPOSITION.png` : rendu initial.
- `arene/ANIMATION.webp` : boucle complète sans perte.
- `arene/arene_aquatique_bois.ora` : 28 calques, état initial.
- `arene/aqua_*.png` : calques plein cadre et 40 compositions.
- `sprites/` : motifs de cascade et d’écume détourés, plateforme ajustée.
- `antre_cascades_v2.zip` : paquet avec références et dépendances nécessaires.

## Contrôles / limites
Le vérificateur teste les 40 recompositions opaques, l’ORA, les 40 phases WebP, le maintien des pixels de plateforme, l’absence d’effets d’eau sur le sec, la localisation des écumes et la continuité des six cascades dans leurs canaux sans recouvrir les roches. Aucun test de collisions, d’import ou de combat dans PMDO n’a été effectué.

Les calques rocheux sont des partitions d’une même image générée, sans reconstruction de surfaces cachées. Le fond d’eau, lui, est complet et peut être affiché seul. Les références PMD restent la propriété de leurs ayants droit.

Depuis la racine, avec Pillow, NumPy et SciPy :
```sh
.venv/bin/python source/antre_cascades_v2/build.py
.venv/bin/python source/antre_cascades_v2/verify.py
.venv/bin/python source/antre_cascades_v2/package.py
```
Le builder utilise aussi le brut de plateforme V1 et `source/layouts_magenta_v1/palette.py`, tous deux fournis dans le ZIP.
