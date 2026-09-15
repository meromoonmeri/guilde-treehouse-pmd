# Animation d'effet — Méga-Évolution

Livrable : [`effects/mega_evolution/`](../../effects/mega_evolution/)

- `MegaEvolution-Anim.png` : planche horizontale de **16 frames de 80 × 96 px** ;
- `frame_00.png` … `frame_15.png` : frames individuelles ;
- `MegaEvolution.gif` : aperçu animé en boucle.

## Déroulé de l'animation

1. **frames 0–2** : de grosses colonnes de foudre s'abattent autour du Pokémon,
   qui est encore visible ;
2. **frames 2–6** : la **sphère d'énergie arc-en-ciel opaque** grandit et
   engloutit complètement le sprite ;
3. **frames 6–13** : le **symbole de la Méga-Évolution** — la double hélice
   d'ADN — brûle devant la sphère, en pleine taille ;
4. **frames 13–15** : la sphère s'effondre, le symbole s'efface, le Pokémon
   réapparaît.

## Choix techniques

- **Sphère opaque**, comme demandé : bandes concentriques arc-en-ciel avec un
  cœur blanc et un liseré clair. Aucune transparence dans le disque, le sprite
  est réellement caché.
- **Colonnes de foudre épaisses** : chaque colonne est faite de 3 ou 4 longs
  segments droits, tracés en barres larges avec cœur blanc, manteau pâle et
  liseré cyan/violet. Une première version avec une gigue pixel par pixel a été
  **testée puis rejetée** : elle produisait un grésillement fin au lieu de
  vraies colonnes. Les colonnes sont réparties dans des couloirs qui encadrent
  le sujet sans lui passer au travers.
- **Symbole** : la double hélice d'ADN de la Méga-Évolution, dessinée en art
  ASCII puis agrandie par **facteur entier** (pas de rééchantillonnage), avec
  un contour sombre pour rester lisible sur la sphère.
- **Discipline pixel art** : palette d'effet écrite à la main, chaque pixel
  est ramené dessus. Transparence binaire. **13 couleurs** utilisées.
- Tout est procédural et déterministe (aléatoire à graine fixe) : le rendu est
  reproductible à l'identique.

Aucun pixel généré par IA.

## Sujet

Par défaut, le sprite englouti est le `Idle` de Terapagos forme Stellaire
(`sprite/1024/Idle-Anim.png`, direction 0). Pour l'appliquer à un autre
Pokémon, changer `SPRITE_SHEET` et `SPRITE_FRAME` en tête du script.

## Reproduction

```bash
python source/effects_mega_evolution/build_mega_animation.py
```

## Réserves honnêtes

- C'est une **animation d'effet VFX**, pas une animation de personnage
  SpriteCollab : elle n'entre pas dans `AnimData.xml` et n'a ni feuille
  `-Offsets` ni feuille `-Shadow`. SpriteCollab n'a pas de slot pour ce type
  d'effet ; c'est un asset pour ton propre jeu.
- La cadence du GIF (90 ms) est un choix de lisibilité, à réaccorder selon le
  moteur.
- Aucun test moteur n'a été effectué.
