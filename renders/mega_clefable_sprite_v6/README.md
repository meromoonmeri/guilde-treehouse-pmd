# Méga-Mélodelfe V6 — design validé par l'utilisateur, animations dessinées par vue, cadre SpriteCollab (lot `mega_clefable_sprite_v6`)

**Design retenu** : l'image envoyée par l'utilisateur (vue de face du turnaround V4) → `source/mega_clefable_sprite_v6/references/design_valide_*.png`, carte de design `gen/design_card.png` (face agrandie + 8 vues) donnée au générateur pour chaque bande.

## Bandes dessinées par le générateur (`gen/raw_*.png`, SHA256 dans le manifest)
Attack face / profil / dos (10 frames chacune : garde, recul, élan bras tendu, maintien, retour), Swing face / profil (9 frames, grand arc du bras), poses Hurt (face/profil/dos), Sleep (2 frames), Charge (face/profil/dos), Idle vol de face (bobbing + battement), Walk = vol de profil, de dos et de ¾ (cycles de battement). Design identique d'une frame à l'autre dans chaque bande (vérifié visuellement + contrôle automatique calotte/2 ailes).

## Mise en cadre SpriteCollab
Pour les 13 animations : grille CHUNSOFT (8 directions : face, ¾, profil, dos ×3, profil miroir, ¾ miroir), nombre de frames, durées, Rush/Hit/Return, Strike=CopyOf ; chaque frame est posée sur le **marqueur vert canonique** (centre du corps) de l'Offsets.png du Mélodelfe → trajectoires des artistes SpriteCollab (élan Attack +19 px, secousse Double ±13 px, arc Swing, parabole Hop, rotation…). Double = frames de frappe de la bande Attack ; Withdraw/Dance/Hop/Rotate = cycles de vol sur leurs chemins canoniques. Frames élargies (+24/+10) pour les ailes ; Offsets/Shadow canoniques décalés ; palette 16 couleurs relevée sur les bandes ; contour 1 px ; alpha binaire.

## Vérification — `verify.py` 64/64 PASS (format PMDOWiki + Offsets/Shadow canoniques + design présent dans 100 % des cases)

## Fichiers
`sprite/0036/0001/`, `0036_0001_mega_clefable_v6_spritecollab.zip`, `apercu_<Anim>.webp` ×12, `planche_<Anim>.png`, `manifest.json`.
Limites : 3 vues + ¾ face (pas de ¾ dos : vue de dos utilisée) ; Withdraw/Dance/Hop/Rotate sans poses dédiées (cycles de vol) — à dessiner au tour suivant si souhaité ; art IA déclaré ; non testé en moteur. V1–V5 conservés.
