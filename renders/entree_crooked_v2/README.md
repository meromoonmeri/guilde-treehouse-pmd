# Entrée grotte v2 — 8 calques générés recalés 1:1 (maquette v1)

Carte 848×1264 sud→nord : bouche (417, 496) devant parvis sableux, chemin en S,
prairie, 4 arbres, rochers au pied de paroi + galets au seuil, 26 touffes de
fleurs statiques.

## Généré (renvoi visuel, pixels régénérés)

6 bruts (`source/entree_crooked_v2/bruts/`, 0 rejet) : G_sol, G_chemin, G_paroi
(848×1264) ; G_rochers, G_fleurs (896×1200) ; G_arbres (768×1376). Refs
canoniques Crooked/Halcyon/Sky Peak en guides, maquette = composite v1.
Recalage par translations seules (snap 8), jamais de resampling : bouche =
référence, chemin dx=+40, rochers par composante, arbres recentrés (+40, −56).

## Règles (détails : `manifest.json → details`)

Magenta cuit purgé en global + frange b>g (chair rose protégée) ; bouche
lum<110 ; paroi = détouré − bouche ; split troncs/canopées par règle vert ;
fleurs filtrées sur prairie (≥12px, ≤15% hors-prairie).

## Fichiers

`EntreeCrookedV2_<calque>_<jour|nuit>.png` (origine commune),
`composite_{jour,nuit}.png`, `entreecrookedv2.ora`, `manifest.json`,
`verification.json` (48 PASS).
Galerie : `apercu_entree_crooked_v2.html` (calques, jour/nuit).

Nuit = Abyss exact, une fois par calque. Entrée (417, 657) sur chemin. Fleurs
statiques : pack v1 natif animé conservé (`renders/entree_crooked_v1/`).
**PMDO non testé, art non approuvé.**

Reconstruction : `source/entree_crooked_v2/{build,verify,make_gallery}.py`.
Méthode et audit : `source/entree_crooked_v1/AUDIT.md` §5.
