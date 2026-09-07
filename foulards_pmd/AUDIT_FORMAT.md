# Audit du format PMDCollab / SpriteCollab

Relevé fait sur un clone partiel de <https://github.com/PMDCollab/SpriteCollab>
(27 starters gen 1‑3, `master`, septembre 2026). Le détail machine est dans
`outils/audit_spritecollab.json`, produit par `outils/audit_format.py`.

Le site <https://sprites.pmdcollab.org> est la vitrine de ce dépôt : il sert les
mêmes fichiers, plus une API GraphQL et des exports ZIP. Ce qu'on télécharge
depuis le site est exactement l'arborescence `sprite/<numéro>/` décrite ici.

---

## 1. Arborescence

```
sprite/0004/                 forme de base (Salamèche)
  AnimData.xml
  Idle-Anim.png  Idle-Offsets.png  Idle-Shadow.png
  Walk-Anim.png  Walk-Offsets.png  Walk-Shadow.png
  … (une triplette par animation)
  credits.txt
  0000/0001/                 chromatique de la forme de base
  0001/                      forme alternative, avec ses propres planches
        0001/                chromatique de cette forme
```

Le niveau racine est la forme normale. Les sous‑dossiers numérotés sont les
formes ; le sous‑dossier `0001` d'une forme est sa version chromatique.
`credits.txt` est un TSV `date / auteur / statut / contact / animations`.
`tracker.json` (1026 entrées) donne les noms anglais, l'état de complétion et
les crédits ; `sprite_config.json` liste les 44 noms d'action canoniques et les
paliers de complétion.

## 2. `AnimData.xml`

```xml
<AnimData>
  <ShadowSize>1</ShadowSize>          <!-- 0 petite, 1 normale, 2 grande -->
  <Anims>
    <Anim>
      <Name>Walk</Name>
      <Index>0</Index>
      <FrameWidth>32</FrameWidth>     <!-- toujours pair -->
      <FrameHeight>32</FrameHeight>
      <Durations><Duration>6</Duration>…</Durations>
    </Anim>
    <Anim>
      <Name>Attack</Name><Index>1</Index>
      <FrameWidth>64</FrameWidth><FrameHeight>64</FrameHeight>
      <RushFrame>2</RushFrame>        <!-- élan -->
      <HitFrame>6</HitFrame>          <!-- impact -->
      <ReturnFrame>8</ReturnFrame>    <!-- retour -->
      <Durations>…</Durations>
    </Anim>
    <Anim><Name>Strike</Name><Index>7</Index><CopyOf>Attack</CopyOf></Anim>
  </Anims>
</AnimData>
```

Points relevés sur les 27 Pokémon :

| Constat | Valeur |
|---|---|
| Animations distinctes rencontrées | 45 noms |
| Présentes chez les 27 | `Walk Attack Shoot Sleep Hurt Idle Swing Double Hop Charge Rotate` |
| Jeu étendu (14 Pokémon sur 27) | + `Eat Faint Wake Pose Pull Pain Float Nod Sit LookUp Sink Trip Laying LeapForth Head Cringe LostBalance Tumble TumbleBack HitGround EventSleep DeepBreath` |
| `<CopyOf>` utilisé par | `Strike`(13) `Twirl`(9) `SpAttack`(7) `Dance`(4) `Shoot`(2) `Rumble`(2) |
| Largeurs de case | 24, 32, 40, 48, 56, 64, 72, 80, 88 px |
| Hauteurs de case | 16 → 112 px |
| `ShadowSize` | 1 (22 Pokémon), 2 (5 Pokémon) |
| Planches réelles (hors `CopyOf`) | 634 |
| Cases totales | 26 744 |

Une animation avec `<CopyOf>` n'a **pas** de PNG : le moteur rejoue la planche
citée. Le nombre de `<Duration>` est égal au nombre de colonnes de la planche.
La durée est exprimée en ticks de 1/60 s.

## 3. Découpage des planches

`<Name>-Anim.png` est une grille régulière : **colonnes = images**,
**lignes = directions**. Vérifié : `largeur % FrameWidth == 0` et
`hauteur % FrameHeight == 0` sur les 634 planches.

