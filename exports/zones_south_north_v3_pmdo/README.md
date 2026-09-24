# SouthNorth V3 — projet Ground PMDO 0.8.12

## Livraison

Le dossier `exports/zones_south_north_v3_pmdo/` est un **projet PMDO séparé** prêt à être copié dans `MODS`, et `exports/zones_south_north_v3_pmdo_pack.zip` est son archive.

Il contient deux propositions dans la direction demandée :

| Ground | Taille | Arrivée | Seuil nord |
|---|---:|---|---|
| `sn_v3_forest_cave` | 512 × 640 px, 64 × 80 cellules | bord sud | grotte de la forêt |
| `sn_v3_blue_rock_cave` | 512 × 408 px, 64 × 51 cellules | bord sud | entrée souterraine ouverte |

Le chemin contrôlé va du sud vers le seuil au nord. Les deux Ground ont des calques séparés pour le sol, le chemin, les parois, l’ouverture, les arbres ou les masses rocheuses. Les fichiers `.rsground`, `.tile`, `.dir` et `index.idx` sont des ressources natives sérialisées ; il ne faut pas réimporter les compositions PNG pour utiliser ce pack.

## Textures canoniques et provenance

Les pixels finaux proviennent des couches livrées par `exports/zones_south_north_v3/`. Aucun générateur d’image n’est appelé par le builder PMDO et aucun pixel des guides `generation/` n’entre dans les banques de tuiles.

- **Forêt** : référence `forêtglomypmdsky.png` pour le sol, la falaise blanche, la grotte, les pierres et la canopée ; arbres complets séparés issus des références natives Vast Steppe/Halcyon documentées dans le V3.
- **Roches bleues** : `rockroadpmd.png` pour le sol, le chemin et les masses de roche ; `undergroundpmd.png` pour le cadre et le portail ouvert, car la référence `rockroadpmd.png` ne contient pas de grotte.

Le terme « canonique » signifie ici **pixels sources documentés, vérifiés sans rotation, miroir, recoloration ni redimensionnement**. Les banques `.tile` de ce pack sont une nouvelle sérialisation 8 × 8 nécessaire au Ground ; elles ne prétendent pas être la récupération byte-identique des banques upstream originales lorsque celles-ci ne sont pas disponibles. Les hashes et les coordonnées de provenance sont conservés dans `provenance/`.

## Installation

### Projet séparé recommandé

1. Fermer PMDO.
2. Copier le dossier `zones_south_north_v3_pmdo` dans le dossier `MODS`.
3. Activer **SouthNorth V3 — entrées canoniques** en mode développement.
4. Ouvrir `sn_v3_forest_cave` ou `sn_v3_blue_rock_cave` dans l’éditeur Ground.

### Fusion dans un mod existant

Le `INSTALLER.py` inclus fusionne les en-têtes de tilesets dans l’index existant, sauvegarde l’index avant modification et refuse les fichiers déjà modifiés. Il ne copie pas l’`index.idx` du pack par-dessus celui d’un autre mod.

```sh
python INSTALLER.py "CHEMIN/PMDO/MODS/mon_mod" --dry-run
python INSTALLER.py "CHEMIN/PMDO/MODS/mon_mod"
```

La cible doit être le dossier qui contient `Mod.xml`. Sous PMDO récent, les scripts sont fournis dans le chemin historique `Data/Script/ground/` et dans le namespace `Data/Script/zones_south_north_v3_pmdo/ground/`.

## Calques Ground

Les calques reprennent exactement l’ordre et les noms du V3. Les couches de feuillage avant ou de couverture finale utilisent `Top = 4` afin de pouvoir passer devant le personnage ; les autres couches restent sur le plan normal. Les calques sont des tuiles statiques, avec `FrameLength = 60` pour leur lecture native.

Les entités livrées sont volontairement minimales :

- `entrance` : arrivée sud ;
- `donjon_seuil` : seuil au nord ;
- aucun Pokémon, objet, spawner ou script narratif ;
- aucune destination de donjon ni téléportation automatique.

La destination réelle, le retour, les callbacks, la sauvegarde et l’annulation doivent être configurés dans le projet de jeu qui connaît les noms des donjons. Un marqueur visuel ou un trou dans le dessin ne suffit pas à créer une transition PMDO.

## Collisions

Le Ground livre une base **conservatrice** : seules les cellules entièrement situées dans le chemin V3 avec une marge de 8 px sont libres (`Tags = 0`). Les autres cellules sont bloquées (`Tags = 1`) afin de ne pas transformer une surface peinte ou une falaise en sol praticable par accident.

Cette décision ne remplace pas une passe de level design : elle peut être élargie dans l’éditeur après contrôle des arbres, rochers, seuil et bordures. Le masque `review/*_path_mask.png` et les rendus `review/*_access_NOT_RUNTIME.png` ne sont pas des preuves de collision moteur.

## Contrôles réellement effectués

`pmdo_verify.py` vérifie :

- en-têtes, offsets, PNG 8 × 8 et alpha prémultiplié des banques `.tile` ;
- index complet et résolution de toutes les références Ground ;
- recomposition de chaque calque depuis les tuiles avec 0 différence de pixel ;
- dimensions, grille 8 px, ordre des couches, `Top = 4` et séparation des deux marqueurs ;
- cohérence du masque de chemin et des cellules libres ;
- installateur en simulation, fusion d’index, idempotence et refus d’écraser une carte modifiée.

**PMDO graphique, ouverture de l’éditeur, GPU, déplacement réel, animation affichée, collisions en mouvement et warps : NON TESTÉS dans cet environnement.** Le projet est préparé pour cette validation, pas déclaré comme une aventure jouable terminée.

## Reproduction

Depuis la racine du dépôt, avec l’environnement `.venv` contenant Pillow et NumPy :

```sh
.venv/bin/python source/zones_south_north_v3/pmdo_build.py
.venv/bin/python source/zones_south_north_v3/pmdo_verify.py
.venv/bin/python source/zones_south_north_v3/pmdo_package.py
```

Le builder ne touche ni aux images V3 ni aux anciens packs ; il ne remplace que sa propre sortie `exports/zones_south_north_v3_pmdo/`.

Crédits et droits : références PMD Sky, Halcyon/Vast Steppe et auteurs des ressources originales. La présence des fichiers dans ce dépôt ne crée pas une licence de redistribution supplémentaire.
