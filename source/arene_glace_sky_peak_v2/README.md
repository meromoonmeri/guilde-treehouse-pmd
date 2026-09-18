# Complément panoramique de l’arène Sky Peak

Demande : conserver arène et accès sud, bordures immersives, chaîne de montagnes, ajouter sapins enneigés et aurore dans le ciel bleu-noir avec lune canonique. Clarification : **l’onde doit occuper les manques de ciel des deux côtés**, pas uniquement le milieu.

## État du dépôt retrouvé

Le checkout local avait été restauré au commit de base, avec les anciennes falaises non commitées. Cet état a été sauvegardé dans un stash nommé avant un fast-forward de **la même branche de session**, vers le dernier travail poussé `d972a438`. Le stash reste conservé ; ne pas le réappliquer aveuglément sur les corrections de ciels. L’arène V1 était déjà sur la branche distante et n’a pas été régénérée ici.

## Deux nouvelles générations

- `aurore_panoramique_magenta.png` : références `renders/onde_boreale_glace_v2/bruts/onde_pmd_magenta.png`, composition arène V1 et `aurorepmdsky.png`. Consigne : un seul rideau panoramique irrégulier aux filaments cyan/verts et replis violet-bleu, continu jusqu’aux deux bords latéraux, espaces transparents au-dessus/en-dessous ; pas de ciel, lune, étoiles ni montagnes cuits dedans. Place libre vers la lune, pas de ruban géométrique à double contour. Un seul dessin maître.
- `sapins_enneiges_magenta.png` : `source/references_54d3731/snow.png` et composition arène V1. Consigne : bande de sapins enneigés en plan intermédiaire, grandes masses sur les côtés et petits arbres au centre ; teintes froides PMD, neige bleu-blanc, fond magenta ; pas de ciel ou montagnes incorporés.

Bruts sauvegardés sans modification. Les deux sorties retenues sont des propositions inspectées, pas des dessins approuvés par l’utilisateur ni des textures natives certifiées.

## Traitement

Les huit PNG V1 sont copiés byte-identiques et épinglés au manifest. On insère les sapins après le panorama montagneux et l’aurore entre étoiles et lune. La lune originale reste donc au-dessus de l’effet ; ses pixels opaques sont contrôlés dans chaque composition.

Détourage par clé magenta. Aurore : petites composantes <30 px retirées, alpha de luminance ; normalisation proportionnelle nearest de 1808×592 vers1056×346, pose(-48,-8). **Pas d’atténuation alpha aux bords gauche/droit**, contrairement au petit effet isolé V2. Le dépassement garantit un vrai contenu aux deux limites. Sapins : recadrage(0,63)-(1792,539),640×170,pose(160,175), sans déformation anisotrope.

Animation :32couleurs du dessin ×8groupes de phase→256indices.32LUT avec variation de teinte HSV±0,10tour ; valeur/saturation constantes à l’arrondiRGB près. Onde verticale par colonne :

```text
dy(x,t)=round(1,5sin(2π(x/448−t/32))+0,5sin(2π(x/176+t/32)))
```

Maximum±2px, pas de translation horizontale, pas de wrap. Chaque phase repart du maître, pas de dérive cumulée.32×125ms=4s, frame32≡frame0.

Les données indexées et l’alpha statique sont fournis avec les32palettes. Ce sont des ressources auxiliaires, pas un format natif PMDO prétendument importable.

## Reproduction

```sh
python -m venv .venv
.venv/bin/pip install pillow numpy scipy
.venv/bin/python source/arene_glace_sky_peak_v2/build.py
.venv/bin/python source/arene_glace_sky_peak_v2/verify.py
.venv/bin/python source/arene_glace_sky_peak_v2/publish.py
node source/arene_glace_sky_peak_v2/test_viewer.cjs
.venv/bin/python source/arene_glace_sky_peak_v2/serve.py
```

Les scripts ne relancent pas le générateur. Le dossier de rendu contient dix PNG de calques,32PNG d’onde,32PNG de composition, les assets indexés, troisWebP, unORA, une planche avant/après et les catalogues Markdown pour GitHub. Pas de nouveau ZIP redondant ; le kit V1 reste historique, il ne contient pas ces ajouts.

## Vérifications

**23tests d’assets PASS**, dont la préservation des huit plans V1, la couverture latérale après occlusion, amplitude/boucle, palette, pixels de terrain et lune, recomposition32PNG, WebP exacts sur RGB visibles et alpha, ORA dix plans. Les29tests de l’arène V1 passent aussi.

Couverture minimale sur toutes les phases dans les bandes de ciel latérales120×300 :18373pixels à gauche,21728à droite (alpha≥24 et non cachés par montagne/terrain/sapins). Les colonnes extrêmes conservent209/261pixels alpha. Ce sont des mesures de couverture, pas une validation artistique.

Les tests de lecteur sont un DOM simulé et des vérifications de chemins, pas un navigateur réel. Aucun test moteur, collision ou navigation ajouté. Pas de nouveau nuage inventé et pas de remplacement des familles validées.
