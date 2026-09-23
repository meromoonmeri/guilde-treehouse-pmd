# Extension sud V2 — quatre cartes de plage supplémentaires

[Atelier animé](index.html) · [Quatre nouvelles cartes, jour, 1024×1024](BeachExt_extension_jour.png) · [Réseau de dix cartes, aperçu à 50 %](BeachExt_reseau_apercu_50pct.webp) · [Plan des connexions](BeachExt_plan_reseau.png) · [Pack autonome 07–10](BeachExtension_4modules.zip)

## Une véritable extension du réseau

| Nouvelle pièce | Type | Accès | Position dans le réseau |
|---|---|---|---|
| 07 · Carrefour des dunes | T | N, E, S | (1,2) |
| 08 · Carrefour du lagon | T | W, E, S | (2,2) |
| 09 · Place des palmes | croix | N, E, S, W | (1,3) |
| 10 · Baie abritée | coude / baie | N, W | (2,3) |

La sortie **05S**, précédemment libre, rejoint **07N**. Les nouvelles liaisons sont 05S–07N, 07E–08W, 07S–09N, 08S–10N et 09E–10W. Les quatre nouvelles cartes forment une boucle, et non quatre variantes isolées.

Le réseau complet contient **10 cartes, 12 liaisons et 27 accès**. Trois sorties restent disponibles : **08E, 09W, 09S**. Les emplacements (0,2) et (0,3) sont vides et transparents : aucune carte n’y est inventée. Les nouveaux carrefours portent le total à cinq carrefours T/croix.

**Les six compositions V1, leurs calques, leurs atlas, leur ciel et leur archive ne sont pas modifiés.** Seul le nouveau manifeste combiné attribue une destination à 05S. Les liens partagés pointent vers `../beach_network_v1/`, sans recopier les anciens assets dans chaque nouveau lot.

## Matière et calques

Cinq générations complètes ont été produites : quatre nouvelles maps et une correction de 07. Sa première sortie avait remplacé l’accès est par une côte infranchissable ; cette version est archivée mais **non utilisée**. La correction rétablit le passage de sable est et ferme les autres parties de ce bord par des rochers.

Références de génération : `DSVFS.png`, les modules V1 05/06, et quatre nouveaux guides. Bruts 1024² archivés en **WebP lossless**, avec égalité RGBA vérifiée face aux PNG générés ; leurs hashes originaux, hashes d’archive et hashes des pixels figurent dans `bruts/provenance.json`. Réduction uniforme en nearest-neighbour à 512² et palette de la plage de référence. Cela reste une **génération référencée PMD, pas une extraction de tuiles natives pixel-identiques**. Références PMD : Nintendo / Creatures / GAME FREAK / Chunsoft.

Chaque carte/mode comprend sable, trois plans rocheux, végétation, eau, écume et un calque par accès : **80 PNG de calques** pour les quatre cartes en jour/nuit. Dimensions natives **512×512**, origine (0,0), alpha binaire, basenames uniques, grille 8 px. Les compositions fusionnées sont aussi conservées en WebP lossless dans le dépôt. L’exporteur produit leurs équivalents PNG sans perte.

Les calques représentent des **surfaces visibles**, pas des volumes complets déplaçables. Certains troncs/ombres peuvent rester dans les partitions minérales ; les dessous cachés ne sont pas reconstruits.

## Raccords

Même standard que V1 : accès centrés de **96 px**, coordonnées de bord `[208,304)`, profondeur 48 px, noyau de 16 px identique dans toutes les orientations et transition vers le matériau local. Prélèvement de sable source `(296,168)–(392,216)`.

Les vingt-sept accès déclarés rejoignent leur centre avec une distance d’au moins 8 px aux obstacles du masque de sable. Toutes les bandes de raccord 96×16, dont **05S–07N**, sont comparées pixel par pixel en jour et en nuit.

