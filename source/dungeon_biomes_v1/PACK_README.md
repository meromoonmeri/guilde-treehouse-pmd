# Donjons réinventés — lot 1 / cinq duos

Dix créations : entrée + zone finale pour **forêt lumineuse, île céleste, volcan, désert, courant marin**. Arrivée/retour sud ; entrée nord dans les cartes d’entrée. Les six autres duos restent à produire. Aucun Pokémon cuit, aucune ancienne map remplacée.

## Fichiers utilisables

- `cartes/` : dix cartes en **calques PNG transparents de surfaces visibles**, alignés. La recomposition des calques est exactement le terrain détouré. `python assemble.py --tick 64 --out assembled` recrée les dix terrains PNG complets et dix démonstrations PNG (Pillow et NumPy nécessaires). Ces images redondantes ne sont pas stockées une seconde fois dans le ZIP. Les parois/arbres ne sont pas des objets mobiles avec leur face cachée reconstruite : retirer un calque laisse une lacune. Les masques sont une segmentation de la composition, pas des collisions validées.
- `animations/` : véritables états PNG des animations extraites, indépendants du terrain. **Pas de lumière ou de lave cuite dans le sol.** Les basenames sont uniques, les canevas divisibles par 8 (Ground). Ne pas appliquer cette règle à tous les formats DTEF.
- `manifest.json` : ordre des calques, sélection des frames, cadences et modes de composition. Les chemins de frames sont relatifs à ce ZIP.
- `references/` : les onze backgrounds natifs décodés à 1×, distincts des créations. Ils ne sont pas présentés comme les nouvelles cartes. Les cycles du désert d’origine sont fournis comme référence supplémentaire, sans préplacement sur le nouveau sol.
- `native_sources.zip` + `audit.json` : fichiers binaires publics BPC/BMA/BPL/BPA et extraits du code source épinglé, vérifiés par SHA Git et SHA-256. Ni ROM ni ressources obtenues dans une compilation privée.

## Animations : important

Les ticks ci-dessous sont des mises à jour du jeu. Les aperçus utilisent une base de 60 Hz. La phase initiale est une convention de lecture en régime établi, pas une capture de l’initialisation du moteur.

| Groupe | Données | Cadence / période |
|---|---|---|
| Forêt | H07P04W : BPA **et** BPL | géométrie 14 × 7 ticks ; palette 32 × 8 ticks ; période commune **12544 ticks** |
| Île, ciel natif seul | couche 1 de H29P04, BPL | 36 états × 6 ticks = 216 ticks ; pas de faux scroll de nuages |
| Courant marin | H02P02W, BPL | 32 × 8 ticks = 256 ticks |
| Volcan, lave | textures H26P01, BPL p5–p8 | 31 × 4 ticks = 124 ticks ; patches 64² assemblés à 1×, raccords par sélection de pixels, jamais par interpolation |
| Volcan, particules | W04, BPA | 16 × 7 ticks = 112 ticks ; fenêtre source [0,0,480,312] |
| Désert, voile météo | W05, BPL + scroll du jeu | 32 × 8 ticks ; déplacement horizontal 1 px / 4 ticks ; wrap horizontal480 ; période combinée 3840 ticks |

La forêt contient **448 états combinés**, pas 448 frames à jouer dans l’ordre des noms. À un tick donné : `BPA=(tick//7)%14`, `BPL=(tick//8)%32`. Les deux horloges sont indépendantes. La banque fournit toutes leurs combinaisons en PNG ; la formule du manifeste donne la bonne sélection. Le code source décrémente le compteur BPA après comparaison (durée stockée +1), et le compteur BPL avant comparaison (durée stockée).

Les lumières de forêt, courant marin et désert requièrent une **addition**, coefficients 16/16, pas un collage alpha normal : le noir est neutre. Les PNG natifs conservent les couleurs et la transparence des indices source. Le compositing d’aperçu applique l’équation RGB555 du renderer PC ; les images natives extraites ne sont pas des captures GPU. Le ciel et la lave vont sous le terrain, les effets météo au-dessus. Le placement des textures et le cadrage des effets sur les nouveaux terrains sont des compositions nouvelles, pas le layout canonique. Pour éviter une grille de répétition visible, les patches de lave sont raccordés par des coutures à coût minimal : chaque pixel et chaque couleur restent ceux de la source, sans miroir/rotation/interpolation. Le PNG de provenance encode la coordonnée source de chaque pixel. Le voile désert est ancré en haut sur264px ; le bas du canevas reste transparent, sans répétition verticale ajoutée au plein-plan. Le moteur natif traite cet effet avec une caméra écran y=0 et un wrap480×264.

Le volcan d’origine a d’autres cycles BPL (période commune 14880 ticks). La nouvelle surface de lave utilise seulement les palettes réellement présentes dans son échantillon : elle n’imite ni ne prétend remplacer les colonnes de lave du background d’origine. Le désert d’origine comporte également deux cycles du terrain, p8=(4,12), p9=(4,9), conservés dans `references/desert_cycles/`, mais non plaqués sur le nouveau sol.

## Aperçus directs et limites

Le dossier public `renders/dungeon_biomes_v1/apercus/` contient une planche PNG et cinq WebP animés (deux cartes chacun). Ce sont des **extraits échantillonnés de 128 ticks / environ 2,13 secondes (début au tick32)**, une image tous les 8 ticks, lus une seule fois. Les rouvrir pour rejouer. Ils ne prétendent pas être les longues boucles composites intégrales. La planche PNG est une présentation quantifiée et les WebP sont compressés avec perte pour rester légers ; **les calques et frames PNG du ZIP sont sans perte**. La planche montre le tick64. Les PNG/horloges du pack permettent de reconstituer les cycles sans réinitialisation arbitraire.

Les créations ont réellement été produites au générateur comme compositions complètes sur magenta ; seules ces créations ont été normalisées/réduites en palette. Les bruts RGBA sont conservés sans perte dans l’historique Git (`source/dungeon_biomes_v1/raws/archive.json`). Les éléments natifs ne sont ni recolorés, ni redimensionnés, ni retournés après décodage. Les flags de flip BPC sont interprétés pour reconstituer le dessin original, pas pour inventer une variante.

Audit : les **207 fichiers H** de la version épinglée PMD Red PC Port sont identiques aux blobs de la décompilation pret épinglée. Les effets ne sont pas tous des BPA. Le cas des palettes hors banque a été résolu : seules des tuiles entièrement transparentes les utilisent ; toute couleur visible hors banque provoque une erreur, aucun modulo de palette.

**Pas de validation PMDO/PC-port exécuté, de collision, warp ou accord artistique revendiqué.** La distinction technique native/générée ne garantit pas la qualité artistique. Conserver l’historique Git complet pour reconstruire les bruts archivés. Les anciennes livraisons, Beach et le mobilier V8 restant sont hors portée de ce lot.
