# IA3 — arène de glace : nouveau layout généré, bordure immersive, chemin, aurore animée générée, montagnes lointaines (22 septembre 2026)

Demande : générer les multicalques puis les assembler ; l'aurore doit avoir **toutes ses frames de mouvement et de changement de couleur** ; nouveau layout avec **bordure immersive** de stalactites, **entrée/chemin** vers l'arène, **ciel aurore animé** et **chaîne de montagnes ultra lointaine**.

Scène 480×816 (ciel 176 px + arène 480×640), grille 8 px, 7 calques.

## Calques (ordre d'empilement) — tout est GÉNÉRÉ sauf mention
1. `IA3_00_ciel_nuit` — gradient reconstitué depuis les lignes sombres natives d'`aurorepmdsky.png`, quantifié palette native.
2. `IA3_01_etoiles` — **points natifs 1×** (seul calque à pixels natifs).
3. `aurore/IA3_aurore_00..07` — **8 frames générées** en une planche 4×2 d'après la référence : les rubans ondulent ET la couleur cycle magenta → violet → cyan/vert → turquoise → retour vers magenta. Détourage par inondation du fond #FF00FF (le magenta des rubans est conservé), quantification dans les couleurs natives d'`aurorepmdsky.png`, fondu bas 16 px. 8 × 8 ticks = 64 ticks (1,07 s). Le bouclage 8→1 est une continuité approximative (testée sur la teinte moyenne), pas une identité pixel.
4. `IA3_02_montagnes_lointaines` — bande de sommets lointains générée, palette native glace, base cachée sous la crête de la bordure.
5. `IA3_03_sol_chemin_arene` — sol continu opaque : chemin depuis le sud vers l'arène circulaire polie.
6. `IA3_04_stalactites_arriere` / 7. `IA3_05_stalactites_avant` — bordure fermée N/E/O avec ouverture sud et pics sentinelles, coupée à mi-hauteur pour l'occlusion (le joueur passe devant la moitié haute, derrière la moitié basse).

## Vérifications
Palette native respectée sur tous les plans glace/aurore ; 8 frames distinctes, cycle de couleur réel, retour vers la frame 0 ; sol opaque ; bordure fermée sur 3 côtés ; entrée sud reliée au centre de l'arène (érosion 17 px) ; Ground `vp1_ia3_arene_glace_boreale` relu exactement (ticks 0/20/63/64), installeur testé. **PMDO non exécuté, pas d'approbation artistique.** Les générations ne sont pas des pixels canoniques ; 9 bruts archivés (4 retenus, 1 planche rejetée, 4 plans supplantés) dans `raws/index.json`.

## Livrables (`renders/arene_glace_boreale_v3/`)
`IA3_arene.png`, `IA3_arene_animee.webp`, `IA3_calques.png`, `IA3_aurore_8_frames.png`, `IA3_viewport_320x240.png`, `IA3_arene_glace_boreale_calques.zip`, `IA3_arene_glace_boreale_PMDO.zip`.
Reproduction : `.venv/bin/python source/arene_glace_boreale_v3/work.py --build --verify --pmdo`.
