# Terapagos #1024 — pack de sprites PMD

Pack complet suivant la méthode et les conventions **PMD Sprite Collab**.
Aucun artwork haute résolution : tout est produit pixel par pixel par un
moteur paramétrique (`outils/`), sans anti-aliasing, avec contour dur et
palette indexée à 3 tons par matière.

**[Ouvrir l’aperçu interactif](apercu.html)**

## Formes

| Code | Forme | Sprites | Portraits |
|------|-------|---------|-----------|
| `0000` | **Teracristal (Tortue de Cristal)** — forme de référence | `sprite/0000` | `portrait/0000` |
| `0001` | Normale | `sprite/0001` | `portrait/0001` |
| `0002` | Stellaire | `sprite/0002` | `portrait/0002` |

Design respecté : dôme de cristal bleu à facettes portant sept pointes,
liseré doré à la base de la carapace, corps et tête ivoire, yeux ambre à
pupille sombre, quatre pattes courtes, petite queue cristalline. Aucun
détail inventé hors du design officiel.

## Cadre et ancrage

- Canvas **48 × 48** pour toutes les frames, toutes les animations.
- Point d’ancrage unique **(24, 40)** = centre des pieds, identique partout.
- Ombre elliptique PMD ancrée au sol, indépendante du saut.
- 8 directions dans l’ordre SpriteCollab : `S, SE, E, NE, N, NO, O, SO`
  (une ligne par direction, une colonne par frame).

## Animations (22)

`Idle, Walk, Run, Attack, Shoot, Special, Strike, Charge, Withdraw, Jump,
Hurt, Faint, Sleep, Wake, Dizzy, Fear, Rage, Joyous, Sad, Shock, Pose,
Determination`

Les animations de déplacement et de combat sont rendues sur les 8 directions ;
les animations d’état/émotion sont rendues face caméra, comme dans les
références PMD. Les durées sont en ticks (1/60 s) et déclarées dans
`AnimData.xml` avec `RushFrame`, `HitFrame` et `ReturnFrame`.

Par animation et par forme :

- `<Anim>-Anim.png` — feuille frames × directions ;
- `<Anim>-Offsets.png` — décalages PMD (rouge tête, vert corps, bleu/blanc mains) ;
- `<Anim>-Shadow.png` — position de l’ombre ;
- `frames/<Anim>/<Anim>-<DIR>-<NN>.png` — frames individuelles prêtes à l’emploi.

## Portraits (20 émotions + miroirs)

Format canonique **40 × 40**, cadrage PMD (visage large, dôme débordant en
haut). Émotions SpriteCollab : `Normal, Happy, Pain, Angry, Worried, Sad,
Crying, Shouting, Teary-Eyed, Determined, Joyous, Inspired, Surprised, Dizzy,
Special0-3, Sigh, Stunned`, chacune avec sa variante miroir `^`.
Feuille regroupée : `Portraits.png` (grille 5 × 8).

## Fonds

Grammaire des fonds de portrait PMD : aplat de couleur unie coupé en deux
valeurs par une diagonale nette, plus un liseré d’un pixel. Aucun dégradé,
aucun flou, aucun élément décoratif. La teinte suit l’émotion (froide au
repos, chaude pour les émotions positives, sourde pour les négatives).

## AssetSprite

`assetsprite/terapagos_<code>_sprites.png` : planche unique par forme,
grille **48 × 48 strictement jointive**, animations empilées sans
chevauchement ni marge, sans texte ni watermark. La table de découpe
(offsets, colonnes, lignes de chaque animation) est dans `terapagos.json`.

## Régénérer

```bash
cd outils
python3 generer_sprites.py   # feuilles d'animation + AnimData.xml + frames
python3 portraits.py         # portraits et feuilles d'émotions
python3 paquet.py            # planches AssetSprite, terapagos.json, apercu.html
```

- `moteur.py` — primitives pixel, palette, contour par dilatation.
- `modele.py` — anatomie de Terapagos, 8 directions, expressions.
- `animations.py` — grammaire d’animation (frames, durées, ticks).
