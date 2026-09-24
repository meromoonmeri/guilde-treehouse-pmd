# Falaises proches Métano — mer, ciel jour/nuit, nuages en wrap (V1)

Galerie autonome : **`apercu_falaises_proches_metano_v1.html`** à la racine (jour/nuit, calques, wrap animé, vitesse, export). [Planche jour/nuit](PLANCHE.png).

## Variantes (768×512, falaises proches caméra)

| Variante | Cadrage |
|---|---|
| Cap gauche | Falaise à gauche, mer/ciel ouverts à droite |
| Terrasse droite | Falaise en paliers à droite, mer/ciel ouverts à gauche |

## Méthode : layouts générés séparés

Comme le réseau jardin : un layout généré par élément, assemblés par script.

- `layouts/falaise_cap_gauche.png`, `layouts/falaise_terrasse_droite.png` : falaises sur magenta, matière guidée par `source/falaises_generees/reference_canonique.png` + pose Cap V3.
- `layouts/mer.png` : mer plein cadre (bande utile y 300–512).
- `layouts/ciel_jour.png` : dégradé jour sans nuages ; `layouts/ciel_nuit.png` : nuit étoilée.
- `layouts/nuages_wrap.png` : famille de 7 nuages sur magenta, rendue périodique par fondu (période 630px).

Normalisation uniforme cover-crop (recadrage côté magenta pour les falaises), **jamais anisotrope**. Détourage magenta, zéro résidu vérifié.

## Calques et nuit

Communs : `01_ciel_jour`, `02_ciel_nuit`, `03_mer_jour`, `04_mer_nuit`, `05/06_nuages_wrap_jour/nuit`. Par variante : `07_falaise`, `08_falaise_nuit`. Ordre : ciel, nuages, mer, falaise (la falaise proche passe devant).

Nuit = **filtre Abyss exact** (`source/cote_v4_abyss/night.py`), une seule passe, sur mer/nuages/falaises. Le ciel nuit est un layout généré à part (étoiles).

## Wrap et audit

Nuages : période 630px, 30px/s réglable, tuilage avec recouvrement — boucle mathématiquement parfaite, continuité de raccord 0,22. La mer est fixe dans ce lot (pas de cycle de vagues).

Audit Métano vs référence canonique : cap 80,6 %, terrasse 85,9 % des pixels à ≤30 en RGB (0 % byte-exacts : **générations guidées, pas des tuiles natives certifiées**).

## Vérifications et reproduction

`verification.json` : SHA-256, dimensions, nuit exacte, wrap, recompositions jour/nuit exactes, audit. Scripts : `source/falaises_proches_metano_v1/{build,verify,gallery}.py` (Pillow, numpy). **Pas de validation PMDO.**
