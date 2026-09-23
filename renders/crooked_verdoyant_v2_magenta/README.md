# Crooked Cavern verdoyante V2 — calques générés séparément sur fond magenta

Suite de la V1 (`renders/crooked_verdoyant_v1`, scène unique découpée par masques). Ici, à la demande
« génère les layers via le générateur fond magenta multicalque » : **chaque calque est une génération propre sur
magenta #FF00FF**, détourée puis empilée (méthode `source/layouts_magenta_v1/WORKFLOW.md`). La scène V1 sert de
**maquette** : elle est l'image d'entrée de chaque extraction, ce qui garde la mise en page (arrivée sud, grotte au
nord) et l'alignement approximatif entre calques (IoU avec la maquette dans `manifest.json → stats`).

Même format que V1 : 512×640, 1 px = 1 px, origine commune 0,0, jour + nuit (filtre Abyss exact), ORA, galerie
`apercu_crooked_verdoyant_v2_magenta.html` (calques cochables, bruts magenta visibles, variante objets natifs).

## Provenance — à lire avant usage

- **Tous les calques générés sont des dessins générés d'après références PMD canoniques** (audit
  `source/crooked_verdoyant_v1/AUDIT.md`, §5 pour cette V2). **Ce ne sont pas des pixels natifs certifiés.**
- Seuls `complement_natif/*_10_rochers_natifs_crooked.png` et `*_11_arbres_natifs_steppe.png` sont natifs
  (Crooked Objects + Shadows, arbre Vast Steppe), posés par translation seule et vérifiés par reconstruction.
- PMDO runtime, collisions, warps : **non testés**.

## Calques (bas → haut) — `calques/CrookedMagentaV2_*.png` (9 calques, taxonomie des entrées sud→nord V3)

| # | Calque | Brut d'origine | Remarque |
|---|---|---|---|
| 01 | `sol_herbe` | `bruts/sol_herbe_brut.png` (pleine) | **herbe pure** : deux appels du générateur pour effacer les lisières sont revenus sans image → cellules 16×16 touchant la lisière remplacées par des cellules d'herbe du même brut (439 cellules, aucune recoloration). La version générée avec lisières est conservée : `bruts/sol_herbe_lisiere_512x640.png` |
| 02 | `lisiere_foret` | `bruts/magenta_lisiere_brut.png` | bordures de forêt sombre sur magenta (le générateur a aussi posé deux blocs en haut, recouverts par la paroi) |
| 03 | `chemin` | `bruts/magenta_chemin_brut_v2.png` | 1er essai rejeté (gardait la paroi) → `bruts/rejetes/` |
| 04 | `parois_crooked` | `bruts/magenta_parois_entree_brut.png` | paroi + plateau sableux ; ouverture retirée |
| 05 | `entree_grotte` | idem | ouverture sombre + sol de terre du débouché (même règle de séparation que V1) |
| 06 | `rochers` | `bruts/magenta_rochers_brut.png` | rochers et cailloux du pied de paroi avec ombres |
| 07 | `vegetation_basse` | `bruts/magenta_feuille_vegetation_brut.png` | **feuille** de 8 plantes générée sur magenta ; sprites détourés puis posés aux emplacements des plantes de la maquette V1 (`manifest.json → vegetation_placements`). Deux extractions directes rejetées (`bruts/rejetes/`). |
| 08 | `troncs_ombres` | `bruts/magenta_arbres_brut.png` | niveau du sol : troncs + ellipses d'ombre (séparés de la canopée : pixels à > 4 px de tout vert clair) |
| 09 | `canopees` | idem | au-dessus du joueur : canopées avec leurs contours sombres |

Détourage (`source/crooked_verdoyant_v2_magenta/build.py → key`) : fond `(r>150)&(b>150)&(g<100)` → alpha 0 ;
frange forte 3 px `b>g+10` pour chemin/parois/rochers/arbres (aucun pixel légitime n'y a b>g), frange douce pour la
feuille de fleurs. Normalisation 512×640 NEAREST après détourage. `verification.json` : 0 pixel magenta résiduel,
composition = pile exacte des calques, sous-couche opaque et sans pixel de lisière, chemin continu bord sud → sol du débouché (largeur ≥ 46 px),
nuit exacte, complément natif identique aux feuilles, ORA cohérent — `all_pass = true`.

## Différences visibles avec la maquette V1

Le générateur ne restitue pas les objets à la position exacte : arbres IoU 0,60, rochers 0,70, chemin 0,73, lisière 0,87,
parois 0,994 (voir `review/maquette_v1_vs_magenta_v2_vs_natifs_1x.png`). C'est inhérent à la génération par calque ;
les calques restent cohérents entre eux (arbres et rochers hors du chemin, à 36 px de cailloux près).

## Exports multicalques (Aseprite + Tiled + atlas 8 px)

`exports/crooked_verdoyant_v2_magenta/multicalques/` (README dédié) : les 9 calques jour et nuit en PNG alignés,
`CrookedMagentaV2_{jour,nuit}.aseprite`, `CrookedMagentaV2_{jour,nuit}.tmj` + atlas `*_8px.{png,tsj}` dérivé de ces calques,
`verification_multicalques.json` (relecture indépendante, 0 différence de pixel).

## Reproduction

```
.venv/bin/python source/crooked_verdoyant_v2_magenta/build.py
.venv/bin/python source/crooked_verdoyant_v2_magenta/verify.py
.venv/bin/python source/crooked_verdoyant_v2_magenta/multicalques.py && .venv/bin/python source/crooked_verdoyant_v2_magenta/verify_multicalques.py
```
