# Falaise océanique originale — layers générés

Cette livraison repart de zéro. Les cinq images de `source/exterieur_original/generation/`
ont été générées séparément, avec une consigne explicite de **pixel art PMD natif
strict** : palette indexée limitée, contours sombres durs, clusters carrés,
diagonales crénelées et tramage contrôlé. Elles ne doivent jamais être lues comme
des illustrations lissées, vectorielles ou peintes. Aucune image de référence,
aucun template ni aucun pixel extérieur n'est présent dans les fichiers finals.

## Composition inventée

La scène de 688 × 384 px présente un horizon marin, une ligne de reliefs naturels,
une falaise rocheuse de premier plan et une mer ouverte. Il n'y a aucune maison,
route, pont, escalier, plateforme construite, bâtiment, objet de gameplay ou
personnage.

L'ordre de parallax est :

1. `00_ciel` — dégradé atmosphérique ouvert, **sans nuage** ;
2. `01_nuages_wrap` — groupes de nuages indépendants ;
3. `02_mer_palette` — surface marine sans objet ;
4. `03_plateaux_reliefs` — masses géographiques naturelles lointaines ;
5. `04_falaise` — roche naturelle de premier plan.

## Fond magenta explicite

Les fichiers finals inspectables sont dans :

```text
calques_magentas/original/
```

Ils sont tous des PNG **RGB** avec le chroma-key strict `#FF00FF` dans les zones
vides. Le ciel couvre naturellement tout le cadre ; les quatre autres layers ont
un fond magenta. `calques_rgba/original/` est l'équivalent alpha dérivé de façon
déterministe du chroma-key, exclusivement pour Aseprite, Tiled et la composition.

## Animations conçues pour boucler

- **Nuages** : le layer généré est transformé en ruban périodique de 344 px,
  répété exactement deux fois sur 688 px. Ses bords de tuile sont magenta pur,
  donc le `offset` horizontal de 1 px par image ne crée aucune cassure à gauche
  ou à droite. Après 344 phases, la matrice est identique à la phase 0.
- **Mer** : 24 états changent uniquement les valeurs de palette de l'eau.
  L'alpha et les coordonnées des pixels restent identiques : aucune vague ne se
  déplace géométriquement. La force chromatique évolue doucement de 0 à son
  maximum et revient à 0, ce qui raccorde la phase 24 à la phase 0 sans coupure.
- La timeline commune fait 1 032 images de 250 ms afin que 344 et 24 soient
  synchronisés. Les cels Aseprite réelles sont écrites sur chaque période puis
  liées pour les répétitions. Tiled possède un atlas par layer animé.

## Aperçu sur grille

Ouvrir [`../apercu_exterieur_original.html`](../apercu_exterieur_original.html).
L'aperçu applique le chroma-key magenta au rendu, affiche une **grille 8 × 8 px**
par défaut, permet de masquer chaque layer et de mettre la boucle en pause. Il est
autonome : les images sont encodées en WebP data URI et aucune requête réseau
n'est nécessaire.

## Reconstruction et contrôle

```bash
pip install -r source/requirements.txt
python source/exterieur_original/build.py
python source/exterieur_original/verify.py
```

Le vérificateur contrôle le fond magenta, la conversion chroma-key/RGBA, la
composition initiale, le wrap bit-identique des nuages, la mer sans déplacement
de géométrie, les cycles Tiled, les cels Aseprite et les repères de la grille HTML.
