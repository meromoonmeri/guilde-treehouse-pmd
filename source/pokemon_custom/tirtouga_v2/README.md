# Carapagos / Tirtouga 0564 — reconstruction V2, partielle

Le premier brouillon sur magenta n'a pas survécu à la restauration du checkout avant push. **Cette V2 est une nouvelle génération**, conservée et poussée, pas le fichier ancien retrouvé.

## Livraison effective

- `exports/pokemon_custom/tirtouga_v2/sprite_multisheet/` : Idle + Walk, chacun 4 colonnes × 8 directions, cellules 48×48 ; XML et triplets Anim/Offsets/Shadow. Palette globale **14 couleurs**, alpha binaire. Ordre D, DR, R, UR, U, UL, L, DL.
- Idle : clignement minimal des cinq vues où le visage est visible ; les autres poses restent fixes. Certaines phases sont des maintiens, **pas 32 dessins distincts**.
- Walk : premier cycle de nageoires opposées, détourées comme membres entiers, déplacement de 1 pixel ; corps fixe. Ce n'est pas Idle renommé, mais la locomotion et les attaches demandent encore une revue artistique/moteur. Ce premier cycle très sobre n'est pas une démarche finale approuvée.
- Portraits : **Normal existant inchangé**, trois adaptations pixel manuelles Happy/Angry/Sad. Fonds issus des cellules correspondantes de `template.png`, réduits à trois couleurs de fond avant composition. Portraits finaux 40×40 opaques, respectivement 13/12/13/13 couleurs. Pas d'invention d'un Normal « manquant ».
- Galerie : `apercu_mega_et_carapagos.html`. Aperçus natifs et agrandis dans `review/`.

## Provenance / attribution

La planche magenta est générée par IA dans cette session, puis détourée, mise à la palette, direction DR corrigée par miroir, yeux retouchés et membres découpés à la main dans le script. Le rendu généré conserve des variations de proportions et de plaques de carapace entre les angles : **la quantification et le précontrôle ne les corrigent pas et ne constituent pas une finition artistique**.

Normal : SpriteCollab `3609a86be2a4c8ad7cf255bd2255f044daafe24f`, `portrait/0564/Normal.png`. Historique MUCRUSH ; crédit courant `<@!217899432652308480>`, **CC_BY-NC_4** selon le fichier natif `references/credits.txt` conservé. Happy/Angry/Sad sont des **adaptations de cette œuvre**, pas des créations intégralement originales ; attribution et restriction non commerciale conservées. Pokémon / Carapagos appartient à ses ayants droit. Pas de soumission publique faite ; admissibilité IA à confirmer avec les mainteneurs.

## Contrôles et reste à faire

`build.py` reconstruit les exports et exécute le précontrôle local.
- Minimum sprite PASS ; minimum portraits PASS.
- Donjon **FAIL attendu** : Sleep, Hurt, Attack, Charge, Swing, Double, Rotate, Hop absents.
- Portrait complet **FAIL attendu** : 12 émotions obligatoires absentes.
- 19 tests unitaires du validateur PASS le 16 septembre 2026.
- Pas de test SpriteBot officiel, d'import PMDO, de réexport moteur ou d'approbation artistique.

La prochaine étape n'est pas de dupliquer Idle sous huit autres noms : finir la cohérence anatomique des huit vues puis dessiner de véritables poses d'action. Aucun autre Pokémon manquant n'est déclaré terminé par ce lot.
