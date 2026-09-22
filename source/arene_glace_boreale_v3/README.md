# IA3 — arène de glace : nouveau layout généré, bordure immersive, chemin, aurore animée générée, montagnes lointaines (22 septembre 2026)

Demande : générer les multicalques puis les assembler ; puis correction : **aurore canonique, plus petite, légère ondulation seulement** ; nouveau layout avec **bordure immersive** de stalactites, **entrée/chemin** vers l'arène, **ciel aurore animé** et **chaîne de montagnes ultra lointaine**.

Scène 480×816 (ciel 176 px + arène 480×640), grille 8 px, 7 calques.

## Calques (ordre d'empilement) — tout est GÉNÉRÉ sauf mention
1. `IA3_00_ciel_nuit` — gradient reconstitué depuis les lignes sombres natives d'`aurorepmdsky.png`, quantifié palette native.
2. `IA3_01_etoiles` — **points natifs 1×**.
3. `aurore/IA3_aurore_00..11` — **rubans CANONIQUES 1×** d'`aurorepmdsky.png` (lignes 0–119, extraction V10 sans ciel ni étoiles, fondu bas 12 px), bande réduite et discrète (< 35 % du ciel). **Ondulation légère** : décalage horizontal par ligne ≤ 3 px (`2·sin(2π(y/120 − t/12)) + 1·sin(2π(2y/120 − t/12) + 0,5)`), 12 × 8 ticks = 1,6 s, boucle exacte, **aucun cycle de couleur**. Correction utilisateur : la planche générée 8 frames mouvement+couleurs (`aurore_planche_B`) était trop grosse et non canonique → archivée, non utilisée.
4. `IA3_02_montagnes_lointaines` — bande de sommets lointains générée, palette native glace, base cachée sous la crête de la bordure.
5. `IA3_03_sol_chemin_arene` — sol continu opaque : chemin depuis le sud vers l'arène circulaire polie.
6. `IA3_04_stalactites_arriere` / 7. `IA3_05_stalactites_avant` — bordure fermée N/E/O avec ouverture sud et pics sentinelles, coupée à mi-hauteur pour l'occlusion (le joueur passe devant la moitié haute, derrière la moitié basse).

## Vérifications
Palette native respectée sur les plans glace ; aurore = couleurs natives, 12 frames, ondulation ≤ 3 px/ligne vérifiée ligne par ligne, boucle exacte ; sol opaque ; bordure fermée sur 3 côtés ; entrée sud reliée au centre de l'arène (érosion 17 px) ; Ground `vp1_ia3_arene_glace_boreale` relu exactement (ticks 0/40/95/96), installeur testé. **PMDO non exécuté, pas d'approbation artistique.** Les générations ne sont pas des pixels canoniques ; 9 bruts archivés (4 retenus, 1 planche rejetée, 4 plans supplantés) dans `raws/index.json`.

## Livrables (`renders/arene_glace_boreale_v3/`)
`IA3_arene.png`, `IA3_arene_animee.webp`, `IA3_calques.png`, `IA3_aurore_12_frames.png`, `IA3_viewport_320x240.png`, `IA3_arene_glace_boreale_calques.zip`, `IA3_arene_glace_boreale_PMDO.zip`.
Reproduction : `.venv/bin/python source/arene_glace_boreale_v3/work.py --build --verify --pmdo`.
