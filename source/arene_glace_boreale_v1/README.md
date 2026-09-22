# IA2 — arène de glace canonique + aurore boréale canonique en frames verticales (22 septembre 2026)

Scène 504×600, grille 8 px, six calques ordonnés, aurore sur son propre calque animé.

## Calques (ordre d'empilement)
1. `IA2_00_ciel_nuit` — champ nocturne reconstitué à partir des médianes natives par ligne d'`aurorepmdsky.png` (hors rubans/étoiles). **Pas une image source inchangée.**
2. `IA2_01_etoiles` — points natifs 1× d'`aurorepmdsky.png`.
3. `aurore/IA2_aurore_00..11` — **rubans canoniques 1×** extraits d'`aurorepmdsky.png` (règles V10 : luminosité+saturation, ciel sombre/étoiles/nuages exclus). **Onde verticale** : chaque ligne est décalée horizontalement de `4·sin(2π(y/144 − t/12)) + 2·sin(2π(3y/144 − t/12) + 0,7)`, la phase descend le long des rideaux ; 12 frames × 6 ticks = 72 ticks (1,2 s), frame 12 ≡ frame 0 (testé). Couleurs des frames ⊆ couleurs natives des rubans (testé). Tuile native en x 0–263, copie miroir en x 264–503 : adaptation de raccord, non native.
4. `IA2_02_sol_glace_continu` — lignes natives 248–279 de `pmdskyicearena.png` répétées : sol opaque continu sous les glaces, à partir de la ligne 40 de l'arène.
5. `IA2_03_glace_arriere` — lignes natives 0–247, pixels 1× inchangés, ciel de jour (55,175,215) et brume d'horizon (l. 28–39) retirés.
6. `IA2_04_glace_avant` — lignes natives 280–407, 1× inchangées, descendues de 96 px pour agrandir l'aire (adaptation de layout).

## Ce qui n'est pas canonique
La cadence et la loi d'ondulation sont nos choix : le cycle officiel du BG n'a jamais été retrouvé (voir `source/ice_arena_aurora_v1/references/`). La glace est le décor de jour placé sous un ciel nocturne : choix de composition. Aucune recoloration, rotation ni redimensionnement des natifs.

## Livrables (`renders/arene_glace_boreale_v1/`)
`IA2_arene.png`, `IA2_arene_animee.webp` (boucle 1,2 s), `IA2_calques.png` (planche), `IA2_aurore_12_frames.png`, `IA2_viewport_320x240.png`, `IA2_arene_glace_boreale_calques.zip` (PNG alignés + manifeste), `IA2_arene_glace_boreale_PMDO.zip` (Ground `vp1_ia2_arene_glace_boreale`, `.tile` 8 px, aurore en piste 12 frames × 6 ticks, INSTALLER.py).

Reproduction : `.venv/bin/python source/arene_glace_boreale_v1/work.py --build --verify --pmdo`. Tests images + relecture Ground exacte (ticks 0/30/66/72) + installeur ; **PMDO non exécuté**, collisions libres, pas d'approbation artistique.
