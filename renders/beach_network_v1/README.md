# Beach Network V1 — six plages raccordables, ciel sans lune

[Ouvrir l’atelier animé](index.html) · [Ensemble jour](BeachNetwork_ensemble_jour.png) · [Ensemble nuit](BeachNetwork_ensemble_nuit.png) · [Plage et ciel corrigé](BeachNetwork_plage_ciel_corrige_nuit.png) · [Plan des connexions](BeachNetwork_plan_connexions.png)

## Ce qui est livré

Six **nouvelles compositions générées** d’après `DSVFS.png`, puis normalisées et séparées en surfaces visibles. Ce ne sont pas six variantes d’une même plage : leurs accès forment un réseau 3×2, suivant la méthode structurelle du lot Ledian souterrain.

| Placement | Carte | Accès |
|---|---|---|
| haut gauche | 01 · Anse du couchant | E, S |
| haut centre | 02 · Carrefour des palmes, T | W, E, S |
| haut droite | 03 · Anse des roches rouges | W, S |
| bas gauche | 04 · Passage des écueils | N, E |
| bas centre | 05 · Grand carrefour, croix | N, E, S, W |
| bas droite | 06 · Anse des marées | N, W |

Sept liaisons : 01E–02W, 02E–03W, 04E–05W, 05E–06W, 01S–04N, 02S–05N, 03S–06N. La sortie 05S est réservée à une extension, pas à une destination inventée.

- Modules : **512×512**, ensemble terrain : **1536×1024**.
- Accès centrés : **96 px**, intervalle `[208,304)`, profondeur 48 px. Le noyau de 16 px au bord est identique pour toutes les orientations ; transition sur le reste.
- Positions de contrôle, alignées 8 px : N `(256,8)`, S `(256,504)`, W `(8,256)`, E `(504,256)`. Les quinze accès rejoignent le centre avec une distance aux obstacles d’au moins 8 px dans le masque de sable.
- Deux modes : jour et **filtre Abyss exact** pour le terrain de nuit.
- Par module/mode : sept partitions de terrain + un calque par accès, composition et OpenRaster. Les originaux du dépôt ne sont pas écrasés.

## Ciel et petits nuages

Le ciel a été **régénéré** avec la référence nocturne PMD : aucune lune, aucun halo lunaire, aucun nuage intégré au fond. Ce n’est pas le crop lunaire rejeté. Fond exporté : 1536×192 ; une bande de 112 px est présentée au-dessus de l’ensemble ou de la plage de référence. Les modules de terrain individuels n’embarquent pas de ciel ; il ne se répète donc pas entre les cartes assemblées.

Les trois nuages centraux complets d’une génération sur magenta ont été isolés, réduits uniformément en nearest-neighbour à **96×28 px maximum**, puis placés dans un overlay transparent de **512×112**. Les groupes tronqués aux extrémités du brut sont écartés. Au moins 24 px transparents aux deux bords du strip ; zéro magenta opaque retenu.

**Wrap horizontal explicite :** 1 px vers la gauche toutes les 125 ms, soit 8 px/s ; 512 pas donnent **64 secondes**. Dessiner des copies voisines du strip, appliquer `x = -(floor(t_ms / 125) % 512)` et clipper à la bande de ciel. La transition du pas 511 au pas 0 équivaut exactement à une translation supplémentaire de 1 px. C’est une translation en wrap, pas une déformation des nuages. Ciel et nuages nocturnes sont déjà colorés : **ne pas leur appliquer Abyss une seconde fois**. Le fond de jour est un bleu uni ; les nuages de jour sont éclaircis.

## Eau, écume et contacts aux rochers

Les nouveaux bassins ont **32 phases × 100 ms = 3,2 s**, avec deux pistes distinctes : `06_eau` et `07_ecume`. Toutes les pistes ont plusieurs images effectivement différentes, pas 32 copies. Les couleurs de l’eau sont remappées à partir des compositions ; le mouvement de base réutilise le guide Beach V1, sans revendiquer un cycle officiel extrait du jeu.

Un **nouveau liseré de contact périodique**, jusqu’à 3 px, dépose puis retire de l’écume autour du rivage et au pied des rochers. Il reprend les couleurs de l’écume côtière la plus proche ; le feuillage est exclu. Les calques rocheux restent immobiles. La phase zéro conserve exactement la composition statique. Ce mouvement local est une nouvelle réalisation, **pas une restauration des anciennes V2/V3 absentes de ce checkout**.