* 439 planches ont **8 lignes** (animation orientable)
* 195 planches ont **1 ligne** (animation à direction unique)

### Ordre des directions

Établi empiriquement, en comparant la position du marqueur de tête à celle du
marqueur de centre sur les 8 lignes de plusieurs Pokémon :

| Ligne | 0 | 1 | 2 | 3 | 4 | 5 | 6 | 7 |
|---|---|---|---|---|---|---|---|---|
| Direction | S | SE | E | NE | N | NO | O | SO |

Ligne 2 : marqueur de tête nettement à droite du centre → face à l'est.
Ligne 6 : symétrique → face à l'ouest. Ligne 4 : tête très haute → de dos.
Ligne 0 : tête basse, face caméra.

## 4. `<Name>-Offsets.png`

Même dimensions que la planche d'animation. **Un pixel opaque par marqueur et
par case** : les quatre couleurs apparaissent chacune 26 744 fois sur le corpus,
soit exactement une occurrence par case. Aucun recouvrement dans ce corpus.

| Couleur | RVB | Rôle |
|---|---|---|
| Noir | `0,0,0` | tête — ancre des icônes de statut |
| Vert | `0,255,0` | centre du corps |
| Rouge | `255,0,0` | main du côté droit de l'entité |
| Bleu | `0,0,255` | main du côté gauche de l'entité |

**Le marqueur de tête est une position 3D projetée, pas le sommet du crâne.**
C'est le constat le plus utile de cet audit. Sur Salamèche au repos, il est à
`y = 16` de face et `y = 8` de dos, dans une case de 40 px de haut : la tête
penchée vers la caméra se projette plus bas, la tête qui s'éloigne se projette
plus haut. Le rendu PMD est une vue oblique, et ce marqueur en tient compte.

Conséquence pour tout ce qui doit se fixer au corps (foulard, collier, sac) :
**ce marqueur ne peut pas servir d'ancre tel quel**, sinon l'accessoire glisse
vers le ventre en vue de face et remonte sur le crâne en vue de dos.

Le basculement est purement directionnel : il suffit de mesurer, sur `Idle`,
l'écart de chaque direction à la moyenne des huit directions **de la même
image**, puis de le retirer. Recentrer image par image est indispensable : sur
un `Idle` très mobile comme celui de Kaiminus, dont la tête monte de 24 à 2 px
au fil de l'animation, une moyenne globale annule complètement le signal
recherché.

Une fois le biais retiré, le marqueur se stabilise sur l'axe du corps
(Salamèche : 13,5 px dans les huit directions) et redevient une ancre fiable,
tout en conservant les mouvements réels de la tête d'une image à l'autre.

Les marqueurs rouge et bleu servent de **seconde ancre indépendante** : leur
milieu donne la ligne d'épaules, qui suit l'animation et reste juste sous le
cou, y compris chez les Pokémon à très grosse tête. Leur écartement donne en
prime la carrure, qui sert à dimensionner un col.

Handedness : ligne 0 (de face), rouge est à gauche de l'écran ; ligne 4 (de dos),
rouge passe à droite. Les deux marqueurs sont donc bien liés au corps et non à
l'écran, et le rouge correspond au côté droit de l'entité.

## 5. `<Name>-Shadow.png`

Même dimensions. Le pixel blanc marque le centre au sol du sprite pour la case.
Les composantes vert / rouge / bleu délimitent l'emprise des ombres petite /
normale / grande, sélectionnées par `<ShadowSize>`.

## 6. Couleurs

Toutes les planches du corpus sont en **RGBA 8 bits** (aucune palette indexée),
avec transparence binaire. Les sprites Chunsoft respectent une contrainte de
16 couleurs par case héritée de la ROM ; les planches du dépôt ne l'imposent pas
au niveau du fichier.

## 7. Licence

SpriteCollab est publié sous **CC BY‑NC 4.0** : réutilisation non commerciale,
attribution obligatoire. Les crédits par Pokémon sont dans `credits.txt` et
repris dans `CREDITS.md`. Les sprites originaux appartiennent à Spike Chunsoft /
The Pokémon Company / Nintendo.
