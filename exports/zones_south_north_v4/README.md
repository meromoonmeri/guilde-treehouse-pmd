# Lot 04 — deux entrées sud → nord, pixels natifs

Suite du programme « relayouts aux pixels natifs » (V1 → V2 → V3 → **V4**). Deux nouvelles références du commit `9ec9a081` sont produites avec la méthode approuvée : arrivée au sud, bouche/issue au nord, matériaux canoniques et calques indépendants. Les lots antérieurs restent intacts ; **aucune carte existante n'est modifiée**.

## Cartes

### Entree aride — `arid_cave_entrance/`
Référence : `entrancearidedungeonpmdsky.png` (408×288). Carte **480×384**, grille 8 px.

| Calque | Contenu |
|---|---|
| `01_sand_ground` | Sable natif, chevauchement de patches (source0,216..280) |
| `02_sand_path` | Chemin sable plus clair, patches sous la bouche (source180,124..200) |
| `03_north_wall` | Bande de falaise reassemblée sans miroir : source0..166, 246..408 (×2) |
| `04_wall_feet` | Pied de falaise (masque roche brun), trous aux emplacements des rochers |
| `05_cave_entrance` | Bouche native source(166,18,246,100) déplacée au centre |
| `06_dead_trees` | 2 arbres morts + 2 brindilles, modules traduits |
| `07_rocks` | 2 gros rochers à leur emplacement natif (translation nulle) + 1 pierre repositionnée |
| `08_pebbles` | 5 cailloux natifs repositionnés |

Entrée : **[240,104]**, arrivée sud dégagée, chemin continu (masque, pas une collision moteur).

### Grotte violette à deux issues — `purple_two_exit_cave/`
Référence : `roadundergound.png` (504×408). Carte **424×360**, grille 8 px.

| Calque | Contenu |
|---|---|
| `00_dark_backdrop` | Fond hors chambre (couleur de marge native source0,0) |
| `01_cave_floor` | Sol violet moucheté du panneau natif, traduit tel quel (source40,96,464,404) |
| `02_west_boulders` | Blocaux ouest, bordure mur/sol d'origine conservée |
| `03_east_boulders` | Blocaux est, idem |
| `04_north_boulders` | Bande nord reassemblée (blocs centraux source204..296, aucun miroir) + socle entre les issues |
| `05_exit_west` | Bouche sombre + arche + seuil de pierres, source(96,44,208,168) → canvas36 |
| `06_exit_east` | Bouche sombre + arche + seuil, source(296,44,408,168) → canvas276 |
| `07_crystal_stars` | 10 grappes de cristaux sombres reimplantées |

Entrées : **issues [92,60] et [332,60]** ; seuil de marche entre les issues à canvas(150..274, 96..128) (outil de contrôle, pas une collision). Le gros cristal du bas-gauche reste sur sa position native.

## Données de provenance

- Chaque PNG de calque est accompagné d'un `*_source.npz` : `source_sxy[y,x] = [source_id,x_source,y_source]`, `-1` en transparent. Sources et SHA-256 dans `manifest.json`.
- Recomposition ordonnée des calques = `composite.png` (testée byte-à-byte).
- `path_connectivity_mask.png` + `access_review_NOT_RUNTIME.png` : contrôle de continuité sud→nord, **hors moteur**.
- TSX 8 px descriptifs. Aucun `.rsground`, aucune collision, aucun warp, pas d'animation.

## Credits / réserves

Références utilisateur `entrancearidedungeonpmdsky.png` et `roadundergound.png` (commit `9ec9a081`), byte-identiques au baseline `3d4ea6f0` (commit de base de la branche ; historique linearisé depuis `438b9288`). Artwork PMD et droits de leurs auteurs ; pas de licence supplémentaire déduite.

12 tests dédiés PASS. **Art à examiner ; PMDO/Tiled/collisions/warps NOT TESTED.** Le masque de chemin ne prouve ni la collision, ni le warp, ni l'occlusion en jeu ; l'égalité des pixels ne vaut pas approbation artistique.

Le programme entier reste non terminé : registre complet dans `FULL_PROGRAMME_STATUS.json` (4 candidats sud–nord produits, 16 références encore en attente de layout, 1 BG réagencé, 1 arène générée V16 à examiner, 1 doublon, 1 affiche hors map).
