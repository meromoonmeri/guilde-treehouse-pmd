# 10 nouvelles maisons naturelles — lot 02

Nouveau lot généré avec les références de **Métano Town / Palika–Halcyon**. Le premier lot `sprites/maisons_metano/` reste inchangé.

1. Souche
2. Champignon
3. Calebasse
4. Fougère
5. Bambou
6. Cactus
7. Coco
8. Racines
9. Artichaut
10. Ruche

Huttes organiques, arrondies, sans toiture pyramidale. Ces dix dessins sont de nouvelles créations générées, pas des extractions officielles ni des recolorations du premier lot. Les références natives figurent dans `source/maisons_metano/references/` ; les cinq paires générées sont conservées dans `source/maisons_organiques_v2/`.

## PNG et échelle

- **`planche.png`** : rendu de présentation des dix maisons, agrandi ×2 sans lissage.
- `01_souche_jour.png` à `10_ruche_jour.png` : dix PNG RGBA indépendants.
- Dix variantes `_nuit.png` : palette dérivée, géométrie identique, pas d'éclairage animé.
- Chaque cadre mesure **112 × 128 px**, soit **14 × 16 cases de 8 px** ; taille visible comparable aux références Métano (80–110 px de large).
- Ligne de base y=120 px, ancre de placement géométrique (56,120). Certaines entrées sont décentrées : l'ancre ne constitue pas un déclencheur de porte.
- Les illustrations sont réduites sans étirement, palette limitée à 48 couleurs, fond magenta retiré. Pas de grille dessinée dans les PNG d'import.

## Éditeurs

- `Maisons_Organiques_V2_{jour|nuit}.png` : deux atlas **560 × 256 px**, cinq colonnes × deux rangées de structures.
- `.tsj` : Tiled, grille 8 px.
- `.tile` : ressources PMDO natives, noms **distincts du premier lot**. À importer et réindexer, pas à substituer aux ressources originales.
- `maisons.json` : rectangles de sélection des maisons, en pixels et en cellules.
- `../../apercu_maisons_organiques_v2.html` : aperçu hors ligne jour/nuit, grille et zoom.

Pour PMDO : Ground à `TexSize = 1` ; réindexer `Content/Tile/` après ajout. Structures fixes, un seul calque par maison ; pas d'intérieur ni d'animation de porte. Collisions, entrées, scripts et occlusion à configurer. Aucune validation en jeu effectuée.

Un placement de démonstration des dix maisons est fourni séparément dans `../falaises_modulaires_v2/decor/04_balcon/village.tmj`. Le calque maisons est indépendant du terrain. Il ne garantit pas l'accessibilité en jeu.

## Reconstruction / contrôle

```sh
python source/build_houses_metano.py --organic-v2
python source/verify_houses_metano.py --organic-v2
```

Pillow requis. Le test contrôle les vingt PNG, l'alpha, la palette, les dimensions, les atlas et leurs deux `.tile` natifs. Les commandes sans option continuent de cibler le premier lot. Voir `verification.json`.

Référence et attribution : [Palika / Halcyon](https://github.com/Palikadude/Halcyon), commit `da6c2130d641507447e6386a5e47a296e8cb4c71`. Les créations ne sont pas des sprites officiels. Voir les crédits de Halcyon pour les ressources de référence.
