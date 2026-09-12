# Côte V2 — roche corrigée, nuages en wrap et vraie rotation de palette

## Ce qui change

- **La dernière terrasse a été régénérée** avec une référence construite depuis les modules rocheux Métano natifs : assises de pierre horizontales, retours arrondis rosés et pied continu. Le tas de gros blocs arrondis de la version précédente a été remplacé. Le promontoire conserve son terrain V1.
- **Nouveau ciel généré sans nuages**, sur un calque propre.
- **Quatre nuages générés**, extraits sans redimensionnement et montés sur un strip transparent avec wrap horizontal continu, sans oscillation aller-retour.
- **Mer à vraie palette cyclique** : les pixels indexés et leur position ne changent jamais entre les huit PNG. Seules huit entrées de palette tournent. La transparence et la couleur dominante du fond restent fixes.

La roche est une **génération référencée sur Métano, pas une copie pixel-perfect des tuiles originales**. La correction visuelle ne change pas ce statut. Les anciennes versions restent disponibles.

## Aperçu

Ouvrir **`apercu_cote_v2.html`** à la racine. Il est autonome et démarre sur la terrasse corrigée.

- Cocher/décocher les quatre calques.
- Mettre les nuages et la palette en pause indépendamment.
- Régler la vitesse des nuages ou leur décalage.
- Cliquer **« Voir la jonction »**, puis **« +1 px »** pour vérifier le passage de la fin au début du strip.
- Choisir une des huit palettes ; les entrées cyclées sont entourées d’or.
- Exporter les calques visibles en PNG transparent. Le damier d’inspection n’est pas exporté.

`APERCU_NE_PAS_IMPORTER.png` est une présentation réduite, pas une texture de jeu.

Le visualiseur à la racine du dépôt est autonome (images intégrées). L’archive contient une version légère liée aux PNG fournis : conserver son arborescence lors de l’extraction. Dans cette version liée, le bouton d’export est masqué pour éviter les restrictions de lecture de canvas des navigateurs en mode fichier local ; les PNG individuels sont déjà inclus.

## Les quatre calques

Dans `01_promontoire/` et `02_terrasse/` :

| Ordre | Contenu | Fichiers |
|---|---|---|
| 0 | Ciel fixe, sans nuages | `COTEV2_01_00_CIEL_SANS_NUAGES.png` / préfixe `02` |
| 1 | Nuages, position de contrôle 0 | `COTEV2_01_01_NUAGES_POSITION_0.png` / `02` |
| 2 | Mer indexée | `COTEV2_01_02_MER_PALETTE_00.png` à `_07.png` / `02` |
| 3 | Terrain transparent | `COTEV2_01_03_TERRAIN.png` / `02` |

Tous les calques d’une zone ont la même origine **(0,0)** et les mêmes dimensions : **1312 × 816** pour le promontoire, **1200 × 896** pour la terrasse. Le ciel s’arrête à y=360 et la mer commence à cette ligne.

Le fichier `…_COMPOSITION_00.png` est la composition fixe de contrôle. `animation.json` contient les chemins, palettes et réglages de chaque zone.

## Nuages : overlay wrap

- Strip partagé : **`COTEV2_NUAGES_WRAP.png`**, **2200 × 344 px**.
- Quatre sprites séparés, complétés par des pixels transparents à des dimensions multiples de 8 (sans redimensionnement) : `COTEV2_NUAGE_01.png` à `_04.png`.
- Position verticale du strip : **y=8 px**.
- Déplacement par défaut : **12 px/s vers la gauche**.
- Période spatiale : **2200 px** ; le strip possède une marge transparente à gauche et à droite.
- Ni les nuages ni le terrain n’ont été redimensionnés. Seul le fond de ciel généré est adapté au rectangle du ciel par nearest-neighbor.

Pour dessiner la boucle, le principe est :

```text
offset = floor(temps_en_secondes * vitesse_px_par_seconde) modulo 2200
x = -offset
répéter : dessiner le strip à (x, 8), puis x += 2200,
jusqu’à couvrir la largeur de la vue
```

