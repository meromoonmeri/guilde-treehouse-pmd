# Luminous Spring — arc-en-ciel, 4 layouts

Galerie autonome : **`apercu_spring_arc_en_ciel_v1.html`** à la racine. Choix du layout, quatre calques masquables, pause, sélection manuelle des 39 phases, export PNG.

## Compositions
- [01 · Source centrale](01_source_centrale/composition.png) / [animation](01_source_centrale/animation.webp)
- [02 · Source à gauche](02_source_gauche/composition.png) / [animation](02_source_gauche/animation.webp)
- [03 · Source à droite](03_source_droite/composition.png) / [animation](03_source_droite/animation.webp)
- [04 · Grande clairière](04_grande_clairiere/composition.png) / [animation](04_grande_clairiere/animation.webp)
- [Planche comparative](PLANCHE_4_LAYOUTS.png), phase 08.

01 conserve la disposition du Spring V1. 02–04 sont trois nouveaux décors générés à partir du Spring V1, puis raccordés au bassin existant. Le bassin est déplacé sans étirement. Les raccords de végétation/rochers ne sont pas des tuiles natives et restent à valider artistiquement ; des détails de raccord subsistent notamment près des rives des variantes 02–04.

## Calques séparés
Tous les calques ont une toile RGBA de **600×600**.

1. `01_decor_sans_lumiere.png` : décor fixe, fond complété sous les pixels lumineux retirés.
2. `02_eau_cascades.png` : phase initiale du mouvement aquatique hors lumière.
3. `03_halo_arc_en_ciel.png` : phase initiale de la lumière du bassin.
4. `04_faisceau_arc_en_ciel.png` : phase initiale du faisceau vertical.

Les 39 frames de chaque calque animé sont mutualisées dans :
- `commun/eau_cascades/00.png`…`38.png`
- `commun/halo_bassin/00.png`…`38.png`
- `commun/faisceau/00.png`…`38.png`

Pour chaque scène, appliquer l’offset du manifeste aux calques communs :

| Layout | X | Y |
|---|---:|---:|
| Centrale | 0 | 0 |
| Gauche | −64 | 0 |
| Droite | +64 | 0 |
| Grande clairière | 0 | −32 |

Les calques initiaux présents dans chaque dossier sont déjà positionnés. Les WebP sont les compositions complètes des 39 phases. Les planches dans `planches/` disposent les frames sur une grille 8×5, cellules de **240×240** pour consultation ; la dernière case est vide. Pour l’import, utiliser les PNG individuels 600×600, non les planches réduites.

## Lumière et animation
Un spectre doux se déplace dans le halo et le faisceau. Le centre reste très clair. La coloration conserve les variations de luminosité du dessin existant ; son mélange s’atténue au bord du bassin pour éviter une découpe de couleur abrupte. Aucun clignotement rapide ajouté.

**39 phases, 10 ticks/image à 60 Hz, boucle 6,5 s**. Les WebP utilisent 167/167/166 ms répétés 13 fois ; la galerie emploie une horloge exacte à 6 images/seconde. Les formes et le rythme de la base Halcyon sont repris, mais **la coloration arc-en-ciel est nouvelle et n’est pas une animation native de Palika**.

Le halo exporté contient aussi les pixels du bassin nécessaires au remplacement de son éclairage initial. C’est un calque de lumière/remplacement RGBA, pas un shader additif. Le fond sous le halo et le faisceau a été reconstruit : désactiver les deux calques lumineux masque effectivement la lumière d’origine.

## Provenance et limites
Base : `renders/soleil_spring_v1/`, carte `Palikadude/Halcyon` au commit `da6c2130d641507447e6386a5e47a296e8cb4c71`, feuilles `PMDCollab/RawAsset` au commit `03c80dad937911572f8fb19903771a47956fc696`. La provenance détaillée reste dans `source/soleil_spring_v1/references/provenance.json`.

Les anciens rendus sont conservés. Les graphismes générés et les nouvelles couleurs ne sont pas attribués à Palika. Les ressources publiques n’impliquent pas une licence illimitée ; respecter les droits et attributions des ressources Pokémon Mystery Dungeon et de leurs contributeurs.

**Pas de nouvelle intégration `.rsground` ou validation en jeu.** Livrable PNG/animations/aperçu multicouche.

## Contrôles et reproduction
Pillow et numpy. Scripts dans `source/spring_arc_en_ciel_v1/` : `build.py`, `gallery.py`, `verify.py`, `test_viewer.cjs`.

`verification.json` : 144 PNG décodés, quatre recompositions initiales exactes, **156 images WebP identiques aux recompositions des calques**, raccord des deux lumières contrôlé numériquement. Ces contrôles ne sont pas une validation artistique ou GPU.
