# Sprites Dynamax — dix Pokémon, toutes leurs animations SpriteCollab

Versions **Dynamax** des sprites de donjon, au format SpriteCollab / SkyTemple. Pour chaque Pokémon, **toutes les
animations du sprite d'origine** sont reprises (noms, index, `CopyOf`, durées, `RushFrame` / `HitFrame` /
`ReturnFrame`, déplacements de l'ancre) ; le dessin est agrandi × 2 pixel par pixel, entouré d'une aura rouge
tramée et surmonté de trois nuages rouges qui tournent au-dessus de la tête. Aucun pixel du Pokémon n'est
redessiné.

| Dossier | Pokémon | Source | Animations (index) | Couleurs | Licence |
| --- | --- | --- | --- | --- | --- |
| `0186_tarpaud/` | Tarpaud (Politoed) | SpriteCollab 0186 (CHUNSOFT) | Walk 0, Attack 1, Strike 2 = Attack, Shoot 3, RearUp 4, Sleep 5, Hurt 6, Idle 7, Swing 8, Double 9, Hop 10, Charge 11, Rotate 12 | 17 | non précisée |
| `0241_ecremeuh/` | Écrémeuh (Miltank) | SpriteCollab 0241 (CHUNSOFT) | Walk, Attack, Stomp, Shoot, Appeal = Twirl, Twirl, Sleep, Hurt, Idle, Swing, Double, Hop, Charge, Rotate | 16 | non précisée |
| `0282_gardevoir/` | Gardevoir | SpriteCollab 0282 (CHUNSOFT) | Walk, Attack, Strike = Attack, Shoot = Charge, SpAttack = Appeal, Appeal, Sleep, Hurt, Idle, Swing, Double, Hop, Charge, Rotate | 12 | non précisée |
| `0297_hariyama/` | Hariyama | SpriteCollab 0297 (CHUNSOFT) | Walk, Attack, Strike, Shoot, Twirl = Rotate, Sleep, Hurt, Idle, Swing, Double, Hop, Charge, Rotate | 15 | non précisée |
| `0424_capidextre/` | Capidextre (Ambipom) | SpriteCollab 0424 (CHUNSOFT) | Walk, Attack, MultiStrike, Shoot, SpAttack = RearUp, RearUp, Sleep, Hurt, Idle, Swing, Double, Hop, Charge, Rotate | 14 | non précisée |
| `0443_griknot/` | Griknot (Gible) | SpriteCollab 0443 (CHUNSOFT) | Walk, Attack, Strike = Attack, Shoot, SpAttack = RearUp, RearUp, Sleep, Hurt, Idle, Swing, Double, Hop, Charge, Rotate | 15 | non précisée |
| `0674_pandespiegle/` | Pandespiègle (Pancham) | SpriteCollab 0674 (baronessfaron) | Walk, Attack, Strike, Shoot = Charge, Punch, Sleep, Hurt, Idle, Swing, Double, Hop, Charge, Rotate | 15 | CC BY-NC 4.0 |
| `0923_patachiot/` | Pâtachiot (Pawmi) | SpriteCollab 0923 (baronessfaron) | Walk, Attack, QuickStrike, Shoot, Shock, Sleep, Hurt, Idle, Swing, Double, Hop, Charge, Rotate | 14 | PMDCollab_1 |
| `0870_falinks/` | Falinks (escouade) | `personnages/falinks/` (ce dépôt) | Walk, Attack, Strike = Attack, Shoot, Sleep, Hurt, Idle, Swing, Double, Hop, Charge, Rotate | 15 | CC BY-NC 4.0 |
| `0893_zarude/` | Zarude | `personnages/zarude/` (ce dépôt) | Walk, Attack, Strike = Attack, Shoot, Sing, Sleep, Hurt, Idle, Swing, Double, Hop, Charge, Rotate | 13 | CC BY-NC 4.0 |

Chaque dossier contient : `AnimData.xml`, `<Anim>-Anim.png` / `-Offsets.png` / `-Shadow.png`, `nuit/` (filtre nuit
des salles), `<slug>.aseprite` (8 calques de directions, une étiquette par animation), `apercu.png` (toutes les
images), `apercu_directions.png`, `apercu_comparaison.png` (origine et Dynamax côte à côte sur le parquet),
`apercu_marche_attente.gif`, `apercu_attaques.gif`, `apercu.html` (lecteur hors ligne), `kit.json`,
`controle_qualite.json`, `credits.txt` et un `README.md` avec le tableau des cases.

## Ce qu'est la transformation

