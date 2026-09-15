# Politoed — portraits PMD / SpriteCollab

Ce dossier contient la source reproductible du lot `#0186 Politoed` livré dans
`portrait/0186/`.

## Règles appliquées

- une émotion = une image opaque de **40 × 40 px** ;
- **15 couleurs maximum par portrait** (la transparence n'est pas utilisée) ;
- ordre SpriteBot/SpriteViewer :
  `Normal, Happy, Pain, Angry, Worried, Sad, Crying, Shouting,
  Teary-Eyed, Determined, Joyous, Inspired, Surprised, Dizzy, Special0,
  Special1, Sigh, Stunned, Special2, Special3` ;
- les 16 émotions hors `Special0`–`Special3` sont présentes ;
- Politoed étant asymétrique (boucle de tête, profil et joue), les 20 portraits
  retournés sont livrés dans la seconde moitié de `Sheet.png` et sous les noms
  `Emotion^.png` ;
- les fonds suivent les motifs canoniques de la planche SpriteViewer et les
  quatre portraits Politoed déjà publiés, sans fond uni inventé ;
- les portraits officiels ou déjà publiés n'ont pas été repeints.

La méthode du guide fourni a été suivie : recherche et références 2D, tête de
base réutilisable, expressions redessinées en pixels, contrôle à la taille
native, puis contrôle de palette. Les détails sont lisibles à 1× ; le contact
sheet agrandi n'est pas un asset de jeu.

## Provenance et crédits

Références consultées le 15 septembre 2026 :

- [Politoed #0186 sur PMD Sprite Repository](https://sprites.pmdcollab.org/#/0186?form=0)
- [PMDCollab/SpriteCollab, commit `39246063655c8b3de3ff104e323b1d5c081c39f0`](https://github.com/PMDCollab/SpriteCollab/tree/39246063655c8b3de3ff104e323b1d5c081c39f0)
- [guide PMD Portraits for SkyTemple](https://docs.google.com/presentation/d/1eM1j_tWP-PHzxzpyIYVe819RxYWr9Ow3CF4vVwdMtmw/edit?usp=drivesdk)

`reference/Normal.png` est le portrait CHUNSOFT existant. `Inspired.png`,
`Shouting.png` et `Surprised.png` sont conservés depuis l'entrée Politoed
existante de SpriteCollab (crédit PMDCollab_2 / Caitemis dans la fiche du
site). Les 16 slots manquants et les variantes miroir sont les nouveaux
pixels de ce lot, produits pour ce dépôt par Arena.ai Agent à la demande de
`meromoonmeri`.

La licence et les conditions d'utilisation des références restent celles de
SpriteCollab : usage non commercial, crédit obligatoire, [CC BY-NC
4.0](https://creativecommons.org/licenses/by-nc/4.0/). Ce lot local n'est pas
une approbation automatique par les approbateurs SpriteCollab.

## Reproduction et contrôle

Depuis la racine du dépôt :

```bash
python -m pip install -r source/requirements.txt
python source/portraits_politoed/build_portraits.py
python source/portraits_politoed/verify_portraits.py
```

Le générateur recopie les quatre PNG de référence sans les réencoder, compose
les autres portraits à partir de la tête de base et des fonds archivés, crée
les miroirs, puis écrit la planche 200 × 320. Le vérificateur contrôle les
40 portraits, les dimensions, l'opacité, la palette, les miroirs et chaque
case de la planche.
