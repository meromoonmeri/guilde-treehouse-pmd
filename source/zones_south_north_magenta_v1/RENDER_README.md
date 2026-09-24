# Forêt Render V1 — composition finale générée sur magenta

Cette livraison corrige la méthode : le rendu généré sur fond magenta est bien la **composition finale** de cette nouvelle map. Les références canoniques servent à conserver la DA PMD et la continuité du lieu, mais les textures finales de ce rendu sont générées, pas annoncées comme des pixels natifs exacts.

## Pipeline

1. Référence de la forêt sud–nord et références PMD canoniques.
2. Génération de la scène complète sur fond chroma-key `#FF00FF`.
3. Détourage du magenta par clé/flood-fill, conservé comme transparence alpha hors silhouette.
4. Le rendu généré nettoyé reste la composition finale, sans remplacement par les pixels canoniques.
5. Découpage en cinq calques et recomposition finale.
6. Export Ground PMDO 8 px, aperçu et archive.

Le résultat doit donner l’impression d’une **autre zone du même endroit** : même échelle, même direction sud → nord, même langage de matière PMD, mais nouvelle composition, nouvelle végétation et nouvelle falaise/grotte.

## Les cinq calques

- `01_sol_chemin` : sol généré et chemin sud → nord ;
- `02_vegetation` : herbe, détails et végétation basse ;
- `03_arbres` : masses d’arbres et troncs ;
- `04_cliff_grotte` : falaise et ouverture de grotte ;
- `05_premier_plan` : pierres et petits détails devant.

La composition finale alpha est `review/composition_final.png` : les pixels du magenta et de son halo anti-aliasé sont transparents, sans remplissage canonique. Le guide magenta et la version alpha de contrôle sont conservés dans `provenance/guide/`. Les références utilisées et leurs hashes sont dans `provenance/references/`.

## Installation

Copier `exports/forest_cave_render_v1_pmdo/` dans `PMDO/MODS/`, activer le mod **Forêt Render V1 — composition magenta**, puis ouvrir `forest_render_v1`.

```sh
python INSTALLER.py "CHEMIN/PMDO/MODS/mon_mod" --dry-run
python INSTALLER.py "CHEMIN/PMDO/MODS/mon_mod"
```

Aucun warp ni destination de donjon n’est inventé. L’arrivée sud et le seuil nord sont des marqueurs à raccorder au projet de jeu.

## Statut

Le contrôle local vérifie le détourage, les cinq couches, la recomposition sans perte par rapport au rendu final, les banques `.tile`, l’index et l’installateur. Le rendu PMDO, le GPU, les collisions en mouvement et le gameplay ne sont pas testés dans cet environnement.

Reproduction :

```sh
.venv/bin/python source/zones_south_north_magenta_v1/render_build.py
.venv/bin/python source/zones_south_north_magenta_v1/render_verify.py
.venv/bin/python source/zones_south_north_magenta_v1/render_package.py
```
