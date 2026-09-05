# Guilde Treehouse — tilesheets et couloirs PMD v2

**Architecture v2 : couloirs et paliers repris de zéro**, avec panneaux de bois debout et bordures d’immersion. Les objets, le parquet, les spirales et les douze salles existantes sont conservés sans modification.

[Voir les plans séparés d’un couloir](apercus/separation_couloir.png).

Ouvrir **[apercu.html](apercu.html)** : aperçu autonome, hors ligne, avec zoom, grille, variantes jour/nuit, contrôle des calques et essai des spirales sur le parquet.

## Contenu

| Ensemble | Quantité | Fichiers principaux |
| --- | ---: | --- |
| Objets | **20** | `objets/objets_jour.png`, `objets_nuit.png` |
| Parquet | **32 tuiles** | `parquet/parquet_jour.png`, `parquet_nuit.png` |
| Traces spiralées | **16 motifs** | `spirales/spirales_jour.png`, `spirales_nuit.png` |
| Panneaux de bois | **Fond + retours séparés** | `architecture/murs_fond_jour.png`, `murs_retours_jour.png` |
| Immersion | **Fond, écorce, racines, feuillage** | `architecture/` |
| Ombres et reflets | **2 plans distincts** | `architecture/contacts_jour.png`, `reflets_jour.png` |
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

### 4. Nouvelle architecture — murs et immersion réellement séparés

La précédente version à murets bas est **remplacée**, pas simplement recolorée. Les nouveaux plans utilisent des pans coupés, des renfoncements et des couloirs traversants.

- **Parquet** : lames horizontales dorées, inchangées.
- **Murs du fond** : panneaux bruns mats de 64 px de haut, fibres noueuses verticales, montants, plinthes et chaperons. Ce motif n’est ni une rotation ni une recoloration du parquet.
- **Retours** : faces obliques de 64 px et parois latérales de 40 px, sur un autre calque. Des pièces de jonction ferment les angles sans laisser de fentes.
- **Immersion** : fond sombre évidé sous le sol, soubassement d’écorce, racines et feuillages sur deux plans. Le chant avant passe devant les objets, comme une bordure de scène PMD.
- Les feuilles de la bordure proviennent de la banque de la guilde. Les murs restent en bois : la référence ne sert pas à remplacer notre DA par une salle de pierre ou d’herbe.

Il s’agit d’une **vue de dessus à murs relevés**, dans la lecture des scènes PMD, plutôt que d’un simple tracé de murs plats autour du sol.

Les panneaux sont dans `architecture/murs_fond_<palette>.png` et `murs_retours_<palette>.png`. Leurs PNG individuels et les pièces de feuillage sont dans `architecture/pieces/`. Les rectangles et noms des pièces figurent dans les catalogues de `kit.json`.

### Les 13 calques de chaque module

| Ordre | Fichier PNG | Fonction |
| --- | --- | --- |
| 00 | `00_fond_immersion.png` | Extérieur sombre ; **transparent sous le parquet**, pas un rectangle de couleur caché sous toute la scène |
| 01 | `01_soubassement.png` | Masse et chant d’écorce sous la scène |
| 02 | `02_feuillage_arriere.png` | Canopée derrière les panneaux |
| 03 | `03_parquet.png` | Sol seul, aucun mur ni végétation intégrés |
| 04 | `04_murs_fond.png` | Panneaux du fond seuls |
| 05 | `05_murs_retours.png` | Retours obliques, parois latérales et pièces de jonction |
| 06 | `06_ombres_contact.png` | Contacts des parois sur le sol |
| 07 | `07_reflets_seuils.png` | Petits reflets latéraux des seuils, atténués la nuit |
| 08 | `08_spirales.png` | Motif optionnel, sans parquet incorporé |
| 09 | `09_ombres_objets.png` | Ombres des accessoires |
| 10 | `10_objets.png` | Accessoires et tentures, indépendants des murs |
| 11 | `11_ecorce_racines_avant.png` | Chant et racines de premier plan |
| 12 | `12_feuillage_avant.png` | Feuillages et retombées devant la scène |

