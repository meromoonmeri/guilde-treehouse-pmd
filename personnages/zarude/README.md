# Zarude #0893 — sprite PMD au format SpriteCollab

![Les huit directions](apercu_directions.png)

Sprite de donjon de **Zarude**, dessin original en pixel art (13 couleurs), livré dans le format des dépôts
PMDCollab / SkyTemple avec le **set donjon complet** : Idle, Walk, Sleep, Hurt, Attack, Charge, Shoot, Strike,
Sing, Swing, Double, Rotate, Hop.

Zarude n'existe pas sur SpriteCollab. Le sprite est donc construit **sur le squelette d'animation de Rillaboom
#0812** (forme 0, baronessfaron, CC BY-NC 4.0), le grand singe le plus proche de sa carrure : mêmes animations,
mêmes cases, mêmes durées, mêmes `RushFrame` / `HitFrame` / `ReturnFrame`, même déplacement de l'ancre à chaque
image, même sens de rotation pour Swing et Rotate, même gabarit d'ombre. Aucun pixel de Rillaboom n'est repris.

![Contrôle de gabarit](apercu_reference.png)

## Ce qui est livré

| Fichier | Contenu |
| --- | --- |
| `AnimData.xml` | Déclaration SpriteCollab : `ShadowSize` 2, et pour chaque animation nom, index officiel, case, `RushFrame` / `HitFrame` / `ReturnFrame`, durées en 1/60 s. `Strike` est un `CopyOf` d'`Attack`. |
| `<Anim>-Anim.png` | Feuille d'images : une colonne par image, une ligne par direction (Bas, Bas-droite, Droite, Haut-droite, Haut, Haut-gauche, Gauche, Bas-gauche ; `Sleep` n'a qu'une ligne). RGBA, alpha 0 ou 255. |
| `<Anim>-Offsets.png` | Repères du jeu : noir = tête, vert = centre, rouge = main gauche, bleu = main droite (couleurs additionnées quand ils se superposent). |
| `<Anim>-Shadow.png` | Pixel blanc = ancre du sprite ; vert / rouge / bleu = gabarit d'ombre petite / normale / grande (celui de la référence). |
| `nuit/<Anim>-Anim.png` | Mêmes feuilles avec le filtre nuit des salles de la guilde (`night()` de `source/rebuild_kit.py`). Offsets et Shadow sont inchangés. |
| `zarude.aseprite` | Fichier Aseprite animé : 8 calques (une direction chacun), les 12 animations bout à bout avec leurs durées (103 images), une étiquette par animation. |
| `apercu.png` | Planche de contrôle × 2 : toutes les images de chaque animation (directions Bas et Droite pour Walk / Attack / Sing). |
| `apercu_directions.png` | Walk image 1 dans les huit directions, × 4. |
| `apercu_reference.png` | Zarude au-dessus de Rillaboom, même case, même ancre : contrôle du gabarit. |
| `apercu_marche_attente.gif`, `apercu_attaque_hurlement.gif` | Lecture animée sur le parquet de la guilde (Walk / Idle, puis Attack / Sing, quatre directions). |
| `apercu.html` | Lecteur hors ligne : choix de l'animation, zoom, ombre, repères, grille de 24 px, variante nuit. |
| `kit.json` | Cases, durées, index, notes de composition, palette, orientations dessinées et miroirs. |
| `controle_qualite.json` | Résultat du vérificateur. |
| `credits.txt` | Crédits au format SpriteCollab (licence CC BY-NC 4.0, référence Rillaboom citée). |

### Cases et cadences

