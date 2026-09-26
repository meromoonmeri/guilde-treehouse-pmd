# Entrée Grotte des Cascades — projet PMDO 0.8.12

Projet d’édition autonome `entree_grotte_cascade_sud_nord` : un Ground `egc1_entree_grotte_cascade` au format **4:3 vaste**, 768 × 576 px, grille 96 × 72 cases de 8 px (`TexSize=1`).

## Installer

- **Projet séparé** : extraire le ZIP et copier le dossier `entree_grotte_cascade_sud_nord` dans `PMDO/MODS/`, l’activer, puis ouvrir le Ground dans l’éditeur.
- **Mod existant** : lancer `python INSTALLER.py /chemin/PMDO/MODS/mon_mod --dry-run`, puis relancer sans `--dry-run`. Fermer PMDO et sauvegarder le mod avant l’installation.

## Calques du Ground (bas → haut)

| # | Calque | Animation |
|---|---|---|
| 00 | Sol complet généré (sous-couche) | fixe |
| 01 | Eau de la caverne | 12 phases × 10 ticks, boucle 2 s |
| 02 | Parois rocheuses et rochers | fixe |
| 03 | Chemin sud → nord | fixe |
| 04 | Voûte et seuil nord | fixe |
| 05 | Vide, `Layer=4` (Top) | pour les éléments d’avant-plan |

La matière d’eau est générée sur magenta. Son palette-cycling et ses reflets sont une animation proposée pour ce projet, **pas un cycle officiel récupéré**.

## Marqueurs et collisions

- `entrance` au sud, sur le chemin ; `donjon_seuil` au nord, devant le passage. **Aucun warp ni destination de donjon n’est configuré.**
- Les collisions sont déduites du corridor généré. Un dégagement 16 × 16 px et une recherche de chemin sud → seuil passent les contrôles de grille. Cela ne valide ni le collider réel, ni la marche, ni le gameplay PMDO.

## Méthode et provenance

- Référence d’ambiance et de composition : `Waterfall_Cave_ledge_TDS.png`. Elle a guidé le générateur ; **aucun morceau de cette map n’est collé dans la nouvelle scène**.
- Le décor complet, le sol complet et la matière d’eau sont des rendus générés sur magenta. Les images brutes font 1200 × 896 px, puis sont réduites uniformément ×0,643 et recadrées au centre en 768 × 576 px. Les classes sont réduites séparément pour éviter le mélange de la clé magenta.
- **Le terrain est généré en DA PMD, pas composé de pixels natifs certifiés.** Le magenta sert à séparer l’eau et le hors-carte. Chaque source, hash, règle de détourage, calque et limite est décrite dans `manifest.json`.
- Les images sont des plans d’une composition, pas des objets dont toutes les faces cachées auraient été reconstruites.

## Reproduction et contrôles

Depuis la racine du dépôt :

```sh
.venv/bin/python source/entree_grotte_cascade_sud_nord_v1/build.py
.venv/bin/python -m unittest source.entree_grotte_cascade_sud_nord_v1.test_build -v
.venv/bin/python source/entree_grotte_cascade_sud_nord_v1/package.py
```

Le build utilise Pillow, NumPy, SciPy et les codecs de `source/pmdo_cote/`. Les tests relisent les PNG, les couches OpenRaster et le Ground/tileset reconstruit. **Aucun test de rendu ou de gameplay dans PMDO n’est revendiqué.**
