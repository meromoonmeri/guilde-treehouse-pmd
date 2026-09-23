# Reference sampler — configuration stricte du generateur

Echantillonne une reference canonique (outils, pas a l'oeil) et produit un pack
qui verrouille le generateur : palette hex, planche de patchs, mesures, prompt.

## Usage

```sh
.venv/bin/python source/reference_sampler/sample.py <REF> source/reference_sampler/packs/<nom> \
  --title "..." --layout "..."
.venv/bin/python -m unittest source.reference_sampler.test_sampler -v
```

## Pack genere

- `palette.png` : couleurs triees par frequence + hex + %.
- `patch_board.png` + `patch_*.png` : extraits originaux par couleur (rects en `samples.json`).
- `samples.json` : hex, comptes, rects sources, note d'echelle.
- `prompt.txt` : prompt strict (a compacter a ≤10 hex si MAX_TOKENS).

## Appel generateur contraint

`images=[reference, patch_board]` + prompt compact :
palette verrouillee, grain des patchs, echelle PMDO 8px, magenta #FF00FF, sans ciel.

## Preuve aride (23 septembre 2026)

`proof/aride_strict_v1.png` : **95,4 % des pixels a Δ≤30** de la palette verrouillee
(19 couleurs), 99,2 % a Δ≤60. Le generateur respecte le verrou aux melanges
anti-aliasing pres ; un remap optionnel vers la palette peut etre applique au build.
Layouts inferieurs : prompt long (16 hex) + 2 refs = MAX_TOKENS → compacter a 10 hex.
