# Lot 04 — entrées aride et grotte violette, sud → nord

## Demandes traitées

Les deux prochaines références du programme en attente, conformément à la correction en vigueur (arrivée au sud, bouche/issue au nord, matériaux canoniques, calques indépendants) :

- **`entrancearidedungeonpmdsky.png`** → `exports/zones_south_north_v4/arid_cave_entrance` — **480×384, 8 calques** : sol sable, chemin sable, falaise nord, pied de falaise, bouche de grotte, arbres morts, rochers, cailloux. La bouche native (source166,18,246,100) est déplacée au centre ; les deux gros rochers restent à leur emplacement natif (translation nulle, calque indépendant) et une petite pierre est repositionnée. La bande nord est reassemblée sans miroir (modules source0..166 puis 246..408).
- **`roadundergound.png`** → `exports/zones_south_north_v4/purple_two_exit_cave` — **424×360, 8 calques** : fond sombre, sol violet moucheté, blocs ouest/est, bande nord, deux bouches, grappes de cristaux. Le panneau natif (source40,96,464,404) est traduit tel quel ; la bande nord est reassemblée uniquement depuis les blocs centraux (source204..296) car les modules de coin contenaient des pixels de marge sombre ; les deux bouches sombres et leurs seuils de pierres sont déplacés (source96..208 → canvas36, source296..408 → canvas276) ; dix grappes de cristaux sombres sont reimplantées ; le gros cristal du bas-gauche reste sur place.

## Méthode (inchangée depuis V3)

- Chaque pixel visible est prélevé à l'identique des sources natives ; les NPZ `*_source.npz` portent les coordonnées `[source,x,y]` par pixel (`-1` = transparent).
- Sols et chemins : chevauchement de patches natifs (jointure calculée sur le coût de couleur), sans mélange de couleurs.
- Parois, bouches, arbres, rochers, cristaux : translation de modules entiers. **Aucune recoloration, rotation, miroir, échelle ni pixel généré.**
- Masque de chemin reliant le bord sud aux entrées/issue(s), avec contrôle de dégagement 8 px. C'est un contrôle hors moteur, pas une collision validée.
- TSX 8 px descriptifs ; pas de `.rsground`, pas de collision, pas de warp.

## Contrôles

`package.py` exécute les 12 tests dédiés (`test_build.py`) avant d'écrire le registre du programme complet, `verification.json` et le ZIP. Baseline de contrôle des sources : **`3d4ea6f0`** (commit de base de la branche de session ; l'historique a été linearisé, les fichiers sources y sont byte-identiques au baseline `438b9288` de V3).

12 tests PASS à la construction. **Art à examiner ; PMDO/Tiled/collisions/warps NOT TESTED.**

## Reproduction

```bash
.venv/bin/python source/zones_south_north_v4/build.py
.venv/bin/python source/zones_south_north_v4/package.py
```

Galerie : `apercu_entrees_sud_nord_v4.html` (racine du dépôt).
