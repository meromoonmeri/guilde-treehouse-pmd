# Terapagos — sprite PMD SpriteCollab

Deux outils, deux rôles séparés.

- **Le générateur d'image** est employé comme un artiste pixel-art spécialisé PMD.
  Il reçoit en entrée de vraies planches SpriteCollab / Explorers of Sky
  (`references/`) et doit en reproduire la grammaire : placement des pixels,
  clusters, outline sélectif, ombres, lumières, expression, simplification.
- **Le moteur paramétrique** (`moteur_sprite.py`) ne dessine rien.
  Il garantit la structure technique : détramage, palette, grille, cadrage,
  directions, frames, export.

## Grammaire appliquée

```
silhouette   compacte, basse, plus large que haute, tenant dans 64×64
proportions  carapace ≈ 2/3 du sprite, tête ≈ 1/3, crinière courte et jointive
clusters     blocs de pixels francs, aucun pixel isolé décoratif
outline      1 px, ton assombri désaturé du remplissage voisin, jamais noir uni
ombres       bandes dures à trois tons, lumière venant du haut avant
lumières     liseré pâle sur l'arête du dôme, un pixel spéculaire par œil
détails      facettes polygonales, éclats de gemmes de 1-2 px, marques zigzag
expression   deux grands yeux cyan, regard neutre d'attente
animation    déplacements entiers, aucune interpolation, aucun flou
```

## Références utilisées

`references/eos_treecko_idle.png` (planche Explorers of Sky),
`references/spritecollab_espurr_sheet.png` (planche communautaire),
`references/terapagos_officiel.jpg` (identité du sujet).
Ces images sont passées **en entrée du générateur**, pas seulement décrites.

## Chaîne technique

1. **Détramage** — la taille du bloc de pixels de l'image générée est retrouvée
   par PGCD des transitions, puis l'image est ramenée à sa résolution réelle.
2. **Nettoyage** — le fond n'est retiré que par propagation depuis les bords,
   ce qui préserve les éclats clairs internes ; l'alpha est binarisé.
3. **Palette** — median-cut sur la mosaïque des huit directions, complété par
   les extrêmes (outline, spéculaire) et les teintes les plus saturées, afin que
   les gemmes et les pupilles survivent à la quantification.
4. **Cadrage** — mise à l'échelle commune, centrage horizontal, pieds ancrés à
   `MARGE_SOL` du bas de la cellule.
5. **Directions** — cinq angles générés, trois obtenus par miroir
   (BasGauche, Gauche, HautGauche), comme le font les artistes SpriteCollab.
6. **Frames** — animations décrites en données : durées, déplacements entiers,
   écrasement vertical en pixels entiers.
7. **Export** — `*-Anim.png`, `*-Shadow.png`, `AnimData.xml`, `sprite.json`,
   planches et GIF de contrôle.

## Sorties — `terapagos/`

| Fichier | Contenu |
| --- | --- |
| `Idle-Anim.png` | 8 directions × 4 frames, cellules 64 × 64 |
| `Walk-Anim.png` | 8 directions × 4 frames |
| `Hurt-Anim.png` | 8 directions × 2 frames |
| `*-Shadow.png` | points d'ombre au format SpriteCollab |
| `AnimData.xml` | index, dimensions et durées des animations |
| `sprite.json` | palette verrouillée et paramètres de cadrage |
| `planche_directions_x3.png` | contrôle visuel des huit directions |
| `apercu_idle.gif` | contrôle de l'animation |

## Régénérer

```bash
python3 source/sprites_pmd/moteur_sprite.py
```

Le moteur relit `generation/brut_*.png`. Pour changer le rendu artistique, on
régénère ces images ; pour changer le format, la palette ou les animations, on
modifie les constantes et la liste `ANIMATIONS` en tête du moteur.
