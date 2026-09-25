# Furnace Desert — biome eau V1 (calques PNG animés)

Galerie autonome : **`apercu_furnace_desert_eau_v1.html`** (racine du dépôt) : calques activables, lecture/pause, phase par phase, zoom 1×/2×, comparaison avec le désert d’origine.

Demande : « cette zone en biome swapping en eau, remplace tout le sable par de l’eau sur son propre calque et anime-le ainsi que le siphon ».

## Calques (456 × 336 px, grille 8 px, origine commune (0,0))

| N° | Fichier (`calques/`) | Contenu | Phases |
|---|---|---|---|
| 01 | `FDE_V1_01_ciel.png` | Ciel source exact (rayons de soleil présents dans cette version source) | statique |
| 02 | `FDE_V1_02_eau.png` | Eau : mer native D25P11A, 15 phases x 130 ms, remplace tout le sable | 15 |
| 03 | `FDE_V1_03_ombres_contact.png` | Ombres de contact semi-transparentes au pied des roches | statique |
| 04 | `FDE_V1_04_siphon.png` | Siphon en tourbillon : cycle de palette natif D14P11A, 6 phases | 6 |
| 05 | `FDE_V1_05_cascades.png` | Chutes d’eau (anciennes chutes de sable), défilement 6 phases | 6 |
| 06 | `FDE_V1_06_roches.png` | Roches et mesas source exactes | statique |
| 07 | `FDE_V1_07_premier_plan.png` | Roches et piliers du premier plan, source exacts | statique |

`calques/FDE_V1_composite.png` = empilement exact des 7 calques (phase 0). Les phases de chaque calque animé sont dans `phases/eau/`, `phases/siphon/`, `phases/cascades/` ; `FDE_V1_animation.webp` montre la boucle complète ; `FDE_V1_furnace_eau.ora` ouvre les calques (phase 0) dans Krita/GIMP. Import PMDO : **PNG to Tileset en 8 px** ; noms de fichiers uniques (préfixe `FDE_V1`).

## Animation

- **Eau** : mer native de `large.D25P11A` (PMD Explorers of Sky) : GIF de 30 images × 130 ms dont le cycle réel est de **15 phases** (1,95 s) — 15 PNG dans `phases/eau/`. La haute mer de la référence est doublement périodique (réseau (48,48) & (144,72)) : sa tuile 48×72 est extraite pour chacune des 30 phases (couleur majoritaire par classe du réseau, accord 95.9%) puis répétée sans couture sur toute l’ancienne surface de sable.
- **Siphon** : même mécanique que les siphons natifs de `large.D14P11A` (pur cycle de palette, 6 phases, vérifié couleur → couleur). Les bandes suivent le contour ondulé de la cuvette d’origine et avancent vers le centre ; halo d’eau claire à la place du halo de sable clair. 6 phases × 130 ms (le natif D14 tourne à 60 ms ; ralenti pour un grand tourbillon).
- **Chutes** : les deux chutes de sable deviennent des chutes d’eau ; texture de chevrons de la chute gauche (hors rayon), défilement vers le bas de 16 px par phase, boucle de 96 px = 6 phases × 130 ms.
- Tout est synchronisé sur un pas de 130 ms (≈ `FrameLength` 8 à 60 im/s dans PMDO) ; boucle commune : 30 images = 3,9 s (15 × 6 → PPCM 30).

## Ce qui est source exacte / ce qui est transformé

- Ciel et premier plan : **pixels source exacts** (0 différence). Roches et mesas : source exacte sauf **1077 pixels** (bords fondus des rayons de soleil incrustés dans cette version, couleurs uniques) ramenés à la couleur fréquente la plus proche de leur voisinage — nettoyage anti-flou, rien de redessiné.
- Eau : pixels de la mer native D25, phase par phase. Siphon et chutes : leurs formes viennent de la scène, leurs couleurs sont **uniquement des bleus de la palette native de la mer D25** (aucune couleur inventée) — c’est la transformation demandée (biome swap), pas un élément officiel.
- Ombres de contact : noir semi-transparent, proportionnel à l’assombrissement du sable d’origine au pied des roches.

## Source de la scène — important

La pièce jointe (`Rescue_Team_Friend_Area_-_Furnace_Desert.png`, version du wiki Mystery Dungeon) **n’est pas arrivée dans le bac à sable**, et le wiki n’est pas joignable directement. La scène utilisée est la version pleine taille 456×336 « Furnace Desert, original version » (pamtre-berry.neocities.org), même décor mais **avec de grands rayons de soleil incrustés** : ils restent visibles sur le ciel et les roches de droite. Si tu déposes ton fichier dans le dépôt (par ex. `source/furnace_desert_eau_v1/references/`), il suffit de changer `REFERENCE` dans `segment.py` et de relancer — tout le pipeline est automatique.

## Vérifications (`verification.json`)

- `gate.py` : **PASS** sur `calques/` (grille 8 px, alpha binaire hors ombres, zéro magenta, palette pixel art, recomposition exacte).
- Pixels source exacts : ciel, roches, premier plan = 0 différence.
- Couleurs de l’eau = couleurs de la phase native correspondante ; siphon et chutes ⊂ palette de la mer D25.
- Phases distinctes : eau 15, siphon 6, chutes 6.
- WebP relu : 30 images identiques aux empilements ; ORA : image fusionnée = composite.
- **Non testé** : rendu dans PMDO, collisions, pack `.rsground` (non demandé pour ce lot).

## Reconstruire

```sh
.venv/bin/python source/furnace_desert_eau_v1/export.py
.venv/bin/python source/controle_qualite_pixel/gate.py renders/furnace_desert_eau_v1/calques
```
