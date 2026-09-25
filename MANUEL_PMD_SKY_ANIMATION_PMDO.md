# Manuel : réutiliser les fonds de PMD Explorers of Sky dans PMDO

Audit du 2026-09-25. Sources :
- la galerie Project Pokémon « Explorers of Sky » ;
- le dépôt `meromoonmeri/PMD-SKY-PMDO-PORT` (branche master) ;
- les fichiers bruts `pret/pmd-sky/files/MAP_BG` ;
- le code de `skytemple-files`.

Données produites : `audits/pmd_sky_port/`. Outils : `tools/pmd_sky/`.

## 1. La galerie Project Pokémon

| Album | Contenu | Usage pour nous |
|---|---|---|
| Dungeon Tilesets (144, `tilesetNNN.dpc.png`) | Tuiles des **donjons aléatoires** (système auto-tile), PNG indexés avec leur palette d'origine | Pas des maps : ce sont des textures de sol, mur et eau pour les étages générés |
| (Animated) Map Backgrounds GIF (42) | Fonds de map avec tuiles **et** palettes animées. L'album prévient que la vitesse peut différer du jeu | Référence visuelle du mouvement, pas du timing |
| Animated Map Backgrounds APNG (40) | Même contenu, en APNG | idem |
| Map Backgrounds (statiques) | Fonds fixes | Textures réutilisables |
| Promo, menus | Illustrations | Hors sujet |

### Lire les noms : `LNNpMMs`

Ce sont les noms des fichiers `MAP_BG` du jeu (`.bma` pour la carte, `.bpc` pour les tuiles, `.bpl` pour les palettes, `.bpa` pour les tuiles animées).

