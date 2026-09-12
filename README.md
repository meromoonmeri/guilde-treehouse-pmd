# Guilde Treehouse — passages ouverts PMD

Cette reprise conserve l’univers graphique du **premier pack**. Les accès ont été corrigés suivant la dernière consigne : **des ruptures du contour avec un sol continu, pas une porte à chaque sortie**.

## Règles effectivement appliquées

- **Est / Ouest :** le plancher traverse une interruption de la bordure latérale. Pas de battant, de portique ni d’arche ajoutée sur ces accès.
- **Sud :** seul le sol se prolonge vers le passage. Une éventuelle porte se trouve hors caméra et n’est pas dessinée.
- **Nord :** passage de sol ouvert pour les salles 01 et 09 ; les accès par échelle gardent leur fonction.
- **Une seule porte fermée visible :** au nord du hall 02, donnant vers le bureau du maître 12. Le bureau conserve son accès sud, sans porte visible depuis l’intérieur.
- Les anciennes fausses portes de fond et les sorties sud superflues des chambres latérales ont été retirées.
- Dans le hall, **le tronc et l’échelle se prolongent au-delà du bord supérieur**, sans sommet de tronc scié visible.
- Les ombres restent des ombres de contact aux retours du contour ; elles ne forment pas de barre noire bouchant le sol.

Les pièces sont **vides et fixes**. Aucun meuble, paillasse, tapis, plante, bannière ou lampe n’est posé dans les fonds. Les deux tableaux muraux du hall sont conservés comme équipements encastrés. La banque d’objets du pack précédent reste fournie séparément.

## Fenêtres et paysage

Les cadres et croisillons sont conservés, mais **aucun paysage n’est peint dans le calque intérieur**.

- `base_jour_transparente.png` / `base_nuit_transparente.png` : vrais PNG RGBA, avec les ouvertures de fenêtres transparentes.
- `base_jour_magenta.png` / `base_nuit_magenta.png` : variantes de contrôle sur fond **#FF00FF**, visible à travers les fenêtres. Pour le jeu, utiliser de préférence les PNG transparents.
- `fenetres_exterieur/NN/` : six vues déjà positionnées et masquées aux fenêtres de chaque salle.
- `exterieur/` : les six panoramas complets, issus de la géographie de la terrasse approuvée.

Ambiances : **jour, nuit, crépuscule, aube, soir et orageux**. Les montagnes, le village et la rivière restent au même endroit. Les palettes, le ciel et la météo varient. Le paysage et la palette de l’intérieur peuvent être choisis indépendamment.

La salle 01 n’a pas de fenêtre vitrée : son accès nord est désormais une continuité de sol. Les persiennes des salles 08/10 conservent leurs lattes, avec une vue interchangeable dans leurs interstices.

## Onze calques séparés

1. Paysage extérieur interchangeable
2. Sol et continuité des passages
3. Structure, murs et ouvertures
4. Cadres de fenêtres, sans paysage
5. Contenu des tableaux encastrés
6. Porte nord du bureau — uniquement dans le hall
7. Décorations — **vide**
8. Objets — **vide**
9. Ombres de contact des accès
10. Éclairage complémentaire — **vide**
11. Bordure de premier plan, interrompue aux passages

Chaque salle est disponible en **jour et nuit**, avec une seule image par fichier Aseprite. Il n’y a aucune animation dans cette version.

## Falaises — tileset animé « Métano / Treasure Town »

24 tuiles de **24 × 24 px** (multiple de la grille 8 px du kit), **4 frames de 150 ms**, déclinées dans les **6 ambiances**. Roche ocre façon Trésor-Ville (lobes arrondis, coutures sombres, lèvre éclairée) harmonisée avec la palette teal/verte du panorama extérieur : les falaises se raccordent visuellement au village et aux salles.

- `falaises/<ambiance>/tileset_falaises_<ambiance>.aseprite` : feuille Aseprite multi-frames — chaque frame est la planche complète (8 × 3 tuiles), grille du document réglée sur 24 px. C'est le fichier à ouvrir dans l'éditeur.
- `falaises/<ambiance>/planche_f1..f4.png` : les mêmes frames en tilesheet PNG, pour un moteur quelconque.
- `falaises/<ambiance>/animation.png` : APNG de prévisualisation (4 frames, 150 ms).
- `falaises/zones/<zone>/…` : cinq zones map falaise rendues **pixel perfect** depuis les tuiles canoniques, en calques séparés `ground` (terrain praticable), `falaise` (roche structurelle) et `decor` (superpositions), plus le composite animé :
  - `ground_jour.png` / `ground_nuit.png`, `falaise_jour.png` / `falaise_nuit.png`, `decor_jour.png` / `decor_nuit.png` : les calques isolés ;
  - `zone_<ambiance>.png` : composite des trois calques, dans les 6 ambiances ;
  - `zone_jour_anim.png` : APNG 4 frames du composite.
  Zones fournies : `col_montagne`, `plateaux_ponts`, `gouffre_passerelle`, `corniche_escalier` et `worldmap` (32 × 18 tuiles, toutes les tuiles du tileset y servent).
