# Suite : finale de la forêt + mobilier à l’échelle

## LF1 — autre clairière de la même forêt H07P03

480×336, six groupes : fond forestier, sol continu, rochers, arbres/racines, végétation basse, lumière native. Entrée LE1 approuvée et inchangée. Fond, sol et végétation réemployés **à l’identique** ; quatre groupes de rochers déplacés entiers, sans nouvelle mise à échelle ; bordure arbres/racines nouvellement générée. Arène centrale élargie, limite de racines au nord et retour au sud. Ce ne sont pas cinq nouvelles générations de plans.

Les bordures ancrées au cadre ne sont pas des arbres mobiles reconstitués hors champ. Sol opaque sous les décors proches. Aucun Pokémon, collision, warp ou script de combat livré. `assemble.py --tick 64 --out assembled` après extraction du ZIP recompose les PNG (Pillow/NumPy).

H07P04W est un **réemploi explicite**, pas la météo originale H07P03 : 32 rayons à8ticks et14 particules à7ticks, fichiers natifs identiques au pack LE1. Fusion additive RGB55516/16, pas alpha50%. WebP : extrait4,267s à lecture unique, pas boucle complète12544ticks (~209s). Les six cascades natives de lave restent dans le pack LE1 ; aucune n’est placée en forêt. PNG d’import sans perte, WebP de présentation compressé.

## FC1 — quatre propositions de mobilier

| Objet | Canevas d’import | Empreinte native de référence |
|---|---|---|
| Table vide Halcyon |48×48|46×44|
| Table souche / auberge |48×48|48×44|
| Coffre |24×24|21×23|
| Plante en pot |40×48|40×44|

Gabarits indiqués **avant génération**, détail visé à la taille logique. L’outil ne garantit pas une sortie brute24/48px : normalisation nearest, proportions préservées, centrage et détourage des **créations uniquement**. Les silhouettes finales peuvent être un peu plus étroites que les références : dimensions exactes dans le manifeste et sur la planche. Aucun redimensionnement à faire pour utiliser les PNG d’import. Tous les canevas sont divisibles par8 (Ground, pas une règle DTEF).

8PNG séparés jour/nuit, 2tilesheets avec index, 4références natives originales1×. Nuit conforme au traitement V8, uniquement sur les créations. La planche compare natif et création à1× ; zoom4× de lecture. Le café de démonstration est une copie à1× avec placement temporaire ; les salles livrées et leurs accès restent inchangés, meubles non cuits dedans.

10bruts conservés losslessly : premières tentatives et corrections. Les demandes de marge au générateur n’ont pas toutes été suivies ; les contacts aux bords des bruts sont consignés (`raw_edges_touched`), sans prétendre avoir reconstitué du hors-champ. Vérifier les contours et le style dans les aperçus avant adoption. Nouvelle table vue principalement du dessus, et non l’ancienne tentative V8 vue du dessous. Quatre propositions à revoir artistiquement, pas une approbation utilisateur : 9anciennes+4nouvelles=13/36, 23objets et les fenêtres restent à poursuivre. Historique V8 non réécrit.

## Reproduction et conservation

Depuis la racine : `.venv/bin/python source/suite_foret_cafe_v1/build.py`, puis `verify.py`. Résultats dans `.cache/suite_foret_cafe_v1/build/`. `storage.py` restitue les livraisons publiées avec contrôle SHA256 ; index `release.json`, dix bruts dans `raws/archive.json`. Tous les octets restent dans l’historique Git complet. Les gros fichiers ne sont pas perdus : liens directs immuables dans les index/README principal, cache volontairement ignoré. `serve.py --port 8013` expose PNG/WebP/ZIP directs, pas de dépendance HTML. Tests techniques ≠ validation PMDO ou artistique.
