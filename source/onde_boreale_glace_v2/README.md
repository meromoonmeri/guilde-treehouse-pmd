# Onde boréale V2 — suite des entrées glacées

Le commit `dfa2ac83` contient déjà trois entrées, les calques terrain et la correction des ciels/nuages de Métano. Il était aussi présent sur la branche distante au début du travail. **Ne pas régénérer ces layouts ni les attribuer à cette nouvelle passe.** Cette livraison ajoute l’onde explicitement demandée : nouvelle génération seule, couleur + légère ondulation simultanées, PNG et WebP visibles directement sur GitHub.

## Génération et choix

Trois bruts conservés dans `renders/onde_boreale_glace_v2/bruts/` :

1. `onde_seule_magenta.png` — référence `aurorepmdsky.png` + ciel validé V1 comme contexte de couleur. Rejeté : trop épais, aspect tube avec grosses dents sombres.
2. `onde_seule_fine_magenta.png` — référence canonique + premier essai + ciel validé. Rejeté : lignes parallèles trop rigides, effet proche d’un pont plutôt que d’un rideau lumineux.
3. **`onde_pmd_magenta.png` — retenu**, référence canonique seule. Consigne : reprendre la texture lumineuse irrégulière cyan/verte, un seul rideau avec quelques plis, fins filaments verticaux, sans sky, étoiles, nuages ou terrain ; fond magenta pur, pas de magenta dans l’effet ; pas de tube ni de double contour. Un dessin maître, pas une planche de poses différentes.

La sortie réelle mesure1792×592. Elle est détourée par clé magenta, y compris les poches internes, petites composantes<30pixels retirées. Alpha proportionnel à la luminance, extrémités atténuées ; aucune image de ciel synthétisée derrière. Recadrage au contenu puis réduction **uniforme nearest** dans672×168maximum, centrage horizontal, y14 dans768×640. Paramètres exacts au manifest.

Le choix de l’alpha et de la palette est artistique, pas une récupération du cycle natif. Le troisième dessin est un candidat inspecté, non approuvé par l’utilisateur.

## Animation reproductible

- 32couleurs médian-cut de la texture ×8bandes de phase spatiale → plan indexé256entrées.
- 32LUT ; teinte HSV variée de±0,115tour par un sinus se propageant le long des8groupes. Saturation et valeur conservées à l’arrondiRGB près. Il s’agit d’une animation de palette interpolée, **pas** d’une permutation stricte des mêmes couleurs comme V12.
- Ondulation uniquement verticale, par colonne :

```text
t = frame / 32
E(x) = min(1, x/64, (767−x)/64)
dy = round(E(x) × [1,5sin(2π(x/448−t)) + 0,5sin(2π(x/176+t))])
```

Amplitude≤2px ; max1px de différence par colonne entre deux étapes, retour31→0 compris. Ni roll horizontal, ni wrap de l’aurore, ni accumulation de déplacements. Chaque frame repart des indices et de l’alpha maîtres. Frame32≡frame0.

32×125ms=4s. Huit WebP au total : effet seul, effet sur ciel, trois boucles de scène, trois extraits avec nuages. Les96PNG de composition et les32PNG d’effet sont présents individuellement, pas seulement dans une archive.

## Conservation des autres plans

`preserved_files` épingle39copies byte-identiques de V1 :30plans terrain jour/nuit,6plans de climat,3scènes de jour. Les ciels et les nuages restent ceux de `source/ciels_valides.py` et des références Guilde/Sharpedo `c16efe12`. Pas de ciel ni étoiles V3/V8 de l’arène. Cinq plans terrain + ciel + étoiles + onde + nuages =9plans par ORA nocturne.

Nuages : wrap1440px à−4px/s, période360s. Le viewer conserve cette vraie période. Les boucles WebP4s ont les nuages fixes ; les extraits8s déplacent les nuages à vitesse réelle et sont encodés avec **loop=1**, une lecture, sans faux raccord court. Ils ne représentent pas la boucle entière de six minutes.

## Reconstruction et tests

```sh
.venv/bin/pip install pillow numpy scipy
.venv/bin/python source/onde_boreale_glace_v2/build.py
.venv/bin/python source/onde_boreale_glace_v2/verify.py
.venv/bin/python source/onde_boreale_glace_v2/publish.py
node source/onde_boreale_glace_v2/test_viewer.cjs
.venv/bin/python source/onde_boreale_glace_v2/serve.py
```

`build.py` ne relance pas le générateur. `publish.py` crée les deux entrées HTML et les catalogues Markdown du nouvel effet et des trois zones. AucunZIP redondant : le dossier Git contient déjà tous les PNG, WebP, ORA et sources.

**41contrôles d’assets PASS** : références, préservation39fichiers,32frames reproductibles, alpha, absence de ciel dans l’effet, amplitude et déplacements, couleurs bouclées, pixels WebP visibles, durées, recomposition des96PNG de scène, neuf plans des ORA et wrap. Les tests des falaises corrigées60 et entrées V1 140 passent aussi.

Le test de galerie utilise un DOMsimulé : sélection des layouts, jour/nuit, vues séparées, position dans le cycle, wrap au raccord, contrôles de calques, zoom, liens et préférence de réduction des mouvements. Il ne remplace pas un vrai test navigateur. Ni renduGPU, navigation, collisions, warp ou importPMDO testés. La correspondance de couleur du terrain V1 ne certifie pas les motifs natifs.
