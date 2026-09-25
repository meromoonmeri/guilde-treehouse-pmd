# Mt. Thunder — arène orageuse multicalque V1

Référence : `reference_mt_thunder.png` (PMD Rouge, salle du boss Mt. Thunder, planche avec éclairs 1-4, Flash, palettes Normal/Fading). SHA-256 dans `renders/mt_thunder_orage_v1/manifest.json`.

## Layout (légèrement différent)
- Plateau élargi de 32 px : duplication de la bande centrale de sable pur x 200-232, recadré (décalage -16 px) → canevas 432×352 inchangé (grille 8 px).
- Décors (pics, rocher vert, cailloux) retirés du sol, comblés avec le sable natif voisin, puis replacés en position symétrique (sprites non retournés) sur un calque `04_details` séparé.
- Pied du plateau prolongé sous la bande de nuages avant (nécessaire car celle-ci défile).
- Aucune couleur hors référence (contrôlé calque par calque), alpha binaire, aucun resampling, aucune génération d'image.

## Calques (ordre)
`00_ciel` · `01_nuages_arriere` (anim) · `02_eclairs` (anim) · `03_plateau` · `04_details` · `05_nuages_avant` (anim)

- **Nuages** : bandes 864 px = original + miroir (raccord sans couture), `RepeatX`, défilement -8 px/s (108 s) et -16 px/s (54 s) — même méthode que les nuages de `viewport_pmdo_v1`. Les nuages cachés derrière le plateau d'origine sont complétés par ping-pong des colonnes de bord (visibles seulement pendant le défilement).
- **Éclairs** : 30 frames plein cadre. Éclairs 1-4 et arc Flash repris pixel pour pixel de la planche ; côté gauche comme la planche, côté droit en miroir (indiqué sur la planche). Chaque impact : Normal / Fading / Normal / Fading, couleurs exactes de la planche. Séquence et cadence (cycle 7,4 s) = choix artistique, pas la cadence GBA officielle.

## Limites
Collisions 8 px indicatives (`collisions_8px` du manifest, `apercu/collisions.png`), non testées en jeu. Aucun test moteur PMDO. Import : PNG to Tileset 8 px, fichiers `MTTHUNDER_V1_*` dans `import_png_8px/` (les éclairs sont dans `eclairs/`).

Reconstruction : `.venv/bin/python source/mt_thunder_orage_v1/build.py`
