# Entrée aride V1 — rendu généré référencé PMD, 6 calques

Référence : `entrancearidedungeonpmdsky.png` (408×288, conservée intacte dans
`source/entree_aride_generee_v1/references/`). Arrivée SUD, grotte au NORD.

## Méthode (honnête)

- 2 bruts générés guidés par la référence : relief complet sur magenta
  (falaise + grotte + arbres morts + cailloux) et sol sableux complet.
- Normalisation uniforme isotrope /3 (1224×864 → 408×288), jamais anisotrope.
- Alpha par inondation du magenta depuis les bords (seuil 130) + seuil serré
  global d<40 + nettoyage de frange 1 px. Zéro magenta résiduel testé.
- Découpe couleur + composantes connexes en partition stricte :
  grotte > arbres > cailloux > ombres, falaise = reste.
- **Dessins générés, PAS des pixels natifs, PAS une mosaïque de bouts de maps.**

## Contenu

| Fichier | Rôle |
|---|---|
| `couches/EntreeArideV1_01_sol.png` | Sol sableux complet, opaque |
| `couches/EntreeArideV1_02_falaise.png` | Falaise ocre |
| `couches/EntreeArideV1_03_bouche_grotte.png` | Bouche sombre (bbox 190,49–223,85) |
| `couches/EntreeArideV1_04_arbres_morts.png` | Arbres morts (gris reconnectés ≥30 px) |
| `couches/EntreeArideV1_05_cailloux.png` | 13 cailloux isolés (déplaçables) |
| `couches/EntreeArideV1_06_ombres.png` | Petits gris + micro-sombres |
| `scene/scene_complete.png` | Recomposition exacte des 6 calques |
| `review/planche_calques.png` | 6 calques sur damier + scène |
| `EntreeArideV1.ora` | Projet éditable 6 calques |
| `manifest.json` | Tailles, hashes, corridor, méthode |
| `apercu_entree_aride_v1.html` (racine) | Viewer autonome : calques, grille 8 px, zoom |

Corridor : bande x 190–221 (32 px) dégagée du sud jusqu'au seuil (y 97),
puis la bouche comme entrée. Indicatif seulement : pas de collisions, warps,
occlusion ni test PMDO. Grille 8 px : 51×36 cases.

## Limites

- Les arbres chevauchant la falaise sont découpés par couleur : masquer leur
  calque laisse des trous dans la falaise (partitions de surfaces visibles,
  pas objets complets avec faces cachées).
- Aucune animation (lot statique demandé) ; aucune validation artistique.
- La référence et tous les anciens lots restent inchangés.

## Reproduction

```sh
.venv/bin/python source/entree_aride_generee_v1/build.py
.venv/bin/python source/entree_aride_generee_v1/package.py  # tests + ZIP
.venv/bin/python -m unittest source.entree_aride_generee_v1.test_build -v
```
