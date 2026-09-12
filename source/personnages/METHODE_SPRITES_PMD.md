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

## 14. Essai mesuré : faire dessiner les images par un générateur d'images

Proposition de l'utilisateur : employer le générateur d'images en l'« éduquant » à tout conserver
et à n'ajouter que l'ouverture de la bouche. Testé sérieusement plutôt que refusé d'emblée ;
`generateur_eat_essai.py` rejoue l'essai et écrit `essais/rapport_generateur.json`.

**Sortie brute** (consigne pourtant très contrainte : « même sprite au pixel près, aucune couleur
nouvelle, pas d'anticrénelage ») :

| Mesure | Résultat | Limite |
| --- | --- | --- |
| couleurs | **287** | 15 |
| pixels du corps conservés | **18,7 %** | 100 % attendus |
| pixels modifiés dans les yeux | **45** | 0 demandés |

Le générateur ne conserve pas : il **redessine de mémoire** une image qui ressemble à l'entrée.

**La discipline de post-traitement** est ce qui rend l'idée à moitié défendable, et elle est
réutilisable telle quelle si un futur modèle fait mieux :
1. rééchantillonner sur la grille exacte en **moyenne de bloc** (`Image.BOX`), jamais en nearest —
   le générateur dessine sa propre grille, décalée ; un nearest échantillonne au hasard dans les
   blocs et détruit tout (première tentative : 18,7 % de conservation, faussement attribuée au
   modèle alors qu'une partie venait de mon rééchantillonnage) ;
2. rabattre chaque pixel sur la couleur la plus proche **de la palette d'origine** ;
3. **masquer par zone** : ne reprendre du générateur que les lignes concernées, et remettre
   l'original partout ailleurs.

Après discipline : 14 couleurs, 92,1 % conservé — mais **2 règles de grammaire sur 4 seulement** :
7 pixels de gorge à vif sur la peau (pas de cerne noir), 1 saut de valeur clair→sombre.

**Conclusion.** Utilisable comme *source d'idées de forme*, pas comme producteur d'images
livrables : la discipline ramène la palette et la zone, mais ne répare pas la grammaire. Il reste
une reprise manuelle — et à ce stade on a refait le travail de `dessine_eat_politoed.py` en moins
bien et sans contrôle. Un résultat négatif mesuré vaut mieux qu'un refus de principe.

## 15. Les fonds de portrait sont canoniques (correction)

Erreur signalée par l'utilisateur, et bien réelle : les fonds produits par
`build_portraits_manquants.py` n'étaient pas canoniques. Ils étaient **dégradés et épousaient la
silhouette du décor d'origine**, ce que ne fait aucun portrait officiel.

**Ce que sont vraiment les fonds PMDCollab**, relevé sur les huit jeux de référence :

- une **paire de couleurs fixe par émotion**, la même d'un Pokémon à l'autre (aux retouches
  d'auteur près, ±3 par canal) — `Happy` = `#ffffaf` / `#ffe777`, `Crying` = `#6f7fb7` / `#9fd7ef`… ;
- une **géométrie imposée** : ciel plein sur toute la largeur jusque vers `y = 8`, sol plein en bas,
  et entre les deux une bande de ~4 lignes en **damier** (`1.1.1.1.`), jamais un dégradé continu ;
- une seule exception, `Shouting`, dont le fond est radial (rayons depuis le visage).

Vérifié en dumpant `0674/Crying`, `0674/Normal`, `0674/Sad` ligne à ligne : lignes 0-7 pleines de
ciel, 8-12 en damier, bas plein de sol.

**Détection du décor d'origine.** L'ancienne méthode (propagation depuis le bord en n'autorisant que
les couleurs absentes du centre) ne trouvait que 14 à 30 % du fond. La corriger a demandé de
**réunir deux critères** :
1. les **couleurs canoniques connues** — toutes les bases sont des portraits `Normal`, donc leur
   décor est `#77c7d7` / `#e7f7b7` / `#d7ffbf` à ±6 ;
2. les couleurs qui **bordent l'image sans jamais apparaître au centre**, pour les auteurs qui ont
   employé une teinte hors de la paire (le sol de Pawmot est plus jaune que la référence).

Pris séparément : 6 % (couleurs canoniques seules, sur Pawmot) et 14-30 % (bord seul). Réunis :
14 à 34 %, et surtout un fond correct là où le personnage ne remplit pas le cadre. Hariyama et
Ambipom restent bas parce que leur personnage occupe presque toute l'image — c'est légitime.

**Contrôle.** `verify_portraits_manquants.py` vérifie désormais la canonicité : teinte majoritaire du
ciel et du sol égale à la valeur officielle de l'émotion, ciel en bandes horizontales unies (ce qui
rejette tout dégradé), et bande de transition contenant bien les deux teintes. Piège rencontré : les
effets (goutte de sueur, larmes, étincelles de `Joyous`) sont dessinés **par-dessus** le fond et
peuvent dominer une ligne entière ; le contrôle raisonne donc en teinte **majoritaire** et tolère une
ligne aberrante, au lieu d'énumérer des boîtes d'effet qui seraient vite fausses.

## 16. Généraliser le dessin à la main, et livrer au format officiel

Dernière étape : dessiner la bouche de quatre Pokémon de plus (`dessine_eat_officiel.py`) et
produire une arborescence déposable sur SpriteCollab (`source/export_spritecollab.py`).

**Un trait par personnage, jamais une recette.** Le § 13 disait que la bouche de Politoed ne se
transpose pas ; c'est confirmé. Il faut dumper chaque case `Idle` en ASCII et repérer ce qui fait
le personnage : la bouche en dents d'Ambipom, la grande gueule rouge de Gible, le museau de
Pawmot, et pour Dedenne — 17 px de haut — une ouverture de deux pixels, c'est tout ce que la
taille permet sans bouillie. Les dessins sont des grilles de caractères avec des **rôles de
couleur** (`gorge`, `dent`, `levre`) résolus dans la palette du sprite : le constructeur refuse
au démarrage toute teinte absente de l'original, ce qui a immédiatement attrapé une palette
Dedenne inventée de mémoire.

**Le seuil d'ombrage doit être mesuré, pas supposé.** Premier contrôle écrit : « la teinte la plus
claire ne touche jamais la plus sombre ». Il rejetait des dessins corrects. En mesurant l'écart de
valeur (somme RVB) entre pixels voisins sur les `Eat` officiels : **487 chez Pichu, 430 chez
Riolu**. Les artistes s'autorisent donc des contrastes francs. Le contrôle est devenu « écart ≤ 487 »
— et il a alors trouvé de vraies fautes (548 sur Pawmot, 574 sur Dedenne, dents blanches posées
contre du brun sombre), corrigées en bordant de la teinte intermédiaire.

Deux pièges de contrôle, tous deux résolus en restreignant la mesure :
- comparer des **familles de teintes sans rapport** (le bleu de peau de Gible est plus clair que
  son rouge de gorge) → ne comparer que les couleurs réellement posées par le dessin ;
- mesurer des contrastes **du sprite d'origine** (le museau blanc de Pawmot jouxte déjà un brun à
  548 d'écart) → exiger que les deux pixels de la paire soient dans la zone dessinée. On ne peut
  pas être tenu responsable de ce qu'on n'a pas peint.

**L'export officiel** (`spritecollab/`) ne contient que ce que connaît le dépôt : `AnimData.xml`,
les trois feuilles par animation, `credits.txt`, et les portraits 40 × 40. Détails de forme
reproduits sur les fichiers officiels : **CRLF**, indentation à **deux espaces**, déclaration
`<?xml version="1.0"?>` sans espace avant `?>`. Sans importance pour SkyTemple, mais un diff propre
compte pour une contribution. Les `credits.txt` conservent toutes les lignes d'origine et
reprennent la licence déjà déclarée sur le sprite.

## 17. Le générateur d'images, employé pour de bon

Les § 14 et 16 concluaient que le générateur n'était pas exploitable. C'était vrai avec un cadrage
serré sur un rectangle de bouche ; ça ne l'est plus quand on lui envoie **le sprite entier** et
qu'on discipline la sortie. `eat_generateur.py` produit ainsi trois `Eat` livrés.

**Protocole.** Le PNG de la case `Idle` officielle, agrandi ×24 sur fond magenta, est soumis avec
la consigne : « même sprite, en train de manger, bouche ouverte, mains levées ». Cinq Pokémon
essayés, mesurés après rabattement sur la palette :

| | conservation | verdict |
| --- | --- | --- |
| Pancham | 87,1 % | retenu |
| Slurpuff | 87,0 % | retenu |
| Gardevoir | 80,6 % | retenu |
| Hariyama | 68,5 % | **écarté** — visage déformé |
| Miltank | 15,1 % | **écarté** — sprite détruit |

Le contrôle visuel confirme la mesure : sous ~80 %, le personnage n'est plus lui-même. Un seuil
n'a d'intérêt que s'il sait dire non ; deux des cinq sont rejetés.

**La discipline reste indispensable** — grille exacte en moyenne de bloc, palette rabattue (178 à
471 couleurs en sortie, 15 autorisées), masque limité au rectangle de la bouche.

**Choisir la zone par la mesure, pas à l'œil.** Les rectangles repérés à la main donnaient des
écarts de valeur de 591 (Gardevoir) et 612 (Pancham). Une recherche exhaustive sur les rectangles
plausibles retient le plus grand qui reste sous le plafond de contraste.

**Le plafond de contraste est propre à chaque sprite.** Le § 16 avait fixé 487, relevé sur Pichu et
Riolu. Faux comme référence absolue : mesuré case par case, **chaque sprite officiel le dépasse** —
Gardevoir 591, Pancham 650, Slurpuff 543, Politoed 606. On compare donc l'ajout au contraste
maximal du personnage concerné, ce qui est plus juste et plus sévère quand le sprite est doux.

**Trois pièges de mesure**, tous dus à des effets dont le générateur n'est pas responsable :
1. le `squash` décale l'ensemble d'un pixel → comparer **silhouette contre silhouette** (recadrée),
   sinon on mesure 38 % et on ne juge que le décalage ;
2. le trajet des mains vient de `move_limbs` → l'exclure du calcul de conservation ;
3. le contraste natif du sprite → n'évaluer que les paires de pixels **dans** la zone dessinée.

## 18. Fonds de portrait : la géométrie était fausse (correction du § 15)

Le § 15 avait relevé les bonnes **couleurs** par émotion, mais posé une géométrie inventée :
horizon à `y = 8`, damier de 4 lignes. L'utilisateur a renvoyé à **Magcargo #0219**, et la mesure
lui donne raison — le résultat ne ressemblait à aucun portrait officiel malgré les bonnes teintes.

**Méthode de mesure.** Le décor ne s'isole pas à l'œil : sur ces portraits le personnage occupe
presque tout le cadre et le fond n'apparaît que dans les coins. On l'isole en empilant les dix
émotions d'un même Pokémon et en gardant les pixels qui **changent d'une émotion à l'autre** : le
personnage est constant, le décor non. Puis, pour chaque teinte du décor, on relève les lignes où
elle apparaît seule et celles où les deux coexistent (le damier) :

    0219 Happy : clair pur 0-21 · damier 16-23 · sol pur 18-39
    0674 Happy : clair pur 0-15 · damier 16-23 · sol pur 24-39
    0282 Happy : clair pur 0-12 · damier 13-21 · sol pur 22-39

**Le partage est au milieu de l'image, vers `y = 16`, et le damier est large — environ 8 lignes.**
`HORIZON = 16`, `DAMIER = 8` au lieu de 8 et 4.

**Contrôle revu, deux fois.** Vérifier « le ciel descend au moins jusqu'au tiers » échoue sur
Hariyama, dont le personnage remplit le cadre : son décor n'existe qu'en lignes 0-8 et 30-39, avec
rien au milieu. On contrôle donc **chaque ligne de décor selon sa hauteur** (ciel au-dessus de
l'horizon, sol sous le damier), en tolérant une ligne aberrante — les étincelles de `Joyous`
peuvent dominer une ligne entière puisqu'elles sont dessinées par-dessus le fond.

**Leçon générale.** Deux versions de suite se sont trompées sur ce fond, chaque fois parce qu'une
structure a été supposée au lieu d'être mesurée. Quand l'utilisateur dit « ce n'est pas canonique »
alors que les couleurs sont bonnes, c'est la **géométrie** qu'il faut aller relever sur les
originaux, en isolant le décor par la variance entre émotions plutôt qu'à l'œil.

## 19. Portraits en deux couches : fond canonique par code, personnage par générateur

Architecture proposée par l'utilisateur — « fais les fonds canoniques, on placera les Pokémon
par-dessus » — et c'est la bonne. `portraits_generateur.py` la met en œuvre.

**Le fond n'a pas besoin du générateur.** Vérification faite avant de lui demander quoi que ce
soit : sur les 245 pixels de décor visibles dans les coins d'un portrait officiel, une
reconstruction par code aux couleurs canoniques est **identique au pixel près (245/245)**. Le
fond est donc entièrement reconstruit, jamais négocié.

**Le générateur ne sert plus qu'à l'expression.** On lui envoie le `Normal` officiel, on découpe
le personnage dans sa sortie, on le pose sur le fond reconstruit. Palette rabattue sur celle du
portrait officiel au passage.

**Le découpage se fait par les teintes, pas par la géométrie.** Trois tentatives :
1. réutiliser le masque de fond de l'officiel → faux, le générateur change la pose ;
2. redétecter le fond par propagation depuis le bord sur sa sortie → laisse les **poches
   enfermées** (le ciel coincé entre les oreilles de Capidextre ne touche aucun bord) ;
3. **retenu** : est du fond tout pixel portant une teinte de décor du portrait officiel — celles
   qui occupent son fond et que le personnage n'emploie jamais — qu'elle touche le bord ou non.

Résultat mesuré : fond canonique exact (438/438, 452/452, 288/288, 372/372 pixels), **zéro
résidu** du ciel d'origine, 13 à 14 couleurs.

**Ce que le générateur réussit et rate.** Sur dix expressions produites pour Capidextre, deux ont
été validées par l'utilisateur (`Inspired`, `Teary-Eyed`) et huit rejetées — « ça fait IA ». Il
lisse les traits et perd le style Chunsoft dès que l'expression est appuyée. En revanche il est
précieux quand la retouche à la main échoue : les portraits de Hariyama produits par opérations
sur les yeux étaient glitchés et figés dans la même pose ; le générateur lui donne enfin une
expression et une pose différentes.

**À retenir :** demander au générateur ce qu'il fait bien (une expression), pas ce que le code
fait exactement (un fond canonique). Et soumettre chaque sortie à l'œil de l'utilisateur : le
taux de conservation ne dit rien du « ça fait IA ».

## 20. Un fond vraiment propre demande DEUX critères (correction du § 19)

Le § 19 découpait le personnage par les teintes de décor. L'utilisateur a vu qu'il restait
« des bouts de couleur dans les fonds » — et il avait raison. Deux causes distinctes, qu'aucun
critère unique ne rattrape :

1. **Le générateur déborde la silhouette** et sème des pixels de personnage dans les coins
   (saumon `#f9857e` chez Capidextre, orange `#d68850` chez Hariyama). Ces teintes appartiennent
   aussi au personnage : aucun test de couleur ne peut les distinguer. Seule la **position** le
   peut → hors du masque de silhouette du portrait officiel, on ne reprend **rien** du générateur.
2. **Le générateur peint son ciel à l'intérieur** de la silhouette (entre les oreilles, sur les
   épaules). Ces pixels sont dans la bonne position : seule la **couleur** les trahit → toute
   teinte de décor du portrait officiel trouvée dans la silhouette est rendue au fond.

Les deux ensemble, et seulement les deux ensemble, donnent un fond canonique intégral.

**Le contrôle était circulaire.** L'ancien test vérifiait que « les pixels portant une couleur de
fond sont bien à la bonne place » — il ne pouvait par construction jamais voir un pixel saumon
dans un coin. Refait à l'envers : on parcourt la zone hors silhouette et on exige que **chaque**
pixel soit exactement celui du fond reconstruit. Vérifié sur l'ancienne sortie : le nouveau test
la rejette (26 écarts), la nouvelle passe (0).

**Leçon.** Un contrôle qui part de la couleur pour juger la couleur ne prouve rien. Partir de la
position, qui est indépendante de ce qu'on veut vérifier.

## 21. Terapagos : formes alternatives et repères de membres trompeurs

**Les formes vivent dans des sous-dossiers.** Sur SpriteCollab, `sprite/1024/` contient le sprite
de base *et* un sous-dossier `0001/` pour la forme Terastal, avec son propre `AnimData.xml` et
ses propres portraits. Ce sont deux sprites distincts — celui de Terastal a 15 couleurs contre 10,
un `Idle` de 13 images contre 4, et une animation `SpAttack` que l'autre n'a pas. L'export
reproduit cette imbrication : la clé `"1024/0001"` crée `spritecollab/sprite/1024/0001/`.

**Un repère `lhand` n'est pas toujours une main.** Le contrôle physiologique a rejeté le `Eat` de
Terapagos avec « les appuis au sol ne bougent pas » — à raison. Ses repères `lhand`/`rhand` sont
à `y = 0`, c'est-à-dire **à un pixel du bas de la silhouette** : ce ne sont pas des mains levables
mais les bords de sa carapace. Les déplacer décollait le sprite du sol.

Correctif (`limb_is_a_foot`) : un repère situé dans le **dernier quart de la hauteur** est un
appui, pas un membre — on ne le bouge pas. Terapagos garde donc ses appuis fixes et n'anime que
sa déformation à charnière. Aucun autre Pokémon du lot n'est affecté, leurs mains étant plus haut.

**Trois expressions sur dix écartées.** Sur la forme Terastal, le générateur a produit dix
émotions ; `Shouting`, `Sigh` et `Stunned` ont été rejetées au contrôle visuel — il y perd la
structure de la tête (facettes en bouillie, œil remplacé par un disque blanc). Le taux de
conservation ne l'avait pas signalé : il faut regarder.

## 22. « Fidélité 100/100 » : une base verrouillée se garantit par construction

Cahier des charges très strict de l'utilisateur pour Terapagos Terastal : une seule tête de base,
qui ne bouge pas d'un pixel entre deux cases ; fond strictement identique ; palette figée ; vrai
pixel art ; 20 expressions.

**Le générateur d'images ne peut pas tenir cette exigence, et c'est mesurable.** Sur mes propres
sorties pour ce même Pokémon : la silhouette se déplaçait sur 2 émotions sur 7 (jusqu'à 71 pixels
d'écart) et 12 à 34 % de l'image changeait à chaque fois. Un générateur *redessine* — il ne
retouche pas.

**La garantie doit être structurelle, pas vérifiée après coup.** `planche_terapagos_terastal.py`
part du tableau d'octets de la case officielle, le copie, et ne réécrit **que** les pixels d'une
boîte de 6 × 8 autour de l'œil. Les 1552 autres pixels sont, littéralement, les mêmes octets. Il
n'y a rien à espérer : la tête *ne peut pas* différer.

Résultat : 13 pixels modifiés en moyenne par expression, sur 1600.

**Trouver la bonne boîte demande de dumper la case.** Premier essai avec une boîte à
`(12, 21, 9×10)` : les dessins écrasaient l'œil au lieu de le remplacer, parce que je l'avais
situé à vue. En dumpant la zone en lettres de palette, l'œil est un ovale précis — blanc `m` +
iris cyan `b` en `x 12..16, y 24..29`, bordé du liseré rose `j` en `x 11`. Boîte corrigée à
`(12, 23, 6×8)`.

**Contrôle non déclaratif.** 390 contrôles : hors boîte, comparaison octet pour octet avec
`Normal` ; silhouette identique ; bords du cadre identiques ; palette incluse dans l'officielle ;
aucun pixel semi-transparent ; et toutes les paires d'expressions deux à deux distinctes.

**Sur les 20 expressions du brief**, 16 ont un équivalent dans la nomenclature SpriteCollab et
partent dans une planche 200 × 320 déposable ; les 4 autres (Très en colère, Choqué, Effrayé,
Pensif…) restent dans la planche de travail. Le dépôt officiel n'a que 16 créneaux d'émotion plus
les `Special`.
