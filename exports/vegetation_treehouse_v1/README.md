# Végétation animée — premier kit PMD / treehouse

**8éléments originaux** : herbe fine, fougère, cloches violettes, fleurs dorées, buisson rond, buisson à baies, branche feuillue, lierre suspendu. Ce sont des objets décoratifs à poser, pas des autotiles de terrain continu ni une map achevée.

## Tilesheets et animation

- `tilesheets/VT1_vegetation_phase_0.png` à `phase_3.png` :4planches RGBA128×64, même placement des8objets.
- `tilesheets/VT1_vegetation_animated_atlas.png` : atlas512×64, les4phases côte à côte.
- `tilesheets/VT1_vegetation_8px.tsx` : tileset animé Tiled sur vraie grille8×8. Les128sous-cases de la phase0 ont chacune leurs4références de frames, y compris les cases initialement vides pour ne pas couper les feuilles en mouvement.
- Chaque plante occupe une empreinte32×32 =4×4sous-cases8px. `plants/` :32PNG individuels, `editable/` :24poses nettoyées.
- Séquence de vent : **neutre / droite / neutre / gauche**,3dessins uniques,4étapes de14ticks. Le cycle revient au neutre après la pose gauche sans double arrêt artificiel.
- `placement_recipe.json` : coordonnées et noms de feuilles pour placer chaque objet et ses sous-cases dans PMDO. **Recette de placement seulement**, pas une map importée ni un faux binaire .tile.
- Ancrage logique au sol `(16,28)`, ou attache supérieure `(16,3)` pour le lierre. Les zones de racine/attache sont pixel-identiques dans toutes les phases ; le contact logique peut être juste sous le dernier pixel visible.

`review/` :8GIFs individuels,1planche animée,1démo sur sol natif et1référence native Halcyon =11GIFs. Cadences GIF arrondies à10ms, Tiled à1ms ; les14ticks restent la valeur de référence PMDO. Les plantes de la démo sont déphasées.

## Méthode / provenance

Référence Halcyon → génération sur magenta → alpha → échelle native et palette → nettoyage des contours → ancrages fixes → composition des phases. Les layouts générés ne respectaient pas toujours la consigne : les grilles réelles et cases sélectionnées sont documentées dans `manifest.json`.

Les fleurs dorées changeaient de hauteur relative entre poses ; les branches changeaient de topologie. Leur dessin neutre a donc été conservé et son feuillage réarticulé au pixel au lieu d’utiliser ces variations comme un mouvement valide. Les autres éléments utilisent les poses générées, recalées et nettoyées. Pas de translation rigide de toute la plante ou de racines glissantes.

Palette : sept valeurs de feuillage des références natives Halcyon ; ombre profonde, écorce et accents floraux/baies adaptés. Ce n’est pas un lot de portraits soumis à la limite15couleurs. Les franges magenta ont été retirées, en préservant les vrais pétales violets ; les palettes sémantiques empêchent les points violets résiduels sur les plantes vertes.

Références canoniques conservées dans `source/amp_plains_fleurie_v1/references/` : Halcyon working-copy**1522c7a8b7a34d70078e11ed605b21d563b0dc51**, Vast_Steppe_Objects, Vast_Steppe_Base et Vast_Steppe_Flower_Animations. La fleur native emploie3dessins24×24, séquence0/1/0/2 à14ticks ; les TexLoc0/3/0/6 correspondent à une grille8px. Empreintes et provenance dans le manifeste.

Les images originales de Halcyon et le sol natif de la démo sont attribués à Halcyon/Palikadude et à leurs artistes, pas revendiqués comme nos créations. La fleur native de comparaison n’est pas intégrée à notre tilesheet. Respecter les crédits et licences des références ; aucune autorisation générale de redistribution des ressources natives n’est déduite de leur disponibilité.

## État

Précontrôle technique localPASS ; tests de reconstruction des4phases depuis les sous-cases Tiled et depuis la recette PMDO, alpha, pivots, bords libres, source hashes et GIFs. **71tests de régression passent**, dont5nouveaux sur ce kit.

**Art non approuvé ; import/runtime PMDO et Tiled non testés.** Le QG treehouse et les bâtiments annexes restent à dessiner. Aucun bâtiment existant, map approuvée ou ressource de guilde n’a été remplacé. Les animations de personnages encore manquantes ne sont pas annulées.

Reconstruction : `.venv/bin/python source/vegetation_treehouse_v1/build.py`.
Archive : `.venv/bin/python source/vegetation_treehouse_v1/package.py`.
Galerie : `apercu_vegetation_treehouse_v1.html` à la racine.
