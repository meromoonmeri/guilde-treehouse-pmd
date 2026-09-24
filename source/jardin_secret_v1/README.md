# Jardin secret v1 — sources

Reconstruction complète : `../../.venv/bin/python segment.py && ../../.venv/bin/python build_ground.py && ../../.venv/bin/python export.py`
(environ 3 min ; Pillow, NumPy, SciPy). Sorties dans `renders/jardin_secret_v1/`, galerie `apercu_jardin_secret_v1.html`.

| Fichier | Rôle |
|---|---|
| `segment.py` | Détoure les objets de `secretgarden.png` par priorité (fleurs → rochers → souche → arbres → rayon ; halo du rayon = verts à b ≥ 55, feuillage = b 31), mesure les classes du sol (V sous-bois / L pelouse / C tapis) et le ton du tapis en 4 bandes. Sorties : `segmentation/` (sprites RGBA exacts + `sprites.json` avec origine). |
| `layout.py` | Plan 816 × 1152 : axes du tapis et de la pelouse paramétrés en y, bords bruités, alcôves, ton en escalier ; caractéristiques de guidage (distances signées aux bords, distances « depuis le bord nord », ton). |
| `quilt.py` | Moteur de synthèse guidée (quilting + texture transfer) : coût FFT (raccord + plan), pénalité de réutilisation, coupe minimale, pixels imposés jamais réécrits, carte de provenance `src` (y, x). |
| `build_ground.py` | Sol : module d'origine (rayon/souche/prairie) imposé à +204 px, le reste synthétisé ; sol caché sous les objets reconstitué. Exclusions : objets, restes d'ombres, rayon + halo. |
| `compose.py` | Placements (objets du module à l'identique, arbres/rochers recalés sur la pelouse, bouquets de fleurs), séparation troncs/cimes, feuillage d'avant-plan synthétisé depuis la frange sombre. |
| `export.py` | Calques jour/nuit, compositions, ORA, provenance, manifeste, `verification.json`. |

Règles de spriter appliquées : la référence n'a **aucun bord de pelouse orienté sud** ni de fin de tapis au sud, donc le plan « coule » vers l'entrée sud et les fermetures sud des alcôves sont placées sous le feuillage d'avant-plan. Pas de miroir, rotation, recoloration ou changement d'échelle.