- `falaises/falaises.json` : manifeste (nom, usage, animation, position sur la planche de chaque tuile).
- `apercu_falaises.html` : aperçu autonome hors ligne, animé : sélecteur d'ambiance, lecture frame par frame, grille des 24 tuiles et scène d'assemblage.

Raccords : `face_roche*` se juxtapose sans couture sur les 4 côtés ; `sommet_herbe`, `sommet_roche_nu` et `coin_haut_*` coiffent les parois ; `bord_gauche/droit` dessinent les flancs à bossages ; `pente_*` et `escalier_*` changent de niveau ; `pont_corde`/`pilier_corde` et `pont_bois`/`pilier_bois` enjambent les vides à même hauteur ; `echelle` monte le long d'une paroi.

Animations (13 tuiles animées, 11 fixes) : frange herbeuse des sommets, plateau, pentes, escaliers, tablier et cordes des ponts (balancement), touffes d'herbe, lierre, brume — 4 frames à 150 ms, le tempo des animations PMD. Les tuiles fixes sont garanties identiques sur les 4 frames par `verify_falaises.py`.

### Zones map : rendu pixel perfect

Chaque zone est un plan de tuiles **canoniques** : le rendu copie exactement les cellules de la planche (aucune transformation, aucun filtrage), alignées sur la grille de 24 px. `verify_falaises.py` le prouve cellule par cellule : chaque cellule d'un calque est soit vide, soit égale au pixel près à la tuile canonique de sa classe, et le composite est exactement `ground + falaise + decor`. Les jonctions suivent trois règles : surface pleine (`sommet_herbe`) contre un escalier, piliers de pont posés sur les bordures, flancs fondus en paroi quand deux massifs se touchent.

## Contenu du kit

- `apercu_pmd.html` : aperçu autonome, hors ligne. Le bouton **« Base seule — magenta »** retire le paysage pour vérifier les ouvertures. Les cases permettent de masquer chaque calque.
- `salles/` : compositions, bases transparentes, bases magenta et 24 Aseprite fixes.
- `calques/` : 11 PNG transparents par salle et par palette.
- `tiled/` : 24 cartes orthogonales à cellules de **8 × 8 px**, avec des tuiles reconstituant exactement les images.
- `fenetres_exterieur/` : masques et 72 couches de paysage positionnées.
- `exterieur/` : 6 ambiances complètes.
- `sprites/` : banque indépendante du premier kit modulaire ; ces éléments ne sont pas posés dans les salles.
- `falaises/` : tileset animé de falaises (24 tuiles, 4 frames, 6 ambiances) en feuilles Aseprite, tilesheets PNG, APNG et exemples d'assemblage.
- `apercu_falaises.html` : aperçu autonome animé du tileset de falaises.
- `kit.json` : dimensions, accès, calques et chemins.
- `source/` : retouches natives retenues, sources du panorama, règles et scripts de reconstruction.

Le hall mesure **1280 × 544 px** ; les autres pièces **648 × 432 px**. Les grilles Aseprite et Tiled sont réglées sur 8 px. Les PNG ne sont pas pixellisés en gros blocs de 8 px.

Les cartes ne sont pas un jeu intégré : collisions, transitions et déclencheurs de porte doivent être configurés dans le moteur. Les accès sont décrits dans `kit.json` et `source/regles_acces.json`.

## Reproduction et contrôles

```bash
pip install -r source/requirements.txt
python source/rebuild_landscapes.py
python source/rebuild_kit.py
python source/build_preview.py
python source/verify_pmd.py
python source/build_falaises.py
python source/verify_falaises.py
```

`build_falaises.py` régénère le tileset de falaises (planches, feuilles Aseprite, APNG, exemples, manifeste, aperçu) ; `verify_falaises.py` relit les feuilles Aseprite, compare les cels aux PNG, contrôle les tuiles animées/figées, les raccords sans couture, les 6 ambiances et l'aperçu hors ligne, puis écrit `controle_falaises.json`.

Le contrôle relit et recompose les PNG, Aseprite et cartes Tiled ; vérifie les bases transparentes/magenta, les 6 vues alignées, les calques vides et l’unique porte nord. Validation par code, pas par ouverture dans l’interface d’Aseprite.

Les retouches ont été faites avec le générateur à partir des images du kit. Les images du jeu fournies par l’utilisateur ont servi à comprendre le principe des passages, pas à être collées dans les décors. **Le tout premier ZIP de la guilde et les archives de la terrasse approuvée restent inchangés.**
