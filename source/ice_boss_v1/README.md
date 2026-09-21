# IB1 — Creuset glacial, adaptation de Searing Crucible

## Référence réellement examinée

Halcyon/Palikadude, branche **working-copy**, commit **1522c7a8b7a34d70078e11ed605b21d563b0dc51**, schéma0.8.9.0. Il s’agit de `searing_crucible`, le combat de Searing Tunnel avec **Volcaropod et huit Limagma**, et non du terrain d’entrée du tunnel. Source `.rsmap`, Ground, scripts d’événement, effet `flowing_lava` et tileset `Spring_Cave_Pit` vérifiés par SHA de blob Git. Les originaux ne sont jamais écrasés.

La carte est de **21×21cases de24px =504×504px**. Les **72cases praticables**, les369cases infranchissables, les points d’entrée et les positions du roster optionnel sont conservés. Les collisions ne sont pas déduites à vue du nouveau dessin.

## Une nouvelle matière, pas un agrandissement

Sol glacé continu, rochers givrés, sources froides et pics sont des **adaptations**, pas des tuiles glaciaires canoniques prétendument retrouvées. Quatre images ont été générées : sol, composition de rochers, pic et réservoir. Les couleurs des rochers mélangent la matière générée et une rampe bleue suivant le relief de la source ; leur alpha suit strictement l’empreinte visible des rochers d’origine. Cela garde la géométrie exacte malgré les variations du générateur. La référence native reste fournie intacte.

Quatre groupes sémantiques : sol opaque sous tous les décors ; rochers ; réservoirs fixes/actifs ; pics. Modules et poses séparés en PNG, aucune silhouette de Pokémon cuite dans les images. Deux poses permanentes de réservoir et les sources latérales reprennent les ancrages de la lave. Le pic24×32 est ancré à sa case24×24 avec8px de dépassement supérieur.

## Fonctionnement du boss : ce qui est repris

Le Lua original a été exécuté dans un banc de test avec adaptateurs d’API pour enregistrer chaque écriture d’effet et son instant. Tracés exacts :

- `TopStraight` / `BottomStraight` : **14cases**, vagues à40et80frames ; préparation totale120frames.
- `DiagonalDown` / `DiagonalUp` : **20cases**, vagues à40,80,120frames ; préparation totale160frames.
- Deux tirages binaires du RNG de carte choisissent les extrémités gauche/droite, comme la source.
- Compteur global : réglage source **2tours actifs /1tour de pause**, garde `context.User == nil`, attente20frames avant changement, préparation des réservoirs40frames et propagation par vagues40frames.
- Les effets ne changent pas le terrain en mur : marcher dans les pics reste possible, mais dangereux.

Les pics ont quatre poses de levée et quatre de retrait par dévoilement vertical, sans étirement du sprite. Une transition occupe16frames, suivies de24frames d’attente pour conserver le rythme source40frames. Le retrait ne supprime que les effets IB1 ; les couches de décoration nommées évitent le fragile retrait arbitraire `RemoveAt(2)` de la source. La couche des réservoirs fixes et les décorations étrangères restent intactes.

### Changements de combat explicites

Dégâts froids de **1/16PV max modulés par les types**, à l’apparition/sous le pied et en fin de tour. Types Glace et `ice_body` immunisés ; `thick_fat` réduit. Pas de brûlure, pas de gel immobilisant répété, pas de bonus de puissance Feu. Ce n’est donc **pas un équilibrage identique** au combat de lave. Le roster de démonstration reste volontairement celui de Halcyon, sans être retypé ni rééquilibré automatiquement.

## Cadrage PMDO

Crooked Cavern Entrance a été lu dans la même branche : Ground40×30, `TexSize=1`, soit320×240px, Clamp, pas de ViewCenter imposé. Cette référence ne prouve pas à elle seule un zoom de jeu particulier. Avec le viewport logique320×240 à **GameZoom x1**, notre carte504×504 laisse voir environ30%de sa surface. Au point d’entrée du boss, le rectangle simulé est[116,132,320,240] : centre et une partie des rochers, pas la carte entière.

