# Cap canonique face mer v1 — falaise Metano stricte, eau native

Nouvelle map SPRITER PRO : paroi Metano plein cadre (1024×512, 128×64 cellules
de 8px), ruisseau de plateau, cascade 64px dans l'axe, ruisseau de premier plan
qui sort au sud vers la mer. **Pixels 100% canoniques, 0 difference.** Aucune
image generee, aucun redimensionnement, rotation, miroir ni recoloration.

Galerie autonome : **`apercu_falaise_mer_canonique_v1.html`** (racine) —
6 calques activables, 4 phases a 167ms, grille 8px, zoom 1×/2×/3×, export PNG.

## Methode (lecons de l'audit appliquees)

- **Modules natifs COMPLETS**, pas de choix cellule-par-cellule :
  herbe 128×128, dalles face 64×48 plein cadre, couronne/pied 64×16.
- Bouche d'eau decoupée dans couronne et pied (cols 60..67) : pas de barre
  rocheuse sur le canal. Contacts W/E/S nets, sans etirement.
- Eau native : canal BASE + 4 planches `River_Animation` + 4 frames cascade
  `Animation_Tileset`, `FrameLength=10`. Les rangees 15-16 de la cascade,
  entierement transparentes en source, sont exclues du mapping (chute sur
  les 15 rangees opaques 0..14 : couronne 0..5, milieu 6..11, pied 12..14).
- Les 3 poteaux jaunes en haut de chute font partie des frames natives.
- Composition dessinee a la main sur grille 8px ; le generateur n'a fourni
  aucun pixel de terrain.

## Contenu `cap_cascade/` (1024×512, multiples de 8)

- `cap_01_sol_herbe.png` : sol plein canvas
- `cap_02_parois.png` : faces 64×48 (2 bandes)
- `cap_03_couronnes_pieds.png` : couronne + pied avec bouche d'eau
- `cap_04_berges.png` : berges BASE du canal (sec : masquer 04/05/06)
- `cap_05_riviere_phase_1..4.png` : eau du canal, 4 phases natives
- `cap_06_cascade_phase_1..4.png` : chute 64px, 4 phases natives
- `cap_SEC.png`, `cap_avec_eau_frame_1..4.png`, `COMPOSITION.png`
- `ANIMATION_COMPLETE.webp` : boucle 4×167ms
- `cap_cascade.ora` : document 6 calques (phase 0), recomposition exacte
- `manifest.json` : sources, hashes, modules, 440 cellules animees avec
  refs `TexLoc` par phase (reutilisable pour PMDO/Tiled)
- `CAP_CANONIQUE_FACE_MER_calques.zip` : tout le lot ci-dessus + controles

## Verification (`verification.json`, PASS)

Decode independant des 7 `.tile`, hashes Git, recomposition SEC + 4 phases,
4 phases distinctes, egalite exhaustive statiques (herbe 8192 cellules,
parois, bordures avec bouche, berges), 1760 cellules eau/phase comparees,
ORA exact, SEC opaque. **Controle pixels uniquement.**

## Limites honnetes

- Ciel et mer non peints : seul le terrain est strict (a composer avec les
  fonds existants si besoin).
- Faces repetees (16× la dalle 64×48) : raccords a apprecier en jeu ; une V2
  pourra varier les modules apres validation de l'echelle en jeu.
- Pas de test PMDO/GPU, collisions, transitions, variante nuit (filtre Abyss
  disponible pour une V2).
- Sources : Palikadude/Halcyon `da6c213...` (riviere : Jaifain). Respecter
  les conditions des auteurs avant redistribution publique.

Reproduction : `source/falaise_mer_canonique_v1/{build,verify,gallery,package}.py`
(Pillow, numpy). Aucun appel reseau ni generateur.
