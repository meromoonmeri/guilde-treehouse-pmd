# Politoed #0186 — pack complet d'animations PMD

Ce lot fournit le dossier multi-sheet SpriteCollab/SpriteBot dans
[`sprite/0186/`](../../sprite/0186/) et l'archive prête à soumettre
[`sprite-0186.zip`](../../sprite-0186.zip).

Le dossier est directement importable dans PMDO via **Char Sprites > Import**.
PMDO peut ensuite l'exporter en single-sheet ou en données moteur WAN. Aucun
binaire PMDO/WAN n'est versionné ici : la source multi-sheet est le format
maître recommandé par le guide et l'archive est autonome.

## Couverture

Les animations de donjon existantes sont conservées avec leurs pixels, ombres
et timings officiels :

- `Walk` (0), `Attack` (1), `Strike` (2, copie de `Attack`), `Shoot` (3),
  `RearUp` (4), `Sleep` (5), `Hurt` (6), `Idle` (7), `Swing` (8),
  `Double` (9), `Hop` (10), `Charge` (11), `Rotate` (12) ;
- les 22 animations starter ajoutées pour la couverture complète SpriteBot :
  `EventSleep`, `Wake`, `Eat`, `Tumble`, `Pose`, `Pull`, `Pain`, `Float`,
  `DeepBreath`, `Nod`, `Sit`, `LookUp`, `Sink`, `Trip`, `Laying`,
  `LeapForth`, `Head`, `Cringe`, `LostBalance`, `TumbleBack`, `Faint`,
  `HitGround` (indices 13 à 34).

Les feuilles suivent le format PMD :

- `Name-Anim.png` : sprites visibles, huit directions lorsque l'animation le
  demande et une ligne pour les animations à direction unique ;
- `Name-Offsets.png` : repères tête noire, corps vert, main droite rouge et
  main gauche bleue ;
- `Name-Shadow.png` : ombre PMD avec les quatre niveaux de couleur ;
- `AnimData.xml` : dimensions, indices, durées et marqueurs d'attaque.

L'ordre des directions est celui du guide : bas, bas-droite, droite,
haut-droite, haut, haut-gauche, gauche, bas-gauche. Les dimensions des nouvelles
frames sont paires et multiples de 8 pour faciliter l'import SkyTemple/PMDO.

## Méthode artistique

La présentation [How to Make PMD Sprites for
SkyTemple](https://docs.google.com/presentation/d/1SH2onT2yttVuznohr4yi3Uh07y4lNLcLlHGT_YWNGmo/edit?usp=drivesdk)
a été suivie pour la couverture et la construction :

1. partir d'un sprite PMD de même espèce et de ses huit angles, plutôt que de
   générer une silhouette isolée ;
2. réutiliser les poses canonique Politoed (`Walk`, `Idle`, `Attack`, `Hurt`,
   `Sleep`) comme bases cohérentes ;
3. construire chaque mouvement par transformations entières nearest-neighbor,
   déplacements pixel par pixel et séquences lisibles : respiration, saut,
   chute, roulade, sommeil et réveil ;
4. aligner chaque pose sur la même base d'ombre, puis calculer les offsets
   séparément ;
5. vérifier à la taille native, sur les quatre angles principaux et dans
   PMDO avant une soumission SpriteBot.

Les nouveaux pixels ne sont pas une génération IA brute : le générateur
`build_sprites.py` ne redessine pas le Pokémon avec une autre espèce et ne
resample aucune image. Il part des pixels Politoed canoniques et conserve leur
palette. Les études d'animation ont donc la cohérence de volume, de boucle de
tête et de couleurs du sprite existant.

## Provenance et crédits

La base officielle vient de
[PMDCollab/SpriteCollab](https://github.com/PMDCollab/SpriteCollab), état
`132ddf5673927e9a7af7f18b15d46f3ccefc74c` dans
`source/sprites_politoed/canonical/`. La ligne `CHUNSOFT / CUR` d'origine est
préservée dans `sprite/0186/credits.txt`. Les animations indices 13–34 sont
attribuées à `meromoonmeri / Arena.ai Agent` dans cette même fiche ; elles ne
sont pas présentées comme des frames Chunsoft officielles.

Le guide est crédité à Emmuffin. Les droits, crédits et règles d'utilisation
de SpriteCollab restent applicables à la base officielle. Vérifier le résultat
dans la version PMDO ciblée avant de publier une soumission.

## Reproduction et contrôle

Depuis la racine :

```bash
python -m pip install -r source/requirements.txt
python source/sprites_politoed/build_sprites.py
python source/sprites_politoed/verify_sprites.py
```

La génération recopie la base canonique, ajoute les animations 13–34, écrit
les trois feuilles de chaque animation, produit `AnimData.xml`, recalcule
`credits.txt` et reconstruit `sprite-0186.zip`.
