# Falaise côtière PMD — kit original

Kit de décor Pokémon Mystery Dungeon à cinq calques éditables, construit depuis les sources visuelles IA de `source/exterieur_original/generation/`. La falaise et la mer suivent la logique de placement demandée (promontoire végétalisé au premier plan, récifs rocheux et mer ouverte), sans reprendre de pixels de l'image de guidage et sans élément artificiel.

## Contenu éditable

| Ordre | Calque | PNG chroma-key | Animation |
|---:|---|---|---|
| 0 | Ciel ouvert sans nuage | `calques_magentas/original/00_ciel.png` | fixe |
| 1 | Nuages | `calques_magentas/original/01_nuages_wrap.png` | défile d'1 px/image, période 344 px |
| 2 | Mer | `calques_magentas/original/02_mer_palette.png` | 24 palettes, aucune translation de pixel |
| 3 | Plateaux et reliefs | `calques_magentas/original/03_plateaux_reliefs.png` | fixe |
| 4 | Falaise naturelle | `calques_magentas/original/04_falaise.png` | fixe |

- **Canvas :** 688 × 384 px. La grille de travail/aperçu est de **8 px**.
- Les PNG de calques avec zones vides utilisent exclusivement le fond de clé `#FF00FF` (RGB 255, 0, 255). Les versions transparentes correspondantes sont dans `calques/original/`.
- Les 24 PNG de mer chroma-key sont dans `cycles_magentas/mer_palette/`. Leur atlas est `animations/source_mer_palette.png`.
- `animations/nuages_wrap_original.png` et `animations/mer_palette_original.png` sont les exports animés. Le cycle combiné fait 1 032 images (PPCM de 344 et 24), à 250 ms/image.
- `aseprite/falaise_originale_original.aseprite` et `tiled/falaise_originale_original.tmj` sont les exports d'édition Aseprite et Tiled.

## Aperçu

Ouvrir `../apercu_exterieur_original.html` dans un navigateur (ou via un petit serveur HTTP). Il permet de masquer chaque calque, mettre en pause l'animation et activer/désactiver la grille 8 px. Il est autonome : les images sont embarquées et aucun appel réseau n'est effectué.

## Reconstruction et contrôle

Depuis la racine du dépôt :

```bash
.cache/audit-venv/bin/python source/exterieur_original/build.py
.cache/audit-venv/bin/python source/exterieur_original/verify.py
```

Le constructeur normalise les canvases retournés par le générateur en pixels entiers, réalise uniquement une clé de transparence fuchsia connectée au bord, puis exporte les fichiers. `verify.py` vérifie les dimensions, le chroma-key, l'identité du wrap à 344 px, l'absence de déplacement de la géométrie marine, la composition, l'entête Aseprite, le fichier Tiled et la présence de la grille dans l'aperçu. Le résultat du dernier contrôle est consigné dans `controle_qualite.json`.
