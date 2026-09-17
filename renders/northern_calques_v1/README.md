# Northern Range — arène centrale, jour/nuit, 9 calques

Galerie autonome : **`apercu_northern_calques_v1.html`**, à la racine. Elle ouvre Northern Range et propose aussi les corrections Spring / Crooked Cavern.

## Voir et télécharger
- [Composition jour](jour/composition.png)
- [Composition nuit](nuit/composition.png)
- [Calques jour](jour/) / [calques nuit](nuit/)
- [Terrain transparent recomposable](terrain_detoure.png)

Référence : **fichier fourni par l’utilisateur au commit `00cb874`**, `Game Boy Advance - Pokemon Mystery Dungeon_ Red Rescue Team - Dungeon Boss Rooms - Northern Range.png` (456×432). La page d’origine est [The Spriters Resource, asset 75116](https://www.spriters-resource.com/game_boy_advance/pokemonmysterydungeonredrescueteam/asset/75116/). Le PNG fourni dans Git a été réellement inspecté et utilisé par le générateur. Aucun autre sommet n’a été substitué à cette référence.

## Pile de calques 456×432
1. **01_ciel** : ciel seul, dégradé jour ou nuit.
2. **02_etoiles** : étoiles seules, transparent en mode jour.
3. **03_lune_halo** : lune et halo, transparent en mode jour.
4. **04_profondeur** : fond sombre sous les falaises.
5. **05_rochers_arriere** : pics arrière redisposés.
6. **06_arene_centrale** : sol de combat dégagé.
7. **07_socle_arene** : paroi sous l’arène.
8. **08_falaises_avant** : contreforts latéraux du premier plan.
9. **09_brume_overlay** : brume légère indépendante.

Les neuf PNG se composent dans cet ordre, sans déplacement. Le centre du canvas **(228,216)** appartient bien à l’arène. La lune et les étoiles ne sont pas peintes dans le ciel. La brume n’est pas fusionnée dans les rochers.

Les strates de terrain sont des partitions à profondeur du dessin généré. Leur recomposition est identique au terrain détouré ; **les surfaces invisibles derrière d’autres rochers ne sont pas reconstruites**. Elles sont adaptées au masquage/compositing, pas à déplacer indépendamment n’importe quel pic sans retouche.

## Matériau et variantes
Nouvelle génération guidée par la référence, avec pics asymétriques et arena gardée au centre ; **pas une reconstruction native pixel-identique**. Le brut reste dans `bruts/terrain_northern.png`. Détourage magenta incluant les franges sombres, puis mise au format nearest 456×432. La brume vient de `bruts/brume.png`, détourée et affichée à faible opacité. Le mode nuit applique le filtre Abyss existant aux quatre calques de terrain.

Les deux compositions sont **statiques** : aucun mouvement ou effet non demandé n’a été ajouté à Northern Range. L’overlay est un PNG transparent, sa position peut être réglée ultérieurement.

## Corrections également livrées
- `renders/crooked_statique_v2/` : trois layouts **sans animation ni particules**. Les anciennes sorties animées ne sont conservées que comme historique, elles ne sont plus la version proposée.
- `renders/spring_pulsation_v2/` : colonne nettoyée, **couleurs fixes et pulsation d’opacité**, sans déplacement du spectre. Bassin turquoise et escalier conservés.

## Contrôles
`verification.json` : recomposition exacte jour/nuit, recomposition exacte des quatre strates de terrain, centre de l’arène vérifié. Vérifications complémentaires des trois Crooked statiques et des 78 phases de pulsation. Galerie testée avec DOM simulé, pas un GPU.

Reproduction : `source/corrections_northern_v1/{build,gallery,verify}.py` (Pillow, numpy). Aucun `.rsground`, collision ou mod natif modifié ; pas de validation PMDO. Les attributions et droits des ressources PMD d’origine restent applicables. Les nouveaux dessins ne sont pas attribués aux auteurs des assets canoniques.
