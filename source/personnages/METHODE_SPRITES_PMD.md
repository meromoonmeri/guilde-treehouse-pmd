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
6. **Aucun pixel repeint** : la palette finale est exactement celle des unités (13 couleurs).

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

## 6. Pour un personnage sans base (Zarude)

Zarude n'a pas de sprite sur SpriteCollab et aucune unité à composer. Plan proposé, à valider avec
l'utilisateur avant de produire le lot :

1. **Références** : télécharger un sprite officiel proche en gabarit et en pose (bipède à longs bras :
   Pichu #0172 pour la structure des fichiers, mais un modèle plus proche du corps de Zarude pour les
   poses — Infernape, Zangoose, ou un singe/félin du dépôt). Relever cases, durées, déplacement de
   l'ancre et repères par image : **ces métadonnées se recopient**, c'est le squelette d'animation.
2. **Palette** : fixer d'abord 15 couleurs max (verts du feuillage, gris du corps, rouge des yeux, noir,
   blanc) et ne jamais en sortir.
3. **Dessiner la pose de repos** en pixel art à l'échelle réelle (Walk ~ 32 × 40 pour un bipède moyen),
   direction Bas, puis Droite, Haut, Bas-droite, Haut-droite ; obtenir Gauche, Bas-gauche, Haut-gauche
   par **miroir exact** (les originaux du dépôt le font : dir 6 = miroir de dir 2). Le générateur
   d'images peut servir de brouillon de pose à grande taille, à repixelliser à la main ensuite ;
   ce qui compte est le résultat à 1:1, pas le brouillon.
4. **Animer par déplacement de pièces**, pas en redessinant chaque image : découper la pose en pièces
   (tête, torse, bras, jambes, feuillage) et les déplacer/pivoter de quelques pixels selon le squelette
   relevé au point 1. C'est ce que font les spriters du dépôt ; ça garantit la cohérence entre images.
5. **Réassembler** avec le même pipeline que Falinks (fonctions `render`, `sheet`, `write_animdata`,
   `write_aseprite`, aperçus) et **vérifier** avec le vérificateur adapté.
6. Licence : dessin original → indiquer la licence choisie par l'utilisateur dans `credits.txt`
   (le dépôt SpriteCollab attend CC BY-NC 4.0 pour une éventuelle soumission).

## 7. Fichiers utiles

- `source/personnages/build_falinks_sprite.py` — constructeur (réutiliser `extract`, `merge_tracks`,
  `render`, `sheet`, `write_animdata`, `write_aseprite`, `gif`, `player_html`).
- `source/personnages/verify_falinks_sprite.py` — vérificateur (règles SpriteBot + composition).
- `source/personnages/reference/0870/0002`, `0003` — unités d'origine.
- `source/portraits/` — même démarche pour les portraits (retouche pixel d'une base, vérificateur).
- `source/rebuild_kit.py` — `night()`, `ase()`, `font()` partagés avec le reste du kit.
