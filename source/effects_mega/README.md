# Méga-Évolution — 10 frames, orbite 2D/3D

Livrable : [`effects/mega/`](../../effects/mega/)

- `Mega-Anim.png` : planche **800 × 768** — **10 frames × 8 directions**
  de 80 × 96 px (une ligne par direction, une colonne par frame) ;
- `Mega-<direction>.gif` : un aperçu animé par direction.

## Les deux règles de cette version

**FLUIDE.** Dix frames, c'est court : rien ne doit sauter. Chaque élément est
une **fonction continue** d'un temps normalisé `t` dans [0,1). Aucune table
frame par frame réglée à la main : les angles avancent d'un pas constant, les
rayons suivent des courbes lissées (`ease_in_out`). Le mouvement est donc
identique à n'importe quelle vitesse de lecture et **la boucle se referme sans
raccord**.

**3D.** L'énergie orbite sur **deux anneaux inclinés rendus en perspective**,
tournant en sens inverse. Chaque particule porte une profondeur `z = sin(angle)` :

- `z < 0` → dessinée **derrière** le sprite ;
- `z > 0` → dessinée **devant** ;
- taille et luminosité suivent la profondeur.

C'est ce tri par profondeur qui crée le volume : l'anneau **enveloppe**
visiblement le Pokémon au lieu de flotter par-dessus.

## Déroulé

| Frames | Contenu |
| --- | --- |
| 0–6 | les deux anneaux tournent et se resserrent, la flaque de lumière monte |
| 7–8 | flash blanc, seul moment où le sprite est masqué |
| 9 | onde de libération, retour du Pokémon |

## Discipline technique

- **Tout est dessiné nativement en 80 × 96, pixel par pixel.** Aucun
  redimensionnement. Aucune image générée par IA.
- **Palette extraite du sprite du sujet** — **12 couleurs**, transparence
  binaire.

## Deux corrections faites en cours de route

- **Particules lointaines invisibles** : la rampe de profondeur partait d'un
  violet quasi noir qui disparaissait sur sol sombre. Elle part maintenant d'un
  bleu acier lisible.
- **Tracé d'orbite en pointillés → rejeté** : à cette échelle, les tirets
  cassaient l'ellipse en arcs disjoints qui ressemblaient à des bugs
  d'affichage. Le tracé est désormais **continu**, et c'est la **couleur** qui
  porte la profondeur (moitié arrière sombre, moitié avant claire).

Les particules ont aussi une **courte traînée** orientée à l'opposé de leur
déplacement, ce qui donne la sensation de vitesse en peu de frames.

## Sujet

Par défaut Terapagos forme Stellaire. Pour un autre Pokémon, changer
`SPRITE_SHEET`, `SUBJECT_W`, `SUBJECT_H` — et réextraire la palette.

## Reproduction

```bash
python source/effects_mega/build_mega.py
```

## Réserves honnêtes

- Effet **VFX**, pas une animation de personnage SpriteCollab : pas
  d'`AnimData.xml`, pas de `-Offsets` ni `-Shadow`.
- **Pas de symbole Méga-Évolution** : le dessiner lisiblement en pixel art
  natif à cette taille est un travail à part entière, à faire à la main.
- Aucun test moteur PMDO.
