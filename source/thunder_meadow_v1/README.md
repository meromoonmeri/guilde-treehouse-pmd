# Thunder Meadow — layout multicalque V1

Référence : `5394.png` (commit f1923699, rip Toastypk, spriters-resource asset 5394) : carte sans éclairs, « Cloud flash colors » (8 couleurs × 6 niveaux Dark→Light) et frames d'éclairs. `Rescue_Team_Friend_Area_-_Thunder_Meadow.png` sert seulement de contrôle visuel (couleurs converties ×8,25 et éclairs incrustés : non utilisée comme matière).

## Layout (légèrement différent)
- Arbre déplacé de 72 px à gauche et 8 px plus bas ; son ancien emplacement est comblé avec le sol natif pris 88 px à droite (ellipse), les pointes de branches par le sol voisin.
- Gros rochers remontés de 8 px et rapprochés du centre de 24 px ; petits rochers, fissure et îlots inchangés.
- Canevas 456×336 (dernière ligne native dupliquée pour la grille 8 px). 0 couleur hors planche sur tous les calques.

## Calques
`00_nuages` (animé, palette flash) · `01_eclairs` (animé) · `02_terrain` · `03_details` (arbre + rochers)

- **Nuages** : les 8 couleurs de la rangée Dark sont remplacées une à une par celles des niveaux 1 à 5 → 6 PNG `nuages_flash/…flash0-5.png`. Méthode de la référence : on change la palette, sans aucun mouvement.
- **Éclairs** : frames de la planche : rangées A/B (6 fissures + 6 éclairs qui grandissent), C/D (4 + 4), E/F (4 fissures seules). Rangées B/D/F en miroir côté droit. L'éclair est accroché au point le plus bas de la fissure : c'est une interprétation.
- **Timeline** (`manifest.json`) : 40 frames sur 7,7 s. Chaque frame associe une image d'éclair et le niveau de flash des nuages (1-3-5-5-3-1 pour un éclair de 6 frames). Les 67 ms par frame et les pauses de 900 ms sont un choix, pas la cadence GBA d'origine.

## Limites
Les collisions 8 px sont indicatives et n'ont pas été testées en jeu. Aucun test moteur. Petits raccords de texture possibles à l'ancien emplacement de l'arbre.
Reconstruction : `.venv/bin/python source/thunder_meadow_v1/build.py`
