# Méthode — sprites de personnages PMD dans ce dépôt

Guide pour l'IA (ou la personne) qui reprend la production de sprites de Pokémon au format
SpriteCollab. Il résume ce qui a marché pour Falinks (`personnages/falinks/`), ce qui a échoué,
et l'ordre des opérations à suivre pour le prochain personnage (Zarude est le suivant prévu).

## 1. Le format cible, en dix lignes

Le format est celui des dépôts PMDCollab / SkyTemple (référence : Pichu #0172,
`https://sprites.pmdcollab.org/#/0172?form=0`). Un sprite = un dossier avec :

- `AnimData.xml` : `<ShadowSize>` (0 petit, 1 normal, 2 grand) puis une liste `<Anim>` avec
  `Name`, `Index`, `FrameWidth`, `FrameHeight`, `RushFrame` / `HitFrame` / `ReturnFrame` optionnels,
  `Durations` en ticks de 1/60 s. Une anim peut être `<CopyOf>` d'une autre (pas de chaînage).
- Pour chaque anim non copiée, trois PNG RGBA **de même taille** : `<Anim>-Anim.png` (dessin),
  `<Anim>-Offsets.png` (repères : noir tête, vert centre, rouge main gauche, bleu main droite ;
  couleurs additionnées quand ils se superposent), `<Anim>-Shadow.png` (pixel blanc = ancre au sol,
  vert / rouge / bleu = ombre petite / normale / grande).
- Feuilles : une **colonne par image**, une **ligne par direction** dans l'ordre Bas, Bas-droite,
  Droite, Haut-droite, Haut, Haut-gauche, Gauche, Bas-gauche (8 lignes) ; `Sleep` n'en a qu'une.
- Cases paires ; l'ancre au repos est en **(largeur/2, hauteur/2 + 4)**. Le jeu aligne les images sur
  le pixel blanc : c'est lui qui absorbe glissades, secousses et bonds (l'ancre bouge dans la case).
- Alpha strictement 0 ou 255. **15 couleurs max** sur tout le sprite (le SpriteBot refuse au-delà).
- Index imposés : Walk 0, Attack 1, Strike 2, Shoot 3, Sleep 5, Hurt 6, Idle 7, Swing 8, Double 9,
  Hop 10, Charge 11, Rotate 12. « Set donjon complet » = ces douze-là.
- Le SpriteBot vérifie aussi : un seul pixel blanc par case, un seul repère de chaque couleur,
  durées = nombre de colonnes, feuille divisible par la case, 1 ou 8 lignes, Rush/Hit/Return < nb d'images.

Le vérificateur `verify_falinks_sprite.py` rejoue toutes ces règles : **le réutiliser** pour le prochain
sprite (adapter `OUT`, `REF` et les contrôles propres à la composition).

## 2. Récupérer les références

- Téléchargement : `fetch_page` sur `https://raw.githubusercontent.com/PMDCollab/SpriteCollab/master/sprite/<num>/...`
  fonctionne pour les fichiers texte (`AnimData.xml`, `credits.txt`). Pour les PNG, `gh api -H "Accept: application/vnd.github.raw" /repos/PMDCollab/SpriteCollab/contents/sprite/<num>/<fichier>` a fonctionné tant que le jeton était valide ; `curl` direct échoue (SSL) dans ce bac à sable.
- Pièges de chemin : les formes sont des sous-dossiers (`sprite/0870/0002` = Brass, `sprite/0870/0003` = Trooper) ;
  `sprite/0002` est Herbizarre. Vérifier avec `credits.txt` avant de travailler.
