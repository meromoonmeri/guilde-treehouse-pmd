# Falinks #0870 — PMD portraits

Lot complet au format SpriteCollab/SpriteBot : 20 émotions canoniques et leurs
20 variantes miroir.

- portraits individuels : `Emotion.png` et `Emotion^.png` ;
- planche importable : [`Sheet.png`](Sheet.png), 200 × 320 px ;
- fond canonique utilisé : [`template.png`](template.png), copie de
  [`portrait/0186/template.png`](../0186/template.png) ;
- ordre de la planche :
  `Normal, Happy, Pain, Angry, Worried / Sad, Crying, Shouting,
  Teary-Eyed, Determined / Joyous, Inspired, Surprised, Dizzy, Special0 /
  Special1, Sigh, Stunned, Special2, Special3`, puis le même ordre retourné ;
- chaque case mesure 40 × 40 px, est opaque et reste à 15 couleurs ou moins.

`Normal.png` conserve au pixel près le portrait Falinks publié sur
SpriteCollab. **Toutes les autres expressions sont dérivées de ce portrait
existant** : le personnage est extrait tel quel, seuls les yeux sont effacés
puis redessinés, avec de petits effets (larmes, gouttes, étincelles, veines de
colère) pris exclusivement dans les 12 couleurs du portrait d'origine. Aucune
image générée n'entre dans le lot.

Les quatre slots `Special` suivent la logique du personnage, un Pokémon de
formation militaire : `Special0` salut discipliné, `Special1` clin d'œil
assuré, `Special2` repos yeux fermés, `Special3` cri de guerre.

Voir [`source/portraits_falinks/README.md`](../../source/portraits_falinks/README.md)
pour la méthode, la provenance et les crédits.
