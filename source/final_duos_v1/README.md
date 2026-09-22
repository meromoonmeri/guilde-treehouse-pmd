# D22 — Onze duos, jour et nuit

Livraison graphique PMDO :22cartes de jour et22variantes de nuit réparties en11packs. Chaque pack comprend entrée/finale jour+nuit, PNG de tous les plans/frames, ressources `.tile`8px, `.dir`, quatre `.rsground`, scripts Ground minimaux, aperçus et installateur.

Les16cartes déjà publiées sont reprises sans écraser les versions précédentes. Trois duos sont assemblés à partir des plans générés sauvegardés : Mont Discipline, forêt secrète, plaines brûlées. Discipline est une **nouvelle proposition MD2**, pas une récupération prétendue des fichiers MD1 non publiés. Les nouvelles cartes ont cinq vrais groupes : base continue et surfaces/architecture/objets/végétation ou effets indépendants. Fond+sol des brûlées se chevauchent ; sol complet derrière les arbres de la forêt secrète. Les dix anciennes cartes DB1 gardent leurs partitions historiques de surfaces visibles : pas de faux sol caché annoncé rétroactivement.

## Nuit selon le biome

Les originaux jour restent intacts. Seules les copies nocturnes reçoivent le traitement Abyss. La lumière est sur une **décoration animée séparée**, jamais cuite dans les plans de terrain :
- Volcan : lave native animée gardée lumineuse, roches assombries, halo chaud autour des surfaces de lave visibles.
- Plaines brûlées : quatre poses natives de flammes Halcyon/Ledian, à1×,6ticks, réemploi explicite ; foyers et halo chaud séparés. Pas une extraction prétendue de la BPA H06P05.
- Forêts, jungle et cour : masques des32phases de rayons PMD réemployés comme éclairage lunaire. Nouvelle interprétation lumineuse, pas nouvelle météo canonique attribuée au lieu.
- Courant marin :32phases natives utilisées pour moduler la lumière sous-marine.
- Désert : modulation de la poussière avec les32phases sources ; le long défilement horizontal natif n'est pas intégralement porté ici.
- Eau et collines conservent les pistes existantes ; seuls les ciels diurnes remplacés en nuit perdent leur ancien cycle.

Pleine lune64×64 et étoiles extraites de la référence PMD Sky déjà auditée par VP1, conservées à1×. Elles apparaissent seulement derrière les zones de ciel des biomes ouverts ; pas de lune affichée sous terre ou sous l'eau. Nuages en overlay à−8px/s, wrap horizontal512px/64s ; silhouette générée déjà livrée, pas animation native prétendue.12poses de scintillement des étoiles, rythme8ticks, ajout artistique explicite.

Le halo restaure partiellement les couleurs du décor sous-jacent : **éclairage graphique compilé pour ce terrain**, pas shader temps réel et pas garantie d'éclairage des personnages ajoutés. Après modification du sol, recalculer le halo. Les pixels émissifs des banques lave/flammes ne sont pas assombris ; le halo les laisse libres. Les sources natives jour sont préservées.

## PMDO : cadrage et portée

Dimensions inchangées, caméra suivie et Clamp, viewport logique320×240 à GameZoom x1. Pas d'agrandissement artificiel des cartes ou des natifs. WindowZoom est indépendant. Les aperçus sont des rendus simulés, pas des captures du moteur.

**Bases Ground d'édition**, `Released=false`, collisions libres, aucun Pokémon, aucune rencontre, aucun warp ni scénario de gameplay livré. Peindre collisions/accès et tester avant de jouer. L'arène de boss glaciale IB2 est un chantier séparé et n'est pas déclarée terminée par ce pack de22zones.

Fermer PMDO, sauvegarder le mod et extraire le ZIP dans un dossier temporaire :
```
python INSTALLER.py /chemin/PMDO/MODS/mon_mod --dry-run
python INSTALLER.py /chemin/PMDO/MODS/mon_mod
```
L'installateur fusionne l'index des tilesets et refuse d'écraser une carte ou ressource modifiée. Ouvrir les cartes `dn1_*` dans l'éditeur Ground. Schéma compatible avec les bases0.7.15.1 déjà livrées ; réenregistrer via l'éditeur si votre version de PMDO exige une conversion. Moteur non exécuté pendant cette livraison.

## Contrôles et lecture

Les ressources de chaque carte sont relues depuis les formats sérialisés à plusieurs ticks et comparées au rendu source (alpha exacte, écartRGB maximal1 en jour et2 en nuit, lié aux arrondis cumulés de prémultiplication). Les aperçus de viewport font320×240. Les WebP nocturnes sont des **extraits de4,8s à lecture unique**, pas des boucles combinées complètes des horloges natives indépendantes. Les fichiers de phases restent sans perte.

Le serveur affiche les états disponibles et les téléchargements ; il ne transforme pas une carte encore en attente en carte terminée. Les anciens exports, les références et Beach ne sont pas supprimés. Les gros livrables peuvent être conservés dans un commit Git épinglé et restitués avec contrôle SHA, plutôt que dupliqués dans le checkout. Garder l'historique Git complet.
