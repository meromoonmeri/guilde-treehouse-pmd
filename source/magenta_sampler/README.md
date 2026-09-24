# Echantillonneur magenta — configuration stricte du generateur

Outil : `sample.py` (aucun effet a l'import). Echantillonne chaque reference par
materiau (effectif, couverture, top12, mediane, HSV p10-p90, grain, dither) et produit :
`configs/<ref>_config.json`, `<ref>_palette.png`, `<ref>_contraintes.txt` (hex + stats
a injecter dans les prompts), `<ref>_audit_bruts.json` (bruts generes vs echantillons,
memes regles des deux cotes).

```sh
.venv/bin/python source/magenta_sampler/sample.py
```

## Resultats V2 (jungle + Southern Jungle)

- Southern Jungle = **ZERO marron** (0 px r>g+15, r>70 sur 3 refs) : troncs verts
  sombres uniquement. Les troncs marron generes V2 sont un ecart DA documente ;
  les prochains prompts arbres imposent des troncs verts.
- `terrain_strict.png` vs jungle : eau/falaise/herbe a 77/47/46 de distance mediane
  (tons generes plus sombres), chutes trop pales (captees par `ecume`, 16% vs 7.6%).

## Boucle sample → generate → audit (sol)

Sol regenere avec hex echantillonnes (`bruts/sol_jungle_echantillonne.png`) :
herbe 26.1 / chemin 24.7, contre **8.6** / 28.2 pour l'ancien sol. Le nouveau brut
(taches douces, moins pixel-net) est **rejete sur audit** et conserve comme tel ;
le sol V2 actuel est garde. Le sampler sert donc d'arbitre chiffre, pas seulement
de prompt : un brut qui n'ameliore pas les distances ne remplace pas l'existant.
