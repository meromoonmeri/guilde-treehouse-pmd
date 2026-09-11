# Harmonisation guilde / cap et overlays de mouvement

## Références retenues

- `source/falaise/falaise_native.png` : sommet, terre, bordures et roche de la guilde.
- `source/sharpedo/falaise_native.png` : paroi côtière et son raccord à la prairie.
- Référence d’ambiance indiquée par l’utilisateur : https://www.reddit.com/r/MysteryDungeon/comments/1dqzgam/made_a_set_of_customizable_pelipper_post_office/ . Le serveur Reddit a renvoyé HTTP 403 à la lecture automatique ; les deux images Bekipan déjà fournies à la racine du dépôt ont donc servi de référence disponible.

Les bâtiments ne sont pas repris. Les nouvelles zones conservent leurs layouts propres.

## Passe graphique

Six plans ont été repassés au générateur, avec les deux falaises du projet comme références de DA : les quatre terrains, la paroi boisée de l’étang et les ressauts des cascades. Les crops sont ceux de `layouts.json`. La normalisation au plus proche voisin rétablit les dimensions natives et conserve les alphas des plans existants ; les prolongements de couleur au bord ont été limités à un ou deux pixels. Les sources `*_genere.png` retiennent les dessins sélectionnés.

La mer de nuages et les montagnes des prairies ont ensuite été générées séparément. `montagnes_fond_genere.png` est fixe. `brume_wrap_generee.png` contient uniquement la nappe de nuages : elle possède un raccord horizontal continu et un fondu bas vers une teinte de brume fixe. Aucun dessin de nuage mobile n’est incorporé au ciel ou aux montagnes.

Les deux falaises de référence et le rêve de personnalité ne sont pas modifiés.

## Un plan par mouvement

- Le ciel est fixe.
- Les nuages lointains et proches sont deux PNG transparents distincts. Ils sont dessinés **au-dessus du ciel** et se répètent horizontalement : 1 px/image pour le lointain, 2 px/image pour le proche.
- La mer de nuages des plateaux possède son propre overlay wrap.
- Le fond du bassin/de la mer est fixe ; le cycling de surface est séparé.
- Chaque chute d’eau possède sa propre carte d’indices, palette et calque. Les phases sont décalées entre les chutes.
- L’écume et les rides sont dans un autre calque.
- Le littoral a une pleine lune et un reflet lunaire indépendant, repris des ressources générées dans `a23a0d5` puis adaptés au cadrage sans étirer les astres.
- Les terrains, les reliefs et la végétation restent fixes.

Le nombre de calques dépend donc de la zone et de ses chutes, plutôt qu’un unique calque contenant toutes les animations. Les sources conservent également les fichiers agrégés anciens pour compatibilité de préparation ; ils ne remplacent pas les calques individuels dans les exports courants.

## Formats et contrôles

Les PNG sont les plans éditables à l’image 0. Les Aseprite RGBA utilisent des cels liés déplacés pour le wrap et des phases séparées pour les autres effets. Les Aseprite indexés gardent la carte d’indices fixe et changent les palettes. Tiled reçoit les mêmes phases d’animation.

Les tests vérifient le raccord du wrap, les deux vitesses, l’identité de la somme des plans de nuages à l’image 0, la séparation de chaque cascade, les palettes fixes/cycliques, la lune fixe, les compositions et le rendu navigateur. Il ne s’agit pas d’une garantie d’intégration native PMDO ni d’une validation dans l’interface graphique d’Aseprite/Tiled.
