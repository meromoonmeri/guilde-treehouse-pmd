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

Zarude n'a pas de sprite sur SpriteCollab et aucune unité à composer. Le lot `personnages/zarude/` a été
produit ainsi (constructeur `build_zarude_sprite.py`, pièces `zarude_pieces.py`, vérificateur
`verify_zarude_sprite.py`) ; c'est la marche à suivre pour le prochain personnage inédit :

1. **Choisir un squelette officiel de même carrure** et le télécharger en entier dans
   `source/personnages/reference/<numéro>/` (pour Zarude : Rillaboom #0812, demandé par l'utilisateur). Le
   squelette, c'est `AnimData.xml` (animations, cases, durées, Rush/Hit/Return) **plus le déplacement du pixel
   blanc de chaque case de `*-Shadow.png`** : c'est lui qui porte la charge de l'attaque, le cercle de Swing,
   l'aller-retour de Double, la parabole de Hop, la secousse de Charge. Le constructeur le relit tel quel
   (`anchor_displacements`), il n'y a rien à inventer côté timing. Pour Swing et Rotate, l'image i regarde la
   direction (d − i) mod 8 : vérifier le sens sur la référence avant d'écrire la règle.
2. **Fixer la palette d'abord** (≤ 15 couleurs opaques) et l'écrire dans le module de pièces ; le vérificateur
   refuse toute couleur hors palette.
3. **Dessiner des pièces, pas des images** : bitmaps ASCII 1:1 (une lettre = une couleur), pour cinq
   orientations seulement — Bas, Bas-droite, Droite, Haut-droite, Haut ; les trois autres sont des miroirs
   exacts (les officiels font pareil). Pièces utiles : tête, crinière, torse, queue, deux jambes, et un jeu de
   bras par pose (repos, levé, tendu, poing au poitrail, poussée) avec deux points nommés chacun (épaule, poing)
   pour les repères mains. Les membres du côté éloigné sont assombris d'un cran (`darker`), les membres pliés
   sont raccourcis en retirant des lignes (`shorten`), jamais redessinés.
4. **Poser le repos sur la grille de la référence** et comparer côte à côte à la même échelle
   (`apercu_reference.png`) : hauteur du corps, largeur, position des poings. Zarude fait 35 px de haut au repos
   comme Rillaboom, pour la même case 48 × 64.
5. **Une pose = un dict de décalages** (`assemble`) : marche = jambes ±2 px et bras opposés, accroupi = corps
   −2 px et membres raccourcis de 2, etc. Le plan d'animation (`frame_plan`) associe à chaque image de chaque
   animation une orientation, une pose, une hauteur (Hop) et des effets (griffures, ondes, étincelles).
6. **Si une pose déborde de la case de la référence**, agrandir la case par pas de 8 en gardant l'ancre en
   (fw/2, fh/2 + 4) (`Builder.fit`) plutôt que de tasser le dessin ; ne le faire que si nécessaire (Swing pour
   Zarude : 88 × 104 au lieu de 80 × 96).
7. **Le générateur d'images n'a servi qu'à des brouillons de pose** (trois vues grand format) pour trancher
   les questions de design — où va la queue, comment lisent les lianes, quelle taille pour le masque. Tout ce qui
   sort du générateur est en dehors de la grille et de la palette : il ne faut jamais l'insérer dans une feuille.
8. **Vérifier contre la référence** : mêmes durées et Rush/Hit/Return, même déplacement d'ancre et même gabarit
   d'ombre à chaque case, cases identiques ou agrandies d'un multiple de 8, miroirs exacts, Swing/Rotate qui
   tournent d'une direction par image, Idle/Charge = repos de Walk. Ces règles sont dans `verify_zarude_sprite.py`
   et s'adaptent en changeant `REF` et la palette importée.
9. **Crédits** : dessin original mais squelette emprunté → citer l'auteur de la référence et sa licence dans
   `credits.txt` (CC BY-NC 4.0 pour Rillaboom, donc pour Zarude), et rappeler que le sprite n'est ni soumis ni
   approuvé sur SpriteCollab.

Ordre de grandeur : un jour de travail d'agent pour les pièces (la tête et le profil demandent plusieurs
passes), le reste est mécanique une fois le pipeline Falinks/Zarude en place.

## 7. Fichiers utiles

- `source/personnages/build_falinks_sprite.py` — constructeur par composition d'unités (réutiliser `extract`,
  `merge_tracks`, `render`, `sheet`, `write_animdata`, `write_aseprite`, `gif`, `player_html`).
- `source/personnages/build_zarude_sprite.py` + `zarude_pieces.py` — constructeur par pièces dessinées sur un
  squelette officiel (réutiliser `anchor_displacements`, `Arm`, `assemble`, `draw`, `frame_plan`, `Builder.fit`).
- `source/personnages/verify_falinks_sprite.py`, `verify_zarude_sprite.py` — vérificateurs (règles SpriteBot +
  contrôles propres à chaque méthode).
- `source/personnages/reference/0870/0002`, `0003` — unités Falinks d'origine ; `reference/0812/` — Rillaboom,
  squelette de Zarude.
- `source/portraits/` — même démarche pour les portraits (retouche pixel d'une base, vérificateur).
- `source/rebuild_kit.py` — `night()`, `ase()`, `font()` partagés avec le reste du kit.
