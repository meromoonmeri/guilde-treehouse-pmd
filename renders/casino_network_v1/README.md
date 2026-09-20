# Casino des braises — nouveau réseau multicalque

[Atelier interactif](index.html) · [Composition](Casino_reseau_decore.webp) · [Aperçu animé](Casino_apercu_anime.webp) · [Pack autonome](Casino_pack.zip)

## Réseau et aménagement

### Fond magenta et kiosques prêts à recevoir un PNJ

Les zones sont conçues/générées sur **magenta `#FF00FF`**. Les exports transparents servent à l’import, ils ne remplacent pas les références sur fond magenta. Dans le dépôt : `Casino_terrain_magenta.webp` et `Casino_reseau_magenta.webp` montrent le terrain et la composition sur magenta pur, sans changer les pixels visibles.

Le dossier **`editeur/`**, également inclus dans le ZIP, fournit des plans arrière/avant pour le kiosque généré et Krow Bank. Ils recomposent exactement les sprites existants. **Aucun Pokémon n’est dessiné dans ces kiosques** : `placements_pnj.json` indique trois postes réservés, les repères de pieds du marchand, le point d’interaction du client et des suggestions de collision.

Dans l’éditeur, remplacer le kiosque fusionné par : **arrière → Pokémon indépendant → devant/comptoir**. Ne pas garder l’ancien sprite complet par-dessus. Les repères sont des indications visuelles en pixels, à adapter au pivot/gabarit du Pokémon ; ils ne constituent pas des entités PMDO déjà configurées. Le motif de tête de Murkrow de Krow Bank appartient à son architecture, pas à un marchand intégré. Laisser le poste marchand et les accès clients libres de mobilier.

Le viewer existant conserve ses38instances ; ce kit prépare l’ajout ultérieur de PNJ dans l’éditeur. Pour exporter une map ou un secteur sur magenta tout en conservant les calques transparents :

```sh
python export_png.py --sector accueil --magenta
```


**Nouveau terrain généré indépendamment**, à la demande de l’utilisateur : les matières de Ledian servent de référence, mais la map n’est ni l’ancienne salle jointe, ni un réarrangement de ses pixels. Une seule composition continue1024×1024 assure la continuité spatiale ; elle se divise en quatre secteurs512×512 :

```text
Scène des braises ─── Salon des mises
       │                    │
Accueil & change ──── Salle des tables
       │
Entrée sud
```

Quatre liaisons internes et une entrée extérieure. Les parois encadrent les passages. Les secteurs partagent une image continue : **les permuter arbitrairement n’est pas certifié raccordable**.

**38 instances de calques indépendantes** :
- 5 partitions de terrain : sol/passages, fond, bordures gauche/droite, premier plan ;
- 4 calques de tapis, issus d’un motif natif continu, sans barre de bordure entre les secteurs ;
- 1 estrade et 1 structure de rideaux ;
- 2 kiosques générés et 1 objet natif Krow Bank ;
- 4 tables de jeu ;
- 2 corps de fourneau générés, sans feu peint ;
- 8 supports de brasero natifs ;
- 10 instances de flammes natives, séparées des supports/fourneaux.

Le terrain a été généré vide **avant** les objets : retirer un meuble révèle le terrain intact, pas un trou reconstruit. Les partitions rocheuses restent des surfaces visibles, pas des volumes complets déplaçables. Les surfaces planes sombres font partie des plafonds/limites rocheuses de la génération.

Le tapis reprend des pixels de `Ledian_Dojo_Objects.png`, rectangle `(176,136)–(232,176)` : répétition de patches8px et raccord des bordures, sans étirement ni recoloration. Les nouvelles structures ont été générées avec les références de couleur et de perspective de Ledian et de Krow Bank, puis normalisées uniformément en nearest-neighbour à l’échelle des objets. Elles ne sont **pas** des sprites natifs extraits du jeu.

## Flammes réellement canoniques Ledian/Halcyon

Référence épinglée : **Palikadude/Halcyon**, commit `da6c2130d641507447e6386a5e47a296e8cb4c71`.

- `Data/Ground/ledian_dojo.rsground`, calque1 « Objects Under » ; instance sur les cellules `(14,11)–(18,19)`, grille8px.
- Banque `Content/Tile/Ledian_Dojo_Animated.tile`.
- **4 poses dans l’ordre réel de la map**, chaque track ayant `FrameLength: 6`.
- Le viewer interprète6ticks à60Hz : **100ms par pose**, boucle400ms. Il ne s’agit pas d’une cadence inventée par interpolation.
- Chaque brasero complet est reconstruit en **32×64**, à sa taille native. Les lignes0–39 forment la flamme32×40 ; les lignes40–63 constituent le support, invariant sur les quatre poses.
- Aucune mise à l’échelle, recoloration, rotation, miroir, déformation ou translation de texture dans les frames natives. Les éléments changent de pose ; ce n’est pas un scroll d’image fixe.
- Les fourneaux sont de **nouveaux corps générés**, avec une ouverture vide : ils reçoivent les mêmes flammes natives, sans agrandissement, sur leur propre calque. Ne pas présenter le corps du fourneau comme un sprite canonique.

