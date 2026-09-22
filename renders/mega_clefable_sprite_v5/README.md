# Méga-Mélodelfe V5 — cohérence de design garantie + mouvements canoniques SpriteCollab (lot `mega_clefable_sprite_v5`)

## Audit demandé (V3/V4, feuilles générées animation par animation)
Mesure par case (signature couleur vs ta référence 64 px, présence de la calotte blanche, ailes des deux côtés) — `source/mega_clefable_sprite_v5/audit_v3_v4.json` :
- calotte blanche absente dans **7 à 100 % des cases** selon la feuille (V4 Attack/Double : 100 %, Withdraw : 51 %, Swing V3 : 86 %) ;
- distance palette à la référence ≈ 0,32–0,53 avec forte dispersion (écart-type jusqu'à 0,19 sur Withdraw) ;
- 10 cases de Withdraw V4 sans une des deux ailes.
Conclusion : dessiner chaque feuille séparément fait dériver le design d'une case à l'autre ; le résultat ne ressemble pas assez à ta référence. Confirmé.

## Méthode V5 (corrige les deux problèmes)
1. **Un seul jeu de base on-model**, dessiné par le générateur d'après ta référence stricte et validé visuellement : turnaround 8 vues (`source/mega_clefable_sprite_v4/gen/raw_turnaround.png`) + poses d'action (attaque face/profil, blessé face/profil, sommeil, charge). Converti une fois en pixel-art (corps 30 px, palette 16 couleurs relevée sur ce dessin, contour 1 px). → `jeu_de_base_on_model_x4.png`.
2. **Mouvement = celui des artistes SpriteCollab** : pour chaque animation/direction/frame, le sprite est placé sur le **marqueur vert (centre du corps) de l'Offsets.png CHUNSOFT du Mélodelfe**. Trajectoires ainsi reprises : Attack (recul −3 px, élan +19 px sur les frames Rush→Return, retour), Double (secousse ±6/10/12/13 px alternée), Swing (arc circulaire de 22 px), Charge (oscillation 1 px), Hop (parabole), Rotate (tour sur place), Withdraw (recul-maintien-retour). Pose substituée par phase : élan → pose d'attaque, Hurt → pose blessé, Sleep → pose sommeil, Charge → pose charge ; ailes battent (décalage de colonnes ±2 px, il vole/plane).
3. Frames agrandies de 24 px de côté et 8 px en hauteur (ailes plus larges que Mélodelfe) ; `Offsets`/`Shadow` = canoniques décalés du padding ; `AnimData.xml` = durées, Rush/Hit/Return et Strike=CopyOf canoniques.

## Vérification — `verify.py` 64/64 PASS
format PMDOWiki (noms/index, CopyOf, 3 PNG même taille, frames paires, colonnes = durées, aucune case vide/coupée, centres uniques, alpha binaire, ≤16 couleurs), Offsets/Shadow identiques au canon après retrait du padding, **design présent dans 100 % des cases** (calotte + deux ailes) pour les 12 animations.

## Fichiers
`sprite/0036/0001/` (13 anims), `0036_0001_mega_clefable_v5_spritecollab.zip`, `apercu_<Anim>.webp` (12 aperçus animés, 8 directions), `planche_<Anim>_x2|x3.png`, `jeu_de_base_on_model_x4.png`, `manifest.json`.

## Limites
Art IA (déclaré) ; les vues haut-droite/haut-gauche utilisent la vue de dos (pas de dessin ¾ dos) ; les poses intermédiaires (ex. main levée du Swing) sont approximées par la pose d'attaque + trajectoire ; relecture humaine avant soumission ; non testé en moteur. V1–V4 conservés.

## Audit V5 (même script, `audit_v3_v4.json` contient aussi v5)
0 case sans une des deux ailes sur les 12 animations ; calotte > 2 % des pixels dans 100 % des cases pour 9 animations ; sur Attack/Double/Swing les cases en pose d'attaque de profil ont une calotte plus petite (< 2 % des pixels, mais toujours présente ≥ 3 px : contrôle `verify.py`). Les pixels d'une direction donnée sont identiques d'une frame à l'autre par construction.