Aucun redimensionnement de carte, ajout de marges vides ou zoom global forcé. `WindowZoom` agrandit l’affichage, pas le monde. Les PNG de viewport sont des **simulations**, pas des captures d’une exécution PMDO. Les Ground du boss gardent leur `TexSize=3` natif et leurs tiles24px ; ne pas appliquer aveuglément la règle Ground8 à cette référence existante.

## Fichiers et installation

- Quatre `.rsground` statiques de lecture/édition, un par tracé, avec les collisions du Ground source.
- `ib1_ice_arena.rsmap` : carte de test sans adversaires ni fin automatique.
- `ib1_ice_boss_halcyon.rsmap` : copie optionnelle du roster original et de ses positions ; initialisation/nettoyage des pics intégrés au système de victoire Halcyon.
- Deux banques `.tile`24px, quatre `.dir` d’objets, donnée Tile `ib1_ice_spikes`, module Lua et tables des quatre trajectoires.
- PNG de plans, modules, poses, quatre états ; aperçu complet, viewport et WebP animé.

Fermer PMDO, sauvegarder le mod puis extraire le ZIP dans un dossier temporaire :

```
python INSTALLER.py /chemin/PMDO/MODS/mon_mod --dry-run
python INSTALLER.py /chemin/PMDO/MODS/mon_mod
```

Par défaut : graphismes et **Ground statiques uniquement**, sans modifier les scripts globaux ou installer des événements non enregistrés. L’index des tilesets est fusionné ; un fichier modifié n’est jamais écrasé.

Pour le contrôleur et les cartes Dungeon, utiliser **une copie de Halcyon working-copy compatible0.8.9**, namespace`halcyon` :

```
python INSTALLER.py /chemin/PMDO/MODS/Halcyon --halcyon-boss --dry-run
python INSTALLER.py /chemin/PMDO/MODS/Halcyon --halcyon-boss
```

Ce mode ajoute une ligne `require 'halcyon.ib1_ice'` à `event.lua`, avec sauvegarde et sans remplacement du fichier ; il refuse un autre namespace. **Enregistrer/sauver `ib1_ice_spikes` dans l’éditeur des données Tile et reconstruire les index de données de votre version avant le test Dungeon.** Aucun index binaire Data/Tile universel n’est prétendu généré. Ouvrir les nouvelles cartes dans l’éditeur ; aucune Zone/campagne existante n’est remplacée ou redirigée automatiquement. Les fonctions de victoire Halcyon restent des dépendances du boss optionnel.

Le WebP montre la propagation/retraite exacte en frames, avec des pauses de lecture60/32frames : **ces pauses ne convertissent pas les tours du joueur en secondes**. Les ressources restent séparées, modifiables.

## Vérification et limites

Contrôles : blobs sources, références lisibles, géométrie/72cases inchangées, correspondance des quatre traces au Lua natif, rythme et états du contrôleur Lua avec API simulée, protection des décorations étrangères, codecs24px/.dir, liens de ressources, installateur en simulation/réinstallation/refus de conflit, viewport. **Le moteur PMDO et la partie entière n’ont pas été exécutés** ; les adaptateurs de test ne prouvent pas la compatibilité de chaque API.NET ou l’équilibrage du combat.

Depuis la racine : `.venv/bin/python source/ice_boss_v1/restore.py --restore` pour les livraisons ; `--build --verify` pour reconstruire (Pillow, NumPy, lupa) ; `--serve --port 8017` pour les fichiers directs. Code, sources et gros fichiers sont conservés dans l’historique Git complet avec SHA ; cache ignoré volontairement. Les anciennes cartes, variantes des plaines et packs viewport ne sont pas remplacés.
