# Entrée aride — map générée V1

Map assemblée depuis **5 bruts générateur** guidés par la référence canonique
`entrancearidedungeonpmdsky.png` (entrée de donjon aride PMD Sky).
Méthode rendus générés (magenta → détourage → calques → assemblage),
**pas** un assemblage de morceaux de map.

## Contenu

- `L00_sol.png` — sable plein cadre 408×288 (cadre magenta rebouché par dilatation du sable vrai, G-B > 15)
- `L01_parois.png` — parois + trou de la bouche (transparent)
- `L03_bouche.png` — intérieur de la bouche (187,46–224,89)
- `L02_props.png` — 4 arbres morts + 2 blocs replacés (`props/*.png` : sprites individuels)
- `fx/frame_00..11.png` — poussière : 3 voiles (alpha 150) + 4 grains, 12×100 ms, boucle parfaite
- `fx/voile*.png`, `fx/grain_*.png` — sprites FX
- `composite.png` — assemblage statique exact L00+L01+L03+L02
- `scene_animee.gif` / `scene_animee.webp` — 12 frames, boucle infinie
- `aride_generee_v1.ora` — OpenRaster multicouche éditable
- `manifest.json` — SHA des bruts, bbox bouche, placements
- `verification.json` — résumé des contrôles

Galerie : `apercu_aride_generee_v1.html` (racine) — calques activables,
lecture/pause FX, curseur de frame, comparatif canonique/brut.
Pack : `renders/aride_generee_v1_pack.zip`.

## Honnêteté du lot

- Textures **reproduites au générateur** depuis la référence canonique,
  détourées et nettoyées (0 pixel rose opaque, RGB zéro sous alpha 0).
  Ce ne sont **pas** des pixels natifs extraits du jeu.
- Animation poussière **proposée** (translations sinusoïdales pures,
  RGB exacts des sprites, boucle testée frame par frame),
  pas un cycle officiel récupéré.
- Chemin sud (205,282) → bouche (205,100) vérifié connecté par flood-fill ;
  corridor ≥ 24 px. Cela ne prouve ni collisions ni warps moteur.
- 10 tests PASS (`source/aride_generee_v1/test_build.py`).
  Pas de test PMDO/GPU, pas de collisions moteur.

## Reproduction

```sh
.venv/bin/python source/aride_generee_v1/build.py
(cd source/aride_generee_v1 && ../../.venv/bin/python fx.py)
.venv/bin/python source/aride_generee_v1/package.py
```