- **Lettre** = famille : `t` ville, `g` guilde, `d` abords et salles de donjon, `v` scène ou cinématique, `s` spécial ou histoire, `p` lieux divers, `h` divers ou caché.
- **`NN`** = numéro de groupe (un lieu). Par exemple `d32` = Grotte d'Aegis (convention du projet).
- **`pMM`** = pièce. Pour les donjons, on observe : `p1x` entrée, `p3x` salle intermédiaire, `p4x` fond ou boss.
- **Suffixe** `a`, `b`, `c`, `a2`… = variante (état de l'histoire, météo, moment de la journée).

### Jouable ou fond ?

La réponse vient de la **collision stockée dans le `.bma`**. Le port l'a reprise telle quelle, et l'outil d'audit la compte.

| | Nombre |
|---|---|
| Grounds du port | 460 |
| **Jouables** (collision présente) | **143** : 101 abords de donjon, 18 guilde, 10 lieux, 7 ville, 6 divers, 1 spécial |
| **Fonds seuls** (aucune collision) | **317** : 122 scènes `v`, 64 spéciaux `s`, 86 fonds et arènes de donjon, 32 lieux `p`, etc. |

La liste complète, avec le type, la taille et l'animation de chaque map, est dans `audits/pmd_sky_port/inventaire_grounds.csv`.

## 2. Comment Sky anime ses fonds

Mesures faites sur les 472 fichiers `.bpl`, avec `tools/pmd_sky/anim_timing.py`. Résultat complet dans `audits/pmd_sky_port/timings_animes.json`.

On compte **152 fonds animés**, avec deux mécanismes indépendants :

1. **Animation de palette** (`.bpl`), sur **110 fonds**. Les pixels ne changent pas : ce sont les couleurs d'une ligne de palette qui tournent (eau, lave, lueurs, cristaux).
   - Chaque ligne a son nombre d'images et sa durée par image.
   - Durées relevées, en images du jeu à 60 fps : **4** (134 cas), 8 (42), 10 (24), 3 (15), 1 (12), 16 (11).
2. **Tuiles animées** (`.bpa`), sur **72 fonds**. Des tuiles 8×8 sont remplacées image par image (cascades, drapeaux, feuillage).
   - Une carte peut en avoir jusqu'à 8 emplacements (0 à 3 pour la couche basse, 4 à 7 pour la couche haute).
   - Durées relevées : **10** (49 cas), 6 (18), 8 (12), 12 (4).

**30 fonds utilisent les deux à la fois.** Les deux horloges tournent séparément. Exemple, `t00p01` (la Place) : sa palette boucle en 6 × 4 images = 400 ms, et ses tuiles animées en 6 × 6 images = 600 ms.

## 3. Ce que fait le port, et ce qu'il perd

Code : `tools/convert_nds_map.py` et `tools/mass_ground_converter.py`.

1. Il calcule toutes les images avec `bma.to_pil(bpc, bpl, bpas)` de skytemple. Dans la couche PMDO, chaque case reçoit sa suite d'images.
2. **Timing perdu.** `to_pil` produit la suite des étapes sans leur durée, et le port impose partout `FrameLength = 10` (60 pour les cases fixes). Conséquences :
   - une palette réglée à 4 images (le cas le plus fréquent) tourne **2,5 fois trop lentement** ;
   - quand palette et tuiles animées se superposent, leurs deux rythmes sont fusionnés, et la cadence d'origine disparaît.
3. **Couches aplaties.** La couche haute du `.bma` est collée sur la couche basse. Le port n'a donc qu'un seul calque `Base`, sans profondeur : rien ne passe devant le personnage.
4. **Chiffres incohérents.** Le rapport annonce 43 maps animées, dont `d53p41b` avec 384 images. Les fichiers contiennent en réalité 145 grounds animés, et 31 images au plus pour `d53p41b`. Il faut se fier à l'audit, pas au rapport.
5. `tools/pmd_sky_port_pipeline.py` est une **simulation** : il affiche « SUCCESS » sans rien faire. Il ne faut pas l'utiliser.

## 4. Règles d'adoption pour nos zones PMDO

1. **Garder les durées d'origine.** Le `FrameLength` de PMDO se compte aussi en images à 60 fps : on recopie la durée du `.bpl` ou du `.bpa` telle quelle. Surtout pas de 10 partout.
2. **Un calque par horloge.** On sépare :
   - la base fixe ;
   - les tuiles animées par la palette, avec la durée de la palette ;
   - les tuiles animées par `.bpa`, avec la durée du `.bpa` ;
   - la couche haute du `.bma`, qui devient un calque de premier plan.

   Si on sépare les horloges, on n'a plus besoin de l'image « plus petit commun multiple », qui fait gonfler le nombre d'images.
3. **Reproduire la palette.** PMDO n'a pas d'animation de palette. On précalcule donc les N images, mais **seulement pour les tuiles qui contiennent une couleur animée**. La planche reste petite et la boucle reste exacte.
4. **Composer nos zones en réutilisant les textures :**
   - base fixe : tuiles extraites et dédoublonnées, réassemblées sur la grille de 8 px ;
   - calques animés : on garde les suites d'images et les durées de la source ;
   - collision : celle de notre nouvelle zone, jamais celle de la source.
5. **Contrôles à chaque zone :**
   - boucle exacte (image N = image 0) ;
   - au plus 16 couleurs par tuile 8×8 si on veut rester fidèle au DS ;
   - chaque durée justifiée par `anim_timing.py`.

## 5. Outils

- `tools/pmd_sky/audit_sky_port.py <clone du port> <dossier de sortie>` : produit l'inventaire CSV et JSON, avec la classification jouable ou fond et les statistiques d'animation.
- `tools/pmd_sky/anim_timing.py <MAP_BG> <codes…>` : donne les durées réelles de la palette et des tuiles animées (nécessite `skytemple-files`, installé dans `.venv`).
- **À faire à la prochaine étape**, au moment de la première zone : `extract_layers.py`, qui produira pour une map les calques séparés (base, palette, `.bpa`, couche haute) avec leurs durées.

## 6. Droits

Ces textures appartiennent à Nintendo, Chunsoft et The Pokémon Company. Le dépôt `zone-pmd` les excluait volontairement (règle « aucun pixel rippé »). Les réutiliser directement est acceptable pour un fan game non commercial, mais cela reste à décider projet par projet.
