# Terapagos #1024 — forme Stellaire, portraits

Livrable : [`portrait/1024/`](../../portrait/1024/) — 16 émotions et leurs
16 miroirs, au format SpriteCollab/SpriteBot.

## Constat de départ

`portrait/1024/0002` (Stellaire) ne contient en amont que **`Normal.png` et
`Normal^.png`**. C'est donc la seule source artistique disponible.

## Étude préalable

J'ai examiné la forme **Terastal** (`portrait/1024/0001`), du même artiste, qui
possède davantage d'expressions. Enseignement : sur Terapagos, la carapace
cristalline **ne se déforme jamais**. L'artiste fait porter toute l'émotion par
**l'œil**, et uniquement par lui. Il n'y a ni bouche ni sourcil mobilisables.

## Méthode

- la carapace du portrait Stellaire publié est **conservée au pixel près** ;
- seul l'**œil** est repeint, dans son empreinte exacte de 6 × 7 px relevée sur
  les pixels publiés (colonnes 12–17, lignes 24–30) ;
- chaque variante réutilise le **langage chromatique de l'œil d'origine** :
  corps cyan, reflet blanc, paupière violette, liseré magenta conservé ;
- quelques effets PMD sobres (goutte, larmes, étincelle, trait de sourcil)
  dessinés uniquement dans la palette Stellaire ;
- **les miroirs ne sont pas un simple retournement** : le `Normal^` publié est
  retouché à la main par l'artiste (54 pixels diffèrent d'un flip mécanique).
  Chaque miroir est donc construit **sur ce `Normal^` publié**, ce qui préserve
  ses corrections au lieu de les jeter.

Aucun pixel généré par IA dans ce lot.

## Slots Special

Laissés vides. Le FAQ SpriteCollab exige qu'un Special soit réellement unique
et refuse tout ce qui se décrit comme « une autre émotion sur un autre fond ».

## Contrôle

```bash
python source/portraits_terapagos/build_portraits.py
python source/portraits_terapagos/verify_portraits.py
```

Le vérificateur contrôle : 40 × 40, opacité, ≤ 15 couleurs, présence des 16
émotions, palette strictement Stellaire, **aucun pixel modifié hors de la zone
œil/effets**, cohérence des miroirs avec les corrections amont, et ordre de la
planche.

## Réserves honnêtes

- L'émotion ne reposant que sur l'œil, les écarts entre expressions sont
  volontairement **fins** : c'est la contrainte du personnage, pas un manque
  d'ambition. À juger au zoom.
- Contrôles de format uniquement ; pas de validation en jeu ni d'approbation
  SpriteCollab.

## Crédits

`Normal` et `Normal^` : `<@!350050109741858829>`, CC BY-NC 4.0. Expressions
dérivées attribuées à `meromoonmeri / Arena.ai Agent` dans
`portrait/1024/credits.txt`.
