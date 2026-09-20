# source/plage_rouge_v1 — pipeline du lot

| Fichier | Rôle |
|---|---|
| `build.py` | bruts → calques → quantification palette → scènes/GIF/WebP/ORA/viewer/manifeste |
| `viewer_template.html` | gabarit de `apercu_plage_rouge_v1.html` (calques, lecture, sèche, grille, zoom, export) |
| `test_build.py` | 19 tests : recomposition, palette 147, magenta, invariance terrain, ORA, GIF/WebP, hashes |
| `package.py` | ZIP `renders/plage_rouge_v1_pack.zip` |
| `make_prompts.md` | provenance exacte des 4 générations (prompts et références) |

Commandes : `.venv/bin/python source/plage_rouge_v1/build.py && .venv/bin/python source/plage_rouge_v1/test_build.py && .venv/bin/python source/plage_rouge_v1/package.py`

Dépendances : pillow, numpy, scipy (dans `.venv`, recréée après reset sandbox).
