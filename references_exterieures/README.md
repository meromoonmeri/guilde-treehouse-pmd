# Layouts extérieurs PMD — références jour / nuit

Les nouveaux layouts de référence sont livrés en **plusieurs calques fixes**, selon la méthode du kit précédent : conserver le cadrage de la référence, préparer une native complète, séparer des plans disjoints, reconstituer l'image, puis exporter les mêmes données en PNG, Aseprite et Tiled.

## Scènes

| Identifiant | Layout repris | Dimensions | Ambiances |
| --- | --- | --- | --- |
| `cascades` | îlot suspendu, chutes d'eau, eau et végétation de rive | 592 × 448 px | Jour, nuit |
| `prairie_maritime` | prairie fleurie, chemin, reliefs latéraux et mer au nord | 504 × 504 px | Jour, nuit |
| `cap_cotier` | prairie maritime, chemin, maison-courrier, falaise et océan | 960 × 600 px | Jour, nuit |

Les trois scènes reprennent les **layouts** des références ajoutées le 11 septembre 2026. Les positions structurantes sont conservées entre les deux ambiances : l'îlot, les chutes, le bassin et les rives pour `cascades` ; le sentier, les parterres et les retours rocheux pour `prairie_maritime` ; le chemin, la maison-courrier, le plateau, la falaise et la mer pour `cap_cotier`.

## Cinq calques par scène et par ambiance

### Sanctuaire des cascades

1. `00_ciel_eau` — ciel, horizon et nappe d'eau ;
2. `01_nuages_astres` — nuages de jour ou étoiles de nuit ;
3. `02_ilot_rocheux` — îlot rocheux et relief central ;
4. `03_cascades` — chutes et écume ;
5. `04_vegetation` — roseaux, buissons et premier plan.

### Prairie maritime

1. `00_ciel_mer` — ciel, horizon et mer ;
2. `01_nuages_astres` — atmosphère et étoiles nocturnes ;
3. `02_prairie_chemin` — prairie centrale et chemin ;
4. `03_reliefs` — falaises, rochers et rebords ;
5. `04_vegetation_fleurs` — fleurs, buissons et arbres.

### Cap côtier

1. `00_ciel_mer` — ciel, horizon et mer ;
2. `01_nuages_astres` — nuages de jour ou lune/étoiles de nuit ;
3. `02_terrain_falaise` — chemin, sol et paroi rocheuse ;
4. `03_maison` — maison-courrier et ses abords immédiats ;
5. `04_vegetation` — arbres, herbes, fleurs et liserés de prairie.

Les calques sont des PNG RGBA pleine taille et **disjoints** : chaque pixel opaque de la native appartient à un seul calque. Leur composition, dans l'ordre ci-dessus, redonne la native puis `compositions/jour.png` ou `compositions/nuit.png` exactement, pixel pour pixel. Il n'y a aucune animation dans cette livraison.

## Arborescence d'une scène

```text
references_exterieures/<scene>/
├── calques/{jour,nuit}/     # 5 PNG RGBA par ambiance
├── compositions/            # rendu reconstitué, PNG complet
├── bases/                   # base sans ciel/mer ni astres, transparente et magenta
├── aseprite/                # 1 image, 5 calques réels, sans timeline animée
└── tiled/                   # 5 image layers, grille 8 px
```

`bases/*_transparente.png` permet de vérifier que le fond a bien été séparé. `bases/*_magenta.png` est le témoin de contrôle sur `#FF00FF`. Les cartes Tiled portent des **image layers** liés aux PNG ; elles ne fournissent ni collisions, ni transitions ni autotiling.

## Méthode appliquée

1. Audit des ajouts `6cf427c` et `bc3afc6` : planche de cascades, GIF de prairie maritime, spritesheet d'étang et paire de références côtières jour/nuit.
2. Préparation des natives : un panneau propre est extrait de la planche de cascades ; l'image 0 du GIF donne le layout de `prairie_maritime` ; les vues côtières sont réduites au facteur entier 4. Les nuits des cascades et de la prairie maritime reprennent strictement leurs géométries de jour, avec une palette nocturne et des astres limités au ciel.
3. Attribution exclusive de chaque pixel à un plan sémantique. Cette partition est contrôlée avant l'export : pas de trou, pas de recouvrement, pas de pixel mélangé.
4. Reconstruction des compositions, des bases transparente/magenta, d'un Aseprite à une image et d'une carte Tiled à cinq image layers.
5. Vérification indépendante des pixels des PNG, cels Aseprite, liens Tiled, bases et aperçu autonome.

Les références d'entrée, le panneau de travail et une planche des quatre phases du GIF sont conservés dans `source/references_exterieures/entrees/`. Les natives préparées sont dans `source/references_exterieures/natives/`; leur provenance et leurs empreintes sont inscrites dans `source/references_exterieures/provenance.json`.

L'audit complet de la branche indiquée, notamment le fait que son rendu précédent est antérieur aux commits apportant ces références, se trouve dans [`../AUDIT_BRANCHE_01A082DB.md`](../AUDIT_BRANCHE_01A082DB.md).

## Reconstruction et contrôle

```bash
pip install -r source/requirements.txt
python source/prepare_references_exterieures.py
python source/rebuild_references_exterieures.py
python source/verify_references_exterieures.py
```

Ouvrir [`../apercu_references_exterieures.html`](../apercu_references_exterieures.html) pour afficher les trois scènes en jour/nuit et masquer chaque plan. Cet aperçu est autonome : les PNG sont intégrés en WebP sans requête réseau.
