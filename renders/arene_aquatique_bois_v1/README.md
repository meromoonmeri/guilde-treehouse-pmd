# Arène aquatique — pierre humide et bois

Référence : `images.png`, 480 × 312, ajoutée dans le commit `3b96b74` (« Référence entrée volcan et arène »). L’autre référence `IMG_4912.jpeg` représente l’entrée volcanique ; elle n’est pas transformée dans cette livraison, consacrée à l’arène demandée.

## Ouvrir
- `../../apercu_arene_aquatique_bois_v1.html` : galerie animée autonome, chaque calque sélectionnable.
- `arene/COMPOSITION.png` : composition à la taille de la référence.
- `arene/ANIMATION.webp` : animation sans perte, 40 × 80 ms, boucle de 3,2 s.
- `arene/arene_aquatique_bois.ora` : les 25 calques à la phase initiale.
- `arene/aqua_*.png` : calques plein cadre alignés et 40 compositions.
- `arene_aquatique_bois_v1.zip` : livraison complète avec scripts, galerie et références nécessaires.

## 25 calques
Cinq statiques : ombre de l’arène, rochers périphériques, couronne de pierre humide, plancher circulaire en bois, passerelle sud en bois et supports de pierre.

Vingt animés : eau du bassin, liserés de contact eau/pierre, **six cascades séparées**, **six écumes d’impact séparées**, **six remous séparés**. Chaque groupe animé possède 40 PNG indépendants en 480 × 312 ; la chronologie est commune. Le plancher et l’accès ne changent pas de pixels pendant l’animation.

Les six chutes reprennent les axes et hauteurs de la référence : (31,99), (79,150), (200,43), (280,43), (400,150), (449,99), coordonnées du pied. Les deux grandes chutes latérales restent plus larges. Stries descendantes, écume persistante au pied, petites gouttes et arcs de remous qui s’élargissent puis s’effacent. Ni écume ni remous ne recouvrent la plateforme. L’eau du bassin est animée par une déformation périodique limitée à deux pixels ; ce n’est pas une simulation de courant global.

## Méthode et provenance
- Plateforme : nouvelle image générée avec `images.png` comme référence, isolée sur magenta, détourée et ajustée en 204 × 240 à (138,72). Plancher, couronne et passerelle sont séparés par masques disjoints. Le brut est conservé. C’est une adaptation **dans le style PMD**, pas un sprite officiel.
- Rochers : sélection des rochers périphériques de la référence dans des régions documentées par le builder, pixels recolorés vers une gamme ardoise humide. L’ancienne arène, les pointes et les matériaux volcaniques sont remplacés.
- Eau : réemploi de la matière générée pour `renders/siphons_ecoulement_v3/bruts/eau_matiere.png`, avec une gamme de huit couleurs adaptée au bassin. Aucun motif de lave ne reste sous forme de simple recoloration du bassin.
- Cascades, écumes, éclaboussures et remous : reconstruits procéduralement aux positions de la référence. Animations artistiques, **pas des animations natives récupérées ni une simulation physique**.

Les textures sont des équivalents visuels adaptés ; la livraison ne certifie pas leur origine ROM. Les éléments issus des références PMD restent soumis aux droits de leurs ayants droit. Les surfaces cachées ne sont pas reconstituées sous chaque morceau statique détouré.

## Vérifications
`verify.py` contrôle les 40 compositions et leurs calques, l’opacité, les six écumes localisées au pied des chutes, l’absence d’animation sur la plateforme sèche, la recomposition ORA et les 40 phases WebP. Les périodes utilisées (8,10,20,40 phases ou une révolution sur40) divisent la boucle commune.

Pas de validation dans PMDO, de collisions ou d’intégration de combat. L’accès sud et le disque sont visuellement ouverts ; cela ne remplace pas un test moteur.

Reconstruction depuis la racine avec Pillow, NumPy et SciPy :
```sh
.venv/bin/python source/arene_aquatique_bois_v1/build.py
.venv/bin/python source/arene_aquatique_bois_v1/verify.py
.venv/bin/python source/arene_aquatique_bois_v1/package.py
```
Le détourage utilise `source/layouts_magenta_v1/palette.py`, fourni avec les références dans le ZIP. Tous les anciens livrables restent intacts.