- Zarude (#0893) **n'existe pas** sur SpriteCollab (404) : il faudra le dessiner, pas le composer.
- `sprite_config.json` du dépôt SpriteCollab donne les noms, index et sets d'animations.
- Les copies de référence vont dans `source/personnages/reference/<num>/<forme>/`, **inchangées**, avec leur `credits.txt`.

## 3. Ce qui a marché pour Falinks : composer, pas générer

Falinks au complet n'existe pas sur SpriteCollab ; le Brass et le Trooper existent séparément.
La bonne approche a été une **composition scriptée** (`build_falinks_sprite.py`) :

1. **Lire les unités par rapport à leur ancre.** Pour chaque case : trouver le pixel blanc de
   `-Shadow.png`, noter son déplacement par rapport à (fw/2, fh/2+4), relever la boîte du dessin et
   les repères relatifs à l'ancre. Tout le reste se raisonne en coordonnées « relatives à l'ancre ».
2. **Plan de formation par direction.** File indienne brass en tête, pas de 8 px (7 × 4 en diagonale),
   léger décalage alterné de face / de dos pour que les casques ne se masquent pas. Le plan est
   centré : l'ancre de la formation = milieu de la file.
3. **Ordre de dessin** : du plus lointain (y écran le plus petit) au plus proche ; à égalité, la tête
   de file au-dessus. Sans cela les unités de derrière passent devant en diagonale.
4. **Pistes temporelles.** Quand les unités ont la même cadence (Attack, Swing, Double, Hop, Charge,
   Rotate, Hurt) : unisson, durées recopiées. Quand elles diffèrent (Idle 6 vs 4 images, Shoot 14 vs
   13) ou qu'on veut de la vie (Walk en vague) : une piste par unité, fusionnées par `merge_tracks`
   qui redécoupe le temps aux changements d'image. Résultat : plus d'images, mêmes ticks totaux.
5. **Réassemblage** : case = 2 × (demi-étendue max + 1), arrondie au multiple de 8 ; ancre à
   (fw/2, fh/2+4) + déplacement du brass d'origine ; gabarit d'ombre 24 × 8 recopié tel quel autour
   de l'ancre ; repères du brass reportés (max des couleurs si superposition).
6. **Aucun pixel repeint**, à une exception près demandée par l'utilisateur : la semelle blanche du pied
   levé (deux pixels dans les trois dernières lignes de chaque unité) est ramenée au gris du pied, car elle
   clignotait sur six unités. La palette finale reste celle des unités (13 couleurs).
7. **Ombres par unité** : le format du jeu n'accepte qu'une ombre par sprite. `-Shadow.png` garde l'ombre
   unique ; un calque hors format `ombres_unites/<Anim>-Ombres.png` (alpha 100, même grille) pose une ombre
   normale 14 × 6 sous chaque unité pour les moteurs qui dessinent l'ombre eux-mêmes. Les aperçus l'utilisent.

Décisions à retenir : `ShadowSize` 2 (emprise de deux cases, comme Onix), étincelles de Hurt gardées
une seule fois (composante non principale de l'image du brass, séparée avec `scipy.ndimage.label`),
Sleep en bivouac 3 + 3, Shoot sur la cadence du trooper avec le Shoot du brass réparti par
déformation temporelle calée sur l'élan, le tir et le retour.

## 4. Ce qui n'a pas marché / à ne pas refaire

- Espacement de 6 px vertical : les casques se recouvrent, la file devient illisible. 8 px est le bon
  compromis entre lisibilité et emprise (comparatif fait à 6 / 8 / 10).
- Décalage alterné en diagonale : il inverse la profondeur apparente ; le garder seulement de face et de dos.
- Faire suivre l'ancre de la formation au brass pendant Shoot : la formation tremblait ; ancre fixe.
- Collage de cases complètes (24 × 24) : déborde de la case composée et écrase les voisins ; coller
  uniquement la boîte du dessin.
- Le générateur d'images n'a servi à rien ici : à 24 px et 15 couleurs, il produit du flou à repixelliser
  entièrement et ne conserve pas une base pixel pour pixel. Il reste envisageable seulement pour un
  personnage sans base (voir § 6), et uniquement comme **brouillon de pose**, jamais comme sortie finale.

## 5. Exports attendus dans ce dépôt (mêmes conventions que le reste du kit)

`personnages/<nom>/` doit contenir : les feuilles + `AnimData.xml` ; `nuit/<Anim>-Anim.png` (filtre
`night()` de `source/rebuild_kit.py`, Offsets et Shadow inchangés) ; `<nom>.aseprite` (8 calques =
directions, toutes les anims bout à bout, une étiquette par anim — voir `write_aseprite`) ; `apercu.png`
(planche complète ×2), `apercu_directions.png`, GIF de lecture sur le parquet de l'accueil
(`salles/01_accueil/salle_jour.png`, découpe 264,252–392,316), `apercu.html` (lecteur hors ligne) ;
`kit.json`, `credits.txt` (format SpriteCollab : date, auteur, statut, licence, anims), `README.md`,
`controle_qualite.json` écrit par le vérificateur. Ajouter une ligne dans le README racine.

Toujours : relancer le constructeur deux fois et vérifier que les PNG sont octet-identiques
(déterminisme), puis `git add -A && git commit` et `git push origin <branche de session>`.

## 6. Pour un personnage sans base : ce qui a marché pour Zarude

Zarude n'a pas de sprite sur SpriteCollab et aucune unité à composer. Une première version dessinée de zéro par
l'agent (13 couleurs, squelette Rillaboom) a été jugée **trop schématique** ; l'utilisateur a alors déposé sa
propre planche de marche (`source/personnages/reference/zarude/`, Game Character Hub, 4 directions × 4 images au
double) avec la consigne « à inclure et améliorer ». Le lot `personnages/zarude/` actuel en découle : c'est la
marche à suivre pour le prochain personnage inédit, dans cet ordre de préférence — **une planche fournie vaut
mieux qu'un dessin d'agent**, demandez-la avant de dessiner.

### 6.1 À partir d'une planche fournie (`zarude_pieces_from_sheet.py`)

1. **Mesurer la planche avant tout** : facteur d'échelle (la planche Zarude était au double : blocs 2 × 2
   uniformes → réduction 1:1 sans perte), taille des cases, ordre des lignes (ici Bas, Gauche, Droite, Haut) et
   des colonnes (repos / pas A / repos / pas B ; les images 2 et 4 étaient les 1 et 3 descendues d'un pixel),
   ancre au sol (le pixel médian du bas des pieds), nombre de couleurs. Écrire ces mesures dans le script.
2. **Réduire la palette sans changer le dessin** : les teintes quasi doublons (écart < 20 sur chaque canal,
   quelques pixels chacune, typiques d'un export d'éditeur) sont fusionnées à leur voisine → Zarude 17 → 11
   couleurs. Ne pas requantifier autrement : le SpriteBot accepte 15 couleurs opaques.
3. **Découper chaque case en pièces pixel-exactes** avec des tables de plages `R(y, x0, x1)` (une pièce = liste
   de segments horizontaux), et **vérifier la découpe** : la réunion des pièces doit redonner la case exactement,
   sans pixel oublié ni compté deux fois. Les pièces d'une vue « gauche » sont retournées à la découpe
   (`flip=True`, x → 15 − x) pour que le constructeur ne travaille qu'en Bas / Droite / Haut, les vues gauches
   restant des miroirs exacts comme chez les officiels.
4. **Nommer les points** utiles sur chaque pièce (épaule, poing, centre de la tête) dans le repère de l'ancre :
   ce sont eux qui donnent les repères Offsets et les articulations des bras dessinés.
5. **Reconstruire Walk d'abord** et comparer au pixel près avec la planche (`WALK_BOB = 0` pour la comparaison ;
   une fonction `cmp` qui liste les pixels différents). Tant que Walk n'est pas exact, ne pas passer aux poses.
6. **Dessiner ce qui manque, dans le trait de la planche** : diagonales (tête et poitrail de trois quarts par
   décalage d'un pixel des traits et affinement de l'oreille éloignée, membres rapprochés de l'axe de 3 px, bras
   éloigné derrière le corps), bras des animations (levé, tendu, plié au poitrail, poussée) avec contour noir,
   cuff et main griffue empruntés à la planche, sommeil, effets. Un bitmap ASCII 1:1 par pièce, deux points
   nommés par bras. **Ne jamais ré-échantillonner** une pièce (rotation, mise à l'échelle) : le résultat a été
   rejeté à chaque essai, on redessine.

### 6.2 Squelette, poses, contrôle (commun aux deux cas)

1. **Choisir un squelette officiel de même carrure** et le télécharger en entier dans
   `source/personnages/reference/<numéro>/` (pour Zarude : Rillaboom #0812, demandé par l'utilisateur). Le
   squelette, c'est `AnimData.xml` (animations, cases, durées, Rush/Hit/Return) **plus le déplacement du pixel
   blanc de chaque case de `*-Shadow.png`** : c'est lui qui porte la charge de l'attaque, le cercle de Swing,
   l'aller-retour de Double, la parabole de Hop, la secousse de Charge. Le constructeur le relit tel quel
   (`anchor_displacements`), il n'y a rien à inventer côté timing. Pour Swing et Rotate, l'image i regarde la
   direction (d − i) mod 8 : vérifier le sens sur la référence avant d'écrire la règle.
2. **Garder la taille native du dessin** : Zarude (22 px) est plus petit que Rillaboom (35 px) et reste 22 px
   dans les mêmes cases 48 × 64 ; on n'agrandit pas un sprite pour remplir un gabarit. Adapter `ShadowSize`
   (0 petit, 1 moyen, 2 grand) à la taille réelle, pas à celle du squelette.
3. **Une pose = un dict de décalages** (`assemble`) : marche = images de la planche, accroupi = corps −2 px et
   membres raccourcis côté épaule (`Arm.shortened`), poussée = bras avancés de 2 px, etc. Le plan d'animation
   (`frame_plan`) associe à chaque image de chaque animation une orientation, une pose, une hauteur (Hop) et des
   effets (griffures, ondes, étincelles). Les membres du côté éloigné sont assombris d'un cran (`darker`).
4. **Si une pose déborde de la case de la référence**, agrandir la case par pas de 8 en gardant l'ancre en
   (fw/2, fh/2 + 4) (`Builder.fit`) plutôt que de tasser le dessin ; ne le faire que si nécessaire (Zarude :
   Hurt 56 × 72 et Swing 88 × 96).
5. **Le générateur d'images n'a servi qu'à des brouillons de pose** pour trancher des questions de design. Tout
   ce qui en sort est hors grille et hors palette : il ne faut jamais l'insérer dans une feuille.
6. **Vérifier contre la référence** : mêmes durées et Rush/Hit/Return, même déplacement d'ancre et même gabarit
   d'ombre à chaque case, cases identiques ou agrandies d'un multiple de 8, miroirs exacts, Swing/Rotate qui
   tournent d'une direction par image, Idle/Charge = repos de Walk, palette ⊂ pièces. Ces règles sont dans
   `verify_zarude_sprite.py` et s'adaptent en changeant `REF`, `SHADOW_SIZE` et la palette importée.
7. **Relire les aperçus à l'œil**, animation par animation, à ×2 ou ×4 (`apercu.png` découpé en bandes, GIF sur
   le parquet) : le vérificateur ne voit ni un bras qui traverse le torse ni une main détachée.
8. **Crédits** : planche fournie + squelette emprunté → citer la planche (auteur si connu, outil), l'auteur de la
   référence et sa licence dans `credits.txt` (CC BY-NC 4.0 pour Rillaboom, donc pour Zarude), et rappeler que le
   sprite n'est ni soumis ni approuvé sur SpriteCollab.

Ordre de grandeur : une demi-journée d'agent pour découper et reconstruire Walk exactement, autant pour les
diagonales et les bras ; le reste est mécanique une fois le pipeline Falinks/Zarude en place.

## 6 bis. Variante d'un sprite existant : ce qui a marché pour les Dynamax

Quand la demande est une **variante** d'un sprite complet (Dynamax, brillant, taille, effet), on ne redessine
rien : on transforme les feuilles de la source case par case (`build_dynamax_sprites.py`).

1. **Lire la source comme SpriteBot la lit** : `AnimData.xml` (attention, certains alias `CopyOf` de SpriteCollab
   n'ont pas d'`<Index>` : le garder absent, ne pas en inventer), les trois feuilles, l'ancre = pixel blanc de
   Shadow, les repères = pixels d'Offsets. Reprendre **toutes** les animations, y compris les spéciales
   (Stomp, Twirl, RearUp, MultiStrike, QuickStrike, Shock, Punch, Appeal, SpAttack) et les `CopyOf`.
2. **Transformer sans rééchantillonner** : agrandissement au plus proche voisin (`np.repeat`, × 3 pour les Dynamax :
   « plus grands » qu'un × 2 jugé insuffisant), effets dessinés en pixels à l'échelle du dessin avant
   agrandissement (aura par dilatation binaire de la silhouette, nuages en bitmaps ASCII), couleurs ajoutées
   comptées (≤ 2 pour rester sous 15 quand la source en a 13).
3. **Recalculer la géométrie** : case = source × échelle puis élargie par pas de 8 pour contenir les effets, ancre
   au repos en (fw/2, fh/2 + 4), déplacement d'ancre = celui de la source × échelle, repères × échelle (un pixel
   chacun, pas un bloc), gabarit d'ombre agrandi mais un seul pixel blanc, `ShadowSize` adapté à la taille finale.
4. **Effets qui bouclent** : tout ce qui tourne ou scintille doit avancer d'un multiple entier de son motif par
   cycle d'animation (les nuages font un tiers de tour par cycle : trois nuages identiques à 120°, la boucle est
   invisible) ; décaler la phase par direction et par image pour que les feuilles ne soient pas des copies.
5. **Effets qui suivent le corps** : ancrer les effets sur la silhouette de *chaque image* (point le plus haut,
   boîte englobante), pas sur l'ancre au sol, sinon ils restent au sol pendant Hop et flottent dans Sleep.
   Cela ne vaut que pour un effet **cuit dans le sprite** (l'aura) ; voir le point 8 pour les effets séparés.
6. **Vérifier par différence avec la source** : chaque pixel opaque de la source doit se retrouver, agrandi, à sa
   place ; les seuls écarts tolérés sont sous un effet de premier plan et doivent être de la couleur de cet effet
   (`verify_dynamax_sprites.py`). Les sprites officiels **ne sont pas** des miroirs exacts gauche/droite :
   comparer chaque direction à la sienne, pas au miroir.
7. **Crédits** : reprendre les lignes de `credits.txt` de la source telles quelles, ajouter la ligne de la
   transformation avec la licence de la source (une variante dérivée suit la licence de l'original ; « Unspecified »
   pour les sprites CHUNSOFT = usage de fan non commercial).
8. **Un effet de jeu est un VFX séparé, pas une partie du sprite** (retour utilisateur : « c'est un VFX quand tu
   actives la Dynamax in-game, donc pas de perso, pas de fond, c'est pour chaque sprite »). Les nuages tournants et
   l'animation de transformation ont d'abord été cuits dans les feuilles de chaque Pokémon (avec le Pokémon
   dedans) : rejeté. La bonne forme est `build_dynamax_vfx.py` → `personnages/dynamax/vfx/` : des feuilles
   **sans personnage ni fond**, génériques, en deux tailles (M : corps ≤ 24 px de large à l'échelle 1, L au-delà),
   avec une ancre (sol pour la transformation, centre de l'anneau pour les nuages, centre du corps pour l'aura),
   `AnimData.xml` aux index libres (13+, une ligne : un VFX n'a pas d'orientation), `HitFrame` = moment où le jeu
   échange le sprite normal contre le sprite Dynamax, `ReturnFrame` = moment où lancer l'effet suivant. Chaque pack
   n'emporte que ce qui lui est propre (l'aura, qui colle à la silhouette) et un `kit.json["dynamax"]["vfx"]`
   (taille + décalage de l'anneau). Le seul lien entre un pack et le VFX est donc géométrique (`vfx_info`), et le
   vérificateur le contrôle. Un GIF de démonstration (`apercu_demonstration.gif`) rejoue la séquence complète sur
   un sprite pour que le lecteur voie le résultat sans moteur de jeu.
9. **Dessiner un VFX en pixel art** (`dynamax_fx.py`) : palette de 4–5 couleurs opaques (sombre, cramoisi, rouge,
   clair, blanc), **aucune transparence partielle** ; les concepts du générateur d'images
   (`reference/dynamax/concept_*.png`) servent de guide de forme et de rythme (volutes à cœur clair, colonne à
   cœur sombre, éclairs qui s'enroulent, flash en étoile), puis tout est retracé en pixels : nuages en bitmaps ASCII
   à trois phases (un tracé paramétrique de spirale est illisible à cette taille), colonne = bandes verticales
   (bord clair | rouge avec étincelles qui coulent | cœur cramoisi), éclairs = polyligne **zigzag** épaisse
   (corps 2–3 px + bord clair de 1 px) posée sur une hélice, la moitié arrière dessinée avant la colonne et la
   moitié avant après (`spiral_bolt` renvoie ce drapeau). Un éclair en hélice régulière fait un ruban lisse : il
   faut ± 5–6 px de jitter latéral pour lire « éclair ». Un flash en rayons de 1 px disparaît à × 3 : masse pleine
   (ellipse blanche) + rayons de 3 px + colonne surexposée en blanc. Les boucles (nuages) avancent d'un multiple
   entier du motif par boucle et l'apparition se termine sur l'image qui précède l'image 0 de la boucle.

Ordre de grandeur : ~30 s de build par Pokémon (dilatation et collage case par case), 5 min pour dix ; quelques
secondes pour les VFX. PNG indexés (`save_png`) : mêmes pixels, fichiers deux fois plus petits qu'en RGBA (les dix
packs × 3 pèsent 24 Mo, comme la v1 × 2 en RGBA).

## 7. Fichiers utiles

- `source/personnages/build_falinks_sprite.py` — constructeur par composition d'unités (réutiliser `extract`,
  `merge_tracks`, `render`, `sheet`, `write_animdata`, `write_aseprite`, `gif`, `player_html`).
- `source/personnages/zarude_pieces_from_sheet.py` — découpe d'une planche fournie en pièces pixel-exactes +
  pièces dessinées (réutiliser `piece`, `block`, `hand`, les tables `R(y, x0, x1)`) ; écrit `zarude_pieces.py`.
- `source/personnages/build_zarude_sprite.py` + `zarude_pieces.py` — constructeur par pièces sur un squelette
  officiel (réutiliser `anchor_displacements`, `Arm`, `assemble`, `draw`, `frame_plan`, `Builder.fit`).
- `source/personnages/build_dynamax_sprites.py` — variante par transformation de feuilles (réutiliser `load_source`,
  `compose_frame`, `fit`, `make_cell`, `write_animdata` avec `CopyOf` et index absents, `comparison_sheet`,
  `save_png`, `vfx_info`).
- `source/personnages/dynamax_fx.py` + `build_dynamax_vfx.py` — VFX séparés sans personnage (réutiliser `bmp`,
  `clouds`, `aura`, `column`, `bolt`, `spiral_bolt`, `flash_burst`, `to_composed` pour tout effet à une ligne avec
  ancre, `gif` / `demo_gif` pour montrer un effet superposé à un sprite) ; `reference/dynamax/concept_*.png` =
  guides du générateur d'images.
- `source/personnages/verify_falinks_sprite.py`, `verify_zarude_sprite.py`, `verify_dynamax_sprites.py` —
  vérificateurs (règles SpriteBot + contrôles propres à chaque méthode).
- `source/personnages/reference/0870/0002`, `0003` — unités Falinks d'origine ; `reference/0812/` — Rillaboom,
  squelette de Zarude ; `reference/zarude/` — planche de marche fournie par l'utilisateur (source du dessin) ;
  `reference/0186, 0241, 0282, 0297, 0424, 0443, 0674, 0923` — sprites complets SpriteCollab (sources Dynamax et
  des compléments à venir).
- `source/portraits/` — même démarche pour les portraits (retouche pixel d'une base, vérificateur).
- `source/rebuild_kit.py` — `night()`, `ase()`, `font()` partagés avec le reste du kit.