| Animation | Index | Case | Images | Durée | Pose |
| --- | --- | --- | --- | --- | --- |
| Walk | 0 | 48 × 64 | 4 | 44 ticks | repos / pas gauche / repos / pas droit, le corps descend d'un pixel sur les pas |
| Attack | 1 | 72 × 88 | 13 | 26 ticks | bras levés au-dessus de la tête, frappe au sol accroupi avec griffures à l'impact, retour · Rush 2 · Hit 3 · Return 6 |
| Strike | 2 | — | — | — | copie d'Attack |
| Shoot | 3 | 48 × 64 | 11 | 26 ticks | rebond, puis accroupi bras tendus devant · Hit 1 · Return 3 |
| Sing | 4 | 48 × 64 | 16 | 48 ticks | hurlement : bras à demi levés, six coups de poing sur le poitrail, tête levée bras au ciel avec ondes · Hit 5 · Return 10 |
| Sleep | 5 | 40 × 40 | 2 | 65 ticks | couché sur le flanc, respiration |
| Hurt | 6 | 48 × 72 | 2 | 10 ticks | bras écartés (rejetés en arrière de profil), tête baissée, étincelles, recul de la référence |
| Idle | 7 | 40 × 64 | 1 | 32 ticks | pose de repos |
| Swing | 8 | 88 × 104 | 9 | 16 ticks | tour complet en décrivant un cercle (l'image i regarde la direction d − i) · Hit 5 · Return 5 |
| Double | 9 | 72 × 88 | 16 | 36 ticks | accroupi, aller-retour latéral de l'ancre |
| Hop | 10 | 48 × 104 | 10 | 24 ticks | accroupi, saut jusqu'à 23 px, réception accroupie · Hit 9 |
| Charge | 11 | 48 × 64 | 10 | 20 ticks | repos, tremblement d'un pixel · Hit 5 · Return 9 |
| Rotate | 12 | 48 × 64 | 9 | 18 ticks | tour complet sur place · Hit 8 |

Toutes les cases sont celles de Rillaboom, sauf **Swing** (80 × 96 chez lui) : la queue et les bras de Zarude
débordaient d'un pixel dans le cercle, la case est agrandie d'un pas de 8. L'ancre au repos est en
(largeur / 2, hauteur / 2 + 4) comme dans tout le dépôt.

## Méthode : dessiner des pièces, recopier un squelette

Le constructeur `source/personnages/build_zarude_sprite.py` et ses pièces `source/personnages/zarude_pieces.py` :

1. **Palette fixée d'abord** : 13 couleurs (contour noir, trois gris-violet du pelage, crinière, deux gris du
   masque et du poitrail, blanc des crocs, rouge et orange de l'œil, trois verts des lianes). Rien n'en sort.
2. **Pièces dessinées à l'échelle 1:1** en bitmaps ASCII pour cinq orientations (Bas, Bas-droite, Droite,
   Haut-droite, Haut) : tête, crinière, torse, queue, deux jambes, quatre variantes de bras (au repos, levé, tendu,
   poing au poitrail, poussée), lianes du dos, griffures, ondes du hurlement. Gauche, Haut-gauche et Bas-gauche
   sont des **miroirs exacts**, comme dans les sprites officiels (dir 6 = miroir de dir 2). Les membres du côté
   éloigné sont assombris d'un cran.
3. **Chaque image est un assemblage** : les pièces sont déplacées ou raccourcies de quelques pixels (pas de
   marche, accroupissement, bras levés) ; jamais redessinées image par image. La cohérence entre images est donc
   mécanique et une retouche d'une pièce se propage partout.
4. **Le squelette vient de Rillaboom** : `AnimData.xml` de la référence (`source/personnages/reference/0812/`,
   copie intacte), et pour chaque case le déplacement du pixel blanc de sa feuille Shadow, relu tel quel. C'est
   ce qui donne la charge de l'attaque, la secousse de Charge, le cercle de Swing, l'aller-retour de Double et la
   parabole de Hop ; les feuilles de Rillaboom ne servent qu'à ce plan.
5. **Réassemblage** avec le pipeline commun aux sprites du kit (`sheet`, `write_aseprite`, aperçus, filtre nuit).

Le vérificateur `source/personnages/verify_zarude_sprite.py` rejoue les contrôles du SpriteBot (index imposés,
`CopyOf`, tailles de feuilles, 1 ou 8 lignes, durées, alpha binaire, un seul pixel blanc et un seul jeu de repères
par case, 15 couleurs au plus) et ajoute : squelette identique à Rillaboom (durées, Rush/Hit/Return, cases
agrandies seulement par pas de 8, déplacement d'ancre et gabarit d'ombre à chaque image), miroirs exacts des
directions gauches, Swing / Rotate tournant d'une direction par image, Idle et Charge égaux à la pose de repos de
Walk, palette ⊂ pièces, marge d'un pixel, repères dans le dessin, silhouettes nuit = jour, Aseprite ↔ feuilles,
`kit.json`, `credits.txt` et aperçus présents.

```
python3 source/personnages/build_zarude_sprite.py     # ~8 s, déterministe
python3 source/personnages/verify_zarude_sprite.py    # « OK — 13 animations, 810 cases contrôlées, 13 couleurs, ShadowSize 2, squelette Rillaboom respecté »
```

## Limites

- **Un seul spriter, pas de relecture humaine.** Le dessin est lisible en jeu (silhouette, masque, lianes,
  queue) mais reste plus schématique que les sprites du dépôt officiel, qui passent par plusieurs relectures.
  Les pièces sont faites pour être retouchées : corriger `zarude_pieces.py` puis relancer le constructeur.
- **Idle à une image**, comme Rillaboom : pas de respiration au repos. Facile à ajouter en dupliquant la logique
  de Walk (durées à changer dans `ANIM_ORDER` / `Builder.build`).
- **Pas sur SpriteCollab.** Le dépôt n'accepte que des sprites relus par sa communauté ; celui-ci n'y a été ni
  soumis ni approuvé. Licence choisie : CC BY-NC 4.0, comme la référence.
