# Aurores V1 — preuve native et reconstruction reproductible

Livraison : [`exports/ice_arena_aurora_native_v2`](../../exports/ice_arena_aurora_native_v2/README.md).

**Statut : mécanisme et dessins natifs retrouvés ; port de rendu RGB8 pour PMDO. Pas de capture DS, pas de validation GPU PMDO.** Les anciennes livraisons ne sont pas modifiées.

## Sources fixées

- `pret/pmd-sky` : **`a3d641227a8e61c887987f17a3d0b7fad6d8f671`**.
- RogueEssence, sous-module de PMDO **0.8.12** : **`4961b2271bb0cace74f40f6a85e799e8e4848ace`**.
- Branche utilisateur de référence : `arena/01a095e8-guilde-treehouse-pmd`, résolue en `d58045243ba2b2089e25ff54020360c4cbbda543` sans changer de branche.
- Travail effectué sur `arena/01a0b45b-guilde-treehouse-pmd`.

[`references/sources.json`](references/sources.json) contient les chemins amont, URLs au commit, identifiants Git blob et SHA256. Les fichiers utilisés sont conservés dans `references/`. `verify.py` recalcule **à la fois** SHA256 et l’identifiant Git blob des données enregistrées.

| Fichier natif | SHA256 |
|---|---|
| `v38p05a.bma` | `c33aa35632b0fdd3ed0161ef841c7c4d94f73a34538027c2fed991396caca111` |
| `v38p05a.bpc` | `1123e42dc5b617a28f82155a918fe74c15347f74319a8b2248719eb2dacd1afc` |
| `v38p05a.bpl` | `c4dc1d836cc72d8f58e10542a66345cd99e12b5bfaed577e1285ee1b07391242` |
| `D52P32A/n09a1207.ssb` EU | `84d464eec7e5e9388d374014f56a22236d7da21f70e6e030b70588b6ca10a80c` |
| `D52P32A/n09a1207.ssa` EU | `9112527c94a47332e3a1a92d461b1737d8c8b8f9b56c3832597d2d6d1bb9e628` |

Les données de l’animation ne nécessitent pas de ROM ou de lien LFS. Les chemins temporaires de recherche et réponses contenant des URLs signées ne font pas partie de cette livraison.

## Pourquoi l’ancienne recherche n’avait pas trouvé le cycle

Le fond n’a ni BPA ni palette BPL animée. Une recherche limitée aux banques d’animation ou aux noms « aurora » ne pouvait pas retrouver son mouvement : **la cinématique anime deux couches de fond statiques par un effet de script**.

Le décodage de `v38p05a` produit deux images de 264 × 216 px : couche basse SkyTemple 0 → BPC1, couche haute SkyTemple 1 → BPC0. BPC0 est exactement la référence `aurorepmdsky.png`. Il n’y a aucun pixel transparent dans ces deux images natives ; la découpe en cinq PNG d’effets est donc une opération éditoriale ultérieure, pas une affirmation sur la structure BPC d’origine.

## Chaîne de preuve, du script aux registres

Les adresses/symboles ci-dessous sont les **labels NA du code `pret`** ; les données de script analysées sont **EU**, au même commit. Aucun binaire ARM régional n’a été exécuté par cet audit.

1. **Scène** — `SCRIPT/D52P32A/n09a1207.ssb`, routine 0 : chargement `back2_SetGround(V38P05A)` puis `supervision_Acting(7)`. La couche SSA 7 associe l’acteur NPC_DEBUG 68 ; la routine 2 pilote le fond.
2. **Commandes** — routine 2, offsets 4492–4502 : effet 5 pendant 120 ticks, attente 120, effet 3 pendant 120 ticks, attente 120, saut au début. Le build reparse le SSB et contrôle ces commandes.
3. **Interpréteur** — `asm/overlay_11.s`, `RunNextOpcode`, opcode 22, label `_022DE808` : `ov11_022EF594(1, effect, duration)` pour `back2_SetEffect`.
4. **Dispatcher** — `asm/overlay_11_022EE5E4.s`, `ov11_022EF594` : effet script 3 → `_022EF61C` → `ov11_022E9DE4`; effet script 5 → `_022EF628` → `ov11_022E9E2C`. Tous deux sélectionnent **l’effet interne 3**.
5. **Sens du fondu** — `src/overlay_11_022E9A78.c`, fonctions `ov11_022E9DE4` et `ov11_022E9E2C` : remise à une extrémité puis interpolation vers l’autre, par `sub_0200BB60` et `sub_0200BB74`.
6. **Bornes et interpolateur** — `asm/main_0200B33C.s`, `sub_0200B928`, `UpdateFadeStatus`, `HandleFades`. La table `_02094AE8`, dans `asm/main_rodata_020925A0.s`, contient les valeurs signées `0, -256, +256, 0`. Les branches de `HandleFades` décrémentent le compteur avant interpolation entière.
7. **Application par frame** — `asm/overlay_11_022EA024.s`, `ov11_022EA0BC`, cas interne 3 → `_022EA4A4` : BG2 premier opérande, BG3 et OBJ seconds opérandes ; valeurs `r7` et `128-r7`. `r7 = clamp((fade+256)/2, 0, 128)`. En fin de disparition, BG2 est désactivé si la valeur est négative.
8. **Quantification matérielle** — `src/main_02009F9C.c`, `sub_02009E70` : les deux coefficients sont convertis indépendamment par `(value & 0xF8) >> 3`, puis envoyés à `G2x_SetBlendAlpha_`, écran secondaire à `0x04001050`.
9. **Attente** — `asm/overlay_11.s`, `_022E0378` charge la durée de `Wait`; `_022E2A98` teste la valeur avant décrément et reprend l’exécution quand elle est déjà nulle. La boucle de `FuncThatCallsRunNextOpcode` permet le traitement immédiat des opcodes non bloquants. Pas de phase d’attente inventée entre les deux demi-cycles dans le port.

