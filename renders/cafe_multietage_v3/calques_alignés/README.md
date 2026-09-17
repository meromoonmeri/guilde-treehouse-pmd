# Café — base commune et calques alignés

Ouvrir `apercu_cafe_calques_v3.html` à la racine. Tous les PNG ont le même canvas **1264×843** et se superposent à **(0,0)**, sans redimensionnement ni déplacement.

## 13 calques
- `00_salle_vide` : architecture vide, sans fenêtres ni rubans ; sol repris depuis le patch natif Metano après génération, à ×3 nearest. Transitions du patch adoucies uniquement au bord ; seuil lumineux café clair conservé.
- `01_mur_casse_remplacement` : fragment de remplacement du mur du fond, brèche et intérieur sombre. Son masque `masque_remplacement_mur.png` est fourni. Ce n’est pas un simple trou alpha qui laisserait le mur intact visible derrière.
- `02_ombre_debris`, `03_debris_bois` : ombre et bois séparés.
- `04_rubans` : rubans détourés depuis la proposition générée, non fusionnés aux murs.
- `05_spirales_sol_murs` : motifs Spinda générés puis isolés ; ils ne remplacent pas la salle par une nouvelle génération.
- `06_table_gauche`, `07_table_droite`, `08_table_avant` : tables canoniques EoSO.
- `09_comptoir_gauche`, `10_comptoir_droit` : corps des comptoirs canoniques.
- `11_decor_comptoir_spinda`, `12_decor_comptoir_bleu` : décorations supérieures canoniques, séparées des corps.

Les sprites natifs non agrandis sont également fournis dans `sprites_natifs/`. Les placements sont enregistrés dans `manifest.json`. Les corps des comptoirs conservent des éléments de contact de leur carte d’origine ; il ne s’agit pas de nouveaux meubles générés. Les masques des décorations excluent les rubans voisins de la feuille source et de petits fragments détachés.

## États identiques hors modification
`salle_vide.png`, `salle_spirales.png` et `salle_mur_casse.png` sont composés depuis **la même base**, et non trois cartes générées indépendamment. Vérification automatique : les pixels hors calques de destruction sont exactement identiques dans intact/cassé ; le tapis et son éclairage restent identiques. En dessous du mur, le masque de destruction suit les éclats et la cavité plutôt qu’un rectangle de sol régénéré.

Dans la galerie, les cases activent chaque calque, et les flèches téléchargent les PNG. Les boutons ne sont que des présélections. La salle s’ouvre vide. `apercu_meuble.png` est une proposition de placement, pas une nouvelle base imposant le mobilier.

### Utiliser la brèche
Sur la base intacte, superposer le calque de remplacement suffit : son cœur couvre le mur intact. Pour éditer le mur séparément, utiliser le masque fourni comme masque d’effacement puis insérer le remplacement. Les rubans sont indépendants : pour l’état cassé, les laisser désactivés ; aucune version déchirée des rubans n’est fournie ici. Ne pas supposer qu’ils s’effacent automatiquement avec la brèche.

## Provenance et limites
Architecture, brèche, débris, rubans et spirales : générations guidées par les vraies références Halcyon / EoSO, puis découpe et correction. Ils ne sont pas des sprites canoniques pixel-identiques. Mobilier : extraits des vraies couches et de la reconstruction `spinda_cafe.rsground` EoSO, source figée dans `source/cafe_multietage_v1/references/`, commit `4e7422acc263886198113a8256677766e4244228` de Minemaker0430/ExplorersOfSkyOrigins. Sol : Metano Cafe Base de Palikadude/Halcyon, commit `da6c2130d641507447e6386a5e47a296e8cb4c71`.

Même canvas et recomposition vérifiés ne signifient pas une validation artistique automatique de chaque ombre ou découpe. Les masques sont adaptés à ces placements fixes ; déplacer un meuble nécessite de revoir ses contacts et ses ombres. Les surfaces cachées des sprites ne sont pas inventées. Pas de `.rsground`, de collision, d’animation de Ludicolo ni de validation PMDO. Le sous-sol apprécié n’est pas modifié.

Reproduction : `.venv/bin/python source/cafe_multietage_v3/layers.py` (Pillow, numpy). Les bruts et les anciennes propositions restent archivés, y compris les essais rejetés ; utiliser ce dossier pour les calques actuels.