1. **Agrandissement × 2 au plus proche voisin** : chaque pixel du sprite d'origine devient un bloc 2 × 2. Un
   Pokémon dynamaxé garde exactement sa forme ; seul son échelle change. Ce choix évite tout rééchantillonnage et
   garde la palette d'origine intacte.
2. **Aura rouge** : un anneau plein d'un pixel (à l'échelle du dessin, donc 2 px à l'écran) colle à la silhouette,
   doublé d'un anneau extérieur tramé en damier dont la phase change à chaque image — le halo scintille pendant
   les animations sans ajouter d'image.
3. **Trois nuages rouges** en halo au-dessus de la tête, sur une ellipse aplatie (demi-largeur = demi-largeur du
   corps + 3 px, demi-hauteur = un sixième de la hauteur du corps) posée juste au-dessus du point le plus haut de
   chaque image : ils suivent les sauts, les bras levés et le sommeil. Ils avancent d'un tiers de tour par cycle
   d'animation, donc la boucle est continue (chaque nuage prend la place du suivant), et d'un douzième de tour par
   direction pour que les huit lignes diffèrent. La moitié arrière de l'anneau passe derrière le corps. Deux jeux
   de nuages : grands (corps ≥ 24 px de large) et petits.
4. **Repères et ancre** : chaque repère d'Offsets (tête, centre, mains) est replacé à sa position × 2, un pixel
   chacun ; l'ancre (pixel blanc de Shadow) aussi, le gabarit d'ombre de l'origine est agrandi et `ShadowSize`
   passe à 2 (grande ombre). Le déplacement de l'ancre à chaque image est celui de l'origine × 2 : charge de
   l'attaque, cercle de Swing, aller-retour de Double, parabole de Hop restent ceux de SpriteCollab.
5. **Cases** : agrandies × 2 puis élargies par pas de 8 pour contenir aura et nuages, l'ancre au repos restant en
   (largeur / 2, hauteur / 2 + 4) comme dans tout le dépôt.
6. **Palette** : deux couleurs ajoutées (aura (232, 40, 72), aura claire (255, 144, 128)) ; l'ombre des nuages
   reprend la couleur la plus sombre du sprite. Les sprites qui avaient 15 couleurs en ont donc 17 (Tarpaud,
   Écrémeuh) : au-delà de la limite d'import strict de SkyTemple, sans conséquence pour un usage dans ce kit.

## Emploi dans la guilde

Un sprite Dynamax occupe environ deux cases de donjon de 24 px en largeur et jusqu'à trois en hauteur (voir les
cases dans chaque `kit.json`). Il se lit à l'échelle 1 du kit : ne pas le réduire. Pour un effet d'apparition,
enchaîner le sprite d'origine (même ancre) puis le sprite Dynamax : les deux ont le même `AnimData` à l'échelle
près, les mêmes durées et les mêmes index, donc la même image courante.

## Reproduire ou adapter

```
python3 source/personnages/build_dynamax_sprites.py                # les dix, ~5 min
python3 source/personnages/build_dynamax_sprites.py gardevoir      # un seul (slug ou numéro)
python3 source/personnages/build_dynamax_sprites.py --echelle 3    # autre facteur
python3 source/personnages/verify_dynamax_sprites.py               # « OK » par pack, controle_qualite.json
```

Pour ajouter un Pokémon : télécharger son sprite complet SpriteCollab dans `source/personnages/reference/<numéro>/`
(voir `source/personnages/METHODE_SPRITES_PMD.md` § 2) et ajouter une ligne à `POKEMON` dans le constructeur.

Le vérificateur rejoue les contrôles du SpriteBot (index, `CopyOf`, tailles de feuilles, 1 ou 8 lignes, colonnes
= durées, alpha binaire, un blanc par case, un pixel par repère, compte des couleurs) et vérifie que chaque pixel
de l'origine se retrouve agrandi à sa place (les seuls pixels différents sont ceux recouverts par un nuage de
premier plan, moins de 1 % du corps), que l'ancre et les repères sont ceux de l'origine × 2, que les durées, index
et `CopyOf` sont identiques, et que la palette = palette d'origine + aura.

## Licences

Les sprites CHUNSOFT (0186, 0241, 0282, 0297, 0424, 0443) sont les sprites originaux des jeux, hébergés par
SpriteCollab sans licence précisée : usage de fan non commercial uniquement. Pandespiègle et Falinks/Zarude sont
en CC BY-NC 4.0, Pâtachiot en PMDCollab_1 ; leurs crédits sont repris dans chaque `credits.txt`. Les formes
Dynamax ne sont pas des formes officielles acceptées par SpriteCollab : ces sprites n'y ont été ni soumis ni
approuvés.
