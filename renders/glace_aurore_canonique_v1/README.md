# V17 — Glace & Aurore canoniques, sud → nord, PNG 8 px

Relayouts aux **pixels natifs exacts** (aucun pixel IA, aucune recoloration /
miroir / rotation / echelle sur les couches fixes), composition guidee par le
layout sud-nord existant (`source/ice_arena_aurora_v1/generation/layout_guide.png`).
Trois references : `aurorepmdsky.png`, `pmdskyicearena.png`, `iceroadpmdsky.png`.

## Contenu

| Map | Taille | Couches fixes | Animation (NOUVELLE) |
|---|---|---|---|
| `bg_aurore` | 264×216 | 01 ciel+nuages, 02 etoiles, 04 frise glace | 03 aurore 10f×160ms (onde verticale pure, boucle exacte) ; etoiles 4f×200ms (alpha seule) |
| `arene_glace` | 504×408 | 01 sol neige, 02 mur nord, 03 blocs cotes, 04 crete sud (ouverture), 05 fissures | 06 reflets 4f×150ms (pulse ±5%, boucle A-B-A-C) |
| `route_glacee` | 504×360 | 01 fond montagnes, 02 lac gele, 03 parois nord (defile), 04 blocs sud (ouverture), 05 fissures | 06 reflets 4f×150ms |

- Coupes organiques calculees (suivent les crevasses sombres, sans fondu) pour
  les ouvertures sud, le defile nord et les pieds de parois.
- Sols/lac paves par patches natifs, joints par cout minimal, sans fondu.
- Chaque couche : PNG transparent + `*_source.npz` (coordonnees source par pixel)
  + `.tsx` descriptif 8 px. Chemins sud→nord/centre verifies degages (pixels
  uniquement, pas une collision moteur).
- Ciel du BG : trous rubans/etoiles combles par plus proche voisin natif ;
  la frise reste transparente derriere les pics (aucun ciel invente).

## Import PNG to Tileset (8 px)

Toutes les dimensions sont multiples de 8. Utiliser `GLACE_V17_png_import_8px.zip`
(noms uniques, a plat) : importer chaque couche en **8 px**, empiler dans l'ordre
numerique, poser les frames animees en overlay au-dessus (cadences ci-dessus).
Ne pas confondre avec la route DTEF 24 px (autotiles donjon, autre lot).

## Limites honnetes

- Animations creees pour ce lot (onde, scintillement, reflets) : **pas des
  cycles officiels recuperes**. L'extraction et la cadence sont nos choix.
- Reflets : modulation logicielle ±5% des RGB d'origine sur masque de pixels
  clairs froids ; pas un shader moteur.
- Sols caches sous les reliefs : paves natifs ; faces cachees des parois non
  reconstruites pour des mouvements arbitraires.
- 13 tests locaux PASS (`source/glace_aurore_canonique_v1/test_build.py`).
  **Pas de test navigateur interactif, pas d'import/runtime PMDO, art non approuve.**

Rebuild : `.venv/bin/python source/glace_aurore_canonique_v1/build.py`
puis `test` + `package.py`.
