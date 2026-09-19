# Entree de foret style Sinister Woods — rendu genere multicouches (V1)

Scene 1408x768 (176x96 cases de 8 px), generee au generateur sur fond magenta,
decoquee puis partitionnee en 7 plans. Arrivee au sud (chemin touche le bord bas),
ouverture sombre au nord (bbox 640-773 x 72-185).

## Sources
- `bruts/foret_entree_magenta.png` : scene complete generee (PMD DA, nuit sombre).
- `bruts/sol_nu_magenta.png` : sol nu genere separement (trace du chemin different :
  donneur de texture / base alternative, PAS un underlay recale).
- Bruts conserves tels quels ; `_grid` / `_review_*` = vues de controle.

## Plans (`SinisterGen_*.png`, RGBA, alpha 0/255)
1. `01_sol` — sol du couloir central (split spatial : dilation 90 px autour du chemin ;
   la couleur/texture ne separe pas la mousse sombre de la canopee sombre).
2. `02_chemin` — chemin beige (regle tan R>115...), sud -> grotte.
3. `03_rochers` — rochers gris (faible saturation).
4. `04_buissons` — buissons (petits blobs verts, bande centrale).
5. `05_vegetation` — masses vegetales laterales et hautes (hors couloir).
6. `06_ombres` — creux strictement sombres (SUM<38).
7. `07_grotte` — ouverture nord : pixels noir-violet (SUM<110 ET G-R<12, la luminosite
   seule confond l'ouverture et le feuillage) + cadre elliptique documente
   (centre 707,131 rx 67 ry 60). Forme organique, pas de bord ROI droit.
- `SinisterGen_00_sol_nu.png` : bonus sol nu. `SinisterGen_composite.png` : recomposition.

## Nettoyages documentes
- Decoupe magenta par inondation depuis les bords, regle large anti-frange
  (R>100&B>100&G<110...) : 0 px de frange residuelle, 0 trou interieur.
- 5 taches bleues parasites (dont un tesson 32x32 sur le chemin) retirees par
  inpaint median en anneaux locaux (contours sombres inclus par dilation 3).
  Aucun bleu restant (teste).
- Recomposition des 7 plans = composite a l'octet ; chaque pixel terrain
  appartient a exactement un plan (45 tests PASS).

## Limites honnetes
- RENDU GENERE : textures inventees dans la DA PMD, PAS des tuiles natives
  certifiees. Aucun import/test PMDO, aucune collision/warp.
- Partition de surfaces visibles : le cache sous les masses n'est pas reconstruit.
- Galerie : `apercu_sinister_woods_gen_v1.html` (calques, zoom, grille 8 px).
- Scripts : `source/sinister_woods_gen_v1/{build,test_build,package}.py`.
