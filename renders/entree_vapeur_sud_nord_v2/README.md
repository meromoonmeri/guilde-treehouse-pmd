# ESN2 — Entrée Vapeur sud → nord, V2

Demande : « pour l'animation d'eau fait quelque chose comme metano town river ! et fait des animation bulle genere les cohérente a l'eau qui éclate car c'est un peu marécageux ».

- Aperçu : `apercu_entree_vapeur_sud_nord_v2.html` à la racine, ou `review/ESN2_scene_animee.webp`.
- Pack PMDO 0.8.12 : `ESN2_projet_pmdo_0812.zip` (mode d'emploi dans `README.md` du pack).
- Calques PNG 8 px pour PNG to Tileset : `ESN2_calques_png_8px.zip`. Tous les noms sont préfixés `ESN2_`.
- Script : `source/entree_vapeur_sud_nord_v2/build.py`, puis `package.py`. 9 tests : `test_build.py`.

## Ce qui change par rapport à la V1

| | V1 | V2 |
|---|---|---|
| Eau | palette cycling générée, 12 × 10 ticks | structure rivière Métano : aplat, bande sombre de 4 px, 1 px intermédiaire, frange dentelée, lèvre claire ; 4 × 10 ticks |
| Ombres de berge | calque translucide | retiré (la bande Métano le remplace) |
| Scintillements | — | 8 amas, pixels `Metano_Town_River_Sparkles` recolorés, 4 × 10 ticks, synchrones comme à Métano |
| Bulles | — | 9 émetteurs générés, décalés, 24 × 5 ticks |
| Terrain | — | identique (7 calques V1 relus, vérifiés égaux au pixel) |

## Cycle d'une bulle (24 phases de 5 ticks)

point ×2 → petite ×2 → ronde ×2 → dôme ×3 → tension (gouttelettes) ×2 → éclatement ×2 → anneaux ×2 → anneau final ×2, puis 7 phases de repos.
Transition dernière → première : la phase 23 est au repos pour un émetteur non décalé, et la phase 0 démarre au point. Les décalages (0, 7, 14, 21, 4, 11, 18, 1, 8) font qu'au moins une bulle est visible à chaque phase (testé).

## Honnêteté des sources

- **Eau** : la cadence (FrameLength 10, 4 phases) a été vérifiée dans `source/eau_metano/animations_carte.json` (Halcyon, da6c2130). Le profil de bande a été mesuré sur les 4 feuilles Métano (valeurs dans le manifeste). Les pixels sont recalculés : **pas des tuiles Métano natives**.
- **Scintillements** : pixels Métano réels, couleurs transposées, positions nouvelles. La famille 16×32 n'a pas trouvé de place.
- **Bulles** : `bruts/bulles_8_poses.png` a été généré. Il a été reçu en 2 × 6 cases au lieu de 1 × 8, avec des doublons, et le disque sombre a été écarté. La pose tension a été recomposée (dôme + gouttelettes), les anneaux recolorés, et l'anneau final dérivé. Toutes les poses ont été réduites de façon uniforme (×0,1).
- Aucun test PMDO en jeu. Art non validé.
