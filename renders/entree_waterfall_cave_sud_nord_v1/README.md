# EWC1 — Entrée Waterfall Cave sud → nord, format 4:3 vaste

Demande : « tu dois utiliser la méthode et reprendre seulement de ta branche parente. Et refaire waterfall avec la génération fond majenta multicalque ». Ce lot repart **uniquement de la branche parente** (Entrée Jungle V1, `0eaa002c`) : rien n'est repris des sessions parallèles. Taille : **768 × 576 px = 96 × 72 cases de 8 px**.

- Aperçu : `apercu_entree_waterfall_cave_sud_nord_v1.html` (racine) ou `review/EWC1_scene_animee.webp`.
- Pack PMDO 0.8.12 : `EWC1_projet_pmdo_0812.zip`.
- Calques PNG 8 px (préfixe `EWC1_`) : `EWC1_calques_png_8px.zip`.
- Source : `source/entree_waterfall_cave_sud_nord_v1/`, 13 tests.

## Méthode : textures canoniques par rendu généré référencé

La référence est `entrancecascade.png`, la capture de l'entrée de Waterfall Cave (PMD Explorers) : grande cascade au nord, promontoire de sable, falaises ocre à bonsaïs. Cette capture a été **passée au générateur comme image de référence**. Les prompts complets sont dans `manifest.json` → `generation`.

1. `bruts/decor_magenta.png` (1200 × 896) : décor complet et **nouveau** en 4:3. Toute l'eau plate (deux bassins) est peinte en magenta ; la cascade, son écume et la vasque restent dessinées.
2. `bruts/sol_complet.png` : sable complet, obtenu par édition du décor ; il sert de sous-couche sous tous les calques.
3. `bruts/ecume_poses.png` : planche d'écume sur magenta. Le générateur a rendu une grille 4 × 4 au lieu des 2 × 6 demandées ; les cases sont choisies à la main (rangées 1-2 : bouillon en 8 poses ; rangée 4 : embruns en 4 poses).

### Fidélité au rip, mesurée par test

Les distances sont celles entre couleurs moyennes RGB, avec le même classifieur des deux côtés ; le rideau du rip est pris dans la boîte x 150-355, y 0-180.

| Matière | Rip | Brut généré | Distance brut | Calque final | Distance finale |
|---|---|---|---|---|---|
| sable | 226,179,107 | 225,177,104 | 3,4 | sable | 6,5 |
| roche | 173,139,97 | 167,135,95 | 8,2 | falaises | 5,0 |
| feuillage | 78,128,43 | 81,128,43 | 2,9 | arbres | 2,3 |
| rideau de cascade | 102,175,204 | 113,175,202 | 11,0 | cascade | 8,8 |

Le test impose une distance inférieure à 20 pour chaque matière, sur le brut comme sur les calques finaux.

## Normalisation et palettes

Le décor est réduit d'un facteur **uniforme** 576/896 → 771 × 576, puis recadré au centre à 768. La réduction se fait par moyenne **par classe** (`down_class` du gabarit Jungle), et chaque pixel revient à la classe de poids maximal.

**Palettes séparées** : dans la palette commune de 96 couleurs, le rideau virait au vert-gris (bleu moyen 204 → 143) et la bouche noire au brun. Les palettes finales sont donc :

| Groupe | Couleurs |
|---|---|
| Terrain | 96 |
| Arbres | 24 |
| Eau dessinée (rideau + écume du pied) | 24 |
| Bouche | 12 |

Des tests de régression vérifient que le rideau reste bleu et la bouche sombre.

## Calques (bas → haut)

| # | Calque | Origine | Animation |
|---|---|---|---|
| 00 | eau (bassins + vasque) | structure rivière Métano, **couleurs Métano exactes** | 4 × 10 ticks |
| 01 | scintillements | pixels Métano natifs (12 groupes) | 4 × 10 ticks |
| 02 | sol complet | sable généré séparément | — |
| 03 | sable | sable praticable (plage principale reliée au sud) | — |
| 04 | cailloux | trous du sable praticable, sur leur propre calque | — |
| 05 | touffes | petites touffes vertes (< 300 px en pleine résolution) | — |
| 06 | plateaux | sable non relié au chemin (hauts de falaise, poches) | — |
| 07 | berge | liseré sombre à 4 px au plus de l'eau | — |
| 08 | falaises | roche ocre et blocs | — |
| 09 | arbres | bonsaïs : feuillage et troncs reliés | — |
| 10 | entrée sombre | bouche derrière la cascade, avec son rebord rocheux | — |
| 11 | cascade | rideau généré du décor, rendu périodique | 12 × 4 ticks |
| 12 | écume du pied | écume générée du décor | — |
| 13 | écume | bouillons générés, 5 émetteurs | 12 × 4 ticks |
| 14 | embruns | gerbes générées, 4 émetteurs | 12 × 4 ticks |
| 15 | Top vide (`Layer=4`) | pour vos éléments | — |

La scène boucle en 240 ticks, soit 4 s (PPCM de 40 et 48). Il n'y a **pas de calque d'ombres** : le rendu généré ne contient pas d'ombre portée séparable (595 px candidats, épars), et aucune n'a été inventée.

### Cascade

- **Texture** : chaque colonne du rideau reprend ses **propres pixels générés**, dans la bande y 4-100 (80 colonnes) ou une période plus bas, y 76-172 (61 colonnes), car le rideau est plus étroit en haut.
- **Période** : 72 px, mesurée par autocorrélation des crêtes (74 px). Un fondu de 24 px ferme la période, puis la texture est ramenée à la palette du rideau.
- **Trous** : 1 351 px cachés par les arbres en surplomb sont bouchés par le pixel valide le plus proche sur la même rangée ; 12 colonnes extrêmes sont recopiées.
- **Défilement** : la texture descend de 6 px par phase. Le test vérifie une translation pure, phase 11 → 0 comprise, et que la bouche n'est jamais recouverte.

### Écume et embruns

- **Réduction** : fenêtre de 160 px ramenée à 32 px (×1/5), palette tirée de l'écume du pied du décor.
- **Bouillon** : naît, gonfle, éclate, se disperse, puis 4 phases de repos, avec des émetteurs déphasés de 5 phases.
- **Embruns** : 4 poses puis 8 phases de repos, avec des émetteurs décalés de 3 phases.
- **Contrôles** : l'écume est visible à chaque phase, et elle est découpée à l'eau, au rideau et à l'écume, sans jamais toucher le sable, les falaises ou la bouche (testé).

## Collisions et marqueurs

- `entrance` (392, 560) au sud, sur la plage. `donjon_seuil` (376, 248) au bord nord du parvis, face à la bouche : comme dans le jeu, on entre en marchant vers la cascade. **Aucun warp.**
- 6 196 cases sur 6 912 sont bloquées (plus de 25 % hors sable praticable, cailloux et touffes enclavées). La zone praticable suit le promontoire de la référence : sentier entre les bassins, parvis de la vasque, plage sud. Un chemin libre de 16 × 16 px a été vérifié (546 cases explorées). **À contrôler en jeu.**

## Honnêteté

- Le terrain, la cascade, l'écume et les embruns sont **générés** à partir de la capture : ce ne sont pas des tuiles natives.
- Le défilement de la cascade, les émetteurs et la chronologie sont créés par nous ; ce ne sont pas des animations officielles.
- L'eau est façon Métano (pixels recalculés, couleurs Métano exactes). Seuls les scintillements sont des pixels Métano natifs.
- Aucun test fait dans PMDO ; art non approuvé (`art_approved: false`, `runtime_tested: false`).
