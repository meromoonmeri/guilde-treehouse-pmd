# IA3 — arène de glace : nouveau layout généré, bordure immersive, chemin, aurore animée générée, montagnes lointaines (22 septembre 2026)

Demande : générer les multicalques puis les assembler ; puis : **aurore générée au design canonique, à la taille du ciel, 20 frames d'ondulation** ; nouveau layout avec **bordure immersive** de stalactites, **entrée/chemin** vers l'arène, **ciel aurore animé** et **chaîne de montagnes ultra lointaine**.

Scène 480×816 (ciel 176 px + arène 480×640), grille 8 px, 7 calques.

## Calques (ordre d'empilement) — tout est GÉNÉRÉ sauf mention
1. `IA3_00_ciel_nuit` — gradient reconstitué depuis les lignes sombres natives d'`aurorepmdsky.png`, quantifié palette native.
2. `IA3_01_etoiles` — **points natifs 1×**.
3. `aurore/IA3_aurore_00..19` — **20 frames GÉNÉRÉES au design canonique** (rubans courbes, cœur magenta, franges cyan, rayons dithérés, d'après `aurorepmdsky.png`), une nappe fine + fragment, **à la taille du ciel** (cellule 564×181 → 480×154, ≤ 40 % du ciel). Deux planches de 10 cellules ; 17 cellules continues retenues (ondulation douce de la courbe et des franges + pulsation rose-violet du cœur), 3 cellules hors composition écartées ; boucle de 20 = aller 17 + retour 3 pour fermer sans saut (IoU > 0,6 entre frames consécutives, testé, y compris 19→0). 20 × 5 ticks = 1,67 s. Quantifiée dans les couleurs natives. Historique : planche 8 frames « mouvement+couleurs » rejetée (trop grosse), puis rubans natifs 1× à ondulation ±3 px (version précédente, dépassée par cette demande).
4. `IA3_02_montagnes_lointaines` — bande de sommets lointains générée, palette native glace, base cachée sous la crête de la bordure.
5. `IA3_03_sol_chemin_arene` — sol continu opaque : chemin depuis le sud vers l'arène circulaire polie.
6. `IA3_04_stalactites_arriere` / 7. `IA3_05_stalactites_avant` — bordure fermée N/E/O avec ouverture sud et pics sentinelles, coupée à mi-hauteur pour l'occlusion (le joueur passe devant la moitié haute, derrière la moitié basse).

## Vérifications
Palette native respectée sur les plans glace ; aurore = 20 frames, couleurs natives, continuité IoU > 0,6 frame à frame et 19→0 ; sol opaque ; bordure fermée sur 3 côtés ; entrée sud reliée au centre de l'arène (érosion 17 px) ; Ground `vp1_ia3_arene_glace_boreale` relu exactement (ticks 0/37/99/100), installeur testé. **PMDO non exécuté, pas d'approbation artistique.** Les générations ne sont pas des pixels canoniques ; 9 bruts archivés (4 retenus, 1 planche rejetée, 4 plans supplantés) dans `raws/index.json`.

## Livrables (`renders/arene_glace_boreale_v3/`)
`IA3_arene.png`, `IA3_arene_animee.webp`, `IA3_calques.png`, `IA3_aurore_20_frames.png`, `IA3_viewport_320x240.png`, `IA3_arene_glace_boreale_calques.zip`, `IA3_arene_glace_boreale_PMDO.zip`.
Reproduction : `.venv/bin/python source/arene_glace_boreale_v3/work.py --build --verify --pmdo`.
