# Politoed #0186 — PMD portraits

Lot complet au format SpriteCollab/SpriteBot : 20 émotions canoniques et leurs
20 variantes miroir pour le Pokémon asymétrique.

- portraits individuels : `Emotion.png` et `Emotion^.png` ;
- planche importable : [`Sheet.png`](Sheet.png), 200 × 320 px ;
- fonds canoniques fournis : [`template.png`](template.png) et
  [`Extra_Backgrounds.png`](Extra_Backgrounds.png) ;
- ordre de la planche :
  `Normal, Happy, Pain, Angry, Worried / Sad, Crying, Shouting,
  Teary-Eyed, Determined / Joyous, Inspired, Surprised, Dizzy, Special0 /
  Special1, Sigh, Stunned, Special2, Special3`, puis le même ordre retourné ;
- chaque case mesure 40 × 40 px, est opaque et reste à 15 couleurs ou moins.

Les fichiers `Normal.png`, `Inspired.png`, `Shouting.png` et `Surprised.png`
conservent les portraits Politoed déjà présents dans SpriteCollab. Les autres
expressions et les variantes miroir complètent le set dans la même contrainte
pixel-art. Le générateur utilise une planche BIG de recherche, puis la nettoie
et la réduit avant de poser les fonds canoniques ; cette planche de travail est
archivée dans `source/portraits_politoed/reference/ai_expression_guide.png`.
Voir [`source/portraits_politoed/README.md`](../../source/portraits_politoed/README.md)
pour la méthode, la provenance et les crédits.
