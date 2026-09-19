# Cristal boréal V1 — plusieurs couches animées (lot `cristal_boreal_layers_animees_v1`)

Demande : « je veux plusieurs layer animée de la zone boréal v1 ». La zone visée est `cristal_boreal`
de `renders/layouts_magenta_v1/` (456 × 504) : elle ne livrait qu'une seule couche animée, les douze
poses natives de l'eau. Le lot en ajoute **quatre autres**, chacune sur son plan et à sa cadence.

## Ce qui est livré

| couche | poses × cadence | cycle | empreinte | d'où ça vient |
|---|---|---|---|---|
| `01_animation_eau_protegee` | 12 × 160 ms | 1 920 ms | 167 059 px | fichiers du lot V1, **recopiés octet pour octet** |
| `08_aurore_ciel` | 8 × 120 ms | 960 ms | bande de ciel, lignes 0–151 | `onde_indexee.png` + `onde_alpha.png` du lot V12, rejoués par rotation de palette seule |
| `09_eclats_cristaux` | 8 × 240 ms | 1 920 ms | 23 461 px | classes de luminance des calques `04`, `05`, `07` du socle V1 |
| `10_scintillement_givre` | 12 × 160 ms | 1 920 ms | 9 748 px | points vifs (lum > 200) des poses natives, hors zone protégée, sélection tournante sur 12 diagonales de 8 px, deux allumées par pose |
| `11_lueur_sol` | 8 × 240 ms | 1 920 ms | 39 304 px | le **même** plan d'aurore, rééchantillonné décalé de 6 px par pose sur le sol visible |

Scène maîtresse : **48 poses de 40 ms, cycle 1 920 ms** (40 divise 120, 160 et 240 : aucune couche n'est
rééchantillonnée). Pile du bas vers le haut : `01`, les cinq calques statiques `02 03 04 05 07`,
`09`, `10`, `11`, puis `08` en voile au sommet.

Fichiers : 71 dans `renders/cristal_boreal_layers_animees_v1/` (5,7 Mo) — `calques/<couche>/frame_NN.png`,
`boucles/<couche>.webp` sans perte, `base/*.png`, `masques/*.png`, `SCENE_ANIMEE.webp`,
`SCENE_SANS_VOILE.webp`, `COMPOSITION.png`, `COMPOSITION_SANS_VOILE.png`,
`cristal_boreal_layers_animees.ora` (53 calques, 10 visibles), `PLANCHE_COUCHEES_ANIMEES.png`,
`controles/regions_des_couches.png`, `manifest.json`. Galerie mono-fichier :
`apercu_cristal_boreal_layers_animees_v1.html` (9,4 Mo, images livrées injectionnées).

## Choix assumés, et pourquoi

- **Le ciel de cette zone est entièrement dans la zone protégée** (`~terrain` ∩ `~preserve` = 437 px sur
  tout le canevas, 0 px dans la bande haute). Une aurore ne peut donc ni être posée « dans le trou du
  ciel », ni être fondue dans la base sans écraser des pixels natifs. Elle est livrée **en voile séparé,
  alpha plafonné à 96/255**, et la scène correspondante sans voile est livrée à côté. C'est le seul
  calque qui touche la zone protégée, et il est retirable en un clic dans la galerie comme dans l'`.ora`.
- **`10` ne peut pas être une simple recopie des poses natives** : hors zone protégée, le GIF ne change
  pas d'une pose à l'autre, donc une recopie pose à pose donnait douze images identiques (piège réel,
  détecté au contrôle). Ce qui tourne est la sélection en diagonales, pas le déplacement.
- `11` n'a pas sa propre couleur : il puise dans le plan de `08`. Le lien lueur ↔ aurore est donc exact,
  testé, et non pas une ressemblance.
- Aucun pinceau, aucune couleur inventée : recopie, rotation d'indices, échantillonnage décalé, voile
  déclaré. Les règles de teinte (`tint(boréal)`) sont importées de `source/layouts_magenta_v1/palette.py`,
  pas réécrites.

## Contrôles

`source/cristal_boreal_layers_animees_v1/test_build.py` — **18 tests PASS**, qui relisent les livrables et
recomposent la pile eux-mêmes : octet-identité des douze poses natives et des cinq calques, empreintes
déclarées au manifeste, zone protégée égale à la pose native sur les 48 poses, voile confiné au ciel et
plafonné, trois couches ajoutées écrivant 0 px sur la zone protégée, aucune pose identique à sa suivante,
durées réelles lues dans les conteneurs WebP, couleurs de l'aurore ⊂ palettes V12, couleurs des éclats ⊂
socle, `.ora` = pile livrée, masques = empreintes déclarées, galerie reprenant les images livrées.

Le build écrit aussi ses propres garanties dans `manifest.json['controles']` et échoue si l'une tombe.
`package.py` régénère, lance les tests, vérifie le JS de la galerie, écrit `verification.json` et emballe
`renders/cristal_boreal_layers_animees_v1_pack.zip` ; `--check` vérifie sans régénérer.

**Non testé :** tout le reste. Aucune collision, aucun warp, aucun import moteur, aucun rendu validé dans
PMD Online ; l'aperçu n'a pas été ouvert dans un navigateur de jeu. Art **non approuvé**.

## À ne pas refaire

- Croire un WebP animé fidèle à son nombre de poses : l'encodeur **fusionne les poses consécutives
  identiques en additionnant leurs durées** (48 poses → 24 images encodées, cycle conservé). Lire
  `n_frames` comme une preuve d'animation est un faux négatif ; lire les durées ANMF et le total est bon.
- Comparer des calques après un enregistrement **avec perte** : `quality=100` reste du lossy et faisait
  disparaître une couche entière dans les boucles. Tout est écrit `lossless=True`.
- Réutiliser `terrain_detoure.png` comme un masque `L` : c'est un RGBA, le tracé est dans l'alpha ; le
  lire en luminance silently élargissait le terrain et vidait le ciel.