Ce contrôle **ne certifie pas la continuité complète des falaises** : il peut rester des ajustements de contours rocheux entre deux modules. Ce ne sont ni des collisions ni des warps PMDO. Les limites hors ports doivent être bloquées explicitement en moteur ; des anfractuosités de bord peuvent contenir du sable sans constituer un accès déclaré.

## Animations et ciel conservé

- Eau et écume : deux pistes indépendantes de **32 phases × 100 ms = 3,2 s**, pour chaque nouvelle carte et chaque mode.
- **512 frames** au total dans 16 atlas WebP lossless. Toutes les pistes comportent plusieurs images différentes, pas des copies.
- Liseré périodique jusqu’à 3 px autour du rivage et aux contacts rocheux, reprenant les couleurs de l’écume existante. Le feuillage est exclu ; les rochers restent immobiles. La phase zéro recompose la carte statique exactement.
- Nuit : filtre Abyss exact appliqué au terrain et aux animations, sans mélange de filtres.
- Le **ciel sans lune et les petits nuages de V1 sont conservés**, pas régénérés à nouveau. Ils apparaissent dans la vue du réseau et la plage de référence ; pas entre les cartes. Nuages en wrap de 64 s ; 20 cycles d’eau correspondent à un cycle de nuages. Ne pas leur appliquer Abyss deux fois.

Les quatre nouveaux modules n’embarquent pas de ciel dans leurs PNG de terrain.

## Viewer et export PNG

Le viewer du dépôt présente les quatre nouvelles cartes, le réseau de dix, la plage de référence, le jour/nuit, les calques et la navigation entre ports. **Accès / connexions** ajoute un schéma de travail ; désactiver ce bouton avant d’exporter une vue sans annotations. Les cases vides restent sans destination. Les sorties réservées ne téléportent vers aucune carte fictive.

Le **ZIP autonome ne contient que les quatre nouveaux modules** et un viewer limité à ceux-ci. Le lien vers 05 est alors signalé comme une connexion externe au lot V1. Ses dépendances visuelles sont locales ; aucun V1 n’est nécessaire pour regarder et animer 07–10. Il exclut les bruts, les anciennes cartes et les copies fusionnées redondantes. Le viewer peut exporter une carte ou un calque en PNG ; l’exporteur Python inclus décode toutes les compositions et toutes les frames.

Dans le ZIP extrait, avec Python et Pillow :

```sh
python -m pip install Pillow
python export_png.py           # 8 compositions PNG, jour et nuit
python export_png.py --frames  # mêmes compositions + 512 frames PNG
```

Tous ces PNG sont en 512×512, sans étirement. Pour l’import PNG to Tileset, remplacer les calques fixes eau/écume par leurs frames synchronisées. Garder les noms uniques. **Aucun Ground natif, collision, warp ou runtime PMDO validé n’est fourni.**

Au besoin, servir le dossier extrait avec `python -m http.server 8000`, puis ouvrir `http://localhost:8000/` sur la même machine.

## Reconstruction et stockage

Sources : `source/beach_extension_v2/`. Depuis la racine du dépôt :

```sh
.venv/bin/python source/beach_extension_v2/build.py
.venv/bin/python source/beach_extension_v2/verify.py
.venv/bin/python source/beach_extension_v2/package.py
node source/beach_extension_v2/test_viewer.cjs
.venv/bin/python source/beach_extension_v2/package.py
```

Pour respecter le budget de livraison sans changer les pixels approuvés, les copies V1 de frames PNG, documents ORA et compositions fusionnées sont désormais ignorées par Git : **leurs octets restent intégralement dans le ZIP V1 préservé**. `source/beach_network_v1/restore_exports.py` les restaure au besoin ; build V2, verify V1 et package V1 l’appellent avant utilisation. Le viewer utilise les calques et atlas toujours conservés. Rien n’est perdu dans cette déduplication.

Les vérifications pixels/codec/topologie, la simulation DOM et le contrôle des archives ne remplacent pas l’approbation artistique, un navigateur graphique ou une validation en jeu. Voir `verification.json`, `verification_viewer.json`, `verification_package.json`.
