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

Design respecté d'après l'artwork officiel fourni : **carapace basse et large
en vitrail polygonal** (cellules bleu nuit, violettes, roses, vertes, cyan
séparées par des nervures menthe claires, motif d'éclair jaune sur le dessus),
**fourrure vaporeuse menthe/crème** en mèches pointues tout autour de la
carapace, **petite tête bleu nuit** à l'avant avec œil cerclé de rouge à iris
cyan et bouche en zigzag, **queue-panache fourchue** claire relevée à l'arrière.
Pas de pattes visibles : le corps repose au sol. Aucun détail inventé.

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

## Portraits (20 expressions, base verrouillée)

Format canonique **40 x 40**, palette indexee de **18 couleurs**, alpha
strictement binaire, aucun anti-aliasing, aucun pixel semi-transparent.

Methode employee (celle d'un spriter SpriteCollab, pas une illustration
reduite) :

1. **une** tete canonique est dessinee pixel par pixel dans `outils/portraits.py` ;
2. cette base est **verrouillee** ;
3. les 20 expressions ne repeignent que la **fenetre faciale** `(8,17)-(32,34)` —
   yeux, paupieres, sourcils, bouche, joues ;
4. tout ce qui sort de cette fenetre est recopie bit a bit depuis la base ;
5. un **controle final** compare chaque portrait au portrait `Normal` hors
   fenetre faciale et interrompt la generation si un seul pixel differe.

Resultat verifie : tete identique au pixel pres dans les 20 cases, fond en
aplat parfaitement uniforme et identique partout, palette stable d'une
expression a l'autre.

Expressions : Normal, Heureux, Tres heureux, Triste, En colere, Tres en
colere, Surpris, Choque, Effraye, Inquiet, Confus, Pensif, Determine,
Combatif, Fatigue, Endormi, Gene, Embarrasse, Douleur, Decu — mappees sur
les slots officiels SpriteCollab, chacune avec sa variante miroir `^`, plus
la feuille `Portraits.png`.

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