Ce n’est pas un simple changement d’images ni une oscillation. La sortie à gauche réapparaît à droite. Le PNG `NUAGES_POSITION_0` sert à contrôler l’alignement ; il ne remplace pas le strip complet pour le wrap.

## Mer : palette cycling véritable

La base vient de la première phase de mer V1, issue de la planche côtière fournie par l’utilisateur. Elle est repositionnée au nouvel horizon, **sans redimensionnement ni quantification des couleurs**.

Les huit PNG sont en mode **P, indexé** :

- mêmes dimensions ;
- même tableau d’indices ;
- mêmes données compressées **IDAT** ;
- même transparence ;
- huit entrées de palette permutées suivant un anneau fermé ;
- huit rendus colorés distincts ;
- phase 8 = phase 0 pour la boucle.

Les couleurs utilisées restent celles de cette base marine. La couleur de fond dominante n’est pas cyclée pour éviter de faire clignoter toute la mer. **Aucun déplacement géométrique des vagues n’est effectué entre les phases.**

Cadence proposée : **160 ms par palette**, cycle de **1,28 s**. Les indices concernés et les huit palettes RGB sont dans `animation.json`. La séquence est nouvelle ; ce n’est pas une animation officielle de Métano.

Un moteur disposant d’un système de palettes peut conserver le tableau d’indices et remplacer uniquement ces couleurs. L’aperçu HTML affiche les huit PNG palettisés ; leurs données d’indices sont effectivement identiques, ce n’est pas une approximation par déplacement d’image.

## Import PMDO

Les noms sont uniques et les calques/strip sont sur des dimensions divisibles par **8**. Pour le test PNG to Tileset, utiliser une taille de cellule de 8 px et ne pas redimensionner les PNG.

**L’import des PNG seul n’active ni le wrap ni les animations.**

- Pour la mer : les huit PNG constituent huit états à configurer comme animation dans le moteur si aucune rotation de palette native n’est disponible.
- Pour les nuages : le mouvement cyclique du strip doit être configuré ou scripté selon les possibilités de la scène/overlay PMDO.
- Le manifeste est une description des assets et réglages, **pas un fichier Ground directement importable**.

Aucun test dans l’installation PMDO de l’utilisateur n’a été exécuté. Les collisions, transitions et intégration runtime ne sont pas fournies.

## Contrôles

`verification.json` enregistre :

- pixels et dimensions des quatre nuages préservés après suppression du fond magenta ;
- identité du wrap aux positions 0/2200, 1/2201 et -1/2199 ;
- continuité du déplacement d’un pixel à la jonction ;
- aucun redimensionnement des terrains ;
- huit index maps **et chunks IDAT identiques** pour chaque mer ;
- permutation de palette exacte, alpha et couleur dominante inchangés ;
- aucune perte de couleur à la création de la phase 0 ;
- recomposition identique des quatre calques.

Le JavaScript de l’aperçu est contrôlé syntaxiquement avec Node. Ces tests ne certifient pas les pixels de roche comme canoniques et ne remplacent pas un essai en jeu.

```sh
.venv/bin/python source/build_cote_v2.py
.venv/bin/python source/verify_cote_v2.py
.venv/bin/python source/package_cote_v2.py
```

## Sources et crédits

- Modules de roche de référence : **Palikadude/Halcyon**, tuiles Métano Town, Palika et contributeurs. La planche de référence montre des extraits natifs à un zoom entier ; elle n’a pas été collée dans le terrain généré.
- Base marine : planche *Pelipper Post Office* fournie par l’utilisateur, créditant Nintendo, Game Freak, Chunsoft et l’extraction par **Jaxster**. Ce ne sont pas les animations de rivière Métano.
- Terrain corrigé, ciel et nuages : nouvelles sorties du générateur, conservées dans `source/cote_v2/`.

Respecter les conditions des ressources d’origine. La disponibilité de ces éléments n’accorde pas de nouveaux droits de redistribution.
