# Falaises proches Métano V3 — générées texture native

Deux variantes 768×512 (cap gauche, terrasse droite) **générées au générateur
d'images sur fond magenta**, guidées par les terrains natifs V2 et la référence
canonique Métano. Commun réutilisé de la V2 à l'octet (ciels, mer 64 phases,
nuages COTEV2 2200px). Nuit Abyss exacte, 1 passe.

## Audit texture (vs `reference_canonique.png`, 20000 px)

| Variante | ≤30 niveaux RGB | Couleurs exactes |
|---|---|---|
| Cap gauche | **99,9%** | 0,71% |
| Terrasse droite | **99,9%** | 0,07% |

(V1 guidée simple : 80,6 / 85,9%, 0% exactes. V2 : 100% pixels natifs par
reconstruction. V3 = le générateur seul, guidé natif.)

## Méthode

`layouts/` (1376×768, magenta) → cover-crop NEAREST 768×512 (gravité
left/right) → détourage magenta → nuit `night.py` → compositions
(ciel + nuages y=8 offset 1289 + mer phase 00 + falaise).

## Contenu

- `layouts/` : 2 bruts générés.
- `commun/` : copies V2 (01–06 + `ocean/` 128 phases P + palettes).
- `cap_gauche/`, `terrasse_droite/` : `07_falaise`, `08_falaise_nuit`,
  compositions jour/nuit.
- `manifest.json` (audit inclus), `verification.json` (20 contrôles PASS),
  `PLANCHE.png`.
- Aperçu : `apercu_falaises_proches_metano_v3.html` (calques, jour/nuit, mer
  64 phases, wrap animé 12px/s, export PNG).