Le contenu OBJ, les personnages de la cinématique, sa caméra et les éventuels fondus d’entrée/sortie de scène ne font pas partie du fond demandé. Le port conserve le cycle périodique du BG entier, placé dans la V1.

## Mathématiques du cycle exporté

Pour `t` modulo 240, avec origine à l’extrémité précédente du fondu entrant :

```text
0 <= t <= 120 : v = -256 + floor(256 * (120-t) / 120)
120 < t < 240 : v = -floor(256 * (240-t) / 120)
r = clamp(floor((v+256)/2), 0, 128)
EVA = (r & 0xF8) >> 3
EVB = ((128-r) & 0xF8) >> 3
```

Le test indépendant reconstruit un état décrémentant un compteur de 120, dans les deux sens, puis décale circulairement ses résultats. Il compare les **240 échantillons** à la formule, sans réutiliser celle-ci comme seule référence.

Le rendu PMDO exporté applique les coefficients aux couleurs RGB8 BPL d’origine :

```text
port_RGB8(x,y) = floor((BPC0_RGB8(x,y) * EVA + BPC1_RGB8(x,y) * EVB) / 16)
```

Il conserve les extrémités pixel pour pixel. **Il ne simule pas l’étape RGB8 → RGB555 puis l’expansion d’un framebuffer DS vers une image d’écran.** La preuve du mécanisme natif ne doit pas être présentée comme une certification de rendu LCD/capture officielle.

## Calques et terrain

La séparation en ciel, rubans, étoiles, brume et glace est détaillée dans `separation_masks` et `split_frame`. Elle réutilise le masque de glace visible déjà fourni dans `exports/zones_relayout_v2/aurora`. Les étoiles sont les petites composantes connexes natives ; les recouvrements avec un ruban de l’autre dessin sont laissés dans les rubans.

Chaque pixel opaque de composant garde exactement la couleur du fond RGB8 calculé. Les pixels égaux au ciel uni sont transparents dans les composants hors `Sky`. **Les cinq plans se recomposent exactement pour les 33 états.** Ce ne sont pas des textures cachées reconstruites.

Les huit statiques V1 sont copiés byte pour byte. La composition utilise le ciel extérieur statique puis le nouveau fond puis les cinq plans de terrain 04–08. Les anciens plans de fond 02/03 sont conservés dans le dossier mais remplacés visuellement par le fond natif animé. Tous les pixels opaques du terrain et tous les pixels hors du rectangle de fond sont contrôlés contre V1.

## Format PMDO, import et mémoire

Sources au sous-module 0.8.12 dans `references/pmdo/` :

- `DirSheet-0.8.12.cs`, `Load` : longueur PNG Int64, PNG, largeur de case Int32, hauteur Int32, `RotateType` Int32, nombre de frames Int32.
- `DrawDir`, `RotateType.None` : parcours des cases en lignes, `frame % TotalX`, `frame / TotalX`.
- `AnimData.cs`, `GetCurrentFrame` : `EndFrame` inclusif, `FrameTime` en frames ; la recette 0–239 / 1 contient bien les 240 ticks.
- `MapBG.cs` : déplacement en pixels/s, parallax, répétition et appel à `GetBackground`.

Les six `.dir` sont destinés à **`Content/BG/`**, pas à `Content/Background/`. Une texture 15 × 16 cases mesure 3960 × 3456 px ; le mode composite évite de charger cinq textures de cette taille simultanément. Les alpha sont 0 ou 255, et les RGB des pixels transparents sont nuls, donc correctement prémultipliés.

## Reproduction et vérifications

```bash
python3 -m venv .venv                 # seulement si nécessaire
.venv/bin/pip install -r source/ice_arena_aurora_native_v2/requirements.txt
.venv/bin/python source/ice_arena_aurora_native_v2/build.py
node source/ice_arena_aurora_native_v2/test_viewer.cjs
.venv/bin/python source/ice_arena_aurora_native_v2/verify.py
```

- `build.py` : extraction native, contrôle SSB, cycle, séparation, PNG/WebP, conteneurs `.dir`, recette et atelier autonome.
- `verify.py` : 49 contrôles de fichiers, calculs, composition, préservation, durée et toutes les cases des conteneurs.
- `test_viewer.cjs` : 15 contrôles de DOM/canvas **simulés**, aucune capture d’un vrai navigateur.

Aucun résultat de test moteur d’une ancienne livraison n’est réutilisé comme preuve pour celle-ci. **Pas de chargement PMDO natif, de GPU, de collisions ou de parcours en jeu exécuté sur ce nouveau pack.** À faire sur un échantillon du BG composite avant l’import des calques multiples ou toute généralisation.
