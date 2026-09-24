# Forêt Render V1 — composition finale magenta, cinq calques

## Correction de méthode

Cette passe suit la méthode des rendus de zones demandée :

1. le générateur produit **la composition finale complète** sur fond magenta `#FF00FF` ;
2. la composition est normalisée à la taille de la map et nettoyée par chroma-key ;
3. les cinq calques sont découpés depuis cette même composition finale ;
4. leur recomposition doit être exactement la composition générée nettoyée.

Les références canoniques PMD servent ici à conserver la DA et l’impression d’un autre lieu du même monde. Elles ne remplacent pas les pixels générés : ce lot est un **render généré référencé**, pas une reconstruction pixel-perfect de la map canonique V3.

La deuxième map n’est pas produite dans cette passe. On valide d’abord cette forêt seule.

## Les cinq calques

- `01_sol_chemin` — sol, herbe et chemin central ;
- `02_vegetation` — végétation basse et détails de terrain ;
- `03_cliff_grotte` — masse rocheuse et ouverture ;
- `04_arbres` — arbres et troncs latéraux ;
- `05_premier_plan` — masses et éléments proches de la caméra.

Les cinq PNG sont des masques alignés de la même image finale. Le viewer permet de les afficher/masquer individuellement et de vérifier la recomposition.

## Livrables

- Viewer : `apercu_forest_cave_render_v1.html` ;
- projet PMDO : `exports/forest_cave_render_v1_pmdo/` ;
- archive : `exports/forest_cave_render_v1_pmdo_pack.zip` ;
- composition magenta : `provenance/generation/forest_cave_final_composition_magenta.png` ;
- composition alpha : `review/composition_final_transparent.png` et `review/composition_final.png`.

## Installation PMDO

Copier `exports/forest_cave_render_v1_pmdo/` dans `PMDO/MODS/`, activer **Forêt Render Magenta V1**, puis ouvrir `forest_cave_render_v1` dans l’éditeur Ground.

Pour fusionner dans un projet existant :

```sh
python INSTALLER.py "CHEMIN/PMDO/MODS/mon_mod" --dry-run
python INSTALLER.py "CHEMIN/PMDO/MODS/mon_mod"
```

Le pack fournit une Ground 8 px, cinq banques `.tile`, un index complet, un namespace unique et deux marqueurs (`entrance`, `donjon_seuil`). Aucun warp automatique ni destination de donjon inventée.

## Validation

Le contrôle exige : fond magenta aux coins du guide, cinq masques sans recouvrement, recomposition exacte de la composition générée, résolution des banques `.tile`, Ground et index. Le statut PMDO graphique, GPU, déplacement réel, collisions en mouvement et warp reste à tester dans le moteur.

## Reproduction

```sh
.venv/bin/python source/forest_cave_render_v1/build.py
.venv/bin/python source/forest_cave_render_v1/verify.py
.venv/bin/python source/forest_cave_render_v1/package.py
```
