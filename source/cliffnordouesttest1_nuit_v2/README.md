# Nuit non destructive — construction et validation

```sh
.venv/bin/python source/cliffnordouesttest1_nuit_v2/build.py
.venv/bin/python source/cliffnordouesttest1_nuit_v2/runtime_test.py
.venv/bin/python source/cliffnordouesttest1_nuit_v2/build.py --apply
.venv/bin/python source/cliffnordouesttest1_nuit_v2/verify.py
```

Pillow/NumPy ; helpers `ciels_valides.py` et `pmdo_cote/build.py`. Le test natif nécessite l’installation jetable documentée dans [pmdo_runtime](../pmdo_runtime/README.md), présente sous `.cache/pmdo-runtime/engine/PMDO`. Aucun cache ou moteur embarqué dans le livrable.

## Préservation

Original lu avec `git show aac14ae4:cliffnordouesttest1.rsground`. Remplacement binaire du seul littéral `"Status": {}` ; aucun reformatage du reste. Application autorisée uniquement si le fichier actuel correspond exactement à l’original, à la version jour34d40dc0 ou au résultat nocturne. Les edits utilisateur indépendants déclenchent un refus.

L’original, le jour et la nuit conservent les mêmes quatre calques et les mêmes collisions, positions, frames, noms, entités et propriétés. Le voile nocturne ne convertit pas les banques elles-mêmes. La demande de mer animée reste explicitement bloquée sur les cinq banques personnalisées absentes.

## Natif

Un `MultiSwitchEmitter` contient deux `OverlayEmitter` ordonnés surTop :

1. Texture opaque1×1 RGB(8,14,36), `Anim.Alpha=176`, mouvement nul. `OverlayAnim.Draw` possède un cas1×1 couvrant l’écran entier sans tuilage pixel par pixel.
2. Nuages Guilde/Sharpedo nocturnes, alpha natif,1440×784, bande ày208, vitesse−4px/s. Éclairage indépendant du voile puisqu’ils sont dessinés ensuite.

Sources inspectées : RogueCollab/RogueEssence `8b7eafafa73ff0c10b9e8fd9348559ee1b5dfe8b`, `SingleEmitter.cs`, `OverlayEmitter.cs`, `OverlayAnim.cs`, `BaseGroundScene.cs`. Le squeletteMapStatusData vient de la référence épinglée de V1. Aucune nouvelle ressource météo/gameplay.

## Tests et limites

- [`verification.json`](verification.json) : **20contrôles PASS**, y compris les octets horsStatus, les binairesBG prémultipliés, l’égalité de l’alpha et de la géométrie des nuages jour/nuit, la recette nocturne exacte et les32phases du WebP d’effet.
- [`runtime_results.tsv`](runtime_results.tsv), [`runtime_verification.json`](runtime_verification.json) : **21contrôles natifs PASS** dans le vrai PMDO0.8.12. Ground etMapStatusData chargés, puis clone du vraiMultiSwitchEmitter exécuté dans les listes d’animation d’un `TitleScene(false)` natif, dérivé deBaseScene. Aucune méthodeBegin/Draw appelée : ce conteneur sert uniquement à tester le cycle de vie de l’émetteur sans GPU.
- Premier essai avec `GroundScene()` : exception car son constructeur crée unRenderTarget2D et nécessite unGPU. Cette tentative a été arrêtée et ses fichiers restaurés. Le test a été corrigé pour utiliser le conteneur sans dessin décrit ci-dessus, puis entièrement relancé. Ce remplacement ne constitue **pas une validation de rendu du Ground**.
- Le hookLua et les ressources installées temporairement sont restaurés, succès ou échec. RenduGPU, visibilité en éditeur, lecture en jeu et textures absentes **non validés**.

Le voile est une ambiance nocturne globale, **pas la palette nocturne canonique exacte du terrain**, impossible à reconstruire ici sans ses images.

[Installation et fichiers](../../exports/cliffnordouesttest1_nuit_v2/README.md).

Recherche supplémentaire des cinq banques : arbres complets de `PMD-SKY-PMDO-PORT`, `NewEra-Canonical-Integration` et `MOREMAP`, aucun nom correspondant. [Commits et résultats](additional_asset_search.json).
