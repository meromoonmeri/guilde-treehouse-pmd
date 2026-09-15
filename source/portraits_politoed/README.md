# Politoed — portraits PMD / SpriteCollab

Ce dossier contient la source reproductible du lot `#0186 Politoed` livré dans
`portrait/0186/`.

## Règles appliquées

- une émotion = une image opaque de **40 × 40 px** ;
- **15 couleurs maximum par portrait** ;
- ordre SpriteBot/SpriteViewer :
  `Normal, Happy, Pain, Angry, Worried, Sad, Crying, Shouting,
  Teary-Eyed, Determined, Joyous, Inspired, Surprised, Dizzy, Special0,
  Special1, Sigh, Stunned, Special2, Special3` ;
- les 16 émotions hors `Special0`–`Special3` sont présentes ;
- Politoed étant asymétrique (boucle de tête, profil et joue), les 20 portraits
  retournés sont livrés dans la seconde moitié de `Sheet.png` et sous les noms
  `Emotion^.png` ;
- les fonds ne sont plus reconstruits par approximation : le fichier fourni
  par l'utilisateur `portrait/0186/template.png` est la planche canonique
  200×320 : ses 20 cases supérieures (grille 5×4) sont lues case par case,
  sans redimensionnement ni interpolation ; la moitié miroir est produite par
  retournement exact, comme l'exige le format SpriteBot ;
- `portrait/0186/Extra_Backgrounds.png` est conservé comme planche canonique
  complémentaire pour les variantes et l'audit visuel ;
- les portraits officiels ou déjà publiés ne sont pas repeints.

## Méthode optimisée

La chaîne suit la méthode du guide PMD Portraits for SkyTemple, avec un
contrôle supplémentaire contre les glitches. La configuration du générateur
est figée dans `ai_generation_config.json` :

1. `reference/ai_expression_guide.png` est une planche **BIG 1024×1024** de
   recherches d'expressions, 16 cases de 256×256 ; elle sert uniquement de
   croquis de pose et d'anatomie, pas de sprite final ;
2. chaque case est isolée par composant connecté afin d'écarter les étoiles,
   points ou symboles parasites éventuellement générés autour de la tête ;
3. la tête est réduite de 256×256 à 40×40 par bilinéaire, comme dans le guide,
   puis chaque pixel visible est ramené à la palette Politoed approuvée ;
4. le fond canonique est posé après la réduction, ce qui empêche les artefacts
   du générateur de contaminer les motifs de fond ;
5. les cases standard conservent exactement les couleurs du template. Les
   cases `Special` à fond très riche passent par une réduction déterministe
   sans tramage, uniquement pour respecter la limite de 15 couleurs ;
6. le rendu est contrôlé à 1×, puis exporté en portraits individuels et en
   planche SpriteBot.

Les détails doivent rester lisibles à 1× ; un contact sheet agrandi n'est pas
un asset de jeu.

## Provenance et crédits

Références consultées le 15 septembre 2026 :

- [Politoed #0186 sur PMD Sprite Repository](https://sprites.pmdcollab.org/#/0186?form=0)
- [PMDCollab/SpriteCollab, commit `39246063655c8b3de3ff104e323b1d5c081c39f0`](https://github.com/PMDCollab/SpriteCollab/tree/39246063655c8b3de3ff104e323b1d5c081c39f0)
- [guide PMD Portraits for SkyTemple](https://docs.google.com/presentation/d/1eM1j_tWP-PHzxzpyIYVe819RxYWr9Ow3CF4vVwdMtmw/edit?usp=drivesdk)

`reference/Normal.png` est le portrait CHUNSOFT existant. `Inspired.png`,
`Shouting.png` et `Surprised.png` sont conservés depuis l'entrée Politoed
existante de SpriteCollab (crédit PMDCollab_2 / Caitemis dans la fiche du
site). Les nouveaux slots sont produits pour ce dépôt par Arena.ai Agent à la
demande de `meromoonmeri` ; la planche BIG est archivée comme référence de
travail et non comme asset SpriteCollab approuvé.

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

Le générateur recopie les quatre PNG de référence sans les réencoder, utilise
le template canonique fourni, extrait et nettoie la planche BIG, crée les
miroirs, puis écrit la planche 200 × 320. Le vérificateur contrôle les 40
portraits, les dimensions, l'opacité, la palette, les miroirs, les sources
canoniques et chaque case de la planche.
