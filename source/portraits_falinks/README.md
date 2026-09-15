# Falinks — portraits PMD / SpriteCollab

Source reproductible du lot `#0870 Falinks` livré dans `portrait/0870/`.

## Correction de méthode demandée par l'utilisateur

Contrairement au lot Politoed, **aucune planche générée par IA n'est utilisée**.
La consigne du 15 septembre 2026 est explicite : partir du portrait existant
pour créer les manquants. Le seul matériau graphique du lot est donc
`reference/Normal.png`, le portrait Falinks publié sur SpriteCollab.

## Règles appliquées

- une émotion = une image opaque de **40 × 40 px** ;
- **15 couleurs maximum par portrait** ;
- ordre SpriteBot/SpriteViewer :
  `Normal, Happy, Pain, Angry, Worried, Sad, Crying, Shouting, Teary-Eyed,
  Determined, Joyous, Inspired, Surprised, Dizzy, Special0, Special1, Sigh,
  Stunned, Special2, Special3` ;
- les 16 émotions requises sont présentes, plus les 4 slots `Special` ;
- Falinks est asymétrique (crête, reflet du casque, plaque faciale) : les 20
  portraits retournés sont livrés sous `Emotion^.png` et dans la seconde moitié
  de `Sheet.png` ;
- le portrait publié `Normal.png` est recopié octet pour octet, jamais repeint.

## Chaîne de production

1. **Extraction exacte.** Le fond du portrait Falinks publié est *identique au
   pixel près* à la case 0 de `portrait/0186/template.png` (mêmes trois
   couleurs, vérifié). Le calque personnage est donc isolé sans masque
   approximatif ni détourage manuel.
2. **Effacement ciblé.** Seuls les pixels d'yeux (bleu, blanc, cyan) situés
   dans les deux boîtes mesurées sur le portrait sont remis à la couleur de la
   plaque faciale. Casque, crête, mentonnière et silhouette restent intacts.
3. **Redessin des yeux.** Chaque émotion reçoit une paire d'yeux dessinée
   pixel par pixel dans `build_portraits.py`, sous forme de petites matrices
   ASCII lisibles et modifiables.
4. **Effets.** Larmes, gouttes de sueur, étincelles et veines de colère sont
   tracés uniquement avec les 12 couleurs du portrait d'origine. Falinks n'a
   pas de bouche dessinée : les marques de bouche sont de discrètes rainures
   de plaque dans le noir existant.
5. **Fond canonique.** Chaque case reprend la case correspondante de
   `template.png`, sans redimensionnement. Les rares cases `Special` dépassant
   15 couleurs passent par une réduction déterministe, sans tramage.
6. **Contrôle.** `verify_portraits.py` valide dimensions, opacité, palette,
   miroirs exacts, conservation du portrait amont, conservation du fond
   canonique et ordre de la planche.

## Provenance et crédits

- [Falinks #0870 sur PMD Sprite Repository](https://sprites.pmdcollab.org/#/0870?form=0)
- [PMDCollab/SpriteCollab, commit `13237e6357e2dd1c6b88649db9dbc4957a5934ad`](https://github.com/PMDCollab/SpriteCollab/tree/13237e6357e2dd1c6b88649db9dbc4957a5934ad)
- [guide PMD Portraits for SkyTemple](https://docs.google.com/presentation/d/1eM1j_tWP-PHzxzpyIYVe819RxYWr9Ow3CF4vVwdMtmw/edit?usp=drivesdk)

Le portrait amont `Normal` est crédité EZERART puis PMDCollab_2 dans
`reference/credits_upstream.txt`. Les nouveaux slots sont produits pour ce
dépôt par Arena.ai Agent à la demande de `meromoonmeri`.

Licence des références : CC BY-NC 4.0, usage non commercial, crédit
obligatoire. Ce lot local n'est pas une approbation automatique par les
approbateurs SpriteCollab.

## Reproduction et contrôle

Depuis la racine du dépôt :

```bash
python source/portraits_falinks/build_portraits.py
python source/portraits_falinks/verify_portraits.py
```
