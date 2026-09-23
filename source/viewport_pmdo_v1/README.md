# VP1 — adaptations Ground PMDO à taille inchangée

## Choix de cadrage : ni étirement ni zoom global imposé

La référence **Crooked Cavern Entrance / Halcyon**, au commit da6c2130d641507447e6386a5e47a296e8cb4c71, contient40×30cases, `TexSize=1` : **320×240pixels**, `EdgeView=Clamp`, `ViewCenter=null`, offset(0,0). Le moteur étudié utilise une fenêtre logique320×240 et une vue de carte `ScreenSize / GameZoom`. Ainsi x1 montre320×240, x2Near160×120, x2Far640×480. **WindowZoom** agrandit l’affichage, ce n’est pas le zoom de carte. Une capture de toute la carte ne prouve pas la vue utilisée par le joueur.

Les cartes livrées mesurent déjà456/480pixels de large sur312/336de haut : elles dépassent une vue normale. Il n’est donc pas nécessaire de les grossir, ni d’inventer des marges vides. On garde leurs dimensions, leurs pixels et leurs calques, avec une caméra suivie, Clamp, des points d’entrée et un décalage de caméra propres aux décors. Zoom de carte conseillé : **x1**. Aucun script ne remplace de force le réglage global du joueur. Les aperçus320×240 sont des simulations de ce cadrage, **pas des captures du jeu exécuté**. Les marqueurs ne représentent pas des Pokémon cuits dans l’image.

## Contenu

Fichiers natifs `.rsground`, `.tile`8px, `.dir` pour les fonds, scripts minimaux, PNG des plans, carte entière et aperçu de viewport. Noms `vp1_*` / `VP1_*`, séparés de toutes les livraisons antérieures. Les16cartes effectivement publiées sont traitées par duo : forêt lumineuse, île, volcan, désert, courant marin, lisière/forêt envahie, jungle, plaines. Les plaines ont en plus quatre variantes : entrée/finale à nuages mobiles, entrée/finale nocturnes. Le duo original des plaines reste disponible sans remplacement.

**Bases d’édition, pas niveaux de gameplay finalisés** : `Released=false`, collisions libres, aucune transition, rencontre ou acteur. Le marqueur d’entrée est indicatif et à vérifier dans l’éditeur. Dessiner collisions/accès avant de jouer. Les dix cartes historiques DB1 gardent leurs calques de surfaces visibles ; leurs zones cachées ne sont pas soudainement reconstruites. Les six cartes suivantes conservent leurs sols continus et plans sémantiques.

## Animations : portée exacte

- Île, lave/cendres, jungle, ciel/lointain des plaines : pistes simples conservées avec leurs cadences.
- Courant marin :32phases,8ticks. Lumière compilée en RGB555 sur son terrain, dans une couche dédiée.
- **Forêts et désert : effets additifs maintenus en pose64 dans ces Ground d’édition.** Les cycles autonomes/longs restent dans les packs originaux. Ils ne sont pas présentés comme portés complètement au moteur ici.
- Les couches RGB555 compilées dépendent du décor situé dessous : les désactiver pendant la peinture puis les recalculer. Ce n’est pas un shader additif général ni une lumière qui éclairera automatiquement de nouveaux personnages. Les copies de plans générés des scènes additives sont converties dans l’espace d’affichage RGB555 pour reproduire la composition publiée ; géométrie inchangée, originaux conservés.

Cette limite évite des millions d’entrées d’animation par carte et une surcharge du mod. Aucune fausse boucle courte n’est présentée comme le cycle indépendant complet de la forêt ou du désert.

## Variantes des plaines : nuages et nuit

Fond `LayeredBG` natif PMDO, dans l’ordre : ciel, étoiles, lune, nuages ; collines et terrain viennent devant. Les nuages sont les petites silhouettes **générées** du pack BeachNetwork, recopiées sans modifier Beach : mouvement horizontal−8px/s, `RepeatX=true`, pas de wrap vertical, période512px/64s. Le mouvement est une adaptation, pas une ondulation native retrouvée. Les nuages peuvent passer devant la lune et les étoiles.

La **pleine lune** vient de `bgnightbackgroundpmdskyda.png`, référence PMD Sky du dépôt : disque64×64 extrait du rectangle[120,20,184,84], pixels visibles à1× sans miroir, resize, recoloration ni dessin de cratères. Elle est placée en[196,12]. Le ciel nocturne est reconstruit avec des couleurs du halo natif échantillonnées dans les18premières lignes dégagées ; ce fond reconstitué n’est pas prétendu identique à l’image source entière.

Étoiles extraites de la même référence ;12poses de visibilité échelonnée à8ticks, sans changer leurs RGB visibles. **Scintillement ajouté**, pas cycle canonique attesté. Dans ces variantes, les collines sont en pose0 : les cycles originaux restent sur les cartes originales. Les copies nocturnes des collines/terrains utilisent le traitement Abyss du dépôt ; les originaux natifs/jour ne sont jamais écrasés. L’extrait WebP nocturne4,8s est à lecture unique : ce n’est pas la boucle entière64s.

## Installation sûre

Fermer PMDO, sauvegarder le mod, extraire ce ZIP dans un dossier temporaire puis :

```
python INSTALLER.py /chemin/PMDO/MODS/mon_mod --dry-run
python INSTALLER.py /chemin/PMDO/MODS/mon_mod
```

La cible contient `Mod.xml`. L’installateur standard-library fusionne l’index des tilesets, sauvegarde l’ancien index et refuse d’écraser une carte/ressource modifiée. Ne pas copier un index partiel sur celui du mod. Les scripts sont copiés vers le namespace Lua du mod si nécessaire. Réouvrir PMDO avec ce mod actif, éditeur **Ground**, ouvrir les `vp1_*`. Les `.rsground` ne sont pas des PNG à importer par « PNG to Tileset ». Les PNG séparés restent proposés pour les retouches.

Vérifications attendues : tous les frames/références se résolvent dans les `.tile`, aller-retour des codecs, rendu source comparé au rendu sérialisé, cadrage, installeur à blanc/réinstallation/refus d’écrasement. **Aucune exécution PMDO/GPU revendiquée.** Schéma historique0.7.15.1, lecteur/codecs RogueEssence épinglés8b7eafafa73ff0c10b9e8fd9348559ee1b5dfe8b. Si la version du moteur a modifié le schéma, ouvrir/réenregistrer via son éditeur plutôt que déclarer le pack universellement testé.

## État des autres cartes

Mont Discipline : fichiers montrés précédemment mais non retrouvés sur la branche publiée après l’échec d’authentification ; non inclus, pas recréés silencieusement. Forêt secrète : dix bruts sauvegardés au commit90fa7e28, pas de duo fini revendiqué. Plaines brûlées : encore à produire. Ces trois duos ne sont pas comptés parmi les16maps converties.

Les versions originales restent intactes. Sources complètes, références, preuves et gros packs sont conservés dans des commits d’archive poussés, puis restituables par le lanceur SHA : conserver l’historique Git complet. Le budget de fichiers du checkout ne doit pas forcer la destruction d’anciens exports.
