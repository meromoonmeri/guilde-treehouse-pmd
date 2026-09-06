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

## Contenu du kit

- `apercu_pmd.html` : aperçu autonome, hors ligne. Le bouton **« Base seule — magenta »** retire le paysage pour vérifier les ouvertures. Les cases permettent de masquer chaque calque.
- `salles/` : compositions, bases transparentes, bases magenta et 24 Aseprite fixes.
- `calques/` : 11 PNG transparents par salle et par palette.
- `tiled/` : 24 cartes orthogonales à cellules de **8 × 8 px**, avec des tuiles reconstituant exactement les images.
- `fenetres_exterieur/` : masques et 72 couches de paysage positionnées.
- `exterieur/` : 6 ambiances complètes.
- `sprites/` : banque indépendante du premier kit modulaire ; ces éléments ne sont pas posés dans les salles.
- `kit.json` : dimensions, accès, calques et chemins.
- `source/` : retouches natives retenues, sources du panorama, règles et scripts de reconstruction.

Le hall mesure **1280 × 544 px** ; les autres pièces **648 × 432 px**. Les grilles Aseprite et Tiled sont réglées sur 8 px. Les PNG ne sont pas pixellisés en gros blocs de 8 px.

Les cartes ne sont pas un jeu intégré : collisions, transitions et déclencheurs de porte doivent être configurés dans le moteur. Les accès sont décrits dans `kit.json` et `source/regles_acces.json`.

## Échelle des salles — analyse comparative

Une analyse chiffrée du rapport **sprite ↔ salle**, avec les guildes de
*PMD: Halcyon* (Palikadude) comme référence, est disponible dans
[`ANALYSE_ECHELLE.md`](ANALYSE_ECHELLE.md).

Résumé : nos chambres font **×3 la surface de sol** d'une chambre de Halcyon
(×1,73 en linéaire), le hall **×2,3** la plus grande salle du jeu de référence, et nos
calques de décor sont vides là où Halcyon couvre 24 à 59 % du sol. Un facteur global de
**×0,65** sur le kit remet chaque salle dans les fourchettes de référence
(chambres ≈ 408 × 264 px, salles ≈ 432 – 480 × 288 – 312 px, hall ≈ 840 × 360 px).

Scripts de mesure et planches de comparaison : `analyse_echelle/`.
Gabarits de retravail salle par salle (grille 24 px, bande mobilier, passages,
sprites posés à 1:1) : `analyse_echelle/guides/`.
Base de dessin déjà mise à l'échelle cible : `calques_reduits/` et `salles_reduites/`
(brouillon à reprendre à la main, le rééchantillonnage adoucit le pixel art).
Banc de props ramené aux tailles PMD : `sprites_reduits/`. Proposition de mise en place
du mobilier (10 à 32 props par salle, calques `06`/`07` remplis) :
`analyse_echelle/placements/`.

## Reproduction et contrôles

```bash
pip install -r source/requirements.txt
python source/rebuild_landscapes.py
python source/rebuild_kit.py
python source/build_preview.py
python source/verify_pmd.py
```

Le contrôle relit et recompose les PNG, Aseprite et cartes Tiled ; vérifie les bases transparentes/magenta, les 6 vues alignées, les calques vides et l’unique porte nord. Validation par code, pas par ouverture dans l’interface d’Aseprite.

Les retouches ont été faites avec le générateur à partir des images du kit. Les images du jeu fournies par l’utilisateur ont servi à comprendre le principe des passages, pas à être collées dans les décors. **Le tout premier ZIP de la guilde et les archives de la terrasse approuvée restent inchangés.**
