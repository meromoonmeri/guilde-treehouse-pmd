# Sky Peak — prairie du sommet, nuit — V4 (corrections sur V3)

Corrections demandées : **garder le layout de base (V3)** et uniquement
1. **prolonger la paroi rocheuse** jusqu'en bas du cadre pour ne plus avoir l'impression d'une « île dans le ciel » ;
2. **améliorer le ciel** (plus profond, plus lumineux à l'horizon) et mettre des **nuages variés**, avec la **lune bien visible dans le cadre**.

Galerie : `index.html` (servir par HTTP) — calques commutables, mode Nuit Abyss, nuages/brume animés.

## Ce qui change par rapport à V3
| Élément | V3 | V4 |
|---|---|---|
| Paroi rocheuse | largeur 144–815, bords libres → panorama visible en bas des flancs | **prolongée sur les flancs (x<179, x>780)** jusqu'aux coins du cadre ; centre rigoureusement inchangé |
| Ciel | dégradé 5 paliers | **dégradé 6 paliers** (indigo nuit → lueur cyan crème à l'horizon), lueur lunaire renforcée |
| Nuages | 2 bandes (lointain + overlay), formes répétées | **6 formes variées** (bande, cumulus, voile, tour, traîne, duo) sur bande lointaine + overlay + **3 accents fixes** (`04b_nuages_accents`) |
| Lune | haut droite (716–844, 48–176) | identique (réutilisée), **libérée de tout nuage** |
| Brume | 3 bandes (505/625/755) | 3 bandes conservées + **brume avant** (`08b_brume_avant`, y=770) sur le pied de la paroi |

## Calques 960 × 864, tous en (0,0)
01 ciel profond (dessiné) · 02 étoiles (réutilisé V3) · 02b filantes (réutilisé V3) · 03 lune (réutilisée V3) · 04 nuages lointains (6 formes) · 04b accents de nuages · 05 panorama · 05b brume overlay · 06 nuages overlay · 07 plateau herbe · 08 paroi rocheuse (prolongée) · 08b brume avant.

## Méthode & limites
- **Layout de base conservé** : étoiles (64 phases), filantes (360 phases), panorama, les 3 bandes de brume, plateau et centre de la paroi sont repris de V3 **à l'identique** (copie de pixels, non régénérés).
- La paroi est prolongée sur les flancs par **continuation des strates natives** : chaque colonne manquante est remplie en répétant verticalement la colonne rocheuse d'origine (denses, vert filtré) la plus proche, avec décalage par colonne pour éviter le motif, ombre de pied progressive et liseré sombre sur le haut de la zone élargie. **Aucun collage étranger, aucune recoloration** — même palette que la paroi d'origine.
- Les nuages V4 sont **dessinés par l'IA** (`gen_v4/raw_nuages_varies.png`), découpés sur fond magenta, assombris en nuit (formule Guilde/Sharpedo, pas Abyss). Le ciel V4 est un dégradé dessiné par le script (couleurs relevées sur le brut IA `raw_ciel_nuages.png`).
- Art IA déclaré ; aucun pixel natif certifié ; aucun test PMDO.

## Vérification
`source/sky_peak_prairie_v1/verify_v4.py` — re-génère et contrôle : centre de la paroi identique au V3, flancs couverts jusqu'aux coins, ciel lisse sans motifs parasites, lune / étoiles épargnées, 6 blocs de nuages distincts, ORA re-composable à la composition.

Reproduction : `.venv/bin/python source/sky_peak_prairie_v1/build_v4.py` puis `verify_v4.py`.
