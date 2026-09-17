# Falinks #0870 — portraits PMD / SpriteCollab

Ce lot conserve le portrait canonique `Normal.png` de la variante Falinks
`0870/0002` et construit les autres expressions par corrections pixel par
pixel sur la même base. Le fond, la silhouette du casque et la palette restent
identiques au portrait fourni.

## Sortie

- `portrait/0870/0002/` : 20 émotions, leurs miroirs exacts et `Sheet.png` ;
- `portrait-0870-0002.zip` : archive prête à importer ;
- `portrait-0870.zip` : alias de compatibilité, byte-for-byte identique ;
- portraits individuels : 40 × 40 px, opaques, 15 couleurs maximum ;
- planche SpriteBot : 200 × 320 px, 20 normales puis 20 miroirs.

Les expressions sont dessinées manuellement depuis `Normal.png` : yeux fermés,
colère, douleur, larmes, surprise, vertige, soupir et variantes Special. Aucun
portrait généré avec une autre espèce ou une autre base n'est mélangé au lot.

Source canonique : `PMDCollab/SpriteCollab/portrait/0870/0002`, commit
`f273fb951f3931503a1c5533e9ff00a19ddd373b`. Le crédit upstream de `Normal.png`
est conservé dans `credits.txt`.

## Contrôle

```bash
python source/portraits_falinks/build_portraits.py
python source/portraits_falinks/verify_portraits.py
```
