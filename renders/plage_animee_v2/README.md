# Plage animée V2 — textures générées par couche + eau en palette cycling

Base : layout et masques V1 (`plage_arene_generee_v1`, conservée intacte).
Référence d'origine `arenapmdskybeach.png` inchangée.

## Méthode (honnête)

- 3 textures plein cadre générées, style guidé par la scène V1 : mer (réseau
  de vaguelettes cyan sur bleu profond), sable (grain + stries), roche
  (rouge bosselé, ombres bleues, mousse).
- Chaque texture est posée sur le masque V1 de sa couche : layout validé
  conservé, rives nettes garanties. Les pixels de chaque couche sont générés,
  la géométrie vient de V1 (vérifié : masques byte-exacts, RGB nouveaux).
- Eau : 1 image indexée (rampe unique de 16, niveaux = luminance + dérive
  spatiale vers les rives : x sur les côtés, y dans le bassin nord) + 16
  tables de couleurs en rotation (+1/phase, 60 ms, 0,96 s). Silhouette fixe,
  boucle exacte, transitions régulières (~13).
- Écume : géométrie V1, 4 niveaux, 16 tables (scintillement sinusoïdal).
- **Cycling NOUVEAU inspiré du canon (sens vers les rives), PAS des frames
  officielles récupérées. Dessins générés, pas des pixels natifs.**

## Contenu

| Fichier | Rôle |
|---|---|
| `couches/PlageAnimeeV2_02_sable.png` | Sable (texture V2) |
| `couches/PlageAnimeeV2_03_falaises.png` | Falaises (texture V2) |
| `couches/PlageAnimeeV2_05_rochers.png` | Rochers (texture V2) |
| `couches/PlageAnimeeV2_06_vide.png` | Vide (V1 byte-identique) |
| `eau/mer_indexee.png` + `ecume_indexee.png` | Images d'indices (L) |
| `eau/palettes_16frames.json` | 16 LUTs mer + 16 LUTs écume |
| `eau/mer/MerV2_00..15.png` | 16 phases mer |
| `eau/ecume/EcumeV2_00..15.png` | 16 phases écume |
| `scene/scene_00..15.png` | 16 scènes recomposées |
| `review/scene_animee.webp` + `.gif` | Animation 16×60 ms |
| `review/planche_calques.png` | Statiques + 16 phases + scènes |
| `PlageAnimeeV2.ora` | 36 calques (f0 visibles) |
| `apercu_plage_animee_v2.html` (racine) | Viewer : lecture/pause, phases, calques, grille |

456×480, grille 8 px (57×60). Corridor sud V1 inchangé (masques).
Indicatif : pas de collisions, warps ni test PMDO.

## Limites

- LUT0 = dégradé échantillonné (p2→p98) : la frame 0 lisse la texture
  (médiane par case s'effondrait sur cet art quasi deux tons).
- Bandes de dérive 8 px visibles dans l'eau : porteuses du mouvement,
  style cycling assumé.
- Aucune validation artistique. V1 et référence inchangées.

## Reproduction

```sh
.venv/bin/python source/plage_animee_v2/build.py
.venv/bin/python source/plage_animee_v2/package.py  # tests + ZIP
.venv/bin/python -m unittest source.plage_animee_v2.test_build -v
```
