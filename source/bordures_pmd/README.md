# Bordures PMD Sky — redessin pour le cap

Bibliothèque de **20 motifs redessinés**, au format natif **24 × 24 px**, en cinq colonnes et quatre lignes. Il s’agit d’une réinterprétation des bordures de PMD Explorateurs du Ciel adaptée à la palette du projet, pas d’un tileset officiel ou d’un simple export des pixels du jeu.

## Motifs

| IDs | Famille | Orientations |
|---|---|---|
| 0–3 | Rives | N, E, S, W |
| 4–7 | Angles sortants | NE, SE, SW, NW |
| 8–11 | Angles rentrants | NE, SE, SW, NW |
| 12–15 | Diagonales | NE, SE, SW, NW |
| 16–19 | Paroi | centre, bas, gauche, droite |

`definitions.json` consigne l’ordre et les propriétés. `guide_atlas.png` est un guide géométrique, sans illustration finale. `atlas_generation_normalisee.png` conserve la génération, ramenée au format du guide. `bordures_redessinees.png` est l’atlas RGBA final : découpe, transparence contrôlée et palette harmonisée avec le cap. Les ombres restent brunes, sans épais trait noir.

## Références

Les extraits de `reference_bordures_pmd_sky.png` proviennent des cartes **Treasure Town**, **GuildOutside** et **Sharpedo Bluff** du dépôt [Minemaker0430/ExplorersOfSkyOrigins au commit b8c0de576606c5a24802158462d5d1d7e561f72d](https://github.com/Minemaker0430/ExplorersOfSkyOrigins/tree/b8c0de576606c5a24802158462d5d1d7e561f72d). Ils servent à étudier les lèvres d’herbe, la terre, les petites facettes rocheuses, les côtés et les angles. Le dépôt crédite notamment Sloth pour les Ground Maps. Ces extraits restent des graphismes tiers ; les fichiers de jeu complets ne sont pas redistribués ici.

Une première demande de génération n’a renvoyé aucune image. L’essai suivant a produit les vingt motifs. La normalisation remet les cellules à 24 px, respecte les formes de transparence du guide et rapproche les verts/ocres de la palette du cap. Les motifs et textures ont été dessinés par le générateur, pas par le script.

## Adaptation au layout actuel

Le cap n’a pas été forcé dans un rectangle de tuiles. Les rives, angles et contours latéraux ont reçu une retouche locale au générateur guidée par cette bibliothèque et par les références PMD. Le motif N est également posé directement, colonne par colonne, sur la rive arrière (`placements_rive_nord.json`). Le gazon intérieur est conservé sous ce raccord afin d’éviter une deuxième bande de pierre isolée.

La zone retouchée est dans `../sharpedo/masque_bordures_pmd.png`. Le chemin possède un masque de protection distinct. L’alpha du cap, l’intérieur de la prairie et le reste de la paroi hors bordure sont conservés. La retouche n’ajoute pas de clôture, de rocher posé sur la prairie ni de bordure artificielle aux limites droite/basse où le terrain continue.

Cette bibliothèque **n’est pas un système d’autotiling automatique à 47 cases**. Les motifs sont disponibles pour la pose manuelle ; le contour organique du cap est adapté dans son PNG, avec les sources et masques conservés.

## Exports utilisables

Dans `../../sharpedo/` :

- `tilesets/bordures_pmd_jour.png` et `bordures_pmd_nuit.png` : atlas natifs.
- `tiled/bordures_pmd_jour.tsj` et `bordures_pmd_nuit.tsj` : tilesets avec noms et orientations.
- `tiled/catalogue_bordures_pmd_jour.tmj` et `catalogue_bordures_pmd_nuit.tmj` : catalogues de toutes les tuiles sur une grille de 24 px.
- Les cartes de falaise chargent aussi le tileset dans leur palette. Leur grille de repérage reste à 8 px ; pour réutiliser les motifs de 24 px, employer une grille de 24 px ou des objets-tuiles.

```bash
python source/prepare_bordures_pmd.py
python source/prepare_sharpedo.py
python source/rebuild_sharpedo.py
python source/build_preview_falaise.py
python source/verify_falaise.py
python source/verify_falaise_browser.py
```

Les contrôles vérifient les vingt motifs, leurs orientations, les liens PNG/TSJ/catalogues, les sorties ouvertes et la conservation du chemin et des zones hors retouche, en plus des animations déjà présentes.
