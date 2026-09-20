# Provenance des générations — plage_rouge_v1 (20 septembre 2026)

Référence canonique côté pixel : `arenapmdskybeach.png` (456×480, 147 couleurs, void (39,39,55)).

## 4 générations (méthode habituelle : magenta → détourage → calques)

| Brut | Références passées au générateur | Rôle |
|---|---|---|
| `bruts/terrain_magenta.png` | `arenapmdskybeach.png` | composition sable+falaises ; zone mer = magenta plat #FF00FF |
| `bruts/mer_f0.png` | `terrain_magenta.png` + `arenapmdskybeach.png` | mer+écume peintes en place dans la zone magenta uniquement |
| `bruts/vagues_8frames.png` | `mer_f0.png` | planche 2×4, silhouette commune, motifs d'écume d'inner déphasés |
| `bruts/sprites_deco.png` | `terrain_magenta.png` | 11 objets au sol sur fond magenta (cailloux→plantes), sans ombres |

Esprit des prompts : style « Pokémon Mystery Dungeon Explorers of Sky, DS-era pixel art, top-down, 1x pixel scale, hard edges, limited palette, no antialiasing, no blur » ; le magenta #FF00FF demandé explicitement comme zone à remplacer / à détourer ; silhouette identique exigée entre les 8 cellules de vagues.

## Décisions dérivées (pas du prompt)

- Canvas final 344×512 (ratio natif du brut, H=512 choisi, W multiple de 8 ; NEAREST uniquement).
- Mer animée : 8 cellules extraites (composante non-magenta majeure/cellule) → réordonnées par cycle Hamiltonien minimal → + fondus 50 % → 16 frames 120 ms. Silhouette = masque maître (zone magenta du terrain normalisé), donc la côte ne tremble jamais.
- Pose peinte écartée du cycle si désalignée du terrain (seuil 3 % ; mesuré 1,07 % donc conservée en export statique).
- Sprites : extraction par composantes (dilatation 6 it. / érosion), normalisation NEAREST vers tailles PMD (16–34 px), placements sur grille 8 px validés dans le masque idoine (sable ou mer).
- Ombres sous les objets au sol : ellipses α=72 calculées, marquées « non natives » dans le manifeste.

## Contre-mesures apprises appliquées

- Pas de `fill_holes` après inondation magenta (leçon V9).
- Seuil serré global d<40 + inondation pour le magenta cuit (leçon V16).
- Pas de wrap horizontal (consigne Halcyon des arènes V13–V16).
- Palette quantifiée ≠ preuve artistique (leçon caps_terrasses_v4) : l'audit dE est publié tel quel dans `manifest.json`.
