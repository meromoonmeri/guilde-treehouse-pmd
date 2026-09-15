# Pipeline générateur → sprite PMDO (Mega Raichu)

Livrables : [`sprite/0026_mega_x_gen/`](../../sprite/0026_mega_x_gen/),
`sprite-0026-mega-x-gen.zip`, aperçus dans `gifs/0026_mega_x_gen/`.

**Idle, 2 frames × 8 directions, avec les ailes-éclairs.**

## Ce que ça résout

Le pack précédent (`sprite/0026_mega_x`) est une **recoloration** de la
géométrie canonique de Raichu : 35 animations, mais **sans les ailes-éclairs**,
faute de pouvoir les redessiner à la main sur tous les angles.

Ici le **générateur d'image fournit les angles manquants**. Il a reçu deux
références :

| Référence | Rôle |
| --- | --- |
| `gen/ref_canonical_8dir.png` | les **8 angles de caméra** et la pose à copier |
| `gen/ref_mega_front.png` | le **design Mega** à appliquer |

Il rend `gen/mega_8dir.png` : une rangée de 8 cellules, design Mega complet,
**ailes et queue tournant correctement** avec le corps.

## La pipeline de conversion

Une planche générée n'est pas un sprite : elle est énorme, sur fond magenta,
anti-aliasée sur les bords et porte des milliers de couleurs. La chaîne
(`pipeline.py`) est déterministe, et chaque étape protège la qualité pixel art.

| # | Étape | Détail |
| --- | --- | --- |
| 1 | **Détourage** | le magenta est retiré **par test de teinte**, pas par égalité stricte : le générateur tramote légèrement la clé |
| 2 | **Découpe** | la rangée est coupée en 8 cellules de direction |
| 3 | **Détection de grille** | la taille de pixel implicite du générateur est **mesurée** sur les longueurs de séries → **facteur 2** détecté |
| 4 | **Réduction** | moyenne d'aire vers cette grille native. **Seul redimensionnement de la chaîne** |
| 5 | **Quantification** | chaque pixel est snappé sur la **palette exacte de l'artwork Mega** |
| 6 | **Durcissement** | alpha strictement 0 ou 255, ce qui tue le fringing du générateur |
| 7 | **Cadrage** | boîte englobante et **ligne de sol communes** aux 8 cellules, pour éviter le sautillement entre directions |
| 8 | **Émission** | feuilles `-Anim`, `-Offsets`, `-Shadow` + `AnimData.xml` |

### Le bug corrigé en route

La quantification tournait **avant** le cadrage. Or le cadrage
redimensionnait encore, remélangeant les couleurs snappées : **3861 couleurs**
en sortie. La quantification a été déplacée **après tout redimensionnement** —
elle n'a de sens qu'une fois la géométrie figée. Résultat : **13 couleurs**.

## Contrôle

```bash
python source/sprites_mega_raichu/pipeline.py
python source/sprites_mega_raichu/verify_gen.py
```

Le vérificateur contrôle : dimensions paires, grille 2 × 8, alpha binaire,
≤ 15 couleurs, **chaque couleur provient de l'artwork Mega d'origine**,
marqueurs légaux, et **les 8 directions sont toutes non vides et toutes
différentes** — c'est tout l'intérêt d'une planche de rotation. Tout passe.

## Réserves honnêtes

- **Seul `Idle` est produit** par cette pipeline, en 2 frames (un léger
  balancement obtenu par décalage vertical, sans invention de pose). Les 34
  autres animations demanderaient une planche générée par animation.
- **Les pixels viennent du générateur**, pas d'une source canonique. La
  cohérence avec le design est garantie par la palette, pas par l'origine.
- Le générateur interprète les angles : les vues de dos et de trois-quarts
  sont **plausibles, pas canoniques**. Un artiste retoucherait la perspective
  des ailes.
- **Deux packs coexistent volontairement** :
  `0026_mega_x` (35 animations, recoloration, sans ailes) et
  `0026_mega_x_gen` (Idle seul, design Mega complet). Les fusionner suppose de
  porter les ailes sur les 34 autres animations.
- **Aucun test moteur PMDO ou SkyTemple.**
