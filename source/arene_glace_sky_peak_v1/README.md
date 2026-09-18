# Production — Arène du Croissant, panorama Sky Peak

Livraison dans `renders/arene_glace_sky_peak_v1/`, indépendante des arènes V2/V3 et des grottes glacées.

## Demande et références réellement inspectées

Une arène de glace, des montagnes enneigées au loin façon Sky Peak, ciel bleu-noir étoilé et lune canonique. Pas de demande de nouvelle aurore : elle n’est pas ajoutée.

- `pmdskyicearena.png` et `iceroadpmdsky.png` : texture de glace et langage des reliefs, fournis au générateur pour l’arène.
- `source/sky_peak_v1/232233_reference.png` et `sommet_reference.png` : panorama neigeux, fournis au générateur pour les montagnes.
- `source/cote_dix_zones/reference_autre_agent/source__falaise__ciel_nuit_native.png` et `source__falaise__astres_nuit_native.png` : climat validé, **non régénéré**. Origine enregistrée dans ce dossier : commit `c16efe12`.

## Trois générations

1. Arène seule sur magenta : ovale large, surface dégagée, courte approche au sud, bordure arrière basse pour laisser le panorama visible, neige et roche glacée sur les côtés. Pas de symbole, d’eau, de ciel ni de lune cuits dans le terrain.
2. Montagnes seules sur magenta : grand sommet neigeux à gauche du centre, chaînes successives plus basses, selle à droite pour dégager la lune ; éclairage nocturne bleu. Pas de végétation ou de ciel inclus.
3. Sol complet : sous-couche de glace générée à partir de la texture du centre de l’arène, aucun relief. Elle est utilisée seulement sous les zones masquées ; le sol visible vient toujours de la première image après traitement.

Les bruts sont conservés. Les dimensions réelles, et non celles suggérées au modèle, sont dans le manifest. Le terrain reçoit une atténuation choisie RGB×(0,72;0,80;0,96), pas une recoloration déclarée native.

## Découpe, ciel, lune

Le plan du sol visible est défini par un polygone inspecté en coordonnées du brut. Le reste du terrain est partitionné en relief arrière, immersion avant gauche et avant droite. Leur assemblage sur le sol complet reproduit exactement le terrain détouré, normalisé et atténué. Cette partition ne reconstitue pas les faces cachées des objets.

La lune est une composante8connexe de la feuille native, dans le ROI(312,24)-(368,80), puis recadrée à33×36 et posée en(800,64). **516 pixels visibles** ; aucun resampling/recoloration des RGB ou de l’alpha. L’alpha source contient des valeurs partielles : vérifier l’identité du calque, pas son égalité naïve aux RGB de la composition opaque.

Le ciel reprend les65lignes supérieures de la recette native `climate.sky`, puis utilise la couleur existante dominante de la ligne64 pour le prolongement inférieur. Répéter une ligne bruitée formait des stries verticales ; ce premier essai de composition a été rejeté. Ne pas annoncer le ciel complet comme byte-identique : sa partie inférieure est volontairement remplacée pour le bleu-noir demandé, mais aucune couleur nouvelle n’est introduite. Étoiles : `climate.stars` inchangé.

## Reconstruction

```sh
python -m venv .venv
.venv/bin/pip install pillow numpy scipy
.venv/bin/python source/arene_glace_sky_peak_v1/build.py
.venv/bin/python source/arene_glace_sky_peak_v1/verify.py
.venv/bin/python source/arene_glace_sky_peak_v1/publish.py
```

`build.py` reconstruit PNG, ORA, planche et manifest, sans relancer le générateur. `publish.py` crée la galerie et le kit compact (sans les bruts, conservés dans Git). Le HTML contient le manifest et utilise des images locales : aucun fetch/API nécessaire, fonctionnement après décompression.

**29 contrôles d’assets PASS** : sources et bruts, transparence, clé, dimensions, ciel sombre, étoiles natives, lune exacte, placement, panorama, recompositions terrain/scène/ORA, et corridor16px sud→centre. Pas de renduGPU, collisions, navigation ou import moteur testé.

Les anciens lots sont inchangés. Au début de ce tour, la sandbox était revenue au commit de base avec l’ancien lot de falaises non commité : cet état a été conservé dans un stash nommé `Sauvegarde etat local avant restauration des livraisons poussees ca2ed3fc`, puis la branche a été avancée en fast-forward vers les livraisons déjà poussées. Ne pas réappliquer aveuglément ce stash ancien sur les ciels corrigés.
