# Beach Cave — l’Anse des Marées

## Règle appliquée : canonique avant nouveauté

La contrainte utilisateur est prioritaire : **les textures finales viennent directement de la map référente** `Minemaker0430/ExplorersOfSkyOrigins`. Pour éviter toute ambiguïté, cette première livraison conserve aussi sa composition canonique `beach_cave_pit` au lieu d'inventer une nouvelle géométrie qui aurait besoin de textures fabriquées.

- `renders/beach_cave_v1/guide_composition_generated.png` est un guide d'ambiance uniquement.
- Aucun pixel de ce guide n'est lu par `build.py` et aucun pixel généré n'entre dans le ZIP PMDO.
- La carte finale utilise uniquement `BeachCavePit.tile` et les placements du `beach_cave_pit.rsground` audité.
- Les cellules restent à leur taille native de **24 px** (`TexSize=3`). Elles ne sont ni réduites à 8 px, ni agrandies, ni recolorées, ni tournées.
- La couche canonique et les 24 phases d'animation sont conservées ; aucun découpage de l'image générée n'est effectué.

Le commit externe est épinglé dans `references/provenance.json` : `bed944992c32e7e7927cc3480c72edb0b1782e26`. L'audit résout tous les `Sheet` de `beach_cave_pit.rsground`, vérifie leurs empreintes Git/SHA-256 et reconstruit la composition à l'échelle native.

## Layout livré

- **Dimensions :** 19 × 20 cellules de 24 px, soit 456 × 480 px.
- **Fonction :** vestibule aquatique de donjon, avec plage centrale et cavité rocheuse.
- **Composition :** parois rouges, eau animée au centre, plage claire et ouverture nord.
- **Calque :** `Terrain` unique, comme dans la référence. Il n'est pas artificiellement séparé : changer l'ordre des sous-calques ferait perdre la fidélité canonique.
- **Marqueurs ajoutés au clone d'édition :** `Entrance` à `(244,364)` et `donjon_seuil` à `(220,4)`. Les personnages, objets et spawners narratifs de la scène de référence ne sont pas copiés.
- **Collisions :** les données de référence sont conservées mais ne constituent pas une validation de gameplay ; elles doivent être revues dans PMDO.

Le guide généré reste archivé afin de montrer la proposition de composition, mais il n'est pas la source de la map finale. La fidélité visuelle recherchée ici vient uniquement du réemploi des cellules canoniques.

## Reproduction

Depuis la racine :

```bash
python source/beach_cave_v1/audit.py
python source/beach_cave_v1/layout.py
python source/beach_cave_v1/build.py
```

Dépendances : Pillow et NumPy, déjà listées dans `source/requirements.txt`.

Sorties principales :

- `source/beach_cave_v1/audit/` — compositions de contrôle des références ;
- `renders/beach_cave_v1/01_terrain_canonique.png` ;
- `renders/beach_cave_v1/composition_phase_00.png` à `23` ;
- `renders/beach_cave_v1/v50812_beach_cave_anse_des_marees.rsground` ;
- `apercu_beach_cave_anse_des_marees.html` ;
- `beach_cave_anse_des_marees_pmdo.zip`.

Le ZIP est un projet PMDO séparé. Il embarque son `Mod.xml`, un `index.idx` limité à `BeachCavePit`, le Ground, la feuille native et un script vide d'édition. Il ne fusionne pas l'index d'un autre projet.

## Limites

- Le Ground cible PMDO 0.8.12 et est contrôlé structurellement ; il n'a pas été ouvert avec rendu GPU dans cet environnement.
- Le raccord de destination du donjon et le retour restent à configurer dans le projet de jeu.
- L'aperçu HTML montre le rendu visuel et les phases natives ; il ne valide pas à lui seul le rendu moteur, les collisions ou le gameplay.
- Le guide généré ne doit jamais être importé comme tileset.
