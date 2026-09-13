# Café Halcyon × Spinda — cinq niveaux, deux plans, fenêtres rondes

## Ouvrir
Galerie autonome : **`apercu_cafe_multietage_v1.html`** à la racine. Elle ouvre l’étage +2 pour montrer les petits hublots. Choix du plan A/B, du niveau et du paysage extérieur jour/nuit ; six calques masquables et exportables ; bouton de schéma de circulation.

- [Planche A](PLANCHE_A.png)
- [Planche B](PLANCHE_B.png)
- [Accueil A](A/accueil/composition_jour.png)
- [Étage +2 A : petits hublots](A/etage2/composition_jour.png)

## Programme
Deux variantes A/B pour chaque niveau, soit **10 layouts** :

| Niveau | Matériau principal | Fenêtres |
|---|---|---|
| Sous-sol −2 | Bordure rocheuse Spinda + panneaux bois + plancher café | Aucune ouverture extérieure |
| Sous-sol −1 | Bordure rocheuse Spinda, pièce plus profonde | Aucune ouverture extérieure |
| Accueil | Base vide Metano Café, salle élargie | 2 fenêtres circulaires, diamètre48px |
| Étage +1 | Base Metano, salle plus profonde | 3 fenêtres circulaires, diamètre48px |
| Étage +2 | Base Metano, salle large | **2 petits hublots32px espacés, aucune baie vitrée** |

Les plans B sont plus spacieux que les plans A. Les ouvertures sont réellement circulaires, avec alpha nul à leurs coins : pas une image rectangulaire posée sur le mur. Les cadres en bois sont réassemblés à partir des textures natives ; ce sont de nouveaux cadres, pas un sprite de fenêtre canonique prétendument retrouvé.

## Pièces vides
**Aucune table, chaise, comptoir, caisse, baril, plante, tapis ou personnage** dans les exports finaux. Les escaliers restent des éléments structurels séparés. Les ornements fixes des murs canoniques (rideaux/rubans et accroches murales) sont conservés ; « vide » désigne ici les surfaces destinées au mobilier, pas des murs entièrement nus.

Les grandes ombres/découpes de mobilier de la feuille Spinda ont été remplacées par du plancher natif. Les retours rocheux, boiseries et escaliers viennent des feuilles sources. Les schémas indiquent les liaisons prévues : SS−2 ↔ SS−1 ↔ accueil ↔ étage+1 ↔ étage+2. Ces liaisons sont **documentaires**, pas des transitions PMDO implémentées.

## Calques alignés
Chaque dossier `A/ss2`, `A/ss1`, `A/accueil`, `A/etage1`, `A/etage2` (idem B) contient :
1. `01_sol_vide.png`
2. `02_vues_exterieures_jour.png` ou `02_vues_exterieures_nuit.png`
3. `03_bois_murs.png`
4. `04_bordure_rocheuse.png`
5. `05_cadres_fenetres.png`
6. `06_escaliers.png`

Puis `composition_jour.png`, `composition_nuit.png`, et `schema.png`. Dimensions, cercles de fenêtres, extensions de salle et coordonnées des accès sont dans `manifest.json`. Tous les canvases ont des dimensions multiples de8, sans étirement des textures.

**Jour/nuit concerne le paysage derrière les fenêtres uniquement.** Le café garde son éclairage intérieur chaud. Ce n’est pas un étalonnage nocturne de toute la pièce ni une animation. Les vues sont des petits extraits du paysage canonique fourni précédemment dans `232233.png`, avec filtre Abyss pour la vue nocturne.

## Sources canoniques inspectées
- [Palikadude/Halcyon](https://github.com/Palikadude/Halcyon), commit **da6c2130d641507447e6386a5e47a296e8cb4c71** : `Data/Ground/metano_cafe.rsground`, cinq feuilles `Metano_Town_Cafe_*` référencées. Carte **456×320**, grille57×40 de8px.
- [Minemaker0430/ExplorersOfSkyOrigins](https://github.com/Minemaker0430/ExplorersOfSkyOrigins), commit **4e7422acc263886198113a8256677766e4244228** : `Data/Ground/spinda_cafe.rsground`, `SpindaCafe1.tile`, `SpindaCafe2.tile`. Carte **696×456**, grille87×57 de8px.

Les cartes ont été reconstruites depuis leurs vraies tuiles, avec conversion de l’alpha prémultiplié, puis inspectées. Sources, feuilles décodées, reconstructions et empreintes SHA-256 se trouvent dans `source/cafe_multietage_v1/references/`.

### Méthode
Deux propositions guidées par les références ont servi d’étude (`propositions/`), puis les rendus finaux ont été **réassemblés avec les pixels canoniques**, sans matière de bois/roche générée à leur place. L’agrandissement insère des bandes de8px du matériau source : il ne redimensionne pas les dessins. Cela peut produire des répétitions visibles dans les grandes longueurs de bordure rocheuse ; ces raccords sont à valider artistiquement.

Les vues, cadres circulaires et plans sont des assemblages nouveaux. Les premiers guides générés montraient des ouvertures rectangulaires : ils sont historiques et **ne remplacent pas les fenêtres rondes des exports finaux**.

## Vérifications et limites
`verification.json` : empreintes des **7 banques tile et2 cartes**, cinq patches comparés pixel par pixel aux extraits canoniques, **20 recompositions exactes**, grille8px, masques des fenêtres circulaires vérifiés, étage+2 limité à deux hublots32px, sous-sols sans fenêtres, liaisons de schéma réciproques. Galerie testée en DOM simulé.

Aucune nouvelle carte `.rsground`, collision, navigation, transition ni validation GPU/PMDO. Les PNG sont éditables en calques ; les escaliers indiquent un projet de circulation à intégrer ensuite. Les matériaux canoniques ne signifient pas que ces nouveaux plans sont des cartes natives originales des auteurs.

Scripts : `source/cafe_multietage_v1/inspect_sources.py`, `build.py`, `gallery.py`, `verify.py`, `test_viewer.cjs` (Pillow et numpy).

Attribution : Palikadude/Halcyon et Minemaker0430/EoSO pour leurs cartes et ressources distribuées ; ayants droit et contributeurs Pokémon Mystery Dungeon pour les ressources concernées. Disponibilité publique ne vaut pas licence générale de réutilisation.