Les couloirs restent sans mobilier ni spirale ; les plans correspondants sont présents mais vides. Certains modules sans paroi droite au fond ont seulement des retours. Le soubassement peut être partiellement ou complètement caché dans la composition complète, mais reste disponible lorsque les murs sont masqués.

L’atelier démarre sur la nouvelle galerie. Les boutons **Sol seul**, **Murs seuls**, **Bordures seules** et **Sans fond** permettent de vérifier la séparation sans cliquer treize fois.

## Les 9 modules reconstruits

| Module | Dimensions | Sorties |
| --- | --- | --- |
| Galerie est-ouest | 448 × 352 px | E / O |
| Galerie nord-sud | 320 × 448 px | N / S |
| Coude nord-est | 384 × 384 px | N / E |
| Coude sud-ouest | 384 × 384 px | S / O |
| Carrefour en T | 512 × 416 px | N / E / O |
| Croisement à pans coupés | 448 × 448 px | N / E / S / O |
| Palier des provisions | 512 × 416 px | E / O |
| Antichambre des racines | 416 × 512 px | N / S |
| Halte des explorateurs | 512 × 480 px | N / E |

Dans chaque dossier `modules/<nom>/` :

- `jour.png` / `nuit.png` : compositions avec le fond d’immersion ;
- `jour_transparent.png` / `nuit_transparent.png` : mêmes scènes **sans le fond sombre**, avec l’écorce et les feuillages conservés ;
- `calques/<palette>/` : les **13 PNG séparés** ;
- `jour.aseprite` / `nuit.aseprite` : les 13 calques, une image fixe, grille 32 px ;
- `jour.tmj` / `nuit.tmj` : les 13 plans dans Tiled ;
- `sol_praticable.png` : masque du sol, sans définir les collisions propres aux accessoires.

Les murs et les feuillages sont des **tile objects** utilisant des pièces réutilisables. Les spirales et les accessoires pointent vers leurs PNG individuels. Les fonds, sols découpés, ombres et chants d’écorce sont des couches de tuiles de 32 px. Les découpes de contour ne constituent pas un système de Wang universel : les plans livrés et `source/hallways/definitions.json` servent de modèles d’assemblage.

### Raccords

Les ouvertures font **96 px**. Tous leurs axes sont congrus à 16 modulo 32, donc les ancrages homologues se raccordent par translations entières de tuiles. Les 40 premiers pixels des bords ouverts restent sans feuillage coupé ; on peut végétaliser la jonction après assemblage.

Exemple : galerie est-ouest, axe y=208 ; palier des provisions, axe y=272. Placer la galerie **64 px plus bas** que le palier pour aligner leurs accès. Les pixels de leurs sols E/O se correspondent ; les joints des planches N/S gardent une phase cohérente. Les raccords décoratifs restent ajustables : il ne s’agit pas d’une promesse d’égalité de chaque pixel de mur ou de racine entre toutes les paires de modules.

**Les sorties des douze salles historiques n’ont pas toutes cette largeur ni cette projection.** Aucun couloir n’est branché automatiquement sur le plan existant. Prévoir les adaptations de seuil, collisions, transitions et profondeur des personnages dans le moteur.

## Reconstruction et validation

Depuis la racine du dépôt :

```bash
pip install -r source/requirements.txt
python source/build_tilesheets.py
python source/verify_tilesheets.py
python source/build_tilesheets_preview.py
```

Pour reconstruire uniquement les couloirs, sans réexporter les autres banques :

```bash
python source/build_hallways.py
python source/verify_hallways.py
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

Les résultats courants sont dans `controle_hallways.json`, `controle_qualite.json`, `controle_navigateur.json` et `controle_reconstruction.json`. La version refusée à murets plats n’est plus réexportée par le constructeur.
