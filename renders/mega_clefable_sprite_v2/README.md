# Méga-Mélodelfe (Mega Clefable) V2 — sprite **dessiné par le générateur** (lot `mega_clefable_sprite_v2`)

Rappel relecture SpriteCollab @aae4cee2 : emplacement `0036/0001 Mega` vide (voir lot V1, conservé). Cette V2 est une proposition indépendante, V1 n'est pas modifiée.

## Méthode
1. **Dessin** : `source/mega_clefable_sprite_v2/gen/mega_clefable_8dir_sheet.png` généré par le modèle d'image, avec la feuille Idle 8 directions du Mélodelfe CHUNSOFT comme référence de style (`gen/style_ref_clefable_8dir_x6.png`). Le générateur a produit 5 vues exploitables (face, face-gauche, gauche, dos-gauche, dos) ; les 3 autres directions sont des miroirs, comme dans les feuilles CHUNSOFT.
2. **Conversion pixel-art** : détourage du fond, hauteur 36 px, quantification 15 couleurs par vue, contour noir 1 px, alpha binaire, frames 64×56.
3. **Animations** (durées canoniques du Mélodelfe) : Idle 6, Walk 8, Hurt 2, Sleep 2, Attack 10 (+ Strike = CopyOf), Charge 10, Dance 6, Hop 10 — battement d'ailes (colonnes externes décalées), rebond, jambe levée, cisaillement pour l'élan/recul, écrasement pour le sommeil.
4. **Offsets/Shadow** générés par frame : vert = centre du corps, noir = tête, rouge/bleu = mains (détectées sur les menottes noires), ombre = disques bleu/rouge/vert emboîtés + pixel blanc au centre.

## Critères format (PMDOWiki « PMD Sprite Format ») — `verify.py` 28/28 PASS
noms/index uniques, CopyOf sans chaînage, 3 PNG de même taille, frames paires, colonnes = nombre de `<Duration>`, 8 lignes, aucun frame vide ni coupé par le bord, un centre vert et un centre d'ombre blanc par frame, alpha sans anti-aliasing.

## Fichiers
`sprite/0036/0001/` (AnimData.xml, 24 PNG, credits.txt), `0036_0001_mega_clefable_v2_spritecollab.zip`, `planche_{Idle,Walk,Attack,Sleep,Hop}_x3.png`, `apercu_walk_8_directions.webp`, `manifest.json` (SHA256 du dessin généré).
Limites : art généré par IA (déclaré dans credits.txt) ; les animations restent des transformations de 5 poses, pas des redessins image par image ; Withdraw/Swing/Double/Rotate non fournies (optionnelles). Non testé en moteur.
