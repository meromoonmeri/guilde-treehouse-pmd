# Guilde Treehouse — tilesheets et modules top view

Un **nouveau kit séparé** : objets inspirés de la finesse des références PMD, parquet ambré assorti à la guilde, traces spiralées transparentes et petites pièces en vue de dessus. Les douze salles existantes ne sont pas modifiées.

Ouvrir **[apercu.html](apercu.html)** : aperçu autonome, hors ligne, avec zoom, grille, variantes jour/nuit, contrôle des calques et essai des spirales sur le parquet.

## Contenu

| Ensemble | Quantité | Fichiers principaux |
| --- | ---: | --- |
| Objets | **20** | `objets/objets_jour.png`, `objets_nuit.png` |
| Parquet | **32 tuiles** | `parquet/parquet_jour.png`, `parquet_nuit.png` |
| Traces spiralées | **16 motifs** | `spirales/spirales_jour.png`, `spirales_nuit.png` |
| Architecture en bois | **47 configurations** | `architecture/structure_jour.png`, `structure_nuit.png` |
| Contacts des murs | **16 combinaisons** | `architecture/contacts_jour.png`, `contacts_nuit.png` |
| Couloirs et jonctions | **6** | `modules/` |
| Paliers / salles intermédiaires | **3** | `modules/` |

Toutes les familles ont une variante **jour et nuit**. Il n’y a pas d’animation dans cette livraison.

### 1. Objets

Bannières vertes et or, lianes gauche/droite, guirlandes, paillasses dorées et vertes, trois tapis, coffres, panier de baies, jarre, sac, paillasses roulées, seau et bûches.

- Atlas : **384 × 480 px**, 4 × 5 cellules de **96 × 96 px**. Les sprites ne remplissent pas artificiellement chaque case.
- PNG individuels : `objets/individuels/`, tailles natives multiples de 8 px, transparence réelle.
- Ombres individuelles : `objets/ombres/`. Les éléments muraux et les tapis n’ont pas de fausse ombre de sol ajoutée.
- Atlas d’ombres : `objets/ombres_jour.png` et `ombres_nuit.png`.
- Aseprite : `objets/objets_jour.aseprite` et `objets_nuit.aseprite`, avec les **objets et leurs ombres sur deux calques**.
- Tiled : collections d’images dans `tiled/objets_jour.tsj` et `objets_nuit.tsj`. Il n’est pas nécessaire de découper soi-même les grandes cellules de l’atlas.
- Les tailles, pivots et rectangles d’atlas figurent dans `kit.json`. Pour un élément mural, adapter l’ancrage à la hauteur du mur ; il ne doit pas être interprété comme un objet posé au sol.

Les objets sont de nouvelles interprétations, pas les sprites originaux du jeu copiés dans le projet. Les couleurs de bois et de feuillage sont rapprochées de la guilde ; la proposition générative et sa préparation sont documentées dans `source/tilesheets/`.

### 2. Parquet sans spirale intégrée

- Tuiles de **32 × 32 px**, compatibles avec la sous-grille de 8 px du projet.
- Atlas : **256 × 128 px**, 8 colonnes et 4 rangées, **sans espacement ni marge**.
- Tuiles **0–15** : planches horizontales, avec variations de veinage et de joints.
- Tuiles **16–31** : versions verticales.
- Les variantes d’un même sens partagent leurs bords et la phase de leurs joints. Ne pas mélanger les orientations au hasard : le changement de sens doit être un choix de pose du parquet.

Les joints reviennent tous les 8 px : la première et la dernière rangée d’une tuile horizontale ne sont donc pas nécessairement de la même couleur, mais la continuité du motif de planches est respectée. Les variantes sont combinables sans faire apparaître un quadrillage supplémentaire de 32 px.

### 3. Traces spiralées en vrai calque séparé

**Aucun parquet n’est peint dans ces PNG.** Les marques ont un alpha partiel pour évoquer une usure/trace claire sur notre bois, sans gros disque opaque.

- Atlas : **256 × 256 px**.
- **16 motifs de 64 × 64 px**, rangés en 4 × 4 blocs.
- Chaque motif occupe **2 × 2 tuiles de 32 px** dans Tiled ; le tileset compte donc 64 sous-tuiles.
- Motifs entiers : `spirales/individuelles/spirale_01_jour.png` à `spirale_16_jour.png`, et leurs variantes nocturnes.
- Variantes horaires/antihoraires, tailles et intensités différentes. Les marques sont plus discrètes la nuit.
- Poser le motif **au-dessus du parquet, sous les objets**. Modifier librement son opacité ou sa position.

