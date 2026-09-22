# FD1 — trois derniers duos : forêt secrète, Mont Discipline, plaines brûlées (22 septembre 2026)

Six cartes (entrée + finale par lieu), 4 à 6 groupes sémantiques chacune, textures canoniques du lieu de référence et Ground PMDO d'édition.

## Origine de chaque matériau (à ne pas confondre)

| Lieu | Natif 1× inchangé | Généré, quantifié dans la palette native du lieu |
|---|---|---|
| Forêt secrète H07P08 (456×312) | souche centrale (palette 4, recadrée, repositionnée dans la finale) ; référence complète | sol continu, troncs/canopée, feuillage avant (bruts du commit 90fa7e28), **toiles** (nouvelle génération, redimensionnées) |
| Mont Discipline H16P01 (480×336) | référence complète seulement | sol sable/herbe continu, dalles, portique nord + marches (entrée), cadre végétal, poteaux/rondins (séparés par couleur depuis le plan végétal) |
| Plaines brûlées H06P05 (456×336) | ciel (lignes 0–95), collines lointaines (palettes 1/2, lignes 96–135), **grands feux BPA 10 poses×3 ticks**, **flammèches palettes 5/6, 9 phases×4 ticks** — pixels et positions natifs | sol brûlé continu (≥ y96), roches chaudes, troncs brûlés |

- Aucun natif n'est redimensionné, recoloré ni retourné. Les pièces générées sont ajustées en NEAREST puis quantifiées sans dithering dans la palette native ; le test refuse toute couleur hors palette sur les plans générés non-sol.
- Les feux natifs sont isolés par masque couleur+variation à l'intérieur des quatre blocs animés natifs : les roches/sol de ces blocs sont omis. Ce n'est pas un sprite autonome fourni par la banque. Les flammèches excluent le fond plat rouge des tuiles (pixels non variants).
- H07P08 et H16P01 n'ont aucune animation native : aucune n'est inventée.
- Le sol est opaque et continu sous tout le décor (vérifié). Arrivée sud libre (érosion 17 px), corridor nord de l'entrée secrète atteint.

## Fichiers

`renders/final_duos_v1/` : `FD1_<lieu>_duo.png`, `FD1_<lieu>_{E,F}_calques.png` (planches par calque), `FD1_brulees_duo_anime.webp` (période conjointe 180 ticks = 3 s, boucle), `FD1_<lieu>_duo_calques.zip` (PNG alignés, manifeste, frames, natifs, provenance), `FD1_<lieu>_PMDO.zip` (Ground `vp1_fd1_*`, `.tile` 8 px, INSTALLER.py, aperçus viewport 320×240).

Reproduction : `.venv/bin/python source/final_duos_v1/work.py --build --verify --pmdo`. Bruts : `raws/index.json` (7 bruts déjà en Git + 4 nouveaux WebP lossless de ce tour ; bruts secrète lus depuis le commit 90fa7e28).

## Limites

Tests d'images et de sérialisation uniquement ; **PMDO non exécuté**, aucune approbation artistique revendiquée. Collisions libres, pas de warps ni de rencontres. Le viewport reste 320×240 à x1 ; les images ne sont pas agrandies. Les 22 cartes du programme sont désormais toutes présentes sur la branche (16 précédentes + ces 6) ; MD1 historique n'est pas restauré, ce lot est une nouvelle version.
