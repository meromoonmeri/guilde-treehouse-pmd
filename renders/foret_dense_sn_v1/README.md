# FDENSE V1 — entrée de forêt dense, arrivée sud → entrée de donjon au nord

## Ouvrir
- `../../apercu_foret_dense_sn_v1.html` : galerie autonome. On peut afficher/masquer chaque calque ou l'isoler (solo), zoomer de 1× à 4×, superposer la grille 8 px et la **carte de provenance** (bleu = D24P11A exact, vert = D24P31A exact, orange = généré puis retouché).
- `FDENSE_V1_composite.png` : composition 512 × 672 (64 × 84 cases de 8 px).
- `FDENSE_V1_calques.ora` : document OpenRaster, calques alignés.
- `FDENSE_V1_pack.zip` : les 9 calques, le composite, l'ORA, le manifest, ce README et la galerie.
- Revue uniquement : `FDENSE_V1_apercu_x2_revue.png` (×2, plus proche voisin) et `PLANCHE_SPRITES_RETOUCHES_revue.png`.

## Calques (empilement dans cet ordre, préfixe d'import unique `FDENSE_V1_`)
| Calque | Contenu | Origine des pixels |
|---|---|---|
| `01_sol` | herbe au soleil, carte entière | **exacts** D24P11A (quilting guidé, 13 couleurs du cœur de l'herbe) |
| `02_ombres` | antichambre sombre devant et derrière l'entrée | **exacts** D24P31A (herbe d'ombre du cercle sombre, liseré guidé par distance signée), pixels opaques |
| `03_chemin` | chemin de terre pavé, du bord sud jusque sous l'entrée | **exacts** D24P11A (26 segments rigides pleine largeur, coupes minimales) |
| `04_vegetation_basse` | 12 fleurs, 6 petits buissons | **sprites exacts** : fleurs D24P11A (3 modèles), buissons D24P31A (2 modèles) |
| `05_rochers` | 3 rochers | **générés** sur magenta, puis retouchés 1:1 |
| `06_parois_foret` | parois d'arbres ouest et est | **exacts** D24P31A : bande périodique de 192 lignes |
| `07_troncs_racines` | troncs, racines et touffes des 2 arbres géants | **générés**, puis retouchés 1:1 |
| `08_entree` | troncs en arche, tunnel, pierres de gué, fleurs de l'entrée | **générée**, puis retouchée 1:1 |
| `09_canopees` | canopées des arbres géants et de l'entrée (au-dessus du joueur) | **générées**, puis retouchées 1:1 |

Le composite compte 175 couleurs. **Aucune** n'est hors de la palette des deux références (union de 204 couleurs sur la grille 15 bits DS). Les comptes par calque (pixels, couleurs, part canonique ou générée) figurent dans `manifest.json` et dans la galerie.

## Provenance, honnêtement
- **Pixels exacts.** Sol, ombre, chemin, parois, fleurs et buissons sont des copies de pixels de `large.D24P11A.gif…` et `large.D24P31A.gif…`. `FDENSE_V1_provenance.npz` donne pour chaque pixel visible de chaque calque `(source, y, x)` : 0 = D24P11A, 1 = D24P31A. Les tests vérifient l'égalité exacte avec la référence pour 100 % de ces pixels.
- **Parois.** D24P31A est lui-même construit sur un bloc vertical de 192 lignes : `B[y] == B[y+192]` sur les lignes 157 à 199 à l'ouest, 189 à 228 à l'est. Empiler `B[170:362]` (ouest, colonnes 0 à 199) et `B[208:400]` (est, colonnes 320 à 503) reproduit donc **exactement** la continuation canonique, sans raccord inventé. La répétition tous les 192 px est celle du jeu. Les arbres géants et l'entrée la cassent.
- **Arbres géants, entrée, rochers : ce ne sont PAS des pixels natifs.** Ils ont été générés sur fond magenta, avec pour référence de style les vrais arbres, le tunnel et les rochers de D24P11A (`source/foret_dense_sn_v1/bruts/ref_*.png`). Ils ont ensuite été retouchés en pixel art 1:1 par `pixelize.py` :
  - détourage magenta explicite ;
  - vote majoritaire par cellule (pas de 4,5 à 15 px générés par pixel) ;
  - projection Lab dans les sous-palettes de matière des références ;
  - alpha binaire, nettoyage des îlots et pixels isolés.

  Leurs couleurs sont canoniques. Leur dessin ne l'est pas.
- Le rocher généré à mousse jaune a été écarté, car il sortait du style des rochers gris de la référence.

## Contrôles effectués
- `source/foret_dense_sn_v1/test_build.py` : **7/7 PASS**. Tailles multiples de 8, composite = empilement exact, alpha binaire, zéro magenta, calques non vides et distincts, toutes les couleurs dans la palette des références, provenance exacte et honnête (calques canoniques 100 % sources 0/1, calques générés 100 % sources ≥ 100), chemin continu du bord sud à l'entrée.
- `source/controle_qualite_pixel/gate.py renders/foret_dense_sn_v1` : **PASS**. Ce contrôle est technique : ce n'est ni une validation artistique ni un test en jeu.

## Non fait / limites
- **Aucun test PMDO.** Collisions, warps, occlusion et gameplay ne sont pas définis : ils ne se déduisent pas des images.
- Ordre de profondeur proposé : 01 à 05 sous le joueur, 06 parois et 09 canopées au-dessus. 07 et 08 dépendent de la collision que vous poserez (pied des troncs, bouche du tunnel).
- Le haut du chemin et le haut de l'antichambre sombre sont masqués par l'entrée : ils existent dans les calques 02 et 03 mais ne sont pas visibles dans le composite.
- Pas d'animation dans cette version.

## Reconstruire
```sh
.venv/bin/python source/foret_dense_sn_v1/build.py      # environ 1 min 45 : calques, composite, ORA, provenance, manifest, galerie, pack
.venv/bin/python source/foret_dense_sn_v1/test_build.py
.venv/bin/python source/controle_qualite_pixel/gate.py renders/foret_dense_sn_v1
```