La plage de référence reprend le terrain et la base d’animation V1 réellement disponibles : 702×466, 64 phases de 50 ms, auxquels s’ajoute ce liseré animé. Ancien ciel retiré, nouveau ciel/nuages séparés. Les atlas de cette scène de référence sont livrés ; les PNG V1 historiques restent dans leur propre lot.

Les nuages bouclent en 64 s, l’eau en 3,2 s : la scène entière revient exactement au même état après 20 cycles d’eau. Le bouton **Raccord 0 ↔ 64 s** permet de comparer ces états. La fermeture temporelle exacte ne constitue pas à elle seule une appréciation artistique du mouvement.

### Format des atlas

Atlas WebP **lossless**, 8 colonnes. `manifest.json` donne pour chaque piste `file`, `rect: [x,y,w,h]`, `columns`, `frames`, et la cadence dans son mode. Les frames des six modules existent aussi en PNG 512×512 transparents. Pour reconstruire une frame d’atlas, découper sa cellule et la poser en `(x,y)` sur le canevas de la map. Remplacer le calque fixe eau/écume par sa frame courante, sans conserver l’écume fixe par-dessus.

## Import et limites

- Les PNG `BeachNetwork_<module>_<mode>_<calque ou frame>.png` des dossiers `calques/` et `animation/` sont sur grille **8 px**, avec basenames uniques. Aucun redimensionnement à l’import. Ne pas importer les contrôles de sol, les compositions génériques ou les atlas WebP comme des tuiles PNG nommées identiquement.
- Prévoir des layers terrain/eau/écume séparés et un background/overlay pour ciel/nuages. La configuration exacte du scroll, des animations, des collisions et des warps dépend du moteur ; **aucun Ground natif ni runtime PMDO validé n’est fourni ici**.
- La scène de référence est en 702×466 pour conserver sa géométrie. Ne pas l’étirer pour atteindre un multiple de 8 ; les copies PAD8 V1 historiques concernent son terrain de base, pas ces nouveaux atlas.
- `controle_sol.png` est un masque chromatique de vérification, **pas une collision moteur**. Des pixels de sable peuvent subsister dans des anfractuosités de bord non déclarées comme ports ; bloquer les limites hors accès lors du paramétrage des collisions.
- Les bandes centrales de sable se raccordent exactement. **Tous les contours rocheux de la jonction ne sont pas certifiés seamless** ; inspection à 1× et ajustements moteur restent nécessaires. La carte 03 conserve quelques ombres brunes plus plates et des roches plus massives.
- Les calques sont des partitions de **surfaces visibles**, pas des objets natifs complets. Le groupe végétal isole principalement le feuillage ; certains troncs/ombres peuvent rester dans les surfaces minérales. Les dessous cachés ne sont pas reconstruits.
- Les compositions générées 1024² sont ramenées uniformément à 512² en nearest-neighbour, puis quantifiées dans la palette de `DSVFS.png`. Les raccords utilisent le prélèvement `(296,168)–(392,216)`, transposé/inversé selon les accès et précomposé dans la transition. **Ce pipeline n’est pas la filière Métano native pixel-identique** et ne doit pas être présenté comme telle.

## Provenance, reconstruction et vérifications

Sources de matière : `DSVFS.png` ; ciel : référence de style `bgnightbackgroundpmdskyda.png` ; structure : lot Ledian. Références PMD : Nintendo / Creatures / GAME FREAK / Chunsoft ; pas de licence nouvelle revendiquée. Le manifeste conserve les hashes des neuf bruts et de la plage source.

Dans le dépôt : `source/beach_network_v1/` contient guides, build, template, tests et packaging ; `bruts/` contient les générations originales, dont la première carte 03 remplacée par sa correction. Le **ZIP de livraison exclut les bruts et les sources de reconstruction** pour éviter la duplication ; il contient les exports et un viewer utilisable avec leurs chemins locaux. Extraire l’archive entière. Lancer au besoin `python -m http.server 8000` depuis le dossier extrait, puis ouvrir `http://localhost:8000/` sur la même machine.

Reconstruction depuis la racine du dépôt, avec Pillow, NumPy, SciPy et le lot Beach V1 présent :

```sh
.venv/bin/python source/beach_network_v1/build.py
.venv/bin/python source/beach_network_v1/verify.py
.venv/bin/python source/beach_network_v1/package.py
node source/beach_network_v1/test_viewer.cjs
.venv/bin/python source/beach_network_v1/package.py
```

Le second packaging inclut le rapport DOM actualisé. Voir `verification.json`, `verification_viewer.json`, `verification_package.json`. Les tests de pixels/codec/topologie et la simulation DOM **ne remplacent ni un navigateur réel, ni l’approbation artistique, ni PMDO**.
