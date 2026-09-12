# Métano pixel-perfect — trois layouts, secs et animés

Cette version répond à la consigne **« avec les tuiles de référence, sans eau ni chemins, uniquement falaises, verdure et bordures »**. Contrairement aux dessins du générateur et aux cours d'eau tracés dans les anciens prototypes, **chaque tuile visible de ce pack est une copie d'une tuile canonique de 8 × 8 px**.

Aucune image générée n'est importée comme texture. Aucun tracé de berge, filtre de palette, pixel redessiné, rotation ou redimensionnement des tuiles de jeu. La composition est nouvelle : ce ne sont pas des cartes officielles de Métano et elles ne reproduisent pas exactement la silhouette du précédent dessin généré.

## Trois layouts

| Dossier | Composition | Taille |
|---|---|---|
| `01_rempart/` | Une grande paroi, trois réservoirs/chutes dans la version humide | 2048 × 1536 px |
| `02_paliers/` | Deux niveaux, une chaîne de deux chutes | 2048 × 1536 px |
| `03_terrasses/` | Trois niveaux, une chaîne de trois chutes | 2048 × 1536 px |

Chaque carte contient **256 × 192 cases**, soit **49 152 cellules de 8 px**.

### Version sèche — exactement les éléments demandés

- `sans_eau_sans_chemins.png` : rendu natif complet.
- `herbe.png` : fond herbeux canonique uniquement.
- `falaises_bordures.png` : reliefs et bordures sur fond transparent.
- `sec.tmj` : carte Tiled avec ces deux calques.

La version sèche **ne contient aucune eau cachée dans son fond**. Les colonnes source des escaliers, de l'entrée rocheuse et de la cascade sont exclues du calque de falaise. Aucun chemin, bâtiment, escalier ni personnage n'est ajouté.

### Version avec eau animée

- `berges_eau.png` : réservoirs et berges d'origine, calque propre à la version humide. Il peut contenir de l'eau statique sous les frames animées, comme la base originale ; il n'est jamais inclus dans la version sèche.
- `eau_frame_1.png` … `eau_frame_4.png` : quatre calques d'eau à positions identiques, RGBA transparents.
- `avec_eau_frame_1.png` … `avec_eau_frame_4.png` : quatre rendus complets en résolution native.
- `anime.tmj` : carte Tiled à quatre calques, animations déjà configurées.
- `layout.json` : dimensions et positions des parois/chutes.

Les réservoirs, leurs deux îlots et les chenaux sont assemblés depuis **Metano_Town_Base** et les **quatre Metano_Town_River_Animation**. Les berges n'ont pas été redessinées. Les portions longues répètent des rangées complètes de tuiles de ces sources.

Les chutes utilisent les quatre colonnes de frames de **Metano_Town_Animation_Tileset**. Les couronnes et pieds sont conservés ; des rangées natives du milieu sont répétées pour franchir les grandes parois. **Pixel-perfect signifie ici que les tuiles ne changent pas : la chute longue entière n'est pas une frame originale intacte de 64 × 136 px.**

## Ce qui est vérifié

Source : [Palikadude/Halcyon](https://github.com/Palikadude/Halcyon), commit `da6c2130d641507447e6386a5e47a296e8cb4c71`.

Le vérificateur indépendant contrôle :

1. les identifiants Git et SHA-256 des **sept ressources natives** utilisées ;
2. les **10 621 entrées réelles de l'atlas**, chacune comparée à ses coordonnées source ;
3. le `.tile` natif et les PNG, avec aller-retour d'alpha prémultiplié ;
4. les sources autorisées de chaque cellule sèche : herbe canonique et colonnes de falaises, sans les colonnes eau/escalier/caverne ;
5. la recomposition de chaque carte Tiled, sèche et aux quatre phases humides ;
6. quatre images d'eau distinctes par layout.

Résultat dans `verification.json` : **zéro différence entre les tuiles utilisées et leurs sources**, zéro différence entre les cartes recomposées et les PNG livrés.

Les textures PMDO natives utilisent un alpha prémultiplié. Les PNG d'éditeur sont en alpha droit : seuls les RGB des rares pixels à alpha partiel sont déprémultipliés pour conserver le rendu. La conversion inverse redonne exactement les pixels source. Les couleurs opaques restent inchangées.

**Non vérifiés :** lancement dans PMDO, collisions, transitions, praticabilité et continuité artistique de tous les nouveaux raccords. Ce test ne certifie pas une carte jouable ni l'identité de la géométrie avec le jeu original.

## Atlas et import

- `Metano_Canonique_8px.png` : atlas commun, pas une image de décor à poser entière.
- `Metano_Canonique_8px.tsj` : Tiled, cellules 8 × 8 px.
- `Metano_Canonique_8px.tile` : ressource PMDO native, nom indépendant des anciens packs.
- `provenance.json` : référence source de **chaque** entrée d'atlas, composition des cartes, Frames et FrameLength natifs.

### Tiled

Ouvrir `sec.tmj` ou `anime.tmj` en gardant les dossiers et l'atlas parent ensemble. Les cartes ont les mêmes dimensions ; leurs deux premiers calques sont identiques. L'ajout de l'eau ne remplace pas le fichier de terrain sec.

### PMDO

Ajouter le `.tile` dans `Content/Tile/`, puis **réindexer** avec les outils du mod/l'éditeur. Ne pas remplacer l'index global par un index partiel. Ground ciblée : **TexSize = 1**, donc 8 px. Les TMJ restent des cartes Tiled ; aucun `.rsground` intégré ni script de collision/transition n'est fourni.

Les animations natives utilisent `FrameLength = 10`, soit environ 166,67 ms à 60 Hz. Le TSJ utilise 167 ms par phase, approximation à la milliseconde entière. La cadence de la rivière est vérifiée dans la carte originale ; celle des grandes chutes assemblées est un choix de présentation à 10 ticks, pas une cadence autonome prouvée pour ces nouvelles formes.

## Aperçus

- `apercu_comparatif.png` : trois layouts en colonnes **sec / avec eau**. Planche de présentation réduite, pas une texture de jeu.
- `../../apercu_metano_pixel_perfect.html` : aperçu autonome, choix de la carte, sec/animé, pause, avance d'une frame, grille et zoom 1×/2×/3×. Le bouton PNG enregistre la vue affichée, grille comprise si activée.

Tous les PNG dans les dossiers de carte sont à **2048 × 1536 px** et ne contiennent aucune grille peinte. Utiliser le zoom natif pour contrôler les pixels ; les aperçus d'ensemble sont nécessairement réduits à l'écran.

## Reconstruction

```sh
python source/build_metano_pixel_perfect.py
python source/verify_metano_pixel_perfect.py
```

Pillow requis. Les sources canoniques sont celles conservées dans `source/falaises_metano/natifs/` et `source/eau_metano/natifs/`. La reconstruction ne fait appel ni à un réseau ni à un générateur d'image.

## Attribution

Tuiles de **Palika / Halcyon** et des artistes crédités dans le projet. Le [README de Halcyon](https://github.com/Palikadude/Halcyon#credits) cite notamment **Jaifain pour les animations de rivière de Métano**. Ce pack ne revendique pas les textures originales comme des créations nouvelles. Vérifier les autorisations des auteurs avant redistribution publique.