`parquet/parquet_et_spirales_jour.aseprite` et sa variante nuit offrent un document d’essai avec **deux calques indépendants**, sur une grille de 32 px.

L’onglet « Parquet & spirales » de l’aperçu permet de choisir le motif, régler son opacité, retirer le parquet pour vérifier l’alpha et déplacer la trace par clic. Il s’agit d’un essai : il ne réécrit aucune salle.

### 4. Architecture top view

Le bois des murs est interprété en **murets vus de dessus**, avec une épaisseur visible de 24 px, des retours arrondis, de fins veinages et des arêtes claires. Ce n’est pas la copie en miniature des hauts murs en coupe des douze salles.

- Grille : 32 px.
- Atlas : **256 × 192 px**, 48 cases. Les 47 configurations comprennent le cas vide ; la dernière case est réservée.
- `kit.json` associe les indices aux voisins de sol : N=1, E=2, S=4, O=8, NE=16, SE=32, SO=64, NO=128.
- Les diagonales déjà couvertes par un voisin cardinal sont éliminées : on obtient les pièces droites, angles, retours et coins nécessaires aux exemples.
- Les ombres des murs sont un **tileset distinct**, pas une bande sombre traversant les sorties.

Les modules fournis sont un point de départ plus pratique que le choix manuel des configurations de voisinage.

## Les 9 modules

| Module | Dimensions | Sorties |
| --- | --- | --- |
| Couloir est-ouest | 288 × 160 px | E / O |
| Couloir nord-sud | 160 × 288 px | N / S |
| Angle nord-est | 224 × 224 px | N / E |
| Angle sud-ouest | 224 × 224 px | S / O |
| Jonction en T | 288 × 224 px | N / E / O |
| Croisement | 288 × 288 px | N / E / S / O |
| Palier des provisions | 352 × 288 px | E / O |
| Antichambre nord-sud | 288 × 352 px | N / S |
| Halte des explorateurs | 352 × 352 px | N / E |

Chaque dossier `modules/<nom>/` contient :

- `jour.png` et `nuit.png` : compositions ;
- `calques/<palette>/` : **six PNG séparés** — parquet, structure, contacts, spirales, ombres d’objets, objets ;
- `jour.aseprite` et `nuit.aseprite` : six calques, une image fixe, grille 32 px ;
- `jour.tmj` et `nuit.tmj` : vraies cartes Tiled utilisant les tilesets partagés ;
- `sol_praticable.png` : masque indicatif du plancher, sans décider des collisions propres aux objets.

Les couloirs sont vides. Les paliers sont présentés avec quelques objets et une trace **en calques optionnels** : dans Tiled, les accessoires sont des *tile objects* déplaçables, pas une image de mobilier aplatie.

### Raccorder les modules

Les ouvertures entre **ces nouveaux modules** font **96 px (3 tuiles)**. Leurs points d’ancrage sont dans `kit.json`.

Exemple : le couloir horizontal a son axe à y=80, le palier est-ouest à y=144. Pour raccorder le bord droit du couloir au bord gauche du palier, placer le couloir **64 px plus bas** que le palier. Le joint a été comparé pixel par pixel, de jour et de nuit, sans changement d’échelle.

**Les sorties des douze salles historiques n’ont pas toutes cette largeur ni cette projection.** Prévoir un raccord de seuil adapté pour les relier aux nouveaux modules ; ils ne sont pas branchés automatiquement sur le plan existant. Collisions des objets, transitions, profondeur des personnages et éventuels changements de caméra restent à configurer dans le moteur.

## Reconstruction et validation

Depuis la racine du dépôt :

```bash
pip install -r source/requirements.txt
python source/build_tilesheets.py
python source/verify_tilesheets.py
python source/build_tilesheets_preview.py
```

Pour contrôler aussi l’aperçu navigateur :

```bash
pip install -r source/requirements-validation.txt
playwright install chromium
python source/verify_tilesheets_browser.py
```

`PMD_CHROMIUM=/chemin/vers/chromium` permet d’utiliser un navigateur déjà installé.

Le build ne rappelle jamais le générateur. Il ne réécrit pas les intérieurs existants. Les contrôles portent sur les transparences, les motifs indépendants, les raccords, les références des tilesets, les objets déplaçables, les recompositions PNG/Aseprite/Tiled et la conservation des salles existantes. Les formats Aseprite/Tiled sont relus par code, pas validés par une ouverture manuelle dans ces applications.
