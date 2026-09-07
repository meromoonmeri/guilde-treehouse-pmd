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

## 8. Compléter un sprite officiel : animations de scène (méthode retenue, lot de huit)

Dix Pokémon demandés (#0186, #0241, #0297, #0282, #0443, #0424, #0923, #0674, puis #0685 et #0702) avaient
le set de donjon publié sur SpriteCollab mais **aucune** des 22 animations de scène du set complet (Eat,
Wake, Sit, Sink, Faint…). `build_animations_scenes.py` les ajoute pour tous d'un coup — ajouter un Pokémon
au lot se réduit à **une ligne dans `POKEMON`**, ce qui est le signe que la méthode tient. Ce qui a marché :

1. **Ne rien dessiner.** Chaque image d'une animation manquante est une **case officielle du même Pokémon**
   (Idle, Hurt, Hop, Charge, Rotate, Sleep…), replacée par rapport à son ancre : décalage de quelques pixels,
   changement de ligne, ou troncature par le bas pour l'enfoncement. La palette du résultat est donc
   forcément incluse dans celle du sprite d'origine — le vérificateur l'exige.
2. **Un squelette qui possède déjà ces animations.** Bayleef #0155 a le jeu Chunsoft complet : il fournit
   nombre d'images, durées, déplacements d'ancre, nombre de lignes **et le numéro de créneau `<Index>`**.
   Attention : `<Index>` n'est **pas** l'index global de `sprite_config.json`, c'est un numéro de créneau
   propre au fichier (0-12 pour le set de donjon, 13-34 pour les scènes) ; les `CopyOf` partagent le créneau
   de leur cible. Ne pas contrôler l'un pour l'autre.
3. **Recopier les animations d'origine octet pour octet** dans le même dossier et les redéclarer dans
   `AnimData.xml` : le dossier s'importe alors directement dans SkyTemple, sans réassemblage.
4. **Recettes plutôt que code par Pokémon.** Un dictionnaire `RECIPES` décrit chaque animation par une liste
   de `Step(src, frame, dx, dy, dir_mode, sink, fade_top)`. Les dix Pokémon partagent ces recettes ; seule
   la lecture des cases change. Résultat : un seul constructeur, 220 animations produites, aucun cas particulier.
5. **Ne coller que la boîte du dessin**, jamais la case entière (même piège que Falinks), et recalculer la
   case par pas de 8 autour de l'étendue réelle.

## 9. Compléter des portraits : `build_portraits_manquants.py`

Généralisation de la méthode Falinks à quatre bases très différentes (#0186, #0297, #0424, #0923). Points
qui ont demandé plusieurs passes :

- **Détecter le fond sans toucher au personnage.** Propager depuis le bord en n'autorisant que les couleurs
  qui apparaissent sur le cadre **et jamais dans le carré central 20 × 20** (toujours occupé par le
  personnage sur ces portraits). Le simple « couleurs du bord » avale la moitié du Pokémon quand il partage
  une teinte avec le ciel ; le simple « quatre coins » laisse la frange d'anticrénelage. Il faut les deux,
  plus un rattrapage : une couleur absente du centre dont ≥ 85 % des pixels touchent déjà le fond en fait partie.
- **Yeux : des opérations, pas des motifs.** Falinks avait des bitmaps ASCII dessinés pour sa seule base.
  Pour quatre bases, ce sont des opérations paramétrées (`arch`, `line`, `squeeze`, `lid`, `slant`, `wet`,
  `shrink`, `blank`, `spiral`, `star`) qui n'emploient que le contour, l'iris, la lumière et la peau **relevés
  dans la boîte de l'œil de cette base**. Seule la boîte est à relever à la main par Pokémon.
- **Tenir dans 15 couleurs.** Le dégradé de fond à deux tons fait parfois passer à 16. Repli en deux temps :
  d'abord un aplat (ce que font déjà Dizzy et Surprised chez Chunsoft), puis, si besoin, rabattement des
  couleurs d'effet sur la plus proche de la base. Les deux sont journalisés dans `kit.json`.
- **Reprendre à l'identique** les émotions déjà publiées : la planche est complète et cohérente, et le
  vérificateur compare octet pour octet.

## 10. Un dessin fourni de l'extérieur : `build_zarude_fourni.py`

Quand l'utilisateur fournit une planche (ici 4 orientations × 4 images de 64 × 64, 17 couleurs) :

- **ne pas la repeindre** ; la copier telle quelle dans `source/personnages/reference/` ;
- calculer l'**ancre au sol** de chaque pose (milieu de la dernière ligne opaque) : les planches externes
  n'ont pas de `-Shadow.png` ;
- **réduire la palette** aux 15 couleurs autorisées en rabattant les plus rares, et journaliser chaque report ;
- prendre un **squelette officiel de même carrure** pour tout le temps, et n'écrire qu'un plan de poses ;
- **avouer la limite** : sans vue diagonale dessinée, les quatre diagonales reprennent le profil. Le
  vérificateur contrôle que chaque silhouette produite est, au pixel près, une pose fournie ou son miroir —
  c'est la garantie que rien n'a été inventé.

## 11. Rendre les animations physiologiques (correction majeure du § 8)

La première version du § 8 fabriquait `Eat` en descendant **tout le sprite** de 2 px. C'est faux, et
l'utilisateur l'a signalé à juste titre : un Pokémon qui mange ne saute pas, il **plonge la tête** en
gardant ses appuis au sol. La bibliothèque SpriteCollab sert de mine de templates pour trouver le bon
geste — encore faut-il mesurer ce que fait vraiment l'original.

**Mesurer avant de coder.** Relevé ligne par ligne de l'`Eat` de Bayleef #0155 :

```
image 0 (repos)   lignes 2→19, 188 pixels
image 1 (bouchée) lignes 5→19, 162 pixels
```

Trois faits en découlent, et ce sont eux la spécification :
1. le **bas ne bouge pas d'un pixel** (19 = 19) — les pattes restent posées ;
2. le **haut descend** de 3 px — la tête plonge ;
3. la silhouette **perd 14 % de ses pixels** — elle s'écrase, elle ne se translate pas.

Une translation aurait conservé 188 pixels et fait bouger le bas : le test discrimine parfaitement.

**Implémentation : déformation à charnière basse** (`deform`). La silhouette est coupée à une hauteur
`pivot` ; la partie haute est rééchantillonnée au plus proche voisin sur `hauteur − delta` lignes, la
partie basse est laissée intacte. Comme on ne fait que retirer ou répéter des lignes de pixels existantes,
**aucune couleur n'est créée** — la contrainte du § 8 (palette incluse dans celle de l'original) tient
toujours. Trois gestes : `squash`, `stretch`, `lean`. Pour `lean`, ne surtout pas utiliser `np.roll` :
les pixels sortis d'un côté réapparaissent de l'autre et coupent la silhouette ; il faut élargir la boîte
puis décaler.

**Amplitude relative à la physionomie** (`physiology`). Un Dedenne de 20 px et un Hariyama de 40 px ne
plongent pas de la même hauteur. Les recettes ne portent donc pas des pixels mais des amplitudes
symboliques (`E`, `B`, `S`, `L`, `N`), résolues par Pokémon à partir de la hauteur de la silhouette au
repos. La classe `Amp` accepte `-L` et `S * 2` pour que les recettes restent lisibles.

**Vérifier un comportement, pas une valeur.** `verify_animations_scenes.py` mesure, sur Eat, Nod, Sit et
LookUp, le déplacement du haut, celui du bas et la variation du nombre de pixels, puis exige qu'ils aillent
**dans le même sens que sur le squelette officiel**. Ne jamais coder la valeur attendue en dur : sur `Sit`,
le squelette lui-même descend d'1 px, ce qu'un seuil rigide aurait signalé à tort. Attention aussi à viser
la bonne image de comparaison (`LookUp` culmine à l'image 1, pas 2).

**Reste à faire si on veut aller plus loin :** les gestes qui demandent de bouger un membre séparément
(mâchoire qui s'ouvre, bras qui porte la nourriture à la bouche) ne sont pas atteignables par déformation
globale. Il faudrait segmenter la silhouette en parties, comme `zarude_pieces.py` le fait pour un dessin
original. La déformation à charnière est le meilleur rapport fidélité/risque tant qu'on refuse de repeindre.

## 12. Membres articulés : mains vers la bouche (suite du § 11)

Le § 11 faisait plonger la silhouette entière. L'utilisateur a demandé mieux : « ils doivent bouger leurs
mains et leur bouche comme Pichu ou Riolu quand ils mangent ». C'est le bon exemple, et la bibliothèque
SpriteCollab donne la réponse.

**Mesure de l'`Eat` de Pichu #0172** (image 0 → image 1) : 165 pixels changent, mais la répartition est
parlante — les colonnes des flancs (x 0-3 et 19-22) se vident, le centre autour de la bouche se garnit, et
la **largeur passe de 23 à 18 px**. Le haut *monte* (y 3 → 1) au lieu de descendre. Ce ne sont pas les
épaules qui plongent : ce sont **les bras qui se lèvent**. Riolu #0447 : même signature, −50 pixels.

**La segmentation est fournie par Chunsoft.** Inutile de deviner où sont les mains : `-Offsets.png` marque
`head`, `lhand` et `rhand` sur **chaque case de chaque sprite**. C'est la clé qui rend l'articulation
possible sans dessiner. `pmd_sprite.load_sprite` les expose déjà dans `Frame.marks`.

**`move_limbs`** prélève un disque de pixels autour du repère, l'efface de sa position d'origine et le
recolle ailleurs. Trois pièges rencontrés, tous corrigés :

1. **Ne garder que la composante connexe reliée au repère** (`ndimage.label`) : sinon le disque emporte un
   bout d'oreille ou de queue qui se retrouve flottant dans le vide.
2. **Rayon petit** (13 % du plus petit côté, pas 22 %) : sur Gible et Ambipom, les repères de mains sont
   proches du visage et un disque large emportait le museau.
3. **Protéger la bande centrale du visage** : au-dessus du repère `head`, aucun pixel n'est prélevé. Une
   main déjà devant la bouche ne bouge pas — c'est physiquement juste, et ça sauve les visages.

Bouger le repère `head` lui-même a été **essayé puis abandonné** : découper la tête d'un sprite 40 px la
détache visiblement du cou. La plongée de la tête reste faite par la déformation à charnière du § 11, qui
étire le cou au lieu de le couper.

**Contrôle.** Le vérificateur exige sur `Eat` la signature de Pichu : largeur qui se resserre, appuis au sol
fixes, moins de pixels, et surtout **mouvement localisé** — le nombre de pixels modifiés doit rester
inférieur au nombre de pixels du sprite. Une translation d'ensemble échoue ce dernier test par construction,
ce qui garantit qu'on ne peut pas régresser vers la version du § 8.

**Limite restante :** la bouche ne s'ouvre pas. Chez Pichu, le museau change de forme parce que l'artiste a
dessiné deux états ; on ne peut pas l'inventer sans repeindre. Déplacer les mains devant la bouche donne
l'essentiel de la lecture du geste ; ouvrir la mâchoire demanderait un dessin, pas un déplacement.

## 13. Dessiner comme un artiste Chunsoft (franchir le pas du repeint)

Les § 8 à 12 refusaient par principe de peindre un pixel. Cette section documente le passage à
l'imitation directe : `dessine_eat_politoed.py` **dessine** une bouche qui s'ouvre.

**Étudier avant de dessiner.** Le visage de Pichu #0172 a été dumpé caractère par caractère, repos
contre bouchée. Constat : l'artiste **redessine la tête entière** (la mâchoire, le museau, l'ombre
du menton), pas seulement quelques pixels. Quatre règles observables en sortent :

1. la palette ne s'élargit jamais — pas une teinte nouvelle dans la bouchée ;
2. tout trait est cerné de noir `(0,0,0)` ;
3. l'ombrage passe du clair au sombre **par la teinte moyenne**, jamais de saut ;
4. le changement est local et légèrement asymétrique (jamais de symétrie parfaite).

**Dessiner en clair, pas en hexadécimal.** Les bouches sont écrites dans le source sous forme de
grilles de caractères (`a` = noir, `d` = lèvre claire, `j` = gorge…), avec une entrée `" "` qui
signifie « garder le pixel d'origine ». C'est lisible, modifiable par un humain, et diffable en git —
très supérieur à des coordonnées codées en dur.

**Choisir le bon trait.** Ne pas dessiner « une bouche générique » : repérer d'abord le trait
caractéristique du personnage. Politoed a une grande bouche fermée en trait noir (`y=16, x=9..13`
dans sa boîte Idle) ; c'est elle qu'un artiste ouvrirait. Il faut dumper la case en ASCII et la
regarder en grille zoomée avec les coordonnées, sinon on dessine au mauvais endroit — première
version placée 1 px trop bas et trop carrée, corrigée après contrôle visuel.

**Le vérificateur doit contrôler la grammaire, pas seulement le format.** `verify_eat_politoed.py`
teste les quatre règles ci-dessus. Il a attrapé une vraie faute : la gorge touchait la peau verte
sans cerne noir.

**Piège du contrôle** : Politoed emploie les mêmes rouges pour ses pupilles et pour la gorge, et le
léger `squash` fait que *tous* les pixels diffèrent entre deux images. Restreindre le contrôle « aux
pixels qui ont changé » ne marche donc pas — il faut le restreindre **au rectangle réellement
dessiné**, dérivé de `ORIGINE_X/Y` et de la taille de la grille.

**Conclusion.** Imiter Chunsoft est faisable dès lors qu'on traite leur travail comme une
spécification mesurable plutôt que comme un style à ressentir. Le coût est qu'il faut le faire
personnage par personnage : la bouche de Politoed ne se transpose pas sur Hariyama.
