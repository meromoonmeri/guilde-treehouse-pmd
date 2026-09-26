# ECN1 — Entrée Cascade sud → nord, 4:3 vaste, pixels natifs exacts

Demande : poursuivre la série des entrées (arrivée sud → entrée nord) au format 4:3, puis correction en cours de route : **« je demande les textures canoniques »**. Ce lot n'utilise donc **aucun pixel généré** : le rendu généré `source/entree_cascade_sud_nord_v1/bruts/decor_magenta.png` n'a servi que de guide de composition (chute nord, deux bassins, chaussée, plateforme).

- Aperçu : `apercu_entree_cascade_sud_nord_v1.html` (racine) ou `review/ECN1_scene_animee.webp`.
- Pack PMDO 0.8.12 : `ECN1_projet_pmdo_0812.zip`.
- Calques PNG 8 px (préfixe `ECN1_`) + provenance : `ECN1_calques_png_8px.zip`.
- Source : `source/entree_cascade_sud_nord_v1/`, 10 tests.

## Sources canoniques et opérations

| Source | Ce qui est pris | Comment |
|---|---|---|
| `Waterfall_Cave_ledge_TDS.png` (L) | vide, plafond/stalactites, rangée nord, parois entières (avec leurs sources turquoise natives), sol du couloir, deux petites pierres | rectangles posés tels quels (identité à gauche, +360 px à droite), coutures verticales à coût minimal, bas coupé le long des contours sombres natifs ; sol par quilting de blocs 48 px (phase verticale 24 px = période native du couloir) |
| `Waterfall_Cave_gem_TDS.png` (G) | eau profonde en mailles, quatre paires de rochers, six cristaux | quilting 48 px pour l'eau ; objets masqués (vide pourpre/eau/noir exclus ; cristaux = facettes saturées ou claires) |
| `sprites/eau_metano/cascade_frame_1..4.png` | corps propre de la cascade (lignes 24–119, colonnes 8–55) | deux bandes de 48 × 96 côte à côte, translation pure, 4 phases × 10 ticks |
| `Metano_Town_River_Sparkles.tile` | grappes de scintillements | pixels natifs inchangés, 4 phases × 10 ticks |

Aucune rotation, aucun miroir, aucun redimensionnement, aucune recoloration. `provenance/ECN1_provenance.npz` donne pour chaque pixel opaque de chaque calque sa source et ses coordonnées ; `test_static_layers`, `test_cascade_frames_native_translation` et `test_sparkles_native` relisent les sources et comparent pixel à pixel. `review/ECN1_sources_cadres.png` montre les cadres prélevés sur L et G.

## Composition

Vestibule 768 × 576 : plafond sombre à stalactites, rangée de rochers au nord, murs latéraux de Waterfall Cave avec leurs sources turquoise natives, cascade Métano qui se déverse par-dessus la rangée nord entre deux paires de rochers, deux bassins profonds liserés de pierres, chaussée centrale sud → nord et **plateforme au pied de la chute = `donjon_seuil`**. `entrance` au bas de la chaussée.

## Honnêteté

- Tout pixel est natif ; seule la disposition est nouvelle.
- L'eau profonde est statique (aucun cycle natif récupéré) ; la cadence 10 ticks de la cascade est proposée.
- Collisions déduites du sol visible (cases > 25 % bloquées), chemin 16 × 16 vérifié sur la grille seulement ; aucun test PMDO en jeu ; art non approuvé.