`flammes_provenance.json` donne hashes, cellules et tracks complets. `animations/` contient les quatre braseros entiers de contrôle et les quatre PNG de flamme. `objets/brasero_support.png` est le support séparé. Tous sont des PNG à alpha binaire.

Krow Bank est repris sans modification depuis l’étude native précédente, qui identifie Murkrow via `Bank_Owner` dans les scripts Métano. Les sources et crédits ne sont pas remplacés par une revendication de création native originale. Ressources PMD : auteurs/contributeurs Halcyon et ayants droit concernés ; présence publique ne signifie pas licence générale de redistribution libre.

## Contrôles du viewer

Choisir le réseau ou un secteur, afficher le terrain vide, activer un groupe ou un objet précis, arrêter les flammes et parcourir les quatre poses. Le mode **Accès** est une annotation de travail, pas une collision moteur.

Chaque meuble a une position indépendante, modifiable par pas8px. Les flammes suivent automatiquement leur support ; masquer un support masque aussi son feu à l’écran. Un export isolé de flamme reste possible. **Exporter positions** conserve les changements locaux dans un JSON ; ils ne modifient pas les fichiers du dépôt et ne configurent pas PMDO.

Les exports PNG de vue retirent les annotations. Pour éviter les restrictions de canvas en `file://`, servir le dossier avec `python -m http.server 8000`, puis ouvrir `http://localhost:8000/` sur la même machine.

## Import / PNG alignés

`manifest.json` contient ordre, fichiers, positions, tailles, hôtes des flammes, cadence et secteurs. Les objets compacts restent séparés des grands calques de terrain. **L’exporteur inclus fabrique tous les PNG alignés** à1024×1024, ou512×512 pour un secteur, sans resampling :

```sh
python -m pip install Pillow
python export_png.py --frames
python export_png.py --sector accueil --frames
python export_png.py --sector scene --frames
python export_png.py --sector salon --frames
python export_png.py --sector jeux --frames
```

Sortie `export_png/`, noms uniques préfixés par secteur, ordre dans `calques.json`, origine `(0,0)`. Les fichiers de flamme ont quatre poses de100ms ; ne pas les empiler comme quatre calques fixes simultanés. Tous les canevas et positions par défaut sont sur grille8px. L’exporteur omet les calques entièrement transparents hors du secteur.

Le ZIP autonome contient calques, objets, frames, viewer, manifeste, exporteur et notice. Il exclut les bruts, sources de rebuild et grosses prévisualisations redondantes ; les liens correspondants sont masqués dans sa copie du viewer.

## Vérifications et limites

Les hashes des sources Ledian restent inchangés. Terrain recomposé exactement ; objets natifs comparés à la source ; ordre des frames, cadence et recomposition support+flamme vérifiés. Le chemin principal des tapis relie les quatre secteurs avec8px de distance aux empreintes rectangulaires des meubles par défaut. **Ce contrôle de placement n’est pas un système de collisions natif, ni une validation des hauteurs de terrain.**

Aperçu WebP animé : les pixels visibles et l’alpha sont exacts. Son codec peut modifier les RGB invisibles sous alpha0 ; les PNG canoniques ne subissent pas cette différence.

Pas de Ground natif, warps, dialogue, logique de jeu de casino ni runtime PMDO testé. Les passages et l’accord artistique restent à apprécier visuellement et en moteur. Les positions exportées nécessitent une intégration manuelle. Simulation DOM ≠ navigateur graphique.

## Reproduire depuis le dépôt

```sh
.venv/bin/python source/casino_network_v1/prepare.py
.venv/bin/python source/casino_network_v1/build.py
.venv/bin/python source/casino_network_v1/verify.py
.venv/bin/python source/casino_network_v1/package.py
node source/casino_network_v1/test_viewer.cjs
.venv/bin/python source/casino_network_v1/package.py
```

Pillow, NumPy, SciPy nécessaires au build. Les sept bruts sont archivés en WebP lossless avec hashes de leurs PNG initiaux et de leurs pixels. La première génération de terrain, trop panoramique, n’est pas utilisée ; `terrain_corrige.webp` est la version carrée retenue. Le générateur a dessiné trois corps de fourneau malgré la consigne d’un seul : le corps central complet a été isolé, sans importer les deux autres dans le casino.

Pour éviter des duplications inutiles, le terrain vide intermédiaire est régénérable depuis le brut corrigé, et les PNG alignés sont exclus du Git. L’ancien viewer Beach V1 racine reste inchangé et autonome ; son ancienne copie de7Mo dans `renders/beach_layers_v1/index.html` devient un lien de redirection vers lui, sans modification des images ou du ZIP Beach V1.
