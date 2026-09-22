# Aride finale magenta V3 — statut

Demande : version finale avec méthode fond magenta au générateur, textures/pixels
natifs, seulement cliff/sol/chemin/roches/arbre/ombre. Grotte au nord, chemin sud→nord.

## Bruts (10 générations cumulées sur ce tour, budget épuisé)

`bruts/` : cliff_magenta, sol_magenta, chemin_magenta, props_magenta, ombre_magenta
(tous 1224×864, /3 exact → 408×288). Rejetés : parois_magenta (bol), fx_magenta
(non demandé), guide_compo_v2 (plein cadre). Ne plus générer ce tour.

## Recette (leçons à réutiliser)

- Inondation magenta (d<170) + pelage 2 px + kill global résidus, AVANT /3 NEAREST.
- Remap palette native 99 couleurs après normalisation ; L05 compositée puis
  requantifiée (les overlaps alpha créent des mélanges hors palette).
- `paste()` : remplacement direct pour opaques, PIL alpha_composite pour ombres
  (le over numpy manuel a causé un bug de broadcast).
- JAMAIS deux edits + un run du même fichier dans le même bloc parallèle :
  races constatées (placements perdus, runs non déterministes apparents).
  Vérifier au grep + double-run md5 en cas de doute.
- Session parallèle active sur la branche (V1/V2 aride) : noms uniques
  `aride_finale_magenta_v3`, ne jamais écraser ses fichiers.

## Sorties

`renders/aride_finale_magenta_v3/` : 6 calques, 17 sprites, composite, access review,
ORA, manifest, verification. Galerie racine + ZIP. 10 tests PASS, build déterministe.
Pas de runtime PMDO. Programme : entrée aride livrée (3 variantes V1/V2/V3) ;
plage/jungle/cristal et autres zones toujours ouvertes.
