# Beach — référence en calques alternatifs

Livraison volontairement simple : la composition visuelle de `beach.rsground` est conservée, mais ses trois couches natives sont exposées comme calques PMDO séparés pour donner au joueur une map alternative au jeu de base.

## Calques

1. `Back` — fond sable, ciel et rivage depuis `D01P11A_layer1.tile` ;
2. `Anim` — animation supérieure depuis `beach_animation.tile` ;
3. `Front` — roches, palmiers et premier plan depuis `D01P11A_layer2.tile`.

L’animation conserve les **17 frames présentes dans le Ground référent** et `FrameLength=16`. Aucun nouveau layout, aucune texture générée et aucun pixel du générateur d’image ne sont utilisés.

## Dimensions

- 33 × 16 cellules ;
- 24 px par cellule ;
- 792 × 384 px ;
- `TexSize=3`.

## Sorties

- `apercu_beach_reference_multilayer_v1.html` ;
- `beach_reference_multilayer_v1_pmdo.zip` ;
- `renders/beach_reference_multilayer_v1/` ;
- `source/beach_reference_multilayer_v1/build.py`.

Les previews magenta servent uniquement à distinguer les calques. Le Ground final contient les cellules canoniques EoSO et le ZIP contient les trois feuilles `.tile` correspondantes.

PMDO/GPU, collisions et raccord de destination ne sont pas validés ici.
