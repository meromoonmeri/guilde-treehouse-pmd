# Waterfall Lake V3 — reprise locale des falaises et cascades ajoutées

L’utilisateur apprécie le reste de V2, mais trouve les falaises posées sans intégration et demande de générer les deux cascades selon leur géométrie rocheuse. Cette reprise ne remplace donc **que six calques** : deux ailes rocheuses, deux chutes latérales et leurs deux écumes.

## Méthode corrigée
1. Génération **commune de la roche et de l’eau** sur magenta, à partir de V2 et du PNG GBA original. Les nouvelles chutes sont dessinées dans les canaux du relief, pas placées ensuite dans des rectangles arbitraires.
2. Reprise des canaux trop étroits pour élargir l’eau avec ses lèvres rocheuses.
3. Reprise de texture : le premier dessin avait trop de strates fines. Le brut final `massif_texture_gba_magenta.png` utilise des faces plus larges, des fractures irrégulières et moins de lignes parallèles, pour se rapprocher du vocabulaire GBA.
4. Détourage, ajustement à la zone haute, puis séparation exacte entre pixels aquatiques et rocheux. Les nouveaux reliefs forment des faces continues autour des chenaux, au lieu d’une succession de socles plats indépendants.
5. Palette des falaises ramenée aux couleurs de la roche d’origine. Matière des nouvelles chutes dérivée de leurs pixels générés, puis ramenée à la gamme de la cascade GBA. Les écumes GBA existantes sont repositionnées à leurs pieds réels et raccordées localement.

Les trois bruts sont archivés. **Seul le troisième est utilisé pour le rendu final** ; ce sont des adaptations générées, pas des sprites natifs intacts. L’appartenance à la palette ne prouve pas, à elle seule, l’identité du style ou des motifs.

## Géométrie / animation
La silhouette de chaque chute provient directement du dessin commun roche/eau. Elle reste fixe dans toutes les poses. Les rangées sont enregistrées le long du chenal courbe ; une bande de matière issue de la chute générée descend de 2 px par pose, avec une période de 48 rangées. L’animation est reconstruite, pas récupérée dans un jeu ni issue d’une simulation physique.

Les impacts sont placés aux pieds déduits du dessin, **(172,107)** et **(339,107)**, et non aux anciens pieds (177,108)/(327,108). Un raccord local assure le chevauchement chute/écume. Les pixels blancs isolés qui ne rejoignent pas ce contact sont écartés. L’eau ne recouvre aucun pixel de la nouvelle roche.

La bande centrale x=208–295 est protégée des nouveaux dessins : la cascade centrale reste inchangée. Le raccord au massif existant est local, sans régénérer le lac.

## Ce qui est conservé
Les **22 autres calques de V2** sont identiques pixel pour pixel :
- fond du lac et animation subtile de ses cercles ;
- cascade et écume centrales ;
- plateformes, pas japonais et leurs reflets assortis ;
- terrain et végétation de base ;
- mêmes positions, cadrage, cadence et ambiance jour/nuit.

Le masque `MASQUE_REPRISE_LOCALE.png` réunit les anciennes et nouvelles zones d’ajout. Pour chacune des 48 compositions jour/nuit, **tous les pixels hors de ce masque sont identiques à V2**. Les modifications du massif peuvent occulter des pixels de fond, mais aucun autre décor n’est repeint.

## Livraison
504 × 360, **28 calques par ambiance**, 24 poses, boucle de 4 secondes.

- `../../apercu_waterfall_lake_raccords_v3.html` : galerie jour/nuit avec sélection des calques et option **Avant · ajouts V2**.
- `jour/COMPOSITION.png`, `nuit/COMPOSITION.png` et `ANIMATION.webp` dans chaque dossier.
- `jour/lake3_jour.ora`, `nuit/lake3_nuit.ora` : calques à l’état initial.
- `jour/lake3_jour_*.png`, `nuit/lake3_nuit_*.png` : calques alignés et 24 compositions par ambiance.
- `AVANT_APRES.png` : comparaison de la reprise locale.
- `sprites/` : ailes rocheuses détourées et matières des deux chutes générées.
- `MASQUE_*.png` : périmètre de reprise, roche et deux silhouettes aquatiques.
- `verification.json` : contrôles d’assemblage et de préservation.
- `waterfall_lake_raccords_v3.zip` : paquet avec scripts et références nécessaires.

## Contrôles et limites
Vérifications : 48 scènes opaques ; 28 calques ; 22 calques approuvés inchangés ; aucune modification hors reprise ; séparation des masques roche/eau ; canaux continus et fixes ; toutes les composantes d’écume attachées ; recomposition ORA exacte ; filtre nuit exact. La nuit utilise toujours le filtre Abyss des livraisons précédentes.

Ces tests ne certifient pas une perfection artistique absolue ni un résultat dans PMDO. Aucun test d’import, de collisions, de mouvement ou de combat dans le moteur. Les références et anciennes livraisons restent intactes ; les ressources PMD gardent les droits de leurs ayants droit.

Reconstruction depuis la racine avec Pillow, NumPy et SciPy :
```sh
.venv/bin/python source/waterfall_lake_raccords_v3/build.py
.venv/bin/python source/waterfall_lake_raccords_v3/verify.py
.venv/bin/python source/waterfall_lake_raccords_v3/package.py
```
